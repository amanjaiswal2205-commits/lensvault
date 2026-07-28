from django.db import models
from django.core.validators import URLValidator
from django.utils.translation import gettext_lazy as _


class BaseCMSModel(models.Model):
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_("Show this record on the site."),
    )
    display_order = models.PositiveIntegerField(
        _("display order"),
        default=0,
        help_text=_("Lower numbers appear first."),
    )
    created_at = models.DateTimeField(
        _("created at"),
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        _("updated at"),
        auto_now=True,
    )

    class Meta:
        abstract = True
        ordering = ["display_order", "-pk"]

    def __str__(self):
        return getattr(self, "title", getattr(self, "heading", str(self.pk)))


class SiteSettings(models.Model):
    # General
    site_name = models.CharField(
        _("site name"),
        max_length=255,
        default="LensVault",
        help_text=_("The name of the site displayed in the header and title tags."),
    )
    site_tagline = models.CharField(
        _("site tagline"),
        max_length=255,
        blank=True,
        help_text=_("A short tagline shown below the site name."),
    )
    site_description = models.TextField(
        _("site description"),
        blank=True,
        help_text=_("A brief description of the site for SEO and meta tags."),
    )

    # Branding
    logo = models.ImageField(
        _("logo"),
        upload_to="cms/logo/",
        blank=True,
        null=True,
        help_text=_("Upload the site logo. Recommended size: 200x200px."),
    )
    favicon = models.ImageField(
        _("favicon"),
        upload_to="cms/favicon/",
        blank=True,
        null=True,
        help_text=_("Upload the favicon. Recommended size: 64x64px."),
    )

    # Contact
    support_email = models.EmailField(
        _("support email"),
        blank=True,
        help_text=_("Email address for customer support."),
    )
    phone = models.CharField(
        _("phone"),
        max_length=20,
        blank=True,
        help_text=_("Contact phone number."),
    )
    address = models.TextField(
        _("address"),
        blank=True,
        help_text=_("Physical address of the business."),
    )

    # Social
    facebook_url = models.URLField(
        _("Facebook URL"),
        blank=True,
        help_text=_("Link to the Facebook page."),
    )
    instagram_url = models.URLField(
        _("Instagram URL"),
        blank=True,
        help_text=_("Link to the Instagram profile."),
    )
    youtube_url = models.URLField(
        _("YouTube URL"),
        blank=True,
        help_text=_("Link to the YouTube channel."),
    )
    linkedin_url = models.URLField(
        _("LinkedIn URL"),
        blank=True,
        help_text=_("Link to the LinkedIn profile."),
    )

    # Status
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_("Only one active SiteSettings record should exist at a time."),
    )

    class Meta:
        verbose_name = _("site settings")
        verbose_name_plural = _("site settings")
        ordering = ["-pk"]

    def __str__(self):
        return self.site_name or "Site Settings"


