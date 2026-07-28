from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.events.models import Event, EventVisibility

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


class EventForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "cover_image",
            "event_date",
            "event_time",
            "location",
            "organizer_name",
            "organizer_contact",
            "event_type",
            "visibility",
            "password",
            "status",
            "gallery_expiry_date",
            "allow_download",
            "show_watermark",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "event_date": forms.DateInput(attrs={"type": "date"}),
            "event_time": forms.TimeInput(attrs={"type": "time"}),
            "gallery_expiry_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_title(self):
        title = self.cleaned_data.get("title")
        qs = Event.objects.filter(title__iexact=title)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(_("An event with this title already exists."))
        return title

    def clean(self):
        cleaned = super().clean()
        visibility = cleaned.get("visibility")
        password = cleaned.get("password")

        if visibility == EventVisibility.PASSWORD_PROTECTED and not password:
            self.add_error(
                "password",
                _("Password is required for password protected events."),
            )

        if visibility != EventVisibility.PASSWORD_PROTECTED and password:
            cleaned["password"] = ""

        expiry = cleaned.get("gallery_expiry_date")
        if expiry and expiry < timezone.localdate():
            self.add_error(
                "gallery_expiry_date",
                _("Gallery expiry date cannot be in the past."),
            )
        return cleaned

    def save(self, commit=True):
        event = super().save(commit=False)
        if event.visibility != EventVisibility.PASSWORD_PROTECTED:
            event.password = ""
        if commit:
            event.save()
        return event
