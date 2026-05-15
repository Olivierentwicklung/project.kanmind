import pytest
from kanban_app.boards.models import Board
from kanban_app.tasks.models import Comment, Task


@pytest.mark.django_db
def test_comment_can_be_created(user_profile):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )

    task = Task.objects.create(
        board=board,
        title='Build API',
    )

    comment = Comment.objects.create(
        task=task,
        author=user_profile,
        content='Looks good.',
    )

    assert comment.task == task
    assert comment.author == user_profile
    assert comment.content == 'Looks good.'
    assert comment.created_at is not None


@pytest.mark.django_db
def test_task_can_have_many_comments(user_profile):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )

    task = Task.objects.create(
        board=board,
        title='Build API',
    )

    comment_1 = Comment.objects.create(
        task=task,
        author=user_profile,
        content='First comment',
    )

    comment_2 = Comment.objects.create(
        task=task,
        author=user_profile,
        content='Second comment',
    )

    assert task.comments.count() == 2
    assert comment_1 in task.comments.all()
    assert comment_2 in task.comments.all()


@pytest.mark.django_db
def test_user_profile_can_write_many_comments(user_profile):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )

    task = Task.objects.create(
        board=board,
        title='Build API',
    )

    comment_1 = Comment.objects.create(
        task=task,
        author=user_profile,
        content='First comment',
    )

    comment_2 = Comment.objects.create(
        task=task,
        author=user_profile,
        content='Second comment',
    )

    assert user_profile.comments.count() == 2
    assert comment_1 in user_profile.comments.all()
    assert comment_2 in user_profile.comments.all()


@pytest.mark.django_db
def test_comment_string_representation(user_profile):
    board = Board.objects.create(
        title='Project Board',
        owner=user_profile,
    )

    task = Task.objects.create(
        board=board,
        title='Build API',
    )

    comment = Comment.objects.create(
        task=task,
        author=user_profile,
        content='Looks good.',
    )

    assert str(comment) == f'Comment by {user_profile}'
