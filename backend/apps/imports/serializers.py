"""
Imports serializers.
"""

from rest_framework import serializers
from apps.accounts.serializers import UserPublicSerializer
from .models import ImportJob, ImportAnomaly


class ImportAnomalySerializer(serializers.ModelSerializer):
    resolved_by = UserPublicSerializer(read_only=True)

    class Meta:
        model = ImportAnomaly
        fields = [
            "id", "row_number", "raw_data",
            "anomaly_type", "severity", "description",
            "recommendation", "action_taken", "status",
            "resolved_by", "resolved_at",
        ]
        read_only_fields = ["id", "resolved_by", "resolved_at"]


class ImportJobSerializer(serializers.ModelSerializer):
    uploaded_by = UserPublicSerializer(read_only=True)
    anomaly_summary = serializers.SerializerMethodField()

    class Meta:
        model = ImportJob
        fields = [
            "id", "group", "uploaded_by", "file_name", "file_hash",
            "status", "rows_total", "rows_imported", "rows_skipped",
            "anomalies_count", "error_message", "anomaly_summary",
            "created_at", "completed_at",
        ]
        read_only_fields = fields

    def get_anomaly_summary(self, obj):
        return {
            "errors": obj.anomalies.filter(severity=ImportAnomaly.Severity.ERROR).count(),
            "warnings": obj.anomalies.filter(severity=ImportAnomaly.Severity.WARNING).count(),
            "info": obj.anomalies.filter(severity=ImportAnomaly.Severity.INFO).count(),
            "pending": obj.anomalies.filter(status=ImportAnomaly.AnomalyStatus.PENDING).count(),
        }


class ImportUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    group_id = serializers.UUIDField()

    def validate_file(self, value):
        if not value.name.endswith(".csv"):
            raise serializers.ValidationError("Only CSV files are accepted.")
        if value.size > 10 * 1024 * 1024:  # 10MB
            raise serializers.ValidationError("File size cannot exceed 10MB.")
        return value


class AnomalyResolveSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["APPROVE", "REJECT"])
    action_taken = serializers.CharField(required=False, allow_blank=True)
