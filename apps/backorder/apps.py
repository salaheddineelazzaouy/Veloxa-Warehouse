from django.apps import AppConfig


class BackorderConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.backorder"
    label = "backorder"
    verbose_name = "Backorder Tracking"

    def ready(self):
        import apps.backorder.signals  # noqa
