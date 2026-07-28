from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from apps.accounts.forms import CustomUserChangeForm, CustomUserCreationForm
from apps.accounts.models import Staff, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = (
        "email",
        "username",
        "profile_thumb",
        "full_name_display",
        "role",
        "account_type",
        "is_verified",
        "is_staff",
        "is_active",
        "last_login",
        "date_joined",
    )
    list_display_links = ("email", "username")
    list_filter = (
        "role",
        "account_type",
        "is_verified",
        "is_staff",
        "is_active",
        "gender",
        "date_joined",
    )
    search_fields = (
        "email",
        "username",
        "full_name",
        "mobile_number",
        "city",
        "country",
    )
    ordering = ("-date_joined",)
    readonly_fields = ("last_login", "date_joined", "profile_preview")

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Profile", {
            "fields": (
                "profile_preview",
                "full_name",
                "profile_photo",
                "mobile_number",
                "date_of_birth",
                "gender",
                "bio",
            )
        }),
        ("Address", {"fields": ("address", "city", "state", "country", "pincode")}),
        ("Account", {
            "fields": ("role", "account_type", "is_verified", "is_active", "is_staff", "is_superuser")
        }),
        ("Permissions", {
            "fields": ("groups", "user_permissions")
        }),
        ("Important dates", {
            "fields": ("last_login", "date_joined")
        }),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "role", "account_type", "password1", "password2"),
        }),
    )

    @admin.display(description="Full Name", ordering="full_name")
    def full_name_display(self, obj):
        return obj.display_name

    @admin.display(description="Photo")
    def profile_thumb(self, obj):
        if obj.profile_photo:
            return format_html(
                '<img src="{}" style="width:32px;height:32px;border-radius:50%;object-fit:cover;" />',
                obj.profile_photo.url,
            )
        return "-"

    @admin.display(description="Profile Preview")
    def profile_preview(self, obj):
        if obj.profile_photo:
            return format_html(
                '<img src="{}" style="max-width:160px;max-height:160px;border-radius:8px;object-fit:cover;" />',
                obj.profile_photo.url,
            )
        return "No photo uploaded"


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "studio",
        "permissions_list",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "studio", "created_at")
    search_fields = (
        "user__email",
        "user__username",
        "user__full_name",
        "studio__name",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "permissions_list")

    fieldsets = (
        ("Assignment", {"fields": ("user", "studio")}),
        ("Permissions", {"fields": ("permissions", "permissions_list")}),
        ("Status", {"fields": ("is_active", "created_at", "updated_at")}),
    )

    @admin.display(description="Permissions")
    def permissions_list(self, obj):
        return ", ".join(obj.permissions) if obj.permissions else "—"
