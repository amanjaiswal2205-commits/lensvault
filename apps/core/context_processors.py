from django.conf import settings

from apps.cms.models import SEOSettings, SiteSettings, ThemeSettings


def site_name(request):
    return {"SITE_NAME": getattr(settings, "SITE_NAME", "LensVault")}


def site_settings(request):
    return {
        "site_settings": SiteSettings.objects.filter(is_active=True).first(),
    }


def seo_settings(request):
    page_key = None
    resolver_match = getattr(request, "resolver_match", None)
    if resolver_match:
        page_key = getattr(resolver_match, "url_name", None)
    if not page_key:
        return {"seo_settings": None}
    return {
        "seo_settings": SEOSettings.objects.filter(page_key=page_key, is_active=True).first(),
    }


def theme_settings(request):
    active_theme = ThemeSettings.objects.filter(is_active=True).first()
    if not active_theme:
        active_theme = ThemeSettings.objects.filter(is_default=True).first()
    return {
        "theme_settings": active_theme,
    }
