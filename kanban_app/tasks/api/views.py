from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from kanban_app.boards.models import Board
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
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore
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
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore
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
    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        board_id = request.data.get('board')

        if board_id is not None:
            get_object_or_404(Board, id=board_id)

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            task = serializer.save()

            annotated_task = (
                Task.objects.select_related(
                    'board',
                    'assignee__user',
                    'reviewer__user',
                )
                .annotate(comments_count=Count('comments', distinct=True))
                .get(id=task.id)
            )

            response_serializer = TaskSerializer(
                annotated_task,
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


class TaskDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [
        IsAuthenticated,
        IsTaskBoardMemberOrOwner,
    ]

    lookup_url_kwarg = 'task_id'

    def get_serializer_class(self):  # type:ignore
        if self.request.method == 'PATCH':
            return TaskUpdateSerializer

        return TaskSerializer

    def get_queryset(self):  # type:ignore
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
        task = self.get_object()

        serializer = TaskUpdateSerializer(
            task,
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )

        if serializer.is_valid():
            updated_task = serializer.save()

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
        task = self.get_object()
        user_profile = request.user.userprofile

        is_author = task.author == user_profile
        is_board_owner = task.board.owner == user_profile

        if not is_author and not is_board_owner:
            return Response(
                {
                    'detail': 'Only the task creator or board owner can delete this task.'
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        task.delete()

        return Response(
            None,
            status=status.HTTP_204_NO_CONTENT,
        )


class TaskCommentsView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_task(self):
        return get_object_or_404(Task, id=self.kwargs['task_id'])

    def check_task_access(self, task):
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
        if self.request.method == 'POST':
            return CommentCreateSerializer

        return CommentSerializer

    def get_queryset(self):  # type:ignore
        task = self.get_task()
        self.check_task_access(task)

        return (
            Comment.objects.filter(task=task)
            .select_related('author__user')
            .order_by('created_at')
        )

    def create(self, request, *args, **kwargs):
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
