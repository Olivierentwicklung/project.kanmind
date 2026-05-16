import pytest

from kanban_app.boards.models import Board
from kanban_app.tasks.models import Task


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
