from unittest.mock import patch

import pytest

from kanban_app.boards.models import Board
from kanban_app.tasks.models import Task

TASKS_URL = '/api/tasks/'


@pytest.mark.django_db
def test_update_task_success(
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
        title='Old title',
        description='Old description',
        status=Task.Status.REVIEW,
        priority=Task.Priority.MEDIUM,
        assignee=user_profile,
        reviewer=second_user_profile,
        due_date='2025-02-27',
    )

    payload = dict(
        title='Finish code review',
        description='Finish checking the PR and give feedback',
        status=Task.Status.DONE,
        priority=Task.Priority.HIGH,
        assignee_id=second_user_profile.id,
        reviewer_id=user_profile.id,
        due_date='2025-02-28',
    )

    response = auth_user_client.patch(
        f'{TASKS_URL}{task.id}/',  # type:ignore
        payload,
        format='json',
    )

    assert response.status_code == 200

    task.refresh_from_db()

    assert task.title == payload['title']
    assert task.description == payload['description']
    assert task.status == payload['status']
    assert task.priority == payload['priority']
    assert task.assignee == second_user_profile
    assert task.reviewer == user_profile
    assert str(task.due_date) == payload['due_date']

    assert response.data['id'] == task.id  # type:ignore
    assert response.data['title'] == payload['title']
    assert response.data['description'] == payload['description']
    assert response.data['status'] == payload['status']
    assert response.data['priority'] == payload['priority']
    assert response.data['assignee']['id'] == second_user_profile.id
    assert response.data['reviewer']['id'] == user_profile.id
    assert response.data['due_date'] == payload['due_date']


@pytest.mark.django_db
def test_update_task_success_with_partial_payload(
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
        title='Old title',
        description='Old description',
        status=Task.Status.TODO,
        priority=Task.Priority.LOW,
    )

    payload = dict(
        title='Changed title',
    )

    response = auth_user_client.patch(
        f'{TASKS_URL}{task.id}/',  # type:ignore
        payload,
        format='json',
    )

    assert response.status_code == 200

    task.refresh_from_db()

    assert task.title == 'Changed title'
    assert task.description == 'Old description'
    assert task.status == Task.Status.TODO
    assert task.priority == Task.Priority.LOW


@pytest.mark.django_db
def test_update_task_fails_when_board_change_is_sent(
    auth_user_client,
    user_profile,
):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )
    board.members.add(user_profile)

    other_board = Board.objects.create(
        title='Other Board',
        owner=user_profile,
    )
    other_board.members.add(user_profile)

    task = Task.objects.create(
        board=board,
        title='Task',
    )

    payload = dict(
        board=other_board.id,  # type:ignore
    )

    response = auth_user_client.patch(
        f'{TASKS_URL}{task.id}/',  # type:ignore
        payload,
        format='json',
    )

    assert response.status_code == 400
    assert 'board' in response.data

    task.refresh_from_db()
    assert task.board == board


@pytest.mark.django_db
def test_update_task_fails_when_not_authenticated(client, user_profile):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )

    task = Task.objects.create(
        board=board,
        title='Task',
    )

    payload = dict(
        title='Changed title',
    )

    response = client.patch(
        f'{TASKS_URL}{task.id}/',  # type:ignore
        payload,
        format='json',
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_update_task_returns_403_when_user_is_not_board_member(
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
        title='Private Task',
    )

    payload = dict(
        title='Changed title',
    )

    response = auth_user_client.patch(
        f'{TASKS_URL}{task.id}/',  # type:ignore
        payload,
        format='json',
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_update_task_returns_404_when_task_does_not_exist(auth_user_client):
    payload = dict(
        title='Changed title',
    )

    response = auth_user_client.patch(
        '{TASKS_URL}999999/',
        payload,
        format='json',
    )

    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize(
    'field,value',
    [
        ('title', ''),
        ('status', 'invalid-status'),
        ('priority', 'invalid-priority'),
        ('due_date', 'invalid-date'),
    ],
)
def test_update_task_fails_with_invalid_field_values(
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

    task = Task.objects.create(
        board=board,
        title='Task',
        status=Task.Status.TODO,
        priority=Task.Priority.LOW,
    )

    payload = dict(field=value)

    response = auth_user_client.patch(
        f'{TASKS_URL}{task.id}/',  # type:ignore
        payload,
        format='json',
    )

    assert response.status_code == 400
    assert field in response.data


@pytest.mark.django_db
def test_update_task_fails_when_assignee_is_not_board_member(
    auth_user_client,
    user_profile,
    third_user_profile,
):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )
    board.members.add(user_profile)

    task = Task.objects.create(
        board=board,
        title='Task',
    )

    payload = dict(assignee_id=third_user_profile.id)

    response = auth_user_client.patch(
        f'{TASKS_URL}{task.id}/',  # type:ignore
        payload,
        format='json',
    )

    assert response.status_code == 400
    assert 'assignee_id' in response.data


@pytest.mark.django_db
def test_update_task_fails_when_reviewer_is_not_board_member(
    auth_user_client,
    user_profile,
    third_user_profile,
):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )
    board.members.add(user_profile)

    task = Task.objects.create(
        board=board,
        title='Task',
    )

    payload = dict(reviewer_id=third_user_profile.id)

    response = auth_user_client.patch(
        f'{TASKS_URL}{task.id}/',  # type:ignore
        payload,
        format='json',
    )

    assert response.status_code == 400
    assert 'reviewer_id' in response.data


@pytest.mark.django_db
def test_update_task_returns_500_when_unexpected_error_happens(
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
        title='Task',
    )

    payload = dict(title='Changed title')

    with patch(
        'kanban_app.tasks.api.views.TaskDetailView.get_queryset',
        side_effect=Exception('Unexpected database error'),
    ):
        response = auth_user_client.patch(
            f'{TASKS_URL}{task.id}/',  # type:ignore
            payload,
            format='json',
        )

    assert response.status_code == 500
