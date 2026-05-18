from django.db import models

from auth_app.models import UserProfile
from kanban_app.boards.models import Board

# Create your models here.


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = 'TODO', 'to-do'
        IN_PROGRESS = 'IN_PROGRESS', 'in-progress'
        REVIEW = 'REVIEW', 'review'
        DONE = 'DONE', 'done'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'low'
        MEDIUM = 'MEDIUM', 'medium'
        HIGH = 'HIGH', 'high'

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
        if self.author:
            return f'Comment by {self.author}'

        return 'Comment by deleted user'
