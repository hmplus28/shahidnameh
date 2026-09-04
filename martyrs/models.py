from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Martyr(models.Model):
    """پرونده جامع زندگی و شهادت یک شهید."""

    first_name = models.CharField("نام", max_length=80)
    last_name = models.CharField("نام خانوادگی (فعلی)", max_length=100)
    last_name_old = models.CharField("نام خانوادگی قدیم", max_length=100, blank=True)
    profile_image = models.ImageField("تصویر پروفایل", upload_to="martyrs/profiles/%Y/%m/", blank=True)
    slug = models.SlugField("شناسه نشانی", max_length=180, unique=True, allow_unicode=True, blank=True)
    father_name = models.CharField("نام پدر", max_length=100, blank=True)
    mother_name = models.CharField("نام مادر", max_length=100, blank=True)
    birth_date = models.DateField("تاریخ تولد (شمسی)", null=True, blank=True)
    birth_date_hijri = models.CharField("تاریخ تولد (قمری)", max_length=80, blank=True, help_text="مانند: ۱۵ شعبان ۱۳۶۲ قمری")
    birth_province = models.CharField("استان تولد", max_length=100, blank=True)
    birth_county = models.CharField("شهرستان تولد", max_length=100, blank=True)
    birth_city = models.CharField("شهر تولد", max_length=100, blank=True)
    birth_village = models.CharField("روستای تولد", max_length=100, blank=True)
    child_order = models.PositiveSmallIntegerField("فرزند چندم", null=True, blank=True)
    father_occupation = models.CharField("شغل پدر", max_length=120, blank=True)
    mother_occupation = models.CharField("شغل مادر", max_length=120, blank=True)
    scientific_background = models.TextField("سوابق علمی و تحصیلی", blank=True)
    political_positions = models.TextField("سمت‌های سیاسی و دفتری", blank=True)
    biography_summary = models.TextField("خلاصه زندگی‌نامه", blank=True)

    martyrdom_date = models.DateField("تاریخ شهادت", null=True, blank=True)
    martyrdom_place = models.CharField("محل شهادت", max_length=180, blank=True)
    martyrdom_manner = models.CharField("نحوه شهادت", max_length=220, blank=True)
    burial_county = models.CharField("شهرستان محل دفن", max_length=100, blank=True)
    burial_village = models.CharField("روستا یا شهر محل دفن", max_length=100, blank=True)
    burial_cemetery = models.CharField("نام محل دفن (قبرستان)", max_length=160, blank=True)
    burial_plot = models.CharField("قطعه", max_length=100, blank=True)

    division = models.CharField("لشکر", max_length=180, blank=True)
    brigade = models.CharField("تیپ", max_length=180, blank=True)
    battalion = models.CharField("گردان", max_length=180, blank=True)
    company = models.CharField("گروهان", max_length=180, blank=True)
    platoon = models.CharField("دسته", max_length=180, blank=True)
    unit_role = models.CharField("مسئولیت در یگان", max_length=180, blank=True)
    front_documents = models.TextField("مدارک و مستندات جبهه", blank=True)

    family_life = models.TextField("ابعاد خانوادگی", blank=True)
    scientific_life = models.TextField("ابعاد علمی", blank=True)
    velayat = models.TextField("ولایت‌مداری", blank=True)
    frontline_life = models.TextField("ابعاد جبهه", blank=True)
    social_life = models.TextField("ابعاد اجتماعی", blank=True)
    ethical_traits = models.TextField("ویژگی‌ها و ابعاد اخلاقی", blank=True)
    neighborhood_mosque_quran = models.TextField("محله، مسجد و جلسات قرآن", blank=True)

    basij_responsibility = models.TextField("مسئولیت در بسیج", blank=True)
    mosque_activity = models.TextField("فعالیت در مسجد", blank=True)
    school_activity = models.TextField("فعالیت در مدرسه", blank=True)
    university_activity = models.TextField("فعالیت در دانشگاه", blank=True)
    frontline_activity = models.TextField("فعالیت در جبهه", blank=True)
    teaching_activity = models.TextField("سوابق معلمی", blank=True)
    religious_practice = models.TextField("برخورد با واجبات، مستحبات و مکروهات", blank=True)
    ramadan_muharram = models.TextField("زهد و رفتار در رمضان و محرم", blank=True)
    favorite_sports = models.CharField("ورزش‌های مورد علاقه", max_length=300, blank=True)

    testament_text = models.TextField("متن کامل وصیت‌نامه", blank=True)
    testament_prayer = models.TextField("سفارش درباره نماز", blank=True)
    testament_hijab = models.TextField("سفارش درباره حجاب", blank=True)
    testament_velayat = models.TextField("سفارش درباره ولایت", blank=True)
    testament_islam = models.TextField("سفارش درباره اسلام", blank=True)
    testament_rights_debts = models.TextField("حق‌الناس و قرض", blank=True)
    handwritten_notes = models.TextField("دست‌نوشته‌ها و حرزها", blank=True)

    is_published = models.BooleanField("انتشار در سایت", default=True, db_index=True)
    is_featured = models.BooleanField("شهید شاخص", default=False)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)

    class Meta:
        verbose_name = "شهید"
        verbose_name_plural = "شهدا"
        ordering = ["-is_featured", "-martyrdom_date", "last_name", "first_name"]
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["birth_province", "birth_city"]),
            models.Index(fields=["martyrdom_date"]),
            models.Index(fields=["division"]),
        ]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def birth_place_full(self):
        """زنجیره محل تولد به ترتیب استان، شهرستان، شهر، روستا."""
        parts = [self.birth_province, self.birth_county, self.birth_city, self.birth_village]
        return "، ".join(part for part in parts if part)

    @property
    def burial_place_full(self):
        """محل دفن با ذکر قبرستان و قطعه."""
        place = "، ".join(
            part for part in (self.burial_village, self.burial_county) if part
        )
        pieces = []
        if self.burial_cemetery:
            pieces.append(self.burial_cemetery)
        if self.burial_plot:
            pieces.append(f"قطعه {self.burial_plot}")
        if place:
            pieces.insert(0, place)
        return "، ".join(pieces)

    @property
    def unit_chain(self):
        """سلسله‌مراتب یگان محل خدمت از لشکر تا دسته."""
        labels = [
            ("division", self.division),
            ("brigade", self.brigade),
            ("battalion", self.battalion),
            ("company", self.company),
            ("platoon", self.platoon),
        ]
        return [(label, value) for label, value in labels if value]

    def get_absolute_url(self):
        return reverse("martyrs:detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.full_name, allow_unicode=True) or "martyr"
            slug = base_slug
            number = 2
            while Martyr.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f"{base_slug}-{number}"
                number += 1
            self.slug = slug
        super().save(*args, **kwargs)


class MartyrSection(models.Model):
    martyr = models.ForeignKey(Martyr, on_delete=models.CASCADE, related_name="sections", verbose_name="شهید")
    title = models.CharField("عنوان بخش", max_length=160)
    content = models.TextField("متن بخش")
    sort_order = models.PositiveSmallIntegerField("ترتیب نمایش", default=0)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)

    class Meta:
        verbose_name = "بخش سفارشی"
        verbose_name_plural = "بخش‌های سفارشی"
        ordering = ["sort_order", "created_at"]

    def __str__(self):
        return f"{self.title} | {self.martyr.full_name}"


