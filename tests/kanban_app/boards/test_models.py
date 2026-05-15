import pytest

from kanban_app.boards.models import Board


@pytest.mark.django_db
def test_board_can_be_created(user_profile):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )

    assert board.title == 'Project Board'
    assert board.owner == user_profile


@pytest.mark.django_db
def test_board_can_have_members(user_profile, second_user_profile):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )

    board.members.add(user_profile, second_user_profile)

    assert board.members.count() == 2
    assert user_profile in board.members.all()
    assert second_user_profile in board.members.all()


@pytest.mark.django_db
def test_user_profile_can_own_many_boards(user_profile):
    board_1 = Board.objects.create(
        title='Board One',
        owner=user_profile,
    )

    board_2 = Board.objects.create(
        title='Board Two',
        owner=user_profile,
    )

    assert user_profile.owned_boards.count() == 2
    assert board_1 in user_profile.owned_boards.all()
    assert board_2 in user_profile.owned_boards.all()


@pytest.mark.django_db
def test_board_string_representation(user_profile):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )

    assert str(board) == 'Project Board'
