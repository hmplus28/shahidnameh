"""آزمون‌های مدیریت تصاویر پس‌زمینه و شفافیت از پنل مدیریت.

تمرکز اصلی این فایل روی «شفافیت» است: هر مقدار تنظیم‌شده در پنل باید
دقیقاً با همان نسبت در CSS صفحات عمومی و پنل تزریق شود.
"""
import tempfile

from django.contrib.auth import get_user_model
from django.contrib.admin.models import LogEntry
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image
from io import BytesIO

from martyrs.models import BackgroundImage


def make_image_file(name="test-bg.png", color=(180, 40, 40)):
    """ساخت یک فایل تصویر واقعی در حافظه برای آزمون آپلود."""
    buffer = BytesIO()
    Image.new("RGB", (90, 60), color).save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


class BackgroundModelTests(TestCase):
    """رفتار مدل اسلات‌های پس‌زمینه."""

    def test_all_slots_seeded_with_default_opacity(self):
        self.assertEqual(BackgroundImage.objects.count(), len(BackgroundImage.Key.choices))
        for key, default in BackgroundImage.DEFAULT_OPACITY.items():
            obj = BackgroundImage.objects.get(key=key)
            self.assertEqual(obj.opacity, default)
            self.assertFalse(obj.is_custom)

    def test_image_url_falls_back_to_static_default(self):
        obj = BackgroundImage.load("home_hero")
        self.assertTrue(obj.image_url.startswith("/static/images/bg/bg-home"))

    def test_custom_image_url_wins(self):
        obj = BackgroundImage.load("panel_login")
        obj.image = make_image_file("login-bg.png")
        obj.save()
        obj = BackgroundImage.load("panel_login")
        self.assertTrue(obj.image_url.startswith("/media/backgrounds/"))
        self.assertIn("login-bg", obj.image_url)

    def test_opacity_css_conversion(self):
        cases = {0: "0.00", 7: "0.07", 34: "0.34", 100: "1.00"}
        for percent, expected in cases.items():
            obj = BackgroundImage(key="home_hero", opacity=percent)
            self.assertEqual(obj.opacity_css, expected)

    def test_wash_css_is_complement_of_opacity(self):
        cases = {0: "1.00", 32: "0.68", 65: "0.35", 100: "0.00"}
        for percent, expected in cases.items():
            obj = BackgroundImage(key="profile_hero", opacity=percent)
            self.assertEqual(obj.wash_css, expected)

    def test_opacity_out_of_range_is_invalid(self):
        obj = BackgroundImage(key="home_hero", opacity=150)
        with self.assertRaises(Exception):
            obj.full_clean()
        obj = BackgroundImage(key="home_hero", opacity=-5)
        with self.assertRaises(Exception):
            obj.full_clean()

    def test_load_map_always_contains_every_slot(self):
        assets = BackgroundImage.load_map()
        for key, _label in BackgroundImage.Key.choices:
            self.assertIn(key, assets)


