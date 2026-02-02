// ============ WELCOME MODAL & COOKIES ============

function initWelcomeModal() {
    const modal = document.getElementById("welcomeModal");
    const closeBtn = document.querySelector(".modal-close");
    const welcomeBtn = document.getElementById("welcomeClose");

    // Check if user has dismissed modal before
    if (localStorage.getItem("cipherlab_modal_dismissed")) {
        modal.style.display = "none";
        return;
    }

    // Show modal
    modal.classList.add("show");

    // Close handlers
    function closeModal() {
        modal.classList.remove("show");
        localStorage.setItem("cipherlab_modal_dismissed", "true");
    }

    closeBtn?.addEventListener("click", closeModal);
    welcomeBtn?.addEventListener("click", closeModal);

    // Close on background click
    modal.addEventListener("click", (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });
}

function getCookie(name) {
    const cookie = document.cookie
        .split("; ")
        .find((row) => row.startsWith(`${name}=`));
    if (!cookie) return null;
    return decodeURIComponent(cookie.split("=")[1]);
}

function getCookiePrefs() {
    const raw = getCookie("cipherlab_cookie_prefs");
    if (!raw) return null;
    try {
        return JSON.parse(raw);
    } catch (e) {
        return null;
    }
}

function initCookieConsent() {
    const banner = document.getElementById("cookieConsent");
    const settingsModal = document.getElementById("cookieSettingsModal");
    const acceptBtn = document.getElementById("cookieAccept");
    const manageBtn = document.getElementById("cookieManageSettings");
    const closeSettingsBtn = document.getElementById("cookieSettingsClose");
    const saveSettingsBtn = document.getElementById("cookieSettingsSave");

    // Load saved preferences from cookies
    const prefs = getCookiePrefs();
    if (prefs) {
        document.getElementById("cookie-functional").checked = prefs.functional ?? true;
        document.getElementById("cookie-analytics").checked = prefs.analytics ?? false;
        document.getElementById("cookie-marketing").checked = prefs.marketing ?? false;
        banner.style.display = "none";
        return;
    }

    // Show banner if no preference set
    banner.classList.add("show");

    // Open settings modal
    manageBtn?.addEventListener("click", () => {
        banner.classList.remove("show");
        settingsModal.style.display = "flex";
        settingsModal.classList.add("show");
    });

    // Accept all cookies
    acceptBtn?.addEventListener("click", () => {
        const prefs = {
            essential: true,
            functional: true,
            analytics: true,
            marketing: true
        };
        banner.classList.remove("show");

        fetch("/api/cookie-consent", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ...prefs, choice: "accepted" })
        }).catch(e => console.log("Cookie consent logged"));
    });

    // Close settings modal
    closeSettingsBtn?.addEventListener("click", () => {
        settingsModal.style.display = "none";
        banner.classList.add("show");
    });

    // Save custom preferences
    saveSettingsBtn?.addEventListener("click", () => {
        const prefs = {
            essential: true, // Always true
            functional: document.getElementById("cookie-functional").checked,
            analytics: document.getElementById("cookie-analytics").checked,
            marketing: document.getElementById("cookie-marketing").checked
        };
        settingsModal.style.display = "none";
        banner.classList.remove("show");

        fetch("/api/cookie-consent", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ...prefs, choice: "custom" })
        }).catch(e => console.log("Custom cookie preferences saved"));
    });

    // Close modal on background click
    settingsModal?.addEventListener("click", (e) => {
        if (e.target === settingsModal) {
            settingsModal.style.display = "none";
            banner.classList.add("show");
        }
    });
}

// API Helper
async function postJSON(url, payload) {
    try {
        const response = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await response.json();
        if (!data.ok) throw new Error(data.error || "Request failed");
        return data;
    } catch (error) {
        throw new Error(error.message || "Network error");
    }
}

// ============ CIPHER ENCRYPTION/DECRYPTION ============

async function encryptWithCipher(slug) {
    const textInput = document.getElementById("plaintext");
    const resultOutput = document.getElementById("result");
    const statusEl = document.getElementById("status");

    if (!textInput.value.trim()) {
        showStatus("Please enter text to encrypt.", "error");
        return;
    }

    showStatus("Encrypting...", "info");

    try {
        const params = collectCipherParams();
        const data = await postJSON("/api/encrypt", {
            slug: slug,
            text: textInput.value,
            params: params,
        });

        resultOutput.value = data.result;
        showStatus("Encryption successful!", "success");
        updateCharCount("result");
    } catch (error) {
        showStatus(`Error: ${error.message}`, "error");
        resultOutput.value = "";
    }
}

