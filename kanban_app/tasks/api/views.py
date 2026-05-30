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

from kanban_app.boards.models import Board
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
    API view for creating a task.

    The view handles:
    - authentication
    - board lookup
    - 404 if board does not exist
    - 403 if user cannot create tasks on this board
    - optimized response after creation
    """

    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_board(self):
        """
        Find and return the Board object from the board ID sent in the request.
        """

        board_id = self.request.data.get('board')  # type:ignore

        return get_object_or_404(
            Board.objects.prefetch_related('members'),
            pk=board_id,
        )

    def get_serializer_context(self):
        """
        Add the board to the serializer context when it exists.
        """

        context = super().get_serializer_context()

        if hasattr(self, 'board'):
            context['board'] = self.board  # type:ignore

        return context

    def get_queryset(self):  # type: ignore
        """
        Return optimized task queryset for the response.
        """

        return Task.objects.select_related(
            'board',
            'assignee__user',
            'reviewer__user',
        ).annotate(
            comments_count=Count('comments', distinct=True),
        )

    def create(self, request, *args, **kwargs):
        """
        Create a task after board lookup and permission check.

        If the board field is missing, let the serializer return 400.
        """

        board_id = request.data.get('board')

        if board_id is not None:
            board = self.get_board()

            if not board.user_has_access(request.user):
                raise PermissionDenied('You must be a board member to create tasks.')

        return super().create(request, *args, **kwargs)


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
    List and create comments for a task using optimized query flows.
    """

    serializer_class = CommentSerializer

    permission_classes = [IsAuthenticated, TaskPermission, CommentPermission]

    def get_task(self):
        if hasattr(self, '_task'):
            return self._task

        task = get_object_or_404(
            Task.objects.select_related('board'),
            id=self.kwargs['task_id'],
        )

        user_profile = getattr(self.request.user, 'userprofile', None)

        is_owner = task.board.owner_id == getattr(user_profile, 'id', None)
        is_member = task.board.members.filter(
            id=getattr(user_profile, 'id', None)
        ).exists()

        if not user_profile or not (is_owner or is_member):
            raise PermissionDenied(
                'You must be a board member to access task comments.'
            )

        self._task = task
        return task

    def get_queryset(self):  # type:ignore
        return (
            Comment.objects.filter(task=self.get_task())
            .select_related('author__user')
            .order_by('created_at')
        )

    def perform_create(self, serializer):
        task = self.get_task()
        author = getattr(self.request.user, 'userprofile', None)

        serializer.save(task=task, author=author)


class TaskCommentDetailView(DestroyAPIView):
    """
    Delete a task comment safely with ownership checks.
    """

    serializer_class = CommentSerializer
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
