from django.contrib import admin
from django.utils.html import format_html

from apps.events.models import Client, Event, Studio


@admin.register(Studio)
class StudioAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "phone",
        "avatar_thumb",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("name", "owner__email", "owner__username", "phone")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "avatar_preview")

    fieldsets = (
        ("Studio", {"fields": ("name", "owner")}),
        ("Contact", {"fields": ("phone", "avatar", "avatar_preview")}),
        ("Status", {"fields": ("status", "created_by", "created_at", "updated_at")}),
    )

    @admin.display(description="Avatar")
    def avatar_thumb(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width:32px;height:32px;border-radius:50%;object-fit:cover;" />',
                obj.avatar.url,
            )
        return "-"

    @admin.display(description="Avatar Preview")
    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="max-width:160px;max-height:160px;border-radius:8px;object-fit:cover;" />',
                obj.avatar.url,
            )
        return "No avatar"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "cover_thumb",
        "title",
        "studio",
        "event_type",
        "status",
        "visibility",
        "event_date",
        "organizer_name",
        "created_by",
        "created_at",
    )
    list_filter = ("status", "event_type", "visibility", "studio", "event_date")
    search_fields = (
        "title",
        "slug",
        "uuid",
        "location",
        "organizer_name",
        "organizer_contact",
        "description",
        "studio__name",
    )
    ordering = ("-created_at",)
    readonly_fields = ("uuid", "slug", "created_at", "updated_at", "cover_preview")

    fieldsets = (
        ("Identity", {"fields": ("title", "slug", "uuid", "studio")}),
        ("Details", {
            "fields": (
                "description",
                "cover_image",
                "cover_preview",
                "event_date",
                "event_time",
                "location",
            )
        }),
        ("Organizer", {"fields": ("organizer_name", "organizer_contact")}),
        ("Configuration", {
            "fields": (
                "event_type",
                "visibility",
                "password",
                "status",
                "gallery_expiry_date",
                "allow_download",
                "show_watermark",
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


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "event",
        "email",
        "phone",
        "status",
        "created_at",
    )
    list_filter = ("status", "event", "created_at")
    search_fields = ("name", "email", "phone", "event__title")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
