from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", User.Role.CLIENT)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.SUPER_ADMIN)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        SUPER_ADMIN = "super_admin", _("Super Admin")
        STUDIO_OWNER = "studio_owner", _("Studio Owner")
        STAFF = "staff", _("Staff")
        CLIENT = "client", _("Client")

    ACCOUNT_ADMIN = "admin"
    ACCOUNT_PHOTOGRAPHER = "photographer"
    ACCOUNT_TYPE_CHOICES = [
        (ACCOUNT_ADMIN, "Admin"),
        (ACCOUNT_PHOTOGRAPHER, "Photographer"),
    ]

    GENDER_MALE = "male"
    GENDER_FEMALE = "female"
    GENDER_OTHER = "other"
    GENDER_CHOICES = [
        (GENDER_MALE, "Male"),
        (GENDER_FEMALE, "Female"),
        (GENDER_OTHER, "Other"),
    ]

    # Authentication
    email = models.EmailField(_("email address"), unique=True)
    username = models.CharField(_("username"), max_length=150, unique=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)

    # Profile
    full_name = models.CharField(_("full name"), max_length=255, blank=True)
    mobile_number = models.CharField(_("mobile number"), max_length=20, blank=True)
    profile_photo = models.ImageField(
        _("profile photo"), upload_to="profiles/", blank=True, null=True
    )
    date_of_birth = models.DateField(_("date of birth"), blank=True, null=True)
    gender = models.CharField(
        _("gender"), max_length=10, choices=GENDER_CHOICES, blank=True
    )
    address = models.TextField(_("address"), blank=True)
    city = models.CharField(_("city"), max_length=100, blank=True)
    state = models.CharField(_("state"), max_length=100, blank=True)
    country = models.CharField(_("country"), max_length=100, blank=True)
    pincode = models.CharField(_("pincode"), max_length=20, blank=True)
    bio = models.TextField(_("bio"), blank=True)

    # Account
    account_type = models.CharField(
        _("account type"),
        max_length=20,
        choices=ACCOUNT_TYPE_CHOICES,
        default=ACCOUNT_PHOTOGRAPHER,
    )
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT,
    )
    is_verified = models.BooleanField(_("is verified"), default=False)
    is_active = models.BooleanField(_("active"), default=True)
    is_staff = models.BooleanField(_("staff status"), default=False)
    date_joined = models.DateTimeField(_("date joined"), auto_now_add=True)
    last_login = models.DateTimeField(_("last login"), blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    @property
    def display_name(self):
        return (
            self.full_name
            or f"{self.first_name} {self.last_name}".strip()
            or self.username
            or self.email
        )

    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN

    @property
    def is_studio_owner(self):
        return self.role == self.Role.STUDIO_OWNER

    @property
    def is_staff_member(self):
        return self.role == self.Role.STAFF

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT

    @property
    def can_access_dashboard(self):
        return self.is_authenticated and self.role in (
            self.Role.SUPER_ADMIN,
            self.Role.STUDIO_OWNER,
            self.Role.STAFF,
        )


class Staff(models.Model):
    PERMISSIONS_CHOICES = [
        ("create_events", _("Create Events")),
        ("upload_photos", _("Upload Photos")),
        ("delete_photos", _("Delete Photos")),
        ("generate_qr", _("Generate QR")),
        ("manage_clients", _("Manage Clients")),
        ("view_analytics", _("View Analytics")),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_profiles",
        verbose_name=_("user"),
        limit_choices_to={"role": "staff"},
    )
    studio = models.ForeignKey(
        "events.Studio",
        on_delete=models.CASCADE,
        related_name="staff",
        verbose_name=_("studio"),
    )
    permissions = models.JSONField(
        _("permissions"),
        default=list,
        blank=True,
        help_text=_("List of enabled permission codenames."),
    )
    is_active = models.BooleanField(_("active"), default=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("staff")
        verbose_name_plural = _("staff")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "studio"],
                name="unique_staff_per_studio",
            )
        ]

    def __str__(self):
        return f"{self.user.display_name} @ {self.studio.name}"

    def has_permission(self, codename):
        return codename in self.permissions
