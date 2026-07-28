from django.contrib import admin
from django.utils.html import format_html

from apps.albums.models import Album


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = (
        "cover_thumb",
        "title",
        "event",
        "album_order",
        "is_featured",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = ("status", "is_featured", "event", "created_at")
    search_fields = ("title", "slug", "uuid", "description", "event__title")
    ordering = ("album_order", "-created_at")
    readonly_fields = ("uuid", "slug", "created_at", "updated_at", "cover_preview")

    fieldsets = (
        ("Identity", {"fields": ("title", "slug", "uuid", "event")}),
        ("Details", {
            "fields": (
                "description",
                "cover_image",
                "cover_preview",
                "album_order",
                "is_featured",
                "status",
            )
        }),
        ("Ownership", {"fields": ("created_by", "created_at", "updated_at")}),
    )

    @admin.display(description="Cover")
    def cover_thumb(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="width:48px;height:36px;border-radius:6px;object-fit:cover;" />',
                obj.cover_image.url,
            )
        return "-"

    @admin.display(description="Cover Preview")
    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-width:320px;max-height:200px;border-radius:8px;object-fit:cover;" />',
                obj.cover_image.url,
            )
        return "No cover image"
