from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
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
    CommentCreateSerializer,
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
    Create a new task.
    """

    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type:ignore
        """
        Define the optimized queryset used to reload the created instance.
        """
        return Task.objects.select_related(
            'board',
            'assignee__user',
            'reviewer__user',
        ).annotate(comments_count=Count('comments', distinct=True))

    def perform_create(self, serializer):
        """
        Save the instance and immediately refresh it from the optimized queryset.
        """
        # 1. Save the instance to the database
        instance = serializer.save()

        # 2. Re-fetch the saved object using the optimized get_queryset() definition
        optimized_instance = self.get_queryset().get(pk=instance.pk)

        # 3. Swap the raw instance with the optimized instance inside the serializer
        # This forces DRF to use the pre-fetched & annotated data for the JSON response
        serializer.instance = optimized_instance


class TaskDetailView(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a task.
    """

    permission_classes = [IsAuthenticated, TaskPermission]

    lookup_url_kwarg = 'task_id'

    def get_serializer_class(self):  # type:ignore
        """Choose the right serializer"""

        if self.request.method == 'PATCH':
            return TaskUpdateSerializer

        return TaskSerializer

    def get_queryset(self):  # type:ignore
        """Defines the optimized query path used by ALL HTTP verbs."""

        # Optimize related object loading and comment aggregation
        return Task.objects.select_related(
            'board',
            'board__owner',
            'assignee__user',
            'reviewer__user',
            'author__user',
        ).annotate(
            comments_count=Count('comments', distinct=True),
        )

    def perform_update(self, serializer):
        """Handles Post-Write Optimization at the View Layer."""
        # A. Serializer runs database mutation safely
        instance = serializer.save()

        # B. View re-fetches instance using the main query path.
        # This safely blows away old prefetch caches and re-links joins in 1 step!
        optimized_instance = self.get_queryset().get(pk=instance.pk)

        # C. Assign the fresh data back to the serializer for an optimized JSON payload
        serializer.instance = optimized_instance


class TaskCommentsView(ListCreateAPIView):
    """
    List and create comments for a task using optimized query flows.
    """

    permission_classes = [IsAuthenticated, TaskPermission, CommentPermission]

    def get_task_and_check_access(self) -> Task:
        """
        Fetch the task and enforce board membership permissions in a single cached step.
        """
        # Return the task instantly if it was already resolved during
        # the request lifecycle
        if hasattr(self, '_cached_task'):
            return self._cached_task

        # Fetch task and follow relation to board to avoid N+1 queries
        task = get_object_or_404(
            Task.objects.select_related('board'), id=self.kwargs['task_id']
        )

        user_profile = getattr(self.request.user, 'userprofile', None)
        board = task.board

        # Extract valid user IDs cleanly to satisfy Pylance/Ruff
        valid_user_ids = set(board.members.values_list('id', flat=True))
        owner_id = getattr(board, 'owner_id', None)
        if owner_id:
            valid_user_ids.add(owner_id)

        # Security Access Enforcement
        if not user_profile or user_profile.id not in valid_user_ids:
            raise PermissionDenied(
                'You must be a board member to access task comments.'
            )

        # Cache instance on the view thread to prevent double-database fetching
        self._cached_task = task
        return task

    def get_serializer_class(self):  # type: ignore
        """Choose the right serializer dynamically based on HTTP method."""
        if self.request.method == 'POST':
            return CommentCreateSerializer
        return CommentSerializer

    def get_serializer_context(self):
        """
        Inject the verified task object directly into the serializer context.
        This provides the data needed for your CommentCreateSerializer
        super().create() hook.
        """
        context = super().get_serializer_context()
        context['task'] = self.get_task_and_check_access()
        return context

    def get_queryset(self):  # type: ignore
        """
        Return the optimized list of comments for the targeted task.
        """
        task = self.get_task_and_check_access()

        return (
            Comment.objects.filter(task=task)
            .select_related('author__user')
            .order_by('created_at')
        )

    def perform_create(self, serializer):
        """
        Save the comment and instantly refresh its representation using
        the optimized serialization layout.
        """
        # Save using the data already stored inside serializer.context['task']
        comment = serializer.save()

        # Re-fetch the comment with all optimized select_related fields loaded
        optimized_comment = Comment.objects.select_related('author__user').get(
            pk=comment.pk
        )

        # Swap raw object with optimized data structure so DRF uses the correct
        # format in the JSON response
        serializer.instance = optimized_comment


class TaskCommentDetailView(DestroyAPIView):
    """
    Delete a task comment safely with ownership checks.
    """

    permission_classes = [IsAuthenticated, CommentPermission]
    lookup_url_kwarg = 'comment_id'

    def get_object(self) -> Comment:  # type: ignore
        """
        Get the task comment by id while ensuring it belongs to the specified task.
        """

        # Ensure the task exists first
        task = get_object_or_404(
            Task,
            id=self.kwargs['task_id'],
        )

        # Retrieve and return the specific comment object
        comment = get_object_or_404(
            Comment,
            id=self.kwargs['comment_id'],
            task=task,
        )

        # IMPORTANT
        self.check_object_permissions(self.request, comment)

        return comment
