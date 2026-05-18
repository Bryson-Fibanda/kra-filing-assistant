// ─────────────────────────────────────────
// SWAHILI TOGGLE
// ─────────────────────────────────────────
let currentLanguage = 'english';

function initSwahiliToggle() {
    const toggle = document.getElementById('swahili-toggle');
    if (!toggle) return;
    toggle.addEventListener('click', async () => {
        if (currentLanguage === 'english') {
            await switchToSwahili();
        } else {
            switchToEnglish();
        }
    });
}

async function switchToSwahili() {
    const toggle       = document.getElementById('swahili-toggle');
    const guideContent = document.getElementById('guide-content');
    if (!guideContent) return;

    guideContent.dataset.original = guideContent.innerHTML;
    toggle.disabled = true;
    toggle.textContent = 'Translating...';

    guideContent.innerHTML = `
        <div class="translation-loading">
            <div class="trans-spinner"></div>
            <p>Inatafsiriwa kwa Kiswahili...</p>
        </div>`;

    try {
        const response = await fetch('/translate-guide', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ guide: guideContent.dataset.original, language: 'swahili' })
        });
        const data = await response.json();
        if (data.translated) {
            guideContent.innerHTML = data.translated;
            currentLanguage = 'swahili';
            toggle.disabled = false;
            toggle.textContent = '🇬🇧 Switch to English';
            toggle.classList.add('active');
        } else {
            throw new Error('No translation');
        }
    } catch (err) {
        guideContent.innerHTML = guideContent.dataset.original;
        currentLanguage = 'english';
        toggle.disabled = false;
        toggle.textContent = '🇰🇪 Swahili';
        showToast('Translation failed. Please try again.');
    }
}

function switchToEnglish() {
    const toggle       = document.getElementById('swahili-toggle');
    const guideContent = document.getElementById('guide-content');
    if (guideContent && guideContent.dataset.original) {
        guideContent.innerHTML = guideContent.dataset.original;
    }
    currentLanguage = 'english';
    if (toggle) {
        toggle.textContent = '🇰🇪 Swahili';
        toggle.classList.remove('active');
    }
}

document.addEventListener('DOMContentLoaded', initSwahiliToggle);
