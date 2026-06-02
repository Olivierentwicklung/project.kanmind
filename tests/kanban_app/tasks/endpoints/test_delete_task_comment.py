import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from kanban_app.boards.models import Board
from kanban_app.tasks.api.views import TaskCommentDetailView
from kanban_app.tasks.models import Comment, Task
from tests.conftest import TASKS_URL


@pytest.mark.django_db
def test_delete_task_comment_peformance_regressiorn(
    user,
    user_profile,
    django_assert_num_queries,
):
    factory = APIRequestFactory()

    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )
    board.members.add(user_profile)

    task = Task.objects.create(
        board=board,
        title='Task with comments',
    )

    comment = Comment.objects.create(
        task=task,
        author=user_profile,
        content='Comment to delete',
    )

    request = factory.delete(
        f'{TASKS_URL}{task.id}/comments/{comment.id}/',  # type:ignore
    )

    force_authenticate(request, user=user)

    view = TaskCommentDetailView.as_view()

    with django_assert_num_queries(2):
        response = view(request, task_id=task.id, comment_id=comment.id)  # type:ignore

    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_delete_task_comment_success_as_author(
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
        title='Task with comments',
    )

    comment = Comment.objects.create(
        task=task,
        author=user_profile,
        content='Comment to delete',
    )

    response = auth_user_client.delete(
        f'{TASKS_URL}{task.id}/comments/{comment.id}/',  # type:ignore
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.data is None
    assert not Comment.objects.filter(id=comment.id).exists()  # type:ignore


@pytest.mark.django_db
def test_delete_task_comment_fails_when_not_authenticated(
    client,
    user_profile,
):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )

    task = Task.objects.create(
        board=board,
        title='Task with comments',
    )

    comment = Comment.objects.create(
        task=task,
        author=user_profile,
        content='Comment to delete',
    )

    response = client.delete(
        f'{TASKS_URL}{task.id}/comments/{comment.id}/',  # type:ignore
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert Comment.objects.filter(id=comment.id).exists()  # type:ignore


@pytest.mark.django_db
def test_delete_task_comment_returns_403_when_user_is_not_author(
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
        title='Task with comments',
    )

    comment = Comment.objects.create(
        task=task,
        author=second_user_profile,
        content='Comment by another user',
    )

    response = auth_user_client.delete(
        f'{TASKS_URL}{task.id}/comments/{comment.id}/',  # type:ignore
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Comment.objects.filter(id=comment.id).exists()  # type:ignore


@pytest.mark.django_db
def test_delete_task_comment_returns_404_when_task_does_not_exist(
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
        title='Task with comments',
    )

    comment = Comment.objects.create(
        task=task,
        author=user_profile,
        content='Comment to delete',
    )

    response = auth_user_client.delete(
        f'{TASKS_URL}999999/comments/{comment.id}/',  # type:ignore
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert Comment.objects.filter(id=comment.id).exists()  # type:ignore


@pytest.mark.django_db
def test_delete_task_comment_returns_404_when_comment_does_not_exist(
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
        title='Task with comments',
    )

    response = auth_user_client.delete(
        f'{TASKS_URL}{task.id}/comments/999999/',  # type:ignore
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_delete_task_comment_returns_404_when_comment_does_not_belong_to_task(
    auth_user_client,
    user_profile,
):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )
    board.members.add(user_profile)

    task_1 = Task.objects.create(
        board=board,
        title='Task one',
    )

    task_2 = Task.objects.create(
        board=board,
        title='Task two',
    )

    comment = Comment.objects.create(
        task=task_2,
        author=user_profile,
        content='Comment on another task',
    )

    response = auth_user_client.delete(
        f'{TASKS_URL}{task_1.id}/comments/{comment.id}/',  # type:ignore
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert Comment.objects.filter(id=comment.id).exists()  # type:ignore


@pytest.mark.django_db
def test_delete_task_comment_returns_500_when_unexpected_error_happens(
    auth_user_client, user_profile, force_db_crash
):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )
    board.members.add(user_profile)

    task = Task.objects.create(
        board=board,
        title='Task with comments',
    )

    comment = Comment.objects.create(
        task=task,
        author=user_profile,
        content='Comment to delete',
    )

    with force_db_crash:
        response = auth_user_client.delete(
            f'{TASKS_URL}{task.id}/comments/{comment.id}/',  # type:ignore
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
