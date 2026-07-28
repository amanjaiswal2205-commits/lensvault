from django.urls import path

from apps.uploads import views

app_name = "uploads"

urlpatterns = [
    path("", views.UploadManagerView.as_view(), name="upload_manager"),
    path("api/", views.UploadAPIView.as_view(), name="upload_api"),
]
