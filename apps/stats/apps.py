from django.apps import AppConfig


class StatsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.stats"
    verbose_name = "Statistics"

    def ready(self):
        """Import signals when app is ready."""
        import apps.stats.signals  # noqa: F401

