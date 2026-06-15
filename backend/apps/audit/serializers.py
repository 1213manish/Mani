from rest_framework import serializers
from apps.accounts.serializers import UserPublicSerializer
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor = UserPublicSerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id", "actor", "action", "resource_type", "resource_id",
            "resource_repr", "before_state", "after_state",
            "ip_address", "extra", "created_at",
        ]
        read_only_fields = fields
