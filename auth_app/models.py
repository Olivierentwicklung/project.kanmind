from django.contrib.auth.models import User
from django.db import models

# Create your models here.


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fullname = models.CharField(
        max_length=255
    )  # the fullname is mandory by the registration

    def __str__(self) -> str:
        return self.fullname
