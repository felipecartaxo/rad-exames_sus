from django.test import SimpleTestCase
from django.urls import reverse


class ProjectFoundationTests(SimpleTestCase):
    def test_admin_login_is_available(self):
        response = self.client.get(reverse("admin:login"))

        self.assertEqual(response.status_code, 200)

