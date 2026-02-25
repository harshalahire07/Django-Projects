from rest_framework import serializers
from .models import Task, TaskActivity
from apps.accounts.models import User


class TaskSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "status",
            "assigned_to",
            "assigned_at",
            "completed_at",
            "duration",
        )
        read_only_fields = ("status", "assigned_at", "completed_at", "duration")

    def get_duration(self, obj):
        """
        Compute assigned_at → completed_at duration dynamically.
        Returns None if the task isn't completed or wasn't assigned.
        Formatting:
          - < 24h  → "Xh Ym"
          - >= 24h → "Xd Yh"
        """
        if not obj.assigned_at:
            return None
        if not obj.completed_at:
            return "In progress"

        delta = obj.completed_at - obj.assigned_at
        total_seconds = int(delta.total_seconds())

        if total_seconds < 0:
            return None

        total_minutes = total_seconds // 60
        total_hours = total_minutes // 60
        remaining_minutes = total_minutes % 60
        days = total_hours // 24
        remaining_hours = total_hours % 24

        if days >= 1:
            if remaining_hours == 0:
                return f"{days}d"
            return f"{days}d {remaining_hours}h"
        else:
            if total_hours == 0:
                return f"{remaining_minutes}m" if remaining_minutes > 0 else "< 1m"
            if remaining_minutes == 0:
                return f"{total_hours}h"
            return f"{total_hours}h {remaining_minutes}m"


class TaskAssignSerializer(serializers.Serializer):
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

class TaskStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Task.STATUS_CHOICES)
    
class TaskActivitySerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True)

    class Meta:
        model = TaskActivity
        fields = (
            "id",
            "activity_type",
            "message",
            "actor_email",
            "created_at",
        )
