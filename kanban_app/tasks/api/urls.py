from django.urls import path

from .views import AssignedTasksView

urlpatterns = [
    path(
        'tasks/assigned-to-me/',
        AssignedTasksView.as_view(),
        name='assigned-tasks',
    ),
]
