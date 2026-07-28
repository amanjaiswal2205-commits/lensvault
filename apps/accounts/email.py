from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def build_verification_link(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    domain = get_current_site(request).domain
    protocol = "https" if request.is_secure() else "http"
    return f"{protocol}://{domain}/accounts/verify-email/{uid}/{token}/"


def send_verification_email(request, user):
    subject = f"Verify your {settings.SITE_NAME} account"
    message = render_to_string(
        "accounts/email/verify_email_email.html",
        {
            "user": user,
            "site_name": settings.SITE_NAME,
            "verification_url": build_verification_link(request, user),
        },
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
