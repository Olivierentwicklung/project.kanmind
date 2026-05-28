from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
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


class LoginView(ObtainAuthToken):
    """
    Authenticate user credentials and return an auth token.
    """

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        """
        Authenticate user credentials and return an auth token.
        """
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request},
        )

        if serializer.is_valid():
            user = serializer.validated_data['user']  # type:ignore

            # Reuse existing token or create a new one
            token, _ = Token.objects.get_or_create(user=user)

            data = {
                'token': token.key,
                'fullname': user.userprofile.fullname,
                'email': user.email,
                'user_id': user.id,
            }

            return Response(data, status=status.HTTP_200_OK)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
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
