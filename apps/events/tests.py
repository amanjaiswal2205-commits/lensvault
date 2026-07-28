from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model

from apps.events.models import Event, EventStatus, EventVisibility


User = get_user_model()


@override_settings(USE_SQLITE=True)
class EventPasswordTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            username="owner",
            password="testpass123",
            role=User.Role.STUDIO_OWNER,
        )
        self.studio = self.user.owned_studios.create(name="Studio A")
        self.event = Event.objects.create(
            title="Test Event",
            event_date="2025-01-01",
            visibility=EventVisibility.PASSWORD_PROTECTED,
            password="legacyplain",
            status=EventStatus.PUBLISHED,
            studio=self.studio,
            created_by=self.user,
        )

    def test_new_password_not_stored_as_plain_text(self):
        event = Event.objects.create(
            title="New Hashed Event",
            event_date="2025-01-01",
            visibility=EventVisibility.PASSWORD_PROTECTED,
            password="secret123",
            status=EventStatus.PUBLISHED,
            studio=self.studio,
            created_by=self.user,
        )
        event.refresh_from_db()
        self.assertNotEqual(event.password, "secret123")
        self.assertTrue(event.password.startswith("pbkdf2_sha256$"))

    def test_check_password_valid(self):
        self.assertTrue(self.event.check_password("legacyplain"))

    def test_check_password_invalid(self):
        self.assertFalse(self.event.check_password("wrongpassword"))

    def test_edit_without_changing_password_does_not_double_hash(self):
        original_password = self.event.password
        self.event.title = "Test Event Updated"
        self.event.save()
        self.event.refresh_from_db()
        self.assertEqual(self.event.password, original_password)
        self.assertTrue(self.event.check_password("legacyplain"))

    def test_legacy_password_upgraded_on_successful_check(self):
        Event.objects.filter(pk=self.event.pk).update(password="legacyplain")
        self.event.refresh_from_db()
        self.assertFalse(self.event.password.startswith("pbkdf2_sha256$"))
        self.assertTrue(self.event.check_password("legacyplain"))
        self.event.refresh_from_db()
        self.assertTrue(self.event.password.startswith("pbkdf2_sha256$"))
        self.assertTrue(self.event.check_password("legacyplain"))

    def test_blank_password_event_behavior(self):
        event = Event.objects.create(
            title="Public Event",
            event_date="2025-01-01",
            visibility=EventVisibility.PUBLIC,
            password="",
            status=EventStatus.PUBLISHED,
            studio=self.studio,
            created_by=self.user,
        )
        self.assertEqual(event.password, "")
        self.assertFalse(event.requires_password)
