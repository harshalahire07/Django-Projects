from rest_framework import serializers
from .models import Task, TaskActivity
from apps.accounts.models import User
class TaskSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "status",
            "assigned_to",
        )
        read_only_fields = ("status",)

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
