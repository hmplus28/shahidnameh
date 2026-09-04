from datetime import date

from django.test import TestCase
from django.urls import reverse
from jalali_date import date2jalali

from martyrs.forms import MartyrDirectoryFilterForm
from martyrs.models import Martyr, Memory


class MartyrViewsTests(TestCase):
    def setUp(self):
        self.martyr = Martyr.objects.create(
            first_name="علی",
            last_name="حسینی",
            birth_city="شیراز",
            birth_province="فارس",
            division="لشکر ۱۹ فجر",
            martyrdom_date=date(1985, 2, 8),
            testament_text="نماز و ولایت دو سفارش این وصیت‌نامه هستند.",
            is_featured=True,
        )
        Memory.objects.create(
            martyr=self.martyr,
            category=Memory.Category.COMRADE,
            narrator="هم‌رزم",
            text="خاطره‌ای از جبهه.",
        )

    def test_home_page_renders_in_persian(self):
        response = self.client.get(reverse("martyrs:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "شهیدنامه")
        self.assertContains(response, "علی حسینی")
        self.assertContains(response, 'dir="rtl"')

    def test_directory_filters_by_province_and_testament_keyword(self):
        response = self.client.get(reverse("martyrs:directory"), {"province": "فارس", "will": "نماز"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "علی حسینی")

    def test_directory_returns_partial_for_interactive_request(self):
        response = self.client.get(reverse("martyrs:directory"), {"q": "علی"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "علی حسینی")
        self.assertNotContains(response, "<html")

    def test_jalali_date_filter_converts_to_a_gregorian_database_range(self):
        response = self.client.get(
            reverse("martyrs:directory"),
            {"martyrdom_from": "1363-11-19", "martyrdom_to": "1363-11-19"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "علی حسینی")

    def test_jalali_form_and_detail_display(self):
        form = MartyrDirectoryFilterForm({"martyrdom_from": "1363-11-19"})
        response = self.client.get(self.martyr.get_absolute_url())
        expected_jalali = date2jalali(self.martyr.martyrdom_date).strftime("%Y/%m/%d")

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["martyrdom_from"], self.martyr.martyrdom_date)
        self.assertContains(response, expected_jalali)

    def test_detail_page_and_service_worker_are_available(self):
        detail = self.client.get(self.martyr.get_absolute_url())
        worker = self.client.get(reverse("martyrs:service-worker"))

        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "وصیت‌نامه و کلیدواژه‌ها")
        self.assertEqual(worker.status_code, 200)
        self.assertEqual(worker["Service-Worker-Allowed"], "/")
        self.assertContains(worker, "CACHE_NAME")