class MartyrInjury(models.Model):
    """سابقه مجروحیت شهید در جبهه؛ به دفعات قابل ثبت است."""

    martyr = models.ForeignKey(Martyr, on_delete=models.CASCADE, related_name="injuries", verbose_name="شهید")
    injury_date = models.DateField("تاریخ مجروحیت", null=True, blank=True)
    description = models.TextField("توضیحات مجروحیت")
    sort_order = models.PositiveSmallIntegerField("ترتیب نمایش", default=0)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)

    class Meta:
        verbose_name = "مجروحیت"
        verbose_name_plural = "سوابق مجروحیت"
        ordering = ["sort_order", "injury_date", "created_at"]

    def __str__(self):
        date_part = f" | {self.injury_date}" if self.injury_date else ""
        return f"مجروحیت {self.martyr.full_name}{date_part}"


class ComradeMartyr(models.Model):
    """همرزم شهید با محل خدمت مشترک و خاطرات او."""

    martyr = models.ForeignKey(Martyr, on_delete=models.CASCADE, related_name="comrades", verbose_name="شهید")
    full_name = models.CharField("نام و نام خانوادگی همرزم", max_length=160)
    service_place = models.CharField("محل خدمت با شهید", max_length=220, blank=True)
    memories = models.TextField("خاطرات همرزم", blank=True)
    sort_order = models.PositiveSmallIntegerField("ترتیب نمایش", default=0)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)

    class Meta:
        verbose_name = "همرزم شهید"
        verbose_name_plural = "همرزمان شهید"
        ordering = ["sort_order", "created_at"]

    def __str__(self):
        return f"{self.full_name} | {self.martyr.full_name}"


class Memory(models.Model):
    class Category(models.TextChoices):
        MARTYR = "martyr", "خود شهید"
        COMRADE = "comrade", "هم‌رزم"
        FAMILY = "family", "خانواده"
        FRIEND = "friend", "دوست"
        DREAM = "dream", "خواب و رؤیا"

    martyr = models.ForeignKey(Martyr, on_delete=models.CASCADE, related_name="memories", verbose_name="شهید")
    category = models.CharField("نوع خاطره", max_length=20, choices=Category.choices, default=Category.COMRADE)
    narrator = models.CharField("راوی", max_length=150)
    text = models.TextField("متن خاطره")
    recorded_at = models.DateField("تاریخ ثبت خاطره", null=True, blank=True)
    is_featured = models.BooleanField("نمایش در صفحه اصلی", default=False)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "خاطره"
        verbose_name_plural = "خاطرات"
        ordering = ["-is_featured", "-recorded_at", "-created_at"]
        indexes = [models.Index(fields=["category"])]

    def __str__(self):
        return f"{self.get_category_display()} | {self.martyr.full_name} | {self.narrator}"


class MartyrImage(models.Model):
    martyr = models.ForeignKey(Martyr, on_delete=models.CASCADE, related_name="images", verbose_name="شهید")
    image = models.ImageField("فایل تصویر", upload_to="martyrs/images/%Y/%m/", blank=True)
    title = models.CharField("عنوان", max_length=160, blank=True)
    description = models.TextField("توضیحات", blank=True)
    sort_order = models.PositiveSmallIntegerField("ترتیب نمایش", default=0)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)

    class Meta:
        verbose_name = "تصویر"
        verbose_name_plural = "گالری تصاویر"
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.title or f"تصویر {self.martyr.full_name}"


class MartyrVideo(models.Model):
    martyr = models.ForeignKey(Martyr, on_delete=models.CASCADE, related_name="videos", verbose_name="شهید")
    video_file = models.FileField("فایل ویدئو", upload_to="martyrs/videos/%Y/%m/", blank=True)
    external_url = models.URLField("پیوند ویدئو", blank=True)
    title = models.CharField("عنوان", max_length=160)
    description = models.TextField("توضیحات", blank=True)
    sort_order = models.PositiveSmallIntegerField("ترتیب نمایش", default=0)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)

    class Meta:
        verbose_name = "ویدئو"
        verbose_name_plural = "گالری ویدئوها"
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return f"{self.title} | {self.martyr.full_name}"
