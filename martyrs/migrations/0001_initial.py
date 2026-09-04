# Generated manually for the initial Shahidnameh domain schema.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Martyr",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("first_name", models.CharField(max_length=80, verbose_name="نام")), ("last_name", models.CharField(max_length=100, verbose_name="نام خانوادگی")),
                ("slug", models.SlugField(allow_unicode=True, blank=True, max_length=180, unique=True, verbose_name="شناسه نشانی")),
                ("father_name", models.CharField(blank=True, max_length=100, verbose_name="نام پدر")), ("mother_name", models.CharField(blank=True, max_length=100, verbose_name="نام مادر")),
                ("birth_date", models.DateField(blank=True, null=True, verbose_name="تاریخ تولد")), ("birth_place", models.CharField(blank=True, max_length=160, verbose_name="محل تولد")),
                ("birth_city", models.CharField(blank=True, max_length=100, verbose_name="شهر تولد")), ("birth_province", models.CharField(blank=True, max_length=100, verbose_name="استان تولد")),
                ("child_order", models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="فرزند چندم")), ("father_occupation", models.CharField(blank=True, max_length=120, verbose_name="شغل پدر")),
                ("mother_occupation", models.CharField(blank=True, max_length=120, verbose_name="شغل مادر")), ("scientific_background", models.TextField(blank=True, verbose_name="سوابق علمی و تحصیلی")),
                ("political_positions", models.TextField(blank=True, verbose_name="سمت‌های سیاسی و دفتری")), ("biography_summary", models.TextField(blank=True, verbose_name="خلاصه زندگی‌نامه")),
                ("martyrdom_date", models.DateField(blank=True, null=True, verbose_name="تاریخ شهادت")), ("martyrdom_place", models.CharField(blank=True, max_length=180, verbose_name="محل شهادت")),
                ("martyrdom_manner", models.CharField(blank=True, max_length=220, verbose_name="نحوه شهادت")), ("burial_place", models.CharField(blank=True, max_length=180, verbose_name="محل دفن")),
                ("military_unit", models.CharField(blank=True, max_length=180, verbose_name="تیپ یا لشکر")), ("front_documents", models.TextField(blank=True, verbose_name="مدارک و مستندات جبهه")),
                ("family_life", models.TextField(blank=True, verbose_name="ابعاد خانوادگی")), ("scientific_life", models.TextField(blank=True, verbose_name="ابعاد علمی")),
                ("velayat", models.TextField(blank=True, verbose_name="ولایت‌مداری")), ("frontline_life", models.TextField(blank=True, verbose_name="ابعاد جبهه")),
                ("social_life", models.TextField(blank=True, verbose_name="ابعاد اجتماعی")), ("ethical_traits", models.TextField(blank=True, verbose_name="ویژگی‌ها و ابعاد اخلاقی")),
                ("neighborhood_mosque_quran", models.TextField(blank=True, verbose_name="محله، مسجد و جلسات قرآن")), ("basij_responsibility", models.TextField(blank=True, verbose_name="مسئولیت در بسیج")),
                ("mosque_activity", models.TextField(blank=True, verbose_name="فعالیت در مسجد")), ("school_activity", models.TextField(blank=True, verbose_name="فعالیت در مدرسه")),
                ("university_activity", models.TextField(blank=True, verbose_name="فعالیت در دانشگاه")), ("frontline_activity", models.TextField(blank=True, verbose_name="فعالیت در جبهه")),
                ("teaching_activity", models.TextField(blank=True, verbose_name="سوابق معلمی")), ("religious_practice", models.TextField(blank=True, verbose_name="برخورد با واجبات، مستحبات و مکروهات")),
                ("ramadan_muharram", models.TextField(blank=True, verbose_name="زهد و رفتار در رمضان و محرم")), ("favorite_sports", models.CharField(blank=True, max_length=300, verbose_name="ورزش‌های مورد علاقه")),
                ("testament_text", models.TextField(blank=True, verbose_name="متن کامل وصیت‌نامه")), ("testament_prayer", models.TextField(blank=True, verbose_name="سفارش درباره نماز")),
                ("testament_hijab", models.TextField(blank=True, verbose_name="سفارش درباره حجاب")), ("testament_velayat", models.TextField(blank=True, verbose_name="سفارش درباره ولایت")),
                ("testament_islam", models.TextField(blank=True, verbose_name="سفارش درباره اسلام")), ("testament_rights_debts", models.TextField(blank=True, verbose_name="حق‌الناس و قرض")),
                ("handwritten_notes", models.TextField(blank=True, verbose_name="دست‌نوشته‌ها و حرزها")), ("is_featured", models.BooleanField(default=False, verbose_name="شهید شاخص")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")), ("updated_at", models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش")),
            ],
            options={"verbose_name": "شهید", "verbose_name_plural": "شهدا", "ordering": ["-is_featured", "-martyrdom_date", "last_name", "first_name"]},
        ),
        migrations.CreateModel(
            name="Memory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("category", models.CharField(choices=[("martyr", "خود شهید"), ("comrade", "هم‌رزم"), ("family", "خانواده"), ("friend", "دوست"), ("dream", "خواب و رؤیا")], default="comrade", max_length=20, verbose_name="نوع خاطره")),
                ("narrator", models.CharField(max_length=150, verbose_name="راوی")), ("text", models.TextField(verbose_name="متن خاطره")),
                ("recorded_at", models.DateField(blank=True, null=True, verbose_name="تاریخ ثبت خاطره")), ("is_featured", models.BooleanField(default=False, verbose_name="نمایش در صفحه اصلی")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")),
                ("martyr", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memories", to="martyrs.martyr", verbose_name="شهید")),
            ], options={"verbose_name": "خاطره", "verbose_name_plural": "خاطرات", "ordering": ["-is_featured", "-recorded_at", "-created_at"]},
        ),
        migrations.CreateModel(
            name="MartyrImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(blank=True, upload_to="martyrs/images/%Y/%m/", verbose_name="فایل تصویر")), ("title", models.CharField(blank=True, max_length=160, verbose_name="عنوان")),
                ("description", models.TextField(blank=True, verbose_name="توضیحات")), ("sort_order", models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب نمایش")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")),
                ("martyr", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="martyrs.martyr", verbose_name="شهید")),
            ], options={"verbose_name": "تصویر", "verbose_name_plural": "گالری تصاویر", "ordering": ["sort_order", "-created_at"]},
        ),
        migrations.CreateModel(
            name="MartyrVideo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("video_file", models.FileField(blank=True, upload_to="martyrs/videos/%Y/%m/", verbose_name="فایل ویدئو")), ("external_url", models.URLField(blank=True, verbose_name="پیوند ویدئو")),
                ("title", models.CharField(max_length=160, verbose_name="عنوان")), ("description", models.TextField(blank=True, verbose_name="توضیحات")),
                ("sort_order", models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب نمایش")), ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")),
                ("martyr", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="videos", to="martyrs.martyr", verbose_name="شهید")),
            ], options={"verbose_name": "ویدئو", "verbose_name_plural": "گالری ویدئوها", "ordering": ["sort_order", "-created_at"]},
        ),
        migrations.AddIndex(model_name="martyr", index=models.Index(fields=["last_name", "first_name"], name="martyrs_ma_last_na_d4f6e2_idx")),
        migrations.AddIndex(model_name="martyr", index=models.Index(fields=["birth_province", "birth_city"], name="martyrs_ma_birth_p_6b2b37_idx")),
        migrations.AddIndex(model_name="martyr", index=models.Index(fields=["martyrdom_date"], name="martyrs_ma_martyr_d_b5d659_idx")),
        migrations.AddIndex(model_name="martyr", index=models.Index(fields=["military_unit"], name="martyrs_ma_militar_e0dbf4_idx")),
        migrations.AddIndex(model_name="memory", index=models.Index(fields=["category"], name="martyrs_me_categor_11d3fb_idx")),
    ]
