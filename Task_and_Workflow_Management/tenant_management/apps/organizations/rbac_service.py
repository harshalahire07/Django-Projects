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

def enforce_organization_isolation(queryset, organization_id, user=None):
    # Depending on the model of the queryset, filter it by the given organization
    model = queryset.model
    if hasattr(model, 'organization') or hasattr(model, 'organization_id'):
        queryset = queryset.filter(organization_id=organization_id)
    elif hasattr(model, 'project'):
        from apps.projects.models import Project
        # Models that relate to organization through project (like Task)
        queryset = queryset.filter(project__organization_id=organization_id)
    else:
        return queryset.none()
        
    # If the model is Task, apply visibility rules based on user role
    if model.__name__ == 'Task' and user is not None:
        role = get_user_role(user, organization_id)
        if role < OrganizationMember.MANAGER:
            try:
                member = OrganizationMember.objects.get(user=user, organization_id=organization_id)
                if role == OrganizationMember.MEMBER:
                    # MEMBER: Only tasks assigned to self
                    queryset = queryset.filter(assigned_to=user)
                elif role == OrganizationMember.PROJECT_MANAGER:
                    # PROJECT_MANAGER: Tasks within own team
                    team_members = OrganizationMember.objects.filter(
                        organization_id=organization_id, 
                        team=member.team
                    ).values_list('user', flat=True)
                    queryset = queryset.filter(assigned_to__in=team_members)
            except OrganizationMember.DoesNotExist:
                return queryset.none()
                
    return queryset
