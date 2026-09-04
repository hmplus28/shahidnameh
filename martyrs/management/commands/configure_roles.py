from django.core.management.base import BaseCommand

from martyrs.signals import configure_martyr_roles


class Command(BaseCommand):
    help = "ایجاد یا همگام‌سازی گروه‌های نویسنده و ناظر شهیدنامه"

    def handle(self, *args, **options):
        configure_martyr_roles()
        self.stdout.write(self.style.SUCCESS("گروه‌ها و مجوزهای نویسنده و ناظر همگام‌سازی شدند."))
