"""تنظیم گروه‌ها و مجوزهای پیش‌فرض مدیریت محتوای شهیدنامه."""
from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver


ROLE_PERMISSIONS = {
    "نویسنده": {
        "martyr": ("add", "change", "view"),
        "memory": ("add", "change", "view"),
        "martyrimage": ("add", "change", "view"),
        "martyrvideo": ("add", "change", "view"),
    },
    "ناظر": {
        "martyr": ("view",),
        "memory": ("view",),
        "martyrimage": ("view",),
        "martyrvideo": ("view",),
    },
}


def configure_martyr_roles():
    """ایجاد/به‌روزرسانی گروه‌های نقش و همگام‌سازی دقیق مجوزهایشان."""
    for role_name, models in ROLE_PERMISSIONS.items():
        permission_codes = [f"{action}_{model}" for model, actions in models.items() for action in actions]
        permissions = Permission.objects.filter(content_type__app_label="martyrs", codename__in=permission_codes)
        group, _ = Group.objects.get_or_create(name=role_name)
        group.permissions.set(permissions)


@receiver(post_migrate)
def ensure_martyr_roles(sender, **kwargs):
    if sender.name == "martyrs":
        configure_martyr_roles()
