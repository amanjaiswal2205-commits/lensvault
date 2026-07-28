from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()

FIELD_CLASSES = (
    "w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm "
    "focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 outline-none transition"
)


class TailwindFormMixin:
    """Applies consistent Tailwind styling to every widget automatically."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                continue
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (css + " " + FIELD_CLASSES).strip()
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs["class"] = "block w-full text-sm text-gray-500 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"


class RegistrationForm(TailwindFormMixin, UserCreationForm):
    full_name = forms.CharField(max_length=255, required=True, label=_("Full name"))
    email = forms.EmailField(required=True, label=_("Email"))
    mobile_number = forms.CharField(max_length=20, required=False, label=_("Mobile number"))
    role = forms.ChoiceField(
        choices=[
            (User.Role.CLIENT, _("Client")),
            (User.Role.STUDIO_OWNER, _("Photographer / Studio")),
        ],
        required=True,
        label=_("Role"),
        initial=User.Role.CLIENT,
    )
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label=_("Confirm password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = User
        fields = ("full_name", "email", "mobile_number", "role")

    def _generate_unique_username(self, email):
        base = email.split("@")[0]
        base = "".join(ch for ch in base if ch.isalnum() or ch == "_")
        base = base.lower()[:150] or "user"
        username = base
        counter = 1
        while User.objects.filter(username=username).exists():
            suffix = str(counter)
            username = f"{base[:150 - len(suffix)]}{suffix}"
            counter += 1
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(_("A user with this email already exists."))
        return email

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        user.full_name = self.cleaned_data["full_name"]
        user.mobile_number = self.cleaned_data.get("mobile_number", "")
        user.role = self.cleaned_data["role"]
        user.username = self._generate_unique_username(user.email)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class ProfileEditForm(TailwindFormMixin, UserChangeForm):
    password = None

    full_name = forms.CharField(max_length=255, required=True, label=_("Full name"))
    profile_photo = forms.ImageField(
        required=False, label=_("Profile photo"), widget=forms.FileInput
    )
    date_of_birth = forms.DateField(
        required=False, label=_("Date of birth"), widget=forms.DateInput(attrs={"type": "date"})
    )

    class Meta:
        model = User
        fields = (
            "full_name",
            "username",
            "email",
            "mobile_number",
            "profile_photo",
            "date_of_birth",
            "gender",
            "address",
            "city",
            "state",
            "country",
            "pincode",
            "bio",
            "account_type",
        )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_("A user with this email already exists."))
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if (
            User.objects.filter(username__iexact=username)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise ValidationError(_("This username is already taken."))
        return username


class CustomPasswordChangeForm(TailwindFormMixin, forms.Form):
    old_password = forms.CharField(
        label=_("Current password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    new_password1 = forms.CharField(
        label=_("New password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    new_password2 = forms.CharField(
        label=_("Confirm new password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data["old_password"]
        if not self.user.check_password(old_password):
            raise ValidationError(_("Your old password was incorrect."))
        return old_password

    def clean_new_password1(self):
        password = self.cleaned_data["new_password1"]
        validate_password(password, self.user)
        return password

    def clean_new_password2(self):
        p1 = self.cleaned_data.get("new_password1")
        p2 = self.cleaned_data.get("new_password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError(_("The two password fields didn't match."))
        return p2

    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user


# Forms used by the Django admin (kept for backward compatibility).
class CustomUserCreationForm(TailwindFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "username", "role", "account_type")


class CustomUserChangeForm(TailwindFormMixin, UserChangeForm):
    class Meta:
        model = User
        fields = (
            "email",
            "username",
            "full_name",
            "profile_photo",
            "mobile_number",
            "role",
            "account_type",
            "is_verified",
            "is_active",
            "is_staff",
            "is_superuser",
        )
