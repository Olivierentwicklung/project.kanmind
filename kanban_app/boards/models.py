from django.db import models

from auth_app.models import UserProfile


class Board(models.Model):
    """
    Represents a collaborative project board.

    A board has:
    - one owner
    - many optional members
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

    def user_has_access(self, user):
        """
        Check if a Django user can access this board.

        A user has access if:
        - they are the board owner
        - or they are one of the board members
        """

        user_profile = getattr(user, 'userprofile', None)

        if not user_profile:
            return False

        return (
            self.owner == user_profile
            or self.members.filter(pk=user_profile.pk).exists()
        )

    def __str__(self):
        """
        Return a readable string representation of the board.
        """

        return self.title
