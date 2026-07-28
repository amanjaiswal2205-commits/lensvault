from django.conf import settings
from django.contrib.auth import (
    login,
    logout,
    update_session_auth_hash,
    views as auth_views,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.urls import reverse_lazy

from apps.accounts.email import send_verification_email
from apps.accounts.forms import (
    CustomPasswordChangeForm,
    ProfileEditForm,
    RegistrationForm,
)
from django.contrib.auth import get_user_model

User = get_user_model()


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    if request.method == "POST":
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            send_verification_email(request, user)
            messages.success(
                request,
                "Account created successfully. Please check your email to verify your account.",
            )
            return redirect("accounts:login")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    return render(
        request,
        "accounts/profile.html",
        {"user": request.user, "site_name": settings.SITE_NAME},
    )


@login_required
def edit_profile(request):
    if request.method == "POST":
        form = ProfileEditForm(
            request.POST, request.FILES, instance=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:profile")
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, "accounts/edit_profile.html", {"form": form})


@login_required
def change_password(request):
    if request.method == "POST":
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, "Your password was changed successfully.")
            return redirect("accounts:profile")
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, "accounts/change_password.html", {"form": form})


@login_required
def custom_logout(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "You have been logged out.")
        return redirect("core:home")
    return redirect("core:home")


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if not user.is_verified:
            user.is_verified = True
            user.save()
        messages.success(
            request, "Your email has been verified. You can now sign in."
        )
        return redirect("accounts:login")

    messages.error(request, "The verification link is invalid or has expired.")
    return redirect("accounts:login")


class CustomLoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class CustomLogoutView(auth_views.LogoutView):
    pass


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "accounts/forgot_password.html"
    email_template_name = "accounts/email/password_reset_email.html"
    subject_template_name = "accounts/email/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "accounts/reset_password.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"
