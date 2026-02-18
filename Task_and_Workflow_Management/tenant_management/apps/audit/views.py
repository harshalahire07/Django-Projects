from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from .models import AuditLog
from .serializers import AuditLogSerializer
from apps.organizations.models import OrganizationMember


class AuditLogListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, org_id):
        is_admin = OrganizationMember.objects.filter(
            user=request.user,
            organization_id=org_id,
            role="ADMIN"
        ).exists()

        if not is_admin:
            return Response(
                {"detail": "Only organization admins can view audit logs"},
                status=status.HTTP_403_FORBIDDEN
            )

        logs = AuditLog.objects.filter(
            organization_id=org_id
        ).order_by("-created_at")

        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
