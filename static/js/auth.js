(function () {
  "use strict";

  // Show / Hide password toggles
  document.querySelectorAll("[data-password-toggle]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const input = document.getElementById(btn.getAttribute("data-password-toggle"));
      if (!input) return;
      const isPassword = input.type === "password";
      input.type = isPassword ? "text" : "password";
      btn.setAttribute("aria-pressed", String(isPassword));
      const icon = btn.querySelector("[data-icon]");
      if (icon) icon.textContent = isPassword ? "🙈" : "👁";
    });
  });

  // Password strength indicator
  document.querySelectorAll("[data-password-strength]").forEach(function (input) {
    const bar = document.getElementById(input.getAttribute("data-password-strength"));
    const label = bar ? bar.parentElement.querySelector("[data-strength-label]") : null;
    const checks = {
      length: false,
      upper: false,
      lower: false,
      number: false,
      special: false,
    };

    function score() {
      return Object.values(checks).filter(Boolean).length;
    }

    function paint() {
      const s = score();
      const colors = ["bg-red-500", "bg-red-500", "bg-yellow-500", "bg-yellow-500", "bg-blue-500", "bg-green-500"];
      const labels = ["", "Very weak", "Weak", "Fair", "Good", "Strong"];
      bar.className = "h-1.5 rounded-full transition-all duration-300 " + (colors[s] || "bg-gray-200");
      bar.style.width = (s / 5) * 100 + "%";
      if (label) {
        label.textContent = labels[s] || "";
        label.className = "text-xs " + (s >= 4 ? "text-green-600" : s >= 3 ? "text-blue-600" : "text-gray-500");
      }
    }

    input.addEventListener("input", function () {
      const v = input.value;
      checks.length = v.length >= 8;
      checks.upper = /[A-Z]/.test(v);
      checks.lower = /[a-z]/.test(v);
      checks.number = /[0-9]/.test(v);
      checks.special = /[^A-Za-z0-9]/.test(v);
      paint();
    });
    paint();
  });

  // Loading button: disable + spinner on form submit
  document.querySelectorAll("form[data-loading]").forEach(function (form) {
    form.addEventListener("submit", function () {
      form.querySelectorAll("button[type=submit][data-loading-btn]").forEach(function (btn) {
        btn.disabled = true;
        btn.classList.add("opacity-70", "cursor-not-allowed");
        const span = btn.querySelector("[data-loading-label]");
        const orig = span ? span.textContent : null;
        if (span) span.textContent = "Please wait...";
        if (span) btn._origLabel = orig;
      });
    });
  });
})();
