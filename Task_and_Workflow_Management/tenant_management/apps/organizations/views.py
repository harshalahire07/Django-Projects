from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import Organization, OrganizationMember
from .serializers import OrganizationSerializer
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
                role="ADMIN"
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
        # Ensure requesting user belongs to the organization
        is_member = OrganizationMember.objects.filter(
            user=request.user,
            organization_id=org_id
        ).exists()

        if not is_member:
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
                "role": member.role
            }
            for member in members
        ]

        return Response(data)