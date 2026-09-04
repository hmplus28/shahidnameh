from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from martyrs.models import Martyr


class PanelTests(TestCase):
    def setUp(self):
        self.martyr = Martyr.objects.create(first_name="علی", last_name="حسینی", martyrdom_date=date(1985, 2, 8))
        self.superuser = get_user_model().objects.create_superuser("boss", "b@example.com", "pass12345")
        self.viewer = get_user_model().objects.create_user(
            "watcher", "w@example.com", "pass12345", is_staff=True,
        )

    def _login_as_superuser(self):
        self.client.force_login(self.superuser)

    def test_panel_requires_login(self):
        response = self.client.get(reverse("martyrs:panel_home"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/panel/login/", response.url)

    def test_non_staff_cannot_enter_panel(self):
        get_user_model().objects.create_user("plain", "p@example.com", "pass12345")
        self.client.login(username="plain", password="pass12345")

        response = self.client.get(reverse("martyrs:panel_home"))
        self.assertEqual(response.status_code, 302)

    def test_non_staff_login_does_not_create_redirect_loop(self):
        get_user_model().objects.create_user("plain", "p@example.com", "pass12345")

        response = self.client.post(
            reverse("martyrs:panel_login"),
            {"username": "plain", "password": "pass12345"},
        )
        self.assertRedirects(response, reverse("martyrs:home"), fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)

        # کاربر ناشناس: صفحه ورود بدون هیچ حلقه‌ای عادی رندر می‌شود.
        response = self.client.get(reverse("martyrs:panel_login"))
        self.assertEqual(response.status_code, 200)

        # کاربر واردشده بدون دسترسی پنل: از صفحه ورود به خانه هدایت می‌شود.
        plain_user = get_user_model().objects.get(username="plain")
        self.client.force_login(plain_user)
        response = self.client.get(reverse("martyrs:panel_login"))
        self.assertRedirects(response, reverse("martyrs:home"), fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse("martyrs:home")).status_code, 200)

    def test_login_page_and_dashboard_render(self):
        response = self.client.get(reverse("martyrs:panel_login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "پنل مدیریت شهیدنامه")

        self._login_as_superuser()
        dashboard = self.client.get(reverse("martyrs:panel_home"))
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, "پیشخوان")

    def test_martyr_list_shows_feature_toggle_for_editors(self):
        self._login_as_superuser()
        response = self.client.get(reverse("martyrs:panel_martyr_list"))

        self.assertContains(response, "تنظیم به‌عنوان شاخص")

    def test_feature_toggle_updates_martyr(self):
        self._login_as_superuser()
        url = reverse("martyrs:panel_martyr_toggle", args=[self.martyr.pk, "feature"])

        response = self.client.post(url)
        self.martyr.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.martyr.is_featured)

        self.client.post(url)
        self.martyr.refresh_from_db()
        self.assertFalse(self.martyr.is_featured)

    def test_viewer_role_is_read_only_in_panel(self):
        self.client.force_login(self.viewer)

        list_response = self.client.get(reverse("martyrs:panel_martyr_list"))
        self.assertEqual(list_response.status_code, 200)
        self.assertNotContains(list_response, "تنظیم به‌عنوان شاخص")

        toggle_response = self.client.post(reverse("martyrs:panel_martyr_toggle", args=[self.martyr.pk, "feature"]))
        self.assertEqual(toggle_response.status_code, 302)
        self.martyr.refresh_from_db()
        self.assertFalse(self.martyr.is_featured)

    def test_martyr_create_page_renders_full_form(self):
        self._login_as_superuser()
        response = self.client.get(reverse("martyrs:panel_martyr_new"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ثبت شهید جدید")
        self.assertContains(response, "نام خانوادگی")
        self.assertContains(response, "ذخیره تغییرات")

    def test_martyr_create_through_panel(self):
        self._login_as_superuser()
        response = self.client.post(
            reverse("martyrs:panel_martyr_new"),
            {"first_name": "حسن", "last_name": "باقری", "is_published": "on"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Martyr.objects.filter(first_name="حسن", last_name="باقری").exists())

    def test_jalali_date_saves_through_panel_form(self):
        from jalali_date import date2jalali

        self._login_as_superuser()
        response = self.client.post(
            reverse("martyrs:panel_martyr_edit", args=[self.martyr.pk]),
            {"first_name": "علی", "last_name": "حسینی", "martyrdom_date": "1363-11-19"},
        )
        self.martyr.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(date2jalali(self.martyr.martyrdom_date).strftime("%Y/%m/%d"), "1363/11/19")

    def test_custom_section_add_and_public_display(self):
        self._login_as_superuser()
        response = self.client.post(
            reverse("martyrs:panel_section_add", args=[self.martyr.pk]),
            {"title": "دوران کودکی", "content": "روایتی از کودکی شهید", "sort_order": "1"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.martyr.sections.filter(title="دوران کودکی").exists())

        public = self.client.get(reverse("martyrs:detail", args=[self.martyr.slug]))
        self.assertContains(public, "دوران کودکی")

    def test_empty_fields_hidden_on_public_detail(self):
        self.martyr.family_life = ""
        self.martyr.save()
        response = self.client.get(reverse("martyrs:detail", args=[self.martyr.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "اطلاعات این بخش هنوز ثبت نشده است")
        self.assertNotContains(response, "زندگی خانوادگی")

    def test_jalali_date_in_panel_list(self):
        from jdatetime import date as jdate

        self._login_as_superuser()
        response = self.client.get(reverse("martyrs:panel_martyr_list"))
        expected = jdate.fromgregorian(date=self.martyr.martyrdom_date).strftime("%Y/%m/%d")

        self.assertContains(response, expected)

    def test_logs_page_lists_recent_changes(self):
        self._login_as_superuser()
        self.client.post(
            reverse("martyrs:panel_martyr_toggle", args=[self.martyr.pk, "feature"])
        )
        response = self.client.get(reverse("martyrs:panel_logs"))

        self.assertContains(response, "تاریخچه تغییرات")
