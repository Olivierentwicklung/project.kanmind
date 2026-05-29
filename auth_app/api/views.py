from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from auth_app.models import UserProfile

from .serializers import (
    CheckEmailQuerySerializer,
    CheckEmailResponseSerializer,
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
    API view used to log in a user.
    """

    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Validate login data and return the login response.
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


class EmailCheckView(generics.RetrieveAPIView):
    """
    API view used to check if an email belongs to an existing user.
    """

    serializer_class = CheckEmailResponseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type:ignore
        """
        gets UserProfile and User together
        """

        return UserProfile.objects.select_related('user')

    def get_object(self):  # type:ignore
        """
        Return the single UserProfile object for the requested email.
        """
        query_serializer = CheckEmailQuerySerializer(data=self.request.query_params)  # type:ignore
        query_serializer.is_valid(raise_exception=True)

        email = query_serializer.validated_data['email']  # type:ignore

        return get_object_or_404(
            self.get_queryset(),
            user__email=email,
        )
