from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

from auth_app.models import UserProfile


class RegistrationSerializer(serializers.ModelSerializer):
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
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['repeated_password']:
            raise serializers.ValidationError(
                {'repeated_password': 'Passwords do not match.'}
            )

        return attrs

    def create(self, validated_data):
        fullname = validated_data.pop('fullname')
        email = validated_data.pop('email')
        password = validated_data.pop('password')

        validated_data.pop('repeated_password')

        with transaction.atomic():
            """
            transaction.atomic: if an exception occurs:
                - Django raises exception
                - transaction rolls back automatically
                - DRF returns 500 response
            """
            user = User.objects.create_user(
                username=email, email=email, password=password
            )

            UserProfile.objects.create(user=user, fullname=fullname)

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
    )

    def validate(self, attrs):
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
