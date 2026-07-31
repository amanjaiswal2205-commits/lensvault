"""
URL configuration for the LensVault project.

App namespaces are wired here. The public QR access route lives at the
project root (``/access/<token>/``) so scanned QR codes resolve directly,
outside the ``/qr/`` management area.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_not_required
from django.contrib import admin
from django.http import Http404
from django.urls import include, path, reverse
from django.shortcuts import redirect
from django.utils import timezone

from apps.events.models import EventStatus, EventVisibility
from apps.gallery.views import PublicGalleryView, gallery_password, toggle_favorite, get_favorites, download_photo
from apps.qr.models import QRCode


@login_not_required
def access_qr(request, token):
    """Resolve a scanned QR code and route the visitor to the event gallery.

    Anonymous users are redirected to the login page. Authenticated users
    are redirected to the gallery URL (which itself enforces further
    visibility / password checks).
    """
    if not request.user.is_authenticated:
        return redirect(
            f"{reverse('accounts:login')}?next={request.path}"
        )

    qr = QRCode.objects.filter(token=token).select_related("event").first()

    if qr is None or not qr.is_active:
        raise Http404("This QR code is invalid or has been deactivated.")

    event = qr.event

    # Respect existing visibility rules
    if event.status != EventStatus.PUBLISHED:
        raise Http404
    if event.visibility == EventVisibility.PRIVATE:
        raise Http404
    if (
        event.visibility == EventVisibility.PASSWORD_PROTECTED
        and str(event.pk) not in [str(pk) for pk in request.session.get("unlocked_events", [])]
    ):
        # Track the scan even though the visitor still needs the password
        qr.scan_count = (qr.scan_count or 0) + 1
        qr.last_scanned_at = timezone.now()
        qr.save(update_fields=["scan_count", "last_scanned_at"])
        return redirect("gallery:event_password", event_slug=event.slug)

    # Successful scan: count it and redirect to the gallery
    qr.scan_count = (qr.scan_count or 0) + 1
    qr.last_scanned_at = timezone.now()
    qr.save(update_fields=["scan_count", "last_scanned_at"])

    return redirect("gallery:event_gallery_detail", event_slug=event.slug)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("events/", include("apps.events.urls")),
    path("albums/", include("apps.albums.urls")),
    path("media/", include("apps.media.urls")),
    path("upload/", include("apps.uploads.urls")),
    path("qr/", include("apps.qr.urls")),
    path("gallery/", include("apps.gallery.urls")),
    path("g/<uuid:share_token>/", PublicGalleryView.as_view(), name="public_gallery"),
    path("g/<uuid:share_token>/unlock/", gallery_password, name="gallery_password"),
    path("g/<uuid:share_token>/favorite/", toggle_favorite, name="toggle_favorite"),
    path("g/<uuid:share_token>/favorites/", get_favorites, name="get_favorites"),
    path("g/<uuid:share_token>/download/<int:photo_id>/", download_photo, name="download_photo"),
    path("downloads/", include("apps.downloads.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("access/<str:token>/", access_qr, name="access_qr"),
    path("", include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


import os
from django.contrib.auth import get_user_model

User = get_user_model()
if os.environ.get("RENDER") == "true":
    try:
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                email="admin@gmail.com",
                username="admin22",
                password="Admin@12345",
            )
            print("Production superuser created.")
        else:
            print("Production superuser already exists.")
    except Exception:
        pass
