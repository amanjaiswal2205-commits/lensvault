(function () {
  "use strict";

  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const browseBtn = document.getElementById("browse-btn");
  const albumSelect = document.getElementById("album-select");
  const albumError = document.getElementById("album-error");
  const queue = document.getElementById("queue");
  const rowTemplate = document.getElementById("row-template");
  const overall = document.getElementById("overall");
  const overallBar = document.getElementById("overall-bar");
  const overallPercent = document.getElementById("overall-percent");
  const overallLabel = document.getElementById("overall-label");

  const CSRF_TOKEN = getCookie("csrftoken");
  const ALLOWED = ["jpg", "jpeg", "png", "webp", "mp4", "mov", "avi", "mkv"];
  const IMAGE_EXTS = ["jpg", "jpeg", "png", "webp"];

  let activeUploads = 0;
  let completedCount = 0;
  let totalCount = 0;

  function getCookie(name) {
    const match = document.cookie.match(new RegExp("(^|; )" + name + "=([^;]+)"));
    return match ? decodeURIComponent(match[2]) : "";
  }

  function extOf(name) {
    const i = name.lastIndexOf(".");
    return i >= 0 ? name.slice(i + 1).toLowerCase() : "";
  }

  function showAlbumError(show) {
    if (albumError) albumError.classList.toggle("hidden", !show);
  }

  function setOverall() {
    if (totalCount === 0) {
      overall.classList.add("hidden");
      return;
    }
    overall.classList.remove("hidden");
    const pct = Math.round((completedCount / totalCount) * 100);
    overallBar.style.width = pct + "%";
    overallPercent.textContent = pct + "%";
    overallLabel.textContent =
      completedCount === totalCount
        ? "All uploads finished"
        : `Uploading ${activeUploads} of ${totalCount}…`;
  }

  function makeRow(file, valid) {
    const node = rowTemplate.content.firstElementChild.cloneNode(true);
    node.querySelector("[data-name]").textContent = file.name;

    const preview = node.querySelector("[data-preview]");
    if (valid && IMAGE_EXTS.includes(extOf(file.name))) {
      const url = URL.createObjectURL(file);
      preview.innerHTML = "";
      const img = document.createElement("img");
      img.src = url;
      img.className = "h-full w-full object-cover";
      preview.appendChild(img);
    } else if (valid) {
      preview.textContent = "🎬";
    } else {
      preview.textContent = "⛔";
    }

    queue.appendChild(node);
    return node;
  }

  function setBadge(row, kind, text) {
    const badge = row.querySelector("[data-badge]");
    badge.textContent = text;
    badge.className =
      "text-xs font-medium px-2 py-0.5 rounded-full " +
      (kind === "success"
        ? "bg-green-100 text-green-700"
        : kind === "error"
        ? "bg-red-100 text-red-700"
        : kind === "uploading"
        ? "bg-indigo-100 text-indigo-700"
        : "bg-gray-100 text-gray-600");
  }

  function setProgress(row, pct) {
    row.querySelector("[data-bar]").style.width = pct + "%";
  }

  function uploadFile(file, row) {
    const valid = ALLOWED.includes(extOf(file.name));
    const album = albumSelect.value;

    if (!valid) {
      row.dataset.state = "error";
      row.querySelector("[data-status]").textContent = "Rejected: unsupported file type";
      setBadge(row, "error", "Failed");
      finishOne();
      return;
    }
    if (!album) {
      showAlbumError(true);
      row.dataset.state = "error";
      row.querySelector("[data-status]").textContent = "Rejected: no album selected";
      setBadge(row, "error", "Failed");
      finishOne();
      return;
    }

    showAlbumError(false);
    const controller = new AbortController();
    row.dataset.controller = "1";
    row._abort = controller;
    row.dataset.state = "uploading";
    setBadge(row, "uploading", "Uploading");
    row.querySelector("[data-status]").textContent = "Uploading 0%";
    activeUploads++;

    const fd = new FormData();
    fd.append("album", album);
    fd.append("file", file);

    const xhr = new XMLHttpRequest();
    row._xhr = xhr;
    xhr.open("POST", window.location.pathname + "api/", true);
    xhr.setRequestHeader("X-CSRFToken", CSRF_TOKEN);
    xhr.timeout = 0;

    xhr.upload.addEventListener("progress", function (e) {
      if (e.lengthComputable) {
        const pct = Math.round((e.loaded / e.total) * 100);
        setProgress(row, pct);
        row.querySelector("[data-status]").textContent = "Uploading " + pct + "%";
      }
    });

    xhr.onload = function () {
      let data = {};
      try { data = JSON.parse(xhr.responseText); } catch (e) { data = {}; }
      if (xhr.status >= 200 && xhr.status < 300 && data.success) {
        row.dataset.state = "success";
        setProgress(row, 100);
        setBadge(row, "success", "Done");
        row.querySelector("[data-status]").textContent = "Uploaded successfully";
        row.querySelector("[data-cancel]").remove();
      } else {
        fail(row, data.error || ("Server error " + xhr.status));
      }
      finishOne();
    };

    xhr.onerror = function () {
      fail(row, "Network error");
      finishOne();
    };

    xhr.onabort = function () {
      row.dataset.state = "cancelled";
      setBadge(row, "error", "Cancelled");
      row.querySelector("[data-status]").textContent = "Upload cancelled";
      finishOne();
    };

    xhr.send(fd);
  }

  function fail(row, message) {
    row.dataset.state = "error";
    setBadge(row, "error", "Failed");
    row.querySelector("[data-status]").textContent = "Failed: " + message;
    // enable retry by restoring cancel button as retry
    const btn = row.querySelector("[data-cancel]");
    if (btn) {
      btn.textContent = "↻";
      btn.title = "Retry";
      btn.onclick = function () {
        row.dataset.state = "pending";
        setBadge(row, "", "Pending");
        row.querySelector("[data-status]").textContent = "Retrying…";
        fileInput._pending = fileInput._pending || [];
        uploadFile(row._file, row);
      };
    }
  }

  function finishOne() {
    activeUploads = Math.max(0, activeUploads - 1);
    completedCount++;
    setOverall();
  }

  function enqueue(files) {
    if (!files || !files.length) return;
    totalCount += files.length;
    setOverall();
    Array.from(files).forEach(function (file) {
      const valid = ALLOWED.includes(extOf(file.name));
      const row = makeRow(file, valid);
      row._file = file;
      uploadFile(file, row);
    });
  }

  // ---- Event wiring ----
  browseBtn.addEventListener("click", function () {
    fileInput.click();
  });
  dropzone.addEventListener("click", function (e) {
    if (e.target === dropzone || e.target.parentElement === dropzone) {
      fileInput.click();
    }
  });

  fileInput.addEventListener("change", function () {
    enqueue(fileInput.files);
    fileInput.value = "";
  });

  ["dragenter", "dragover"].forEach(function (evt) {
    dropzone.addEventListener(evt, function (e) {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add("dropzone-active");
    });
  });
  ["dragleave", "drop"].forEach(function (evt) {
    dropzone.addEventListener(evt, function (e) {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("dropzone-active");
    });
  });
  dropzone.addEventListener("drop", function (e) {
    const dt = e.dataTransfer;
    if (dt && dt.files && dt.files.length) {
      enqueue(dt.files);
    }
  });

  // Cancel / retry handling on dynamically created rows
  queue.addEventListener("click", function (e) {
    const btn = e.target.closest("[data-cancel]");
    if (!btn) return;
    const row = btn.closest(".upload-row");
    if (row.dataset.state === "uploading" || row.dataset.state === "pending") {
      if (row._xhr) row._xhr.abort();
      if (row._abort) row._abort.abort();
    }
  });

  // Prevent the whole window from navigating when files are dropped outside the zone
  ["dragover", "drop"].forEach(function (evt) {
    window.addEventListener(evt, function (e) {
      if (e.target !== dropzone && !dropzone.contains(e.target)) {
        e.preventDefault();
      }
    });
  });
})();
