from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Order, OrderItem, InstallationRequest, SiteAssessmentRequest, CustomerProfile, Interaction, JobCard, LoanApplication
from conversations.models import Contact
from products_and_services.models import SerializedItem

User = get_user_model()

# A simple serializer for providing context on related models
class SimpleContactSerializer(serializers.ModelSerializer):
    """A lightweight serializer for basic Contact information."""
    class Meta:
        model = Contact
        fields = ['id', 'whatsapp_id', 'name']

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

class InstallationRequestSerializer(serializers.ModelSerializer):
    customer = SimpleCustomerProfileSerializer(read_only=True)
    associated_order = OrderSerializer(read_only=True)

    class Meta:
        model = InstallationRequest
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')