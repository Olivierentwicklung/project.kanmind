import pytest

BOARDS_URL = '/api/boards/'


@pytest.mark.django_db
def test_list_boards_success_as_owner(
    auth_user_client,
    board_with_tasks,
    user_profile,
):
    response = auth_user_client.get(BOARDS_URL)

    assert response.status_code == 200
    assert len(response.data) == 1

    board_data = response.data[0]

    assert board_data['id'] == board_with_tasks.id
    assert board_data['title'] == 'Project X'
    assert board_data['member_count'] == 1
    assert board_data['ticket_count'] == 3
    assert board_data['tasks_to_do_count'] == 2
    assert board_data['tasks_high_prio_count'] == 1
    assert board_data['owner_id'] == user_profile.id


@pytest.mark.django_db
def test_list_boards_success_as_member(
    auth_user_client,
    member_board,
    second_user_profile,
):
    response = auth_user_client.get(BOARDS_URL)

    assert response.status_code == 200

    board_data = response.data[0]

    assert board_data['id'] == member_board.id
    assert board_data['member_count'] == 2
    assert board_data['owner_id'] == second_user_profile.id


@pytest.mark.django_db
def test_list_boards_returns_only_accessible_boards(
    auth_user_client,
    owned_board,
    member_board,
    private_board,
):
    response = auth_user_client.get(BOARDS_URL)

    assert response.status_code == 200

    board_ids = [board['id'] for board in response.data]

    assert owned_board.id in board_ids
    assert member_board.id in board_ids
    assert private_board.id not in board_ids


@pytest.mark.django_db
def test_list_boards_returns_empty_list_when_user_has_no_boards(
    auth_user_client,
    user_profile,
    private_board,
):
    response = auth_user_client.get(BOARDS_URL)

    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db
def test_list_boards_fails_when_not_authenticated(client):
    response = client.get(BOARDS_URL)

    assert response.status_code == 401


@pytest.mark.django_db
def test_list_boards_returns_500_when_unexpected_error_happens(
    auth_user_client, force_db_crash
):

    with force_db_crash:
        response = auth_user_client.get(BOARDS_URL)

    assert response.status_code == 500
