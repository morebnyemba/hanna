# whatsappcrm_backend/paynow_integration/views.py

from rest_framework import viewsets, permissions
from .models import PaynowConfig
from .serializers import PaynowConfigSerializer

class PaynowConfigViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Paynow Configuration.
    There should only be one instance.
    """
    queryset = PaynowConfig.objects.all()
    serializer_class = PaynowConfigSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        # Ensure we always work with the first (and ideally only) config object
        return PaynowConfig.objects.all().order_by('id')

    def list(self, request, *args, **kwargs):
        # Return the first object, or an empty response if none exists
        instance = self.get_queryset().first()
        if instance:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        return Response({})

    def perform_create(self, serializer):
        # Ensure only one config exists
        if PaynowConfig.objects.exists():
            raise serializers.ValidationError("A Paynow configuration already exists.")
        serializer.save()