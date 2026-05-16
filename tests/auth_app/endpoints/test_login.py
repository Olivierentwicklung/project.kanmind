from unittest.mock import patch

import pytest
from rest_framework.authtoken.models import Token


@pytest.mark.django_db
def test_login_success(client, user_profile, user_login_payload):

    response = client.post('/api/login/', user_login_payload, format='json')

    assert response.status_code == 200

    data = response.data

    assert 'token' in data
    assert data['email'] == user_profile.user.email
    assert data['fullname'] == user_profile.fullname
    assert data['user_id'] == user_profile.pk

    assert Token.objects.filter(user=user_profile.user).exists()


@pytest.mark.django_db
def test_login_fails_with_wrong_password(client, user_profile, user_login_payload):

    user_login_payload.update(dict(password='wrongPassword123'))

    response = client.post('/api/login/', user_login_payload, format='json')

    assert response.status_code == 400


@pytest.mark.django_db
def test_login_fails_with_unknown_email(client, user_login_payload):
    user_login_payload.update(dict(email='unknown@mail.com'))

    response = client.post('/api/login/', user_login_payload, format='json')

    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize(
    'missing_field',
    [
        'email',
        'password',
    ],
)
def test_login_fails_when_required_field_is_missing(
    client, user_login_payload, missing_field
):

    user_login_payload.pop(missing_field)

    response = client.post('/api/login/', user_login_payload, format='json')

    assert response.status_code == 400
    assert missing_field in response.data


@pytest.mark.django_db
def test_login_fails_with_invalid_email_format(client, user_login_payload):
    user_login_payload.update(dict(email='not-an-email'))

    response = client.post('/api/login/', user_login_payload, format='json')

    assert response.status_code == 400
    assert 'email' in response.data


@pytest.mark.django_db
def test_login_returns_same_token_if_token_already_exists(
    client, user_profile, user_login_payload
):

    existing_token = Token.objects.create(user=user_profile.user)

    response = client.post('/api/login/', user_login_payload, format='json')

    assert response.status_code == 200
    assert response.data['token'] == existing_token.key
    assert Token.objects.filter(user=user_profile.user).count() == 1


@pytest.mark.django_db
def test_login_returns_500_when_unexpected_error_happens(
    client, user_profile, user_login_payload
):

    with patch(
        'auth_app.api.views.Token.objects.get_or_create',
        side_effect=Exception('Unexpected token error'),
    ):
        response = client.post(
            '/api/login/',
            user_login_payload,
            format='json',
        )

    assert response.status_code == 500
