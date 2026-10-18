import django.core.validators
from django.db import migrations, models


def seed_default_elements(apps, schema_editor):
    """ساخت رکورد پیش‌فرض برای همه المان‌های سایت با شفافیت کامل."""
    SiteElement = apps.get_model("martyrs", "SiteElement")
    for key in ("site_logo", "quran_header_icon", "tulip_icon", "martyr_default_photo"):
        SiteElement.objects.get_or_create(key=key, defaults={"opacity": 100})


def unseed(apps, schema_editor):
    SiteElement = apps.get_model("martyrs", "SiteElement")
    SiteElement.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('martyrs', '0009_backgroundimage'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteElement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(choices=[('site_logo', 'لوگوی شهیدنامه'), ('quran_header_icon', 'آیکون آیه قرآن سربرگ'), ('tulip_icon', 'آیکون لاله نوار پایین'), ('martyr_default_photo', 'تصویر پیش\u200cفرض شهید')], max_length=40, unique=True, verbose_name='کلید')),
                ('image', models.ImageField(blank=True, help_text='در صورت خالی بودن، تصویر پیش\u200cفرض سایت نمایش داده می\u200cشود.', upload_to='elements/', verbose_name='تصویر سفارشی')),
                ('opacity', models.PositiveSmallIntegerField(default=100, help_text='۰ = کاملاً نامرئی، ۱۰۰ = نمایش کامل تصویر.', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='شفافیت نمایش (درصد)')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='آخرین ویرایش')),
            ],
            options={
                'verbose_name': 'المان سایت',
                'verbose_name_plural': 'المان\u200cهای سایت',
                'ordering': ['key'],
            },
        ),
        migrations.RunPython(seed_default_elements, unseed),
    ]
