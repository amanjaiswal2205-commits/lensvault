(function () {
  "use strict";

  function getCookie(name) {
    const match = document.cookie.match(new RegExp("(^|; )" + name + "=([^;]+)"));
    return match ? decodeURIComponent(match[2]) : "";
  }

  const CSRF_TOKEN = getCookie("csrftoken");

  // ----------------------------------------------------------------------
  // Load More (AJAX fragment from album_gallery media grid)
  // ----------------------------------------------------------------------
  const loadMoreBtn = document.getElementById("load-more");
  if (loadMoreBtn) {
    loadMoreBtn.addEventListener("click", function () {
      const nextPage = loadMoreBtn.dataset.nextPage;
      const eventSlug = loadMoreBtn.dataset.event;
      const album = loadMoreBtn.dataset.album;
      const search = loadMoreBtn.dataset.search;
      const grid = document.getElementById("media-grid");

      const params = new URLSearchParams({ page: nextPage });
      if (album) params.set("album", album);
      if (search) params.set("search", search);

      loadMoreBtn.disabled = true;
      loadMoreBtn.textContent = "Loading…";

      fetch(`/gallery/event/${eventSlug}/?${params.toString()}`, {
        headers: { "X-CSRFToken": CSRF_TOKEN, "X-Requested-With": "XMLHttpRequest" },
      })
        .then((r) => r.text())
        .then((html) => {
          // Parse fragment and append media cards
          const tmp = document.createElement("div");
          tmp.innerHTML = html;
          const cards = tmp.querySelectorAll("a.gallery-card");
          if (cards.length === 0 || html.includes("No media found")) {
            loadMoreBtn.remove();
            return;
          }
          cards.forEach((c) => grid.appendChild(c));

          // Detect if there's a next page by checking next-page marker
          const nextMatch = html.match(/data-next-page="(\d+)"/);
          if (nextMatch) {
            loadMoreBtn.dataset.nextPage = nextMatch[1];
            loadMoreBtn.disabled = false;
            loadMoreBtn.textContent = "Load More";
          } else {
            loadMoreBtn.remove();
          }
        })
        .catch(() => {
          loadMoreBtn.disabled = false;
          loadMoreBtn.textContent = "Load More";
        });
    });
  }

  // ----------------------------------------------------------------------
  // Lazy loading via IntersectionObserver (native loading="lazy" fallback)
  // ----------------------------------------------------------------------
  if ("IntersectionObserver" in window) {
    const lazyObserver = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const img = entry.target;
            if (img.dataset.src) {
              img.src = img.dataset.src;
              img.removeAttribute("data-src");
            }
            obs.unobserve(img);
          }
        });
      },
      { rootMargin: "200px" }
    );
    document.querySelectorAll("img[data-src]").forEach((img) => lazyObserver.observe(img));
  }

  // ----------------------------------------------------------------------
  // Clickable gallery cards -> media detail page
  // ----------------------------------------------------------------------
  document.querySelectorAll('.lv-media-card[data-media-uuid], .gallery-card[data-media-uuid]').forEach(function(card) {
    card.addEventListener('click', function(e) {
      if (e.target.closest('button') || e.target.closest('a')) return;
      var uuid = card.getAttribute('data-media-uuid');
      if (uuid) {
        window.location.href = '/gallery/media/' + uuid + '/';
      }
    });
  });

  // ----------------------------------------------------------------------
  // Image zoom & lightbox (detail page)
  // ----------------------------------------------------------------------
  const zoomable = document.getElementById("zoomable");
  if (zoomable) {
    const lightbox = document.getElementById("lightbox");
    let scale = 1;

    function openLightbox() {
      if (!lightbox) return;
      lightbox.classList.remove("hidden");
      lightbox.classList.add("flex");
    }

    function closeLightbox() {
      if (!lightbox) return;
      lightbox.classList.add("hidden");
      lightbox.classList.remove("flex");
    }

    function toggleZoom() {
      scale = scale === 1 ? 2.2 : 1;
      zoomable.style.transform = `scale(${scale})`;
      zoomable.classList.toggle("cursor-zoom-in", scale === 1);
      zoomable.classList.toggle("cursor-zoom-out", scale !== 1);
    }

    // Single click -> open lightbox
    zoomable.addEventListener("click", openLightbox);

    // Double click -> zoom
    zoomable.addEventListener("dblclick", function (e) {
      e.preventDefault();
      toggleZoom();
    });

    // Lightbox close / backdrop click
    if (lightbox) {
      lightbox.querySelector("#lightbox-close").addEventListener("click", closeLightbox);
      lightbox.addEventListener("click", function (e) {
        if (e.target === lightbox) closeLightbox();
      });

      // Prev / Next within lightbox navigate to the respective pages
      lightbox.querySelector("#lightbox-prev").addEventListener("click", function () {
        const link = document.getElementById("nav-prev");
        if (link) window.location.href = link.href;
      });
      lightbox.querySelector("#lightbox-next").addEventListener("click", function () {
        const link = document.getElementById("nav-next");
        if (link) window.location.href = link.href;
      });

      document.addEventListener("keydown", function (e) {
        if (lightbox.classList.contains("hidden")) {
          if (e.key === "ArrowLeft") {
            const prev = document.getElementById("nav-prev");
            if (prev) window.location.href = prev.href;
          } else if (e.key === "ArrowRight") {
            const next = document.getElementById("nav-next");
            if (next) window.location.href = next.href;
          }
        } else {
          if (e.key === "Escape") closeLightbox();
        }
      });
    }
  }

  // ----------------------------------------------------------------------
  // Video player keyboard: space play/pause, left/right seek
  // ----------------------------------------------------------------------
  const player = document.getElementById("media-player");
  if (player) {
    document.addEventListener("keydown", function (e) {
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
      if (e.key === " ") {
        e.preventDefault();
        if (player.paused) player.play();
        else player.pause();
      } else if (e.key === "ArrowRight") {
        player.currentTime = Math.min(player.duration, player.currentTime + 5);
      } else if (e.key === "ArrowLeft") {
        player.currentTime = Math.max(0, player.currentTime - 5);
      }
    });
  }

  // ----------------------------------------------------------------------
  // Favorites toggle
  // ----------------------------------------------------------------------
  const favoriteButtons = document.querySelectorAll(".favorite-btn");
  if (favoriteButtons.length > 0) {
    const gridEl = document.getElementById("photo-grid");
    const shareToken = gridEl ? gridEl.dataset.shareToken : null;

    favoriteButtons.forEach((btn) => {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        const photoUuid = btn.dataset.photoUuid;
        if (!photoUuid || !shareToken) return;

        const icon = btn.querySelector(".favorite-icon");
        const formData = new FormData();
        formData.append("photo_id", photoUuid);

        fetch(`/g/${shareToken}/favorite/`, {
          method: "POST",
          headers: { "X-CSRFToken": CSRF_TOKEN },
          body: formData,
        })
          .then((r) => r.json())
          .then((data) => {
            if (data.success) {
              icon.textContent = data.favorited ? "❤️" : "♡";
            }
          })
          .catch(() => {});
      });
    });
  }
})();
