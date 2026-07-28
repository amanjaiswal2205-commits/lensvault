/**
 * LensVault Design System JavaScript
 * Premium SaaS Interactions
 */

(function() {
  'use strict';

  // Theme Toggle
  function initTheme() {
    const theme = localStorage.getItem('lv-theme') || 'light';
    document.documentElement.setAttribute('data-theme', theme);
    updateThemeIcon(theme);
  }

  function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('lv-theme', next);
    updateThemeIcon(next);
  }

  function updateThemeIcon(theme) {
    const icon = document.getElementById('theme-icon');
    if (icon) {
      icon.textContent = theme === 'light' ? '🌙' : '☀️';
    }
  }

  // Expose to global scope for inline handlers
  window.toggleTheme = toggleTheme;
  window.initTheme = initTheme;

  // Mobile Menu
  window.toggleMobileMenu = function() {
    const menu = document.getElementById('lv-mobile-menu');
    const btn = document.querySelector('.lv-navbar-toggle');
    menu.classList.toggle('lv-mobile-open');
    btn.classList.toggle('lv-active');
  };

  // Dropdown
  window.toggleDropdown = function(btn) {
    const dropdown = btn.closest('.lv-dropdown');
    dropdown.classList.toggle('open');
  };

  // Close dropdowns when clicking outside
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.lv-dropdown')) {
      document.querySelectorAll('.lv-dropdown.open').forEach(function(d) {
        d.classList.remove('open');
      });
    }
  });

  // Scroll Reveal
  function initScrollReveal() {
    const observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('lv-revealed');
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll('.lv-reveal').forEach(function(el) {
      observer.observe(el);
    });
  }

  // Smooth Scroll
  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
      anchor.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        if (href === '#') return;
        const target = document.querySelector(href);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    });
  }

  // Navbar scroll effect
  function initNavbarScroll() {
    const navbar = document.getElementById('lv-navbar');
    if (!navbar) return;

    let lastScroll = 0;
    window.addEventListener('scroll', function() {
      const currentScroll = window.pageYOffset;

      if (currentScroll > 50) {
        navbar.classList.add('lv-navbar-scrolled');
      } else {
        navbar.classList.remove('lv-navbar-scrolled');
      }

      lastScroll = currentScroll;
    });
  }

  // Loading Bar
  function showLoadingBar() {
    const bar = document.getElementById('lv-loading-bar');
    if (!bar) return;
    bar.style.width = '70%';
    bar.classList.remove('lv-loading-complete');
  }

  function hideLoadingBar() {
    const bar = document.getElementById('lv-loading-bar');
    if (!bar) return;
    bar.style.width = '100%';
    setTimeout(function() {
      bar.classList.add('lv-loading-complete');
    }, 400);
  }

  // Toast Notifications
  function showToast(message, type) {
    type = type || 'info';
    const container = document.querySelector('.lv-toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'lv-toast lv-toast-' + type;
    toast.innerHTML = '<span>' + message + '</span>';
    container.appendChild(toast);

    setTimeout(function() {
      toast.remove();
    }, 5000);
  }

  // Sidebar
  function initSidebar() {
    const sidebar = document.getElementById('lv-sidebar');
    if (!sidebar) return;

    const collapsed = localStorage.getItem('lv-sidebar-collapsed') === 'true';
    if (collapsed) {
      sidebar.classList.add('collapsed');
      const main = document.querySelector('.lv-main-content');
      if (main) main.classList.add('expanded');
    }

    const overlay = document.getElementById('lv-sidebar-overlay');
    if (overlay) {
      overlay.addEventListener('click', closeMobileSidebar);
    }

    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        closeMobileSidebar();
      }
    });
  }

  window.toggleSidebar = function() {
    const sidebar = document.getElementById('lv-sidebar');
    if (!sidebar) return;

    if (sidebar.classList.contains('lv-sidebar-open')) {
      closeMobileSidebar();
      return;
    }

    sidebar.classList.toggle('collapsed');
    const main = document.querySelector('.lv-main-content');
    if (main) main.classList.toggle('expanded');
    localStorage.setItem('lv-sidebar-collapsed', sidebar.classList.contains('collapsed'));
  };

  window.openMobileSidebar = function() {
    const sidebar = document.getElementById('lv-sidebar');
    const overlay = document.getElementById('lv-sidebar-overlay');
    if (!sidebar) return;
    sidebar.classList.add('lv-sidebar-open');
    if (overlay) overlay.classList.add('lv-sidebar-open');
    document.body.style.overflow = 'hidden';
  };

  window.closeMobileSidebar = function() {
    const sidebar = document.getElementById('lv-sidebar');
    const overlay = document.getElementById('lv-sidebar-overlay');
    if (sidebar) sidebar.classList.remove('lv-sidebar-open');
    if (overlay) overlay.classList.remove('lv-sidebar-open');
    document.body.style.overflow = '';
  };

  // Rotating Hero Text
  function initRotatingHeroText() {
    const el = document.getElementById('lv-rotating-text');
    if (!el) return;

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    const phrases = [
      'Timeless.',
      'Personal.',
      'Unforgettable.',
      'Beautiful.',
    ];

    let index = 0;
    const interval = 3200;

    setInterval(function() {
      el.style.opacity = '0';
      el.style.transform = 'translateY(8px)';

      setTimeout(function() {
        index = (index + 1) % phrases.length;
        el.textContent = phrases[index];
        el.style.opacity = '1';
        el.style.transform = 'translateY(0)';
      }, 350);
    }, interval);
  }

  function initFeatureShowcase() {
    const section = document.getElementById('lv-features-showcase');
    if (!section) return;

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion) {
      section.classList.add('lv-revealed');
      return;
    }

    if (!('IntersectionObserver' in window)) {
      section.classList.add('lv-revealed');
      return;
    }

    const observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('lv-revealed');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });

    if (observer) {
      observer.observe(section);

      if (section.getBoundingClientRect().top < window.innerHeight && section.getBoundingClientRect().bottom > 0) {
        section.classList.add('lv-revealed');
        observer.unobserve(section);
      }
    }
  }

  function initFeatureSlider() {
    const track = document.getElementById('lv-features-track');
    const prevBtn = document.getElementById('lv-features-prev');
    const nextBtn = document.getElementById('lv-features-next');
    if (!track || !prevBtn || !nextBtn) return;

    const card = track.querySelector('.lv-feature-card');
    if (!card) return;

    const gap = 24;
    const getScrollAmount = function() {
      return card.offsetWidth + gap;
    };

    prevBtn.addEventListener('click', function() {
      track.scrollBy({ left: -getScrollAmount(), behavior: 'smooth' });
    });

    nextBtn.addEventListener('click', function() {
      track.scrollBy({ left: getScrollAmount(), behavior: 'smooth' });
    });
  }

  function initFeatureTilt() {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    const cards = document.querySelectorAll('.lv-feature-card[data-tilt]');
    if (!cards.length) return;

    cards.forEach(function(card) {
      card.addEventListener('mousemove', function(e) {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        const rotateX = ((y - centerY) / centerY) * -2;
        const rotateY = ((x - centerX) / centerX) * 2;

        card.style.transform = 'perspective(800px) rotateX(' + rotateX + 'deg) rotateY(' + rotateY + 'deg) translateY(-10px) scale(1.02)';
      });

      card.addEventListener('mouseleave', function() {
        card.style.transform = '';
      });
    });
  }

  function initWorkflowSection() {
    const section = document.getElementById('lv-workflow-section');
    if (!section) return;

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion) {
      section.classList.add('lv-revealed');
      return;
    }

    if (!('IntersectionObserver' in window)) {
      section.classList.add('lv-revealed');
      return;
    }

    const observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('lv-revealed');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });

    if (section.getBoundingClientRect().top < window.innerHeight && section.getBoundingClientRect().bottom > 0) {
      section.classList.add('lv-revealed');
      return;
    }

    observer.observe(section);
  }

  function initGalleryShowcase() {
    const section = document.getElementById('lv-gallery-showcase');
    if (!section) return;

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion) {
      section.classList.add('lv-revealed');
      return;
    }

    if (!('IntersectionObserver' in window)) {
      section.classList.add('lv-revealed');
      return;
    }

    const observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('lv-revealed');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    if (section.getBoundingClientRect().top < window.innerHeight && section.getBoundingClientRect().bottom > 0) {
      section.classList.add('lv-revealed');
      return;
    }

    observer.observe(section);
  }

  function initGalleryParallax() {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    const cards = document.querySelectorAll('.lv-gallery-card[data-parallax]');
    if (!cards.length) return;

    cards.forEach(function(card) {
      const img = card.querySelector('.lv-gallery-image-wrap img');
      if (!img) return;

      card.addEventListener('mousemove', function(e) {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        const rotateX = ((y - centerY) / centerY) * -1.5;
        const rotateY = ((x - centerX) / centerX) * 1.5;
        const moveX = ((x - centerX) / centerX) * -4;
        const moveY = ((y - centerY) / centerY) * -4;

        card.style.transform = 'perspective(800px) rotateX(' + rotateX + 'deg) rotateY(' + rotateY + 'deg) translateY(-8px) scale(1.01)';
        img.style.transform = 'translate(' + moveX + 'px, ' + moveY + 'px) scale(1.06)';
      });

      card.addEventListener('mouseleave', function() {
        card.style.transform = '';
        img.style.transform = '';
      });
    });
  }

  function initTrustSection() {
    const section = document.getElementById('lv-trust-section');
    if (!section) return;

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion) {
      section.classList.add('lv-revealed');
      return;
    }

    if (!('IntersectionObserver' in window)) {
      section.classList.add('lv-revealed');
      return;
    }

    const observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('lv-revealed');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });

    if (section.getBoundingClientRect().top < window.innerHeight && section.getBoundingClientRect().bottom > 0) {
      section.classList.add('lv-revealed');
      return;
    }

    observer.observe(section);
  }

  function initTrustSpotlight() {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    const section = document.getElementById('lv-trust-section');
    if (!section) return;

    const spotlight = section.querySelector('.lv-trust-spotlight');
    if (!spotlight) return;

    section.addEventListener('pointermove', function(e) {
      const rect = section.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      spotlight.style.setProperty('--mouse-x', x + '%');
      spotlight.style.setProperty('--mouse-y', y + '%');
      spotlight.style.opacity = '1';
    });

    section.addEventListener('pointerleave', function() {
      spotlight.style.opacity = '0';
    });
  }

  function initTrustConnectors() {
    const section = document.getElementById('lv-trust-section');
    if (!section) return;

    const consoleEl = section.querySelector('.lv-trust-console');
    if (!consoleEl) return;

    const svg = consoleEl.querySelector('.lv-trust-connectors');
    if (!svg) return;

    const hub = consoleEl.querySelector('.lv-trust-hub');
    const panels = Array.from(consoleEl.querySelectorAll('.lv-trust-panel'));
    if (!hub || panels.length !== 4) return;

    const ns = 'http://www.w3.org/2000/svg';
    const lines = [];
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function getCenter(el) {
      const rect = el.getBoundingClientRect();
      const consoleRect = consoleEl.getBoundingClientRect();
      return {
        x: rect.left + rect.width / 2 - consoleRect.left,
        y: rect.top + rect.height / 2 - consoleRect.top
      };
    }

    function drawLines() {
      svg.innerHTML = '';
      lines.length = 0;

      const hubCenter = getCenter(hub);

      panels.forEach(function(panel, i) {
        const panelCenter = getCenter(panel);
        const line = document.createElementNS(ns, 'line');
        line.setAttribute('x1', hubCenter.x);
        line.setAttribute('y1', hubCenter.y);
        line.setAttribute('x2', panelCenter.x);
        line.setAttribute('y2', panelCenter.y);
        line.classList.add('lv-trust-connector-line');
        if (prefersReducedMotion) {
          line.style.animation = 'none';
          line.setAttribute('stroke-dasharray', 'none');
        }
        svg.appendChild(line);
        lines.push(line);

        panel.addEventListener('mouseenter', function() {
          line.classList.add('lv-trust-connector-active');
          hub.classList.add('lv-trust-hub-active');
        });

        panel.addEventListener('mouseleave', function() {
          line.classList.remove('lv-trust-connector-active');
          hub.classList.remove('lv-trust-hub-active');
        });
      });
    }

    drawLines();
    let resizeTimeout;
    window.addEventListener('resize', function() {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(drawLines, 150);
    });
  }

  // Initialize
  document.addEventListener('DOMContentLoaded', function() {
    document.documentElement.classList.add('lv-motion-ready');

    initTheme();
    initScrollReveal();
    initSmoothScroll();
    initNavbarScroll();
    initSidebar();
    initRotatingHeroText();
    initFeatureShowcase();
    initFeatureSlider();
    initFeatureTilt();
    initWorkflowSection();
    initGalleryShowcase();
    initGalleryParallax();
    initTrustSection();
    initTrustSpotlight();
    initTrustConnectors();
  });

  // Loading bar for page transitions
  window.addEventListener('load', function() {
    hideLoadingBar();
  });

  window.addEventListener('beforeunload', function() {
    showLoadingBar();
  });

  // Expose toasts
  window.showToast = showToast;

})();
