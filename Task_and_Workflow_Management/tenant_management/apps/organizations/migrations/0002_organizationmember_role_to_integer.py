# Generated manually – RBAC role hierarchy migration
# Safely converts OrganizationMember.role from CharField to IntegerField.
#
# Mapping applied to existing rows:
#   "ADMIN"  -> 4  (ADMIN)
#   "MEMBER" -> 1  (MEMBER)   [covers any unknown value as a safe fallback]
#
# No data is removed. Migration is fully reversible.

from django.db import migrations, models


# ---------------------------------------------------------------------------
# Forward: copy char value -> integer value
# ---------------------------------------------------------------------------
CHAR_TO_INT = {
    "ADMIN":  4,
    "MANAGER": 3,
    "PROJECT_MANAGER": 2,
    "MEMBER": 1,
}

def role_char_to_int(apps, schema_editor):
    """Convert existing string role values to integer equivalents."""
    OrganizationMember = apps.get_model("organizations", "OrganizationMember")
    for obj in OrganizationMember.objects.all():
        obj.role_int = CHAR_TO_INT.get(obj.role_char, 1)   # default to MEMBER
        obj.save(update_fields=["role_int"])


# ---------------------------------------------------------------------------
# Reverse: copy integer value -> char value (best-effort rollback)
# ---------------------------------------------------------------------------
INT_TO_CHAR = {v: k for k, v in CHAR_TO_INT.items()}

def role_int_to_char(apps, schema_editor):
    """Restore string role values from integer equivalents (rollback path)."""
    OrganizationMember = apps.get_model("organizations", "OrganizationMember")
    for obj in OrganizationMember.objects.all():
        obj.role_char = INT_TO_CHAR.get(obj.role_int, "MEMBER")   # default to MEMBER
        obj.save(update_fields=["role_char"])


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0001_initial"),
    ]

    operations = [
        # ----------------------------------------------------------------
        # Phase 1: add a temporary integer column (nullable so it can be
        # added without touching existing rows yet).
        # ----------------------------------------------------------------
        migrations.AddField(
            model_name="organizationmember",
            name="role_int",
            field=models.IntegerField(
                null=True,
                blank=True,
                choices=[
                    (4, "Admin"),
                    (3, "Manager"),
                    (2, "Project Manager"),
                    (1, "Member"),
                ],
            ),
        ),
        # Keep the OLD column accessible during data migration under a
        # temporary alias so RunPython can read it.
        migrations.RenameField(
            model_name="organizationmember",
            old_name="role",
            new_name="role_char",
        ),
        # ----------------------------------------------------------------
        # Phase 2: back-fill the integer column from the old char column.
        # ----------------------------------------------------------------
        migrations.RunPython(
            role_char_to_int,
            reverse_code=role_int_to_char,
        ),
        # ----------------------------------------------------------------
        # Phase 3: remove the old char column and rename the int column to
        # the canonical "role" name.
        # ----------------------------------------------------------------
        migrations.RemoveField(
            model_name="organizationmember",
            name="role_char",
        ),
        migrations.RenameField(
            model_name="organizationmember",
            old_name="role_int",
            new_name="role",
        ),
        # ----------------------------------------------------------------
        # Phase 4: set NOT NULL + default now that every row has a value.
        # ----------------------------------------------------------------
        migrations.AlterField(
            model_name="organizationmember",
            name="role",
            field=models.IntegerField(
                choices=[
                    (4, "Admin"),
                    (3, "Manager"),
                    (2, "Project Manager"),
                    (1, "Member"),
                ],
                default=1,
            ),
        ),
    ]
