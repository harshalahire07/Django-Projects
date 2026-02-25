from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.projects.models import Project
from apps.accounts.models import User
import uuid
# Create your models here.
class Task(models.Model):
    STATUS_TODO = "TODO"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_DONE = "DONE"

    STATUS_CHOICES = (
        (STATUS_TODO, "To Do"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_DONE, "Done"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_TODO
    )

    assigned_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-set assigned_at when a task gets assigned
        if self.assigned_to_id:
            if self.pk:
                try:
                    old = Task.objects.filter(pk=self.pk).values_list('assigned_to_id', flat=True).first()
                except Exception:
                    old = None
                if old != self.assigned_to_id:
                    self.assigned_at = timezone.now()
            else:
                # New task being created with an assignee
                self.assigned_at = timezone.now()
        else:
            # Unassigned – clear the timestamp
            self.assigned_at = None

        # Auto-set completed_at when status becomes DONE
        if self.status == self.STATUS_DONE and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != self.STATUS_DONE:
            self.completed_at = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.project.name})"
class TaskActivity(models.Model):
    ACTIVITY_CHOICES = (
        ("ASSIGNED", "Assigned"),
        ("REASSIGNED", "Reassigned"),
        ("STATUS_CHANGED", "Status Changed"),
        ("COMMENT", "Comment"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="activities"
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    activity_type = models.CharField(
        max_length=50,
        choices=ACTIVITY_CHOICES
    )

    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.activity_type} - {self.task.title}"