class HeroSection(BaseCMSModel):
    # Content
    badge_text = models.CharField(
        _("badge text"),
        max_length=255,
        blank=True,
        help_text=_("Small text displayed above the main heading."),
    )
    heading = models.CharField(
        _("heading"),
        max_length=255,
        help_text=_("Main hero heading."),
    )
    subtitle = models.TextField(
        _("subtitle"),
        blank=True,
        help_text=_("Supporting text displayed below the heading."),
    )

    # Buttons
    primary_button_text = models.CharField(
        _("primary button text"),
        max_length=255,
        blank=True,
        help_text=_("Text for the primary call-to-action button."),
    )
    primary_button_url = models.CharField(
        _("primary button URL"),
        max_length=255,
        blank=True,
        help_text=_("URL for the primary button."),
    )
    secondary_button_text = models.CharField(
        _("secondary button text"),
        max_length=255,
        blank=True,
        help_text=_("Text for the secondary button."),
    )
    secondary_button_url = models.CharField(
        _("secondary button URL"),
        max_length=255,
        blank=True,
        help_text=_("URL for the secondary button."),
    )

    # Media
    hero_image = models.ImageField(
        _("hero image"),
        upload_to="cms/hero/",
        blank=True,
        null=True,
        help_text=_("Main hero image shown in the visual area."),
    )
    background_image = models.ImageField(
        _("background image"),
        upload_to="cms/hero/",
        blank=True,
        null=True,
        help_text=_("Background image for the hero section."),
    )

    # Statistics
    stat_1_number = models.CharField(
        _("statistic 1 number"),
        max_length=50,
        blank=True,
        help_text=_("First statistic value, e.g. 2500+."),
    )
    stat_1_label = models.CharField(
        _("statistic 1 label"),
        max_length=255,
        blank=True,
        help_text=_("First statistic label, e.g. Photos."),
    )
    stat_2_number = models.CharField(
        _("statistic 2 number"),
        max_length=50,
        blank=True,
        help_text=_("Second statistic value, e.g. 150."),
    )
    stat_2_label = models.CharField(
        _("statistic 2 label"),
        max_length=255,
        blank=True,
        help_text=_("Second statistic label, e.g. Events."),
    )
    stat_3_number = models.CharField(
        _("statistic 3 number"),
        max_length=50,
        blank=True,
        help_text=_("Third statistic value, e.g. 98%."),
    )
    stat_3_label = models.CharField(
        _("statistic 3 label"),
        max_length=255,
        blank=True,
        help_text=_("Third statistic label, e.g. Client Satisfaction."),
    )
    rotating_words = models.CharField(
        _("rotating words"),
        max_length=255,
        blank=True,
        help_text=_("Comma-separated words for the rotating text animation, e.g. Timeless., Personal., Unforgettable."),
    )

    class Meta(BaseCMSModel.Meta):
        verbose_name = _("hero section")
        verbose_name_plural = _("hero sections")

    def __str__(self):
        return self.heading or "Hero Section"


class Feature(BaseCMSModel):
    title = models.CharField(
        _("title"),
        max_length=255,
        help_text=_("Feature card title."),
    )
    description = models.TextField(
        _("description"),
        help_text=_("Short description shown inside the feature card."),
    )
    icon = models.CharField(
        _("icon"),
        max_length=255,
        blank=True,
        help_text=_("Emoji or icon string, e.g. 📅, 🖼️, 🔒."),
    )
    icon_background = models.CharField(
        _("icon background"),
        max_length=50,
        default="primary",
        help_text=_("Background style for the icon container. Recommended value: primary."),
    )
    accent_color = models.CharField(
        _("accent color"),
        max_length=50,
        blank=True,
        help_text=_("Optional accent color override for this feature card."),
    )
    link = models.CharField(
        _("link"),
        max_length=255,
        blank=True,
        help_text=_("Optional URL when the feature card is clicked."),
    )
    button_text = models.CharField(
        _("button text"),
        max_length=255,
        blank=True,
        help_text=_("Optional CTA button text for this feature card."),
    )
    is_featured = models.BooleanField(
        _("featured"),
        default=False,
        help_text=_("Highlight this feature in a featured area if supported."),
    )

    class Meta(BaseCMSModel.Meta):
        verbose_name = _("feature")
        verbose_name_plural = _("features")

    def __str__(self):
        return self.title


