from functools import wraps
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User
from apps.events.models import Studio, Event
from apps.albums.models import Album
from apps.media.models import Media


def require_super_admin(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != User.Role.SUPER_ADMIN:
            return redirect("core:home")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def require_owner(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != User.Role.STUDIO_OWNER:
            return redirect("core:home")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def require_staff(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != User.Role.STAFF:
            return redirect("core:home")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def require_dashboard_access(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('accounts:login')}?next={request.path}")
        if request.user.role == User.Role.CLIENT:
            return redirect("core:home")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# ---------------------------------------------------------------------------
# Ownership helpers
# ---------------------------------------------------------------------------

def get_user_studio(user):
    if user.role == User.Role.SUPER_ADMIN:
        return None
    if user.role == User.Role.STUDIO_OWNER:
        return Studio.objects.filter(owner=user).first()
    if user.role == User.Role.STAFF:
        staff_profile = getattr(user, "staff_profiles", None)
        if staff_profile and staff_profile.exists():
            return staff_profile.first().studio
    return None


def enforce_event_ownership(event, user):
    """Return True if user can access the event."""
    if user.role == User.Role.SUPER_ADMIN:
        return True
    studio = get_user_studio(user)
    if studio and event.studio_id == studio.id:
        return True
    return False


def enforce_studio_ownership(studio, user):
    """Return True if user owns the studio."""
    if user.role == User.Role.SUPER_ADMIN:
        return True
    return studio.owner_id == user.id
