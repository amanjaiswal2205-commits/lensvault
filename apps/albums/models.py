from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class AlbumStatus(models.TextChoices):
    ACTIVE = "active", _("Active")
    HIDDEN = "hidden", _("Hidden")


def album_cover_upload_path(instance, filename):
    return f"covers/albums/{instance.uuid}/{filename}"


class Album(models.Model):
    uuid = models.UUIDField(_("uuid"), unique=True, editable=False)
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="albums",
        verbose_name=_("event"),
    )
    title = models.CharField(_("album title"), max_length=255)
    slug = models.SlugField(_("slug"), max_length=280, blank=True)
    description = models.TextField(_("description"), blank=True)
    cover_image = models.ImageField(
        _("cover image"), upload_to=album_cover_upload_path, blank=True, null=True, max_length=500
    )
    album_order = models.PositiveIntegerField(_("album order"), default=0, blank=True)
    is_featured = models.BooleanField(_("is featured"), default=False)
    status = models.CharField(
        _("status"), max_length=20, choices=AlbumStatus.choices, default=AlbumStatus.ACTIVE
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="albums",
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("album")
        verbose_name_plural = _("albums")
        ordering = ["album_order", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "title"],
                name="unique_album_title_per_event",
            ),
            models.UniqueConstraint(
                fields=["event", "slug"],
                name="unique_album_slug_per_event",
            ),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("albums:album_detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.uuid:
            import uuid

            self.uuid = uuid.uuid4()
        if not self.slug:
            base = slugify(self.title)[:270]
            slug = base
            counter = 1
            qs = Album.objects.filter(event=self.event)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            while qs.filter(slug=slug).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
