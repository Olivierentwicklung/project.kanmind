from django.db import models

from auth_app.models import UserProfile


class Board(models.Model):
    """
    Represents a collaborative project board.
    """

    title = models.CharField(max_length=255)

    owner = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='owned_boards',
    )

    members = models.ManyToManyField(
        UserProfile,
        related_name='member_boards',
        blank=True,
    )

    def __str__(self):
        return self.title
