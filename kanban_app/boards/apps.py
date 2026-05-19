from django.apps import AppConfig


class BoardsConfig(AppConfig):
    """Kanban app Board configuration"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kanban_app.boards'
    label = 'boards'
