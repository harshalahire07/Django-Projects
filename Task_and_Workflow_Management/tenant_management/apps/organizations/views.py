from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import Organization, OrganizationMember, Team, PermissionRequest
from .serializers import (
    OrganizationSerializer, TeamSerializer,
    PermissionRequestSerializer, PermissionRequestCreateSerializer,
)
from apps.audit.models import AuditLog
from apps.organizations.rbac_service import has_permission, get_user_role
# Create your views here.
class CreateOrganizationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = OrganizationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from django.db import transaction

        with transaction.atomic():
            organization = serializer.save()

            team = Team.objects.create(
                name="General",
                organization=organization
            )

            OrganizationMember.objects.create(
                user=request.user,
                organization=organization,
                team=team,
                role=OrganizationMember.ADMIN,   # integer 4
            )
            
            AuditLog.objects.create(
                actor=request.user,
                action="ORG_CREATED",
                description=f"Organization '{organization.name}' created.",
                organization_id=organization.id,
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class MyOrganizationsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        memberships = OrganizationMember.objects.filter(user=request.user)
        organizations = [m.organization for m in memberships]
        serializer = OrganizationSerializer(organizations, many=True)
        return Response(serializer.data)

class OrganizationMembersAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, org_id):
        if not has_permission(request.user, org_id, OrganizationMember.MEMBER):
            return Response(
                {"detail": "Access denied"},
                status=403
            )

        members = OrganizationMember.objects.filter(
            organization_id=org_id
        ).select_related("user")

        data = [
            {
                "id": str(member.user.id),
                "email": member.user.email,
                "role": member.role,
                "team": {"id": str(member.team.id), "name": member.team.name} if member.team else None,
                "joined_at": member.joined_at.isoformat()
            }
            for member in members
        ]

        return Response(data)


