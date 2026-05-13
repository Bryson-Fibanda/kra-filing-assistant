// ─────────────────────────────────────────
// SWAHILI TOGGLE
// Regenerates the filing guide in Swahili
// ─────────────────────────────────────────

let currentLanguage = "english";

function initSwahiliToggle() {
  const toggle = document.getElementById("swahili-toggle");
  if (!toggle) return;

  toggle.addEventListener("click", async () => {
    if (currentLanguage === "english") {
      await switchToSwahili();
    } else {
      switchToEnglish();
    }
  });
}

async function switchToSwahili() {
  const toggle = document.getElementById("swahili-toggle");
  const guideContent = document.getElementById("guide-content");
  const originalGuide = guideContent.innerHTML;

  // Store original
  guideContent.dataset.original = originalGuide;

  // Update button state
  toggle.disabled = true;
  toggle.innerHTML = `<span class="toggle-spinner"></span> Translating...`;

  // Show loading in guide
  guideContent.innerHTML = `
        <div class="translation-loading">
            <div class="trans-spinner"></div>
            <p>Inatafsiriwa kwa Kiswahili...</p>
        </div>
    `;

  try {
    const response = await fetch("/translate-guide", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        guide: guideContent.dataset.original,
        language: "swahili",
      }),
    });

    const data = await response.json();

    if (data.translated) {
      guideContent.innerHTML = data.translated;
      currentLanguage = "swahili";
      toggle.disabled = false;
      toggle.innerHTML = `🇰🇪 Switch to English`;
      toggle.classList.add("active");
    } else {
      throw new Error("No translation returned");
    }
  } catch (err) {
    guideContent.innerHTML = originalGuide;
    currentLanguage = "english";
    toggle.disabled = false;
    toggle.innerHTML = `🇰🇪 Swahili`;
    showToast("Translation failed. Please try again.");
  }
}

function switchToEnglish() {
  const toggle = document.getElementById("swahili-toggle");
  const guideContent = document.getElementById("guide-content");

  // Restore original
  if (guideContent.dataset.original) {
    guideContent.innerHTML = guideContent.dataset.original;
  }

  currentLanguage = "english";
  toggle.innerHTML = `🇰🇪 Swahili`;
  toggle.classList.remove("active");
}

// Init when DOM is ready
document.addEventListener("DOMContentLoaded", initSwahiliToggle);
