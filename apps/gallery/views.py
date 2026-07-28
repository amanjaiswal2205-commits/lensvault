from django.contrib.auth.decorators import login_not_required
from django.db.models import Count
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from apps.albums.models import Album, AlbumStatus
from apps.events.models import (
    Event,
    EventStatus,
    EventVisibility,
)
from apps.gallery.models import ClientGallery, GalleryDownloadLog, GalleryFavorite
from apps.gallery.services import GalleryAccessService
from apps.media.models import Media, MediaStatus


# ---------------------------------------------------------------------------
# Visibility helpers (security boundary for the public gallery)
# ---------------------------------------------------------------------------

def public_events_queryset():
    """Events that may appear in the public gallery."""
    return (
        Event.objects.filter(
            status=EventStatus.PUBLISHED,
            visibility__in=[EventVisibility.PUBLIC, EventVisibility.PASSWORD_PROTECTED],
        )
        .select_related("created_by")
        .annotate(album_count=Count("albums", distinct=True))
    )


def _event_unlocked(request, event):
    unlocked = request.session.get("unlocked_events", [])
    return str(event.pk) in [str(pk) for pk in unlocked]


def _can_view_event(request, event):
    if event.status != EventStatus.PUBLISHED:
        return False
    if event.visibility == EventVisibility.PUBLIC:
        return True
    if event.visibility == EventVisibility.PASSWORD_PROTECTED:
        return _event_unlocked(request, event)
    return False  # private


def _visible_albums(event):
    return (
        Album.objects.filter(event=event, status=AlbumStatus.ACTIVE)
        .select_related("event")
        .annotate(media_count=Count("media", distinct=True))
    )


def _visible_media(album):
    return Media.objects.filter(album=album, status=MediaStatus.ACTIVE).order_by(
        "created_at"
    )


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


class EventGalleryView(ListView):
    """Public landing: browse all publicly visible events."""

    model = Event
    template_name = "gallery/event_gallery.html"
    context_object_name = "events"
    paginate_by = 12

    def get_queryset(self):
        qs = public_events_queryset()
        search = self.request.GET.get("search", "").strip()
        if search:
            qs = qs.filter(title__icontains=search)
        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = self.request.GET.get("search", "")
        context["total_media"] = Media.objects.filter(
            status=MediaStatus.ACTIVE,
            album__status=AlbumStatus.ACTIVE,
            album__event__in=self.get_queryset(),
        ).count()
        return context


class AlbumGalleryView(View):
    """Album gallery for a single event, or a direct album view.

    Reached via /gallery/event/<event_slug>/ (album cover grid + media)
    or /gallery/album/<album_slug>/ (media of one album).
    """

    def get(self, request, event_slug=None, album_slug=None):
        if album_slug:
            album = get_object_or_404(
                Album.objects.select_related("event").filter(
                    status=AlbumStatus.ACTIVE,
                    event__status=EventStatus.PUBLISHED,
                    event__visibility__in=[
                        EventVisibility.PUBLIC,
                        EventVisibility.PASSWORD_PROTECTED,
                    ],
                ),
                slug=album_slug,
            )
            event = album.event
            if (
                event.visibility == EventVisibility.PASSWORD_PROTECTED
                and not _event_unlocked(request, event)
            ):
                return redirect("gallery:event_password", event_slug=event.slug)
            albums = _visible_albums(event).order_by("album_order", "title")
            active_album_slug = album.slug
        else:
            event = get_object_or_404(public_events_queryset(), slug=event_slug)
            if (
                event.visibility == EventVisibility.PASSWORD_PROTECTED
                and not _event_unlocked(request, event)
            ):
                return redirect("gallery:event_password", event_slug=event.slug)
            albums = _visible_albums(event).order_by("album_order", "title")
            active_album_slug = request.GET.get("album")

        search = request.GET.get("search", "").strip()

        media_qs = Media.objects.filter(
            album__event=event,
            album__status=AlbumStatus.ACTIVE,
            status=MediaStatus.ACTIVE,
        ).select_related("album", "event")

        if active_album_slug:
            media_qs = media_qs.filter(album__slug=active_album_slug)
        if search:
            media_qs = media_qs.filter(title__icontains=search)
        media_qs = media_qs.order_by("created_at")

        from django.core.paginator import Paginator

        paginator = Paginator(media_qs, 24)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        # If this is an AJAX "load more" request, return only the grid fragment.
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return render(
                request,
                "gallery/partials/media_grid.html",
                {"media_items": page_obj, "page_obj": page_obj},
            )

        return render(
            request,
            "gallery/album_gallery.html",
            {
                "event": event,
                "albums": albums,
                "media_items": page_obj,
                "page_obj": page_obj,
                "search": search,
                "album_filter": active_album_slug or "",
            },
        )


