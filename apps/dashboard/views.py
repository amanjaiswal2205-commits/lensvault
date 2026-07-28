from datetime import timedelta
from django.db.models import Count, Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.accounts.decorators import get_user_studio
from apps.accounts.models import User
from apps.albums.models import Album
from apps.events.models import Event
from apps.gallery.analytics import GalleryAnalyticsService
from apps.gallery.models import ClientGallery, GalleryDownloadLog
from apps.media.models import Media


def index(request):
    event_count = Event.objects.count()
    album_count = Album.objects.count()
    media_count = Media.objects.count()
    storage_bytes = Media.objects.aggregate(total=Sum("file_size"))["total"] or 0
    storage_gb = round(storage_bytes / (1024 ** 3), 1)
    storage_total_gb = 10
    storage_percent = round((storage_gb / storage_total_gb) * 100) if storage_total_gb else 0

    return render(
        request,
        "dashboard/index.html",
        context={
            "event_count": event_count,
            "album_count": album_count,
            "media_count": media_count,
            "storage_used_gb": storage_gb,
            "storage_total_gb": storage_total_gb,
            "storage_percent": storage_percent,
        },
    )


def analytics(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    if request.user.role == User.Role.CLIENT:
        return redirect("core:home")

    if request.user.role == User.Role.STAFF:
        staff_profile = getattr(request.user, "staff_profiles", None)
        if not (staff_profile and staff_profile.first() and staff_profile.first().has_permission("view_analytics")):
            return redirect("core:home")

    allowed_days = {"7": 7, "30": 30}
    raw_days = request.GET.get("days", "30")
    days = allowed_days.get(raw_days, 30)

    context = GalleryAnalyticsService.get_dashboard_analytics(request.user, days=days)
    if context is None:
        return redirect("core:home")

    context["selected_days"] = days
    context["days_options"] = [
        {"value": 7, "label": "7 Days"},
        {"value": 30, "label": "30 Days"},
    ]

    return render(request, "dashboard/analytics.html", context)


def _download_history_access(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    if request.user.role == User.Role.CLIENT:
        return redirect("core:home")
    if request.user.role == User.Role.STAFF:
        staff_profile = getattr(request.user, "staff_profiles", None)
        if not (staff_profile and staff_profile.first() and staff_profile.first().has_permission("view_analytics")):
            return redirect("core:home")
    return None


def download_history(request):
    access_result = _download_history_access(request)
    if access_result is not None:
        return access_result

    studio = get_user_studio(request.user)

    qs = GalleryDownloadLog.objects.select_related(
        "gallery", "gallery__event", "photo", "photo__album"
    )
    if studio:
        qs = qs.filter(gallery__event__studio=studio)

    gallery_slug = request.GET.get("gallery", "").strip()
    event_slug = request.GET.get("event", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    if gallery_slug:
        qs = qs.filter(gallery__slug=gallery_slug)
    if event_slug:
        qs = qs.filter(gallery__event__slug=event_slug)
    if date_from:
        try:
            from datetime import datetime
            datetime.strptime(date_from, "%Y-%m-%d")
            qs = qs.filter(downloaded_at__date__gte=date_from)
        except ValueError:
            pass
    if date_to:
        try:
            from datetime import datetime
            datetime.strptime(date_to, "%Y-%m-%d")
            qs = qs.filter(downloaded_at__date__lte=date_to)
        except ValueError:
            pass

    qs = qs.order_by("-downloaded_at")

    from django.core.paginator import Paginator

    paginator = Paginator(qs, 25)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    total_downloads = qs.count()
    today = timezone.now().date()
    seven_days_ago = today - timezone.timedelta(days=7)
    thirty_days_ago = today - timezone.timedelta(days=30)

    downloads_today = qs.filter(downloaded_at__date=today).count()
    downloads_7d = qs.filter(downloaded_at__date__gte=seven_days_ago).count()
    downloads_30d = qs.filter(downloaded_at__date__gte=thirty_days_ago).count()

    most_gallery = (
        qs.values("gallery__name", "gallery__slug")
        .annotate(count=Count("id"))
        .order_by("-count")
        .first()
    )
    most_photo = (
        qs.values("photo__title", "photo__uuid")
        .annotate(count=Count("id"))
        .order_by("-count")
        .first()
    )

    if studio:
        available_galleries = ClientGallery.objects.filter(event__studio=studio).order_by("name")
        available_events = Event.objects.filter(studio=studio).order_by("title")
    else:
        available_galleries = ClientGallery.objects.all().order_by("name")
        available_events = Event.objects.all().order_by("title")

    context = {
        "page_obj": page_obj,
        "total_downloads": total_downloads,
        "downloads_today": downloads_today,
        "downloads_7d": downloads_7d,
        "downloads_30d": downloads_30d,
        "most_gallery": most_gallery,
        "most_photo": most_photo,
        "available_galleries": available_galleries,
        "available_events": available_events,
        "selected_gallery": gallery_slug,
        "selected_event": event_slug,
        "date_from": date_from,
        "date_to": date_to,
    }

    return render(request, "dashboard/downloads.html", context)