class AddMemberAPIView(APIView):
    """
    POST /api/organizations/<org_id>/add_member/
    Admin-only: add an existing user to this organization as MEMBER.
    Body: { "email": "user@example.com" }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, org_id):
        # Only admins (role >= 4) can invite members
        if not has_permission(request.user, org_id, OrganizationMember.ADMIN):
            return Response(
                {"detail": "Only admins can add members"},
                status=status.HTTP_403_FORBIDDEN
            )

        email = request.data.get("email", "").strip()
        if not email:
            return Response(
                {"detail": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.accounts.models import User as AppUser
        try:
            user_to_add = AppUser.objects.get(email=email)
        except AppUser.DoesNotExist:
            return Response(
                {"detail": f"No user found with email '{email}'"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return Response({"detail": "Organization not found"}, status=404)

        # Prevent duplicate membership
        if OrganizationMember.objects.filter(user=user_to_add, organization=org).exists():
            return Response(
                {"detail": "User is already a member of this organization"},
                status=status.HTTP_400_BAD_REQUEST
            )

        team_id = request.data.get("team_id")
        team = None
        if team_id:
            try:
                team = Team.objects.get(id=team_id, organization=org)
            except Team.DoesNotExist:
                return Response({"detail": "Team not found in this organization"}, status=404)
        else:
            team = Team.objects.filter(organization=org).first()

        OrganizationMember.objects.create(
            user=user_to_add,
            organization=org,
            team=team,
            role=OrganizationMember.MEMBER,  # integer 1
        )
        
        AuditLog.objects.create(
            actor=request.user,
            action="MEMBER_ADDED",
            description=f"User '{user_to_add.email}' was added as Member.",
            organization_id=org.id,
        )

        return Response(
            {"detail": f"{email} added to organization as Member"},
            status=status.HTTP_201_CREATED
        )

class TeamListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, org_id):
        if not has_permission(request.user, org_id, OrganizationMember.MEMBER):
            return Response({"detail": "Access denied"}, status=403)
            
        teams = Team.objects.filter(organization_id=org_id)
        serializer = TeamSerializer(teams, many=True)
        return Response(serializer.data)

    def post(self, request, org_id):
        if not has_permission(request.user, org_id, OrganizationMember.ADMIN):
            return Response({"detail": "Only admins can create teams"}, status=403)
            
        serializer = TeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        team = serializer.save(organization_id=org_id)
        
        AuditLog.objects.create(
            actor=request.user,
            action="TEAM_CREATED",
            description=f"Team '{team.name}' created.",
            organization_id=org_id,
        )
        return Response(TeamSerializer(team).data, status=status.HTTP_201_CREATED)

class AssignTeamAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, org_id, member_uuid):
        if not has_permission(request.user, org_id, OrganizationMember.ADMIN):
            return Response({"detail": "Only admins can assign teams"}, status=403)

        team_id = request.data.get("team_id")
        if not team_id:
            return Response({"detail": "team_id is required"}, status=400)

        try:
            member = OrganizationMember.objects.get(user__id=member_uuid, organization_id=org_id)
        except OrganizationMember.DoesNotExist:
            return Response({"detail": "Member not found"}, status=404)

        try:
            team = Team.objects.get(id=team_id, organization_id=org_id)
        except Team.DoesNotExist:
            return Response({"detail": "Team not found"}, status=404)

        member.team = team
        member.save()

        return Response({"detail": "Team assigned successfully"}, status=200)


class PermissionRequestListCreateAPIView(APIView):
    """
    GET  /api/organizations/<org_id>/permission-requests/
         List all permission requests for this org (admins see all, others see own).
    POST /api/organizations/<org_id>/permission-requests/
         Create a new permission escalation request.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, org_id):
        if not has_permission(request.user, org_id, OrganizationMember.MEMBER):
            return Response({"detail": "Access denied"}, status=403)

        user_role = get_user_role(request.user, org_id)

        if user_role >= OrganizationMember.ADMIN or getattr(request.user, 'is_super_admin', False):
            # Admins see all requests in the org
            qs = PermissionRequest.objects.filter(organization_id=org_id)
        else:
            # Regular members see only their own requests
            qs = PermissionRequest.objects.filter(
                organization_id=org_id,
                requester=request.user,
            )

        serializer = PermissionRequestSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request, org_id):
        # Must be a member of the organization
        if not has_permission(request.user, org_id, OrganizationMember.MEMBER):
            return Response({"detail": "Access denied"}, status=403)

        serializer = PermissionRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # The requested role must be strictly higher than the user's current base role
        try:
            member = OrganizationMember.objects.get(
                user=request.user, organization_id=org_id
            )
        except OrganizationMember.DoesNotExist:
            return Response({"detail": "Not a member of this organization"}, status=403)

        if data["requested_role"] <= member.role:
            return Response(
                {"detail": "Requested role must be higher than your current role."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # No duplicate pending requests for same org
        if PermissionRequest.objects.filter(
            requester=request.user,
            organization_id=org_id,
            status=PermissionRequest.STATUS_PENDING,
        ).exists():
            return Response(
                {"detail": "You already have a pending escalation request for this organization."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        perm_request = PermissionRequest.objects.create(
            requester=request.user,
            organization_id=org_id,
            requested_role=data["requested_role"],
            target_scope=data.get("target_scope", "organization"),
            requested_action=data.get("requested_action", ""),
            start_time=data["start_time"],
            end_time=data["end_time"],
            status=PermissionRequest.STATUS_PENDING,
        )

        AuditLog.objects.create(
            actor=request.user,
            action="PERM_ESCALATION_REQUESTED",
            description=(
                f"{request.user.email} requested escalation to "
                f"{perm_request.get_requested_role_label()} "
                f"(until {perm_request.end_time.isoformat()})."
            ),
            organization_id=org_id,
        )

        return Response(
            PermissionRequestSerializer(perm_request).data,
            status=status.HTTP_201_CREATED,
        )


class PermissionRequestApproveAPIView(APIView):
    """
    POST /api/organizations/<org_id>/permission-requests/<request_id>/approve/
    Approve a permission escalation request.
    Approver must have a role strictly HIGHER than the requested role.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, org_id, request_id):
        # Load the permission request – must belong to this org (cross-org blocking)
        try:
            perm_request = PermissionRequest.objects.get(
                id=request_id,
                organization_id=org_id,
            )
        except PermissionRequest.DoesNotExist:
            return Response({"detail": "Permission request not found"}, status=404)

        if perm_request.status != PermissionRequest.STATUS_PENDING:
            return Response(
                {"detail": f"Request is already {perm_request.status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Cannot approve own request
        if perm_request.requester == request.user:
            return Response(
                {"detail": "You cannot approve your own request."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Approver must have a role strictly higher than the requested role
        approver_role = get_user_role(request.user, org_id)
        if approver_role <= perm_request.requested_role:
            return Response(
                {"detail": "You must have a role higher than the requested role to approve."},
                status=status.HTTP_403_FORBIDDEN,
            )

        perm_request.status = PermissionRequest.STATUS_APPROVED
        perm_request.approved_by = request.user
        perm_request.save()

        AuditLog.objects.create(
            actor=request.user,
            action="PERM_ESCALATION_APPROVED",
            description=(
                f"Approved escalation of {perm_request.requester.email} to "
                f"{perm_request.get_requested_role_label()} "
                f"(until {perm_request.end_time.isoformat()})."
            ),
            organization_id=org_id,
        )

        return Response(PermissionRequestSerializer(perm_request).data)


class PermissionRequestRejectAPIView(APIView):
    """
    POST /api/organizations/<org_id>/permission-requests/<request_id>/reject/
    Reject a permission escalation request.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, org_id, request_id):
        try:
            perm_request = PermissionRequest.objects.get(
                id=request_id,
                organization_id=org_id,
            )
        except PermissionRequest.DoesNotExist:
            return Response({"detail": "Permission request not found"}, status=404)

        if perm_request.status != PermissionRequest.STATUS_PENDING:
            return Response(
                {"detail": f"Request is already {perm_request.status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Cannot reject own request
        if perm_request.requester == request.user:
            return Response(
                {"detail": "You cannot reject your own request."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Rejector must have a role strictly higher than the requested role
        rejector_role = get_user_role(request.user, org_id)
        if rejector_role <= perm_request.requested_role:
            return Response(
                {"detail": "You must have a role higher than the requested role to reject."},
                status=status.HTTP_403_FORBIDDEN,
            )

        perm_request.status = PermissionRequest.STATUS_REJECTED
        perm_request.approved_by = request.user  # track who handled it
        perm_request.save()

        AuditLog.objects.create(
            actor=request.user,
            action="PERM_ESCALATION_REJECTED",
            description=(
                f"Rejected escalation of {perm_request.requester.email} to "
                f"{perm_request.get_requested_role_label()}."
            ),
            organization_id=org_id,
        )

        return Response(PermissionRequestSerializer(perm_request).data)