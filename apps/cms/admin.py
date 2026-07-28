from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from .models import (
    SiteSettings,
    HeroSection,
    Feature,
    SEOSettings,
    MediaAsset,
    ThemeSettings,
    WorkflowSection,
    WorkflowStep,
    TrustSection,
    TrustItem,
    CTASection,
    GalleryShowcase,
)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "site_name",
        "support_email",
        "phone",
        "is_active",
    )
    search_fields = (
        "site_name",
        "support_email",
        "phone",
    )
    list_filter = ("is_active",)
    actions = ["restore_lensvault_defaults"]

    def has_add_permission(self, request):
        if SiteSettings.objects.exists():
            return False
        return super().has_add_permission(request)

    def save_model(self, request, obj, form, change):
        if obj.is_active:
            SiteSettings.objects.filter(is_active=True).exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)
        messages.success(request, _("Site settings saved successfully."))

    def delete_model(self, request, obj):
        if SiteSettings.objects.count() == 1:
            messages.error(request, _("Cannot delete the only SiteSettings record. Edit it instead."))
            return
        super().delete_model(request, obj)
        messages.success(request, _("Site settings deleted successfully."))

    @admin.action(description=_("Restore selected Site Settings to LensVault defaults"))
    def restore_lensvault_defaults(self, request, queryset):
        defaults = {
            "site_name": "LensVault",
            "site_tagline": "",
            "site_description": "",
            "support_email": "",
            "phone": "",
            "address": "",
            "facebook_url": "",
            "instagram_url": "",
            "youtube_url": "",
            "linkedin_url": "",
        }
        updated = 0
        for settings in queryset:
            for field, value in defaults.items():
                setattr(settings, field, value)
            settings.save()
            updated += 1
        self.message_user(request, _("%(count)s site settings record(s) restored to LensVault defaults.") % {"count": updated})


@admin.register(HeroSection)
class HeroSectionAdmin(admin.ModelAdmin):
    list_display = (
        "heading",
        "badge_text",
        "is_active",
        "display_order",
    )
    search_fields = (
        "heading",
        "badge_text",
        "subtitle",
    )
    list_filter = ("is_active",)
    fieldsets = (
        (_("Content"), {
            "fields": ("badge_text", "heading", "subtitle", "rotating_words"),
        }),
        (_("Buttons"), {
            "fields": (
                "primary_button_text",
                "primary_button_url",
                "secondary_button_text",
                "secondary_button_url",
            ),
        }),
        (_("Media"), {
            "fields": ("hero_image", "background_image"),
        }),
        (_("Statistics"), {
            "fields": (
                "stat_1_number",
                "stat_1_label",
                "stat_2_number",
                "stat_2_label",
                "stat_3_number",
                "stat_3_label",
            ),
        }),
        (_("Status"), {
            "fields": ("is_active", "display_order"),
        }),
    )
    actions = ["restore_lensvault_defaults"]

    @admin.action(description=_("Restore selected Hero to LensVault defaults"))
    def restore_lensvault_defaults(self, request, queryset):
        defaults = {
            "badge_text": "The Modern Client Gallery",
            "heading": "Turn Every Moment Into<br>A Gallery That's",
            "subtitle": "Create beautiful client galleries, organize every event, and deliver unforgettable photographs through one elegant workspace.",
            "rotating_words": "Timeless.",
            "primary_button_text": "Start Creating",
            "primary_button_url": "/accounts/register/",
            "secondary_button_text": "Explore Gallery",
            "secondary_button_url": "/gallery/",
        }
        updated = 0
        for hero in queryset:
            for field, value in defaults.items():
                setattr(hero, field, value)
            hero.save()
            updated += 1
        self.message_user(request, _("%(count)s hero section(s) restored to LensVault defaults.") % {"count": updated})

    def has_add_permission(self, request):
        return super().has_add_permission(request)

    def save_model(self, request, obj, form, change):
        if obj.is_active:
            HeroSection.objects.filter(is_active=True).exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)
        if obj.is_active:
            messages.success(request, _("Hero activated successfully."))
        else:
            messages.success(request, _("Hero saved."))

    def delete_model(self, request, obj):
        was_active = obj.is_active
        super().delete_model(request, obj)
        if was_active:
            remaining = HeroSection.objects.filter(is_active=True).first()
            if remaining:
                messages.warning(request, _("Active hero deleted. '%(heading)s' has been activated.") % {"heading": remaining.heading})
            else:
                messages.warning(request, _("Active hero deleted. Frontend will use LensVault fallback content."))
        else:
            messages.success(request, _("Hero deleted successfully."))

    def delete_queryset(self, request, queryset):
        active_heroes = list(queryset.filter(is_active=True))
        super().delete_queryset(request, queryset)
        if active_heroes:
            remaining = HeroSection.objects.filter(is_active=True).first()
            if remaining:
                messages.warning(request, _("%(count)d active heroes deleted. '%(heading)s' has been activated.") % {"count": len(active_heroes), "heading": remaining.heading})
            else:
                messages.warning(request, _("%(count)d active heroes deleted. Frontend will use LensVault fallback content.") % {"count": len(active_heroes)})


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "display_order",
        "is_active",
        "is_featured",
    )
    search_fields = (
        "title",
        "description",
    )
    list_filter = (
        "is_active",
        "is_featured",
    )
    fieldsets = (
        (_("Content"), {
            "fields": ("title", "description", "icon"),
        }),
        (_("Style"), {
            "fields": ("icon_background", "accent_color"),
        }),
        (_("Display"), {
            "fields": ("display_order", "is_active", "is_featured"),
        }),
        (_("Call to Action"), {
            "fields": ("link", "button_text"),
        }),
    )


