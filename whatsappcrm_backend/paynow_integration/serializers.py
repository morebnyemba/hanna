# whatsappcrm_backend/paynow_integration/serializers.py

from rest_framework import serializers
from .models import PaynowConfig

class PaynowConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaynowConfig
        fields = ['id', 'integration_id', 'integration_key', 'api_base_url']
        read_only_fields = ['id']
        extra_kwargs = {
            'integration_key': {
                'write_only': True,
                'style': {'input_type': 'password'},
                'help_text': "Leave empty if not changing."
            },
        }
