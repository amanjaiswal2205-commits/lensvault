from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.events.models import Event, EventStatus, EventVisibility
from apps.albums.models import Album
from apps.media.models import Media


User = get_user_model()


@override_settings(
    USE_SQLITE=True,
    STORAGES={
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    },
)
class MediaCrossStudioAccessTestCase(TestCase):
    def setUp(self):
        self.owner_a = User.objects.create_user(
            email="ownera@example.com",
            username="ownera",
            password="testpass123",
            role=User.Role.STUDIO_OWNER,
        )
        self.owner_b = User.objects.create_user(
            email="ownerb@example.com",
            username="ownerb",
            password="testpass123",
            role=User.Role.STUDIO_OWNER,
        )
        self.staff_a = User.objects.create_user(
            email="staffa@example.com",
            username="staffa",
            password="testpass123",
            role=User.Role.STAFF,
        )
        self.client_user = User.objects.create_user(
            email="client@example.com",
            username="client",
            password="testpass123",
            role=User.Role.CLIENT,
        )
        self.super_admin = User.objects.create_superuser(
            email="super@example.com",
            username="super",
            password="testpass123",
        )

        self.studio_a = self.owner_a.owned_studios.create(name="Studio A")
        self.studio_b = self.owner_b.owned_studios.create(name="Studio B")

        self.event_a = Event.objects.create(
            title="Event A",
            event_date="2025-01-01",
            status=EventStatus.PUBLISHED,
            visibility=EventVisibility.PUBLIC,
            studio=self.studio_a,
            created_by=self.owner_a,
        )
        self.event_b = Event.objects.create(
            title="Event B",
            event_date="2025-01-01",
            status=EventStatus.PUBLISHED,
            visibility=EventVisibility.PUBLIC,
            studio=self.studio_b,
            created_by=self.owner_b,
        )

        self.album_a = Album.objects.create(
            title="Album A",
            event=self.event_a,
            created_by=self.owner_a,
        )
        self.album_b = Album.objects.create(
            title="Album B",
            event=self.event_b,
            created_by=self.owner_b,
        )

        self.media_file_a = SimpleUploadedFile("media_a.jpg", b"content", content_type="image/jpeg")
        self.media_file_b = SimpleUploadedFile("media_b.jpg", b"content", content_type="image/jpeg")

        self.media_a = Media.objects.create(
            album=self.album_a,
            event=self.event_a,
            title="Media A",
            file=self.media_file_a,
            status="active",
        )
        self.media_b = Media.objects.create(
            album=self.album_b,
            event=self.event_b,
            title="Media B",
            file=self.media_file_b,
            status="active",
        )

    def test_anonymous_media_detail_redirect_to_login(self):
        url = reverse("media:media_detail", kwargs={"uuid": str(self.media_a.uuid)})
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}")

    def test_anonymous_media_edit_redirect_to_login(self):
        url = reverse("media:media_update", kwargs={"uuid": str(self.media_a.uuid)})
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}")

    def test_anonymous_media_delete_redirect_to_login(self):
        url = reverse("media:media_delete", kwargs={"uuid": str(self.media_a.uuid)})
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}")

    def test_studio_owner_a_can_access_own_media(self):
        self.client.force_login(self.owner_a)
        url = reverse("media:media_detail", kwargs={"uuid": str(self.media_a.uuid)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["media_item"], self.media_a)

    def test_studio_owner_a_cannot_access_studio_b_media(self):
        self.client.force_login(self.owner_a)
        url = reverse("media:media_detail", kwargs={"uuid": str(self.media_b.uuid)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_staff_can_access_assigned_studio_media(self):
        from apps.accounts.decorators import get_user_studio
        import functools
        original_get_user_studio = get_user_studio
        def mock_get_user_studio(user):
            if user == self.staff_a:
                return self.studio_a
            return original_get_user_studio(user)
        import apps.accounts.decorators as dec
        dec.get_user_studio = mock_get_user_studio
        import apps.media.views as views
        views.get_user_studio = mock_get_user_studio
        self.client.force_login(self.staff_a)
        url = reverse("media:media_detail", kwargs={"uuid": str(self.media_a.uuid)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_staff_cannot_access_another_studio_media(self):
        import apps.accounts.decorators as dec
        import apps.media.views as views
        original_get_user_studio = dec.get_user_studio
        def mock_get_user_studio(user):
            if user == self.staff_a:
                return self.studio_a
            return original_get_user_studio(user)
        dec.get_user_studio = mock_get_user_studio
        views.get_user_studio = mock_get_user_studio
        self.client.force_login(self.staff_a)
        url = reverse("media:media_detail", kwargs={"uuid": str(self.media_b.uuid)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_client_cannot_access_internal_media_management(self):
        self.client.force_login(self.client_user)
        url = reverse("media:media_detail", kwargs={"uuid": str(self.media_a.uuid)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_super_admin_can_access_all_media(self):
        self.client.force_login(self.super_admin)
        url_a = reverse("media:media_detail", kwargs={"uuid": str(self.media_a.uuid)})
        response_a = self.client.get(url_a)
        self.assertEqual(response_a.status_code, 200)
        url_b = reverse("media:media_detail", kwargs={"uuid": str(self.media_b.uuid)})
        response_b = self.client.get(url_b)
        self.assertEqual(response_b.status_code, 200)

    def test_cross_studio_edit_blocked(self):
        self.client.force_login(self.owner_a)
        url = reverse("media:media_update", kwargs={"uuid": str(self.media_b.uuid)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_cross_studio_delete_blocked(self):
        self.client.force_login(self.owner_a)
        url = reverse("media:media_delete", kwargs={"uuid": str(self.media_b.uuid)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
