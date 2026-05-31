import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from kanban_app.boards.api.views import BoardDetailView
from kanban_app.boards.models import Board
from kanban_app.tasks.models import Comment, Task
from tests.conftest import BOARDS_URL


@pytest.mark.django_db
def test_delete_board_performance_regression(
    user,
    owned_board,
    user_profile,
    django_assert_num_queries,
):
    factory = APIRequestFactory()

    task = Task.objects.create(
        board=owned_board,
        title='Task to delete',
    )

    Comment.objects.create(
        task=task,
        author=user_profile,
        content='Comment to delete',
    )

    request = factory.delete(
        f'{BOARDS_URL}{owned_board.id}/',
    )
    force_authenticate(request, user=user)

    view = BoardDetailView.as_view()

    with django_assert_num_queries(10):
        response = view(request, board_id=owned_board.id)

    assert response.status_code == status.HTTP_204_NO_CONTENT


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

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.data is None

    assert not Board.objects.filter(id=owned_board.id).exists()
    assert not Task.objects.filter(id=task.id).exists()  # type: ignore
    assert not Comment.objects.filter(task=task).exists()


@pytest.mark.django_db
def test_delete_board_fails_when_not_authenticated(client, owned_board):
    response = client.delete(
        f'{BOARDS_URL}{owned_board.id}/',
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert Board.objects.filter(id=owned_board.id).exists()


@pytest.mark.django_db
def test_delete_board_returns_403_when_user_is_member_but_not_owner(
    auth_user_client,
    member_board,
):
    response = auth_user_client.delete(
        f'{BOARDS_URL}{member_board.id}/',
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
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

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Board.objects.filter(id=private_board.id).exists()


@pytest.mark.django_db
def test_delete_board_returns_404_when_board_does_not_exist(auth_user_client):
    response = auth_user_client.delete('{BOARDS_URL}999999/')

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_delete_board_returns_500_when_unexpected_error_happens(
    auth_user_client, owned_board, user_profile, force_db_crash
):
    with force_db_crash:
        response = auth_user_client.delete(
            f'{BOARDS_URL}{owned_board.id}/',
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
