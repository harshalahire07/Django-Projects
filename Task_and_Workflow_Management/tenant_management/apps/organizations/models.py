from django.db import models
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