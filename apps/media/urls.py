from django.urls import path

from apps.media import views

app_name = "media"

urlpatterns = [
    path("", views.MediaListView.as_view(), name="media_list"),
    path("create/", views.MediaCreateView.as_view(), name="media_create"),
    path("<uuid:uuid>/", views.MediaDetailView.as_view(), name="media_detail"),
    path("<uuid:uuid>/edit/", views.MediaUpdateView.as_view(), name="media_update"),
    path("<uuid:uuid>/delete/", views.MediaDeleteView.as_view(), name="media_delete"),
]
