from datetime import timedelta
from collections import OrderedDict

from django.db.models import Count, Q, F
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.accounts.decorators import get_user_studio
from apps.accounts.models import User
from apps.events.models import Client
from apps.gallery.models import ClientGallery, GalleryDownloadLog, GalleryFavorite, GalleryVisit
from apps.media.models import Media


class GalleryAnalyticsService:
    @staticmethod
    def _get_studio(user):
        if user.role == User.Role.SUPER_ADMIN:
            return None
        return get_user_studio(user)

    @staticmethod
    def _can_access_analytics(user):
        if user.role == User.Role.SUPER_ADMIN:
            return True
        if user.role == User.Role.STUDIO_OWNER:
            return True
        if user.role == User.Role.STAFF:
            staff_profile = getattr(user, "staff_profiles", None)
            return bool(
                staff_profile
                and staff_profile.first()
                and staff_profile.first().has_permission("view_analytics")
            )
        return False

    @staticmethod
    def _base_gallery_queryset(user):
        studio = GalleryAnalyticsService._get_studio(user)
        qs = ClientGallery.objects.select_related("event", "event__studio")
        if studio:
            return qs.filter(event__studio=studio)
        return qs

    @staticmethod
    def get_stats(user, days=30):
        base = GalleryAnalyticsService._base_gallery_queryset(user)
        start_date = timezone.now() - timedelta(days=days)

        total_visits = GalleryVisit.objects.filter(gallery__in=base, visited_at__gte=start_date).count()
        total_downloads = GalleryDownloadLog.objects.filter(gallery__in=base, downloaded_at__gte=start_date).count()
        total_favorites = GalleryFavorite.objects.filter(gallery__in=base, created_at__gte=start_date).count()

        return {
            "total_galleries": base.count(),
            "total_visits": total_visits,
            "total_downloads": total_downloads,
            "total_favorites": total_favorites,
            "active_galleries": base.filter(is_active=True).count(),
            "protected_galleries": base.filter(access_type=ClientGallery.AccessType.PASSWORD_PROTECTED).count(),
            "private_galleries": base.filter(access_type=ClientGallery.AccessType.PRIVATE).count(),
        }

    @staticmethod
    def get_daily_stats(user, days=30):
        base = GalleryAnalyticsService._base_gallery_queryset(user)
        start_date = timezone.now() - timedelta(days=days)
        end_date = timezone.now()

        visits_qs = (
            GalleryVisit.objects.filter(gallery__in=base, visited_at__gte=start_date)
            .annotate(date=TruncDate("visited_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        downloads_qs = (
            GalleryDownloadLog.objects.filter(gallery__in=base, downloaded_at__gte=start_date)
            .annotate(date=TruncDate("downloaded_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        favorites_qs = (
            GalleryFavorite.objects.filter(gallery__in=base, created_at__gte=start_date)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        visits_by_date = {item["date"]: item["count"] for item in visits_qs}
        downloads_by_date = {item["date"]: item["count"] for item in downloads_qs}
        favorites_by_date = {item["date"]: item["count"] for item in favorites_qs}

        date_range = []
        current = end_date.date()
        start = (end_date - timedelta(days=days)).date()
        while current >= start:
            date_range.append(current)
            current -= timedelta(days=1)
        date_range.reverse()

        daily = []
        for d in date_range:
            daily.append({
                "date": d.isoformat(),
                "visits": visits_by_date.get(d, 0),
                "downloads": downloads_by_date.get(d, 0),
                "favorites": favorites_by_date.get(d, 0),
            })
        return daily

    @staticmethod
    def get_popular_galleries(user, limit=5, days=None):
        base = GalleryAnalyticsService._base_gallery_queryset(user)
        qs = base.annotate(
            visit_count=Count("visits", distinct=True),
            download_count=Count("download_logs", distinct=True),
            favorite_count=Count("favorites", distinct=True),
        )
        if days:
            start_date = timezone.now() - timedelta(days=days)
            qs = qs.filter(
                Q(visits__visited_at__gte=start_date)
                | Q(download_logs__downloaded_at__gte=start_date)
                | Q(favorites__created_at__gte=start_date)
            ).distinct()
        return list(
            qs.order_by("-visit_count", "-download_count", "-favorite_count")[:limit].values(
                "id", "name", "event__title", "visit_count", "download_count", "favorite_count"
            )
        )

    @staticmethod
    def get_popular_media(user, limit=10, days=None):
        studio = GalleryAnalyticsService._get_studio(user)
        base = GalleryAnalyticsService._base_gallery_queryset(user)
        gallery_ids = list(base.values_list("id", flat=True))

        qs = Media.objects.filter(
            Q(download_logs__gallery__in=gallery_ids)
            | Q(gallery_favorites__gallery__in=gallery_ids)
        ).distinct()

        if days:
            start_date = timezone.now() - timedelta(days=days)
            qs = qs.filter(
                Q(download_logs__downloaded_at__gte=start_date)
                | Q(gallery_favorites__created_at__gte=start_date)
            ).distinct()

        qs = qs.annotate(
            downloads=Count("download_logs", filter=Q(download_logs__gallery__in=gallery_ids), distinct=True),
            favorites=Count("gallery_favorites", filter=Q(gallery_favorites__gallery__in=gallery_ids), distinct=True),
            view_count_media=F("view_count"),
        ).select_related("event", "album")

        return list(
            qs.order_by("-downloads", "-favorites", "-view_count_media")[:limit].values(
                "id", "uuid", "title", "event__title", "album__title", "downloads", "favorites", "view_count_media"
            )
        )

    @staticmethod
    def get_recent_activity(user, limit=10):
        studio = GalleryAnalyticsService._get_studio(user)
        base = GalleryAnalyticsService._base_gallery_queryset(user)
        gallery_ids = list(base.values_list("id", flat=True))

        visits = list(
            GalleryVisit.objects.filter(gallery__in=base)
            .select_related("gallery", "gallery__event")
            .order_by("-visited_at")[: limit * 3]
            .values("gallery__name", "visited_at", "session_id")
        )
        downloads = list(
            GalleryDownloadLog.objects.filter(gallery__in=base)
            .select_related("gallery", "gallery__event", "photo")
            .order_by("-downloaded_at")[: limit * 3]
            .values("gallery__name", "downloaded_at", "photo__title")
        )
        favorites = list(
            GalleryFavorite.objects.filter(gallery__in=base)
            .select_related("gallery", "gallery__event", "photo")
            .order_by("-created_at")[: limit * 3]
            .values("gallery__name", "created_at", "photo__title")
        )

        activity = []
        for item in visits:
            activity.append({
                "type": "visit",
                "gallery": item["gallery__name"],
                "media": None,
                "timestamp": item["visited_at"].isoformat() if item["visited_at"] else None,
            })
        for item in downloads:
            activity.append({
                "type": "download",
                "gallery": item["gallery__name"],
                "media": item["photo__title"],
                "timestamp": item["downloaded_at"].isoformat() if item["downloaded_at"] else None,
            })
        for item in favorites:
            activity.append({
                "type": "favorite",
                "gallery": item["gallery__name"],
                "media": item["photo__title"],
                "timestamp": item["created_at"].isoformat() if item["created_at"] else None,
            })

        activity.sort(key=lambda x: x["timestamp"] or "", reverse=True)
        return activity[:limit]

    @staticmethod
    def get_dashboard_analytics(user, days=30):
        if not GalleryAnalyticsService._can_access_analytics(user):
            return None

        return {
            "stats": GalleryAnalyticsService.get_stats(user, days=days),
            "daily": GalleryAnalyticsService.get_daily_stats(user, days=days),
            "popular_galleries": GalleryAnalyticsService.get_popular_galleries(user, limit=5, days=days),
            "popular_media": GalleryAnalyticsService.get_popular_media(user, limit=10, days=days),
            "recent_activity": GalleryAnalyticsService.get_recent_activity(user, limit=10),
        }
