import pytest
from rest_framework import status

from tests.conftest import EMAIL_CHECK_URL


@pytest.mark.django_db
def test_email_check_success(auth_user_client, user_profile):

    response = auth_user_client.get(
        EMAIL_CHECK_URL,
        {'email': user_profile.user.email},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data['id'] == user_profile.id
    assert response.data['email'] == user_profile.user.email
    assert response.data['fullname'] == user_profile.fullname


@pytest.mark.django_db
def test_email_check_fails_when_not_authenticated(client, user_profile):
    response = client.get(
        EMAIL_CHECK_URL,
        {'email': user_profile.user.email},
        format='json',
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_email_check_fails_when_email_is_missing(auth_user_client):

    response = auth_user_client.get(EMAIL_CHECK_URL, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'email' in response.data


@pytest.mark.django_db
def test_email_check_fails_with_invalid_email_format(auth_user_client):

    response = auth_user_client.get(
        EMAIL_CHECK_URL,
        {'email': 'not-an-email'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'email' in response.data


@pytest.mark.django_db
def test_email_check_returns_404_when_email_does_not_exist(auth_user_client):

    response = auth_user_client.get(
        EMAIL_CHECK_URL,
        {'email': 'unknown@example.com'},
        format='json',
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_email_check_returns_500_when_unexpected_error_happens(
    auth_user_client, user_profile, force_db_crash
):

    with force_db_crash:
        response = auth_user_client.get(
            EMAIL_CHECK_URL,
            {'email': user_profile.user.email},
            format='json',
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
