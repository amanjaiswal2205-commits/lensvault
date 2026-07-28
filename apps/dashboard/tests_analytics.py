from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from apps.events.models import Event, EventStatus, EventVisibility
from apps.albums.models import Album
from apps.media.models import Media
from apps.gallery.models import ClientGallery, GalleryVisit, GalleryDownloadLog, GalleryFavorite
from apps.gallery.analytics import GalleryAnalyticsService

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
class DashboardAnalyticsFrontendTestCase(TestCase):
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
        self.staff_b = User.objects.create_user(
            email="staffb@example.com",
            username="staffb",
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

        from apps.accounts.decorators import get_user_studio
        import apps.accounts.decorators as dec
        original_get_user_studio = dec.get_user_studio
        def mock_get_user_studio(user):
            if user in (self.staff_a, self.staff_b):
                return self.studio_a
            return original_get_user_studio(user)
        dec.get_user_studio = mock_get_user_studio
        import apps.gallery.analytics as analytics_mod
        analytics_mod.get_user_studio = mock_get_user_studio

        from apps.accounts.models import Staff
        self.staff_profile_a = Staff.objects.create(user=self.staff_a, studio=self.studio_a, permissions=["view_analytics"])
        Staff.objects.create(user=self.staff_b, studio=self.studio_a, permissions=[])

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

        self.gallery_a = ClientGallery.objects.create(
            name="Gallery A",
            event=self.event_a,
            access_type=ClientGallery.AccessType.PUBLIC,
            is_active=True,
        )
        self.gallery_b = ClientGallery.objects.create(
            name="Gallery B",
            event=self.event_b,
            access_type=ClientGallery.AccessType.PRIVATE,
            is_active=True,
        )

        self.album_a = Album.objects.create(title="Album A", event=self.event_a, created_by=self.owner_a)
        self.media_file = SimpleUploadedFile("media.jpg", b"content", content_type="image/jpeg")
        self.media_a = Media.objects.create(
            album=self.album_a,
            event=self.event_a,
            title="Media A",
            file=self.media_file,
            status="active",
        )

    def _create_visit(self, gallery, days_ago=0):
        visit = GalleryVisit.objects.create(
            gallery=gallery,
            session_id="session123",
            ip_address="127.0.0.1",
            user_agent="test",
        )
        visit.visited_at = timezone.now() - timedelta(days=days_ago)
        visit.save(update_fields=["visited_at"])
        return visit

    def _create_download(self, gallery, photo, days_ago=0):
        download = GalleryDownloadLog.objects.create(
            gallery=gallery,
            photo=photo,
            session_id="session123",
            ip_address="127.0.0.1",
            user_agent="test",
        )
        download.downloaded_at = timezone.now() - timedelta(days=days_ago)
        download.save(update_fields=["downloaded_at"])
        return download

    def _create_favorite(self, gallery, photo, days_ago=0):
        favorite = GalleryFavorite.objects.create(
            gallery=gallery,
            photo=photo,
            session_id="session123",
        )
        favorite.created_at = timezone.now() - timedelta(days=days_ago)
        favorite.save(update_fields=["created_at"])
        return favorite

    # ACCESS CONTROL
    def test_anonymous_analytics_redirects_to_login(self):
        response = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_client_denied(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("core:home"))

    def test_studio_owner_200(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(response.status_code, 200)

    def test_staff_with_permission_200(self):
        self.client.force_login(self.staff_a)
        response = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(response.status_code, 200)

    def test_staff_without_permission_denied(self):
        self.client.force_login(self.staff_b)
        response = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("core:home"))

    def test_super_admin_200(self):
        self.client.force_login(self.super_admin)
        response = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(response.status_code, 200)

    # STUDIO ISOLATION
    def test_studio_owner_excludes_other_studio_data(self):
        self._create_visit(self.gallery_a, days_ago=1)
        self._create_visit(self.gallery_b, days_ago=1)
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gallery A")
        self.assertNotContains(response, "Gallery B")

    def test_staff_excludes_other_studio_data(self):
        self._create_visit(self.gallery_a, days_ago=1)
        self._create_visit(self.gallery_b, days_ago=1)
        self.client.force_login(self.staff_a)
        response = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gallery A")
        self.assertNotContains(response, "Gallery B")

    # DATE RANGE
    def test_days_7_works(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:analytics") + "?days=7")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "7 Days")

    def test_days_30_works(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:analytics") + "?days=30")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "30 Days")

    def test_invalid_days_falls_back_to_30(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:analytics") + "?days=abc")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "30 Days")

    # RENDER CHECKS
    def test_kpi_values_render(self):
        self._create_visit(self.gallery_a, days_ago=1)
        self._create_download(self.gallery_a, self.media_a, days_ago=1)
        self._create_favorite(self.gallery_a, self.media_a, days_ago=1)
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Total Visits")
        self.assertContains(response, "Total Downloads")
        self.assertContains(response, "Total Favorites")

    def test_popular_galleries_render(self):
        self._create_visit(self.gallery_a, days_ago=1)
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Popular Galleries")
        self.assertContains(response, "Gallery A")

    def test_popular_media_render(self):
        self._create_download(self.gallery_a, self.media_a, days_ago=1)
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Popular Media")
        self.assertContains(response, "Media A")

    def test_recent_activity_renders(self):
        self._create_visit(self.gallery_a, days_ago=1)
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recent Activity")

    def test_empty_analytics_page_renders(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No popular galleries yet")
        self.assertContains(response, "No popular media yet")
        self.assertContains(response, "No recent activity")

    # SIDEBAR
    def test_analytics_link_visible_for_studio_owner(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("dashboard:analytics"))

    def test_analytics_link_visible_for_permitted_staff(self):
        self.client.force_login(self.staff_a)
        response = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("dashboard:analytics"))

    def test_analytics_link_hidden_for_staff_without_permission(self):
        self.client.force_login(self.staff_b)
        response = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("core:home"))

    def test_analytics_link_hidden_for_client(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("core:home"))

    # REGRESSION
    def test_client_gallery_management_still_works(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("gallery:gallery_manage_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gallery A")

    def test_private_gallery_security_still_works(self):
        response = self.client.get(reverse("public_gallery", kwargs={"share_token": self.gallery_b.share_token}))
        self.assertEqual(response.status_code, 302)
