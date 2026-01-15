import re
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Order, OrderItem, InstallationRequest, SiteAssessmentRequest, CustomerProfile, Interaction, JobCard, LoanApplication
from conversations.models import Contact
from conversations.utils import normalize_phone_number
from products_and_services.models import SerializedItem

User = get_user_model()

# A simple serializer for providing context on related models
class SimpleContactSerializer(serializers.ModelSerializer):
    """A lightweight serializer for basic Contact information."""
    class Meta:
        model = Contact
        fields = ['id', 'whatsapp_id', 'name']
    
    def validate_whatsapp_id(self, value):
        """Normalize whatsapp_id to E.164 format if it looks like a phone number."""
        # Only normalize if it looks like a phone number (contains only digits and possibly +)
        if re.match(r'^[\d+\s\-()]+$', value):
            normalized = normalize_phone_number(value)
            if normalized:
                return normalized
        return value

class SimpleUserSerializer(serializers.ModelSerializer):
    """A lightweight serializer for basic User (agent) information."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'first_name', 'last_name']

class SimpleSerializedItemSerializer(serializers.ModelSerializer):
    """A lightweight serializer for basic SerializedItem information."""
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = SerializedItem
        fields = ['serial_number', 'product_name']

class SimpleCustomerProfileSerializer(serializers.ModelSerializer):
    """A lightweight serializer for basic CustomerProfile information, ideal for nesting."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    contact_id = serializers.IntegerField(source='contact.id', read_only=True)

    class Meta:
        model = CustomerProfile
        fields = ['contact_id', 'full_name', 'company']

class SiteAssessmentRequestSerializer(serializers.ModelSerializer):
    customer = SimpleCustomerProfileSerializer(read_only=True)

    class Meta:
        model = SiteAssessmentRequest
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Customizes the JWT response to include a 'role' claim, which the frontend needs for redirection.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email

        # Add role claim based on user profile/status
        if user.is_superuser or user.is_staff:
            token['role'] = 'admin'
        elif hasattr(user, 'manufacturer_profile'):
            token['role'] = 'manufacturer'
        elif hasattr(user, 'technician_profile'):
            token['role'] = 'technician'
        elif hasattr(user, 'retailer_profile'):
            token['role'] = 'retailer'
        elif hasattr(user, 'retailer_branch_profile'):
            token['role'] = 'retailer_branch'
        else:
            token['role'] = 'client'

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Add user details and role to the response for the frontend.
        token = self.get_token(self.user)
        data['username'] = self.user.username
        data['email'] = self.user.email
        data['role'] = token['role']
        return data

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm Password")

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        # Auto-create Contact + CustomerProfile for client users (non-staff)
        if not user.is_staff and not user.is_superuser:
            from conversations.models import Contact
            from .models import CustomerProfile
            # Use email or username as whatsapp_id placeholder if real number not provided
            whatsapp_id_placeholder = user.email or f"user-{user.id}"  # ensure uniqueness
            contact = Contact.objects.create(
                whatsapp_id=whatsapp_id_placeholder,
                name=user.get_full_name() or user.username,
                user=user
            )
            CustomerProfile.objects.create(
                contact=contact,
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email
            )
        return user

# --- OrderItem Serializer ---
class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem with fulfillment tracking"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    fulfillment_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'order', 'product', 'product_name', 'product_sku',
            'quantity', 'unit_price', 'total_amount',
            'units_assigned', 'is_fully_assigned', 'fulfillment_percentage',
            'created_at'
        ]
        read_only_fields = ('id', 'units_assigned', 'is_fully_assigned', 'created_at')
    
    def get_fulfillment_percentage(self, obj):
        """Calculate fulfillment percentage"""
        if obj.quantity == 0:
            return 0
        return round((obj.units_assigned / obj.quantity) * 100, 1)

