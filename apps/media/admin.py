from django.contrib import admin
from django.utils.html import format_html

from apps.media.models import Media


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = (
        "thumbnail_preview",
        "title",
        "album",
        "event",
        "media_type",
        "status",
        "is_featured",
        "file_size_admin",
        "view_count",
        "download_count",
        "uploaded_by",
        "created_at",
    )
    list_filter = ("media_type", "status", "is_featured", "event", "album", "created_at")
    search_fields = ("title", "description", "uuid", "album__title", "event__title")
    ordering = ("-created_at",)
    readonly_fields = (
        "uuid",
        "file_size",
        "view_count",
        "download_count",
        "created_at",
        "updated_at",
        "thumbnail_preview",
    )

    fieldsets = (
        ("Identity", {"fields": ("title", "uuid", "album", "event")}),
        ("Content", {
            "fields": (
                "description",
                "file",
                "thumbnail",
                "thumbnail_preview",
                "media_type",
                "mime_type",
            )
        }),
        ("Metadata", {
            "fields": ("file_size", "width", "height", "duration")
        }),
        ("Flags & Stats", {
            "fields": ("is_featured", "status", "view_count", "download_count")
        }),
        ("Ownership", {"fields": ("uploaded_by", "created_at", "updated_at")}),
    )

    @admin.display(description="Thumbnail")
    def thumbnail_preview(self, obj):
        img = obj.thumbnail or (obj.file if obj.is_image else None)
        if img:
            return format_html(
                '<img src="{}" style="width:48px;height:36px;border-radius:6px;object-fit:cover;" />',
                img.url,
            )
        return "—"

    @admin.display(description="File Size")
    def file_size_admin(self, obj):
        return f"{obj.file_size_mb} MB" if obj.file_size else "—"
