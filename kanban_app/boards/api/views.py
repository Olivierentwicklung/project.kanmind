from django.db.models import Q
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated

from kanban_app.boards.models import Board

from .serializers import BoardListSerializer


class BoardListView(ListCreateAPIView):
    serializer_class = BoardListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore
        user_profile = self.request.user.userprofile  # type: ignore

        return Board.objects.filter(
            Q(owner=user_profile) | Q(members=user_profile)
        ).distinct()
