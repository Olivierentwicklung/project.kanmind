from django.urls import path

from .views import BoardListView

urlpatterns = [
    path(
        'boards/',
        BoardListView.as_view(),
        name='board-list',
    ),
]
