// ─────────────────────────────────────────
// FILING TYPE SELECTOR
// ─────────────────────────────────────────
function selectFiling(type) {
  // Deselect all cards
  document.querySelectorAll(".filing-card").forEach((card) => {
    card.classList.remove("selected");
  });

  // Select clicked card
  const selected = document.querySelector(`[data-type="${type}"]`);
  if (selected) selected.classList.add("selected");

  // Hide all forms
  document.querySelectorAll(".filing-form").forEach((form) => {
    form.style.display = "none";
  });

  // Show the matching form
  const formEl = document.getElementById(`form-${type}`);
  if (formEl) {
    formEl.style.display = "block";
  }

  // Show form area with smooth scroll
  const formArea = document.getElementById("form-area");
  if (formArea) {
    formArea.style.display = "block";
    setTimeout(() => {
      formArea.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
  }

  // Update step strip
  document.querySelectorAll(".step-item").forEach((s, i) => {
    s.classList.toggle("active", i === 1);
  });
}

// ─────────────────────────────────────────
// TAB SWITCHER (Upload vs Manual)
// ─────────────────────────────────────────
function switchTab(tab, event) {
  const parentCard = event.target.closest(".card");
  if (!parentCard) return;

  parentCard
    .querySelectorAll(".tab-content")
    .forEach((t) => t.classList.remove("active"));
  parentCard
    .querySelectorAll(".tab-btn")
    .forEach((b) => b.classList.remove("active"));

  const targetTab = parentCard.querySelector(`#tab-${tab}`);
  if (targetTab) targetTab.classList.add("active");
  event.target.classList.add("active");
}

// ─────────────────────────────────────────
// DRAG & DROP FILE UPLOAD
// ─────────────────────────────────────────
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("p9_file");
const fileSelected = document.getElementById("file-selected");
const fileNameEl = document.getElementById("file-name");

if (dropZone) {
  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    const file = e.dataTransfer.files[0];
    if (file && file.type === "application/pdf") {
      applyFile(file);
    } else {
      showToast("Please drop a PDF file only.");
    }
  });
}

if (fileInput) {
  fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) applyFile(fileInput.files[0]);
  });
}

function applyFile(file) {
  const defaultContent = dropZone.querySelector(".drop-zone-default");
  if (defaultContent) defaultContent.style.display = "none";
  if (fileSelected) {
    fileSelected.style.display = "flex";
    if (fileNameEl) fileNameEl.textContent = file.name;
  }
  // Update step strip
  document.querySelectorAll(".step-item").forEach((s, i) => {
    s.classList.toggle("active", i === 1);
  });
}

// ─────────────────────────────────────────
// PROCESSING OVERLAY
// ─────────────────────────────────────────
const overlay = document.getElementById("processing-overlay");
const uploadForm = document.getElementById("upload-form");
const allForms = document.querySelectorAll(
  "#manual-form, #nil-form, #business-form, #rental-form, " +
    "#vat-form, #turnover-form, #cgt-form, #company-form",
);

function showProcessing() {
  if (overlay) {
    overlay.style.display = "flex";
    animateSteps();
  }
}

if (uploadForm) {
  uploadForm.addEventListener("submit", () => showProcessing());
}

allForms.forEach((form) => {
  form.addEventListener("submit", () => showProcessing());
});

// ─────────────────────────────────────────
// ANIMATE PROCESSING STEPS
// ─────────────────────────────────────────
function animateSteps() {
  const stepIds = ["proc-1", "proc-2", "proc-3", "proc-4"];
  let current = 0;

  const interval = setInterval(() => {
    // Mark previous as done
    if (current > 0) {
      const prev = document.getElementById(stepIds[current - 1]);
      if (prev) {
        prev.classList.remove("active");
        prev.classList.add("done");
        prev.querySelector(".proc-step-dot").textContent = "";
      }
    }

    if (current < stepIds.length) {
      const el = document.getElementById(stepIds[current]);
      if (el) el.classList.add("active");
      current++;
    } else {
      clearInterval(interval);
    }
  }, 2200);
}

// ─────────────────────────────────────────
// SIMPLE TOAST NOTIFICATION
// ─────────────────────────────────────────
function showToast(message) {
  const toast = document.createElement("div");
  toast.style.cssText = `
        position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
        background: #1A1A1A; color: white; padding: 12px 24px;
        border-radius: 999px; font-size: 0.85rem; z-index: 9999;
        font-family: 'DM Sans', sans-serif; box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    `;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}
