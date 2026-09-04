from datetime import date
from urllib.parse import quote

from django.contrib.admin.models import ADDITION, LogEntry
from django.test import TestCase
from django.urls import reverse

from martyrs.models import Martyr


class SeoAndPublishingTests(TestCase):
    def setUp(self):
        self.published = Martyr.objects.create(
            first_name="علی",
            last_name="حسینی",
            martyrdom_date=date(1985, 2, 8),
            is_featured=True,
        )
        self.draft = Martyr.objects.create(
            first_name="رضا",
            last_name="کریمی",
            is_published=False,
        )

    def test_sitemap_lists_published_and_excludes_drafts(self):
        response = self.client.get("/sitemap.xml")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, quote(self.published.slug))
        self.assertNotContains(response, quote(self.draft.slug))

    def test_robots_txt_disallows_admin_and_links_sitemap(self):
        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Disallow: /admin/")
        self.assertContains(response, "Sitemap:")

    def test_home_page_hides_drafts(self):
        response = self.client.get(reverse("martyrs:home"))

        self.assertContains(response, "علی حسینی")
        self.assertNotContains(response, "رضا کریمی")

    def test_directory_hides_drafts_even_when_matching_filters(self):
        self.draft.birth_province = "فارس"
        self.draft.save()

        response = self.client.get(reverse("martyrs:directory"), {"province": "فارس"})

        self.assertNotContains(response, "رضا کریمی")

    def test_draft_detail_is_hidden_from_public_but_visible_to_staff(self):
        url = self.draft.get_absolute_url()

        anonymous = self.client.get(url)
        self.assertEqual(anonymous.status_code, 404)

        self.client.force_login(self._make_staff())
        staff_response = self.client.get(url)
        self.assertEqual(staff_response.status_code, 200)
        self.assertContains(staff_response, "حالت پیش‌نمایش")

    def test_detail_page_renders_seo_meta(self):
        response = self.client.get(self.published.get_absolute_url())

        self.assertContains(response, '<meta property="og:type" content="profile">')
        self.assertContains(response, 'application/ld+json')
        self.assertContains(response, "شهید علی حسینی")

    def test_change_log_is_registered_in_admin(self):
        from django.contrib import admin as dj_admin

        from martyrs.admin import ChangeLog

        self.assertTrue(dj_admin.site.is_registered(ChangeLog))

    def test_admin_editing_creates_a_log_entry(self):
        from django.contrib.auth import get_user_model

        admin_user = get_user_model().objects.create_superuser("logger", "l@example.com", "pass12345")
        self.client.force_login(admin_user)
        url = reverse("admin:martyrs_martyr_add")
        response = self.client.post(
            url,
            {
                "first_name": "مصطفی",
                "last_name": "احمدی",
                "is_published": "on",
                "is_featured": "on",
                "memories-TOTAL_FORMS": "0",
                "memories-INITIAL_FORMS": "0",
                "images-TOTAL_FORMS": "0",
                "images-INITIAL_FORMS": "0",
                "videos-TOTAL_FORMS": "0",
                "videos-INITIAL_FORMS": "0",
                "sections-TOTAL_FORMS": "0",
                "sections-INITIAL_FORMS": "0",
                "injuries-TOTAL_FORMS": "0",
                "injuries-INITIAL_FORMS": "0",
                "comrades-TOTAL_FORMS": "0",
                "comrades-INITIAL_FORMS": "0",
                "_save": "ذخیره",
            },
        )
        self.assertEqual(response.status_code, 302)

        entry = LogEntry.objects.filter(user=admin_user, action_flag=ADDITION).first()
        self.assertIsNotNone(entry)
        self.assertIn("مصطفی", entry.object_repr)

    def _make_staff(self):
        from django.contrib.auth import get_user_model

        return get_user_model().objects.create_user("staffer", "s@example.com", "pass12345", is_staff=True)
