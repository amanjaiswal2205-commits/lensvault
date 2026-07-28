from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User
from apps.events.models import Event, EventVisibility
from apps.gallery.models import ClientGallery


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
                field.widget.attrs["class"] = (
                    "block w-full text-sm text-gray-500 file:mr-3 file:py-2 file:px-4 "
                    "file:rounded-lg file:border-0 file:bg-indigo-50 file:text-indigo-700 "
                    "hover:file:bg-indigo-100"
                )


class ClientGalleryForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = ClientGallery
        fields = [
            "name",
            "event",
            "access_type",
            "gallery_password",
            "expires_at",
            "allow_download",
            "allow_favorites",
            "is_active",
        ]
        widgets = {
            "expires_at": forms.DateInput(attrs={"type": "date"}),
            "gallery_password": forms.PasswordInput(render_value=False, attrs={"autocomplete": "new-password"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self._filter_event_queryset()
        if self.instance and self.instance.pk:
            self._adjust_password_field_for_edit()

    def _adjust_password_field_for_edit(self):
        if self.instance.access_type == ClientGallery.AccessType.PASSWORD_PROTECTED:
            self.fields["gallery_password"].required = False
            self.fields["gallery_password"].help_text = "Leave blank to keep the current password."

    def _filter_event_queryset(self):
        qs = Event.objects.all().order_by("title")
        user = self.user
        if user and user.role == User.Role.SUPER_ADMIN:
            pass
        elif user and user.role in (User.Role.STUDIO_OWNER, User.Role.STAFF):
            from apps.accounts.decorators import get_user_studio
            studio = get_user_studio(user)
            if studio:
                qs = qs.filter(studio=studio)
            else:
                qs = Event.objects.none()
        else:
            qs = Event.objects.none()
        self.fields["event"].queryset = qs

    def clean(self):
        cleaned = super().clean()
        access_type = cleaned.get("access_type")
        password = cleaned.get("gallery_password")

        if access_type == ClientGallery.AccessType.PASSWORD_PROTECTED:
            if self.instance and self.instance.pk and not password:
                self._keep_password = True
                cleaned.pop("gallery_password", None)
            elif not password:
                self.add_error(
                    "gallery_password",
                    _("Password is required for password-protected galleries."),
                )
                password = ""

        if access_type != ClientGallery.AccessType.PASSWORD_PROTECTED:
            password = ""
            cleaned["gallery_password"] = password

        return cleaned

    def _post_clean(self):
        super()._post_clean()

    def save(self, commit=True):
        password = self.cleaned_data.pop("gallery_password", None)
        gallery = super().save(commit=False)
        keep_password = getattr(self, "_keep_password", False)
        if keep_password:
            pass
        elif password:
            gallery.set_password(password)
        else:
            gallery.gallery_password = ""
        if commit:
            gallery.save()
        return gallery
