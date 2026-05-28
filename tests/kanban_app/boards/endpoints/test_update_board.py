import pytest

from tests.conftest import BOARDS_URL


@pytest.mark.django_db
def test_update_board_success_as_owner(
    auth_user_client,
    owned_board,
    user_profile,
    second_user_profile,
):
    payload = dict(
        title='Changed title',
        members=[
            user_profile.id,
            second_user_profile.id,
        ],
    )

    response = auth_user_client.patch(
        f'{BOARDS_URL}{owned_board.id}/',
        payload,
        format='json',
    )

    assert response.status_code == 200

    owned_board.refresh_from_db()

    assert owned_board.title == 'Changed title'
    assert owned_board.members.count() == 2
    assert user_profile in owned_board.members.all()
    assert second_user_profile in owned_board.members.all()

    assert response.data['id'] == owned_board.id
    assert response.data['title'] == 'Changed title'

    assert response.data['owner_data']['id'] == user_profile.id
    assert response.data['owner_data']['email'] == user_profile.user.email
    assert response.data['owner_data']['fullname'] == user_profile.fullname

    member_ids = [member['id'] for member in response.data['members_data']]

    assert user_profile.id in member_ids
    assert second_user_profile.id in member_ids


@pytest.mark.django_db
def test_update_board_success_as_member(
    auth_user_client,
    member_board,
    user_profile,
    second_user_profile,
):
    payload = dict(
        title='Changed by member',
        members=[
            user_profile.id,
            second_user_profile.id,
        ],
    )

    response = auth_user_client.patch(
        f'{BOARDS_URL}{member_board.id}/',
        payload,
        format='json',
    )

    assert response.status_code == 200

    member_board.refresh_from_db()

    assert member_board.title == 'Changed by member'
    assert member_board.members.count() == 2


@pytest.mark.django_db
def test_update_board_can_remove_members(
    auth_user_client,
    board_with_members,
    user_profile,
):
    payload = dict(
        members=[
            user_profile.id,
        ],
    )

    response = auth_user_client.patch(
        f'{BOARDS_URL}{board_with_members.id}/',
        payload,
        format='json',
    )

    assert response.status_code == 200

    board_with_members.refresh_from_db()

    assert board_with_members.members.count() == 1
    assert user_profile in board_with_members.members.all()


@pytest.mark.django_db
def test_update_board_fails_when_not_authenticated(client, owned_board):
    payload = dict(
        title='Changed title',
    )

    response = client.patch(
        f'{BOARDS_URL}{owned_board.id}/',
        payload,
        format='json',
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_update_board_returns_403_when_user_has_no_access(
    auth_user_client,
    user_profile,
    private_board,
):
    payload = dict(
        title='Changed title',
        members=[
            user_profile.id,
        ],
    )

    response = auth_user_client.patch(
        f'{BOARDS_URL}{private_board.id}/',
        payload,
        format='json',
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_update_board_returns_404_when_board_does_not_exist(
    auth_user_client,
    user_profile,
):
    payload = dict(
        title='Changed title',
        members=[
            user_profile.id,
        ],
    )

    response = auth_user_client.patch(
        '{BOARDS_URL}999999/',
        payload,
        format='json',
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_update_board_fails_when_title_is_empty(
    auth_user_client,
    owned_board,
    user_profile,
):
    payload = dict(
        title='',
        members=[
            user_profile.id,
        ],
    )

    response = auth_user_client.patch(
        f'{BOARDS_URL}{owned_board.id}/',
        payload,
        format='json',
    )

    assert response.status_code == 400
    assert 'title' in response.data


@pytest.mark.django_db
def test_update_board_fails_when_member_does_not_exist(
    auth_user_client,
    owned_board,
):
    payload = dict(
        members=[
            999999,
        ],
    )

    response = auth_user_client.patch(
        f'{BOARDS_URL}{owned_board.id}/',
        payload,
        format='json',
    )

    assert response.status_code == 400
    assert 'members' in response.data


@pytest.mark.django_db
def test_update_board_returns_500_when_unexpected_error_happens(
    auth_user_client, owned_board, user_profile, force_db_crash
):
    payload = dict(
        title='Changed title',
        members=[
            user_profile.id,
        ],
    )

    with force_db_crash:
        response = auth_user_client.patch(
            f'{BOARDS_URL}{owned_board.id}/',
            payload,
            format='json',
        )

    assert response.status_code == 500
