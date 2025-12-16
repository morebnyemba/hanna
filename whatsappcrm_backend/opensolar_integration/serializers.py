# whatsappcrm_backend/opensolar_integration/serializers.py

from rest_framework import serializers
from .models import (
    OpenSolarConfig,
    OpenSolarProject,
    OpenSolarWebhookLog,
    OpenSolarSyncLog
)


class OpenSolarConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpenSolarConfig
        fields = [
            'id',
            'organization_name',
            'org_id',
            'api_base_url',
            'webhook_url',
            'auto_sync_enabled',
            'webhook_enabled',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class OpenSolarProjectSerializer(serializers.ModelSerializer):
    installation_request_id = serializers.IntegerField(
        source='installation_request.id',
        read_only=True
    )
    customer_name = serializers.CharField(
        source='installation_request.full_name',
        read_only=True
    )
    
    class Meta:
        model = OpenSolarProject
        fields = [
            'id',
            'installation_request_id',
            'customer_name',
            'opensolar_project_id',
            'opensolar_contact_id',
            'project_name',
            'project_status',
            'system_size_kw',
            'proposal_url',
            'proposal_sent_at',
            'contract_signed_at',
            'installation_scheduled_date',
            'sync_status',
            'last_synced_at',
            'sync_error_message',
            'sync_retry_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'opensolar_project_id',
            'opensolar_contact_id',
            'last_synced_at',
            'created_at',
            'updated_at'
        ]


class OpenSolarWebhookLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpenSolarWebhookLog
        fields = [
            'id',
            'event_type',
            'opensolar_project_id',
            'payload',
            'headers',
            'status',
            'processed_at',
            'error_message',
            'created_at'
        ]
        read_only_fields = ['created_at', 'processed_at']


class OpenSolarSyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpenSolarSyncLog
        fields = [
            'id',
            'project',
            'sync_type',
            'status',
            'request_data',
            'response_data',
            'error_message',
            'started_at',
            'completed_at',
            'duration_ms'
        ]
        read_only_fields = ['started_at', 'completed_at', 'duration_ms']