class MediaAsset(BaseCMSModel):
    class MediaType(models.TextChoices):
        IMAGE = "image", _("Image")
        VIDEO = "video", _("Video")
        DOCUMENT = "document", _("Document")

    title = models.CharField(
        _("title"),
        max_length=255,
        help_text=_("Human-readable name for this media asset."),
    )
    file = models.FileField(
        _("file"),
        upload_to="cms/media/",
        help_text=_("Upload the media file."),
    )
    alt_text = models.CharField(
        _("alt text"),
        max_length=255,
        blank=True,
        help_text=_("Alternative text for accessibility and SEO."),
    )
    media_type = models.CharField(
        _("media type"),
        max_length=20,
        choices=MediaType.choices,
        default=MediaType.IMAGE,
        help_text=_("Type of media asset."),
    )
    category = models.CharField(
        _("category"),
        max_length=100,
        blank=True,
        help_text=_("Optional category for grouping assets."),
    )
    tags = models.CharField(
        _("tags"),
        max_length=255,
        blank=True,
        help_text=_("Comma-separated tags for filtering."),
    )
    is_public = models.BooleanField(
        _("public"),
        default=True,
        help_text=_("Allow this asset to be used on public pages."),
    )

    class Meta(BaseCMSModel.Meta):
        verbose_name = _("media asset")
        verbose_name_plural = _("media assets")
        ordering = ["display_order", "-pk"]

    def __str__(self):
        return self.title


class SEOSettings(BaseCMSModel):
    page_key = models.CharField(
        _("page key"),
        max_length=100,
        unique=True,
        help_text=_("Unique identifier for this page, e.g. home, events, gallery."),
    )
    meta_title = models.CharField(
        _("meta title"),
        max_length=255,
        blank=True,
        help_text=_("Title shown in browser tab and search results."),
    )
    meta_description = models.TextField(
        _("meta description"),
        blank=True,
        help_text=_("Short description for search engines."),
    )
    meta_keywords = models.CharField(
        _("meta keywords"),
        max_length=255,
        blank=True,
        help_text=_("Comma-separated keywords for search engines."),
    )
    og_title = models.CharField(
        _("Open Graph title"),
        max_length=255,
        blank=True,
        help_text=_("Title used when sharing on social media."),
    )
    og_description = models.TextField(
        _("Open Graph description"),
        blank=True,
        help_text=_("Description used when sharing on social media."),
    )
    og_image = models.ImageField(
        _("Open Graph image"),
        upload_to="cms/seo/",
        blank=True,
        null=True,
        help_text=_("Image shown when sharing on social media."),
    )
    canonical_url = models.URLField(
        _("canonical URL"),
        blank=True,
        help_text=_("Preferred URL for this page to avoid duplicate content issues."),
    )
    robots = models.CharField(
        _("robots"),
        max_length=255,
        blank=True,
        help_text=_("Search engine crawl instructions, e.g. index, follow."),
    )

    class Meta(BaseCMSModel.Meta):
        verbose_name = _("SEO settings")
        verbose_name_plural = _("SEO settings")
        ordering = ["page_key"]

    def __str__(self):
        return self.page_key


