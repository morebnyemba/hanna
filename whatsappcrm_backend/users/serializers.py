# whatsappcrm_backend/users/serializers.py

from django.contrib.auth.models import User, Group
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction

from .models import Retailer, RetailerBranch
from .constants import RETAILER_GROUP_NAME, RETAILER_BRANCH_GROUP_NAME


class UserSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Group.objects.all()
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'groups']
        read_only_fields = ['id', 'username'] # Username is not editable after creation


class UserInviteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=150)
    role = serializers.ChoiceField(choices=['Admin', 'Manufacturer', 'Technician']) # Example roles

    def create(self, validated_data):
        email = validated_data['email']
        first_name = validated_data['first_name']
        last_name = validated_data['last_name']
        role = validated_data['role']

        # Create a temporary password
        temp_password = User.objects.make_random_password()

        # Create the user
        user = User.objects.create_user(
            username=email, # Use email as username for simplicity
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=temp_password,
            is_staff=(role == 'Admin') # Only Admins are staff
        )

        # Assign to group
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)

        # Send invitation email (placeholder logic)
        # In a real app, you'd send a link to a password reset/setup page
        send_mail(
            'You have been invited to Hanna CRM',
            f'Hi {first_name},\n\nYou have been invited to join the Hanna CRM. Your temporary password is: {temp_password}\n\nPlease log in and change your password.',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        return user


class RetailerBranchSerializer(serializers.ModelSerializer):
    """
    Serializer for RetailerBranch model.
    """
    user = UserSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    retailer_name = serializers.CharField(source='retailer.company_name', read_only=True)

    class Meta:
        model = RetailerBranch
        fields = [
            'id', 'user', 'username', 'email', 'retailer', 'retailer_name',
            'branch_name', 'branch_code', 'contact_phone', 'address',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'username', 'email', 'retailer', 'retailer_name', 'created_at', 'updated_at']


class RetailerBranchCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a new retailer branch.
    Creates a user account for the branch.
    """
    # User fields for the branch account
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    
    # Branch fields
    branch_name = serializers.CharField(max_length=255)
    branch_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    contact_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        """Ensure email is unique."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_password(self, value):
        """Validate password using Django's password validators."""
        validate_password(value)
        return value

    def validate(self, data):
        """Check that the branch name is unique for this retailer."""
        retailer = self.context.get('retailer')
        if retailer and RetailerBranch.objects.filter(retailer=retailer, branch_name=data['branch_name']).exists():
            raise serializers.ValidationError({
                'branch_name': 'A branch with this name already exists for this retailer.'
            })
        return data

    @transaction.atomic
    def create(self, validated_data):
        """Create user and branch profile."""
        retailer = self.context.get('retailer')
        if not retailer:
            raise serializers.ValidationError("Retailer context is required.")

        # Create user for the branch
        email = validated_data['email']
        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data['password'],
            first_name=validated_data['branch_name'],  # Use branch name as first name
            last_name=retailer.company_name,  # Use company name as last name
            is_staff=False
        )

        # Add to RetailerBranch group
        branch_group, _ = Group.objects.get_or_create(name=RETAILER_BRANCH_GROUP_NAME)
        user.groups.add(branch_group)

        # Create branch profile
        branch = RetailerBranch.objects.create(
            user=user,
            retailer=retailer,
            branch_name=validated_data['branch_name'],
            branch_code=validated_data.get('branch_code') or None,
            contact_phone=validated_data.get('contact_phone') or None,
            address=validated_data.get('address') or None,
        )

        return branch


class RetailerBranchUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a retailer branch.
    """
    class Meta:
        model = RetailerBranch
        fields = ['branch_name', 'branch_code', 'contact_phone', 'address', 'is_active']


class RetailerSerializer(serializers.ModelSerializer):
    """
    Serializer for Retailer model.
    """
    user = UserSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    branch_count = serializers.SerializerMethodField()
    branches = RetailerBranchSerializer(many=True, read_only=True)

    class Meta:
        model = Retailer
        fields = [
            'id', 'user', 'username', 'email', 'company_name',
            'business_registration_number', 'contact_phone', 'address',
            'is_active', 'branch_count', 'branches', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'username', 'email', 'branch_count', 'branches', 'created_at', 'updated_at']

    def get_branch_count(self, obj):
        return obj.branches.count()


class RetailerRegistrationSerializer(serializers.Serializer):
    """
    Serializer for retailer registration.
    Creates a user account and associated retailer profile.
    """
    # User fields
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=150)
    
    # Retailer fields
    company_name = serializers.CharField(max_length=255)
    business_registration_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    contact_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        """Ensure email is unique."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_business_registration_number(self, value):
        """Ensure business registration number is unique if provided."""
        if value and Retailer.objects.filter(business_registration_number=value).exists():
            raise serializers.ValidationError("A retailer with this business registration number already exists.")
        return value

    def validate_password(self, value):
        """Validate password using Django's password validators."""
        validate_password(value)
        return value

    @transaction.atomic
    def create(self, validated_data):
        """Create user and retailer profile."""
        # Extract user data
        email = validated_data['email']
        password = validated_data['password']
        first_name = validated_data['first_name']
        last_name = validated_data['last_name']

        # Create user
        user = User.objects.create_user(
            username=email,  # Use email as username
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=False
        )

        # Add to Retailer group
        retailer_group, _ = Group.objects.get_or_create(name=RETAILER_GROUP_NAME)
        user.groups.add(retailer_group)

        # Create retailer profile
        retailer = Retailer.objects.create(
            user=user,
            company_name=validated_data['company_name'],
            business_registration_number=validated_data.get('business_registration_number') or None,
            contact_phone=validated_data.get('contact_phone') or None,
            address=validated_data.get('address') or None,
        )

        return retailer


class RetailerUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating retailer profile.
    """
    class Meta:
        model = Retailer
        fields = ['company_name', 'business_registration_number', 'contact_phone', 'address']

    def validate_business_registration_number(self, value):
        """Ensure business registration number is unique if changed."""
        if value and self.instance:
            existing = Retailer.objects.filter(business_registration_number=value).exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError("A retailer with this business registration number already exists.")
        return value


class RetailerSelectSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for retailer selection dropdown (public).
    Used during branch login to select which retailer the branch belongs to.
    """
    class Meta:
        model = Retailer
        fields = ['id', 'company_name']
