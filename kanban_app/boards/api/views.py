from django.db.models import Count, Prefetch, Q
from rest_framework import status
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from kanban_app.boards.models import Board
from kanban_app.tasks.models import Task

from .permissions import BoardPermission
from .serializers import (
    BoardCreateSerializer,
    BoardDetailSerializer,
    BoardSummarySerializer,
    BoardUpdateSerializer,
)


class BoardListView(ListCreateAPIView):
    """
    API view used to list boards and create new boards.
    """

    serializer_class = BoardSummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore
        """Return the boards that the current logged-in user is allowed to see."""

        user_profile = getattr(self.request.user, 'userprofile', None)

        # User can access owned boards and boards where they are a member
        accessible_board_ids = Board.objects.filter(
            Q(owner=user_profile) | Q(members=user_profile)
        ).values('id')

        return self.get_annotated_queryset().filter(id__in=accessible_board_ids)

    def get_serializer_class(self):  # type: ignore
        """Choose which serializer should be used for the current request."""

        if self.request.method == 'POST':
            return BoardCreateSerializer

        return BoardSummarySerializer

    def create(self, request, *args, **kwargs):
        """Create a new board and return the created board as a summary."""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        owner = request.user.userprofile
        members = serializer.validated_data['members']

        board = serializer.save(owner=owner)
        board.members.set(members)

        board = self.get_queryset().get(pk=board.pk)

        response_serializer = BoardSummarySerializer(board)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def get_annotated_queryset(self):
        """
        Return boards with extra calculated statistics.
        This method builds an optimized queryset for Board objects.
        """

        return (
            # Optimize ForeignKey joins
            Board.objects.select_related('owner')
            .annotate(
                # Aggregate board statistics
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


class BoardDetailView(RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific board."""

    permission_classes = [IsAuthenticated, BoardPermission]
    lookup_url_kwarg = 'board_id'

    def get_serializer_class(self):  # type: ignore
        """Choose the right serializer based on the action."""
        if self.request.method in ['PUT', 'PATCH']:
            return BoardUpdateSerializer
        return BoardDetailSerializer

    def get_queryset(self):  # type: ignore
        """Get the board with optimized task relations and comment aggregations."""

        tasks_queryset = Task.objects.select_related(
            'assignee__user',
            'reviewer__user',
        ).annotate(
            comments_count=Count('comments', distinct=True),
        )

        return Board.objects.select_related('owner__user').prefetch_related(
            'members__user',
            Prefetch('tasks', queryset=tasks_queryset),
        )

    def perform_update(self, serializer):
        """Handles Post-Write Optimization at the View Layer."""

        # Serializer save the database records atomically
        instance = serializer.save()

        # View re-fetches instance using the main query path.
        # This safely blows away old prefetch caches and re-links joins
        optimized_instance = self.get_queryset().get(pk=instance.pk)

        # Assign the fresh data back to the serializer for an optimized JSON payload
        serializer.instance = optimized_instance
