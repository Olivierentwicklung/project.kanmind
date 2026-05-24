from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from kanban_app.tasks.models import Comment, Task

from .permissions import IsTaskBoardMemberOrOwner
from .serializers import (
    CommentCreateSerializer,
    CommentSerializer,
    TaskCreateSerializer,
    TaskSerializer,
    TaskUpdateSerializer,
)


class AssignedTasksView(ListAPIView):
    """
    List tasks assigned to the authenticated user.
    """

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore
        """Get List tasks assigned to the authenticated user."""

        user_profile = self.request.user.userprofile  # type: ignore

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
    List tasks assigned to the authenticated reviewer.
    """

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore
        """Get List tasks assigned to the authenticated reviewer."""

        user_profile = self.request.user.userprofile  # type: ignore

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

    permission_classes = [
        IsAuthenticated,
        IsTaskBoardMemberOrOwner,
    ]

    lookup_url_kwarg = 'task_id'

    def get_serializer_class(self):  # type:ignore
        """Choose the right serializer"""

        if self.request.method == 'PATCH':
            return TaskUpdateSerializer

        return TaskSerializer

    def get_queryset(self):  # type:ignore
        """Get the task"""

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

    def partial_update(self, request, *args, **kwargs):
        """Update the task"""

        task = self.get_object()

        serializer = TaskUpdateSerializer(
            task,
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )

        if serializer.is_valid():
            updated_task = serializer.save()

            # Reload updated task with response annotations
            response_task = (
                Task.objects.select_related(
                    'board',
                    'assignee__user',
                    'reviewer__user',
                )
                .annotate(
                    comments_count=Count('comments', distinct=True),
                )
                .get(id=updated_task.id)
            )

            response_serializer = TaskSerializer(
                response_task,
                context=self.get_serializer_context(),
            )

            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def destroy(self, request, *args, **kwargs):
        """Delete the task"""

        task = self.get_object()
        user_profile = request.user.userprofile

        is_author = task.author == user_profile
        is_board_owner = task.board.owner == user_profile

        # Only task authors or board owners can delete tasks
        if not is_author and not is_board_owner:
            return Response(
                {
                    'detail': (
                        'Only the task creator or board owner can delete this task.'
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        task.delete()

        return Response(
            None,
            status=status.HTTP_204_NO_CONTENT,
        )


class TaskCommentsView(ListCreateAPIView):
    """
    List and create comments for a task.
    """

    permission_classes = [IsAuthenticated]

    def get_task(self):
        """Get the task by Id"""

        return get_object_or_404(
            Task,
            id=self.kwargs['task_id'],
        )

    def check_task_access(self, task):
        """
        Ensure the user has access to the task board.
        """

        user_profile = self.request.user.userprofile  # type:ignore
        board = task.board

        if not (
            board.owner == user_profile
            or board.members.filter(id=user_profile.id).exists()
        ):
            raise PermissionDenied(
                'You must be a board member to access task comments.'
            )

    def get_serializer_class(self):  # type:ignore
        """Choose the right serializer"""

        if self.request.method == 'POST':
            return CommentCreateSerializer

        return CommentSerializer

    def get_queryset(self):  # type:ignore
        """Get the task comments"""

        task = self.get_task()
        self.check_task_access(task)

        return (
            Comment.objects.filter(task=task)
            .select_related('author__user')
            .order_by('created_at')
        )

    def create(self, request, *args, **kwargs):
        """Create a task comment"""

        task = self.get_task()
        self.check_task_access(task)

        serializer = CommentCreateSerializer(
            data=request.data,
            context={
                'request': request,
                'task': task,
            },
        )

        if serializer.is_valid():
            comment = serializer.save()

            response_serializer = CommentSerializer(
                comment,
                context=self.get_serializer_context(),
            )

            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class TaskCommentDetailView(DestroyAPIView):
    """
    Delete a task comment.
    """

    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'comment_id'

    def get_object(self):  # type: ignore
        """Get the task comment by id"""

        task = get_object_or_404(
            Task,
            id=self.kwargs['task_id'],
        )

        return get_object_or_404(
            Comment,
            id=self.kwargs['comment_id'],
            task=task,
        )

    def destroy(self, request, *args, **kwargs):
        """Delete a task comment"""

        comment = self.get_object()
        user_profile = request.user.userprofile

        # Only the comment author can delete the comment
        if comment.author != user_profile:
            raise PermissionDenied('Only the comment author can delete this comment.')

        comment.delete()

        return Response(
            None,
            status=status.HTTP_204_NO_CONTENT,
        )
