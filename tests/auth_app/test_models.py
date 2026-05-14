import pytest

from auth_app.models import UserProfile


@pytest.mark.django_db
def test_user_profile_can_be_created(user):
    user_profile = UserProfile.objects.create(user=user, fullname='Example User')

    assert user_profile.user == user
    assert user_profile.fullname == 'Example User'


@pytest.mark.django_db
def test_user_has_one_user_profile(user):
    user_profile = UserProfile.objects.create(user=user, fullname='Example User')

    assert user.userprofile == user_profile


@pytest.mark.django_db
def test_user_profile_string_representation(user):
    user_profile = UserProfile.objects.create(user=user, fullname='Example User')

    assert str(user_profile) == 'Example User'
