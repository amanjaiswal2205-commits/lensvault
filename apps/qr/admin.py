from django.contrib import admin
from django.utils.html import format_html

from apps.qr.models import QRCode


@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = (
        "qr_thumb",
        "event",
        "is_active",
        "scan_count",
        "last_scanned_at",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_active", "created_at", "updated_at")
    search_fields = ("event__title", "event__slug", "token", "uuid")
    ordering = ("-created_at",)
    readonly_fields = (
        "uuid",
        "token",
        "scan_count",
        "last_scanned_at",
        "created_at",
        "updated_at",
        "qr_preview",
    )

    fieldsets = (
        ("Identity", {"fields": ("event", "uuid", "token", "qr_preview")}),
        ("Image", {"fields": ("qr_image",)}),
        ("Status & Stats", {"fields": ("is_active", "scan_count", "last_scanned_at")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="QR")
    def qr_thumb(self, obj):
        if obj.qr_image:
            return format_html(
                '<img src="{}" style="width:48px;height:48px;border-radius:6px;object-fit:cover;" />',
                obj.qr_image.url,
            )
        return "—"

    @admin.display(description="QR Preview")
    def qr_preview(self, obj):
        if obj.qr_image:
            return format_html(
                '<img src="{}" style="max-width:200px;max-height:200px;border-radius:8px;object-fit:cover;" />',
                obj.qr_image.url,
            )
        return "No QR image"
