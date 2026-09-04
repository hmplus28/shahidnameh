from datetime import date

from django.test import TestCase
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from jalali_date.widgets import AdminJalaliDateWidget

from martyrs.models import Martyr, Memory


class MartyrModelTests(TestCase):
    def test_creates_a_persian_slug_and_full_name(self):
        martyr = Martyr.objects.create(first_name="محمد", last_name="آقایی")

        self.assertEqual(martyr.full_name, "محمد آقایی")
        self.assertTrue(martyr.slug)
        self.assertTrue(martyr.get_absolute_url().startswith("/martyrs/"))
        self.assertTrue(martyr.get_absolute_url().endswith("/"))

    def test_allocates_a_unique_slug_for_repeated_names(self):
        first = Martyr.objects.create(first_name="حسن", last_name="صادقی")
        second = Martyr.objects.create(first_name="حسن", last_name="صادقی")

        self.assertNotEqual(first.slug, second.slug)

    def test_memory_is_linked_to_its_martyr(self):
        martyr = Martyr.objects.create(first_name="حمید", last_name="کریمی")
        memory = Memory.objects.create(
            martyr=martyr,
            category=Memory.Category.FAMILY,
            narrator="خواهر شهید",
            text="روایتی برای آزمون رابطه خاطره و شهید.",
            recorded_at=date(1986, 1, 1),
        )

        self.assertEqual(martyr.memories.get(), memory)
        self.assertEqual(memory.get_category_display(), "خانواده")

    def test_admin_uses_jalali_date_widgets_for_martyr_dates(self):
        request = RequestFactory().get("/admin/martyrs/martyr/add/")
        martyr_admin = admin.site._registry[Martyr]
        form_class = martyr_admin.get_form(request)

        self.assertIsInstance(form_class.base_fields["birth_date"].widget, AdminJalaliDateWidget)
        self.assertIsInstance(form_class.base_fields["martyrdom_date"].widget, AdminJalaliDateWidget)

    def test_admin_add_form_renders_the_jalali_picker_assets(self):
        user_model = get_user_model()
        manager = user_model.objects.create_superuser("manager", "manager@example.com", "safe-test-password")
        self.client.force_login(manager)

        response = self.client.get("/admin/martyrs/martyr/add/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "django_jalali.min")
        self.assertContains(response, "birth_date")
        self.assertContains(response, "martyrdom_date")
