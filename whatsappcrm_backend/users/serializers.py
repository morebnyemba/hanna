# whatsappcrm_backend/users/serializers.py

from django.contrib.auth.models import User, Group
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.conf import settings

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
