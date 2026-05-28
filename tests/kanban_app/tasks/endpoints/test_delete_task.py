import pytest
from rest_framework import status

from kanban_app.boards.models import Board
from kanban_app.tasks.models import Comment, Task
from tests.conftest import TASKS_URL


@pytest.mark.django_db
def test_delete_task_success_as_task_creator(
    auth_user_client,
    user_profile,
    second_user_profile,
):
    board = Board.objects.create(
        title='Project Board',
        owner=second_user_profile,
    )
    board.members.add(user_profile, second_user_profile)

    task = Task.objects.create(
        board=board,
        title='Task to delete',
        author=user_profile,
    )

    response = auth_user_client.delete(
        f'{TASKS_URL}{task.id}/',  # type:ignore
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.data is None
    assert not Task.objects.filter(id=task.id).exists()  # type:ignore


@pytest.mark.django_db
def test_delete_task_success_as_board_owner(
    auth_user_client,
    user_profile,
    second_user_profile,
):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )
    board.members.add(user_profile, second_user_profile)

    task = Task.objects.create(
        board=board,
        title='Task to delete',
        author=second_user_profile,
    )

    response = auth_user_client.delete(
        f'{TASKS_URL}{task.id}/',  # type:ignore
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.data is None
    assert not Task.objects.filter(id=task.id).exists()  # type:ignore


@pytest.mark.django_db
def test_delete_task_deletes_related_comments(
    auth_user_client,
    user_profile,
):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )
    board.members.add(user_profile)

    task = Task.objects.create(
        board=board,
        title='Task to delete',
        author=user_profile,
    )

    comment = Comment.objects.create(
        task=task,
        author=user_profile,
        content='Comment to delete',
    )

    response = auth_user_client.delete(
        f'{TASKS_URL}{task.id}/',  # type:ignore
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Task.objects.filter(id=task.id).exists()  # type:ignore
    assert not Comment.objects.filter(id=comment.id).exists()  # type:ignore


@pytest.mark.django_db
def test_delete_task_fails_when_not_authenticated(
    client,
    user_profile,
):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )

    task = Task.objects.create(
        board=board,
        title='Task to delete',
        author=user_profile,
    )

    response = client.delete(
        f'{TASKS_URL}{task.id}/',  # type:ignore
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert Task.objects.filter(id=task.id).exists()  # type:ignore


@pytest.mark.django_db
def test_delete_task_returns_403_when_user_is_only_board_member(
    auth_user_client,
    user_profile,
    second_user_profile,
    third_user_profile,
):
    board = Board.objects.create(
        title='Project Board',
        owner=second_user_profile,
    )
    board.members.add(user_profile, second_user_profile, third_user_profile)

    task = Task.objects.create(
        board=board,
        title='Task to delete',
        author=third_user_profile,
    )

    response = auth_user_client.delete(
        f'{TASKS_URL}{task.id}/',  # type:ignore
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Task.objects.filter(id=task.id).exists()  # type:ignore


@pytest.mark.django_db
def test_delete_task_returns_404_when_task_does_not_exist(
    auth_user_client,
):
    response = auth_user_client.delete('{TASKS_URL}999999/')

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_delete_task_returns_500_when_unexpected_error_happens(
    auth_user_client, user_profile, force_db_crash
):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )
    board.members.add(user_profile)

    task = Task.objects.create(
        board=board,
        title='Task to delete',
        author=user_profile,
    )

    with force_db_crash:
        response = auth_user_client.delete(
            f'{TASKS_URL}{task.id}/',  # type:ignore
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
