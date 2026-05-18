from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from kanban_app.boards.models import Board
from kanban_app.tasks.models import Task

from .serializers import TaskCreateSerializer, TaskSerializer


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
