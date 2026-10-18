from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.templatetags.static import static
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


class SiteSettings(models.Model):
    """تنظیمات عمومی سایت"""
    music_url = models.URLField("آدرس موزیک پس‌زمینه", blank=True, default="")
    music_file = models.FileField("فایل موزیک", upload_to="music/", blank=True)
    music_enabled = models.BooleanField("فعال‌سازی موزیک پس‌زمینه", default=False)

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"

    def __str__(self):
        return "تنظیمات سایت"

    @property
    def music_source(self):
        if self.music_file:
            return self.music_file.url
        return self.music_url

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class BackgroundImage(models.Model):
    """تصویر پس‌زمینه صفحات سایت با امکان تعویض تصویر و تنظیم شفافیت از پنل مدیریت.

    هر «اسلات» پس‌زمینه (مثل پس‌زمینه صفحه اصلی یا بنر حماسی) یک رکورد است.
    اگر تصویر سفارشی آپلود نشده باشد، تصویر پیش‌فرض static همان اسلات استفاده می‌شود.
    «شفافیت» میزان دیده‌شدن تصویر است: ۰٪ کاملاً نامرئی و ۱۰۰٪ نمایش کامل.
    """

    class Key(models.TextChoices):
        HOME_HERO = "home_hero", "پس‌زمینه هیرو صفحه اصلی"
        HOME_PAGE = "home_page", "پس‌زمینه محو کل صفحه اصلی"
        DIRECTORY_PAGE = "directory_page", "پس‌زمینه محو فهرست شهدا"
        PROFILE_HERO = "profile_hero", "پس‌زمینه پرونده شهید (چفیه)"
        EPIC_BANNER = "epic_banner", "بنر حماسی صفحه اصلی"
        EPIC_BANNER_ZIYARAT = "epic_banner_ziyarat", "بنر حماسی زیارت‌نامه"
        PANEL_LOGIN = "panel_login", "پس‌زمینه صفحه ورود پنل"
        HERO_ARCH = "hero_arch", "قاب محراب صفحه اصلی"
        ESLIMI_TEXTURE = "eslimi_texture", "بافت اسلیمی (تزئینی)"
        ESLIMI_DIVIDER = "eslimi_divider", "جداکننده اسلیمی"

    # شفافیت پیش‌فرض هر اسلات (درصد) — مطابق طراحی اولیه سایت
    DEFAULT_OPACITY = {
        Key.HOME_HERO: 7,
        Key.HOME_PAGE: 12,
        Key.DIRECTORY_PAGE: 12,
        Key.PROFILE_HERO: 32,
        Key.EPIC_BANNER: 34,
        Key.EPIC_BANNER_ZIYARAT: 34,
        Key.PANEL_LOGIN: 45,
        Key.HERO_ARCH: 16,
        Key.ESLIMI_TEXTURE: 9,
        Key.ESLIMI_DIVIDER: 100,
    }

    # مسیر پیش‌فرض تصویر هر اسلات در پوشه static
    DEFAULT_STATIC_PATH = {
        Key.HOME_HERO: "images/bg/bg-home.jpg",
        Key.HOME_PAGE: "images/bg/bg-home.jpg",
        Key.DIRECTORY_PAGE: "images/bg/bg-directory.jpg",
        Key.PROFILE_HERO: "images/chafiyeh.jpg",
        Key.EPIC_BANNER: "images/war-front/war-01.jpeg",
        Key.EPIC_BANNER_ZIYARAT: "images/memorials/memorial-01.jpg",
        Key.PANEL_LOGIN: "images/bg/bg-login.jpg",
        Key.HERO_ARCH: "images/patterns/mihrab-arch.png",
        Key.ESLIMI_TEXTURE: "images/patterns/eslimi-texture.jpg",
        Key.ESLIMI_DIVIDER: "images/patterns/eslimi-divider.jpg",
    }

    key = models.CharField("کلید", max_length=40, unique=True, choices=Key.choices)
    image = models.ImageField(
        "تصویر سفارشی", upload_to="backgrounds/", blank=True,
        help_text="در صورت خالی بودن، تصویر پیش‌فرض سایت نمایش داده می‌شود.",
    )
    opacity = models.PositiveSmallIntegerField(
        "شفافیت نمایش (درصد)", default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="۰ = کاملاً نامرئی، ۱۰۰ = نمایش کامل تصویر.",
    )
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)

    class Meta:
        verbose_name = "تصویر پس‌زمینه"
        verbose_name_plural = "تصاویر پس‌زمینه"
        ordering = ["key"]

    def __str__(self):
        return self.label

    @property
    def label(self):
        return self.get_key_display()

    @property
    def default_opacity(self):
        return self.DEFAULT_OPACITY.get(self.key, 100)

    @property
    def is_custom(self):
        return bool(self.image)

    @property
    def default_image_url(self):
        return static(self.DEFAULT_STATIC_PATH.get(self.key, "images/bg/bg-home.jpg"))

    @property
    def image_url(self):
        """نشانی تصویر فعال: تصویر سفارشی در صورت آپلود، وگرنه تصویر پیش‌فرض."""
        if self.image:
            try:
                return self.image.url
            except ValueError:
                return self.default_image_url
        return self.default_image_url

    @property
    def opacity_css(self):
        """مقدار شفافیت به‌صورت عددی ۰ تا ۱ برای استفاده در CSS."""
        return f"{(self.opacity or 0) / 100:.2f}"

    @property
    def wash_css(self):
        """مکمل شفافیت (۱ منهای شفافیت) برای پوشش‌های روشن روی تصویر."""
        return f"{1 - (self.opacity or 0) / 100:.2f}"

    @classmethod
    def load(cls, key):
        """بازگرداندن رکورد اسلات؛ در نبود رکورد، نمونه پیش‌فرضِ ذخیره‌نشده."""
        obj = cls.objects.filter(key=key).first()
        if obj is None:
            obj = cls(key=key, opacity=cls.DEFAULT_OPACITY.get(key, 100))
        return obj

    @classmethod
    def load_map(cls):
        """نقشه کامل همه اسلات‌ها برای استفاده در قالب‌ها (همیشه کامل است)."""
        items = {obj.key: obj for obj in cls.objects.all()}
        for key, _label in cls.Key.choices:
            if key not in items:
                items[key] = cls(key=key, opacity=cls.DEFAULT_OPACITY.get(key, 100))
        return items
