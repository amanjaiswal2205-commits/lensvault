from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

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
class ClientGalleryManagementTestCase(TestCase):
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
        import apps.gallery.services as gallery_svc
        gallery_svc.get_user_studio = mock_get_user_studio
        import apps.gallery.forms as gallery_forms
        gallery_forms.get_user_studio = mock_get_user_studio
        import apps.gallery.management_views as gallery_mgmt
        gallery_mgmt.get_user_studio = mock_get_user_studio

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
        )
        self.gallery_b = ClientGallery.objects.create(
            name="Gallery B",
            event=self.event_b,
            access_type=ClientGallery.AccessType.PRIVATE,
        )

    def test_anonymous_list_redirect_to_login(self):
        url = reverse("gallery:gallery_manage_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_anonymous_create_redirect_to_login(self):
        url = reverse("gallery:gallery_manage_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_client_list_denied(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse("gallery:gallery_manage_list"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("core:home"))

    def test_client_create_denied(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse("gallery:gallery_manage_create"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("core:home"))

    def test_studio_owner_a_sees_own_galleries(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("gallery:gallery_manage_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gallery A")
        self.assertNotContains(response, "Gallery B")

    def test_studio_owner_a_cannot_see_studio_b_gallery(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("gallery:gallery_manage_list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Gallery B")

    def test_staff_can_access_gallery_list(self):
        self.client.force_login(self.staff_a)
        response = self.client.get(reverse("gallery:gallery_manage_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gallery A")
        self.assertNotContains(response, "Gallery B")

    def test_staff_cannot_see_another_studio_gallery(self):
        self.client.force_login(self.staff_a)
        response = self.client.get(reverse("gallery:gallery_manage_list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Gallery B")

    def test_super_admin_sees_all_galleries(self):
        self.client.force_login(self.super_admin)
        response = self.client.get(reverse("gallery:gallery_manage_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gallery A")
        self.assertContains(response, "Gallery B")

    def test_studio_owner_event_dropdown_own_events_only(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("gallery:gallery_manage_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Event A")
        self.assertNotContains(response, "Event B")

    def test_studio_owner_cannot_post_another_studio_event(self):
        self.client.force_login(self.owner_a)
        response = self.client.post(
            reverse("gallery:gallery_manage_create"),
            {
                "name": "Hacked Gallery",
                "event": self.event_b.pk,
                "access_type": ClientGallery.AccessType.PUBLIC,
                "is_active": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            ClientGallery.objects.filter(name="Hacked Gallery").exists()
        )

    def test_super_admin_can_create_gallery(self):
        self.client.force_login(self.super_admin)
        response = self.client.post(
            reverse("gallery:gallery_manage_create"),
            {
                "name": "Admin Gallery",
                "event": self.event_a.pk,
                "access_type": ClientGallery.AccessType.PUBLIC,
                "is_active": True,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            ClientGallery.objects.filter(name="Admin Gallery").exists()
        )

    def test_password_protected_gallery_hashes_password(self):
        self.client.force_login(self.owner_a)
        response = self.client.post(
            reverse("gallery:gallery_manage_create"),
            {
                "name": "Secret Gallery",
                "event": self.event_a.pk,
                "access_type": ClientGallery.AccessType.PASSWORD_PROTECTED,
                "gallery_password": "secret123",
                "is_active": True,
            },
        )
        self.assertEqual(response.status_code, 302)
        gallery = ClientGallery.objects.get(name="Secret Gallery")
        self.assertNotEqual(gallery.gallery_password, "secret123")
        self.assertTrue(gallery.gallery_password.startswith("pbkdf2_sha256$"))
        self.assertTrue(gallery.check_password("secret123"))

    def test_raw_password_not_stored(self):
        self.client.force_login(self.owner_a)
        self.client.post(
            reverse("gallery:gallery_manage_create"),
            {
                "name": "Raw Password Gallery",
                "event": self.event_a.pk,
                "access_type": ClientGallery.AccessType.PASSWORD_PROTECTED,
                "gallery_password": "rawpassword",
                "is_active": True,
            },
        )
        gallery = ClientGallery.objects.get(name="Raw Password Gallery")
        self.assertNotIn("rawpassword", gallery.gallery_password)

    def test_share_token_auto_generated(self):
        self.client.force_login(self.owner_a)
        self.client.post(
            reverse("gallery:gallery_manage_create"),
            {
                "name": "Token Gallery",
                "event": self.event_a.pk,
                "access_type": ClientGallery.AccessType.PUBLIC,
                "is_active": True,
            },
        )
        gallery = ClientGallery.objects.get(name="Token Gallery")
        self.assertIsNotNone(gallery.share_token)

    def test_duplicate_gallery_names_unique_slug(self):
        self.client.force_login(self.owner_a)
        self.client.post(
            reverse("gallery:gallery_manage_create"),
            {
                "name": "Duplicate",
                "event": self.event_a.pk,
                "access_type": ClientGallery.AccessType.PUBLIC,
                "is_active": True,
            },
        )
        self.client.post(
            reverse("gallery:gallery_manage_create"),
            {
                "name": "Duplicate",
                "event": self.event_a.pk,
                "access_type": ClientGallery.AccessType.PUBLIC,
                "is_active": True,
            },
        )
        galleries = ClientGallery.objects.filter(name__startswith="Duplicate")
        self.assertEqual(galleries.count(), 2)
        slugs = [g.slug for g in galleries]
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_public_client_gallery_still_works(self):
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 200)

    def test_existing_password_protected_gallery_still_works(self):
        self.gallery_a.set_password("oldpass")
        self.gallery_a.access_type = ClientGallery.AccessType.PASSWORD_PROTECTED
        self.gallery_a.save()
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(str(self.gallery_a.share_token), response.url)

    def test_existing_favorites_still_work(self):
        response = self.client.get(
            reverse("get_favorites", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 200)

    def test_existing_downloads_still_work(self):
        album = Album.objects.create(
            title="Download Album",
            event=self.event_a,
            created_by=self.owner_a,
        )
        media_file = SimpleUploadedFile("dl.jpg", b"content", content_type="image/jpeg")
        media = Media.objects.create(
            album=album,
            event=self.event_a,
            title="DL Media",
            file=media_file,
            status="active",
        )
        response = self.client.get(
            reverse("download_photo", kwargs={"share_token": self.gallery_a.share_token, "photo_id": media.pk})
        )
        self.assertEqual(response.status_code, 200)

    # DETAIL
    def test_anonymous_detail_redirect_to_login(self):
        url = reverse("gallery:gallery_manage_detail", kwargs={"slug": self.gallery_a.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_client_detail_denied(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse("gallery:gallery_manage_detail", kwargs={"slug": self.gallery_a.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("core:home"))

    def test_studio_owner_can_view_own_gallery_detail(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("gallery:gallery_manage_detail", kwargs={"slug": self.gallery_a.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gallery A")
        self.assertContains(response, self.gallery_a.share_token)

    def test_studio_owner_cannot_view_another_studio_gallery_detail(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("gallery:gallery_manage_detail", kwargs={"slug": self.gallery_b.slug}))
        self.assertEqual(response.status_code, 404)

    def test_staff_can_view_assigned_studio_gallery_detail(self):
        self.client.force_login(self.staff_a)
        response = self.client.get(reverse("gallery:gallery_manage_detail", kwargs={"slug": self.gallery_a.slug}))
        self.assertEqual(response.status_code, 200)

    def test_super_admin_can_view_any_gallery_detail(self):
        self.client.force_login(self.super_admin)
        response = self.client.get(reverse("gallery:gallery_manage_detail", kwargs={"slug": self.gallery_a.slug}))
        self.assertEqual(response.status_code, 200)

    def test_gallery_detail_generates_public_url(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("gallery:gallery_manage_detail", kwargs={"slug": self.gallery_a.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.gallery_a.share_token))

    def test_gallery_detail_open_gallery_resolves(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("gallery:gallery_manage_detail", kwargs={"slug": self.gallery_a.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("public_gallery", kwargs={"share_token": self.gallery_a.share_token}))

    def test_gallery_detail_no_password_exposed(self):
        self.gallery_a.set_password("secret123")
        self.gallery_a.save()
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("gallery:gallery_manage_detail", kwargs={"slug": self.gallery_a.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "secret123")
        self.assertNotContains(response, self.gallery_a.gallery_password)

    # EDIT
    def test_owner_can_edit_own_gallery(self):
        self.client.force_login(self.owner_a)
        response = self.client.post(
            reverse("gallery:gallery_manage_update", kwargs={"slug": self.gallery_a.slug}),
            {
                "name": "Gallery A Updated",
                "event": self.event_a.pk,
                "access_type": ClientGallery.AccessType.PUBLIC,
                "is_active": True,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.gallery_a.refresh_from_db()
        self.assertEqual(self.gallery_a.name, "Gallery A Updated")

    def test_owner_cannot_edit_another_studio_gallery(self):
        self.client.force_login(self.owner_a)
        response = self.client.post(
            reverse("gallery:gallery_manage_update", kwargs={"slug": self.gallery_b.slug}),
            {
                "name": "Hacked",
                "event": self.event_b.pk,
                "access_type": ClientGallery.AccessType.PUBLIC,
                "is_active": True,
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_edit_blank_password_preserves_existing_hash(self):
        self.gallery_a.set_password("originalpass")
        self.gallery_a.access_type = ClientGallery.AccessType.PASSWORD_PROTECTED
        self.gallery_a.save()
        original_hash = self.gallery_a.gallery_password
        self.client.force_login(self.owner_a)
        response = self.client.post(
            reverse("gallery:gallery_manage_update", kwargs={"slug": self.gallery_a.slug}),
            {
                "name": "Gallery A Updated",
                "event": self.event_a.pk,
                "access_type": ClientGallery.AccessType.PASSWORD_PROTECTED,
                "is_active": True,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.gallery_a.refresh_from_db()
        self.assertEqual(self.gallery_a.gallery_password, original_hash)
        self.assertTrue(self.gallery_a.check_password("originalpass"))

    def test_edit_new_password_changes_hash(self):
        self.gallery_a.set_password("oldpass")
        self.gallery_a.access_type = ClientGallery.AccessType.PASSWORD_PROTECTED
        self.gallery_a.save()
        self.client.force_login(self.owner_a)
        response = self.client.post(
            reverse("gallery:gallery_manage_update", kwargs={"slug": self.gallery_a.slug}),
            {
                "name": "Gallery A Updated",
                "event": self.event_a.pk,
                "access_type": ClientGallery.AccessType.PASSWORD_PROTECTED,
                "gallery_password": "newpass",
                "is_active": True,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.gallery_a.refresh_from_db()
        self.assertNotEqual(self.gallery_a.gallery_password, "oldpass")
        self.assertTrue(self.gallery_a.check_password("newpass"))

    def test_edit_protected_to_public_clears_password(self):
        self.gallery_a.set_password("secret123")
        self.gallery_a.access_type = ClientGallery.AccessType.PASSWORD_PROTECTED
        self.gallery_a.save()
        self.client.force_login(self.owner_a)
        response = self.client.post(
            reverse("gallery:gallery_manage_update", kwargs={"slug": self.gallery_a.slug}),
            {
                "name": "Gallery A Updated",
                "event": self.event_a.pk,
                "access_type": ClientGallery.AccessType.PUBLIC,
                "is_active": True,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.gallery_a.refresh_from_db()
        self.assertEqual(self.gallery_a.gallery_password, "")

    def test_edit_cross_studio_event_post_rejected(self):
        self.client.force_login(self.owner_a)
        response = self.client.post(
            reverse("gallery:gallery_manage_update", kwargs={"slug": self.gallery_a.slug}),
            {
                "name": "Gallery A Updated",
                "event": self.event_b.pk,
                "access_type": ClientGallery.AccessType.PUBLIC,
                "is_active": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.gallery_a.refresh_from_db()
        self.assertEqual(self.gallery_a.event_id, self.event_a.pk)

    # DELETE
    def test_owner_can_delete_own_gallery(self):
        self.client.force_login(self.owner_a)
        response = self.client.post(
            reverse("gallery:gallery_manage_delete", kwargs={"slug": self.gallery_a.slug})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ClientGallery.objects.filter(pk=self.gallery_a.pk).exists())

    def test_owner_cannot_delete_another_studio_gallery(self):
        self.client.force_login(self.owner_a)
        response = self.client.post(
            reverse("gallery:gallery_manage_delete", kwargs={"slug": self.gallery_b.slug})
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(ClientGallery.objects.filter(pk=self.gallery_b.pk).exists())

    def test_delete_does_not_delete_event(self):
        self.client.force_login(self.owner_a)
        response = self.client.post(
            reverse("gallery:gallery_manage_delete", kwargs={"slug": self.gallery_a.slug})
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Event.objects.filter(pk=self.event_a.pk).exists())

    def test_delete_does_not_delete_album_media(self):
        album = Album.objects.create(title="Album X", event=self.event_a, created_by=self.owner_a)
        media_file = SimpleUploadedFile("media.jpg", b"content", content_type="image/jpeg")
        Media.objects.create(album=album, event=self.event_a, title="Media X", file=media_file, status="active")
        gallery = ClientGallery.objects.create(name="Gallery X", event=self.event_a, access_type=ClientGallery.AccessType.PUBLIC)
        self.client.force_login(self.owner_a)
        response = self.client.post(
            reverse("gallery:gallery_manage_delete", kwargs={"slug": gallery.slug})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ClientGallery.objects.filter(pk=gallery.pk).exists())
        self.assertTrue(Album.objects.filter(pk=album.pk).exists())
        self.assertTrue(Media.objects.filter(title="Media X").exists())

    # SHARING
    def test_share_url_uses_reverse(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("gallery:gallery_manage_detail", kwargs={"slug": self.gallery_a.slug}))
        self.assertEqual(response.status_code, 200)
        expected_url = reverse("public_gallery", kwargs={"share_token": self.gallery_a.share_token})
        self.assertContains(response, expected_url)

    def test_open_gallery_resolves_to_public_gallery(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(reverse("gallery:gallery_manage_detail", kwargs={"slug": self.gallery_a.slug}))
        self.assertEqual(response.status_code, 200)
        public_url = reverse("public_gallery", kwargs={"share_token": self.gallery_a.share_token})
        self.assertContains(response, public_url)

    def test_password_protected_open_gallery_redirects_to_unlock(self):
        self.gallery_a.set_password("pass123")
        self.gallery_a.access_type = ClientGallery.AccessType.PASSWORD_PROTECTED
        self.gallery_a.save()
        response = self.client.get(reverse("public_gallery", kwargs={"share_token": self.gallery_a.share_token}))
        self.assertEqual(response.status_code, 302)
        self.assertIn(str(self.gallery_a.share_token), response.url)

    # PUBLIC ACCESS
    def test_anonymous_can_access_active_public_gallery(self):
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_can_access_active_public_gallery(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 200)

    def test_inactive_public_gallery_denied(self):
        self.gallery_a.is_active = False
        self.gallery_a.save()
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 404)

    def test_expired_public_gallery_denied(self):
        self.gallery_a.expires_at = timezone.now() - timedelta(days=1)
        self.gallery_a.save()
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 404)

    # PASSWORD_PROTECTED ACCESS
    def test_anonymous_password_protected_redirects_to_unlock(self):
        self.gallery_a.set_password("pass123")
        self.gallery_a.access_type = ClientGallery.AccessType.PASSWORD_PROTECTED
        self.gallery_a.save()
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(str(self.gallery_a.share_token), response.url)

    def test_correct_password_unlocks_gallery(self):
        self.gallery_a.set_password("pass123")
        self.gallery_a.access_type = ClientGallery.AccessType.PASSWORD_PROTECTED
        self.gallery_a.save()
        response = self.client.post(
            reverse("gallery_password", kwargs={"share_token": self.gallery_a.share_token}),
            {"password": "pass123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(str(self.gallery_a.share_token), response.url)

    def test_incorrect_password_denied(self):
        self.gallery_a.set_password("pass123")
        self.gallery_a.access_type = ClientGallery.AccessType.PASSWORD_PROTECTED
        self.gallery_a.save()
        response = self.client.post(
            reverse("gallery_password", kwargs={"share_token": self.gallery_a.share_token}),
            {"password": "wrong"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Incorrect password")

    def test_inactive_password_protected_gallery_denied(self):
        self.gallery_a.set_password("pass123")
        self.gallery_a.access_type = ClientGallery.AccessType.PASSWORD_PROTECTED
        self.gallery_a.is_active = False
        self.gallery_a.save()
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 404)

    def test_expired_password_protected_gallery_denied(self):
        self.gallery_a.set_password("pass123")
        self.gallery_a.access_type = ClientGallery.AccessType.PASSWORD_PROTECTED
        self.gallery_a.expires_at = timezone.now() - timedelta(days=1)
        self.gallery_a.save()
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 404)

    # PRIVATE ACCESS
    def test_anonymous_cannot_access_private_gallery(self):
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": self.gallery_b.share_token})
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_random_authenticated_client_cannot_access_private_gallery(self):
        self.client.force_login(self.client_user)
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": self.gallery_b.share_token})
        )
        self.assertEqual(response.status_code, 404)

    def test_client_with_event_link_can_access_private_gallery(self):
        from apps.events.models import Client
        Client.objects.create(user=self.client_user, event=self.event_a)
        gallery_private_a = ClientGallery.objects.create(
            name="Private Gallery Client",
            event=self.event_a,
            access_type=ClientGallery.AccessType.PRIVATE,
        )
        self.client.force_login(self.client_user)
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": gallery_private_a.share_token})
        )
        self.assertEqual(response.status_code, 200)

    def test_client_without_event_link_cannot_access_private_gallery(self):
        gallery_private_a = ClientGallery.objects.create(
            name="Private Gallery Client",
            event=self.event_a,
            access_type=ClientGallery.AccessType.PRIVATE,
        )
        self.client.force_login(self.client_user)
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": gallery_private_a.share_token})
        )
        self.assertEqual(response.status_code, 404)

    def test_studio_owner_can_access_own_private_gallery(self):
        gallery_private_a = ClientGallery.objects.create(
            name="Private Gallery A",
            event=self.event_a,
            access_type=ClientGallery.AccessType.PRIVATE,
        )
        self.client.force_login(self.owner_a)
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": gallery_private_a.share_token})
        )
        self.assertEqual(response.status_code, 200)

    def test_studio_owner_cannot_access_another_studio_private_gallery(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": self.gallery_b.share_token})
        )
        self.assertEqual(response.status_code, 404)

    def test_staff_can_access_assigned_studio_private_gallery(self):
        gallery_private_a = ClientGallery.objects.create(
            name="Private Gallery A",
            event=self.event_a,
            access_type=ClientGallery.AccessType.PRIVATE,
        )
        self.client.force_login(self.staff_a)
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": gallery_private_a.share_token})
        )
        self.assertEqual(response.status_code, 200)

    def test_staff_cannot_access_another_studio_private_gallery(self):
        gallery_private_b = ClientGallery.objects.create(
            name="Private Gallery B",
            event=self.event_b,
            access_type=ClientGallery.AccessType.PRIVATE,
        )
        self.client.force_login(self.staff_a)
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": gallery_private_b.share_token})
        )
        self.assertEqual(response.status_code, 404)

    def test_super_admin_can_access_private_gallery(self):
        self.client.force_login(self.super_admin)
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": self.gallery_b.share_token})
        )
        self.assertEqual(response.status_code, 200)

    def test_inactive_private_gallery_denied_even_to_authorized_user(self):
        gallery_private_a = ClientGallery.objects.create(
            name="Private Gallery A",
            event=self.event_a,
            access_type=ClientGallery.AccessType.PRIVATE,
            is_active=False,
        )
        self.client.force_login(self.owner_a)
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": gallery_private_a.share_token})
        )
        self.assertEqual(response.status_code, 404)

    def test_expired_private_gallery_denied_even_to_authorized_user(self):
        gallery_private_a = ClientGallery.objects.create(
            name="Private Gallery A",
            event=self.event_a,
            access_type=ClientGallery.AccessType.PRIVATE,
            expires_at=timezone.now() - timedelta(days=1),
        )
        self.client.force_login(self.owner_a)
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": gallery_private_a.share_token})
        )
        self.assertEqual(response.status_code, 404)

    def test_share_token_alone_does_not_authorize_private_access(self):
        self.client.force_login(self.owner_a)
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": self.gallery_b.share_token})
        )
        self.assertEqual(response.status_code, 404)

    # SELECTED PHOTOS / FAVORITES PAGE
    def test_public_gallery_selected_photos_page_accessible(self):
        response = self.client.get(
            reverse("gallery:gallery_selected_photos", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Selected Photos")

    def test_selected_photos_empty_state_renders(self):
        response = self.client.get(
            reverse("gallery:gallery_selected_photos", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No favorite photos yet")

    def test_selected_photos_shows_only_current_session_favorites(self):
        album = Album.objects.create(title="Fav Album", event=self.event_a, created_by=self.owner_a)
        media_file = SimpleUploadedFile("fav.jpg", b"content", content_type="image/jpeg")
        media = Media.objects.create(album=album, event=self.event_a, title="Fav Media", file=media_file, status="active")

        session_a = self.client.session
        session_a.create()
        session_id_a = session_a.session_key

        from apps.gallery.models import GalleryFavorite
        fav_a = GalleryFavorite.objects.create(gallery=self.gallery_a, photo=media, session_id=session_id_a)
        session_b = self.client.session
        session_b.create()
        session_id_b = session_b.session_key

        self.client.cookies[settings.SESSION_COOKIE_NAME] = session_id_a
        response = self.client.get(
            reverse("gallery:gallery_selected_photos", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fav Media")

        self.client.cookies[settings.SESSION_COOKIE_NAME] = session_id_b
        response = self.client.get(
            reverse("gallery:gallery_selected_photos", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Fav Media")

    def test_selected_photos_link_present_in_public_gallery(self):
        response = self.client.get(
            reverse("public_gallery", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("gallery:gallery_selected_photos", kwargs={"share_token": self.gallery_a.share_token}))

    def test_password_protected_selected_photos_redirects_to_unlock(self):
        self.gallery_a.set_password("pass123")
        self.gallery_a.access_type = ClientGallery.AccessType.PASSWORD_PROTECTED
        self.gallery_a.save()
        response = self.client.get(
            reverse("gallery:gallery_selected_photos", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(str(self.gallery_a.share_token), response.url)

    def test_private_selected_photos_denied_to_anonymous(self):
        response = self.client.get(
            reverse("gallery:gallery_selected_photos", kwargs={"share_token": self.gallery_b.share_token})
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_private_selected_photos_denied_to_unauthorized_client(self):
        self.client.force_login(self.client_user)
        response = self.client.get(
            reverse("gallery:gallery_selected_photos", kwargs={"share_token": self.gallery_b.share_token})
        )
        self.assertEqual(response.status_code, 404)

    def test_inactive_gallery_selected_photos_denied(self):
        self.gallery_a.is_active = False
        self.gallery_a.save()
        response = self.client.get(
            reverse("gallery:gallery_selected_photos", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 404)

    def test_expired_gallery_selected_photos_denied(self):
        self.gallery_a.expires_at = timezone.now() - timedelta(days=1)
        self.gallery_a.save()
        response = self.client.get(
            reverse("gallery:gallery_selected_photos", kwargs={"share_token": self.gallery_a.share_token})
        )
        self.assertEqual(response.status_code, 404)
