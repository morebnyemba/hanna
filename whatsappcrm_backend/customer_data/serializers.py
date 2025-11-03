from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Order, InstallationRequest, SiteAssessmentRequest, CustomerProfile, Interaction, JobCard
from conversations.models import Contact

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
        return user

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

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'name', 'customer', 'stage', 'stage_display', 'payment_status', 'payment_status_display',
            'amount', 'currency', 'expected_close_date', 'assigned_agent', 'assigned_agent_id', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')

class CustomerProfileSerializer(serializers.ModelSerializer):
    """
    A comprehensive serializer for CustomerProfile details.

    Handles the full representation of a customer's profile, including nested
    details for read operations and ID-based fields for write operations.
    """
    # The primary key of CustomerProfile is 'contact', which is a OneToOneField.
    # DRF handles this, 'pk' in the URL will map to 'contact_id'.
    contact = SimpleContactSerializer(read_only=True)

    # To make choices human-readable in API responses
    lead_status_display = serializers.CharField(source='get_lead_status_display', read_only=True)

    # Nested serializer for the assigned agent
    assigned_agent = SimpleUserSerializer(read_only=True)
    # Writable field for assigning an agent by their ID
    assigned_agent_id = serializers.PrimaryKeyRelatedField(
        # For performance and security, only list users who can be agents.
        queryset=User.objects.filter(is_staff=True),
        source='assigned_agent', write_only=True, allow_null=True, required=False
    )

    class Meta:
        model = CustomerProfile
        # The 'contact' field is the PK, so it's implicitly read-only here.
        fields = [
            'contact', 'first_name', 'last_name', 'email', 'company', 'role',
            'address_line_1', 'address_line_2', 'city', 'state_province', 'postal_code', 'country',
            'lead_status', 'lead_status_display', 'potential_value', 'acquisition_source',
            'assigned_agent', 'assigned_agent_id', 'tags', 'notes', 'custom_attributes',
            'created_at', 'updated_at', 'last_interaction_date'
        ]
        read_only_fields = ('created_at', 'updated_at', 'last_interaction_date')

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

    class Meta:
        model = JobCard
        fields = [
            'job_card_number',
            'customer_name',
            'customer_whatsapp',
            'product_description',
            'product_serial_number',
            'status',
            'creation_date',
        ]

class InstallationRequestSerializer(serializers.ModelSerializer):
    customer = SimpleCustomerProfileSerializer(read_only=True)
    associated_order = OrderSerializer(read_only=True)

    class Meta:
        model = InstallationRequest
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')