@admin.register(WorkflowSection)
class WorkflowSectionAdmin(admin.ModelAdmin):
    list_display = (
        "heading",
        "eyebrow",
        "is_active",
        "display_order",
    )
    search_fields = (
        "heading",
        "eyebrow",
        "subtitle",
    )
    list_filter = ("is_active",)
    fieldsets = (
        (_("Content"), {
            "fields": ("eyebrow", "heading", "subtitle"),
        }),
        (_("Status"), {
            "fields": ("is_active", "display_order"),
        }),
    )


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "display_order",
        "is_active",
    )
    search_fields = (
        "title",
        "description",
    )
    list_filter = ("is_active",)
    fieldsets = (
        (_("Content"), {
            "fields": ("title", "description", "icon"),
        }),
        (_("Display"), {
            "fields": ("display_order", "is_active"),
        }),
    )


class TrustItemInline(admin.TabularInline):
    model = TrustItem
    extra = 4
    fields = (
        "title",
        "description",
        "badge",
        "icon",
        "display_order",
        "is_active",
    )
    ordering = ("display_order", "-pk")


@admin.register(TrustSection)
class TrustSectionAdmin(admin.ModelAdmin):
    list_display = (
        "heading",
        "eyebrow",
        "is_active",
        "display_order",
    )
    search_fields = (
        "heading",
        "eyebrow",
        "subtitle",
    )
    list_filter = ("is_active",)
    inlines = [TrustItemInline]
    fieldsets = (
        (_("Content"), {
            "fields": ("eyebrow", "heading", "subtitle", "hub_label"),
        }),
        (_("Status"), {
            "fields": ("is_active", "display_order"),
        }),
    )


@admin.register(CTASection)
class CTASectionAdmin(admin.ModelAdmin):
    list_display = (
        "heading",
        "primary_button_text",
        "is_active",
        "display_order",
    )
    search_fields = (
        "heading",
        "description",
    )
    list_filter = ("is_active",)
    fieldsets = (
        (_("Content"), {
            "fields": ("heading", "description"),
        }),
        (_("Buttons"), {
            "fields": (
                "primary_button_text",
                "primary_button_url",
                "secondary_button_text",
                "secondary_button_url",
            ),
        }),
        (_("Status"), {
            "fields": ("is_active", "display_order"),
        }),
    )


