from rest_framework.permissions import BasePermission
from apps.organizations.models import OrganizationMember


class IsOrganizationAdmin(BasePermission):
    """
    Grants access only to members whose role >= ADMIN (integer 4).
    This covers ADMIN (4) and any future roles above it.
    """
    def has_permission(self, request, view):
        org_id = view.kwargs.get("org_id")
        if not org_id or not request.user.is_authenticated:
            return False

        return OrganizationMember.objects.filter(
            user=request.user,
            organization_id=org_id,
            role__gte=OrganizationMember.ADMIN,
        ).exists()


class IsOrganizationManager(BasePermission):
    """
    Grants access to members whose role >= MANAGER (integer 3).
    Covers MANAGER (3) and ADMIN (4).
    """
    def has_permission(self, request, view):
        org_id = view.kwargs.get("org_id")
        if not org_id or not request.user.is_authenticated:
            return False

        return OrganizationMember.objects.filter(
            user=request.user,
            organization_id=org_id,
            role__gte=OrganizationMember.MANAGER,
        ).exists()


class IsOrganizationProjectManager(BasePermission):
    """
    Grants access to members whose role >= PROJECT_MANAGER (integer 2).
    Covers PROJECT_MANAGER (2), MANAGER (3), and ADMIN (4).
    """
    def has_permission(self, request, view):
        org_id = view.kwargs.get("org_id")
        if not org_id or not request.user.is_authenticated:
            return False

        return OrganizationMember.objects.filter(
            user=request.user,
            organization_id=org_id,
            role__gte=OrganizationMember.PROJECT_MANAGER,
        ).exists()