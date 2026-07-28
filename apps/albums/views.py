from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
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
from apps.albums.forms import AlbumForm
from apps.albums.models import Album, AlbumStatus
from apps.events.models import Event, EventStatus


class AlbumListView(LoginRequiredMixin, ListView):
    model = Album
    template_name = "albums/album_list.html"
    context_object_name = "albums"
    paginate_by = 9

    def get_queryset(self):
        queryset = Album.objects.select_related("event", "event__studio", "event__studio__owner").all()
        request = self.request
        user = request.user

        if user.role == User.Role.SUPER_ADMIN:
            pass
        elif user.role in (User.Role.STUDIO_OWNER, User.Role.STAFF):
            studio = get_user_studio(user)
            if studio:
                queryset = queryset.filter(event__studio=studio)
            else:
                return Album.objects.none()
        else:
            return Album.objects.none()

        search = request.GET.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        event = request.GET.get("event")
        if event:
            queryset = queryset.filter(event__slug=event)

        status = request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        sort = request.GET.get("sort", "album_order")
        if sort == "latest":
            queryset = queryset.order_by("-created_at")
        elif sort == "album_order":
            queryset = queryset.order_by("album_order", "-created_at")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = self.request.GET.get("search", "")
        context["event_filter"] = self.request.GET.get("event", "")
        context["status_filter"] = self.request.GET.get("status", "")
        context["sort"] = self.request.GET.get("sort", "album_order")
        context["status_choices"] = AlbumStatus.choices
        context["events"] = Event.objects.all().order_by("title")
        context["album_create_url"] = reverse_lazy("albums:album_create")
        return context


class AlbumDetailView(LoginRequiredMixin, DetailView):
    model = Album
    template_name = "albums/album_detail.html"
    context_object_name = "album"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        qs = super().get_queryset().select_related("event", "event__studio", "event__studio__owner")
        user = self.request.user
        if user.role == User.Role.SUPER_ADMIN:
            return qs
        studio = get_user_studio(user)
        if studio:
            return qs.filter(event__studio=studio)
        return Album.objects.none()


class AlbumCreateView(LoginRequiredMixin, CreateView):
    model = Album
    form_class = AlbumForm
    template_name = "albums/album_create.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        user = request.user
        if user.role not in (User.Role.SUPER_ADMIN, User.Role.STUDIO_OWNER):
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        user = self.request.user
        if user.role == User.Role.STUDIO_OWNER:
            studio = get_user_studio(user)
            if studio and not form.instance.event.studio_id:
                form.instance.event.studio = studio
                form.instance.event.save()
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


class AlbumUpdateView(LoginRequiredMixin, UpdateView):
    model = Album
    form_class = AlbumForm
    template_name = "albums/album_update.html"
    context_object_name = "album"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        qs = super().get_queryset().select_related("event", "event__studio", "event__studio__owner")
        user = self.request.user
        if user.role == User.Role.SUPER_ADMIN:
            return qs
        studio = get_user_studio(user)
        if studio:
            return qs.filter(event__studio=studio)
        return Album.objects.none()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return self.object.get_absolute_url()


class AlbumDeleteView(LoginRequiredMixin, DeleteView):
    model = Album
    template_name = "albums/album_delete.html"
    context_object_name = "album"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    success_url = reverse_lazy("albums:album_list")

    def get_queryset(self):
        qs = super().get_queryset().select_related("event", "event__studio", "event__studio__owner")
        user = self.request.user
        if user.role == User.Role.SUPER_ADMIN:
            return qs
        studio = get_user_studio(user)
        if studio:
            return qs.filter(event__studio=studio)
        return Album.objects.none()
