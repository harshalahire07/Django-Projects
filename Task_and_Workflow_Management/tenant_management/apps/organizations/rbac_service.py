from django.utils import timezone
from apps.organizations.models import OrganizationMember


def get_user_role(user, organization_id):
    """
    Return the effective role for a user in an organization.
    Considers: super_admin flag > active permission escalation > base membership role.
    """
    if getattr(user, 'is_super_admin', False):
        return float('inf')  # Superadmin effectively has highest role
    try:
        member = OrganizationMember.objects.get(user=user, organization_id=organization_id)
        base_role = member.role
    except OrganizationMember.DoesNotExist:
        return 0

    # Check for an active, approved time-bound permission escalation
    escalated_role = get_escalated_role(user, organization_id)
    return max(base_role, escalated_role)


def get_escalated_role(user, organization_id):
    """
    Return the highest active (approved + within time window) escalated role
    for a user in an organization. Returns 0 if none found.
    Also auto-expires any approved requests whose end_time has passed.
    """
    from apps.organizations.models import PermissionRequest

    now = timezone.now()

    # Auto-expire any approved requests that have passed their end_time
    expired_qs = PermissionRequest.objects.filter(
        requester=user,
        organization_id=organization_id,
        status=PermissionRequest.STATUS_APPROVED,
        end_time__lt=now,
    )
    if expired_qs.exists():
        from apps.audit.models import AuditLog
        for req in expired_qs:
            AuditLog.objects.create(
                actor=user,
                action="PERM_ESCALATION_EXPIRED",
                description=(
                    f"Permission escalation to "
                    f"{req.get_requested_role_label()} for {user.email} expired."
                ),
                organization_id=organization_id,
            )
        expired_qs.update(status=PermissionRequest.STATUS_EXPIRED)

    # Find the highest active escalation
    active = PermissionRequest.objects.filter(
        requester=user,
        organization_id=organization_id,
        status=PermissionRequest.STATUS_APPROVED,
        start_time__lte=now,
        end_time__gte=now,
    ).order_by('-requested_role').first()

    return active.requested_role if active else 0


def has_permission(user, organization_id, required_level):
    """Check if a user's effective role meets the required level."""
    return get_user_role(user, organization_id) >= required_level


def enforce_organization_isolation(queryset, organization_id, user=None):
    """
    Filter a queryset to only include records belonging to the given organization.
    For Task models, also apply visibility rules based on effective user role
    (including any active permission escalations).
    """
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
