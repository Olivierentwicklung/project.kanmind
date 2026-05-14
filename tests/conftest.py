import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

mock_user_data = dict(
    fullname='Example User', email='example@mail.com', password='examplePassword123'
)


@pytest.fixture
def client():
    client = APIClient()
    client.raise_request_exception = False  # for Testing 500
    return client


@pytest.fixture
def user():
    return User.objects.create_user(
        username=mock_user_data['fullname'],
        email=mock_user_data['email'],
        password=mock_user_data['password'],
    )


@pytest.fixture
def user_registration_payload():
    return dict(
        fullname=mock_user_data['fullname'],
        email=mock_user_data['email'],
        password=mock_user_data['password'],
        repeated_password=mock_user_data['password'],
    )
