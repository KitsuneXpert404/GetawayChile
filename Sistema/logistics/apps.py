from django.apps import AppConfig


class LogisticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "logistics"
    verbose_name = "Logística"

    def ready(self):
        import logistics.signals  # noqa: F401
