import pytest

from kanban_app.boards.models import Board
from tests.conftest import BOARDS_URL


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

    assert response.status_code == 201

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

    assert response.status_code == 401
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

    assert response.status_code == 400
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

    assert response.status_code == 400
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

    assert response.status_code == 400
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

    assert response.status_code == 400
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

    assert response.status_code == 400
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

    assert response.status_code == 500
