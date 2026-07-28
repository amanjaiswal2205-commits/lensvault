from django.shortcuts import render
from django.urls import reverse

from apps.cms.models import (
    CTASection,
    Feature,
    GalleryShowcase,
    HeroSection,
    TrustSection,
    WorkflowSection,
    WorkflowStep,
)


def home(request):
    hero_section = HeroSection.objects.filter(is_active=True).first()
    features = Feature.objects.filter(is_active=True).order_by("display_order", "pk")
    workflow_section = WorkflowSection.objects.filter(is_active=True).first()
    workflow_steps = WorkflowStep.objects.filter(is_active=True).order_by("display_order", "pk")
    trust_section = TrustSection.objects.filter(is_active=True).first()
    trust_items = []
    if trust_section:
        trust_items = trust_section.items.filter(is_active=True).order_by("display_order", "pk")
    cta_section = CTASection.objects.filter(is_active=True).first()
    cta_section_inactive = CTASection.objects.filter(is_active=False).exists()
    gallery_showcase = GalleryShowcase.objects.filter(is_active=True).first()
    gallery_showcase_inactive = GalleryShowcase.objects.filter(is_active=False).exists()

    hero_rotating_words = []
    if hero_section and hero_section.rotating_words:
        hero_rotating_words = [
            word.strip()
            for word in hero_section.rotating_words.split(",")
            if word.strip()
        ]

    showcase_galleries = []
    if gallery_showcase:
        galleries = []
        if gallery_showcase.featured_gallery:
            galleries.append(gallery_showcase.featured_gallery)
        galleries.extend(list(gallery_showcase.selected_galleries.all())[:5])

        for gallery in galleries:
            image_url = None
            if hasattr(gallery, 'event') and gallery.event:
                first_media = gallery.event.media.filter(media_type='image', status='active').first()
                if first_media and first_media.thumbnail:
                    image_url = first_media.thumbnail.url
            if not image_url:
                image_url = 'https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=1200&q=80'
            showcase_galleries.append({
                'gallery': gallery,
                'image_url': image_url,
                'url': reverse('gallery:event_gallery'),
            })

    context = {
        "hero_section": hero_section,
        "hero_rotating_words": hero_rotating_words,
        "features": features,
        "workflow_section": workflow_section,
        "workflow_steps": workflow_steps,
        "trust_section": trust_section,
        "trust_items": trust_items,
        "cta_section": cta_section,
        "cta_section_inactive": cta_section_inactive,
        "gallery_showcase": gallery_showcase,
        "gallery_showcase_inactive": gallery_showcase_inactive,
        "showcase_galleries": showcase_galleries,
    }
    return render(request, "core/home.html", context)
