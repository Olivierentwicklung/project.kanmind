import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient


@pytest.fixture
def client():
    client = APIClient()
    client.raise_request_exception = False  # for checking 500
    return client


@pytest.fixture
def user():
    return User.objects.create_user(
        username='example@mail.com',
        email='example@mail.com',
        password='examplePassword123',
    )


@pytest.fixture
def user_registration_payload():
    return dict(
        fullname='Example User',
        email='example@mail.com',
        password='examplePassword123',
        repeated_password='examplePassword123',
    )
