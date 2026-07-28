import unittest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.accounts.forms import RegistrationForm

User = get_user_model()


class AuthRegistrationBugTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.base_data = {
            "full_name": "Test User",
            "username": "regtest",
            "email": "regtest@example.com",
            "mobile_number": "",
            "password1": "StrongPass1!",
            "password2": "StrongPass1!",
        }

    def test_registration_password_is_hashed(self):
        User.objects.filter(email="regtest1@example.com").delete()
        data = {**self.base_data, "username": "regtest1", "email": "regtest1@example.com", "role": "client"}
        form = RegistrationForm(data)
        self.assertTrue(form.is_valid(), msg=form.errors)
        user = form.save()
        self.assertNotEqual(user.password, "StrongPass1!")
        self.assertTrue(user.password.startswith("pbkdf2_sha256"))
        self.assertTrue(user.check_password("StrongPass1!"))
        self.assertFalse(user.check_password("WrongPass"))

    def test_login_succeeds_after_client_registration(self):
        User.objects.filter(email="regtest2@example.com").delete()
        data = {**self.base_data, "username": "regtest2", "email": "regtest2@example.com", "role": "client"}
        form = RegistrationForm(data)
        self.assertTrue(form.is_valid(), msg=form.errors)
        form.save()

        resp = self.client.post(
            reverse("accounts:login"),
            {"username": "regtest2@example.com", "password": "StrongPass1!"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, "/dashboard/")

    def test_login_succeeds_after_photographer_registration(self):
        User.objects.filter(email="regtest_photo@example.com").delete()
        data = {
            **self.base_data,
            "username": "regtest_photo",
            "email": "regtest_photo@example.com",
            "role": "studio_owner",
        }
        form = RegistrationForm(data)
        self.assertTrue(form.is_valid(), msg=form.errors)
        form.save()

        resp = self.client.post(
            reverse("accounts:login"),
            {"username": "regtest_photo@example.com", "password": "StrongPass1!"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, "/dashboard/")

    def test_login_wrong_password_fails(self):
        from django.contrib.auth import authenticate
        User.objects.filter(email="regtest3@example.com").delete()
        data = {**self.base_data, "username": "regtest3", "email": "regtest3@example.com", "role": "studio_owner"}
        form = RegistrationForm(data)
        self.assertTrue(form.is_valid(), msg=form.errors)
        form.save()

        user = authenticate(username="regtest3@example.com", password="WrongPass")
        self.assertIsNone(user)

    def test_super_admin_not_in_registration_form(self):
        form = RegistrationForm()
        role_choices = [choice[0] for choice in form.fields["role"].choices]
        self.assertNotIn(User.Role.SUPER_ADMIN, role_choices)
        self.assertNotIn(User.Role.STAFF, role_choices)

    def test_public_registration_cannot_escalate_to_super_admin(self):
        data = {
            **self.base_data,
            "username": "regtest_sa",
            "email": "regtest_sa@example.com",
            "role": User.Role.SUPER_ADMIN,
        }
        form = RegistrationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("role", form.errors)

    def test_public_registration_cannot_escalate_to_staff(self):
        data = {
            **self.base_data,
            "username": "regtest_staff",
            "email": "regtest_staff@example.com",
            "role": User.Role.STAFF,
        }
        form = RegistrationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("role", form.errors)

    def test_client_login_redirects_to_dashboard_then_home(self):
        user = User.objects.create_user(
            email="clientreg@example.com",
            username="clientreg",
            password="StrongPass1!",
            role=User.Role.CLIENT,
        )
        resp = self.client.post(
            reverse("accounts:login"),
            {"username": "clientreg@example.com", "password": "StrongPass1!"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, "/dashboard/")

    def test_studio_owner_login_redirects_to_dashboard(self):
        user = User.objects.create_user(
            email="soreg@example.com",
            username="soreg",
            password="StrongPass1!",
            role=User.Role.STUDIO_OWNER,
        )
        resp = self.client.post(
            reverse("accounts:login"),
            {"username": "soreg@example.com", "password": "StrongPass1!"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, "/dashboard/")

    def test_password_reset_flow_unchanged(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse
        user = User.objects.create_user(
            email="resetreg@example.com", username="resetreg", password="OldPass1!"
        )
        resp = self.client.post(reverse("accounts:password_reset"), {"email": "resetreg@example.com"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("accounts:password_reset_done"))

    def test_change_password_flow_unchanged(self):
        user = User.objects.create_user(
            email="changereg@example.com", username="changereg", password="OldPass1!"
        )
        self.client.force_login(user)
        resp = self.client.post(
            reverse("accounts:change_password"),
            {"old_password": "OldPass1!", "new_password1": "NewPass1!", "new_password2": "NewPass1!"},
        )
        self.assertEqual(resp.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewPass1!"))

    def test_email_prefix_generates_unique_username(self):
        User.objects.filter(email="prefix_a@example.com").delete()
        User.objects.filter(email="prefix_b@another.com").delete()
        data_a = {
            **self.base_data,
            "username": "prefix_a",
            "email": "prefix_a@example.com",
            "role": "client",
        }
        form_a = RegistrationForm(data_a)
        self.assertTrue(form_a.is_valid(), msg=form_a.errors)
        user_a = form_a.save()

        data_b = {
            **self.base_data,
            "username": "prefix_b",
            "email": "prefix_b@another.com",
            "role": "studio_owner",
        }
        form_b = RegistrationForm(data_b)
        self.assertTrue(form_b.is_valid(), msg=form_b.errors)
        user_b = form_b.save()

        self.assertNotEqual(user_a.username, user_b.username)
        self.assertTrue(user_a.username.startswith("prefix_a"))
        self.assertTrue(user_b.username.startswith("prefix_b"))
        self.assertTrue(user_a.check_password("StrongPass1!"))
        self.assertTrue(user_b.check_password("StrongPass1!"))

    def test_duplicate_email_prefix_gets_unique_username(self):
        User.objects.filter(email="dupuser@example.com").delete()
        User.objects.filter(email="dupuser1@example.com").delete()
        User.objects.filter(email="dupuser2@example.com").delete()

        data1 = {
            **self.base_data,
            "email": "dupuser@example.com",
            "role": "client",
        }
        form1 = RegistrationForm(data1)
        self.assertTrue(form1.is_valid(), msg=form1.errors)
        user1 = form1.save()
        self.assertEqual(user1.username, "dupuser")

        data2 = {
            **self.base_data,
            "email": "dupuser1@example.com",
            "role": "client",
        }
        form2 = RegistrationForm(data2)
        self.assertTrue(form2.is_valid(), msg=form2.errors)
        user2 = form2.save()
        self.assertNotEqual(user2.username, "dupuser")
        self.assertTrue(user2.username.startswith("dupuser"))

        data3 = {
            **self.base_data,
            "email": "dupuser2@example.com",
            "role": "client",
        }
        form3 = RegistrationForm(data3)
        self.assertTrue(form3.is_valid(), msg=form3.errors)
        user3 = form3.save()
        self.assertNotEqual(user3.username, "dupuser")
        self.assertNotEqual(user3.username, user2.username)


if __name__ == "__main__":
    unittest.main()
