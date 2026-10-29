"""طرح نشانی عددی صفحات شهدا و اعتبار توسعه‌دهنده (دایناکد)."""
from django.test import TestCase
from django.urls import reverse

from martyrs.models import Martyr


class NumericUrlSchemeTests(TestCase):
    """نشانی عمومی شهدا فقط شناسهٔ عددی است؛ اسلاگ فارسی دیگر در نشانی نیست."""

    def setUp(self):
        self.martyr = Martyr.objects.create(
            first_name="عبدالحسین",
            last_name="صحتی",
            is_published=True,
        )

    def test_get_absolute_url_is_numeric(self):
        self.assertEqual(self.martyr.get_absolute_url(), f"/martyrs/{self.martyr.pk}/")

    def test_detail_by_id_returns_200_for_anonymous(self):
        response = self.client.get(f"/martyrs/{self.martyr.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "عبدالحسین صحتی")

    def test_old_slug_url_redirects_permanently_to_numeric_url(self):
        response = self.client.get(f"/martyrs/{self.martyr.slug}/")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], f"/martyrs/{self.martyr.pk}/")

    def test_unknown_slug_returns_404(self):
        response = self.client.get("/martyrs/ناموجود-در-سیستم/")
        self.assertEqual(response.status_code, 404)

    def test_numeric_id_with_persian_digits_is_not_matched(self):
        # «۱۲» فارسی عدد نیست؛ نباید ۵۰۰ بدهد — به مسیر اسلاگ می‌رود و ۴۰۴
        response = self.client.get("/martyrs/۱۲/")
        self.assertEqual(response.status_code, 404)

    def test_draft_hidden_by_numeric_id_from_public_but_visible_to_staff(self):
        from django.contrib.auth import get_user_model

        draft = Martyr.objects.create(first_name="رضا", last_name="کریمی", is_published=False)

        anonymous = self.client.get(f"/martyrs/{draft.pk}/")
        self.assertEqual(anonymous.status_code, 404)

        staff = get_user_model().objects.create_user(
            "staffer", "staffer@example.com", "pass12345", is_staff=True
        )
        self.client.force_login(staff)
        staff_response = self.client.get(f"/martyrs/{draft.pk}/")
        self.assertEqual(staff_response.status_code, 200)


class DaynacodeCreditTests(TestCase):
    """اعتبار «توسعه یافته توسط تیم دایناکد» در منوی بیشتر، لینک به daynacode.ir."""

    def test_credit_item_present_on_home_page(self):
        response = self.client.get(reverse("martyrs:home"))
        self.assertContains(response, "https://daynacode.ir")
        self.assertContains(response, "https://daynacode.ir/assets/dayna-logo.png")
        self.assertContains(response, "توسعه یافته توسط تیم دایناکد")
        self.assertContains(response, 'rel="noopener noreferrer"')
