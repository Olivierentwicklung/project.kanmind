from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """
    Stores additional profile information for a user.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )

    # Full name provided during registration
    fullname = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.fullname
