from django.urls import path

from .views import AssignedTasksView, ReviewTasksView

urlpatterns = [
    path(
        'tasks/assigned-to-me/',
        AssignedTasksView.as_view(),
        name='assigned-tasks',
    ),
    path(
        'tasks/reviewing/',
        ReviewTasksView.as_view(),
        name='review-tasks',
    ),
]
