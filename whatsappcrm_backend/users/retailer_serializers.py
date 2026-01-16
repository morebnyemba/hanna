# whatsappcrm_backend/users/retailer_serializers.py
"""
Serializers for retailer portal - Installation & Warranty Tracking
Provides read-only access to installation and warranty data for products sold by retailers.
"""

from rest_framework import serializers
from django.utils import timezone
from installation_systems.models import InstallationSystemRecord, InstallationPhoto
from warranty.models import Warranty, WarrantyClaim
from products_and_services.models import SerializedItem
from customer_data.models import JobCard


class RetailerInstallationTrackingSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for retailers to view installation tracking.
    Shows installations for products sold by the retailer.
    """
    customer_name = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()
    installation_type_display = serializers.CharField(source='get_installation_type_display', read_only=True)
    installation_status_display = serializers.CharField(source='get_installation_status_display', read_only=True)
    system_classification_display = serializers.CharField(source='get_system_classification_display', read_only=True)
    short_id = serializers.CharField(read_only=True)
    technician_names = serializers.SerializerMethodField()
    order_number = serializers.SerializerMethodField()
    installation_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = InstallationSystemRecord
        fields = [
            'id',
            'short_id',
            'customer_name',
            'customer_phone',
            'order_number',
            'installation_type',
            'installation_type_display',
            'installation_status',
            'installation_status_display',
            'system_classification',
            'system_classification_display',
            'system_size',
            'capacity_unit',
            'installation_date',
            'commissioning_date',
            'technician_names',
            'installation_address',
            'latitude',
            'longitude',
            'installation_progress',
            'created_at',
            'updated_at',
        ]
        read_only_fields = '__all__'
    
    def get_customer_name(self, obj):
        """Get customer full name"""
        return obj.customer.get_full_name() or 'N/A'
    
    def get_customer_phone(self, obj):
        """Get customer phone number"""
        if obj.customer.contact:
            return obj.customer.contact.whatsapp_id
        return 'N/A'
    
    def get_technician_names(self, obj):
        """Get list of assigned technician names"""
        return [tech.user.get_full_name() or tech.user.username for tech in obj.technicians.all()]
    
    def get_order_number(self, obj):
        """Get associated order number"""
        if obj.order:
            return obj.order.order_number or str(obj.order.id)
        return None
    
    def get_installation_progress(self, obj):
        """Get installation progress summary from checklists"""
        entries = obj.checklist_entries.all()
        if not entries.exists():
            return {
                'has_checklists': False,
                'overall_completion': 0,
                'checklists': []
            }
        
        checklist_data = []
        total_completion = 0
        for entry in entries:
            checklist_data.append({
                'name': entry.template.name,
                'type': entry.template.get_checklist_type_display(),
                'completion_percentage': float(entry.completion_percentage),
                'status': entry.get_completion_status_display(),
            })
            total_completion += float(entry.completion_percentage)
        
        overall = total_completion / len(checklist_data) if checklist_data else 0
        
        return {
            'has_checklists': True,
            'overall_completion': round(overall, 2),
            'checklists': checklist_data
        }


class RetailerInstallationDetailSerializer(serializers.ModelSerializer):
    """
    Detailed read-only serializer for installation details.
    Includes photos, full checklist info, and system details.
    """
    customer_info = serializers.SerializerMethodField()
    system_details = serializers.SerializerMethodField()
    installation_progress = serializers.SerializerMethodField()
    photos = serializers.SerializerMethodField()
    job_cards = serializers.SerializerMethodField()
    technician_details = serializers.SerializerMethodField()
    order_details = serializers.SerializerMethodField()
    
    class Meta:
        model = InstallationSystemRecord
        fields = [
            'id',
            'short_id',
            'customer_info',
            'order_details',
            'system_details',
            'installation_progress',
            'technician_details',
            'photos',
            'job_cards',
            'installation_address',
            'latitude',
            'longitude',
            'remote_monitoring_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = '__all__'
    
    def get_customer_info(self, obj):
        """Get customer information"""
        customer = obj.customer
        return {
            'name': customer.get_full_name() or 'N/A',
            'phone': customer.contact.whatsapp_id if customer.contact else 'N/A',
            'email': customer.email or 'N/A',
            'address_line_1': customer.address_line_1 or '',
            'city': customer.city or '',
        }
    
    def get_system_details(self, obj):
        """Get system details"""
        return {
            'installation_type': obj.get_installation_type_display(),
            'system_size': str(obj.system_size) if obj.system_size else 'N/A',
            'capacity_unit': obj.capacity_unit,
            'system_classification': obj.get_system_classification_display(),
            'installation_status': obj.get_installation_status_display(),
            'installation_date': obj.installation_date,
            'commissioning_date': obj.commissioning_date,
        }
    
    def get_installation_progress(self, obj):
        """Get detailed installation progress from checklists"""
        entries = obj.checklist_entries.all()
        if not entries.exists():
            return {
                'has_checklists': False,
                'overall_completion': 0,
                'checklists': []
            }
        
        checklist_data = []
        total_completion = 0
        for entry in entries:
            checklist_data.append({
                'id': str(entry.id),
                'template_name': entry.template.name,
                'checklist_type': entry.template.get_checklist_type_display(),
                'completion_percentage': float(entry.completion_percentage),
                'completion_status': entry.get_completion_status_display(),
                'started_at': entry.started_at,
                'completed_at': entry.completed_at,
                'items': entry.template.items,
                'completed_items': entry.completed_items,
            })
            total_completion += float(entry.completion_percentage)
        
        overall = total_completion / len(checklist_data) if checklist_data else 0
        
        return {
            'has_checklists': True,
            'overall_completion': round(overall, 2),
            'checklists': checklist_data
        }
    
    def get_photos(self, obj):
        """Get installation photos grouped by type"""
        photos = obj.photos.select_related('media_asset').all()
        photo_data = {}
        
        for photo in photos:
            photo_type = photo.get_photo_type_display()
            if photo_type not in photo_data:
                photo_data[photo_type] = []
            
            photo_data[photo_type].append({
                'id': str(photo.id),
                'photo_type': photo.photo_type,
                'caption': photo.caption or '',
                'description': photo.description or '',
                'uploaded_at': photo.uploaded_at,
                'media_url': photo.media_asset.file_url if photo.media_asset else None,
                'thumbnail_url': photo.media_asset.file_url if photo.media_asset else None,  # Could add thumbnail logic
            })
        
        return photo_data
    
    def get_job_cards(self, obj):
        """Get associated job cards (if available from manufacturer)"""
        job_cards = obj.job_cards.all()
        return [{
            'job_card_number': jc.job_card_number,
            'status': jc.get_status_display(),
            'reported_fault': jc.reported_fault or '',
            'is_under_warranty': jc.is_under_warranty,
            'creation_date': jc.creation_date,
        } for jc in job_cards]
    
    def get_technician_details(self, obj):
        """Get technician details"""
        return [{
            'name': tech.user.get_full_name() or tech.user.username,
            'specialization': tech.specialization or 'N/A',
            'contact_phone': tech.contact_phone or 'N/A',
        } for tech in obj.technicians.all()]
    
    def get_order_details(self, obj):
        """Get order details"""
        if not obj.order:
            return None
        
        order = obj.order
        return {
            'order_number': order.order_number or str(order.id),
            'order_name': order.name or 'N/A',
            'amount': str(order.amount) if order.amount else 'N/A',
            'currency': order.currency,
            'stage': order.get_stage_display(),
            'payment_status': order.get_payment_status_display(),
            'created_at': order.created_at,
        }


class RetailerWarrantySerializer(serializers.ModelSerializer):
    """
    Read-only serializer for retailers to view warranty information.
    Shows warranties for products sold by the retailer.
    """
    product_name = serializers.SerializerMethodField()
    product_serial_number = serializers.CharField(source='serialized_item.serial_number', read_only=True)
    customer_name = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    manufacturer_name = serializers.CharField(source='manufacturer.name', read_only=True)
    days_remaining = serializers.SerializerMethodField()
    active_claims_count = serializers.SerializerMethodField()
    order_number = serializers.SerializerMethodField()
    
    class Meta:
        model = Warranty
        fields = [
            'id',
            'product_name',
            'product_serial_number',
            'customer_name',
            'customer_phone',
            'manufacturer_name',
            'order_number',
            'start_date',
            'end_date',
            'days_remaining',
            'status',
            'status_display',
            'active_claims_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = '__all__'
    
    def get_product_name(self, obj):
        """Get product name"""
        return obj.serialized_item.product.name if obj.serialized_item else 'N/A'
    
    def get_customer_name(self, obj):
        """Get customer full name"""
        return obj.customer.get_full_name() or 'N/A'
    
    def get_customer_phone(self, obj):
        """Get customer phone number"""
        if obj.customer.contact:
            return obj.customer.contact.whatsapp_id
        return 'N/A'
    
    def get_days_remaining(self, obj):
        """Calculate days remaining until warranty expires"""
        today = timezone.now().date()
        if obj.end_date > today:
            return (obj.end_date - today).days
        return 0
    
    def get_active_claims_count(self, obj):
        """Get count of active claims for this warranty"""
        return obj.claims.filter(
            status__in=['pending', 'approved', 'in_progress']
        ).count()
    
    def get_order_number(self, obj):
        """Get associated order number"""
        if obj.associated_order:
            return obj.associated_order.order_number or str(obj.associated_order.id)
        return None


class RetailerWarrantyDetailSerializer(serializers.ModelSerializer):
    """
    Detailed read-only serializer for warranty details.
    Includes product info, customer info, and claims history.
    """
    product_info = serializers.SerializerMethodField()
    customer_info = serializers.SerializerMethodField()
    warranty_details = serializers.SerializerMethodField()
    claims = serializers.SerializerMethodField()
    order_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Warranty
        fields = [
            'id',
            'product_info',
            'customer_info',
            'warranty_details',
            'claims',
            'order_info',
            'created_at',
            'updated_at',
        ]
        read_only_fields = '__all__'
    
    def get_product_info(self, obj):
        """Get product information"""
        if not obj.serialized_item:
            return None
        
        item = obj.serialized_item
        return {
            'name': item.product.name,
            'sku': item.product.sku,
            'serial_number': item.serial_number,
            'barcode': item.barcode or 'N/A',
            'status': item.get_status_display(),
            'location': item.get_location_display(),
        }
    
    def get_customer_info(self, obj):
        """Get customer information"""
        customer = obj.customer
        return {
            'name': customer.get_full_name() or 'N/A',
            'phone': customer.contact.whatsapp_id if customer.contact else 'N/A',
            'email': customer.email or 'N/A',
            'address': f"{customer.address_line_1 or ''} {customer.city or ''}".strip() or 'N/A',
        }
    
    def get_warranty_details(self, obj):
        """Get warranty details"""
        today = timezone.now().date()
        days_remaining = (obj.end_date - today).days if obj.end_date > today else 0
        
        return {
            'manufacturer': obj.manufacturer.name if obj.manufacturer else 'N/A',
            'start_date': obj.start_date,
            'end_date': obj.end_date,
            'days_remaining': days_remaining,
            'status': obj.get_status_display(),
            'is_active': obj.status == 'active',
            'is_expired': obj.status == 'expired',
            'manufacturer_email': obj.manufacturer_email or 'N/A',
        }
    
    def get_claims(self, obj):
        """Get warranty claims"""
        claims = obj.claims.all().order_by('-created_at')
        return [{
            'claim_id': claim.claim_id,
            'description_of_fault': claim.description_of_fault,
            'status': claim.get_status_display(),
            'resolution_notes': claim.resolution_notes or '',
            'created_at': claim.created_at,
            'updated_at': claim.updated_at,
        } for claim in claims]
    
    def get_order_info(self, obj):
        """Get associated order information"""
        if not obj.associated_order:
            return None
        
        order = obj.associated_order
        return {
            'order_number': order.order_number or str(order.id),
            'order_name': order.name or 'N/A',
            'stage': order.get_stage_display(),
            'payment_status': order.get_payment_status_display(),
            'amount': str(order.amount) if order.amount else 'N/A',
            'currency': order.currency,
            'created_at': order.created_at,
        }


class RetailerProductMovementSerializer(serializers.ModelSerializer):
    """
    Serializer for tracking product movements (scanned in/out).
    Shows movement history for products sold by the retailer.
    """
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    location_display = serializers.CharField(source='get_location_display', read_only=True)
    order_number = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    movement_history = serializers.SerializerMethodField()
    
    class Meta:
        model = SerializedItem
        fields = [
            'id',
            'product_name',
            'product_sku',
            'serial_number',
            'barcode',
            'status',
            'status_display',
            'location',
            'location_display',
            'order_number',
            'customer_name',
            'checked_in_at',
            'checked_out_at',
            'current_holder',
            'movement_history',
            'created_at',
            'updated_at',
        ]
        read_only_fields = '__all__'
    
    def get_order_number(self, obj):
        """Get order number if item is assigned to an order"""
        if obj.order_item and obj.order_item.order:
            order = obj.order_item.order
            return order.order_number or str(order.id)
        return None
    
    def get_customer_name(self, obj):
        """Get customer name if item is assigned"""
        if obj.order_item and obj.order_item.order and obj.order_item.order.customer:
            return obj.order_item.order.customer.get_full_name() or 'N/A'
        return None
    
    def get_movement_history(self, obj):
        """Get movement history from logs"""
        # Get recent status changes from logs (if implemented)
        # For now, return basic movement info
        history = []
        
        if obj.checked_in_at:
            history.append({
                'action': 'Checked In',
                'timestamp': obj.checked_in_at,
                'location': obj.get_location_display(),
            })
        
        if obj.checked_out_at:
            history.append({
                'action': 'Checked Out',
                'timestamp': obj.checked_out_at,
                'location': obj.get_location_display(),
            })
        
        return history
