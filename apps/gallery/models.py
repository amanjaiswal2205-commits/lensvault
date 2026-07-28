import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.cms.models import BaseCMSModel
from apps.events.models import Event
from apps.media.models import Media


class ClientGallery(BaseCMSModel):
    class AccessType(models.TextChoices):
        PUBLIC = "public", _("Public")
        PASSWORD_PROTECTED = "password_protected", _("Password Protected")
        PRIVATE = "private", _("Private")

    name = models.CharField(
        _("name"),
        max_length=255,
        help_text=_("Name of the client gallery."),
    )
    slug = models.SlugField(
        _("slug"),
        max_length=280,
        unique=True,
        help_text=_("URL-friendly identifier for this gallery."),
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="client_galleries",
        verbose_name=_("event"),
        help_text=_("The event this gallery belongs to."),
    )
    access_type = models.CharField(
        _("access type"),
        max_length=20,
        choices=AccessType.choices,
        default=AccessType.PRIVATE,
        help_text=_("Who can access this gallery."),
    )
    gallery_password = models.CharField(
        _("gallery password"),
        max_length=128,
        blank=True,
        help_text=_("Password required to access this gallery. Leave empty for public or private access."),
    )
    share_token = models.UUIDField(
        _("share token"),
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text=_("Unique token for sharing the gallery link."),
    )
    expires_at = models.DateTimeField(
        _("expires at"),
        null=True,
        blank=True,
        help_text=_("Optional expiration date for the gallery."),
    )
    allow_download = models.BooleanField(
        _("allow download"),
        default=True,
        help_text=_("Allow users to download photos from this gallery."),
    )
    allow_favorites = models.BooleanField(
        _("allow favorites"),
        default=True,
        help_text=_("Allow users to mark photos as favorites."),
    )

    class Meta(BaseCMSModel.Meta):
        verbose_name = _("client gallery")
        verbose_name_plural = _("client galleries")
        ordering = ["display_order", "-pk"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)[:240]
            slug = base_slug
            counter = 2
            while ClientGallery.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("gallery:gallery_manage_detail", kwargs={"slug": self.slug})

    def set_password(self, raw_password):
        from django.contrib.auth.hashers import make_password
        self.gallery_password = make_password(raw_password)

    def check_password(self, raw_password):
        from django.contrib.auth.hashers import check_password
        if not self.gallery_password:
            return False
        return check_password(raw_password, self.gallery_password)

    @property
    def visit_count(self):
        return self.visits.count()

    @property
    def favorite_count(self):
        return self.favorites.count()

    @property
    def download_count(self):
        return self.download_logs.count()

    def clean(self):
        if self.access_type == self.AccessType.PASSWORD_PROTECTED and not self.gallery_password:
            raise ValidationError({"gallery_password": _("Gallery password is required for password-protected galleries.")})


class GalleryVisit(models.Model):
    gallery = models.ForeignKey(
        ClientGallery,
        on_delete=models.CASCADE,
        related_name="visits",
        verbose_name=_("gallery"),
    )
    session_id = models.CharField(
        _("session id"),
        max_length=128,
    )
    ip_address = models.GenericIPAddressField(_("ip address"))
    user_agent = models.TextField(_("user agent"))
    referrer = models.URLField(_("referrer"), blank=True)
    visited_at = models.DateTimeField(_("visited at"), auto_now_add=True)

    class Meta:
        verbose_name = _("gallery visit")
        verbose_name_plural = _("gallery visits")
        ordering = ["-visited_at"]

    def __str__(self):
        return f"{self.session_id} → {self.gallery.name} ({self.visited_at})"


class GalleryFavorite(models.Model):
    gallery = models.ForeignKey(
        ClientGallery,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name=_("gallery"),
    )
    photo = models.ForeignKey(
        Media,
        on_delete=models.CASCADE,
        related_name="gallery_favorites",
        verbose_name=_("photo"),
    )
    session_id = models.CharField(
        _("session id"),
        max_length=128,
        help_text=_("Session identifier for the user who favorited this photo."),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("gallery favorite")
        verbose_name_plural = _("gallery favorites")
        ordering = ["-created_at"]
        unique_together = ["gallery", "photo", "session_id"]

    def __str__(self):
        return f"{self.session_id} → {self.photo.title} ({self.gallery.name})"


class GalleryDownloadLog(models.Model):
    gallery = models.ForeignKey(
        ClientGallery,
        on_delete=models.CASCADE,
        related_name="download_logs",
        verbose_name=_("gallery"),
    )
    photo = models.ForeignKey(
        Media,
        on_delete=models.CASCADE,
        related_name="download_logs",
        verbose_name=_("photo"),
    )
    session_id = models.CharField(
        _("session id"),
        max_length=128,
    )
    downloaded_at = models.DateTimeField(_("downloaded at"), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_("ip address"))
    user_agent = models.TextField(_("user agent"))

    class Meta:
        verbose_name = _("gallery download log")
        verbose_name_plural = _("gallery download logs")
        ordering = ["-downloaded_at"]

    def __str__(self):
        return f"{self.gallery.name} — {self.photo.title}"
