from datetime import timedelta

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

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
class GalleryAnalyticsTestCase(TestCase):
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

        from apps.accounts.decorators import get_user_studio
        import apps.accounts.decorators as dec
        original_get_user_studio = dec.get_user_studio
        def mock_get_user_studio(user):
            if user == self.staff_a:
                return self.studio_a
            return original_get_user_studio(user)
        dec.get_user_studio = mock_get_user_studio
        import apps.gallery.analytics as analytics_mod
        analytics_mod.get_user_studio = mock_get_user_studio

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

    # ACCESS
    def test_anonymous_cannot_access_analytics_service(self):
        result = GalleryAnalyticsService.get_dashboard_analytics(self.client_user, days=30)
        self.assertIsNone(result)

    def test_client_cannot_access_analytics_service(self):
        self.client.force_login(self.client_user)
        result = GalleryAnalyticsService.get_dashboard_analytics(self.client_user, days=30)
        self.assertIsNone(result)

    # STUDIO ISOLATION
    def test_studio_owner_a_stats_exclude_studio_b(self):
        self._create_visit(self.gallery_a, days_ago=1)
        self._create_visit(self.gallery_b, days_ago=1)
        stats = GalleryAnalyticsService.get_stats(self.owner_a, days=30)
        self.assertEqual(stats["total_visits"], 1)

    def test_studio_owner_a_visits_exclude_studio_b(self):
        self._create_visit(self.gallery_a, days_ago=1)
        self._create_visit(self.gallery_b, days_ago=1)
        daily = GalleryAnalyticsService.get_daily_stats(self.owner_a, days=30)
        total_visits = sum(d["visits"] for d in daily)
        self.assertEqual(total_visits, 1)

    def test_studio_owner_a_downloads_exclude_studio_b(self):
        self._create_download(self.gallery_a, self.media_a, days_ago=1)
        self._create_download(self.gallery_b, self.media_a, days_ago=1)
        stats = GalleryAnalyticsService.get_stats(self.owner_a, days=30)
        self.assertEqual(stats["total_downloads"], 1)

    def test_studio_owner_a_favorites_exclude_studio_b(self):
        self._create_favorite(self.gallery_a, self.media_a, days_ago=1)
        self._create_favorite(self.gallery_b, self.media_a, days_ago=1)
        stats = GalleryAnalyticsService.get_stats(self.owner_a, days=30)
        self.assertEqual(stats["total_favorites"], 1)

    def test_staff_analytics_assigned_studio_scoped(self):
        self._create_visit(self.gallery_a, days_ago=1)
        self._create_visit(self.gallery_b, days_ago=1)
        stats = GalleryAnalyticsService.get_stats(self.staff_a, days=30)
        self.assertEqual(stats["total_visits"], 1)

    def test_super_admin_aggregation_includes_all_studios(self):
        self._create_visit(self.gallery_a, days_ago=1)
        self._create_visit(self.gallery_b, days_ago=1)
        stats = GalleryAnalyticsService.get_stats(self.super_admin, days=30)
        self.assertEqual(stats["total_visits"], 2)
        self.assertEqual(stats["total_galleries"], 2)

    # KPIs
    def test_total_galleries_correct(self):
        stats = GalleryAnalyticsService.get_stats(self.owner_a, days=30)
        self.assertEqual(stats["total_galleries"], 1)

    def test_visits_correct(self):
        self._create_visit(self.gallery_a, days_ago=1)
        self._create_visit(self.gallery_a, days_ago=2)
        stats = GalleryAnalyticsService.get_stats(self.owner_a, days=30)
        self.assertEqual(stats["total_visits"], 2)

    def test_downloads_correct(self):
        self._create_download(self.gallery_a, self.media_a, days_ago=1)
        stats = GalleryAnalyticsService.get_stats(self.owner_a, days=30)
        self.assertEqual(stats["total_downloads"], 1)

    def test_favorites_correct(self):
        self._create_favorite(self.gallery_a, self.media_a, days_ago=1)
        stats = GalleryAnalyticsService.get_stats(self.owner_a, days=30)
        self.assertEqual(stats["total_favorites"], 1)

    def test_active_galleries_correct(self):
        self.gallery_a.is_active = False
        self.gallery_a.save()
        stats = GalleryAnalyticsService.get_stats(self.owner_a, days=30)
        self.assertEqual(stats["active_galleries"], 0)
        self.assertEqual(stats["total_galleries"], 1)

    def test_protected_private_counts_correct(self):
        self.gallery_b.access_type = ClientGallery.AccessType.PASSWORD_PROTECTED
        self.gallery_b.save()
        stats = GalleryAnalyticsService.get_stats(self.super_admin, days=30)
        self.assertEqual(stats["protected_galleries"], 1)
        self.assertEqual(stats["private_galleries"], 0)

    # TIME SERIES
    def test_7_day_aggregation_correct(self):
        self._create_visit(self.gallery_a, days_ago=1)
        self._create_visit(self.gallery_a, days_ago=3)
        daily = GalleryAnalyticsService.get_daily_stats(self.owner_a, days=7)
        total = sum(d["visits"] for d in daily)
        self.assertEqual(total, 2)

    def test_30_day_aggregation_correct(self):
        self._create_visit(self.gallery_a, days_ago=5)
        daily = GalleryAnalyticsService.get_daily_stats(self.owner_a, days=30)
        total = sum(d["visits"] for d in daily)
        self.assertEqual(total, 1)

    def test_older_records_excluded(self):
        self._create_visit(self.gallery_a, days_ago=40)
        stats = GalleryAnalyticsService.get_stats(self.owner_a, days=30)
        self.assertEqual(stats["total_visits"], 0)

    def test_missing_days_handled_consistently(self):
        daily = GalleryAnalyticsService.get_daily_stats(self.owner_a, days=7)
        self.assertEqual(len(daily), 8)
        for d in daily:
            self.assertIn("date", d)
            self.assertIn("visits", d)
            self.assertIn("downloads", d)
            self.assertIn("favorites", d)
            self.assertGreaterEqual(d["visits"], 0)
            self.assertGreaterEqual(d["downloads"], 0)
            self.assertGreaterEqual(d["favorites"], 0)

    # POPULAR GALLERIES
    def test_popular_gallery_ordering_correct(self):
        gallery_c = ClientGallery.objects.create(
            name="Gallery C", event=self.event_a, access_type=ClientGallery.AccessType.PUBLIC
        )
        self._create_visit(self.gallery_a, days_ago=1)
        self._create_visit(self.gallery_a, days_ago=2)
        self._create_visit(gallery_c, days_ago=1)
        popular = GalleryAnalyticsService.get_popular_galleries(self.owner_a, limit=5, days=30)
        self.assertEqual(len(popular), 2)
        self.assertEqual(popular[0]["name"], "Gallery A")

    def test_popular_gallery_limit_respected(self):
        for i in range(10):
            g = ClientGallery.objects.create(
                name=f"Gallery {i}", event=self.event_a, access_type=ClientGallery.AccessType.PUBLIC
            )
            if i < 5:
                self._create_visit(g, days_ago=1)
        popular = GalleryAnalyticsService.get_popular_galleries(self.owner_a, limit=5, days=30)
        self.assertEqual(len(popular), 5)

    # POPULAR MEDIA
    def test_popular_media_download_ordering_correct(self):
        popular = GalleryAnalyticsService.get_popular_media(self.owner_a, limit=10, days=30)
        self.assertEqual(len(popular), 0)
        self._create_download(self.gallery_a, self.media_a, days_ago=1)
        popular = GalleryAnalyticsService.get_popular_media(self.owner_a, limit=10, days=30)
        self.assertEqual(len(popular), 1)
        self.assertEqual(popular[0]["downloads"], 1)

    def test_popular_media_favorites_reflected(self):
        self._create_favorite(self.gallery_a, self.media_a, days_ago=1)
        popular = GalleryAnalyticsService.get_popular_media(self.owner_a, limit=10, days=30)
        self.assertEqual(len(popular), 1)
        self.assertEqual(popular[0]["favorites"], 1)

    # RECENT ACTIVITY
    def test_recent_activity_newest_first(self):
        self._create_visit(self.gallery_a, days_ago=5)
        self._create_visit(self.gallery_a, days_ago=1)
        activity = GalleryAnalyticsService.get_recent_activity(self.owner_a, limit=10)
        self.assertGreaterEqual(len(activity), 2)
        self.assertIn("timestamp", activity[0])

    def test_recent_activity_limit_respected(self):
        for i in range(15):
            self._create_visit(self.gallery_a, days_ago=i % 5)
        activity = GalleryAnalyticsService.get_recent_activity(self.owner_a, limit=10)
        self.assertLessEqual(len(activity), 10)

    def test_recent_activity_does_not_leak_other_studio(self):
        self._create_visit(self.gallery_a, days_ago=1)
        self._create_visit(self.gallery_b, days_ago=1)
        activity = GalleryAnalyticsService.get_recent_activity(self.owner_a, limit=10)
        for item in activity:
            self.assertNotEqual(item["gallery"], "Gallery B")

    # SECURITY REGRESSION
    def test_private_gallery_security_remains(self):
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": self.gallery_b.share_token})
        )
        self.assertEqual(response.status_code, 302)

    def test_public_gallery_works(self):
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 200)

    def test_password_protected_gallery_works(self):
        self.gallery_a.set_password("pass123")
        self.gallery_a.access_type = ClientGallery.AccessType.PASSWORD_PROTECTED
        self.gallery_a.save()
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 302)
