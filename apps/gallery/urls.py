from django.urls import path

from apps.gallery import management_views, views

app_name = "gallery"

urlpatterns = [
    path("", views.EventGalleryView.as_view(), name="event_gallery"),
    path("event/<slug:event_slug>/", views.AlbumGalleryView.as_view(), name="event_gallery_detail"),
    path("event/<slug:event_slug>/password/", views.event_password, name="event_password"),
    path("album/<slug:album_slug>/", views.AlbumGalleryView.as_view(), name="album_gallery"),
    path("media/<uuid:uuid>/", views.MediaDetailView.as_view(), name="media_detail"),
    path("g/<uuid:share_token>/password/", views.gallery_password, name="gallery_password"),
    path("g/<uuid:share_token>/selected/", views.selected_photos, name="gallery_selected_photos"),
    path("manage/", management_views.ClientGalleryListView.as_view(), name="gallery_manage_list"),
    path("manage/create/", management_views.ClientGalleryCreateView.as_view(), name="gallery_manage_create"),
    path("manage/<slug:slug>/", management_views.ClientGalleryDetailView.as_view(), name="gallery_manage_detail"),
    path("manage/<slug:slug>/edit/", management_views.ClientGalleryUpdateView.as_view(), name="gallery_manage_update"),
    path("manage/<slug:slug>/delete/", management_views.ClientGalleryDeleteView.as_view(), name="gallery_manage_delete"),
]
