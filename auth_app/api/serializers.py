from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

from auth_app.models import UserProfile


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Creates both:
    - Django User
    - UserProfile
    """

    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'fullname',
            'email',
            'password',
            'repeated_password',
        ]

    def validate_email(self, value):
        """
        Ensure the email address is unique.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists.')
        return value

    def validate(self, attrs):
        """
        Validate that both passwords match.
        """
        if attrs['password'] != attrs['repeated_password']:
            raise serializers.ValidationError(
                {'repeated_password': 'Passwords do not match.'}
            )

        return attrs

    def create(self, validated_data):
        """
        Create User and UserProfile inside a database transaction.
        """
        fullname = validated_data.pop('fullname')
        email = validated_data.pop('email')
        password = validated_data.pop('password')

        # Remove repeated_password because it is not needed anymore
        validated_data.pop('repeated_password')

        # Ensure both objects are created successfully or rollback everything
        with transaction.atomic():
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
            )

            UserProfile.objects.create(
                user=user,
                fullname=fullname,
            )

        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user authentication.
    """

    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
    )

    def validate(self, attrs):
        """
        Authenticate user credentials.
        """
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(
            username=email,
            password=password,
        )

        if not user:
            raise serializers.ValidationError('Invalid email or password.')

        attrs['user'] = user
        return attrs


class EmailCheckSerializer(serializers.Serializer):
    """
    Serializer for email existence/validation checks.
    """

    email = serializers.EmailField()