# --- Order Serializer ---
class OrderSerializer(serializers.ModelSerializer):
    customer = SimpleCustomerProfileSerializer(read_only=True)
    assigned_agent = SimpleUserSerializer(read_only=True)
    assigned_agent_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_staff=True),
        source='assigned_agent', write_only=True, allow_null=True, required=False
    )
    stage_display = serializers.CharField(source='get_stage_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'name', 'customer', 'stage', 'stage_display', 'payment_status', 'payment_status_display',
            'amount', 'currency', 'expected_close_date', 'assigned_agent', 'assigned_agent_id', 'notes', 
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')

class CustomerProfileSerializer(serializers.ModelSerializer):
    contact = SimpleContactSerializer()
    lead_status_display = serializers.SerializerMethodField()

    def get_lead_status_display(self, obj):
        return obj.get_lead_status_display()

    class Meta:
        model = CustomerProfile
        fields = [
            'contact', 'first_name', 'last_name', 'email', 'company', 'role',
            'address_line_1', 'address_line_2', 'city', 'state_province', 'postal_code', 'country',
            'lead_status', 'lead_status_display', 'potential_value', 'acquisition_source',
            'assigned_agent', 'assigned_agent_id', 'tags', 'notes', 'custom_attributes',
            'created_at', 'updated_at', 'last_interaction_date'
        ]
        read_only_fields = ('created_at', 'updated_at', 'last_interaction_date')

    def create(self, validated_data):
        contact_data = validated_data.pop('contact')
        contact = Contact.objects.create(**contact_data)
        customer_profile = CustomerProfile.objects.create(contact=contact, **validated_data)
        return customer_profile

class InteractionSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and viewing customer interactions.

    On read, it provides lightweight, nested representations of the customer and agent.
    On write, it accepts IDs for customer and agent, and can automatically assign
    the logged-in user as the agent if not specified.
    """
    # Display human-readable choice values
    interaction_type_display = serializers.CharField(source='get_interaction_type_display', read_only=True)

    # Provide context on the customer and agent using lightweight serializers for performance
    customer = SimpleCustomerProfileSerializer(read_only=True)
    agent = SimpleUserSerializer(read_only=True)

    # Writable fields for creating an interaction
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomerProfile.objects.all(), source='customer', write_only=True
    )
    agent_id = serializers.PrimaryKeyRelatedField(
        # Ensure only staff members can be assigned as agents
        queryset=User.objects.filter(is_staff=True),
        source='agent', write_only=True, allow_null=True, required=False
    )

    class Meta:
        model = Interaction
        fields = [
            'id', 'customer', 'customer_id', 'agent', 'agent_id', 'interaction_type',
            'interaction_type_display', 'notes', 'created_at'
        ]
        read_only_fields = ('id', 'created_at')

    def create(self, validated_data):
        """
        Overrides create to automatically assign the authenticated user as the
        agent if one is not provided in the request payload.
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            # Check if an agent was specified in the payload before assigning the request user.
            # This handles cases where agent_id is explicitly sent as null.
            if 'agent' not in validated_data and 'agent_id' not in self.initial_data:
                validated_data['agent'] = request.user

        return super().create(validated_data)

class JobCardSerializer(serializers.ModelSerializer):
    """
    Serializer for listing Job Cards, including some related customer info.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True, default='N/A')
    customer_whatsapp = serializers.CharField(source='customer.contact.whatsapp_id', read_only=True, default='N/A')
    serialized_item = SimpleSerializedItemSerializer(read_only=True)

    class Meta:
        model = JobCard
        fields = [
            'job_card_number',
            'customer_name',
            'customer_whatsapp',
            'serialized_item',
            'status',
            'creation_date',
        ]

class JobCardDetailSerializer(JobCardSerializer):
    """
    Detailed serializer for a single Job Card, including more fields.
    """
    customer_address = serializers.CharField(source='customer.address_line_1', read_only=True, default='')
    
    class Meta(JobCardSerializer.Meta):
        # Inherit fields from JobCardSerializer and add more
        fields = JobCardSerializer.Meta.fields + [
            'reported_fault',
            'is_under_warranty',
            'customer_address',
            'job_card_details', # The raw JSON
        ]

class LoanApplicationSerializer(serializers.ModelSerializer):
    customer = SimpleCustomerProfileSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = LoanApplication
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

class SimpleTechnicianSerializer(serializers.ModelSerializer):
    """A lightweight serializer for Technician information."""
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        from warranty.models import Technician
        model = Technician
        fields = ['id', 'user', 'technician_type', 'specialization']


class InstallationRequestSerializer(serializers.ModelSerializer):
    customer = SimpleCustomerProfileSerializer(read_only=True)
    associated_order = OrderSerializer(read_only=True)
    technicians = SimpleTechnicianSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    installation_type_display = serializers.CharField(source='get_installation_type_display', read_only=True)

    class Meta:
        model = InstallationRequest
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class RetailerOrderCreationSerializer(serializers.Serializer):
    """
    Serializer for retailers to create orders for solar package sales.
    Handles the complete workflow: customer creation, order, installation request, and SSR.
    """
    # Solar package selection
    solar_package_id = serializers.IntegerField(
        required=True,
        help_text="ID of the solar package being ordered"
    )
    
    # Customer details
    customer_first_name = serializers.CharField(max_length=100, required=True)
    customer_last_name = serializers.CharField(max_length=100, required=True)
    customer_phone = serializers.CharField(
        max_length=50,
        required=True,
        help_text="Customer phone number (will be used for WhatsApp contact)"
    )
    customer_email = serializers.EmailField(required=False, allow_blank=True)
    customer_company = serializers.CharField(max_length=150, required=False, allow_blank=True)
    
    # Address details
    address_line_1 = serializers.CharField(max_length=255, required=True)
    address_line_2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=True)
    state_province = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    country = serializers.CharField(max_length=100, default='Zimbabwe')
    
    # Location details (optional)
    latitude = serializers.DecimalField(
        max_digits=10, decimal_places=7, required=False, allow_null=True
    )
    longitude = serializers.DecimalField(
        max_digits=10, decimal_places=7, required=False, allow_null=True
    )
    
    # Payment details
    payment_method = serializers.ChoiceField(
        choices=Order.PaymentMethod.choices,
        required=True,
        help_text="Payment method selected by customer"
    )
    
    # Loan details (if applicable)
    loan_approved = serializers.BooleanField(
        default=False,
        help_text="Whether the customer has loan approval"
    )
    loan_application_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="ID of the loan application if applicable"
    )
    
    # Installation details
    preferred_installation_date = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Customer's preferred installation date/time"
    )
    installation_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Additional notes for the installation"
    )
    
    def validate_solar_package_id(self, value):
        """Validate that the solar package exists and is active"""
        from products_and_services.models import SolarPackage
        try:
            package = SolarPackage.objects.get(id=value, is_active=True)
        except SolarPackage.DoesNotExist:
            raise serializers.ValidationError(
                "Solar package not found or is not active"
            )
        return value
    
    def validate_customer_phone(self, value):
        """Normalize phone number to E.164 format"""
        normalized = normalize_phone_number(value)
        if not normalized:
            raise serializers.ValidationError(
                "Invalid phone number format. Please provide a valid phone number."
            )
        return normalized
    
    def validate_loan_application_id(self, value):
        """Validate loan application exists if provided"""
        if value:
            if not LoanApplication.objects.filter(id=value).exists():
                raise serializers.ValidationError(
                    "Loan application not found"
                )
        return value
    
    def create(self, validated_data):
        """
        Create the complete order workflow:
        1. Get or create Contact
        2. Get or create CustomerProfile
        3. Create Order with order items
        4. Create InstallationRequest
        5. Create InstallationSystemRecord (if applicable)
        6. Send confirmation notification
        """
        from products_and_services.models import SolarPackage
        from conversations.models import Contact
        
        # Get the solar package
        package = SolarPackage.objects.prefetch_related('package_products__product').get(
            id=validated_data['solar_package_id']
        )
        
        # Get the retailer from request context
        request = self.context.get('request')
        retailer = None
        if request and hasattr(request.user, 'retailer_profile'):
            retailer = request.user.retailer_profile
        elif request and hasattr(request.user, 'retailer_branch_profile'):
            retailer = request.user.retailer_branch_profile.retailer
        
        # 1. Get or create Contact
        contact, _ = Contact.objects.get_or_create(
            whatsapp_id=validated_data['customer_phone'],
            defaults={'name': f"{validated_data['customer_first_name']} {validated_data['customer_last_name']}"}
        )
        
        # 2. Get or create CustomerProfile
        customer_profile, _ = CustomerProfile.objects.get_or_create(
            contact=contact,
            defaults={
                'first_name': validated_data['customer_first_name'],
                'last_name': validated_data['customer_last_name'],
                'email': validated_data.get('customer_email', ''),
                'company': validated_data.get('customer_company', ''),
                'address_line_1': validated_data['address_line_1'],
                'address_line_2': validated_data.get('address_line_2', ''),
                'city': validated_data['city'],
                'state_province': validated_data.get('state_province', ''),
                'postal_code': validated_data.get('postal_code', ''),
                'country': validated_data['country'],
                'lead_status': 'qualified',
                'acquisition_source': f'Retailer: {retailer.company_name if retailer else "Unknown"}',
            }
        )
        
        # Update profile if it already exists
        if not _:
            customer_profile.first_name = validated_data['customer_first_name']
            customer_profile.last_name = validated_data['customer_last_name']
            if validated_data.get('customer_email'):
                customer_profile.email = validated_data['customer_email']
            customer_profile.address_line_1 = validated_data['address_line_1']
            customer_profile.city = validated_data['city']
            customer_profile.country = validated_data['country']
            customer_profile.save()
        
        # 3. Create Order
        import uuid
        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        order = Order.objects.create(
            order_number=order_number,
            name=f"{package.name} for {customer_profile.get_full_name()}",
            customer=customer_profile,
            stage=Order.Stage.CLOSED_WON,
            payment_status=Order.PaymentStatus.PENDING,
            source=Order.Source.API,
            amount=package.price,
            currency=package.currency,
            payment_method=validated_data['payment_method'],
            assigned_agent=request.user if request else None,
            notes=f"Ordered by retailer: {retailer.company_name if retailer else 'Unknown'}\n" +
                  (f"Loan approved: {validated_data['loan_approved']}\n" if validated_data.get('loan_approved') else "")
        )
        
        # Create order items from package products
        for package_product in package.package_products.all():
            OrderItem.objects.create(
                order=order,
                product=package_product.product,
                quantity=package_product.quantity,
                unit_price=package_product.product.price or 0,
                total_amount=(package_product.product.price or 0) * package_product.quantity
            )
        
        # Update order total
        order.update_total_amount()
        order.save()
        
        # 4. Create InstallationRequest
        installation_request = InstallationRequest.objects.create(
            customer=customer_profile,
            associated_order=order,
            status='pending',
            installation_type='solar',
            order_number=order_number,
            full_name=customer_profile.get_full_name(),
            address=validated_data['address_line_1'],
            location_latitude=validated_data.get('latitude'),
            location_longitude=validated_data.get('longitude'),
            preferred_datetime=validated_data.get('preferred_installation_date', 'To be scheduled'),
            contact_phone=validated_data['customer_phone'],
            notes=validated_data.get('installation_notes', '')
        )
        
        # 5. Create InstallationSystemRecord (SSR) if model exists
        try:
            from installation_systems.models import InstallationSystemRecord
            
            isr = InstallationSystemRecord.objects.create(
                installation_request=installation_request,
                customer=customer_profile,
                order=order,
                installation_type='solar',
                system_size=package.system_size,
                capacity_unit='kW',
                system_classification='residential',
                installation_status='pending',
                installation_address=validated_data['address_line_1'],
                latitude=validated_data.get('latitude'),
                longitude=validated_data.get('longitude')
            )
        except ImportError:
            # SSR model not available yet, skip
            isr = None
        
        # 6. Send confirmation notification (optional - can be implemented later)
        # TODO: Send WhatsApp/Email notification to customer
        
        return {
            'order': order,
            'installation_request': installation_request,
            'installation_system_record': isr,
            'customer_profile': customer_profile
        }