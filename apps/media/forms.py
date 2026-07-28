from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.albums.models import Album
from apps.events.models import Event
from apps.media.models import (
    ALLOWED_EXTENSIONS,
    MAX_IMAGE_SIZE,
    MAX_VIDEO_SIZE,
    Media,
    MediaType,
)

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


def _get_extension(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


class MediaForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Media
        fields = [
            "album",
            "title",
            "description",
            "file",
            "thumbnail",
            "media_type",
            "is_featured",
            "status",
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["album"].queryset = Album.objects.select_related("event").all().order_by("title")

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if not file:
            raise ValidationError(_("A media file is required."))

        ext = _get_extension(file.name)
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationError(
                _(
                    "Unsupported file type '.%(ext)s'. Allowed: images (jpg, jpeg, png, webp) "
                    "and videos (mp4, mov, avi, mkv)."
                )
                % {"ext": ext}
            )

        size = getattr(file, "size", None)
        if size is None:
            return file

        if ext in ("jpg", "jpeg", "png", "webp"):
            if size > MAX_IMAGE_SIZE:
                raise ValidationError(
                    _("Image file is too large (%(size).1f MB). Maximum allowed is 20 MB.")
                    % {"size": size / (1024 * 1024)}
                )
        else:
            if size > MAX_VIDEO_SIZE:
                raise ValidationError(
                    _("Video file is too large (%(size).1f MB). Maximum allowed is 2048 MB.")
                    % {"size": size / (1024 * 1024)}
                )
        return file

    def clean(self):
        cleaned = super().clean()
        album = cleaned.get("album")
        media_type = cleaned.get("media_type")
        file = cleaned.get("file")
        if album and not self.instance.event_id:
            cleaned["event"] = album.event
        if album and file:
            ext = _get_extension(file.name)
            expected = MediaType.IMAGE if ext in ("jpg", "jpeg", "png", "webp") else MediaType.VIDEO
            if media_type and media_type != expected:
                self.add_error(
                    "media_type",
                    _(
                        "Selected media type (%(sel)s) does not match the uploaded file "
                        "(%(exp)s)."
                    )
                    % {
                        "sel": MediaType(media_type).label,
                        "exp": MediaType(expected).label,
                    },
                )
        return cleaned

    def save(self, commit=True):
        media = super().save(commit=False)
        if media.album_id and not media.event_id:
            media.event = media.album.event
        if commit:
            media.save()
        return media
