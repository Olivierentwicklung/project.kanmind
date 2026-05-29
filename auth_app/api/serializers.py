from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers

from auth_app.models import UserProfile


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer used for registering a new user.
    """

    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)

    token = serializers.SerializerMethodField()
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        """Configuration class for the serializer."""

        model = UserProfile
        fields = [
            'fullname',
            'email',
            'password',
            'repeated_password',
            'token',
            'user_id',
        ]

    def validate_email(self, value):
        """Validate the email field."""

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists.')
        return value

    def validate(self, attrs):
        """
        We compare:
           - password
           - repeated_password
        """

        if attrs['password'] != attrs['repeated_password']:
            raise serializers.ValidationError(
                {'repeated_password': 'Passwords do not match.'}
            )
        return attrs

    def get_token(self, obj):
        """Return the authentication token for the response."""

        return self.context.get('token')

    def to_representation(self, instance):
        """Customize the final API response."""

        data = {
            'token': self.get_token(instance),
            'fullname': instance.fullname,
            'email': instance.user.email,
            'user_id': instance.id,
        }

        return data


class LoginSerializer(serializers.Serializer):
    """
    Serializer used for logging in a user.
    """

    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)

    token = serializers.SerializerMethodField()

    def validate(self, attrs):
        """
        Validate the complete login data.
        """

        email = attrs['email']
        password = attrs['password']

        user = authenticate(
            username=email,
            password=password,
        )

        if user is None:
            raise serializers.ValidationError({'detail': 'Invalid email or password.'})

        attrs['user'] = user
        return attrs

    def get_token(self, obj):
        """
        Return token from serializer context.
        """

        return self.context.get('token')

    def to_representation(self, instance):
        """Customize the final API response."""

        data = {
            'token': self.get_token(instance),
            'fullname': instance.userprofile.fullname,
            'email': instance.email,
            'user_id': instance.id,
        }

        return data


class CheckEmailQuerySerializer(serializers.Serializer):
    """
    Serializer used to validate the query parameters for checking an email.
    This serializer is used for input only.
    """

    email = serializers.EmailField()


class CheckEmailResponseSerializer(serializers.Serializer):
    """
    Serializer used to format the response for the check-email endpoint.
    This serializer is used for output only.
    """

    id = serializers.IntegerField(source='user.id')
    email = serializers.EmailField(source='user.email')
    fullname = serializers.CharField()
