from rest_framework import serializers
from .models import InstallationSystemRecord, CommissioningChecklistTemplate, InstallationChecklistEntry
from customer_data.models import CustomerProfile, Order, InstallationRequest
from warranty.models import Technician, Warranty
from customer_data.models import JobCard
from products_and_services.models import SerializedItem


class CommissioningChecklistTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for CommissioningChecklistTemplate model.
    """
    checklist_type_display = serializers.CharField(source='get_checklist_type_display', read_only=True)
    installation_type_display = serializers.CharField(source='get_installation_type_display', read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CommissioningChecklistTemplate
        fields = [
            'id',
            'name',
            'checklist_type',
            'checklist_type_display',
            'installation_type',
            'installation_type_display',
            'description',
            'items',
            'is_active',
            'item_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_item_count(self, obj):
        """Get count of items in the checklist"""
        return len(obj.items) if obj.items else 0
    
    def validate_items(self, value):
        """
        Validate checklist items structure.
        Each item should have: id, title, required fields.
        """
        if not isinstance(value, list):
            raise serializers.ValidationError("Items must be a list")
        
        for idx, item in enumerate(value):
            if not isinstance(item, dict):
                raise serializers.ValidationError(f"Item {idx} must be a dictionary")
            
            # Check required fields
            required_fields = ['id', 'title', 'required']
            for field in required_fields:
                if field not in item:
                    raise serializers.ValidationError(
                        f"Item {idx} missing required field: {field}"
                    )
        
        return value


class InstallationChecklistEntrySerializer(serializers.ModelSerializer):
    """
    Serializer for InstallationChecklistEntry model.
    """
    template_details = serializers.SerializerMethodField()
    installation_record_short_id = serializers.SerializerMethodField()
    technician_name = serializers.SerializerMethodField()
    completion_status_display = serializers.CharField(source='get_completion_status_display', read_only=True)
    
    class Meta:
        model = InstallationChecklistEntry
        fields = [
            'id',
            'installation_record',
            'installation_record_short_id',
            'template',
            'template_details',
            'technician',
            'technician_name',
            'completed_items',
            'completion_status',
            'completion_status_display',
            'completion_percentage',
            'started_at',
            'completed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'completion_percentage', 'created_at', 'updated_at']
    
    def get_template_details(self, obj):
        """Get template details"""
        return {
            'id': obj.template.id,
            'name': obj.template.name,
            'checklist_type': obj.template.checklist_type,
            'checklist_type_display': obj.template.get_checklist_type_display(),
            'items': obj.template.items,
        }
    
    def get_installation_record_short_id(self, obj):
        """Get shortened ISR ID"""
        return f"ISR-{str(obj.installation_record.id)[:8]}"
    
    def get_technician_name(self, obj):
        """Get technician name"""
        if obj.technician:
            return obj.technician.user.get_full_name() or obj.technician.user.username
        return None
    
    def validate_completed_items(self, value):
        """Validate completed items structure"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("completed_items must be a dictionary")
        return value
    
    def update(self, instance, validated_data):
        """
        Update instance and recalculate completion status.
        """
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Recalculate completion status
        instance.update_completion_status()
        instance.save()
        
        return instance


class InstallationChecklistEntryCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new checklist entries.
    """
    class Meta:
        model = InstallationChecklistEntry
        fields = [
            'installation_record',
            'template',
            'technician',
        ]
    
    def create(self, validated_data):
        """
        Create new checklist entry with initial status.
        """
        instance = InstallationChecklistEntry.objects.create(**validated_data)
        instance.update_completion_status()
        instance.save()
        return instance


class InstallationSystemRecordListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing installation system records.
    Used in list views to minimize data transfer.
    """
    customer_name = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()
    order_number = serializers.CharField(source='order.order_number', read_only=True, allow_null=True)
    installation_type_display = serializers.CharField(source='get_installation_type_display', read_only=True)
    system_classification_display = serializers.CharField(source='get_system_classification_display', read_only=True)
    installation_status_display = serializers.CharField(source='get_installation_status_display', read_only=True)
    short_id = serializers.SerializerMethodField()
    
    class Meta:
        model = InstallationSystemRecord
        fields = [
            'id',
            'short_id',
            'customer',
            'customer_name',
            'customer_phone',
            'order',
            'order_number',
            'installation_type',
            'installation_type_display',
            'system_classification',
            'system_classification_display',
            'system_size',
            'capacity_unit',
            'installation_status',
            'installation_status_display',
            'installation_date',
            'commissioning_date',
            'installation_address',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_customer_name(self, obj):
        """Get customer full name or WhatsApp ID"""
        return obj.customer.get_full_name() or str(obj.customer.contact.whatsapp_id)
    
    def get_customer_phone(self, obj):
        """Get customer WhatsApp phone number"""
        return obj.customer.contact.whatsapp_id
    
    def get_short_id(self, obj):
        """Get shortened UUID for display"""
        return f"ISR-{str(obj.id)[:8]}"


class InstallationSystemRecordDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for installation system records with all relationships.
    Used for detail views and updates.
    """
    customer_details = serializers.SerializerMethodField()
    order_details = serializers.SerializerMethodField()
    installation_request_details = serializers.SerializerMethodField()
    technician_details = serializers.SerializerMethodField()
    component_details = serializers.SerializerMethodField()
    warranty_details = serializers.SerializerMethodField()
    job_card_details = serializers.SerializerMethodField()
    
    installation_type_display = serializers.CharField(source='get_installation_type_display', read_only=True)
    system_classification_display = serializers.CharField(source='get_system_classification_display', read_only=True)
    installation_status_display = serializers.CharField(source='get_installation_status_display', read_only=True)
    capacity_unit_display = serializers.CharField(source='get_capacity_unit_display', read_only=True)
    short_id = serializers.SerializerMethodField()
    
    class Meta:
        model = InstallationSystemRecord
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_short_id(self, obj):
        """Get shortened UUID for display"""
        return f"ISR-{str(obj.id)[:8]}"
    
    def get_customer_details(self, obj):
        """Get customer profile details"""
        customer = obj.customer
        return {
            'id': customer.contact_id,
            'name': customer.get_full_name(),
            'email': customer.email,
            'phone': customer.contact.whatsapp_id,
            'company': customer.company,
        }
    
    def get_order_details(self, obj):
        """Get order details"""
        if not obj.order:
            return None
        order = obj.order
        return {
            'id': str(order.id),
            'order_number': order.order_number,
            'name': order.name,
            'amount': str(order.amount) if order.amount else None,
            'stage': order.stage,
            'payment_status': order.payment_status,
        }
    
    def get_installation_request_details(self, obj):
        """Get installation request details"""
        if not obj.installation_request:
            return None
        req = obj.installation_request
        return {
            'id': req.id,
            'status': req.status,
            'installation_type': req.installation_type,
            'order_number': req.order_number,
            'preferred_datetime': req.preferred_datetime,
            'created_at': req.created_at,
        }
    
    def get_technician_details(self, obj):
        """Get assigned technician details"""
        technicians = obj.technicians.all()
        return [{
            'id': tech.id,
            'name': tech.user.get_full_name() or tech.user.username,
            'email': tech.user.email,
            'specialization': tech.specialization,
            'technician_type': tech.technician_type,
        } for tech in technicians]
    
    def get_component_details(self, obj):
        """Get installed component details"""
        components = obj.installed_components.select_related('product').all()
        return [{
            'id': comp.id,
            'serial_number': comp.serial_number,
            'product_name': comp.product.name if comp.product else None,
            'product_sku': comp.product.sku if comp.product else None,
            'status': comp.status,
        } for comp in components]
    
    def get_warranty_details(self, obj):
        """Get warranty details"""
        warranties = obj.warranties.select_related('serialized_item', 'manufacturer').all()
        return [{
            'id': warranty.id,
            'status': warranty.status,
            'start_date': warranty.start_date,
            'end_date': warranty.end_date,
            'manufacturer': warranty.manufacturer.name if warranty.manufacturer else None,
            'serial_number': warranty.serialized_item.serial_number,
        } for warranty in warranties]
    
    def get_job_card_details(self, obj):
        """Get job card details"""
        job_cards = obj.job_cards.all()
        return [{
            'id': job_card.id,
            'job_card_number': job_card.job_card_number,
            'status': job_card.status,
            'reported_fault': job_card.reported_fault,
            'is_under_warranty': job_card.is_under_warranty,
            'creation_date': job_card.creation_date,
        } for job_card in job_cards]


class InstallationSystemRecordCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating installation system records.
    Validates all required fields and relationships.
    """
    
    class Meta:
        model = InstallationSystemRecord
        fields = [
            'installation_request',
            'customer',
            'order',
            'installation_type',
            'system_size',
            'capacity_unit',
            'system_classification',
            'installation_status',
            'installation_date',
            'commissioning_date',
            'remote_monitoring_id',
            'latitude',
            'longitude',
            'installation_address',
            'technicians',
            'installed_components',
            'warranties',
            'job_cards',
        ]
    
    def validate(self, data):
        """
        Validate that required fields are present based on installation type.
        """
        installation_type = data.get('installation_type')
        
        # Solar installations should have system_size in kW
        if installation_type in ['solar', 'hybrid']:
            if not data.get('system_size'):
                raise serializers.ValidationError({
                    'system_size': 'System size is required for solar installations.'
                })
            if data.get('capacity_unit') not in ['kW', None]:
                raise serializers.ValidationError({
                    'capacity_unit': 'Capacity unit should be kW for solar installations.'
                })
        
        # Starlink installations should have system_size in Mbps
        if installation_type == 'starlink':
            if data.get('capacity_unit') not in ['Mbps', 'units', None]:
                raise serializers.ValidationError({
                    'capacity_unit': 'Capacity unit should be Mbps or units for Starlink installations.'
                })
        
        return data
    
    def create(self, validated_data):
        """
        Create installation system record and handle many-to-many relationships.
        """
        # Extract many-to-many fields
        technicians = validated_data.pop('technicians', [])
        installed_components = validated_data.pop('installed_components', [])
        warranties = validated_data.pop('warranties', [])
        job_cards = validated_data.pop('job_cards', [])
        
        # Create the instance
        instance = InstallationSystemRecord.objects.create(**validated_data)
        
        # Set many-to-many relationships
        if technicians:
            instance.technicians.set(technicians)
        if installed_components:
            instance.installed_components.set(installed_components)
        if warranties:
            instance.warranties.set(warranties)
        if job_cards:
            instance.job_cards.set(job_cards)
        
        return instance
    
    def update(self, instance, validated_data):
        """
        Update installation system record and handle many-to-many relationships.
        """
        # Extract many-to-many fields
        technicians = validated_data.pop('technicians', None)
        installed_components = validated_data.pop('installed_components', None)
        warranties = validated_data.pop('warranties', None)
        job_cards = validated_data.pop('job_cards', None)
        
        # Update simple fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update many-to-many relationships
        if technicians is not None:
            instance.technicians.set(technicians)
        if installed_components is not None:
            instance.installed_components.set(installed_components)
        if warranties is not None:
            instance.warranties.set(warranties)
        if job_cards is not None:
            instance.job_cards.set(job_cards)
        
        return instance
