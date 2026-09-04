from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from martyrs.signals import configure_martyr_roles


class MartyrRolePermissionTests(TestCase):
    def setUp(self):
        configure_martyr_roles()
        self.user_model = get_user_model()

    def test_writer_can_create_and_edit_content_but_cannot_delete_or_manage_users(self):
        writer = self.user_model.objects.create_user("writer", password="safe-test-password", is_staff=True)
        writer.groups.add(Group.objects.get(name="نویسنده"))

        self.assertTrue(writer.has_perm("martyrs.add_martyr"))
        self.assertTrue(writer.has_perm("martyrs.change_memory"))
        self.assertTrue(writer.has_perm("martyrs.change_martyrimage"))
        self.assertFalse(writer.has_perm("martyrs.delete_martyr"))
        self.assertFalse(writer.has_perm("auth.change_user"))

    def test_reviewer_can_only_view_content(self):
        reviewer = self.user_model.objects.create_user("reviewer", password="safe-test-password", is_staff=True)
        reviewer.groups.add(Group.objects.get(name="ناظر"))

        self.assertTrue(reviewer.has_perm("martyrs.view_martyr"))
        self.assertTrue(reviewer.has_perm("martyrs.view_martyrvideo"))
        self.assertFalse(reviewer.has_perm("martyrs.add_martyr"))
        self.assertFalse(reviewer.has_perm("martyrs.change_memory"))


class MartyrImageAdminPreviewTests(TestCase):
    def test_image_admin_form_loads_live_preview_assets_and_container(self):
        user_model = get_user_model()
        manager = user_model.objects.create_superuser("media-manager", "media@example.com", "safe-test-password")
        self.client.force_login(manager)

        response = self.client.get("/admin/martyrs/martyrimage/add/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "admin-image-preview")
        self.assertContains(response, "admin-image-preview")
        self.assertContains(response, "image-live-preview")
