from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from apps.accounts.decorators import get_user_studio
from apps.accounts.models import User
from apps.events.forms import EventForm
from apps.events.models import Event, EventStatus, EventType, EventVisibility


class EventListView(LoginRequiredMixin, ListView):
    model = Event
    template_name = "events/event_list.html"
    context_object_name = "events"
    paginate_by = 9

    def get_queryset(self):
        queryset = Event.objects.select_related("studio", "studio__owner", "created_by").all()
        request = self.request
        user = request.user

        if user.role == User.Role.SUPER_ADMIN:
            pass
        elif user.role in (User.Role.STUDIO_OWNER, User.Role.STAFF):
            studio = get_user_studio(user)
            if studio:
                queryset = queryset.filter(studio=studio)
            else:
                return Event.objects.none()
        else:
            return Event.objects.none()

        search = request.GET.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(location__icontains=search)
                | Q(organizer_name__icontains=search)
                | Q(description__icontains=search)
            )

        status = request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        event_type = request.GET.get("event_type")
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        visibility = request.GET.get("visibility")
        if visibility:
            queryset = queryset.filter(visibility=visibility)

        order = request.GET.get("order", "latest")
        if order == "oldest":
            queryset = queryset.order_by("created_at")
        else:
            queryset = queryset.order_by("-created_at")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = self.request.GET.get("search", "")
        context["status_filter"] = self.request.GET.get("status", "")
        context["type_filter"] = self.request.GET.get("event_type", "")
        context["visibility_filter"] = self.request.GET.get("visibility", "")
        context["order"] = self.request.GET.get("order", "latest")
        context["status_choices"] = EventStatus.choices
        context["type_choices"] = EventType.choices
        context["visibility_choices"] = EventVisibility.choices
        context["events_create_url"] = reverse_lazy("events:event_create")
        return context


class EventDetailView(LoginRequiredMixin, DetailView):
    model = Event
    template_name = "events/event_detail.html"
    context_object_name = "event"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        qs = super().get_queryset().select_related("studio", "studio__owner", "created_by")
        user = self.request.user
        if user.role == User.Role.SUPER_ADMIN:
            return qs
        studio = get_user_studio(user)
        if studio:
            return qs.filter(studio=studio)
        return Event.objects.none()


class EventCreateView(LoginRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = "events/event_create.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        user = request.user
        if user.role not in (User.Role.SUPER_ADMIN, User.Role.STUDIO_OWNER):
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        user = self.request.user
        if user.role == User.Role.STUDIO_OWNER:
            studio = get_user_studio(user)
            if studio:
                form.instance.studio = studio
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


class EventUpdateView(LoginRequiredMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = "events/event_update.html"
    context_object_name = "event"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        qs = super().get_queryset().select_related("studio", "studio__owner")
        user = self.request.user
        if user.role == User.Role.SUPER_ADMIN:
            return qs
        studio = get_user_studio(user)
        if studio:
            return qs.filter(studio=studio)
        return Event.objects.none()

    def get_success_url(self):
        return self.object.get_absolute_url()


class EventDeleteView(LoginRequiredMixin, DeleteView):
    model = Event
    template_name = "events/event_delete.html"
    context_object_name = "event"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    success_url = reverse_lazy("events:event_list")

    def get_queryset(self):
        qs = super().get_queryset().select_related("studio", "studio__owner")
        user = self.request.user
        if user.role == User.Role.SUPER_ADMIN:
            return qs
        studio = get_user_studio(user)
        if studio:
            return qs.filter(studio=studio)
        return Event.objects.none()
