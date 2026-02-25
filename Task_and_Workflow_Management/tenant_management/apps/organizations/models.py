from django.db import models
from django.utils import timezone
from apps.accounts.models import User
import uuid
# Create your models here.

class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="teams")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("name", "organization")

    def __str__(self):
        return f"{self.name} - {self.organization.name}"

class OrganizationMember(models.Model):
    # ---------------------------------------------------------------------------
    # RBAC role hierarchy (higher integer = more authority)
    # SUPER_ADMIN (5) lives at the User level (User.is_super_admin), not here.
    # ---------------------------------------------------------------------------
    ADMIN           = 4
    MANAGER         = 3
    PROJECT_MANAGER = 2
    MEMBER          = 1

    ROLE_CHOICES = (
        (ADMIN,           "Admin"),
        (MANAGER,         "Manager"),
        (PROJECT_MANAGER, "Project Manager"),
        (MEMBER,          "Member"),
    )

    user         = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    team         = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="members", null=False)
    role         = models.IntegerField(choices=ROLE_CHOICES, default=MEMBER)

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "organization")

    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.get_role_display()})"

    # ------------------------------------------------------------------
    # Convenience helpers for role comparisons (use these in views/perms)
    # ------------------------------------------------------------------
    def is_admin(self):
        """True for any role >= ADMIN (i.e. admins only)."""
        return self.role >= self.ADMIN

    def is_manager_or_above(self):
        """True for MANAGER, ADMIN."""
        return self.role >= self.MANAGER

    def is_project_manager_or_above(self):
        """True for PROJECT_MANAGER, MANAGER, ADMIN."""
        return self.role >= self.PROJECT_MANAGER


class PermissionRequest(models.Model):
    """
    Time-bound permission escalation request.
    A user requests a higher role for a limited time window within an organization.
    Must be approved by someone with a role strictly higher than the requested role.
    """
    STATUS_PENDING  = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_REJECTED = "REJECTED"
    STATUS_EXPIRED  = "EXPIRED"

    STATUS_CHOICES = (
        (STATUS_PENDING,  "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_EXPIRED,  "Expired"),
    )

    ROLE_CHOICES = OrganizationMember.ROLE_CHOICES

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    requester = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="permission_requests",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="permission_requests",
    )

    requested_role = models.IntegerField(
        choices=OrganizationMember.ROLE_CHOICES,
        help_text="The role level the user wants to be temporarily elevated to.",
    )
    target_scope = models.CharField(
        max_length=255,
        blank=True,
        default="organization",
        help_text="Scope of escalation, e.g. 'organization', 'project:<id>'",
    )
    requested_action = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Description of why the escalation is needed.",
    )

    start_time = models.DateTimeField(
        help_text="When the elevated permission becomes active.",
    )
    end_time = models.DateTimeField(
        help_text="When the elevated permission expires.",
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_permission_requests",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        role_label = dict(OrganizationMember.ROLE_CHOICES).get(self.requested_role, self.requested_role)
        return f"{self.requester.email} → {role_label} ({self.status})"

    def is_active(self):
        """Return True if the request is approved and currently within the time window."""
        if self.status != self.STATUS_APPROVED:
            return False
        now = timezone.now()
        return self.start_time <= now <= self.end_time

    def is_expired(self):
        """Return True if the time window has passed."""
        return timezone.now() > self.end_time

    def get_requested_role_label(self):
        return dict(OrganizationMember.ROLE_CHOICES).get(self.requested_role, "Unknown")