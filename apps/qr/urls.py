from django.urls import path

from apps.qr import views

app_name = "qr"

urlpatterns = [
    path("<slug:event_slug>/generate/", views.GenerateQRCodeView.as_view(), name="generate"),
]