class ThemeSettings(BaseCMSModel):
    theme_name = models.CharField(
        _("theme name"),
        max_length=255,
        help_text=_("Name of the theme, e.g. Default, Dark, Ocean."),
    )
    primary_color = models.CharField(
        _("primary color"),
        max_length=10,
        default="#6366f1",
        help_text=_("Main brand color in hex format. Default: #6366f1."),
    )
    secondary_color = models.CharField(
        _("secondary color"),
        max_length=10,
        default="#8b5cf6",
        help_text=_("Secondary brand color in hex format. Default: #8b5cf6."),
    )
    accent_color = models.CharField(
        _("accent color"),
        max_length=10,
        default="#f59e0b",
        help_text=_("Accent color in hex format. Default: #f59e0b."),
    )
    font_family = models.CharField(
        _("font family"),
        max_length=100,
        default="Inter",
        help_text=_("Primary font family for the theme."),
    )
    heading_font = models.CharField(
        _("heading font"),
        max_length=100,
        default="Inter",
        help_text=_("Font family for headings."),
    )
    body_font = models.CharField(
        _("body font"),
        max_length=100,
        default="Inter",
        help_text=_("Font family for body text."),
    )
    border_radius = models.CharField(
        _("border radius"),
        max_length=50,
        choices=[
            ("none", _("None")),
            ("sm", _("Small")),
            ("md", _("Medium")),
            ("lg", _("Large")),
            ("xl", _("Extra Large")),
            ("full", _("Full")),
        ],
        default="lg",
        help_text=_("Corner radius for cards, buttons, and inputs."),
    )
    button_style = models.CharField(
        _("button style"),
        max_length=20,
        choices=[
            ("rounded", _("Rounded")),
            ("square", _("Square")),
            ("pill", _("Pill")),
        ],
        default="rounded",
        help_text=_("Global button shape style."),
    )
    container_width = models.IntegerField(
        _("container max width"),
        default=1280,
        help_text=_("Maximum content width in pixels. Default: 1280."),
    )
    card_shadow = models.CharField(
        _("card shadow"),
        max_length=50,
        choices=[
            ("none", _("None")),
            ("sm", _("Small")),
            ("md", _("Medium")),
            ("lg", _("Large")),
            ("xl", _("Extra Large")),
        ],
        default="md",
        help_text=_("Shadow depth for cards."),
    )
    glass_effect_enabled = models.BooleanField(
        _("glass effect enabled"),
        default=True,
        help_text=_("Enable glassmorphism effects on cards and navbars."),
    )
    is_default = models.BooleanField(
        _("default"),
        default=False,
        help_text=_("Only one default theme can exist."),
    )

    class Meta(BaseCMSModel.Meta):
        verbose_name = _("theme settings")
        verbose_name_plural = _("theme settings")
        ordering = ["-is_default", "display_order", "-pk"]

    def __str__(self):
        return self.theme_name

    @property
    def border_radius_css(self):
        mapping = {
            "none": "0",
            "sm": "0.125rem",
            "md": "0.375rem",
            "lg": "0.5rem",
            "xl": "0.75rem",
            "full": "9999px",
        }
        return mapping.get(self.border_radius, "0.5rem")

    @property
    def card_shadow_css(self):
        mapping = {
            "none": "none",
            "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
            "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)",
            "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)",
            "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)",
        }
        return mapping.get(self.card_shadow, "0 4px 6px -1px rgba(0, 0, 0, 0.1)")

    @property
    def button_border_radius_css(self):
        mapping = {
            "rounded": "0.5rem",
            "square": "0",
            "pill": "9999px",
        }
        return mapping.get(self.button_style, "0.5rem")


class WorkflowSection(BaseCMSModel):
    eyebrow = models.CharField(
        _("eyebrow"),
        max_length=255,
        blank=True,
        help_text=_("Small text above the workflow heading."),
    )
    heading = models.CharField(
        _("heading"),
        max_length=255,
        help_text=_("Main workflow section heading."),
    )
    subtitle = models.TextField(
        _("subtitle"),
        blank=True,
        help_text=_("Supporting text below the heading."),
    )

    class Meta(BaseCMSModel.Meta):
        verbose_name = _("workflow section")
        verbose_name_plural = _("workflow sections")
        ordering = ["-pk"]

    def __str__(self):
        return self.heading or "Workflow Section"


class WorkflowStep(BaseCMSModel):
    title = models.CharField(
        _("title"),
        max_length=255,
        help_text=_("Workflow step title."),
    )
    description = models.TextField(
        _("description"),
        help_text=_("Short description shown for this step."),
    )
    icon = models.CharField(
        _("icon"),
        max_length=255,
        blank=True,
        help_text=_("Emoji or icon string, e.g. 📅, 🖼️, 🔒."),
    )

    class Meta(BaseCMSModel.Meta):
        verbose_name = _("workflow step")
        verbose_name_plural = _("workflow steps")
        ordering = ["display_order", "-pk"]

    def __str__(self):
        return self.title


