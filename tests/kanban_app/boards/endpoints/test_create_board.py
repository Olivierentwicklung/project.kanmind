from unittest.mock import Mock

import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from kanban_app.boards.api.permissions import BoardPermission
from kanban_app.boards.api.views import BoardListView
from kanban_app.boards.models import Board
from tests.conftest import BOARDS_URL


@pytest.mark.django_db
def test_create_board_performance_regression(
    user,
    user_profile,
    second_user_profile,
    django_assert_num_queries,
):
    factory = APIRequestFactory()

    payload = dict(
        title='New Project',
        members=[
            user_profile.id,
            second_user_profile.id,
        ],
    )

    request = factory.post(
        BOARDS_URL,
        payload,
        format='json',
    )

    force_authenticate(request, user=user)

    view = BoardListView.as_view()

    with django_assert_num_queries(7):
        response = view(request)

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_create_board_success(auth_user_client, user_profile, second_user_profile):
    payload = dict(
        title='New Project',
        members=[
            user_profile.id,
            second_user_profile.id,
        ],
    )

    response = auth_user_client.post(
        BOARDS_URL,
        payload,
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED

    board = Board.objects.get(id=response.data['id'])

    assert board.title == payload['title']
    assert board.owner == user_profile
    assert board.members.count() == 2
    assert user_profile in board.members.all()
    assert second_user_profile in board.members.all()

    assert response.data['title'] == payload['title']
    assert response.data['member_count'] == 2
    assert response.data['ticket_count'] == 0
    assert response.data['tasks_to_do_count'] == 0
    assert response.data['tasks_high_prio_count'] == 0
    assert response.data['owner_id'] == user_profile.id


@pytest.mark.django_db
def test_board_permission_post_returns_false(
    user,
    user_profile,
    second_user_profile,
):
    factory = APIRequestFactory()

    payload = {
        'title': 'New Project',
        'members': [
            user_profile.id,
            second_user_profile.id,
        ],
    }

    request = factory.post(
        BOARDS_URL,
        payload,
        format='json',
    )
    request.user = user

    board_mock = Mock()
    board_mock.owner.user = user
    board_mock.members.filter.return_value.exists.return_value = False

    permission = BoardPermission()

    result = permission.has_object_permission(request, None, board_mock)

    assert result is False


@pytest.mark.django_db
def test_create_board_fails_when_not_authenticated(client, user_profile):
    payload = dict(
        title='New Project',
        members=[user_profile.id],
    )

    response = client.post(
        BOARDS_URL,
        payload,
        format='json',
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert Board.objects.count() == 0


@pytest.mark.django_db
def test_create_board_fails_when_title_is_missing(auth_user_client, user_profile):
    payload = dict(
        members=[user_profile.id],
    )

    response = auth_user_client.post(
        BOARDS_URL,
        payload,
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'title' in response.data
    assert Board.objects.count() == 0


@pytest.mark.django_db
def test_create_board_fails_when_title_is_empty(auth_user_client, user_profile):
    payload = dict(
        title='',
        members=[user_profile.id],
    )

    response = auth_user_client.post(
        BOARDS_URL,
        payload,
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'title' in response.data
    assert Board.objects.count() == 0


@pytest.mark.django_db
def test_create_board_fails_when_members_are_missing(auth_user_client):
    payload = dict(
        title='New Project',
    )

    response = auth_user_client.post(
        BOARDS_URL,
        payload,
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'members' in response.data
    assert Board.objects.count() == 0


@pytest.mark.django_db
def test_create_board_fails_when_members_are_empty(auth_user_client):
    payload = dict(
        title='New Project',
        members=[],
    )

    response = auth_user_client.post(
        BOARDS_URL,
        payload,
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'members' in response.data
    assert Board.objects.count() == 0


@pytest.mark.django_db
def test_create_board_fails_when_member_does_not_exist(auth_user_client):
    payload = dict(
        title='New Project',
        members=[999999],
    )

    response = auth_user_client.post(
        BOARDS_URL,
        payload,
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'members' in response.data
    assert Board.objects.count() == 0


@pytest.mark.django_db
def test_create_board_returns_500_when_unexpected_error_happens(
    auth_user_client, user_profile, force_db_crash
):
    payload = dict(
        title='New Project',
        members=[user_profile.id],
    )

    with force_db_crash:
        response = auth_user_client.post(
            BOARDS_URL,
            payload,
            format='json',
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
