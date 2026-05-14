from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from auth_app.models import UserProfile


@pytest.mark.django_db
def test_registration_sucess(client, user_registration_payload):

    response = client.post(
        '/api/registration/', user_registration_payload, format='json'
    )

    assert response.status_code == 201

    data = response.data

    assert 'token' in data
    assert data['fullname'] == user_registration_payload['fullname']
    assert data['email'] == user_registration_payload['email']
    assert 'user_id' in data

    user = User.objects.get(email=user_registration_payload['email'])
    profile = UserProfile.objects.get(user=user)

    assert user.username == user_registration_payload['email']
    assert user.check_password(user_registration_payload['password'])
    assert profile.fullname == user_registration_payload['fullname']
    assert Token.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_registration_fails_when_email_already_exists(
    client, user, user_registration_payload
):

    response = client.post(
        '/api/registration/', user_registration_payload, format='json'
    )

    assert response.status_code == 400
    assert 'email' in response.data


@pytest.mark.django_db
def test_registration_fails_when_passwords_do_not_match(
    client, user_registration_payload
):

    response = client.post(
        '/api/registration/', user_registration_payload, format='json'
    )

    assert response.status_code == 400
    assert 'repeated_password' in response.data


@pytest.mark.django_db
@pytest.mark.parametrize(
    'missing_field',
    [
        'fullname',
        'email',
        'password',
        'repeated_password',
    ],
)
def test_registration_fails_when_required_field_is_missing(
    client, missing_field, user_registration_payload
):

    user_registration_payload.pop(missing_field)

    response = client.post(
        '/api/registration/', user_registration_payload, format='json'
    )

    assert response.status_code == 400
    assert missing_field in response.data


@pytest.mark.django_db
def test_registration_fails_with_invalid_email(client, user_registration_payload):

    response = client.post(
        '/api/registration/', user_registration_payload, format='json'
    )

    assert response.status_code == 400
    assert 'email' in response.data


@pytest.mark.django_db
def test_registration_fails_with_empty_fullname(client, user_registration_payload):

    response = client.post(
        '/api/registration/', user_registration_payload, format='json'
    )

    assert response.status_code == 400
    assert 'fullname' in response.data


@pytest.mark.django_db
def test_registration_fails_with_too_long_fullname(client, user_registration_payload):

    user_registration_payload.update({'fullname': 'a' * 256})

    response = client.post(
        '/api/registration/', user_registration_payload, format='json'
    )

    assert response.status_code == 400
    assert 'fullname' in response.data


@pytest.mark.django_db
def test_registration_returns_500_when_unexpected_error_happens(
    client, user_registration_payload
):

    with patch(
        'auth_app.api.serializers.UserProfile.objects.create',
        side_effect=Exception('Unexpected database error'),
    ):
        response = client.post(
            '/api/registration/',
            user_registration_payload,
            format='json',
        )

    assert response.status_code == 500
