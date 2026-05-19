from django.apps import AppConfig


class TasksConfig(AppConfig):
    """Kanban app Task configuration"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kanban_app.tasks'
    label = 'tasks'