class MediaDetailView(View):
    """Media detail page with prev/next navigation within the album."""

    def get(self, request, uuid):
        media = get_object_or_404(
            Media.objects.select_related("album", "album__event", "event"),
            uuid=uuid,
            status=MediaStatus.ACTIVE,
        )
        album = media.album
        event = album.event

        if event.status != EventStatus.PUBLISHED:
            raise Http404
        if event.visibility == EventVisibility.PRIVATE:
            raise Http404
        if (
            event.visibility == EventVisibility.PASSWORD_PROTECTED
            and not _event_unlocked(request, event)
        ):
            return redirect("gallery:event_password", event_slug=event.slug)
        if album.status != AlbumStatus.ACTIVE:
            raise Http404

        siblings = list(_visible_media(album))
        index = next(
            (i for i, m in enumerate(siblings) if str(m.uuid) == str(media.uuid)), 0
        )
        prev_media = siblings[index - 1] if index > 0 else None
        next_media = siblings[index + 1] if index < len(siblings) - 1 else None

        return render(
            request,
            "gallery/media_detail.html",
            {
                "media_item": media,
                "event": event,
                "album": album,
                "prev_media": prev_media,
                "next_media": next_media,
            },
        )


class PublicGalleryView(View):
    """Public gallery access via share token."""

    template_name = "gallery/public_gallery.html"

    def get(self, request, share_token):
        gallery = GalleryAccessService.get_gallery_by_token(share_token)

        if GalleryAccessService.is_private(gallery):
            if not GalleryAccessService.can_access_private(gallery, request):
                if request.user.is_authenticated:
                    raise Http404
                return redirect(f"{reverse('accounts:login')}?next={request.path}")

        if GalleryAccessService.is_password_required(gallery):
            session_key = f"gallery_access_{gallery.share_token}"
            if not request.session.get(session_key):
                return redirect(
                    f"/g/{gallery.share_token}/unlock/"
                )

        event = gallery.event
        albums = (
            Album.objects.filter(event=event, status=AlbumStatus.ACTIVE)
            .select_related("event")
            .annotate(media_count=Count("media", distinct=True))
            .order_by("album_order", "title")
        )

        photos = (
            Media.objects.filter(
                album__event=event,
                album__status=AlbumStatus.ACTIVE,
                status=MediaStatus.ACTIVE,
            )
            .select_related("album", "event")
            .order_by("created_at")
        )

        context = {
            "gallery": gallery,
            "event": event,
            "albums": albums,
            "photos": photos,
        }

        GalleryAccessService.record_visit(gallery, request)

        return render(request, self.template_name, context)


@login_not_required
def gallery_password(request, share_token):
    gallery = GalleryAccessService.get_gallery_by_token(share_token)

    if GalleryAccessService.is_private(gallery):
        if request.user.is_authenticated:
            raise Http404
        return redirect(f"{reverse('accounts:login')}?next={request.path}")

    if not GalleryAccessService.is_password_required(gallery):
        return redirect("public_gallery", share_token=share_token)

    session_key = f"gallery_access_{gallery.share_token}"
    if request.session.get(session_key):
        return redirect("public_gallery", share_token=share_token)

    error = None
    if request.method == "POST":
        password = request.POST.get("password", "")
        if GalleryAccessService.check_password(gallery, password):
            request.session[session_key] = True
            request.session.modified = True
            return redirect("public_gallery", share_token=share_token)
        error = "Incorrect password. Please try again."

    return render(
        request,
        "gallery/gallery_password.html",
        {"gallery": gallery, "event": gallery.event, "error": error},
    )


@login_not_required
def event_password(request, event_slug):
    event = get_object_or_404(
        public_events_queryset(), slug=event_slug
    )
    if event.visibility != EventVisibility.PASSWORD_PROTECTED:
        return redirect("gallery:event_gallery_detail", event_slug=event.slug)

    error = None
    if request.method == "POST":
        password = request.POST.get("password", "")
        if event.check_password(password):
            unlocked = request.session.get("unlocked_events", [])
            if str(event.pk) not in [str(pk) for pk in unlocked]:
                unlocked.append(str(event.pk))
            request.session["unlocked_events"] = unlocked
            request.session.modified = True
            return redirect("gallery:event_gallery_detail", event_slug=event.slug)
        error = "Incorrect password. Please try again."

    return render(
        request,
        "gallery/password_required.html",
        {"event": event, "error": error},
    )


