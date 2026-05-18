from django.urls import path

from .views import (
    AssignedTasksView,
    ReviewTasksView,
    TaskCommentsView,
    TaskCreateView,
    TaskDetailView,
)

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
    path('tasks/', TaskCreateView.as_view(), name='task-create'),
    path('tasks/<int:task_id>/', TaskDetailView.as_view(), name='task-detail'),
    path(
        'tasks/<int:task_id>/comments/',
        TaskCommentsView.as_view(),
        name='task-comments',
    ),
]
