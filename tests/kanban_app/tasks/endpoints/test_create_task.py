from unittest.mock import Mock

import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from kanban_app.boards.models import Board
from kanban_app.tasks.api.permissions import TaskPermission
from kanban_app.tasks.api.views import TaskCreateView
from kanban_app.tasks.models import Task
from tests.conftest import TASKS_URL


@pytest.mark.django_db
def test_create_task_peformance_regressiorn(
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

    payload = dict(
        board=board.id,  # type:ignore
        title='Review code',
        description='Review the new PR for feature X',
        status=Task.Status.REVIEW,
        priority=Task.Priority.MEDIUM,
        assignee_id=second_user_profile.id,
        reviewer_id=user_profile.id,
        due_date='2025-02-27',
    )

    request = factory.post(
        TASKS_URL,
        payload,
        format='json',
    )

    force_authenticate(request, user=user)

    view = TaskCreateView.as_view()

    with django_assert_num_queries(10):
        response = view(request)

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_create_task_success(
    auth_user_client,
    user_profile,
    second_user_profile,
):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )
    board.members.add(user_profile, second_user_profile)

    payload = dict(
        board=board.id,  # type:ignore
        title='Review code',
        description='Review the new PR for feature X',
        status=Task.Status.REVIEW,
        priority=Task.Priority.MEDIUM,
        assignee_id=second_user_profile.id,
        reviewer_id=user_profile.id,
        due_date='2025-02-27',
    )

    response = auth_user_client.post(
        TASKS_URL,
        payload,
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED

    task = Task.objects.get(id=response.data['id'])

    assert task.board == board
    assert task.title == payload['title']
    assert task.description == payload['description']
    assert task.status == payload['status']
    assert task.priority == payload['priority']
    assert task.assignee == second_user_profile
    assert task.reviewer == user_profile
    assert str(task.due_date) == payload['due_date']

    assert response.data['board'] == board.id  # type:ignore
    assert response.data['title'] == payload['title']
    assert response.data['description'] == payload['description']
    assert response.data['status'] == payload['status']
    assert response.data['priority'] == payload['priority']
    assert response.data['assignee']['id'] == second_user_profile.id
    assert response.data['assignee']['email'] == second_user_profile.user.email
    assert response.data['assignee']['fullname'] == second_user_profile.fullname
    assert response.data['reviewer']['id'] == user_profile.id
    assert response.data['reviewer']['email'] == user_profile.user.email
    assert response.data['reviewer']['fullname'] == user_profile.fullname
    assert response.data['due_date'] == payload['due_date']
    assert response.data['comments_count'] == 0


@pytest.mark.django_db
def test_task_permission_trace_returns_false(user_profile):
    factory = APIRequestFactory()

    request = factory.generic('TRACE', '/tasks/')
    request.user = Mock(userprofile=user_profile)

    task = Mock()
    task.author_id = user_profile.id
    task.board.owner_id = user_profile.id
    task.board.members.filter.return_value.exists.return_value = True

    permission = TaskPermission()

    result = permission.has_object_permission(
        request,
        None,
        task,
    )

    assert result is False


@pytest.mark.django_db
def test_create_task_success_without_assignee_and_reviewer(
    auth_user_client,
    user_profile,
):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )
    board.members.add(user_profile)

    payload = dict(
        board=board.id,  # type: ignore
        title='Open task',
        description='Task without assignee and reviewer',
        status=Task.Status.TODO,
        priority=Task.Priority.LOW,
        due_date='2025-02-27',
    )

    response = auth_user_client.post(
        TASKS_URL,
        payload,
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED

    task = Task.objects.get(id=response.data['id'])

    assert task.assignee is None
    assert task.reviewer is None
    assert response.data['assignee'] is None
    assert response.data['reviewer'] is None


@pytest.mark.django_db
def test_create_task_fails_when_not_authenticated(client, user_profile):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )

    payload = dict(
        board=board.id,  # type:ignore
        title='Review code',
        description='Review the new PR for feature X',
        status=Task.Status.REVIEW,
        priority=Task.Priority.MEDIUM,
    )

    response = client.post(TASKS_URL, payload, format='json')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert Task.objects.count() == 0


