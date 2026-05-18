// ─────────────────────────────────────────
// FILING TYPE SELECTOR
// ─────────────────────────────────────────
function selectFiling(type) {
    document.querySelectorAll('.filing-card').forEach(c => c.classList.remove('selected'));
    const selected = document.querySelector(`[data-type="${type}"]`);
    if (selected) selected.classList.add('selected');

    document.querySelectorAll('.filing-form').forEach(f => f.style.display = 'none');
    const formEl = document.getElementById(`form-${type}`);
    if (formEl) formEl.style.display = 'block';

    const formArea = document.getElementById('form-area');
    if (formArea) {
        formArea.style.display = 'block';
        setTimeout(() => {
            formArea.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    }
}

// ─────────────────────────────────────────
// PROCESSING OVERLAY
// ─────────────────────────────────────────
const overlay = document.getElementById('processing-overlay');

function showProcessing() {
    if (overlay) {
        overlay.style.display = 'flex';
        animateSteps();
    }
}

document.querySelectorAll('form[action="/upload"]').forEach(form => {
    form.addEventListener('submit', () => showProcessing());
});

function animateSteps() {
    const stepIds = ['proc-1', 'proc-2', 'proc-3', 'proc-4'];
    let current = 0;
    const interval = setInterval(() => {
        if (current > 0) {
            const prev = document.getElementById(stepIds[current - 1]);
            if (prev) {
                prev.classList.remove('active');
                prev.classList.add('done');
            }
        }
        if (current < stepIds.length) {
            const el = document.getElementById(stepIds[current]);
            if (el) el.classList.add('active');
            current++;
        } else {
            clearInterval(interval);
        }
    }, 2200);
}

// ─────────────────────────────────────────
// TOAST NOTIFICATION
// ─────────────────────────────────────────
function showToast(message) {
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
        background: #1A1A1A; color: white; padding: 12px 24px;
        border-radius: 999px; font-size: 0.85rem; z-index: 9999;
        font-family: 'DM Sans', sans-serif; box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        white-space: nowrap;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}
