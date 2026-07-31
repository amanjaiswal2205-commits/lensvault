from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.events.models import Event, EventStatus, EventVisibility
from apps.albums.models import Album
from apps.media.models import Media
from apps.gallery.models import ClientGallery


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
class RuntimeSmokeTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            username="testuser",
            password="testpass123",
            role=User.Role.STUDIO_OWNER,
        )
        self.studio = self.user.owned_studios.create(name="Studio A")
        self.event = Event.objects.create(
            title="Test Event",
            event_date="2025-01-01",
            status=EventStatus.PUBLISHED,
            visibility=EventVisibility.PUBLIC,
            studio=self.studio,
            created_by=self.user,
        )
        self.album = Album.objects.create(
            title="Test Album",
            event=self.event,
            created_by=self.user,
        )
        self.media_file = SimpleUploadedFile("test.jpg", b"content", content_type="image/jpeg")
        self.media = Media.objects.create(
            album=self.album,
            event=self.event,
            title="Test Media",
            file=self.media_file,
            status="active",
        )
        self.gallery = ClientGallery.objects.create(
            name="Test Gallery",
            event=self.event,
            access_type="public",
        )

    # PUBLIC / AUTH
    def test_home(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)

    def test_login_page(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)

    def test_register_page(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)

    def test_logout_redirect(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("core:home"))

    def test_password_reset_page(self):
        response = self.client.get(reverse("accounts:password_reset"))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_done_page(self):
        response = self.client.get(reverse("accounts:password_reset_done"))
        self.assertEqual(response.status_code, 200)

    # AUTHENTICATED USER
    def test_login_redirect_to_dashboard(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "user@example.com", "password": "testpass123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard:index"))

    def test_dashboard_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 200)

    def test_profile_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)

    def test_edit_profile_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:edit_profile"))
        self.assertEqual(response.status_code, 200)

    def test_change_password_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:change_password"))
        self.assertEqual(response.status_code, 200)

    # MANAGEMENT
    def test_events_list_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("events:event_list"))
        self.assertEqual(response.status_code, 200)

    def test_event_create_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("events:event_create"))
        self.assertEqual(response.status_code, 200)

    def test_event_detail_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("events:event_detail", kwargs={"slug": self.event.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("gallery:event_gallery_detail", kwargs={"event_slug": self.event.slug}))
        self.assertContains(response, reverse("qr:generate", kwargs={"event_slug": self.event.slug}))

    def test_albums_list_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("albums:album_list"))
        self.assertEqual(response.status_code, 200)

    def test_album_create_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("albums:album_create"))
        self.assertEqual(response.status_code, 200)

    def test_album_detail_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("albums:album_detail", kwargs={"slug": self.album.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("gallery:album_gallery", kwargs={"album_slug": self.album.slug}))

    def test_media_list_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("media:media_list"))
        self.assertEqual(response.status_code, 200)

    def test_media_detail_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("media:media_detail", kwargs={"uuid": str(self.media.uuid)}))
        self.assertEqual(response.status_code, 200)

    def test_upload_manager_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("uploads:upload_manager"))
        self.assertEqual(response.status_code, 200)

    # GALLERY
    def test_gallery_event_list_anonymous_redirect(self):
        response = self.client.get(reverse("gallery:event_gallery"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_gallery_event_list_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("gallery:event_gallery"))
        self.assertEqual(response.status_code, 200)

    def test_gallery_event_detail_anonymous_redirect(self):
        response = self.client.get(reverse("gallery:event_gallery_detail", kwargs={"event_slug": self.event.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_gallery_event_detail_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("gallery:event_gallery_detail", kwargs={"event_slug": self.event.slug}))
        self.assertEqual(response.status_code, 200)

    def test_gallery_album_detail_anonymous_redirect(self):
        response = self.client.get(reverse("gallery:album_gallery", kwargs={"album_slug": self.album.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_gallery_album_detail_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("gallery:album_gallery", kwargs={"album_slug": self.album.slug}))
        self.assertEqual(response.status_code, 200)

    def test_public_client_gallery(self):
        response = self.client.get(reverse("public_gallery", kwargs={"share_token": self.gallery.share_token}))
        self.assertEqual(response.status_code, 200)
    def test_gallery_password_page_anonymous_redirect(self):
        self.event.visibility = EventVisibility.PASSWORD_PROTECTED
        self.event.password = "testpass"
        self.event.save()
        response = self.client.get(reverse("gallery:event_password", kwargs={"event_slug": self.event.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_gallery_password_page_authenticated(self):
        self.client.force_login(self.user)
        self.event.visibility = EventVisibility.PASSWORD_PROTECTED
        self.event.password = "testpass"
        self.event.save()
        response = self.client.get(reverse("gallery:event_password", kwargs={"event_slug": self.event.slug}))
        self.assertEqual(response.status_code, 200)

    def test_favorites_endpoint(self):
        response = self.client.get(reverse("get_favorites", kwargs={"share_token": self.gallery.share_token}))
        self.assertEqual(response.status_code, 200)

    def test_download_endpoint(self):
        response = self.client.get(reverse("download_photo", kwargs={"share_token": self.gallery.share_token, "photo_id": self.media.pk}))
        self.assertEqual(response.status_code, 200)

    # QR
    def test_qr_flow_anonymous_redirect_to_login(self):
        from apps.qr.models import QRCode
        qr = QRCode.objects.create(event=self.event, is_active=True)
        response = self.client.get(reverse("access_qr", kwargs={"token": qr.token}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_qr_flow_authenticated_redirects_to_gallery(self):
        self.client.force_login(self.user)
        from apps.qr.models import QRCode
        qr = QRCode.objects.create(event=self.event, is_active=True)
        response = self.client.get(reverse("access_qr", kwargs={"token": qr.token}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("gallery:event_gallery_detail", kwargs={"event_slug": self.event.slug}))

    # ADMIN
    def test_admin_redirect(self):
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 302)

    def test_admin_login_redirect(self):
        response = self.client.get(reverse("admin:login"))
        self.assertEqual(response.status_code, 200)

    def test_admin_dashboard_authenticated_superuser(self):
        superuser = User.objects.create_superuser(
            email="super@example.com",
            username="superuser",
            password="superpass123",
        )
        self.client.force_login(superuser)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)

    # PASSWORD PROTECTED GALLERY
    def test_password_protected_event_gallery_anonymous_redirect(self):
        self.event.visibility = EventVisibility.PASSWORD_PROTECTED
        self.event.password = "testpass"
        self.event.save()
        response = self.client.get(reverse("gallery:event_gallery_detail", kwargs={"event_slug": self.event.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_password_protected_event_gallery_authenticated_redirects_to_password(self):
        self.client.force_login(self.user)
        self.event.visibility = EventVisibility.PASSWORD_PROTECTED
        self.event.password = "testpass"
        self.event.save()
        response = self.client.get(reverse("gallery:event_gallery_detail", kwargs={"event_slug": self.event.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("gallery:event_password", kwargs={"event_slug": self.event.slug}))

    # ANONYMOUS ACCESS TO MANAGEMENT
    def test_anonymous_events_list_redirect(self):
        response = self.client.get(reverse("events:event_list"))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_media_list_redirect(self):
        response = self.client.get(reverse("media:media_list"))
        self.assertEqual(response.status_code, 302)
