from django.conf import settings
from django.contrib.auth.hashers import identify_hasher, make_password
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class EventType(models.TextChoices):
    WEDDING = "wedding", _("Wedding")
    BIRTHDAY = "birthday", _("Birthday")
    COLLEGE = "college", _("College")
    TRAINING = "training", _("Training")
    CORPORATE = "corporate", _("Corporate")
    FESTIVAL = "festival", _("Festival")
    OTHER = "other", _("Other")


class EventVisibility(models.TextChoices):
    PUBLIC = "public", _("Public")
    PRIVATE = "private", _("Private")
    PASSWORD_PROTECTED = "password_protected", _("Password Protected")


class EventStatus(models.TextChoices):
    DRAFT = "draft", _("Draft")
    PUBLISHED = "published", _("Published")
    ARCHIVED = "archived", _("Archived")


def event_cover_upload_path(instance, filename):
    return f"covers/events/{instance.uuid}/{filename}"


class Studio(models.Model):
    name = models.CharField(_("studio name"), max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_studios",
        verbose_name=_("owner"),
        limit_choices_to={"role": "studio_owner"},
    )
    phone = models.CharField(_("phone"), max_length=20, blank=True)
    avatar = models.ImageField(
        _("avatar"), upload_to="studios/avatars/", blank=True, null=True
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=[("active", _("Active")), ("inactive", _("Inactive"))],
        default="active",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_studios",
        verbose_name=_("created by"),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("studio")
        verbose_name_plural = _("studios")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name"],
                name="unique_studio_name_per_owner",
            )
        ]

    def __str__(self):
        return self.name


class Event(models.Model):
    uuid = models.UUIDField(_("uuid"), unique=True, editable=False)
    studio = models.ForeignKey(
        "events.Studio",
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name=_("studio"),
        null=True,
        blank=True,
    )
    title = models.CharField(_("event title"), max_length=255, unique=True)
    slug = models.SlugField(_("slug"), max_length=280, unique=True, blank=True)
    description = models.TextField(_("description"), blank=True)
    cover_image = models.ImageField(
        _("cover image"), upload_to=event_cover_upload_path, blank=True, null=True, max_length=500
    )
    event_date = models.DateField(_("event date"))
    event_time = models.TimeField(_("event time"), null=True, blank=True)
    location = models.CharField(_("location"), max_length=255, blank=True)
    organizer_name = models.CharField(_("organizer name"), max_length=255, blank=True)
    organizer_contact = models.CharField(_("organizer contact"), max_length=50, blank=True)

    event_type = models.CharField(
        _("event type"), max_length=20, choices=EventType.choices, default=EventType.OTHER
    )
    visibility = models.CharField(
        _("visibility"),
        max_length=20,
        choices=EventVisibility.choices,
        default=EventVisibility.PUBLIC,
    )
    password = models.CharField(
        _("password"), max_length=128, blank=True,
        help_text=_("Required only for password protected events."),
    )

    status = models.CharField(
        _("status"), max_length=20, choices=EventStatus.choices, default=EventStatus.DRAFT
    )
    gallery_expiry_date = models.DateField(_("gallery expiry date"), null=True, blank=True)
    allow_download = models.BooleanField(_("allow download"), default=False)
    show_watermark = models.BooleanField(_("show watermark"), default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="events",
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("event")
        verbose_name_plural = _("events")
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("events:event_detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if self.password:
            try:
                identify_hasher(self.password)
            except ValueError:
                self.password = make_password(self.password)
        if not self.uuid:
            import uuid
            self.uuid = uuid.uuid4()
        if not self.slug:
            self.slug = slugify(self.title)[:280]
        super().save(*args, **kwargs)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        from django.contrib.auth.hashers import check_password
        if not self.password:
            return False
        try:
            is_valid = check_password(raw_password, self.password)
        except ValueError:
            is_valid = False
        if not is_valid:
            if self.password == raw_password:
                self.password = make_password(raw_password)
                self.save(update_fields=["password"])
                return True
            return False
        return True

    @property
    def is_expired(self):
        if not self.gallery_expiry_date:
            return False
        return self.gallery_expiry_date < timezone.localdate()

    @property
    def requires_password(self):
        return self.visibility == EventVisibility.PASSWORD_PROTECTED

    @property
    def studio_owner(self):
        return self.studio.owner if self.studio else None


class Client(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="client_profiles",
        verbose_name=_("user"),
        limit_choices_to={"role": "client"},
    )
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="clients",
        verbose_name=_("event"),
    )
    name = models.CharField(_("name"), max_length=255)
    email = models.EmailField(_("email"), blank=True)
    phone = models.CharField(_("phone"), max_length=20, blank=True)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=[("active", _("Active")), ("inactive", _("Inactive"))],
        default="active",
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("client")
        verbose_name_plural = _("clients")
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
