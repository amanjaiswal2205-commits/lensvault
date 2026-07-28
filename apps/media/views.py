from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from apps.accounts.decorators import get_user_studio
from apps.accounts.models import User
from apps.albums.models import Album
from apps.events.models import Event
from apps.media.forms import MediaForm
from apps.media.models import Media, MediaStatus, MediaType


class MediaListView(LoginRequiredMixin, ListView):
    model = Media
    template_name = "media/media_list.html"
    context_object_name = "media_items"
    paginate_by = 12

    def get_queryset(self):
        queryset = Media.objects.select_related("album", "event", "uploaded_by").all()
        request = self.request
        user = request.user

        if user.role == User.Role.SUPER_ADMIN:
            pass
        elif user.role in (User.Role.STUDIO_OWNER, User.Role.STAFF):
            studio = get_user_studio(user)
            if studio:
                queryset = queryset.filter(event__studio=studio)
            else:
                return Media.objects.none()
        else:
            return Media.objects.none()

        search = request.GET.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        album = request.GET.get("album")
        if album:
            queryset = queryset.filter(album__slug=album)

        event = request.GET.get("event")
        if event:
            queryset = queryset.filter(event__slug=event)

        media_type = request.GET.get("media_type")
        if media_type:
            queryset = queryset.filter(media_type=media_type)

        status = request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        sort = request.GET.get("sort", "latest")
        if sort == "oldest":
            queryset = queryset.order_by("created_at")
        elif sort == "most_viewed":
            queryset = queryset.order_by("-view_count", "-created_at")
        elif sort == "most_downloaded":
            queryset = queryset.order_by("-download_count", "-created_at")
        else:
            queryset = queryset.order_by("-created_at")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = self.request.GET.get("search", "")
        context["album_filter"] = self.request.GET.get("album", "")
        context["event_filter"] = self.request.GET.get("event", "")
        context["type_filter"] = self.request.GET.get("media_type", "")
        context["status_filter"] = self.request.GET.get("status", "")
        context["sort"] = self.request.GET.get("sort", "latest")
        context["type_choices"] = MediaType.choices
        context["status_choices"] = MediaStatus.choices
        context["albums"] = Album.objects.all().order_by("title")
        context["events"] = Event.objects.all().order_by("title")
        context["media_create_url"] = reverse_lazy("media:media_create")
        return context


class MediaDetailView(LoginRequiredMixin, DetailView):
    model = Media
    template_name = "media/media_detail.html"
    context_object_name = "media_item"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    pk_url_kwarg = None

    def get_queryset(self):
        qs = super().get_queryset().select_related("album", "album__event", "event")
        user = self.request.user
        if user.role == User.Role.SUPER_ADMIN:
            return qs
        studio = get_user_studio(user)
        if studio:
            return qs.filter(event__studio=studio)
        return Media.objects.none()

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        self.object.view_count = (self.object.view_count or 0) + 1
        self.object.save(update_fields=["view_count"])
        return response


class MediaCreateView(LoginRequiredMixin, CreateView):
    model = Media
    form_class = MediaForm
    template_name = "media/media_create.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        user = request.user
        if user.role not in (User.Role.SUPER_ADMIN, User.Role.STUDIO_OWNER):
            if user.role == User.Role.STAFF:
                staff_profile = getattr(user, "staff_profiles", None)
                if not (staff_profile and staff_profile.first() and staff_profile.first().has_permission("upload_photos")):
                    return redirect("core:home")
            else:
                return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


class MediaUpdateView(LoginRequiredMixin, UpdateView):
    model = Media
    form_class = MediaForm
    template_name = "media/media_update.html"
    context_object_name = "media_item"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    pk_url_kwarg = None

    def get_queryset(self):
        qs = super().get_queryset().select_related("album", "album__event", "event")
        user = self.request.user
        if user.role == User.Role.SUPER_ADMIN:
            return qs
        studio = get_user_studio(user)
        if studio:
            return qs.filter(event__studio=studio)
        return Media.objects.none()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return self.object.get_absolute_url()


class MediaDeleteView(LoginRequiredMixin, DeleteView):
    model = Media
    template_name = "media/media_delete.html"
    context_object_name = "media_item"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    pk_url_kwarg = None
    success_url = reverse_lazy("media:media_list")

    def get_queryset(self):
        qs = super().get_queryset().select_related("album", "album__event", "event")
        user = self.request.user
        if user.role == User.Role.SUPER_ADMIN:
            return qs
        studio = get_user_studio(user)
        if studio:
            return qs.filter(event__studio=studio)
        return Media.objects.none()
