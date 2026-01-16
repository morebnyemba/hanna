# whatsappcrm_backend/installation_systems/branch_serializers.py
"""
Serializers for branch installer allocation and scheduling.
"""

from rest_framework import serializers
from .branch_models import InstallerAssignment, InstallerAvailability
from .models import InstallationSystemRecord
from warranty.models import Technician
from users.models import RetailerBranch
from django.contrib.auth.models import User


class InstallerSummarySerializer(serializers.ModelSerializer):
    """Lightweight installer info for listing"""
    name = serializers.SerializerMethodField()
    specialization = serializers.CharField(read_only=True)
    contact_phone = serializers.CharField(read_only=True)
    technician_type = serializers.CharField(source='get_technician_type_display', read_only=True)
    
    class Meta:
        model = Technician
        fields = ['id', 'name', 'specialization', 'contact_phone', 'technician_type']
    
    def get_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class InstallationSummarySerializer(serializers.ModelSerializer):
    """Lightweight installation info for assignments"""
    customer_name = serializers.SerializerMethodField()
    installation_type_display = serializers.CharField(source='get_installation_type_display', read_only=True)
    status_display = serializers.CharField(source='get_installation_status_display', read_only=True)
    
    class Meta:
        model = InstallationSystemRecord
        fields = [
            'id', 'short_id', 'customer_name', 'installation_type', 
            'installation_type_display', 'installation_status', 'status_display',
            'installation_address', 'system_size', 'capacity_unit'
        ]
    
    def get_customer_name(self, obj):
        return obj.customer.get_full_name() or str(obj.customer.contact.whatsapp_id)


class InstallerAssignmentSerializer(serializers.ModelSerializer):
    """Full installer assignment serializer"""
    installer_details = InstallerSummarySerializer(source='installer', read_only=True)
    installation_details = InstallationSummarySerializer(source='installation_record', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    assigned_by_name = serializers.SerializerMethodField()
    actual_duration_hours = serializers.DecimalField(max_digits=4, decimal_places=1, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = InstallerAssignment
        fields = [
            'id', 'installation_record', 'installer', 'branch',
            'scheduled_date', 'scheduled_start_time', 'scheduled_end_time',
            'estimated_duration_hours', 'status', 'status_display',
            'actual_start_time', 'actual_end_time', 'actual_duration_hours',
            'notes', 'completion_notes', 'customer_feedback',
            'customer_satisfaction_rating', 'is_overdue',
            'assigned_by', 'assigned_by_name',
            'installer_details', 'installation_details',
            'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'assigned_by', 'created_at', 'updated_at', 'completed_at',
            'actual_duration_hours', 'is_overdue'
        ]
    
    def get_assigned_by_name(self, obj):
        if obj.assigned_by:
            return obj.assigned_by.get_full_name() or obj.assigned_by.username
        return None


class InstallerAssignmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating assignments"""
    
    class Meta:
        model = InstallerAssignment
        fields = [
            'installation_record', 'installer', 'scheduled_date',
            'scheduled_start_time', 'scheduled_end_time',
            'estimated_duration_hours', 'notes'
        ]
    
    def validate(self, data):
        """Validate assignment data"""
        # Check if installer already has an assignment for this date/time
        installer = data.get('installer')
        scheduled_date = data.get('scheduled_date')
        scheduled_start = data.get('scheduled_start_time')
        scheduled_end = data.get('scheduled_end_time')
        
        if scheduled_start and scheduled_end and scheduled_start >= scheduled_end:
            raise serializers.ValidationError({
                'scheduled_end_time': 'End time must be after start time'
            })
        
        # Check for conflicts
        conflicts = InstallerAssignment.objects.filter(
            installer=installer,
            scheduled_date=scheduled_date,
            status__in=[
                InstallerAssignment.AssignmentStatus.PENDING,
                InstallerAssignment.AssignmentStatus.CONFIRMED,
                InstallerAssignment.AssignmentStatus.IN_PROGRESS
            ]
        )
        
        # If we have time ranges, check for overlaps
        if scheduled_start and scheduled_end and conflicts.exists():
            for conflict in conflicts:
                if conflict.scheduled_start_time and conflict.scheduled_end_time:
                    # Check for time overlap
                    if not (scheduled_end <= conflict.scheduled_start_time or 
                            scheduled_start >= conflict.scheduled_end_time):
                        raise serializers.ValidationError({
                            'scheduled_date': f'Installer already has an assignment during this time on {scheduled_date}'
                        })
        
        return data


class InstallerAvailabilitySerializer(serializers.ModelSerializer):
    """Installer availability serializer"""
    installer_details = InstallerSummarySerializer(source='installer', read_only=True)
    availability_type_display = serializers.CharField(source='get_availability_type_display', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = InstallerAvailability
        fields = [
            'id', 'installer', 'date', 'start_time', 'end_time',
            'availability_type', 'availability_type_display', 'notes',
            'created_by', 'created_by_name', 'installer_details',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None


class InstallerScheduleSerializer(serializers.Serializer):
    """Serializer for installer schedule view"""
    date = serializers.DateField()
    assignments = InstallerAssignmentSerializer(many=True)
    availability = InstallerAvailabilitySerializer(many=True)
    is_available = serializers.BooleanField()
    total_scheduled_hours = serializers.DecimalField(max_digits=4, decimal_places=1)


class AvailableInstallerSerializer(serializers.Serializer):
    """Serializer for listing available installers"""
    installer = InstallerSummarySerializer()
    assignments_count = serializers.IntegerField()
    available_dates = serializers.ListField(child=serializers.DateField())
    next_available_date = serializers.DateField()
    current_workload = serializers.IntegerField()
