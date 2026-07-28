from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import ClientGallery, GalleryFavorite, GalleryDownloadLog, GalleryVisit


@admin.register(ClientGallery)
class ClientGalleryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "event",
        "access_type",
        "allow_download",
        "allow_favorites",
        "is_active",
        "display_order",
    )
    search_fields = (
        "name",
        "slug",
    )
    list_filter = (
        "access_type",
        "is_active",
        "allow_download",
        "allow_favorites",
    )
    fieldsets = (
        (_("Identity"), {
            "fields": ("name", "slug"),
        }),
        (_("Relation"), {
            "fields": ("event",),
        }),
        (_("Access"), {
            "fields": ("access_type", "gallery_password"),
        }),
        (_("Sharing"), {
            "fields": ("share_token", "expires_at"),
        }),
        (_("Options"), {
            "fields": ("allow_download", "allow_favorites"),
        }),
        (_("Status"), {
            "fields": ("is_active", "display_order"),
        }),
    )
    readonly_fields = ("share_token",)


@admin.register(GalleryVisit)
class GalleryVisitAdmin(admin.ModelAdmin):
    list_display = (
        "gallery",
        "visited_at",
        "ip_address",
    )
    search_fields = (
        "gallery__name",
        "session_id",
        "ip_address",
    )
    list_filter = (
        "gallery",
        "visited_at",
    )
    readonly_fields = (
        "gallery",
        "session_id",
        "ip_address",
        "user_agent",
        "referrer",
        "visited_at",
    )


@admin.register(GalleryFavorite)
class GalleryFavoriteAdmin(admin.ModelAdmin):
    list_display = (
        "gallery",
        "photo",
        "session_id",
        "created_at",
    )
    search_fields = (
        "gallery__name",
        "photo__title",
        "session_id",
    )
    list_filter = (
        "gallery",
        "created_at",
    )
    readonly_fields = (
        "gallery",
        "photo",
        "session_id",
        "created_at",
    )


@admin.register(GalleryDownloadLog)
class GalleryDownloadLogAdmin(admin.ModelAdmin):
    list_display = (
        "gallery",
        "photo",
        "downloaded_at",
        "ip_address",
    )
    search_fields = (
        "gallery__name",
        "photo__title",
    )
    list_filter = (
        "gallery",
        "downloaded_at",
    )
    readonly_fields = (
        "gallery",
        "photo",
        "session_id",
        "downloaded_at",
        "ip_address",
        "user_agent",
    )

