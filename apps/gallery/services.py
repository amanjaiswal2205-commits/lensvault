from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.accounts.decorators import get_user_studio
from apps.accounts.models import User
from apps.events.models import Client
from apps.gallery.models import ClientGallery, GalleryDownloadLog, GalleryVisit
from apps.media.models import Media


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


class GalleryAccessService:
    @staticmethod
    def get_gallery_by_token(share_token):
        gallery = get_object_or_404(
            ClientGallery.objects.select_related("event", "event__studio"),
            share_token=share_token,
            is_active=True,
        )
        if gallery.expires_at and gallery.expires_at < timezone.now():
            raise Http404("Gallery has expired.")
        return gallery

    @staticmethod
    def is_public(gallery):
        return gallery.access_type == ClientGallery.AccessType.PUBLIC

    @staticmethod
    def is_password_required(gallery):
        return gallery.access_type == ClientGallery.AccessType.PASSWORD_PROTECTED

    @staticmethod
    def is_private(gallery):
        return gallery.access_type == ClientGallery.AccessType.PRIVATE

    @staticmethod
    def can_access_private(gallery, request):
        if not request.user.is_authenticated:
            return False
        if request.user.role == User.Role.SUPER_ADMIN:
            return True
        studio = get_user_studio(request.user)
        if studio and gallery.event.studio_id == studio.id:
            return True
        if request.user.role == User.Role.CLIENT:
            return Client.objects.filter(user=request.user, event=gallery.event).exists()
        return False

    @staticmethod
    def can_download(gallery, request=None):
        if not gallery.allow_download:
            return False
        if request and GalleryAccessService.is_password_required(gallery):
            session_key = f"gallery_access_{gallery.share_token}"
            if not request.session.get(session_key):
                return False
        return True

    @staticmethod
    def can_favorite(gallery):
        return gallery.allow_favorites

    @staticmethod
    def check_password(gallery, raw_password):
        return gallery.check_password(raw_password)

    @staticmethod
    def record_visit(gallery, request):
        session_id = request.session.session_key or ""
        if not session_id:
            request.session.save()
            session_id = request.session.session_key

        thirty_minutes_ago = timezone.now() - timezone.timedelta(minutes=30)
        last_visit = (
            GalleryVisit.objects.filter(
                gallery=gallery,
                session_id=session_id,
                visited_at__gte=thirty_minutes_ago,
            )
            .order_by("-visited_at")
            .first()
        )
        if last_visit:
            return None

        return GalleryVisit.objects.create(
            gallery=gallery,
            session_id=session_id,
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
            referrer=request.META.get("HTTP_REFERER", ""),
        )

    @staticmethod
    def download_photo(gallery, photo, request):
        if photo.event_id != gallery.event_id:
            raise Http404("Photo not found.")

        if not GalleryAccessService.can_download(gallery, request):
            raise Http404("Download not allowed.")

        session_id = request.session.session_key or ""
        if not session_id:
            request.session.save()
            session_id = request.session.session_key

        GalleryDownloadLog.objects.create(
            gallery=gallery,
            photo=photo,
            session_id=session_id,
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
        )

        return FileResponse(
            photo.file.open("rb"),
            as_attachment=True,
            filename=photo.file.name.split("/")[-1],
        )
