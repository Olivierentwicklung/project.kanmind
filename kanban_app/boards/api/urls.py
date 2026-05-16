from django.urls import path

from .views import BoardDetailView, BoardListView

urlpatterns = [
    path(
        'boards/',
        BoardListView.as_view(),
        name='board-list',
    ),
    path(
        'boards/<int:board_id>/',
        BoardDetailView.as_view(),
        name='board-detail',
    ),
]
