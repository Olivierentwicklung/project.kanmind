import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from kanban_app.boards.models import Board
from kanban_app.tasks.api.views import TaskCommentsView
from kanban_app.tasks.models import Comment, Task
from tests.conftest import TASKS_URL


@pytest.mark.django_db
def test_list_task_comments_peformance_regressiorn(
    user,
    user_profile,
    second_user_profile,
    django_assert_num_queries,
):
    factory = APIRequestFactory()

    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )
    board.members.add(user_profile, second_user_profile)

    task = Task.objects.create(
        board=board,
        title='Task with comments',
    )

    request = factory.get(
        f'{TASKS_URL}{task.id}/comments/',  # type:ignore
    )

    force_authenticate(request, user=user)

    view = TaskCommentsView.as_view()

    with django_assert_num_queries(3):
        response = view(request, task_id=task.id)  # type:ignore

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_list_task_comments_success(
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

    first_comment = Comment.objects.create(
        task=task,
        author=user_profile,
        content='First comment',
    )

    second_comment = Comment.objects.create(
        task=task,
        author=second_user_profile,
        content='Second comment',
    )

    response = auth_user_client.get(
        f'{TASKS_URL}{task.id}/comments/',  # type:ignore
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2

    assert response.data[0]['id'] == first_comment.id  # type:ignore
    assert response.data[0]['author'] == user_profile.fullname
    assert response.data[0]['content'] == 'First comment'
    assert 'created_at' in response.data[0]

    assert response.data[1]['id'] == second_comment.id  # type:ignore
    assert response.data[1]['author'] == second_user_profile.fullname
    assert response.data[1]['content'] == 'Second comment'
    assert 'created_at' in response.data[1]


@pytest.mark.django_db
def test_list_task_comments_returns_empty_list_when_task_has_no_comments(
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
        title='Task without comments',
    )

    response = auth_user_client.get(
        f'{TASKS_URL}{task.id}/comments/',  # type:ignore
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data == []


@pytest.mark.django_db
def test_list_task_comments_fails_when_not_authenticated(
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

    response = client.get(
        f'{TASKS_URL}{task.id}/comments/',  # type:ignore
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_list_task_comments_returns_403_when_user_is_not_board_member(
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

    response = auth_user_client.get(
        f'{TASKS_URL}{task.id}/comments/',  # type:ignore
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_list_task_comments_returns_404_when_task_does_not_exist(
    auth_user_client,
):
    response = auth_user_client.get(
        '{TASKS_URL}999999/comments/',
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_list_task_comments_are_sorted_chronologically(
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

    first_comment = Comment.objects.create(
        task=task,
        author=user_profile,
        content='First comment',
    )

    second_comment = Comment.objects.create(
        task=task,
        author=user_profile,
        content='Second comment',
    )

    response = auth_user_client.get(
        f'{TASKS_URL}{task.id}/comments/',  # type:ignore
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data[0]['id'] == first_comment.id  # type:ignore
    assert response.data[1]['id'] == second_comment.id  # type:ignore


@pytest.mark.django_db
def test_list_task_comments_returns_500_when_unexpected_error_happens(
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

    with force_db_crash:
        response = auth_user_client.get(
            f'{TASKS_URL}{task.id}/comments/',  # type:ignore
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
