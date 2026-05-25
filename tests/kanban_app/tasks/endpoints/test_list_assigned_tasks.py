from datetime import date

import pytest

from kanban_app.boards.models import Board
from kanban_app.tasks.models import Comment, Task

ASSIGNED_TASKS_URL = '/api/tasks/assigned-to-me/'


@pytest.mark.django_db
def test_list_assigned_tasks_success(
    auth_user_client,
    user_profile,
    second_user_profile,
):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )
    board.members.add(user_profile, second_user_profile)

    assigned_task_1 = Task.objects.create(
        board=board,
        title='Task 1',
        description='Description for task 1',
        status=Task.Status.TODO,
        priority=Task.Priority.HIGH,
        assignee=user_profile,
        reviewer=second_user_profile,
        due_date=date(2025, 2, 25),
    )

    assigned_task_2 = Task.objects.create(
        board=board,
        title='Task 2',
        description='Description for task 2',
        status=Task.Status.IN_PROGRESS,
        priority=Task.Priority.MEDIUM,
        assignee=user_profile,
        reviewer=None,
        due_date=date(2025, 2, 20),
    )

    not_assigned_task = Task.objects.create(
        board=board,
        title='Other Task',
        assignee=second_user_profile,
        reviewer=user_profile,
    )

    Comment.objects.create(
        task=assigned_task_1,
        author=user_profile,
        content='First comment',
    )

    response = auth_user_client.get(ASSIGNED_TASKS_URL)

    assert response.status_code == 200
    assert len(response.data) == 2

    task_ids = [task['id'] for task in response.data]

    assert assigned_task_1.id in task_ids  # type:ignore
    assert assigned_task_2.id in task_ids  # type:ignore
    assert not_assigned_task.id not in task_ids  # type:ignore

    task_1_data = next(
        task
        for task in response.data
        if task['id'] == assigned_task_1.id  # type:ignore
    )

    assert task_1_data['board'] == board.id  # type:ignore
    assert task_1_data['title'] == 'Task 1'
    assert task_1_data['description'] == 'Description for task 1'
    assert task_1_data['status'] == Task.Status.TODO
    assert task_1_data['priority'] == Task.Priority.HIGH
    assert task_1_data['assignee']['id'] == user_profile.id
    assert task_1_data['assignee']['email'] == user_profile.user.email
    assert task_1_data['assignee']['fullname'] == user_profile.fullname
    assert task_1_data['reviewer']['id'] == second_user_profile.id
    assert task_1_data['due_date'] == '2025-02-25'
    assert task_1_data['comments_count'] == 1


@pytest.mark.django_db
def test_list_assigned_tasks_returns_empty_list_when_no_tasks_assigned(
    auth_user_client,
    user_profile,
    second_user_profile,
):
    board = Board.objects.create(
        title='Project Board',
        owner=second_user_profile,
    )

    Task.objects.create(
        board=board,
        title='Other Task',
        assignee=second_user_profile,
    )

    response = auth_user_client.get(ASSIGNED_TASKS_URL)

    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db
def test_list_assigned_tasks_fails_when_not_authenticated(client):
    response = client.get(ASSIGNED_TASKS_URL)

    assert response.status_code == 401


@pytest.mark.django_db
def test_list_assigned_tasks_returns_500_when_unexpected_error_happens(
    auth_user_client, user_profile, force_db_crash
):
    with force_db_crash:
        response = auth_user_client.get(ASSIGNED_TASKS_URL)

    assert response.status_code == 500
