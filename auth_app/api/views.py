from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.models import UserProfile

from .serializers import (
    EmailCheckSerializer,
    LoginSerializer,
    RegistrationSerializer,
)


class RegistrationView(generics.CreateAPIView):
    """API view used to register a new user."""

    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    @transaction.atomic
    def perform_create(self, serializer):
        """Create a User, a UserProfile, and a Token."""

        fullname = serializer.validated_data['fullname']
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
        )

        profile = UserProfile.objects.create(
            user=user,
            fullname=fullname,
        )

        token, _ = Token.objects.get_or_create(user=user)

        serializer.instance = profile
        serializer.context['token'] = token.key


class LoginView(generics.GenericAPIView):
    """
    API view for user login.
    """

    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Validate login data and return token response.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        token, _ = Token.objects.get_or_create(user=user)

        serializer.instance = user
        serializer.context['token'] = token.key

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class EmailCheckView(APIView):
    """
    Check whether a user exists by email address.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Check whether a user exists by email address.
        """
        serializer = EmailCheckSerializer(data=request.query_params)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data['email']  # type:ignore

        try:
            user = User.objects.get(email=email)

            return Response(
                {
                    'id': user.id,  # type:ignore
                    'email': user.email,
                    'fullname': user.userprofile.fullname,  # type:ignore
                },
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            return Response(
                {'detail': 'Email not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
