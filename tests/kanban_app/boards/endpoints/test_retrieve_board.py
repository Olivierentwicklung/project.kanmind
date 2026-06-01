import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from kanban_app.boards.api.views import BoardDetailView
from kanban_app.tasks.models import Task
from tests.conftest import BOARDS_URL


@pytest.mark.django_db
def test_retrieve_board_performance_regression(
    user,
    board_with_detailed_tasks,
    user_profile,
    second_user_profile,
    django_assert_num_queries,
):
    factory = APIRequestFactory()

    request = factory.get(f'{BOARDS_URL}{board_with_detailed_tasks.id}/')
    force_authenticate(request, user=user)

    view = BoardDetailView.as_view()

    with django_assert_num_queries(5):
        response = view(request, board_id=board_with_detailed_tasks.id)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_retrieve_board_success_as_owner(
    auth_user_client,
    board_with_detailed_tasks,
    user_profile,
    second_user_profile,
):
    response = auth_user_client.get(f'{BOARDS_URL}{board_with_detailed_tasks.id}/')

    assert response.status_code == status.HTTP_200_OK

    data = response.data

    assert data['id'] == board_with_detailed_tasks.id
    assert data['title'] == board_with_detailed_tasks.title
    assert data['owner_id'] == user_profile.id

    assert len(data['members']) == 2

    member_ids = [member['id'] for member in data['members']]
    assert user_profile.id in member_ids
    assert second_user_profile.id in member_ids

    assert len(data['tasks']) == 2

    task_1_data = next(
        task for task in data['tasks'] if task['title'] == 'Write API documentation'
    )

    assert task_1_data['description'] == 'Complete the backend API documentation'
    assert task_1_data['status'] == Task.Status.TODO
    assert task_1_data['priority'] == Task.Priority.HIGH
    assert task_1_data['assignee'] is None
    assert task_1_data['reviewer']['id'] == user_profile.id
    assert task_1_data['due_date'] == '2025-02-25'
    assert task_1_data['comments_count'] == 0


@pytest.mark.django_db
def test_retrieve_board_success_as_member(
    auth_user_client, member_board, second_user_profile
):
    response = auth_user_client.get(f'{BOARDS_URL}{member_board.id}/')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['id'] == member_board.id
    assert response.data['owner_id'] == second_user_profile.id


@pytest.mark.django_db
def test_retrieve_board_includes_comments_count(
    auth_user_client, board_with_commented_task
):
    response = auth_user_client.get(f'{BOARDS_URL}{board_with_commented_task.id}/')

    assert response.status_code == status.HTTP_200_OK

    task_data = response.data['tasks'][0]

    assert task_data['title'] == 'Task with comments'
    assert task_data['comments_count'] == 2


@pytest.mark.django_db
def test_retrieve_board_fails_when_not_authenticated(client, owned_board):
    response = client.get(f'{BOARDS_URL}{owned_board.id}/')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_retrieve_board_returns_403_when_user_has_no_access(
    auth_user_client, user_profile, private_board
):
    response = auth_user_client.get(f'{BOARDS_URL}{private_board.id}/')

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_retrieve_board_returns_404_when_board_does_not_exist(auth_user_client):
    response = auth_user_client.get('{BOARDS_URL}999999/')

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_retrieve_board_returns_500_when_unexpected_error_happens(
    auth_user_client, user_profile, owned_board, force_db_crash
):
    with force_db_crash:
        response = auth_user_client.get(f'{BOARDS_URL}{owned_board.id}/')

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
