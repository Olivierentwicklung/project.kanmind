import pytest
from rest_framework import status

from kanban_app.boards.models import Board
from kanban_app.tasks.models import Comment, Task
from tests.conftest import TASKS_URL


@pytest.mark.django_db
def test_create_task_comment_success(
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

    payload = {
        'content': 'This is a new task comment.',
    }

    response = auth_user_client.post(
        f'{TASKS_URL}{task.id}/comments/',  # type:ignore
        payload,
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED

    comment = Comment.objects.get(id=response.data['id'])

    assert comment.task == task
    assert comment.author == user_profile
    assert comment.content == payload['content']

    assert response.data['author'] == user_profile.fullname
    assert response.data['content'] == payload['content']
    assert 'created_at' in response.data


@pytest.mark.django_db
def test_create_task_comment_fails_when_content_is_missing(
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

    response = auth_user_client.post(
        f'{TASKS_URL}{task.id}/comments/',  # type:ignore
        {},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'content' in response.data
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_create_task_comment_fails_when_content_is_empty(
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

    payload = {
        'content': '',
    }

    response = auth_user_client.post(
        f'{TASKS_URL}{task.id}/comments/',  # type:ignore
        payload,
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'content' in response.data
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_create_task_comment_fails_when_not_authenticated(
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

    payload = {
        'content': 'This is a new task comment.',
    }

    response = client.post(
        f'{TASKS_URL}{task.id}/comments/',  # type:ignore
        payload,
        format='json',
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_create_task_comment_returns_403_when_user_is_not_board_member(
    auth_user_client,
    user_profile,
    second_user_profile,
):
    board = Board.objects.create(
        title='Private Board',
        owner=second_user_profile,
    )

    task = Task.objects.create(
        board=board,
        title='Private task',
    )

    payload = {
        'content': 'This is a new task comment.',
    }

    response = auth_user_client.post(
        f'{TASKS_URL}{task.id}/comments/',  # type:ignore
        payload,
        format='json',
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_create_task_comment_returns_404_when_task_does_not_exist(
    auth_user_client,
):
    payload = {
        'content': 'This is a new task comment.',
    }

    response = auth_user_client.post(
        '{TASKS_URL}999999/comments/',
        payload,
        format='json',
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_create_task_comment_returns_500_when_unexpected_error_happens(
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

    payload = {
        'content': 'This is a new task comment.',
    }

    with force_db_crash:
        response = auth_user_client.post(
            f'{TASKS_URL}{task.id}/comments/',  # type:ignore
            payload,
            format='json',
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
