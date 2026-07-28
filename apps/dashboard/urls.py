from django.urls import path

from apps.dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("", views.index, name="index"),
    path("analytics/", views.analytics, name="analytics"),
    path("downloads/", views.download_history, name="downloads"),
]
