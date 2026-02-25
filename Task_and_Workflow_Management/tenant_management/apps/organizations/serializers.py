from rest_framework import serializers
from django.utils import timezone
from .models import Organization, Team, PermissionRequest, OrganizationMember


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name")

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ("id", "name", "organization", "created_at")
        read_only_fields = ("id", "organization", "created_at")


class PermissionRequestSerializer(serializers.ModelSerializer):
    requester_email = serializers.EmailField(source="requester.email", read_only=True)
    approved_by_email = serializers.SerializerMethodField()
    requested_role_label = serializers.SerializerMethodField()
    is_currently_active = serializers.SerializerMethodField()

    class Meta:
        model = PermissionRequest
        fields = (
            "id",
            "requester",
            "requester_email",
            "organization",
            "requested_role",
            "requested_role_label",
            "target_scope",
            "requested_action",
            "start_time",
            "end_time",
            "approved_by",
            "approved_by_email",
            "status",
            "is_currently_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id", "requester", "requester_email", "organization",
            "approved_by", "approved_by_email", "status",
            "is_currently_active", "created_at", "updated_at",
        )

    def get_approved_by_email(self, obj):
        return obj.approved_by.email if obj.approved_by else None

    def get_requested_role_label(self, obj):
        return obj.get_requested_role_label()

    def get_is_currently_active(self, obj):
        return obj.is_active()


class PermissionRequestCreateSerializer(serializers.Serializer):
    requested_role = serializers.IntegerField()
    target_scope = serializers.CharField(required=False, default="organization")
    requested_action = serializers.CharField(required=False, default="", allow_blank=True)
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()

    def validate_requested_role(self, value):
        valid_roles = [r[0] for r in OrganizationMember.ROLE_CHOICES]
        if value not in valid_roles:
            raise serializers.ValidationError(
                f"Invalid role. Must be one of: {valid_roles}"
            )
        return value

    def validate(self, data):
        if data["end_time"] <= data["start_time"]:
            raise serializers.ValidationError(
                {"end_time": "End time must be after start time."}
            )
        if data["end_time"] <= timezone.now():
            raise serializers.ValidationError(
                {"end_time": "End time must be in the future."}
            )
        return data