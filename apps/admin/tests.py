from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse

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
class AdminNavigationTestCase(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            email="super@example.com",
            username="superuser",
            password="superpass123",
        )

    def test_admin_index(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)

    def test_admin_navigation_links(self):
        self.client.force_login(self.superuser)
        links = [
            ("admin:index", {}),
            ("admin:events_event_changelist", {}),
            ("admin:albums_album_changelist", {}),
            ("admin:gallery_clientgallery_changelist", {}),
            ("admin:media_media_changelist", {}),
            ("admin:cms_herosection_changelist", {}),
            ("admin:cms_feature_changelist", {}),
            ("admin:cms_mediaasset_changelist", {}),
            ("admin:cms_seosettings_changelist", {}),
            ("admin:cms_themesettings_changelist", {}),
            ("admin:gallery_galleryvisit_changelist", {}),
            ("admin:gallery_gallerydownloadlog_changelist", {}),
            ("admin:gallery_galleryfavorite_changelist", {}),
            ("admin:accounts_user_changelist", {}),
            ("admin:accounts_staff_changelist", {}),
            ("admin:auth_group_changelist", {}),
            ("admin:cms_sitesettings_changelist", {}),
        ]
        for url_name, kwargs in links:
            with self.subTest(url=url_name):
                url = reverse(url_name, kwargs=kwargs)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, f"Failed for {url_name}")

    def test_admin_quick_actions(self):
        self.client.force_login(self.superuser)
        quick_actions = [
            ("admin:events_event_add", {}),
            ("admin:gallery_clientgallery_add", {}),
            ("admin:media_media_add", {}),
            ("admin:media_media_changelist", {}),
            ("admin:cms_sitesettings_changelist", {}),
        ]
        for url_name, kwargs in quick_actions:
            with self.subTest(url=url_name):
                url = reverse(url_name, kwargs=kwargs)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, f"Failed for {url_name}")
