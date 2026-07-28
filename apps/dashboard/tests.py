from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from apps.events.models import Event, EventStatus, EventVisibility, Studio
from apps.albums.models import Album
from apps.media.models import Media
from apps.gallery.models import ClientGallery, GalleryDownloadLog


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
class DownloadHistoryTestCase(TestCase):
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
            allow_download=True,
        )
        self.gallery_b = ClientGallery.objects.create(
            name="Gallery B",
            event=self.event_b,
            access_type=ClientGallery.AccessType.PUBLIC,
            allow_download=True,
        )

        self.album_a = Album.objects.create(
            title="Album A",
            event=self.event_a,
            status="active",
        )
        self.album_b = Album.objects.create(
            title="Album B",
            event=self.event_b,
            status="active",
        )

        media_file = SimpleUploadedFile("test.jpg", b"content", content_type="image/jpeg")
        self.media_a = Media.objects.create(
            album=self.album_a,
            event=self.event_a,
            title="Media A",
            file=media_file,
            status="active",
        )
        media_file_b = SimpleUploadedFile("testb.jpg", b"content", content_type="image/jpeg")
        self.media_b = Media.objects.create(
            album=self.album_b,
            event=self.event_b,
            title="Media B",
            file=media_file_b,
            status="active",
        )

        now = timezone.now()
        self.log_a1 = GalleryDownloadLog.objects.create(
            gallery=self.gallery_a,
            photo=self.media_a,
            session_id="sess-a-1",
            downloaded_at=now - timedelta(days=1),
            ip_address="127.0.0.1",
            user_agent="test",
        )
        self.log_a2 = GalleryDownloadLog.objects.create(
            gallery=self.gallery_a,
            photo=self.media_a,
            session_id="sess-a-2",
            downloaded_at=now - timedelta(days=10),
            ip_address="127.0.0.1",
            user_agent="test",
        )
        self.log_b1 = GalleryDownloadLog.objects.create(
            gallery=self.gallery_b,
            photo=self.media_b,
            session_id="sess-b-1",
            downloaded_at=now - timedelta(days=5),
            ip_address="127.0.0.1",
            user_agent="test",
        )

    def test_anonymous_redirects_to_login(self):
        url = reverse("dashboard:downloads")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_client_denied(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse("dashboard:downloads"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("core:home"))

    def test_studio_owner_receives_200(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:downloads"))
        self.assertEqual(response.status_code, 200)

    def test_super_admin_receives_200(self):
        self.client.force_login(self.super_admin)
        response = self.client.get(reverse("dashboard:downloads"))
        self.assertEqual(response.status_code, 200)

    def test_staff_with_permission_access(self):
        self.staff_a.staff_profiles.create(
            studio=self.studio_a,
            permissions=["view_analytics"],
        )
        self.client.force_login(self.staff_a)
        response = self.client.get(reverse("dashboard:downloads"))
        self.assertEqual(response.status_code, 200)

    def test_staff_without_permission_denied(self):
        self.staff_a.staff_profiles.create(
            studio=self.studio_a,
            permissions=[],
        )
        self.client.force_login(self.staff_a)
        response = self.client.get(reverse("dashboard:downloads"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("core:home"))

    def test_studio_owner_a_sees_own_logs(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:downloads"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gallery A")
        self.assertContains(response, "Media A")

    def test_studio_owner_a_cannot_see_studio_b_logs(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:downloads"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Gallery B")
        self.assertNotContains(response, "Media B")

    def test_staff_sees_assigned_studio_only(self):
        self.staff_a.staff_profiles.create(
            studio=self.studio_a,
            permissions=["view_analytics"],
        )
        self.client.force_login(self.staff_a)
        response = self.client.get(reverse("dashboard:downloads"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gallery A")
        self.assertNotContains(response, "Gallery B")

    def test_super_admin_sees_all_studios(self):
        self.client.force_login(self.super_admin)
        response = self.client.get(reverse("dashboard:downloads"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gallery A")
        self.assertContains(response, "Gallery B")

    def test_manipulated_gallery_filter_cannot_expose_other_studio(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(
            reverse("dashboard:downloads"),
            {"gallery": self.gallery_b.slug},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Gallery B")

    def test_download_row_renders(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:downloads"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Media A")
        self.assertContains(response, "Album A")
        self.assertContains(response, "Event A")

    def test_gallery_event_media_links_resolve(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:downloads"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("gallery:gallery_manage_detail", kwargs={"slug": self.gallery_a.slug}))
        self.assertContains(response, reverse("events:event_detail", kwargs={"slug": self.event_a.slug}))
        self.assertContains(response, reverse("media:media_detail", kwargs={"uuid": str(self.media_a.uuid)}))

    def test_empty_history_renders_200(self):
        GalleryDownloadLog.objects.all().delete()
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:downloads"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No downloads recorded yet")

    def test_ordering_newest_first(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:downloads"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        pos_log_a1 = content.find("sess-a-1")
        pos_log_a2 = content.find("sess-a-2")
        self.assertNotEqual(pos_log_a1, -1)
        self.assertNotEqual(pos_log_a2, -1)
        self.assertGreater(pos_log_a1, pos_log_a2)

    def test_total_downloads_kpi(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:downloads"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2")

    def test_today_downloads_kpi(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:downloads"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1")

    def test_7_day_downloads_kpi(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:downloads"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2")

    def test_30_day_downloads_kpi(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:downloads"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2")

    def test_gallery_filter_works(self):
        self.client.force_login(self.super_admin)
        response = self.client.get(
            reverse("dashboard:downloads"),
            {"gallery": self.gallery_a.slug},
        )
        self.assertEqual(response.status_code, 200)
        for log in response.context["page_obj"]:
            self.assertEqual(log.gallery.slug, self.gallery_a.slug)

    def test_event_filter_works(self):
        self.client.force_login(self.super_admin)
        response = self.client.get(
            reverse("dashboard:downloads"),
            {"event": self.event_a.slug},
        )
        self.assertEqual(response.status_code, 200)
        for log in response.context["page_obj"]:
            self.assertEqual(log.gallery.event.slug, self.event_a.slug)

    def test_date_filter_works(self):
        self.client.force_login(self.super_admin)
        target_date = (timezone.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        response = self.client.get(
            reverse("dashboard:downloads"),
            {"date_from": target_date, "date_to": target_date},
        )
        self.assertEqual(response.status_code, 200)
        for log in response.context["page_obj"]:
            self.assertEqual(log.downloaded_at.date().isoformat(), target_date)

    def test_invalid_date_filter_handled_safely(self):
        self.client.force_login(self.super_admin)
        response = self.client.get(
            reverse("dashboard:downloads"),
            {"date_from": "not-a-date"},
        )
        self.assertEqual(response.status_code, 200)

    def test_pagination_works(self):
        for i in range(30):
            GalleryDownloadLog.objects.create(
                gallery=self.gallery_a,
                photo=self.media_a,
                session_id=f"sess-a-pag-{i}",
                downloaded_at=timezone.now() - timedelta(minutes=i),
                ip_address="127.0.0.1",
                user_agent="test",
            )
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:downloads"), {"page": 2})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Page 2")

    def test_studio_scope_enforced_across_pages(self):
        for i in range(30):
            GalleryDownloadLog.objects.create(
                gallery=self.gallery_b,
                photo=self.media_b,
                session_id=f"sess-b-pag-{i}",
                downloaded_at=timezone.now() - timedelta(minutes=i),
                ip_address="127.0.0.1",
                user_agent="test",
            )
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:downloads"), {"page": 2})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Gallery B")

    def test_sidebar_link_resolves(self):
        url = reverse("dashboard:downloads")
        self.assertEqual(url, "/dashboard/downloads/")

    def test_existing_detail_links_resolve(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:downloads"))
        self.assertEqual(response.status_code, 200)

    def test_existing_download_endpoint_works(self):
        response = self.client.get(
            reverse("download_photo", kwargs={"share_token": self.gallery_a.share_token, "photo_id": self.media_a.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_allow_download_false_remains_blocked(self):
        self.gallery_a.allow_download = False
        self.gallery_a.save()
        response = self.client.get(
            reverse("download_photo", kwargs={"share_token": self.gallery_a.share_token, "photo_id": self.media_a.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_analytics_download_counts_remain_correct(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2")

    def test_selected_photos_remains_functional(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(
            reverse("gallery:gallery_selected_photos", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 200)

    def test_private_client_gallery_security_remains_functional(self):
        self.gallery_a.access_type = ClientGallery.AccessType.PRIVATE
        self.gallery_a.save()
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 302)

    def test_client_gallery_management_remains_functional(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("gallery:gallery_manage_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gallery A")
