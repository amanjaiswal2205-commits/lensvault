from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.accounts.decorators import get_user_studio
from apps.accounts.models import User
from apps.gallery.forms import ClientGalleryForm
from apps.gallery.models import ClientGallery


class ClientGalleryListView(LoginRequiredMixin, ListView):
    model = ClientGallery
    template_name = "gallery/manage/gallery_list.html"
    context_object_name = "galleries"
    paginate_by = 12

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if request.user.role == User.Role.CLIENT:
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = ClientGallery.objects.select_related("event", "event__studio", "event__studio__owner").all()
        user = self.request.user

        if user.role == User.Role.SUPER_ADMIN:
            pass
        elif user.role in (User.Role.STUDIO_OWNER, User.Role.STAFF):
            studio = get_user_studio(user)
            if studio:
                qs = qs.filter(event__studio=studio)
            else:
                return ClientGallery.objects.none()
        else:
            return ClientGallery.objects.none()

        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create_url"] = reverse_lazy("gallery:gallery_manage_create")
        return context


class ClientGalleryCreateView(LoginRequiredMixin, CreateView):
    model = ClientGallery
    form_class = ClientGalleryForm
    template_name = "gallery/manage/gallery_form.html"
    context_object_name = "gallery"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        user = request.user
        if user.role == User.Role.CLIENT:
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
        return reverse_lazy("gallery:gallery_manage_list")


class ClientGalleryDetailView(LoginRequiredMixin, DetailView):
    model = ClientGallery
    template_name = "gallery/manage/gallery_detail.html"
    context_object_name = "gallery"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if request.user.role == User.Role.CLIENT:
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset().select_related("event", "event__studio", "event__studio__owner")
        user = self.request.user
        if user.role == User.Role.SUPER_ADMIN:
            return qs
        studio = get_user_studio(user)
        if studio:
            return qs.filter(event__studio=studio)
        return ClientGallery.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gallery = self.object
        context["public_url"] = reverse("public_gallery", kwargs={"share_token": gallery.share_token})
        return context


class ClientGalleryUpdateView(LoginRequiredMixin, UpdateView):
    model = ClientGallery
    form_class = ClientGalleryForm
    template_name = "gallery/manage/gallery_form.html"
    context_object_name = "gallery"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if request.user.role == User.Role.CLIENT:
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset().select_related("event", "event__studio", "event__studio__owner")
        user = self.request.user
        if user.role == User.Role.SUPER_ADMIN:
            return qs
        studio = get_user_studio(user)
        if studio:
            return qs.filter(event__studio=studio)
        return ClientGallery.objects.none()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        if user.role == User.Role.STUDIO_OWNER:
            studio = get_user_studio(user)
            if studio and form.instance.event.studio_id and form.instance.event.studio_id != studio.id:
                form.instance.event = self.object.event
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("gallery:gallery_manage_detail", kwargs={"slug": self.object.slug})


class ClientGalleryDeleteView(LoginRequiredMixin, DeleteView):
    model = ClientGallery
    template_name = "gallery/manage/gallery_confirm_delete.html"
    context_object_name = "gallery"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    success_url = reverse_lazy("gallery:gallery_manage_list")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if request.user.role == User.Role.CLIENT:
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset().select_related("event", "event__studio", "event__studio__owner")
        user = self.request.user
        if user.role == User.Role.SUPER_ADMIN:
            return qs
        studio = get_user_studio(user)
        if studio:
            return qs.filter(event__studio=studio)
        return ClientGallery.objects.none()
