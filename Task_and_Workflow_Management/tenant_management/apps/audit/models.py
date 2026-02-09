from django.db import models
from django.conf import settings
import uuid

class AuditLog(models.Model):
    ACTION_CHOICES = (
        ("TASK_ASSIGNED", "Task Assigned"),
        ("TASK_REASSIGNED", "Task Reassigned"),
        ("STATUS_CHANGED", "Status Changed"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_actions"
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()

    organization_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} by {self.actor}"
