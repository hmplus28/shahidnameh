from django.test import TestCase


class PwaAndMobileShellTests(TestCase):
    def test_home_contains_installable_pwa_and_mobile_app_shell(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'rel="manifest"')
        self.assertContains(response, 'data-install-card')
        self.assertContains(response, 'class="app-bottom-nav"')
        self.assertContains(response, 'data-nav-toggle-mobile')

    def test_service_worker_is_root_scoped_and_uses_current_cache(self):
        response = self.client.get("/service-worker.js")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Service-Worker-Allowed"], "/")
        self.assertRegex(response.content.decode(), r"shahidnameh-v\d+")
        self.assertIn("SKIP_WAITING", response.content.decode())
