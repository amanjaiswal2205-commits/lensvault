from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class MediaType(models.TextChoices):
    IMAGE = "image", _("Image")
    VIDEO = "video", _("Video")


class MediaStatus(models.TextChoices):
    ACTIVE = "active", _("Active")
    HIDDEN = "hidden", _("Hidden")


IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
VIDEO_EXTENSIONS = ["mp4", "mov", "avi", "mkv"]
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS + VIDEO_EXTENSIONS

MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20 MB
MAX_VIDEO_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB


def media_file_upload_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    folder = "videos" if instance.media_type == MediaType.VIDEO else "images"
    return f"events/{instance.event.uuid}/albums/{instance.album.uuid}/media/{instance.uuid}.{ext}"


def media_thumbnail_upload_path(instance, filename):
    return f"events/{instance.event.uuid}/albums/{instance.album.uuid}/media/{instance.uuid}_thumb.jpg"


class Media(models.Model):
    uuid = models.UUIDField(_("uuid"), unique=True, editable=False)
    album = models.ForeignKey(
        "albums.Album",
        on_delete=models.CASCADE,
        related_name="media",
        verbose_name=_("album"),
    )
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="media",
        verbose_name=_("event"),
    )
    title = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    file = models.FileField(_("file"), upload_to=media_file_upload_path, max_length=500)
    thumbnail = models.ImageField(
        _("thumbnail"), upload_to=media_thumbnail_upload_path, blank=True, null=True, max_length=500
    )
    media_type = models.CharField(
        _("media type"), max_length=10, choices=MediaType.choices, default=MediaType.IMAGE
    )
    file_size = models.BigIntegerField(_("file size"), default=0, editable=False)
    width = models.PositiveIntegerField(_("width"), null=True, blank=True)
    height = models.PositiveIntegerField(_("height"), null=True, blank=True)
    duration = models.PositiveIntegerField(
        _("duration (seconds)"), null=True, blank=True,
        help_text=_("Video duration in seconds."),
    )
    mime_type = models.CharField(_("mime type"), max_length=100, blank=True)
    download_count = models.PositiveIntegerField(_("download count"), default=0, editable=False)
    view_count = models.PositiveIntegerField(_("view count"), default=0, editable=False)
    is_featured = models.BooleanField(_("is featured"), default=False)
    status = models.CharField(
        _("status"), max_length=20, choices=MediaStatus.choices, default=MediaStatus.ACTIVE
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="media",
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("media")
        verbose_name_plural = _("media")
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("media:media_detail", kwargs={"uuid": str(self.uuid)})

    def save(self, *args, **kwargs):
        if not self.uuid:
            import uuid as uuid_lib

            self.uuid = uuid_lib.uuid4()
        if not self.event_id and self.album_id:
            self.event = self.album.event
        if self.file and hasattr(self.file, "size"):
            self.file_size = self.file.size
            if self.file.name:
                ext = self.file.name.rsplit(".", 1)[-1].lower()
                if ext in IMAGE_EXTENSIONS:
                    self.media_type = MediaType.IMAGE
                elif ext in VIDEO_EXTENSIONS:
                    self.media_type = MediaType.VIDEO
        super().save(*args, **kwargs)

    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2) if self.file_size else 0

    @property
    def is_image(self):
        return self.media_type == MediaType.IMAGE

    @property
    def is_video(self):
        return self.media_type == MediaType.VIDEO
