from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    EmailCheckSerializer,
    LoginSerializer,
    RegistrationSerializer,
)


class RegistrationView(APIView):
    """
    Register a new user and return an authentication token.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            # Create token for authenticated API access
            token, _ = Token.objects.get_or_create(user=user)

            data = {
                'token': token.key,
                'fullname': user.userprofile.fullname,  # type:ignore
                'email': user.email,  # type:ignore
                'user_id': user.id,  # type:ignore
            }

            return Response(data, status=status.HTTP_201_CREATED)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class LoginView(ObtainAuthToken):
    """
    Authenticate user credentials and return an auth token.
    """

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
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
