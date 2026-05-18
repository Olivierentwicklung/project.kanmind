from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from kanban_app.boards.models import Board
from kanban_app.tasks.models import Task

from .permissions import IsTaskBoardMemberOrOwner
from .serializers import TaskCreateSerializer, TaskSerializer, TaskUpdateSerializer


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
            'assignee__user',
            'reviewer__user',
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
