from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import Project
from .serializers import ProjectSerializer
from apps.organizations.models import OrganizationMember
from apps.organizations.permissions import IsOrganizationAdmin
# Create your views here.
class CreateProjectAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrganizationAdmin]

    def post(self, request, org_id):
        serializer = ProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = serializer.save(organization_id=org_id)

        return Response(
            ProjectSerializer(project).data,
            status=status.HTTP_201_CREATED
        )

class OrganizationProjectsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, org_id):
        is_member = OrganizationMember.objects.filter(
            user=request.user,
            organization_id=org_id
        ).exists()

        if not is_member:
            return Response(
                {"detail": "Access denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        projects = Project.objects.filter(organization_id=org_id)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)