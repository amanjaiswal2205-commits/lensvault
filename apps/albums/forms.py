from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.albums.models import Album, AlbumStatus
from apps.events.models import Event

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


class AlbumForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Album
        fields = [
            "event",
            "title",
            "description",
            "cover_image",
            "album_order",
            "is_featured",
            "status",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["event"].queryset = Event.objects.all().order_by("title")
        if user is not None and not user.is_staff:
            pass

    def clean_title(self):
        title = self.cleaned_data.get("title")
        event = self.cleaned_data.get("event")
        qs = Album.objects.filter(event=event, title__iexact=title)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(
                _("An album with this title already exists for the selected event.")
            )
        return title

    def save(self, commit=True):
        album = super().save(commit=False)
        if commit:
            album.save()
        return album
