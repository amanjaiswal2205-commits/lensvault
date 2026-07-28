import io

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.decorators import get_user_studio
from apps.accounts.models import User
from apps.albums.models import Album
from apps.media.models import (
    ALLOWED_EXTENSIONS,
    IMAGE_EXTENSIONS,
    MAX_IMAGE_SIZE,
    MAX_VIDEO_SIZE,
    Media,
    MediaStatus,
    MediaType,
)


def _extension(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _generate_thumbnail(uploaded_file, max_size=(400, 400)):
    """Generate a small JPEG thumbnail for image uploads. Returns bytes or None."""
    try:
        from PIL import Image

        image = Image.open(uploaded_file)
        image.thumbnail(max_size)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=80)
        return buffer.getvalue()
    except Exception:
        return None


class UploadManagerView(LoginRequiredMixin, TemplateView):
    template_name = "upload/upload_manager.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        queryset = Album.objects.select_related("event").all()
        if user.role == User.Role.STUDIO_OWNER:
            studio = get_user_studio(user)
            if studio:
                queryset = queryset.filter(event__studio=studio)
        elif user.role == User.Role.STAFF:
            studio = get_user_studio(user)
            if studio:
                queryset = queryset.filter(event__studio=studio)
        elif user.role == User.Role.CLIENT:
            queryset = Album.objects.none()
        context["albums"] = queryset.order_by("event__title", "title")
        return context


class UploadAPIView(LoginRequiredMixin, View):
    """AJAX endpoint: accepts one file + album id and creates a Media record."""

    def post(self, request, *args, **kwargs):
        user = request.user
        album_id = request.POST.get("album")
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            return JsonResponse(
                {"success": False, "error": str(_("No file was provided."))}, status=400
            )

        if not album_id:
            return JsonResponse(
                {"success": False, "error": str(_("Please select an album."))}, status=400
            )

        try:
            album = Album.objects.select_related("event").get(pk=album_id)
        except Album.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": str(_("Selected album does not exist."))},
                status=400,
            )

        if user.role == User.Role.SUPER_ADMIN:
            pass
        else:
            studio = get_user_studio(user)
            if not studio or album.event.studio_id != studio.id:
                return JsonResponse(
                    {"success": False, "error": str(_("You do not have permission to upload to this album."))},
                    status=403,
                )

        ext = _extension(uploaded_file.name)
        if ext not in ALLOWED_EXTENSIONS:
            return JsonResponse(
                {
                    "success": False,
                    "error": str(
                        _("Unsupported file type '.%(ext)s'.") % {"ext": ext}
                    ),
                },
                status=400,
            )

        size = getattr(uploaded_file, "size", 0) or 0
        if ext in IMAGE_EXTENSIONS:
            if size > MAX_IMAGE_SIZE:
                return JsonResponse(
                    {
                        "success": False,
                        "error": str(
                            _("Image is too large. Maximum allowed is 20 MB.")
                        ),
                    },
                    status=400,
                )
            media_type = MediaType.IMAGE
        else:
            if size > MAX_VIDEO_SIZE:
                return JsonResponse(
                    {
                        "success": False,
                        "error": str(
                            _("Video is too large. Maximum allowed is 2048 MB.")
                        ),
                    },
                    status=400,
                )
            media_type = MediaType.VIDEO

        title = uploaded_file.name.rsplit("/", 1)[-1]
        if "." in title:
            title = title.rsplit(".", 1)[0] or title

        try:
            import uuid as uuid_lib

            media = Media(
                uuid=uuid_lib.uuid4(),
                album=album,
                event=album.event,
                title=title,
                media_type=media_type,
                uploaded_by=user,
                status=MediaStatus.ACTIVE,
            )

            if media_type == MediaType.IMAGE:
                thumb_data = _generate_thumbnail(uploaded_file)
                if thumb_data:
                    from django.core.files.base import ContentFile

                    media.thumbnail.save(
                        f"{media.uuid}_thumb.jpg",
                        ContentFile(thumb_data),
                        save=False,
                    )
                    uploaded_file.seek(0)

            media.file = uploaded_file
            media.save()
        except Exception as exc:  # pragma: no cover - defensive
            return JsonResponse(
                {"success": False, "error": str(exc)}, status=500
            )

        return JsonResponse(
            {
                "success": True,
                "uuid": str(media.uuid),
                "title": media.title,
                "media_type": media.media_type,
                "url": media.get_absolute_url(),
                "detail_url": media.get_absolute_url(),
            }
        )
