import secrets

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def generate_secure_token():
    """Cryptographically secure, non-sequential, URL-safe token."""
    return secrets.token_urlsafe(32)


def qr_image_upload_path(instance, filename):
    return f"qr/{instance.uuid}/qr.png"


class QRCode(models.Model):
    uuid = models.UUIDField(_("uuid"), unique=True, editable=False)
    event = models.OneToOneField(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="qr_code",
        verbose_name=_("event"),
    )
    token = models.CharField(
        _("secure token"), max_length=64, unique=True, editable=False,
        default=generate_secure_token,
    )
    qr_image = models.ImageField(
        _("qr image"), upload_to=qr_image_upload_path, blank=True, null=True
    )
    is_active = models.BooleanField(_("is active"), default=True)
    scan_count = models.PositiveIntegerField(_("scan count"), default=0, editable=False)
    last_scanned_at = models.DateTimeField(_("last scanned at"), null=True, blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("qr code")
        verbose_name_plural = _("qr codes")
        ordering = ["-created_at"]

    def __str__(self):
        return f"QR · {self.event.title}"

    def save(self, *args, **kwargs):
        if not self.uuid:
            import uuid as uuid_lib

            self.uuid = uuid_lib.uuid4()
        super().save(*args, **kwargs)

    @property
    def access_path(self):
        return f"/access/{self.token}/"

    def get_access_url(self, request=None):
        path = self.access_path
        if request is not None:
            return request.build_absolute_uri(path)
        return path

    def gallery_redirect_url(self):
        return reverse("gallery:event_gallery_detail", kwargs={"event_slug": self.event.slug})