class TrustSection(BaseCMSModel):
    eyebrow = models.CharField(
        _("eyebrow"),
        max_length=255,
        blank=True,
        help_text=_("Small text above the trust heading."),
    )
    heading = models.CharField(
        _("heading"),
        max_length=255,
        help_text=_("Main trust section heading."),
    )
    subtitle = models.TextField(
        _("subtitle"),
        blank=True,
        help_text=_("Supporting text below the heading."),
    )
    hub_label = models.CharField(
        _("hub label"),
        max_length=255,
        blank=True,
        help_text=_("Optional label shown near the center hub."),
    )

    class Meta(BaseCMSModel.Meta):
        verbose_name = _("trust section")
        verbose_name_plural = _("trust sections")
        ordering = ["-pk"]

    def __str__(self):
        return self.heading or "Trust Section"


class TrustItem(BaseCMSModel):
    section = models.ForeignKey(
        TrustSection,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("section"),
        help_text=_("The trust section this item belongs to."),
    )
    title = models.CharField(
        _("title"),
        max_length=255,
        help_text=_("Trust card title."),
    )
    description = models.TextField(
        _("description"),
        help_text=_("Short description shown inside the trust card."),
    )
    badge = models.CharField(
        _("badge"),
        max_length=50,
        blank=True,
        help_text=_("Small status badge, e.g. ENCRYPTED, FAST."),
    )
    icon = models.CharField(
        _("icon"),
        max_length=255,
        blank=True,
        help_text=_("Emoji or icon string, e.g. 🔒, ⚡, 🔗, ✨."),
    )

    class Meta(BaseCMSModel.Meta):
        verbose_name = _("trust item")
        verbose_name_plural = _("trust items")
        ordering = ["display_order", "-pk"]

    def __str__(self):
        return self.title


class CTASection(BaseCMSModel):
    heading = models.CharField(
        _("heading"),
        max_length=255,
        help_text=_("Main CTA heading."),
    )
    description = models.TextField(
        _("description"),
        blank=True,
        help_text=_("Supporting text below the heading."),
    )
    primary_button_text = models.CharField(
        _("primary button text"),
        max_length=255,
        blank=True,
        help_text=_("Text for the primary button."),
    )
    primary_button_url = models.CharField(
        _("primary button URL"),
        max_length=255,
        blank=True,
        help_text=_("URL for the primary button."),
    )
    secondary_button_text = models.CharField(
        _("secondary button text"),
        max_length=255,
        blank=True,
        help_text=_("Text for the secondary button."),
    )
    secondary_button_url = models.CharField(
        _("secondary button URL"),
        max_length=255,
        blank=True,
        help_text=_("URL for the secondary button."),
    )

    class Meta(BaseCMSModel.Meta):
        verbose_name = _("CTA section")
        verbose_name_plural = _("CTA sections")
        ordering = ["-pk"]

    def __str__(self):
        return self.heading or "CTA Section"


class GalleryShowcase(BaseCMSModel):
    eyebrow = models.CharField(
        _("eyebrow"),
        max_length=255,
        blank=True,
        help_text=_("Small text above the gallery heading."),
    )
    heading = models.CharField(
        _("heading"),
        max_length=255,
        help_text=_("Main gallery section heading."),
    )
    subtitle = models.TextField(
        _("subtitle"),
        blank=True,
        help_text=_("Supporting text below the heading."),
    )
    featured_gallery = models.ForeignKey(
        "gallery.ClientGallery",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="featured_gallery_showcase",
        verbose_name=_("featured gallery"),
        help_text=_("The main featured gallery displayed prominently."),
    )
    selected_galleries = models.ManyToManyField(
        "gallery.ClientGallery",
        blank=True,
        related_name="gallery_showcases",
        verbose_name=_("selected galleries"),
        help_text=_("Additional galleries to display in the showcase."),
    )

    class Meta(BaseCMSModel.Meta):
        verbose_name = _("gallery showcase")
        verbose_name_plural = _("gallery showcases")
        ordering = ["-pk"]

    def __str__(self):
        return self.heading or "Gallery Showcase"