@login_not_required
def toggle_favorite(request, share_token):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)

    gallery = GalleryAccessService.get_gallery_by_token(share_token)

    if GalleryAccessService.is_private(gallery) and not GalleryAccessService.can_access_private(gallery, request):
        raise Http404

    if not gallery.allow_favorites:
        return JsonResponse({"success": False, "error": "Favorites are disabled for this gallery."}, status=403)

    if GalleryAccessService.is_password_required(gallery):
        session_key = f"gallery_access_{gallery.share_token}"
        if not request.session.get(session_key):
            return JsonResponse({"success": False, "error": "Password required."}, status=403)

    try:
        photo_id = request.POST.get("photo_id")
        photo = Media.objects.get(uuid=photo_id)
    except Media.DoesNotExist:
        return JsonResponse({"success": False, "error": "Photo not found."}, status=404)

    session_id = request.session.session_key
    if not session_id:
        request.session.save()
        session_id = request.session.session_key

    favorite, created = GalleryFavorite.objects.get_or_create(
        gallery=gallery,
        photo=photo,
        session_id=session_id,
    )

    if not created:
        favorite.delete()
        return JsonResponse({
            "success": True,
            "favorited": False,
            "count": gallery.favorites.filter(session_id=session_id).count(),
        })

    return JsonResponse({
        "success": True,
        "favorited": True,
        "count": gallery.favorites.filter(session_id=session_id).count(),
    })


@login_not_required
def get_favorites(request, share_token):
    gallery = GalleryAccessService.get_gallery_by_token(share_token)

    if GalleryAccessService.is_private(gallery) and not GalleryAccessService.can_access_private(gallery, request):
        raise Http404

    if not gallery.allow_favorites:
        return JsonResponse({"success": True, "favorites": []})

    if GalleryAccessService.is_password_required(gallery):
        session_key = f"gallery_access_{gallery.share_token}"
        if not request.session.get(session_key):
            return JsonResponse({"success": True, "favorites": []})

    session_id = request.session.session_key
    if not session_id:
        request.session.save()
        session_id = request.session.session_key

    favorites = gallery.favorites.filter(session_id=session_id).select_related("photo")
    favorite_list = [
        {"uuid": str(fav.photo.uuid), "title": fav.photo.title}
        for fav in favorites
    ]

    return JsonResponse({"success": True, "favorites": favorite_list})


@login_not_required
def download_photo(request, share_token, photo_id):
    gallery = GalleryAccessService.get_gallery_by_token(share_token)

    if GalleryAccessService.is_private(gallery) and not GalleryAccessService.can_access_private(gallery, request):
        raise Http404

    if not GalleryAccessService.can_download(gallery, request):
        return HttpResponse("Downloads are disabled for this gallery.", status=403)

    photo = get_object_or_404(Media, pk=photo_id)
    if photo.event_id != gallery.event_id:
        raise Http404("Photo not found.")

    return GalleryAccessService.download_photo(gallery, photo, request)


@login_not_required
def selected_photos(request, share_token):
    gallery = GalleryAccessService.get_gallery_by_token(share_token)

    if GalleryAccessService.is_private(gallery) and not GalleryAccessService.can_access_private(gallery, request):
        if request.user.is_authenticated:
            raise Http404
        return redirect(f"{reverse('accounts:login')}?next={request.path}")

    if GalleryAccessService.is_password_required(gallery):
        session_key = f"gallery_access_{gallery.share_token}"
        if not request.session.get(session_key):
            return redirect(f"/g/{gallery.share_token}/unlock/")

    if not gallery.allow_favorites:
        return render(
            request,
            "gallery/selected_photos.html",
            {
                "gallery": gallery,
                "event": gallery.event,
                "favorites": [],
                "favorite_count": 0,
            },
        )

    session_id = request.session.session_key
    if not session_id:
        request.session.save()
        session_id = request.session.session_key

    favorites = list(
        gallery.favorites.filter(session_id=session_id)
        .select_related("photo", "photo__album", "photo__event")
        .order_by("-created_at")
    )

    return render(
        request,
        "gallery/selected_photos.html",
        {
            "gallery": gallery,
            "event": gallery.event,
            "favorites": favorites,
            "favorite_count": len(favorites),
        },
    )
