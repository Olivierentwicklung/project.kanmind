from django.db.models import Count, Q
from rest_framework import status
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from kanban_app.boards.models import Board
from kanban_app.tasks.models import Task

from .serializers import BoardListSerializer


class BoardListView(ListCreateAPIView):
    serializer_class = BoardListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore
        user_profile = self.request.user.userprofile  # type: ignore

        accessible_board_ids = Board.objects.filter(
            Q(owner=user_profile) | Q(members=user_profile)
        ).values('id')

        return self.get_annotated_queryset().filter(id__in=accessible_board_ids)

    def create(self, request, *args, **kwargs):
        serializer = BoardListSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )

        if serializer.is_valid():
            board = serializer.save()

            annotated_board = self.get_annotated_queryset().get(id=board.id)  # type: ignore

            response_serializer = BoardListSerializer(
                annotated_board,
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

    def get_annotated_queryset(self):
        return (
            Board.objects.select_related('owner')  # optimization ForeignKey
            .annotate(  # optimization ManyToMany and reverse FK
                member_count=Count('members', distinct=True),
                ticket_count=Count('tasks', distinct=True),
                tasks_to_do_count=Count(
                    'tasks',
                    filter=Q(tasks__status=Task.Status.TODO),
                    distinct=True,
                ),
                tasks_high_prio_count=Count(
                    'tasks',
                    filter=Q(tasks__priority=Task.Priority.HIGH),
                    distinct=True,
                ),
            )
            .distinct()
        )