@admin.register(GalleryShowcase)
class GalleryShowcaseAdmin(admin.ModelAdmin):
    list_display = (
        "heading",
        "eyebrow",
        "featured_gallery",
        "is_active",
        "display_order",
    )
    search_fields = (
        "heading",
        "eyebrow",
        "subtitle",
    )
    list_filter = ("is_active",)
    filter_horizontal = ("selected_galleries",)
    fieldsets = (
        (_("Content"), {
            "fields": ("eyebrow", "heading", "subtitle"),
        }),
        (_("Galleries"), {
            "fields": ("featured_gallery", "selected_galleries"),
        }),
        (_("Status"), {
            "fields": ("is_active", "display_order"),
        }),
    )


@admin.register(SEOSettings)
class SEOSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "page_key",
        "meta_title",
        "is_active",
        "display_order",
    )
    search_fields = (
        "page_key",
        "meta_title",
        "meta_description",
    )
    list_filter = ("is_active",)
    fieldsets = (
        (_("Page"), {
            "fields": ("page_key",),
        }),
        (_("SEO"), {
            "fields": ("meta_title", "meta_description", "meta_keywords"),
        }),
        (_("Social"), {
            "fields": ("og_title", "og_description", "og_image"),
        }),
        (_("Technical"), {
            "fields": ("canonical_url", "robots"),
        }),
        (_("Status"), {
            "fields": ("is_active", "display_order"),
        }),
    )

    def save_model(self, request, obj, form, change):
        if obj.is_active:
            SEOSettings.objects.filter(page_key=obj.page_key, is_active=True).exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)
        messages.success(request, _("SEO settings saved successfully."))

    def delete_model(self, request, obj):
        if SEOSettings.objects.filter(page_key=obj.page_key, is_active=True).count() == 1 and obj.is_active:
            messages.warning(request, _("Deleted the active SEO settings for '%(page_key)s'. Frontend will use fallback SEO.") % {"page_key": obj.page_key})
        super().delete_model(request, obj)
        messages.success(request, _("SEO settings deleted successfully."))


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "media_type",
        "category",
        "is_active",
        "display_order",
    )
    search_fields = (
        "title",
        "tags",
    )
    list_filter = (
        "media_type",
        "category",
        "is_active",
    )
    fieldsets = (
        (_("File"), {
            "fields": ("title", "file", "alt_text"),
        }),
        (_("Classification"), {
            "fields": ("media_type", "category", "tags"),
        }),
        (_("Status"), {
            "fields": ("is_public", "is_active", "display_order"),
        }),
    )
    readonly_fields = ("preview_thumbnail",)

    def preview_thumbnail(self, obj):
        if obj.media_type == "image" and obj.file:
            return format_html(
                '<img src="{}" style="max-height: 160px; max-width: 100%; border-radius: 8px;" />',
                obj.file.url,
            )
        return "-"
    preview_thumbnail.short_description = _("Preview")


@admin.register(ThemeSettings)
class ThemeSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "theme_name",
        "primary_color",
        "is_active",
        "is_default",
        "display_order",
    )
    search_fields = (
        "theme_name",
    )
    list_filter = (
        "is_default",
        "is_active",
    )
    fieldsets = (
        (_("Branding"), {
            "fields": ("theme_name", "primary_color", "secondary_color", "accent_color"),
        }),
        (_("Typography"), {
            "fields": ("font_family", "heading_font", "body_font"),
        }),
        (_("Buttons"), {
            "fields": ("border_radius", "button_style"),
        }),
        (_("Layout"), {
            "fields": ("container_width", "card_shadow", "glass_effect_enabled"),
        }),
        (_("Status"), {
            "fields": ("is_active", "is_default", "display_order"),
        }),
    )

    def save_model(self, request, obj, form, change):
        if obj.is_default:
            ThemeSettings.objects.filter(is_default=True).exclude(pk=obj.pk).update(is_default=False)
        super().save_model(request, obj, form, change)
        messages.success(request, _("Theme settings saved successfully."))

    def delete_model(self, request, obj):
        if ThemeSettings.objects.filter(is_default=True).count() == 1 and obj.is_default:
            messages.warning(request, _("Deleted the default theme. Please set another theme as default."))
        super().delete_model(request, obj)
        messages.success(request, _("Theme settings deleted successfully."))