@pytest.mark.django_db
def test_create_task_returns_403_when_user_is_not_board_member(
    auth_user_client,
    user_profile,
    second_user_profile,
):
    board = Board.objects.create(
        title='Private Board',
        owner=second_user_profile,
    )
    board.members.add(second_user_profile)

    payload = dict(
        board=board.id,  # type: ignore
        title='Review code',
        description='Review the new PR for feature X',
        status=Task.Status.REVIEW,
        priority=Task.Priority.MEDIUM,
    )

    response = auth_user_client.post(
        TASKS_URL,
        payload,
        format='json',
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Task.objects.count() == 0


@pytest.mark.django_db
def test_create_task_returns_404_when_board_does_not_exist(
    auth_user_client,
):
    payload = dict(
        board=999999,
        title='Review code',
        description='Review the new PR for feature X',
        status=Task.Status.REVIEW,
        priority=Task.Priority.MEDIUM,
    )

    response = auth_user_client.post(
        TASKS_URL,
        payload,
        format='json',
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert Task.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    'missing_field',
    [
        'board',
        'title',
    ],
)
def test_create_task_fails_when_required_field_is_missing(
    auth_user_client,
    user_profile,
    missing_field,
):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )
    board.members.add(user_profile)

    payload = dict(
        board=board.id,  # type:ignore
        title='Review code',
        description='Review the new PR for feature X',
        status=Task.Status.REVIEW,
        priority=Task.Priority.MEDIUM,
    )

    payload.pop(missing_field)

    response = auth_user_client.post(
        TASKS_URL,
        payload,
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert missing_field in response.data
    assert Task.objects.count() == 0


@pytest.mark.django_db
def test_create_task_fails_when_title_is_empty(
    auth_user_client,
    user_profile,
):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )
    board.members.add(user_profile)

    payload = dict(
        board=board.id,  # type:ignore
        title='',
        description='Review the new PR for feature X',
        status=Task.Status.REVIEW,
        priority=Task.Priority.MEDIUM,
    )

    response = auth_user_client.post(
        TASKS_URL,
        payload,
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'title' in response.data
    assert Task.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    'field,value',
    [
        ('status', 'invalid-status'),
        ('priority', 'invalid-priority'),
        ('due_date', 'invalid-date'),
    ],
)
def test_create_task_fails_with_invalid_field_values(
    auth_user_client,
    user_profile,
    field,
    value,
):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )
    board.members.add(user_profile)

    payload = dict(
        board=board.id,  # type:ignore
        title='Review code',
        description='Review the new PR for feature X',
        status=Task.Status.REVIEW,
        priority=Task.Priority.MEDIUM,
        due_date='2025-02-27',
    )

    payload[field] = value

    response = auth_user_client.post(
        TASKS_URL,
        payload,
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert field in response.data
    assert Task.objects.count() == 0


@pytest.mark.django_db
def test_create_task_fails_when_assignee_is_not_board_member(
    auth_user_client,
    user_profile,
    second_user_profile,
    third_user_profile,
):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )
    board.members.add(user_profile)

    payload = dict(
        board=board.id,  # type:ignore
        title='Review code',
        description='Review the new PR for feature X',
        status=Task.Status.REVIEW,
        priority=Task.Priority.MEDIUM,
        assignee_id=third_user_profile.id,
    )

    response = auth_user_client.post(
        TASKS_URL,
        payload,
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'assignee_id' in response.data
    assert Task.objects.count() == 0


@pytest.mark.django_db
def test_create_task_fails_when_reviewer_is_not_board_member(
    auth_user_client,
    user_profile,
    third_user_profile,
):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )
    board.members.add(user_profile)

    payload = dict(
        board=board.id,  # type:ignore
        title='Review code',
        description='Review the new PR for feature X',
        status=Task.Status.REVIEW,
        priority=Task.Priority.MEDIUM,
        reviewer_id=third_user_profile.id,
    )

    response = auth_user_client.post(
        TASKS_URL,
        payload,
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'reviewer_id' in response.data
    assert Task.objects.count() == 0


@pytest.mark.django_db
def test_create_task_returns_500_when_unexpected_error_happens(
    auth_user_client, user_profile, force_db_crash
):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )
    board.members.add(user_profile)

    payload = dict(
        board=board.id,  # type:ignore
        title='Review code',
        description='Review the new PR for feature X',
        status=Task.Status.REVIEW,
        priority=Task.Priority.MEDIUM,
    )

    with force_db_crash:
        response = auth_user_client.post(
            TASKS_URL,
            payload,
            format='json',
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
