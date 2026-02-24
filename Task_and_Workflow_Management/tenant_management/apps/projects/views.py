from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import Project
from .serializers import ProjectSerializer
from apps.organizations.models import OrganizationMember
from apps.organizations.permissions import IsOrganizationAdmin
from apps.audit.models import AuditLog
from apps.organizations.rbac_service import has_permission, enforce_organization_isolation
class CreateProjectAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrganizationAdmin]

    def post(self, request, org_id):
        serializer = ProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = serializer.save(organization_id=org_id)

        AuditLog.objects.create(
            actor=request.user,
            action="PROJECT_CREATED",
            description=f"Project '{project.name}' created.",
            organization_id=org_id,
        )

        return Response(
            ProjectSerializer(project).data,
            status=status.HTTP_201_CREATED
        )

class OrganizationProjectsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, org_id):
        if not has_permission(request.user, org_id, OrganizationMember.MEMBER):
            return Response(
                {"detail": "Access denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        projects = enforce_organization_isolation(Project.objects.all(), org_id).filter(organization_id=org_id)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)