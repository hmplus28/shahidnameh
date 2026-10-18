"""آزمون‌های مدیریت المان‌های گرافیکی سایت (لوگو، آیکون‌ها و تصویر پیش‌فرض شهید).

تمرکز اصلی: تعویض تصویر هر المان و تنظیم شفافیت آن از پنل مدیریت باید
دقیقاً در صفحات سایت (لوگوی هدر، آیکون قرآن، آیکون لاله، عکس پیش‌فرض شهید)
و مانیفست PWA اعمال شود.
"""
import json
import tempfile

from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from io import BytesIO
from PIL import Image

from martyrs.models import Martyr, SiteElement


def make_image_file(name="test-element.png", color=(40, 120, 90)):
    """ساخت یک فایل تصویر واقعی در حافظه برای آزمون آپلود."""
    buffer = BytesIO()
    Image.new("RGB", (80, 80), color).save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ElementModelTests(TestCase):
    """رفتار مدل المان‌های سایت."""

    def test_all_elements_seeded_with_full_opacity(self):
        self.assertEqual(SiteElement.objects.count(), len(SiteElement.Key.choices))
        for key, default in SiteElement.DEFAULT_OPACITY.items():
            obj = SiteElement.objects.get(key=key)
            self.assertEqual(obj.opacity, default)
            self.assertFalse(obj.is_custom)

    def test_image_url_falls_back_to_static_default(self):
        # در تولید، نام فایل‌های static هش می‌شوند؛ پس فقط پیشوند را می‌سنجیم
        self.assertTrue(SiteElement.load("site_logo").image_url.startswith("/static/images/bg/logo-main"))
        self.assertTrue(SiteElement.load("quran_header_icon").image_url.startswith("/static/images/bg/quran-header"))
        self.assertTrue(SiteElement.load("tulip_icon").image_url.startswith("/static/images/bg/tulip-icon"))
        self.assertTrue(SiteElement.load("martyr_default_photo").image_url.startswith("/static/images/martyr-default"))

    def test_custom_image_url_wins(self):
        obj = SiteElement.load("site_logo")
        obj.image = make_image_file("logo-custom.png")
        obj.save()
        obj = SiteElement.load("site_logo")
        self.assertTrue(obj.is_custom)
        self.assertTrue(obj.image_url.startswith("/media/elements/"))
        self.assertIn("logo-custom", obj.image_url)

    def test_opacity_css_conversion(self):
        cases = {0: "0.00", 25: "0.25", 55: "0.55", 100: "1.00"}
        for percent, expected in cases.items():
            obj = SiteElement(key="site_logo", opacity=percent)
            self.assertEqual(obj.opacity_css, expected)

    def test_opacity_out_of_range_is_invalid(self):
        obj = SiteElement(key="site_logo", opacity=150)
        with self.assertRaises(Exception):
            obj.full_clean()
        obj = SiteElement(key="site_logo", opacity=-3)
        with self.assertRaises(Exception):
            obj.full_clean()

    def test_load_map_always_contains_every_element(self):
        items = SiteElement.load_map()
        for key, _label in SiteElement.Key.choices:
            self.assertIn(key, items)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ElementTemplateTests(TestCase):
    """تزریق تصویر و شفافیت المان‌ها در قالب‌های سایت."""

    def _set(self, key, opacity, image=None):
        obj = SiteElement.load(key)
        obj.opacity = opacity
        if image is not None:
            obj.image = image
        obj.save()
        return obj

    def test_home_injects_element_css_vars_with_defaults(self):
        html = self.client.get("/").content.decode()
        self.assertIn('--el-logo-url:url("/static/images/bg/logo-main', html)
        self.assertIn("--el-logo-opacity:1.00", html)
        self.assertIn('--el-quran-url:url("/static/images/bg/quran-header', html)
        self.assertIn("--el-quran-opacity:1.00", html)
        self.assertIn('--el-tulip-url:url("/static/images/bg/tulip-icon', html)
        self.assertIn("--el-tulip-opacity:1.00", html)
        self.assertIn('--el-martyr-default-url:url("/static/images/martyr-default', html)

    def test_logo_replacement_and_opacity_reflect_on_home(self):
        self._set("site_logo", 55, image=make_image_file("logo-custom.png"))
        html = self.client.get("/").content.decode()
        # لوگوی هدر باید به تصویر آپلودشده اشاره کند
        self.assertIn('class="header-logo-img" src="/media/elements/logo-custom', html)
        self.assertIn("--el-logo-opacity:0.55", html)
        self.assertNotIn("--el-logo-opacity:1.00", html)
        # فاوآیکون هم باید از همان المان پیروی کند
        self.assertIn('<link rel="icon" type="image/jpeg" href="/media/elements/logo-custom', html)

    def test_quran_and_tulip_icons_reflect_panel_changes(self):
        self._set("quran_header_icon", 40, image=make_image_file("quran-custom.png"))
        self._set("tulip_icon", 0, image=make_image_file("tulip-custom.png"))
        html = self.client.get("/").content.decode()
        self.assertIn('class="header-quran-icon" src="/media/elements/quran-custom', html)
        self.assertIn("--el-quran-opacity:0.40", html)
        # ترتیب اتریبیوت‌ها در قالب لاله برعکس است (src قبل از class)
        self.assertIn('src="/media/elements/tulip-custom', html)
        self.assertIn('class="tulip-icon"', html)
        # شفافیت صفر یعنی آیکون کاملاً نامرئی
        self.assertIn("--el-tulip-opacity:0.00", html)

    def test_martyr_default_photo_replacement(self):
        self._set("martyr_default_photo", 70, image=make_image_file("default-custom.png"))
        martyr = Martyr.objects.create(first_name="علی", last_name="موسی‌زاده", is_published=True)
        html = self.client.get(martyr.get_absolute_url()).content.decode()
        self.assertIn('src="/media/elements/default-custom', html)
        self.assertIn("--el-martyr-default-opacity:0.70", html)

    def test_martyr_default_photo_on_directory_and_home(self):
        self._set("martyr_default_photo", 60, image=make_image_file("default-custom.png"))
        Martyr.objects.create(first_name="حسن", last_name="کریمی", is_published=True, is_featured=True)
        home = self.client.get("/").content.decode()
        directory = self.client.get(reverse("martyrs:directory")).content.decode()
        self.assertIn("/media/elements/default-custom", home)
        self.assertIn("/media/elements/default-custom", directory)

    def test_panel_login_and_brand_use_custom_logo(self):
        self._set("site_logo", 80, image=make_image_file("logo-custom.png"))
        login_html = self.client.get(reverse("martyrs:panel_login")).content.decode()
        self.assertIn('class="login-brand-img" src="/media/elements/logo-custom', login_html)

    def test_manifest_uses_custom_logo(self):
        self._set("site_logo", 100, image=make_image_file("manifest-logo.png"))
        self._set("tulip_icon", 100, image=make_image_file("manifest-tulip.png"))
        response = self.client.get(reverse("martyrs:manifest"))
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content.decode())
        self.assertTrue(payload["icons"][0]["src"].startswith("/media/elements/manifest-logo"))
        self.assertTrue(payload["shortcuts"][0]["icons"][0]["src"].startswith("/media/elements/manifest-tulip"))
        self.assertEqual(payload["short_name"], "شهیدنامه")

    def test_manifest_default_logo_is_static(self):
        payload = json.loads(self.client.get(reverse("martyrs:manifest")).content.decode())
        self.assertTrue(payload["icons"][0]["src"].startswith("/static/images/bg/logo-main"))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ElementPanelTests(TestCase):
    """آزمون صفحه «المان‌های سایت» در پنل مدیریت."""

    def setUp(self):
        self.superuser = get_user_model().objects.create_superuser("boss", "b@example.com", "pass12345")
        self.staff = get_user_model().objects.create_user("writer", "w@example.com", "pass12345", is_staff=True)

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(reverse("martyrs:panel_elements"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/panel/login/", response.url)

    def test_non_superuser_staff_denied(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("martyrs:panel_elements"))
        self.assertRedirects(response, reverse("martyrs:panel_home"), fetch_redirect_response=False)

    def test_superuser_sees_all_elements(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("martyrs:panel_elements"))
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(html.count("data-bg-card"), len(SiteElement.Key.choices))
        for key, label in SiteElement.Key.choices:
            self.assertIn(f'value="{key}"', html)
        self.assertIn(label, html)
        self.assertIn("شفافیت", html)
        self.assertIn("لوگوی شهیدنامه", html)
        self.assertIn("تصویر پیش‌فرض شهید", html)

    def test_opacity_only_post_updates_element(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("martyrs:panel_elements"),
            {"key": "site_logo", "site_logo-opacity": "35"},
        )
        self.assertRedirects(response, reverse("martyrs:panel_elements"))
        obj = SiteElement.load("site_logo")
        self.assertEqual(obj.opacity, 35)
        self.assertFalse(obj.is_custom)
        self.assertTrue(LogEntry.objects.filter(change_message__contains="المان").exists())

    def test_opacity_out_of_range_rejected(self):
        self.client.force_login(self.superuser)
        self.client.post(
            reverse("martyrs:panel_elements"),
            {"key": "tulip_icon", "tulip_icon-opacity": "220"},
        )
        self.assertEqual(SiteElement.load("tulip_icon").opacity, 100)

    def test_invalid_key_rejected(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("martyrs:panel_elements"),
            {"key": "not_a_key", "not_a_key-opacity": "50"},
        )
        self.assertRedirects(response, reverse("martyrs:panel_elements"))

    def test_upload_custom_image(self):
        self.client.force_login(self.superuser)
        self.client.post(
            reverse("martyrs:panel_elements"),
            {"key": "site_logo", "site_logo-opacity": "65", "site_logo-image": make_image_file("panel-logo.png")},
            format="multipart",
        )
        obj = SiteElement.load("site_logo")
        self.assertTrue(obj.is_custom)
        self.assertTrue(obj.image_url.startswith("/media/elements/"))
        self.assertEqual(obj.opacity, 65)
        # صفحه اصلی باید لوگوی جدید را نشان دهد
        html = self.client.get("/").content.decode()
        self.assertIn("panel-logo", html)
        self.assertIn("--el-logo-opacity:0.65", html)

    def test_reset_returns_element_to_default(self):
        obj = SiteElement.load("site_logo")
        obj.image = make_image_file("to-be-removed.png")
        obj.opacity = 30
        obj.save()
        removed_path = obj.image.path

        self.client.force_login(self.superuser)
        self.client.post(reverse("martyrs:panel_element_reset", args=["site_logo"]))

        import os

        obj = SiteElement.load("site_logo")
        self.assertFalse(obj.is_custom)
        self.assertEqual(obj.opacity, 100)
        self.assertTrue(obj.image_url.startswith("/static/images/bg/logo-main"))
        self.assertFalse(os.path.exists(removed_path))
        self.assertTrue(LogEntry.objects.filter(change_message__contains="المان").exists())

    def test_reset_unknown_key_safe(self):
        self.client.force_login(self.superuser)
        response = self.client.post(reverse("martyrs:panel_element_reset", args=["unknown"]))
        self.assertRedirects(response, reverse("martyrs:panel_elements"))

    def test_reset_get_request_ignored(self):
        obj = SiteElement.load("site_logo")
        obj.opacity = 40
        obj.save()
        self.client.force_login(self.superuser)
        self.client.get(reverse("martyrs:panel_element_reset", args=["site_logo"]))
        self.assertEqual(SiteElement.load("site_logo").opacity, 40)

    def test_panel_page_is_mobile_friendly(self):
        self.client.force_login(self.superuser)
        html = self.client.get(reverse("martyrs:panel_elements")).content.decode()
        self.assertIn('name="viewport" content="width=device-width, initial-scale=1"', html)
        self.assertIn('type="range"', html)
        self.assertIn("panel-nav-toggle", html)
