from rest_framework.permissions import BasePermission
from apps.organizations.models import OrganizationMember

class IsOrganizationAdmin(BasePermission):
    def has_permission(self, request, view):
        org_id = view.kwargs.get("org_id")
        if not org_id or not request.user.is_authenticated:
            return False

        return OrganizationMember.objects.filter(
            user=request.user,
            organization_id=org_id,
            role="ADMIN"
        ).exists()