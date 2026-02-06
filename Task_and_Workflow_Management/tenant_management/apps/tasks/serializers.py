from rest_framework import serializers
from .models import Task
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
    assigned_to = serializers.IntegerField()

    def validate_assigned_to(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")