class BackgroundCssInjectionTests(TestCase):
    """تزریق متغیرهای CSS (تصویر + شفافیت) در صفحات عمومی و پنل."""

    def test_home_injects_default_opacity_vars(self):
        html = self.client.get("/").content.decode()
        self.assertIn("--bg-home-hero-url:url(", html)
        self.assertIn("--bg-home-hero-opacity:0.07", html)
        self.assertIn("--bg-home-page-opacity:0.12", html)
        self.assertIn("--bg-profile-hero-wash:0.68", html)
        self.assertIn("--bg-eslimi-opacity:0.09", html)
        self.assertIn("--bg-hero-arch-opacity:0.16", html)

    def test_home_hero_img_uses_managed_asset(self):
        html = self.client.get("/").content.decode()
        obj = BackgroundImage.load("home_hero")
        self.assertIn(f'src="{obj.image_url}"', html)
        # جداکننده اسلیمی با شفافیت ۱۰۰٪ و style درون‌خطی
        self.assertIn('style="opacity:1.00"', html)

    def test_directory_page_uses_its_own_slot(self):
        html = self.client.get(reverse("martyrs:directory")).content.decode()
        self.assertIn("--bg-directory-page-opacity:0.12", html)
        self.assertIn("--bg-directory-page-url:url(", html)

    def test_ziyaratnama_epic_banner_inline_opacity(self):
        html = self.client.get(reverse("martyrs:ziyaratnama")).content.decode()
        self.assertIn('style="opacity:0.34"', html)
        obj = BackgroundImage.load("epic_banner_ziyarat")
        self.assertIn(obj.image_url, html)

    def test_panel_login_page_injects_login_vars(self):
        html = self.client.get(reverse("martyrs:panel_login")).content.decode()
        self.assertIn("--bg-panel-login-url:url(", html)
        self.assertIn("--bg-panel-login-opacity:0.45", html)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TransparencyTests(TestCase):
    """آزمون اختصاصی شفافیت: تغییر درصد باید دقیقاً در CSS صفحات دیده شود."""

    def _set(self, key, opacity, image=None):
        obj = BackgroundImage.load(key)
        obj.opacity = opacity
        if image is not None:
            obj.image = image
        obj.save()
        return obj

    def test_hero_opacity_change_reflects_on_home(self):
        self._set("home_hero", 65)
        html = self.client.get("/").content.decode()
        self.assertIn("--bg-home-hero-opacity:0.65", html)
        self.assertNotIn("--bg-home-hero-opacity:0.07", html)

    def test_hero_transparency_zero_hides_background(self):
        self._set("home_hero", 0)
        html = self.client.get("/").content.decode()
        self.assertIn("--bg-home-hero-opacity:0.00", html)

    def test_hero_full_opacity(self):
        self._set("home_hero", 100)
        html = self.client.get("/").content.decode()
        self.assertIn("--bg-home-hero-opacity:1.00", html)

    def test_page_background_opacity_reflects_on_home_and_directory(self):
        self._set("home_page", 40)
        self._set("directory_page", 0)
        home = self.client.get("/").content.decode()
        directory = self.client.get(reverse("martyrs:directory")).content.decode()
        self.assertIn("--bg-home-page-opacity:0.40", home)
        self.assertIn("--bg-directory-page-opacity:0.00", directory)

    def test_profile_wash_is_inverse_of_opacity(self):
        # شفافیت ۶۵٪ → پوشش سفید باید ۳۵٪ شود تا نسبت دقیق برقرار بماند
        self._set("profile_hero", 65)
        html = self.client.get("/").content.decode()
        self.assertIn("--bg-profile-hero-opacity:0.65", html)
        self.assertIn("--bg-profile-hero-wash:0.35", html)
        self.assertNotIn("--bg-profile-hero-wash:0.68", html)

    def test_eslimi_texture_opacity_shared_between_hero_and_profile(self):
        self._set("eslimi_texture", 30)
        html = self.client.get("/").content.decode()
        self.assertIn("--bg-eslimi-opacity:0.30", html)

    def test_panel_login_transparency_change(self):
        self._set("panel_login", 80)
        html = self.client.get(reverse("martyrs:panel_login")).content.decode()
        self.assertIn("--bg-panel-login-opacity:0.80", html)
        self.assertNotIn("--bg-panel-login-opacity:0.45", html)

    def test_epic_banner_inline_opacity_updates(self):
        self._set("epic_banner", 90)
        self._set("epic_banner_ziyarat", 10)
        home = self.client.get("/").content.decode()
        ziyarat = self.client.get(reverse("martyrs:ziyaratnama")).content.decode()
        self.assertIn('style="opacity:0.90"', home)
        self.assertIn('style="opacity:0.10"', ziyarat)

    def test_divider_opacity_inline_style_updates(self):
        self._set("eslimi_divider", 25)
        html = self.client.get("/").content.decode()
        self.assertIn('style="opacity:0.25"', html)

    def test_custom_image_and_transparency_work_together(self):
        self._set("home_hero", 55, image=make_image_file("custom-hero.png"))
        html = self.client.get("/").content.decode()
        self.assertIn("--bg-home-hero-opacity:0.55", html)
        # خط نشانی هیرو باید دقیقاً به تصویر آپلودشده اشاره کند
        hero_line = next(
            line for line in html.splitlines() if "--bg-home-hero-url" in line
        )
        self.assertIn('/media/backgrounds/custom-hero.png', hero_line)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class BackgroundPanelTests(TestCase):
    """آزمون صفحه «تصاویر پس‌زمینه» در پنل مدیریت."""

    def setUp(self):
        self.superuser = get_user_model().objects.create_superuser("boss", "b@example.com", "pass12345")
        self.staff = get_user_model().objects.create_user("writer", "w@example.com", "pass12345", is_staff=True)

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(reverse("martyrs:panel_backgrounds"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/panel/login/", response.url)

    def test_non_superuser_staff_denied(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("martyrs:panel_backgrounds"))
        self.assertRedirects(response, reverse("martyrs:panel_home"), fetch_redirect_response=False)

    def test_superuser_sees_all_slots(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("martyrs:panel_backgrounds"))
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(html.count("data-bg-card"), len(BackgroundImage.Key.choices))
        for key, _label in BackgroundImage.Key.choices:
            self.assertIn(f'value="{key}"', html)
        self.assertIn("شفافیت", html)

    def test_page_is_mobile_friendly(self):
        self.client.force_login(self.superuser)
        html = self.client.get(reverse("martyrs:panel_backgrounds")).content.decode()
        # پنل باید موبایل‌محور بماند: متای viewport و اسلایدر لمسی
        self.assertIn('name="viewport" content="width=device-width, initial-scale=1"', html)
        self.assertIn('type="range"', html)
        self.assertIn("panel-nav-toggle", html)

    def test_opacity_only_post_updates_slot(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("martyrs:panel_backgrounds"),
            {"key": "home_hero", "home_hero-opacity": "70"},
        )
        self.assertRedirects(response, reverse("martyrs:panel_backgrounds"))
        obj = BackgroundImage.load("home_hero")
        self.assertEqual(obj.opacity, 70)
        self.assertFalse(obj.is_custom)
        self.assertTrue(LogEntry.objects.filter(change_message__contains="پس‌زمینه").exists())

    def test_opacity_out_of_range_rejected(self):
        self.client.force_login(self.superuser)
        self.client.post(
            reverse("martyrs:panel_backgrounds"),
            {"key": "home_hero", "home_hero-opacity": "180"},
        )
        self.assertEqual(BackgroundImage.load("home_hero").opacity, 7)

    def test_upload_custom_image(self):
        self.client.force_login(self.superuser)
        self.client.post(
            reverse("martyrs:panel_backgrounds"),
            {"key": "epic_banner", "epic_banner-opacity": "50", "epic_banner-image": make_image_file("epic-custom.png")},
            format="multipart",
        )
        obj = BackgroundImage.load("epic_banner")
        self.assertTrue(obj.is_custom)
        self.assertTrue(obj.image_url.startswith("/media/backgrounds/"))
        self.assertEqual(obj.opacity, 50)
        # صفحه اصلی باید تصویر آپلودشده و شفافیت جدید را نشان دهد
        html = self.client.get("/").content.decode()
        self.assertIn("epic-custom", html)
        self.assertIn('style="opacity:0.50"', html)

    def test_clear_image_returns_to_default(self):
        obj = BackgroundImage.load("panel_login")
        obj.image = make_image_file("login-custom.png")
        obj.save()
        self.client.force_login(self.superuser)
        # نام چک‌باکس حذف، هم‌نام فیلد با پسوند -clear است: panel_login-image-clear
        self.client.post(
            reverse("martyrs:panel_backgrounds"),
            {
                "key": "panel_login",
                "panel_login-opacity": "45",
                "panel_login-image-clear": "on",
            },
            format="multipart",
        )
        obj = BackgroundImage.load("panel_login")
        self.assertFalse(obj.is_custom)
        self.assertTrue(obj.image_url.startswith("/static/images/bg/bg-login"))

    def test_reset_restores_default_image_and_opacity(self):
        obj = BackgroundImage.load("home_hero")
        obj.image = make_image_file("hero-custom.png")
        obj.opacity = 77
        obj.save()
        self.client.force_login(self.superuser)
        response = self.client.post(reverse("martyrs:panel_background_reset", args=["home_hero"]))
        self.assertRedirects(response, reverse("martyrs:panel_backgrounds"))
        obj = BackgroundImage.load("home_hero")
        self.assertFalse(obj.is_custom)
        self.assertEqual(obj.opacity, obj.default_opacity)
        self.assertEqual(obj.opacity, 7)

    def test_reset_unknown_key_is_safe(self):
        self.client.force_login(self.superuser)
        response = self.client.post(reverse("martyrs:panel_background_reset", args=["nope"]))
        self.assertRedirects(response, reverse("martyrs:panel_backgrounds"))

    def test_invalid_key_post_is_rejected(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("martyrs:panel_backgrounds"),
            {"key": "hacker", "hacker-opacity": "10"},
        )
        self.assertRedirects(response, reverse("martyrs:panel_backgrounds"))
        self.assertEqual(BackgroundImage.load("home_hero").opacity, 7)

    def test_staff_cannot_change_backgrounds(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("martyrs:panel_backgrounds"),
            {"key": "home_hero", "home_hero-opacity": "99"},
        )
        self.assertRedirects(response, reverse("martyrs:panel_home"), fetch_redirect_response=False)
        self.assertEqual(BackgroundImage.load("home_hero").opacity, 7)


class BackgroundAdminTests(TestCase):
    """دسترسی مدل از پنل استاندارد جنگو هم باید برقرار باشد."""

    def setUp(self):
        self.superuser = get_user_model().objects.create_superuser("adminx", "a@example.com", "pass12345")
        self.client.force_login(self.superuser)

    def test_changelist_renders_all_slots(self):
        url = reverse("admin:martyrs_backgroundimage_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # هر اسلات یک ردیف با فیلد شفافیت دارد
        self.assertContains(response, 'class="field-opacity"', count=len(BackgroundImage.Key.choices))
        self.assertContains(response, "تصاویر پس‌زمینه")

    def test_change_page_shows_opacity(self):
        obj = BackgroundImage.load("panel_login")
        url = reverse("admin:martyrs_backgroundimage_change", args=[obj.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'type="range"')
