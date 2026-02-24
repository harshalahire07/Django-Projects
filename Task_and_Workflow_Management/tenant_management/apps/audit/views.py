from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from .models import AuditLog
from .serializers import AuditLogSerializer
from apps.organizations.models import OrganizationMember
from apps.organizations.rbac_service import has_permission, enforce_organization_isolation


class AuditLogListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, org_id):
        if not has_permission(request.user, org_id, OrganizationMember.ADMIN):
            return Response(
                {"detail": "Only organization admins can view audit logs"},
                status=status.HTTP_403_FORBIDDEN
            )

        logs = enforce_organization_isolation(AuditLog.objects.all(), org_id).order_by("-created_at")

        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
