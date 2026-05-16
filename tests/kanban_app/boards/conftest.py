from datetime import date

import pytest

from kanban_app.boards.models import Board
from kanban_app.tasks.models import Comment, Task


@pytest.fixture
def owned_board(user_profile):
    board = Board.objects.create(
        title='Owned Board',
        owner=user_profile,
    )

    board.members.add(user_profile)

    return board


@pytest.fixture
def member_board(user_profile, second_user_profile):
    board = Board.objects.create(
        title='Member Board',
        owner=second_user_profile,
    )

    board.members.add(user_profile, second_user_profile)

    return board


@pytest.fixture
def private_board(second_user_profile):
    return Board.objects.create(
        title='Private Board',
        owner=second_user_profile,
    )


@pytest.fixture
def board_with_members(user_profile, second_user_profile):
    board = Board.objects.create(
        title='Project X',
        owner=user_profile,
    )
    board.members.add(user_profile, second_user_profile)
    return board


@pytest.fixture
def board_with_tasks(user_profile):
    board = Board.objects.create(
        title='Project X',
        owner=user_profile,
    )

    board.members.add(user_profile)

    Task.objects.create(
        board=board,
        title='Task 1',
        status=Task.Status.TODO,
        priority=Task.Priority.HIGH,
    )

    Task.objects.create(
        board=board,
        title='Task 2',
        status=Task.Status.TODO,
        priority=Task.Priority.MEDIUM,
    )

    Task.objects.create(
        board=board,
        title='Task 3',
        status=Task.Status.DONE,
        priority=Task.Priority.LOW,
    )

    return board


@pytest.fixture
def board_with_detailed_tasks(board_with_members, user_profile):
    Task.objects.create(
        board=board_with_members,
        title='Write API documentation',
        description='Complete the backend API documentation',
        status=Task.Status.TODO,
        priority=Task.Priority.HIGH,
        assignee=None,
        reviewer=user_profile,
        due_date=date(2025, 2, 25),
    )

    Task.objects.create(
        board=board_with_members,
        title='Review code',
        description='Review the new PR for feature X',
        status=Task.Status.REVIEW,
        priority=Task.Priority.MEDIUM,
        assignee=user_profile,
        reviewer=None,
        due_date=date(2025, 2, 27),
    )

    return board_with_members


@pytest.fixture
def board_with_commented_task(owned_board, user_profile):
    task = Task.objects.create(
        board=owned_board,
        title='Task with comments',
    )

    Comment.objects.create(
        task=task,
        author=user_profile,
        content='First comment',
    )

    Comment.objects.create(
        task=task,
        author=user_profile,
        content='Second comment',
    )

    return owned_board
