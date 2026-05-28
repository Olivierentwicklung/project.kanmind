import pytest

from kanban_app.boards.models import Board
from kanban_app.tasks.models import Comment, Task
from tests.conftest import BOARDS_URL


@pytest.mark.django_db
def test_delete_board_success_as_owner(
    auth_user_client,
    owned_board,
    user_profile,
):
    task = Task.objects.create(
        board=owned_board,
        title='Task to delete',
    )

    Comment.objects.create(
        task=task,
        author=user_profile,
        content='Comment to delete',
    )

    response = auth_user_client.delete(
        f'{BOARDS_URL}{owned_board.id}/',
    )

    assert response.status_code == 204
    assert response.data is None

    assert not Board.objects.filter(id=owned_board.id).exists()
    assert not Task.objects.filter(id=task.id).exists()  # type: ignore
    assert not Comment.objects.filter(task=task).exists()


@pytest.mark.django_db
def test_delete_board_fails_when_not_authenticated(client, owned_board):
    response = client.delete(
        f'{BOARDS_URL}{owned_board.id}/',
    )

    assert response.status_code == 401
    assert Board.objects.filter(id=owned_board.id).exists()


@pytest.mark.django_db
def test_delete_board_returns_403_when_user_is_member_but_not_owner(
    auth_user_client,
    member_board,
):
    response = auth_user_client.delete(
        f'{BOARDS_URL}{member_board.id}/',
    )

    assert response.status_code == 403
    assert Board.objects.filter(id=member_board.id).exists()


@pytest.mark.django_db
def test_delete_board_returns_403_when_user_has_no_access(
    auth_user_client,
    user_profile,
    private_board,
):
    response = auth_user_client.delete(
        f'{BOARDS_URL}{private_board.id}/',
    )

    assert response.status_code == 403
    assert Board.objects.filter(id=private_board.id).exists()


@pytest.mark.django_db
def test_delete_board_returns_404_when_board_does_not_exist(auth_user_client):
    response = auth_user_client.delete('{BOARDS_URL}999999/')

    assert response.status_code == 404


@pytest.mark.django_db
def test_delete_board_returns_500_when_unexpected_error_happens(
    auth_user_client, owned_board, user_profile, force_db_crash
):
    with force_db_crash:
        response = auth_user_client.delete(
            f'{BOARDS_URL}{owned_board.id}/',
        )

    assert response.status_code == 500
