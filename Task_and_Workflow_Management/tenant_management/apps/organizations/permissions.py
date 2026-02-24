from rest_framework.permissions import BasePermission
from apps.organizations.models import OrganizationMember
from apps.organizations.rbac_service import has_permission as rbac_has_permission


class IsOrganizationAdmin(BasePermission):
    """
    Grants access only to members whose role >= ADMIN (integer 4).
    This covers ADMIN (4) and any future roles above it.
    """
    def has_permission(self, request, view):
        org_id = view.kwargs.get("org_id")
        if not org_id or not request.user.is_authenticated:
            return False

        return rbac_has_permission(request.user, org_id, OrganizationMember.ADMIN)


class IsOrganizationManager(BasePermission):
    """
    Grants access to members whose role >= MANAGER (integer 3).
    Covers MANAGER (3) and ADMIN (4).
    """
    def has_permission(self, request, view):
        org_id = view.kwargs.get("org_id")
        if not org_id or not request.user.is_authenticated:
            return False

        return rbac_has_permission(request.user, org_id, OrganizationMember.MANAGER)


class IsOrganizationProjectManager(BasePermission):
    """
    Grants access to members whose role >= PROJECT_MANAGER (integer 2).
    Covers PROJECT_MANAGER (2), MANAGER (3), and ADMIN (4).
    """
    def has_permission(self, request, view):
        org_id = view.kwargs.get("org_id")
        if not org_id or not request.user.is_authenticated:
            return False

        return rbac_has_permission(request.user, org_id, OrganizationMember.PROJECT_MANAGER)