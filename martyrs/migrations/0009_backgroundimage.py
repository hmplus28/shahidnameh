from django.db import migrations, models
import django.core.validators


def seed_default_backgrounds(apps, schema_editor):
    """ساخت رکورد پیش‌فرض برای همه اسلات‌های پس‌زمینه با شفافیت طراحی اولیه."""
    BackgroundImage = apps.get_model("martyrs", "BackgroundImage")
    defaults = {
        "home_hero": 7,
        "home_page": 12,
        "directory_page": 12,
        "profile_hero": 32,
        "epic_banner": 34,
        "epic_banner_ziyarat": 34,
        "panel_login": 45,
        "hero_arch": 16,
        "eslimi_texture": 9,
        "eslimi_divider": 100,
    }
    for key, opacity in defaults.items():
        BackgroundImage.objects.get_or_create(key=key, defaults={"opacity": opacity})


def unseed(apps, schema_editor):
    BackgroundImage = apps.get_model("martyrs", "BackgroundImage")
    BackgroundImage.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("martyrs", "0008_sitesettings_music_file_alter_sitesettings_music_url"),
    ]

    operations = [
        migrations.CreateModel(
            name="BackgroundImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "key",
                    models.CharField(
                        choices=[
                            ("home_hero", "پس‌زمینه هیرو صفحه اصلی"),
                            ("home_page", "پس‌زمینه محو کل صفحه اصلی"),
                            ("directory_page", "پس‌زمینه محو فهرست شهدا"),
                            ("profile_hero", "پس‌زمینه پرونده شهید (چفیه)"),
                            ("epic_banner", "بنر حماسی صفحه اصلی"),
                            ("epic_banner_ziyarat", "بنر حماسی زیارت‌نامه"),
                            ("panel_login", "پس‌زمینه صفحه ورود پنل"),
                            ("hero_arch", "قاب محراب صفحه اصلی"),
                            ("eslimi_texture", "بافت اسلیمی (تزئینی)"),
                            ("eslimi_divider", "جداکننده اسلیمی"),
                        ],
                        max_length=40,
                        unique=True,
                        verbose_name="کلید",
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True,
                        help_text="در صورت خالی بودن، تصویر پیش‌فرض سایت نمایش داده می‌شود.",
                        upload_to="backgrounds/",
                        verbose_name="تصویر سفارشی",
                    ),
                ),
                (
                    "opacity",
                    models.PositiveSmallIntegerField(
                        default=100,
                        help_text="۰ = کاملاً نامرئی، ۱۰۰ = نمایش کامل تصویر.",
                        validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)],
                        verbose_name="شفافیت نمایش (درصد)",
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش")),
            ],
            options={
                "verbose_name": "تصویر پس‌زمینه",
                "verbose_name_plural": "تصاویر پس‌زمینه",
                "ordering": ["key"],
            },
        ),
        migrations.RunPython(seed_default_backgrounds, unseed),
    ]