async function decryptWithCipher(slug) {
    const textInput = document.getElementById("plaintext");
    const resultOutput = document.getElementById("result");
    const statusEl = document.getElementById("status");

    if (!textInput.value.trim()) {
        showStatus("Please enter text to decrypt.", "error");
        return;
    }

    showStatus("Decrypting...", "info");

    try {
        const params = collectCipherParams();
        const data = await postJSON("/api/decrypt", {
            slug: slug,
            text: textInput.value,
            params: params,
        });

        resultOutput.value = data.result;
        showStatus("Decryption successful!", "success");
        updateCharCount("result");
    } catch (error) {
        showStatus(`Error: ${error.message}`, "error");
        resultOutput.value = "";
    }
}

function collectCipherParams() {
    const params = {};
    const inputs = document.querySelectorAll("[data-param]");
    inputs.forEach((input) => {
        const paramName = input.getAttribute("data-param");
        const paramType = input.getAttribute("data-type");

        if (paramType === "number") {
            params[paramName] = parseInt(input.value) || 0;
        } else {
            params[paramName] = input.value;
        }
    });
    return params;
}

// ============ AES ENCRYPTION ============

async function aesEncrypt() {
    const passwordInput = document.getElementById("aesPassword");
    const textInput = document.getElementById("aesText");
    const bundleOutput = document.getElementById("aesBundle");
    const resultOutput = document.getElementById("aesResult");

    if (!passwordInput.value.trim()) {
        showStatus("Please enter a password.", "error");
        return;
    }

    if (!textInput.value.trim()) {
        showStatus("Please enter text to encrypt.", "error");
        return;
    }

    showStatus("Encrypting with AES-GCM...", "info");

    try {
        const data = await postJSON("/api/aes/encrypt", {
            password: passwordInput.value,
            text: textInput.value,
        });

        bundleOutput.value = JSON.stringify(data.bundle, null, 2);
        resultOutput.value = "✓ Encryption complete. Bundle saved above.";
        showStatus("AES-GCM encryption successful!", "success");
    } catch (error) {
        showStatus(`Error: ${error.message}`, "error");
        resultOutput.value = "";
    }
}

async function aesDecrypt() {
    const passwordInput = document.getElementById("aesPassword");
    const bundleInput = document.getElementById("aesBundle");
    const resultOutput = document.getElementById("aesResult");

    if (!passwordInput.value.trim()) {
        showStatus("Please enter a password.", "error");
        return;
    }

    if (!bundleInput.value.trim()) {
        showStatus("Please enter a bundle.", "error");
        return;
    }

    showStatus("Decrypting with AES-GCM...", "info");

    try {
        let bundle = JSON.parse(bundleInput.value);
        const data = await postJSON("/api/aes/decrypt", {
            password: passwordInput.value,
            bundle: bundle,
        });

        resultOutput.value = data.result;
        showStatus("AES-GCM decryption successful!", "success");
    } catch (error) {
        showStatus(`Error: ${error.message}`, "error");
        resultOutput.value = "";
    }
}

// ============ UTILITY FUNCTIONS ============

function showStatus(message, type = "info") {
    const statusEl = document.getElementById("status");
    if (!statusEl) return;

    statusEl.textContent = message;
    statusEl.className = `alert ${type}`;
    statusEl.style.display = "block";

    if (type === "success" || type === "error") {
        setTimeout(() => {
            statusEl.style.display = "none";
        }, 5000);
    }
}

function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.select();
    element.setSelectionRange(0, 99999);

    try {
        document.execCommand("copy");
        showStatus("Copied to clipboard!", "success");
    } catch (err) {
        showStatus("Failed to copy.", "error");
    }
}

function updateCharCount(elementId) {
    const element = document.getElementById(elementId);
    const countEl = document.getElementById(`${elementId}-count`);

    if (element && countEl) {
        countEl.textContent = `${element.value.length} characters`;
    }
}

function clearTextarea(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.value = "";
        updateCharCount(elementId);
    }
}

// ============ EVENT LISTENERS ============

document.addEventListener("DOMContentLoaded", () => {
    // Initialize modals and cookies
    initWelcomeModal();
    initCookieConsent();

    // Add live character counting
    const textareas = document.querySelectorAll("textarea");
    textareas.forEach((ta) => {
        const id = ta.id;
        ta.addEventListener("input", () => updateCharCount(id));
        updateCharCount(id);
    });

    // Add parameter change listeners for cipher switching
    const paramInputs = document.querySelectorAll("[data-param]");
    paramInputs.forEach((input) => {
        input.addEventListener("change", () => {
            // Could trigger re-encryption here if needed
        });
    });
});

// ============ EXPORT/IMPORT ============

function exportAsJSON(ciphertextId, filenamePrefix = "cipher") {
    const ciphertext = document.getElementById(ciphertextId);
    if (!ciphertext || !ciphertext.value.trim()) {
        showStatus("Nothing to export.", "error");
        return;
    }

    const data = {
        timestamp: new Date().toISOString(),
        content: ciphertext.value,
    };

    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${filenamePrefix}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showStatus("Exported successfully!", "success");
}
