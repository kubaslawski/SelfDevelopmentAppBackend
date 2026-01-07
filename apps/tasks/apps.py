from django.apps import AppConfig


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tasks'
    verbose_name = 'Tasks'

    def ready(self):
        try:
            import apps.tasks.signals  # noqa: F401
        except ImportError:
            pass

