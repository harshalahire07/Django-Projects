from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import Organization, OrganizationMember
from .serializers import OrganizationSerializer
from apps.audit.models import AuditLog
from apps.organizations.rbac_service import has_permission
# Create your views here.
class CreateOrganizationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = OrganizationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from django.db import transaction

        with transaction.atomic():
            organization = serializer.save()

            OrganizationMember.objects.create(
                user=request.user,
                organization=organization,
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

        OrganizationMember.objects.create(
            user=user_to_add,
            organization=org,
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