from apps.organizations.models import OrganizationMember

def get_user_role(user, organization_id):
    if getattr(user, 'is_super_admin', False):
        return float('inf')  # Superadmin effectively has highest role
    try:
        member = OrganizationMember.objects.get(user=user, organization_id=organization_id)
        return member.role
    except OrganizationMember.DoesNotExist:
        return 0

def has_permission(user, organization_id, required_level):
    return get_user_role(user, organization_id) >= required_level

def enforce_organization_isolation(queryset, organization_id):
    # Depending on the model of the queryset, filter it by the given organization
    model = queryset.model
    if hasattr(model, 'organization') or hasattr(model, 'organization_id'):
        return queryset.filter(organization_id=organization_id)
    elif hasattr(model, 'project'):
        from apps.projects.models import Project
        # Models that relate to organization through project (like Task)
        return queryset.filter(project__organization_id=organization_id)
    return queryset.none()
