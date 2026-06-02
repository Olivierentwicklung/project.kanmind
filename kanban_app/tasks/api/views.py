from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated

from kanban_app.tasks.models import Comment, Task

from .permissions import CommentPermission, TaskPermission
from .serializers import (
    CommentSerializer,
    TaskCreateSerializer,
    TaskSerializer,
    TaskUpdateSerializer,
)


class AssignedTasksView(ListAPIView):
    """
    API view for listing tasks assigned to the currently logged-in user.
    """

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore
        """Return all tasks assigned to the authenticated user."""

        user_profile = getattr(self.request.user, 'userprofile', None)

        return (
            Task.objects.filter(assignee=user_profile)
            .select_related(
                'board',
                'assignee__user',
                'reviewer__user',
            )
            .annotate(
                comments_count=Count('comments', distinct=True),
            )
        )


class ReviewTasksView(ListAPIView):
    """
    API view for listing tasks where the current user is the reviewer.
    """

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore
        """Return all tasks assigned to the authenticated user as reviewer."""

        user_profile = getattr(self.request.user, 'userprofile', None)

        return (
            Task.objects.filter(reviewer=user_profile)
            .select_related(
                'board',
                'assignee__user',
                'reviewer__user',
            )
            .annotate(
                comments_count=Count('comments', distinct=True),
            )
        )


class TaskCreateView(CreateAPIView):
    """
    API view for creating tasks.

    Access is restricted to authenticated users who are
    members of the specified board or the board owner.

    The authenticated user's profile is automatically
    assigned as the task author.
    """

    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated, TaskPermission]

    def perform_create(self, serializer):
        """
        Save the task with the authenticated user's profile
        as the author.
        """
        serializer.save(author=self.request.user.userprofile)  # type:ignore


class TaskDetailView(RetrieveUpdateDestroyAPIView):
    """
    API view used to retrieve, update, or delete a single task.

    Supported actions:
    - GET: retrieve task details
    - PATCH: partially update task fields
    - PUT: fully update task fields
    - DELETE: delete the task
    """

    permission_classes = [IsAuthenticated, TaskPermission]
    lookup_url_kwarg = 'task_id'

    def get_serializer_class(self):  # type: ignore
        """
        Return the correct serializer depending on the request method.
        """

        if self.request.method in ['PATCH', 'PUT']:
            return TaskUpdateSerializer

        return TaskSerializer

    def get_queryset(self):  # type: ignore
        """
        Return the optimized queryset used to retrieve task objects.

        Object permissions are handled by TaskPermission.
        """

        return (
            Task.objects.select_related(
                'board',
                'board__owner',
                'assignee__user',
                'reviewer__user',
                'author__user',
            )
            .prefetch_related(
                'board__members',
            )
            .annotate(
                comments_count=Count('comments', distinct=True),
            )
        )

    def perform_update(self, serializer):
        """
        Save the task update and refresh the instance with optimized relations.

        This makes sure the response contains fresh nested assignee/reviewer
        data and the latest comments_count value.
        """

        instance = serializer.save()

        serializer.instance = self.get_queryset().get(pk=instance.pk)


class TaskCommentsView(ListCreateAPIView):
    """
    List and create comments for a task.

    Access is restricted to users who have permission to
    access the associated task.
    """

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, TaskPermission]

    def get_task(self):
        """
        Retrieve the task referenced in the URL and verify
        that the current user has permission to access it.

        Returns:
            Task: The requested task instance.

        Raises:
            Http404: If the task does not exist.
            PermissionDenied: If the user cannot access the task.
        """
        task = get_object_or_404(
            Task.objects.select_related('board').prefetch_related('board__members'),
            id=self.kwargs['task_id'],  # type: ignore
        )

        self.check_object_permissions(self.request, task)

        return task

    def get_queryset(self):  # type: ignore
        """
        Return all comments belonging to the requested task,
        ordered by creation date.
        """
        return (
            Comment.objects.filter(task=self.get_task())
            .select_related('author__user')
            .order_by('created_at')
        )

    def perform_create(self, serializer):
        """
        Create a comment for the requested task and assign
        the authenticated user's profile as the author.
        """
        serializer.save(
            task=self.get_task(),
            author=self.request.user.userprofile,  # type: ignore
        )


class TaskCommentDetailView(DestroyAPIView):
    """
    Delete a comment belonging to a specific task.

    Only the comment author is allowed to delete the comment.
    """

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, CommentPermission]
    lookup_url_kwarg = 'comment_id'

    def get_queryset(self):  # type: ignore
        """
        Return comments that belong to the task specified in
        the URL.
        """
        return Comment.objects.filter(task_id=self.kwargs['task_id']).select_related(
            'author__user'
        )
