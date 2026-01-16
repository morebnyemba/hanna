# whatsappcrm_backend/installation_systems/branch_urls.py
"""
URL Configuration for Branch API
Installer allocation and performance metrics for retailer branches.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .branch_views import (
    BranchInstallerAssignmentViewSet,
    BranchInstallerAvailabilityViewSet,
    BranchInstallerManagementViewSet,
    BranchPerformanceMetricsViewSet,
)

app_name = 'branch_api'

router = DefaultRouter()

# Installer assignment management
router.register(
    r'installer-assignments',
    BranchInstallerAssignmentViewSet,
    basename='installer-assignment'
)

# Installer availability
router.register(
    r'installer-availability',
    BranchInstallerAvailabilityViewSet,
    basename='installer-availability'
)

# Installer management
router.register(
    r'installers',
    BranchInstallerManagementViewSet,
    basename='installer'
)

# Performance metrics
router.register(
    r'metrics',
    BranchPerformanceMetricsViewSet,
    basename='metrics'
)

urlpatterns = [
    path('', include(router.urls)),
]
