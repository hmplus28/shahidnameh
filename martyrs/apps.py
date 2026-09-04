from django.apps import AppConfig


class MartyrsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "martyrs"
    verbose_name = "شهدا و یادمان‌ها"

    def ready(self):
        from . import signals  # noqa: F401
