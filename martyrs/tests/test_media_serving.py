"""سروشدن فایل‌های رسانه در حالت تولید (DEBUG=False) — مسیر ‎/media/‎.

روی هاست اشتراکی، آپاچی/Passenger همیشه درخواست ‎/media/‎ را به جنگو می‌سپارد؛
بنابراین مسیر سرو media باید حتی با DEBUG=False فعال بماند (config/urls.py).
"""
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from martyrs.models import Martyr, MartyrImage

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 32 + b"\xff\xd9"


class MediaServingTests(TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        override = override_settings(MEDIA_ROOT=self._tmp)
        override.enable()
        self.addCleanup(override.disable)
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)

    def _martyr(self, **kw):
        base = dict(first_name="علی", last_name="حسینی", is_published=True)
        base.update(kw)
        return Martyr.objects.create(**base)

    def test_uploaded_profile_image_is_served_in_production_mode(self):
        martyr = self._martyr(
            profile_image=SimpleUploadedFile("prof.jpg", JPEG, content_type="image/jpeg")
        )
        response = self.client.get(martyr.profile_image.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), JPEG)
        self.assertIn("image/jpeg", response["Content-Type"])

    def test_uploaded_gallery_image_is_served(self):
        martyr = self._martyr()
        img = MartyrImage.objects.create(
            martyr=martyr, image=SimpleUploadedFile("gal.jpg", JPEG, content_type="image/jpeg")
        )
        response = self.client.get(img.image.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), JPEG)

    def test_missing_media_file_returns_plain_404_without_debug_page(self):
        response = self.client.get("/media/martyrs/missing.jpg")
        self.assertEqual(response.status_code, 404)
        body = b"".join(response.streaming_content) if response.streaming else response.content
        # نباید صفحهٔ فنی DEBUG برگردد (روی سرور یک بار DEBUG=True بود و لو رفت)
        self.assertNotIn(b"Page not found", body)

    def test_og_image_prefers_profile_then_gallery(self):
        # فقط پروفایل → og:image باید آدرس عکس پروفایل باشد
        m1 = self._martyr(
            profile_image=SimpleUploadedFile("p1.jpg", JPEG, content_type="image/jpeg")
        )
        html = self.client.get(m1.get_absolute_url()).content.decode()
        self.assertIn(m1.profile_image.url, html)

        # پروفایل + گالری → og:image همچنان پروفایل است (اولویت تازه)
        m2 = self._martyr(
            profile_image=SimpleUploadedFile("p2.jpg", JPEG, content_type="image/jpeg")
        )
        MartyrImage.objects.create(
            martyr=m2, image=SimpleUploadedFile("g2.jpg", JPEG, content_type="image/jpeg")
        )
        html2 = self.client.get(m2.get_absolute_url()).content.decode()
        self.assertIn(m2.profile_image.url, html2)
