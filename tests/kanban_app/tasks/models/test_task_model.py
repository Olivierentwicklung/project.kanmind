import pytest
from kanban_app.boards.models import Board
from kanban_app.tasks.models import Task


@pytest.mark.django_db
def test_task_can_be_created(user_profile, second_user_profile):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )

    task = Task.objects.create(
        board=board,
        title='Build API',
        description='Create the task endpoint',
        status=Task.Status.TODO,
        priority=Task.Priority.MEDIUM,
        assignee=user_profile,
        reviewer=second_user_profile,
    )

    assert task.board == board
    assert task.title == 'Build API'
    assert task.description == 'Create the task endpoint'
    assert task.status == Task.Status.TODO
    assert task.priority == Task.Priority.MEDIUM
    assert task.assignee == user_profile
    assert task.reviewer == second_user_profile


@pytest.mark.django_db
def test_board_can_have_many_tasks(user_profile):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )

    task_1 = Task.objects.create(
        board=board,
        title='Task One',
    )

    task_2 = Task.objects.create(
        board=board,
        title='Task Two',
    )

    assert board.tasks.count() == 2
    assert task_1 in board.tasks.all()
    assert task_2 in board.tasks.all()


@pytest.mark.django_db
def test_user_profile_can_be_assigned_to_many_tasks(user_profile):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )

    task_1 = Task.objects.create(
        board=board,
        title='Task One',
        assignee=user_profile,
    )

    task_2 = Task.objects.create(
        board=board,
        title='Task Two',
        assignee=user_profile,
    )

    assert user_profile.assigned_tasks.count() == 2
    assert task_1 in user_profile.assigned_tasks.all()
    assert task_2 in user_profile.assigned_tasks.all()


@pytest.mark.django_db
def test_user_profile_can_review_many_tasks(user_profile):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )

    task_1 = Task.objects.create(
        board=board,
        title='Task One',
        reviewer=user_profile,
    )

    task_2 = Task.objects.create(
        board=board,
        title='Task Two',
        reviewer=user_profile,
    )

    assert user_profile.review_tasks.count() == 2
    assert task_1 in user_profile.review_tasks.all()
    assert task_2 in user_profile.review_tasks.all()


@pytest.mark.django_db
def test_task_string_representation(user_profile):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )

    task = Task.objects.create(
        board=board,
        title='Build API',
    )

    assert str(task) == 'Build API'
