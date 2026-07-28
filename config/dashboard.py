"""
Dashboard callback for the LensVault admin index.

Provides statistics and recent activity data to the custom admin dashboard.
"""

from django.urls import reverse

from apps.accounts.models import User
from apps.events.models import Event, EventStatus, EventVisibility
from apps.gallery.models import (
    ClientGallery,
    GalleryDownloadLog,
    GalleryFavorite,
    GalleryVisit,
)
from apps.media.models import Media


def dashboard_callback(request, context):
    galleries = ClientGallery.objects
    events = Event.objects
    media = Media.objects

    stats = [
        {
            "title": "Total Galleries",
            "value": galleries.count(),
            "icon": "collections",
            "color": "text-violet-600 bg-violet-50 dark:text-violet-400 dark:bg-violet-900/20",
        },
        {
            "title": "Total Events",
            "value": events.count(),
            "icon": "calendar_today",
            "color": "text-sky-600 bg-sky-50 dark:text-sky-400 dark:bg-sky-900/20",
        },
        {
            "title": "Total Photos",
            "value": media.count(),
            "icon": "image",
            "color": "text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-900/20",
        },
        {
            "title": "Total Downloads",
            "value": GalleryDownloadLog.objects.count(),
            "icon": "download",
            "color": "text-amber-600 bg-amber-50 dark:text-amber-400 dark:bg-amber-900/20",
        },
        {
            "title": "Total Favorites",
            "value": GalleryFavorite.objects.count(),
            "icon": "favorite",
            "color": "text-rose-600 bg-rose-50 dark:text-rose-400 dark:bg-rose-900/20",
        },
        {
            "title": "Gallery Visits",
            "value": GalleryVisit.objects.count(),
            "icon": "visibility",
            "color": "text-indigo-600 bg-indigo-50 dark:text-indigo-400 dark:bg-indigo-900/20",
        },
    ]

    quick_actions = [
        {
            "label": "Create Event",
            "icon": "add_circle",
            "url": reverse("admin:events_event_add"),
        },
        {
            "label": "Create Gallery",
            "icon": "add_circle",
            "url": reverse("admin:gallery_clientgallery_add"),
        },
        {
            "label": "Upload Media",
            "icon": "cloud_upload",
            "url": reverse("admin:media_media_add"),
        },
        {
            "label": "Edit Homepage Hero",
            "icon": "view_carousel",
            "url": reverse("admin:cms_herosection_changelist"),
        },
        {
            "label": "Manage Workflow",
            "icon": "linear_scale",
            "url": reverse("admin:cms_workflowstep_changelist"),
        },
        {
            "label": "Manage Gallery Showcase",
            "icon": "photo_album",
            "url": reverse("admin:cms_galleryshowcase_changelist"),
        },
    ]

    context.update(
        {
            "dashboard_stats": stats,
            "dashboard_quick_actions": quick_actions,
            "dashboard_recent_galleries": galleries.order_by("-created_at")[:5],
            "dashboard_recent_events": events.order_by("-created_at")[:5],
            "dashboard_recent_downloads": (
                GalleryDownloadLog.objects.select_related("gallery", "photo")
                .order_by("-downloaded_at")[:5]
            ),
            "dashboard_recent_visits": (
                GalleryVisit.objects.select_related("gallery").order_by("-visited_at")[:5]
            ),
            "dashboard_system_overview": {
                "users": User.objects.count(),
                "active_galleries": galleries.filter(is_active=True).count(),
                "password_protected_galleries": galleries.filter(
                    access_type=ClientGallery.AccessType.PASSWORD_PROTECTED
                ).count(),
                "public_galleries": galleries.filter(
                    access_type=ClientGallery.AccessType.PUBLIC
                ).count(),
            },
        }
    )

    return context
