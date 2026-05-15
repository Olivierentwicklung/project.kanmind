import pytest
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from auth_app.models import UserProfile

FAKE_USER_PROFILE_DATA = dict(
    fullname='Example User', email='example@mail.com', password='examplePassword123'
)


@pytest.fixture
def client():
    client = APIClient()
    client.raise_request_exception = False  # Only for Testing 500
    return client


@pytest.fixture
def user():
    return User.objects.create_user(
        username=FAKE_USER_PROFILE_DATA['email'],
        email=FAKE_USER_PROFILE_DATA['email'],
        password=FAKE_USER_PROFILE_DATA['password'],
    )


@pytest.fixture
def user_profile(user):
    UserProfile.objects.create(user=user, fullname=FAKE_USER_PROFILE_DATA['fullname'])

    return user


@pytest.fixture
def user_registration_payload():
    return dict(
        fullname=FAKE_USER_PROFILE_DATA['fullname'],
        email=FAKE_USER_PROFILE_DATA['email'],
        password=FAKE_USER_PROFILE_DATA['password'],
        repeated_password=FAKE_USER_PROFILE_DATA['password'],
    )


@pytest.fixture
def user_login_payload():
    return dict(
        email=FAKE_USER_PROFILE_DATA['email'],
        password=FAKE_USER_PROFILE_DATA['password'],
    )


@pytest.fixture
def auth_user_client(client, user_profile):

    token, _ = Token.objects.get_or_create(user=user_profile)

    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    return client
