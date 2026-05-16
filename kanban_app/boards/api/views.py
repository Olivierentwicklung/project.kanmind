from django.db.models import Count, Q
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated

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

        return (
            Board.objects.filter(id__in=accessible_board_ids)
            .select_related('owner')
            .annotate(
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
