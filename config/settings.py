"""
Django settings for the LensVault project.

Generated base configuration: PostgreSQL, environment variables, static/media,
WhiteNoise, Tailwind CSS, custom User model and authentication.
"""

from pathlib import Path

import os

import dj_database_url
from dotenv import load_dotenv

load_dotenv()


def env_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).lower() in ("1", "true", "yes", "on")


# Build paths inside the project like this: BASE_DIR / "subdir".
BASE_DIR = Path(__file__).resolve().parent.parent

# Application definition
SITE_NAME = os.getenv("SITE_NAME", "LensVault")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "insecure-development-key")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_bool("DJANGO_DEBUG", True)

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if h.strip()
]

INSTALLED_APPS = [
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_tailwind_cli",
    "whitenoise.runserver_nostatic",
    # Local apps
    "apps.accounts",
    "apps.dashboard",
    "apps.events",
    "apps.albums",
    "apps.media",
    "apps.uploads",
    "apps.qr",
    "apps.gallery",
    "apps.downloads",
    "apps.analytics",
    "apps.core",
    "apps.cms",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.accounts.middleware.DashboardAccessMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
                "apps.core.context_processors.site_name",
                "apps.core.context_processors.site_settings",
                "apps.core.context_processors.seo_settings",
                "apps.core.context_processors.theme_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
# Use SQLite for local development when USE_SQLITE=True.
# Otherwise the existing PostgreSQL configuration is used (production default).
if env_bool("USE_SQLITE", False):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": dj_database_url.config(
            conn_max_age=600,
            ssl_require=True,
        )
    }

# Authentication
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LOGIN_REDIRECT_URL = "dashboard:index"
LOGOUT_REDIRECT_URL = "core:home"
LOGIN_URL = "accounts:login"

# Email
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@lensvault.com")
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static" / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Media files (user uploads)
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Tailwind CSS
TAILWIND_APP_STATIC_DIR = BASE_DIR / "static" / "css"
NPM_BIN_DIR = BASE_DIR / "node_modules" / ".bin"

# WhiteNoise (production static file serving)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

UNFOLD = {
    "SITE_TITLE": "LensVault Admin",
    "SITE_HEADER": "LensVault Studio",
    "SITE_SUBTITLE": "Photography Management Platform",
    "SITE_URL": "/",
    "SITE_ICON": "camera",
    "COLORS": {
        "primary": {
            "50": "#EDE9FE",
            "100": "#DDD6FE",
            "200": "#C4B5FD",
            "300": "#A78BFA",
            "400": "#8B5CF6",
            "500": "#7C3AED",
            "600": "#6D28D9",
            "700": "#5B21B6",
            "800": "#4C1D95",
            "900": "#3B0764",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
    },
    "TABS": [],
    "ENVIRONMENT": "env",
    "ENVIRONMENT_NAME": "Environment",
    "BREADCRUMBS": {
        "show_all": True,
    },
    "navigation": [
        {
            "label": "Photography",
            "items": [
                {"model": "events.Event", "icon": "calendar_today", "label": "Events"},
                {"model": "albums.Album", "icon": "photo_library", "label": "Albums"},
                {"model": "gallery.ClientGallery", "icon": "collections", "label": "Galleries"},
                {"model": "media.Media", "icon": "image", "label": "Photos"},
            ],
        },
        {
            "label": "CMS",
            "items": [
                {"model": "cms.HeroSection", "icon": "view_carousel", "label": "Hero Sections"},
                {"model": "cms.Feature", "icon": "stars", "label": "Features"},
                {"model": "cms.WorkflowStep", "icon": "linear_scale", "label": "Workflow"},
                {"model": "cms.TrustSection", "icon": "verified_user", "label": "Trust Section"},
                {"model": "cms.CTASection", "icon": "campaign", "label": "CTA"},
                {"model": "cms.GalleryShowcase", "icon": "photo_album", "label": "Gallery Showcase"},
                {"model": "cms.MediaAsset", "icon": "perm_media", "label": "Media Library"},
                {"model": "cms.SEOSettings", "icon": "search", "label": "SEO Settings"},
                {"model": "cms.ThemeSettings", "icon": "palette", "label": "Theme Settings"},
            ],
        },
        {
            "label": "Analytics",
            "items": [
                {"model": "gallery.GalleryVisit", "icon": "visibility", "label": "Gallery Visits"},
                {"model": "gallery.GalleryDownloadLog", "icon": "download", "label": "Downloads"},
                {"model": "gallery.GalleryFavorite", "icon": "favorite", "label": "Favorites"},
            ],
        },
        {
            "label": "Accounts",
            "items": [
                {"model": "accounts.User", "icon": "person", "label": "Users"},
                {"model": "accounts.Staff", "icon": "badge", "label": "Staff"},
                {"model": "auth.Group", "icon": "group", "label": "Groups"},
            ],
        },
        {
            "label": "System",
            "items": [
                {"model": "cms.SiteSettings", "icon": "settings", "label": "Site Settings"},
            ],
        },
    ],
    "DASHBOARD_CALLBACK": "config.dashboard.dashboard_callback",
}
