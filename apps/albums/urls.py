from django.urls import path

from apps.albums import views

app_name = "albums"

urlpatterns = [
    path("", views.AlbumListView.as_view(), name="album_list"),
    path("create/", views.AlbumCreateView.as_view(), name="album_create"),
    path("<slug:slug>/", views.AlbumDetailView.as_view(), name="album_detail"),
    path("<slug:slug>/edit/", views.AlbumUpdateView.as_view(), name="album_update"),
    path("<slug:slug>/delete/", views.AlbumDeleteView.as_view(), name="album_delete"),
]
