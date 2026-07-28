from django.shortcuts import redirect
from django.urls import reverse


class DashboardAccessMiddleware:
    """Protect dashboard routes.

    - Anonymous users -> redirect to login.
    - Client users -> redirect to home (dashboard forbidden).
    - Super Admin, Studio Owner, Staff -> allowed.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.protected_prefixes = ("/dashboard/",)

    def __call__(self, request):
        path = request.path_info
        if any(path.startswith(prefix) for prefix in self.protected_prefixes):
            user = request.user
            if not user.is_authenticated:
                return redirect(f"{reverse('accounts:login')}?next={path}")
            if user.role == user.Role.CLIENT:
                return redirect("core:home")
        return self.get_response(request)
