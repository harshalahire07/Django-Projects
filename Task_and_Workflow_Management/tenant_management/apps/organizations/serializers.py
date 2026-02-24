from rest_framework import serializers
from .models import Organization, Team

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name")

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ("id", "name", "organization", "created_at")
        read_only_fields = ("id", "organization", "created_at")