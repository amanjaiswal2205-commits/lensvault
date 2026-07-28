import io

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import ContentFile
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views import View

from apps.accounts.decorators import get_user_studio, enforce_event_ownership
from apps.accounts.models import User
from apps.events.models import Event, EventStatus
from apps.qr.models import QRCode
from apps.qr.qrgen import generate_qr_png_bytes


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


class GenerateQRCodeView(LoginRequiredMixin, View):
    """Generate (or reuse) a QR code for a published event and show it."""

    http_method_names = ["get", "post"]

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        user = request.user
        if user.role not in (User.Role.SUPER_ADMIN, User.Role.STUDIO_OWNER):
            if user.role == User.Role.STAFF:
                staff_profile = getattr(user, "staff_profiles", None)
                if not (staff_profile and staff_profile.first() and staff_profile.first().has_permission("generate_qr")):
                    return redirect("core:home")
            else:
                return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, event_slug):
        return self._generate(request, event_slug, force=True)

    def get(self, request, event_slug):
        return self._generate(request, event_slug, force=False)

    def _generate(self, request, event_slug, force=False):
        event = get_object_or_404(
            Event,
            slug=event_slug,
            status=EventStatus.PUBLISHED,
        )

        if request.user.role != User.Role.SUPER_ADMIN:
            studio = get_user_studio(request.user)
            if not studio or event.studio_id != studio.id:
                raise Http404("You do not have permission to access this event.")

        qr = QRCode.objects.filter(event=event).first()

        if qr and not force:
            return self._render(request, qr)

        if qr and force:
            import secrets
            qr.token = secrets.token_urlsafe(32)
            qr.is_active = True
        else:
            qr = QRCode(event=event)

        access_url = request.build_absolute_uri(qr.access_path)
        png_bytes = generate_qr_png_bytes(access_url)
        qr.qr_image.save(f"{qr.uuid}.png", ContentFile(png_bytes), save=False)
        qr.save()

        return self._render(request, qr)

    def _render(self, request, qr):
        return render(
            request,
            "qr/qr_detail.html",
            {
                "qr": qr,
                "event": qr.event,
                "access_url": qr.get_access_url(request),
            },
        )
