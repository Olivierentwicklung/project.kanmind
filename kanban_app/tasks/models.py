from django.db import models

from auth_app.models import UserProfile
from kanban_app.boards.models import Board


class Task(models.Model):
    """
    Represents a task within a board.
    """

    class Status(models.TextChoices):
        """Status list of a Task"""

        TODO = 'to-do'
        IN_PROGRESS = 'in-progress'
        REVIEW = 'review'
        DONE = 'done'

    class Priority(models.TextChoices):
        """Priority list of a Task"""

        LOW = 'low'
        MEDIUM = 'medium'
        HIGH = 'high'

    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name='tasks',
    )

    author = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_tasks',
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TODO,
    )

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.LOW,
    )

    assignee = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
    )

    reviewer = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='review_tasks',
    )

    due_date = models.DateField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.title


class Comment(models.Model):
    """
    Represents a comment attached to a task.
    """

    created_at = models.DateTimeField(auto_now_add=True)

    author = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_comments',
    )

    content = models.TextField()

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
    )

    def __str__(self):
        return f'Comment by {self.author}'
