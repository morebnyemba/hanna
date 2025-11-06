from rest_framework import generics, permissions
from .models import Manufacturer
from .serializers import ManufacturerSerializer

class ManufacturerCreateView(generics.CreateAPIView):
    queryset = Manufacturer.objects.all()
    serializer_class = ManufacturerSerializer
    permission_classes = [permissions.IsAdminUser]
