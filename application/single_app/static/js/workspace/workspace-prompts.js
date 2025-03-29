// /js/workspace/workspace-prompts.js

import { escapeHtml } from "./workspace-utils.js";

// ------------- DOM Elements (Prompts Tab) -------------
const promptsTableBody = document.querySelector("#prompts-table tbody");
const promptModalEl = document.getElementById("promptModal") ? new bootstrap.Modal(document.getElementById("promptModal")) : null;
const promptForm = document.getElementById("prompt-form");
const promptIdEl = document.getElementById("prompt-id");
const promptNameEl = document.getElementById("prompt-name");
const promptContentEl = document.getElementById("prompt-content");
const createPromptBtn = document.getElementById("create-prompt-btn");
const promptSaveBtn = document.getElementById('prompt-save-btn');

// Check if elements exist
    if (!promptsTableBody || !promptModalEl || !promptForm || !promptIdEl || !promptNameEl || !promptContentEl || !createPromptBtn || !promptSaveBtn) {
    console.warn("Workspace Prompts Tab: One or more essential DOM elements not found. Script might not function correctly.");
    // return; // Decide how to handle missing elements
}

let simplemde = null; // Declare outside to be accessible

// Initialize SimpleMDE only if the element exists and the library is loaded
if (promptContentEl && typeof SimpleMDE !== 'undefined') {
    try {
        simplemde = new SimpleMDE({ element: promptContentEl, spellChecker: false });
    } catch (e) {
        console.error("Failed to initialize SimpleMDE:", e);
        // Fallback or alternative behavior if needed
    }
} else if (!promptContentEl) {
    console.warn("Prompt content textarea not found, SimpleMDE not initialized.");
} else if (typeof SimpleMDE === 'undefined') {
    console.warn("SimpleMDE library not loaded before workspace-prompts.js");
}


// ------------- Prompt Functions -------------
function fetchUserPrompts() {
    if (!promptsTableBody) return;
    promptsTableBody.innerHTML = '<tr><td colspan="2" class="text-center p-3"><div class="spinner-border spinner-border-sm" role="status"><span class="visually-hidden">Loading...</span></div> Loading prompts...</td></tr>';
    fetch("/api/prompts")
        .then(r => r.ok ? r.json() : r.json().then(err => Promise.reject(err)))
        .then(data => {
            promptsTableBody.innerHTML = "";
            if (!data.prompts || data.prompts.length === 0) {
                promptsTableBody.innerHTML = '<tr><td colspan="2" class="text-center p-3 text-muted">No prompts created yet.</td></tr>';
            } else {
                data.prompts.forEach(p => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                    <td>${escapeHtml(p.name)}</td>
                    <td>
                    <button class="btn btn-sm btn-primary" onclick="window.onEditPrompt('${p.id}')" title="Edit Prompt">
                        <i class="bi bi-pencil-fill"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-danger ms-1" onclick="window.onDeletePrompt('${p.id}', event)" title="Delete Prompt">
                        <i class="bi bi-trash-fill"></i> Delete
                    </button>
                    </td>
                `;
                    promptsTableBody.appendChild(tr);
                });
            }
        })
        .catch(err => {
            console.error("Error fetching prompts:", err);
            promptsTableBody.innerHTML = `<tr><td colspan="2" class="text-center text-danger p-3">Error loading prompts: ${err.error || err.message || 'Unknown error'}</td></tr>`;
        });
}
// Make fetchUserPrompts globally available for workspace-init.js
window.fetchUserPrompts = fetchUserPrompts;

// ------------- Event Listeners -------------
if (createPromptBtn) {
    createPromptBtn.addEventListener("click", () => {
        if (!promptModalEl || !promptIdEl || !promptNameEl || !promptContentEl) return;
        const modalLabel = document.getElementById("promptModalLabel");
        if (modalLabel) modalLabel.textContent = "Create New Prompt";
        promptIdEl.value = ""; // Clear ID for creation
        promptNameEl.value = "";
        if (simplemde) {
            simplemde.value(""); // Clear editor content
        } else {
            promptContentEl.value = ""; // Fallback if MDE failed
        }
        promptModalEl.show();
    });
}

if (promptForm) {
    promptForm.addEventListener("submit", (e) => {
        e.preventDefault();
            if (!promptSaveBtn || !promptIdEl || !promptNameEl || !promptContentEl || !promptModalEl) return;

        promptSaveBtn.disabled = true;
        promptSaveBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Saving...`;

        let contentValue = simplemde ? simplemde.value() : promptContentEl.value;

        const promptId = promptIdEl.value;
        const payload = {
            name: promptNameEl.value.trim(),
            content: contentValue.trim(),
        };

        const url = promptId ? `/api/prompts/${promptId}` : "/api/prompts";
        const method = promptId ? "PATCH" : "POST";

        fetch(url, {
            method: method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        })
            .then(r => r.ok ? r.json() : r.json().then(err => Promise.reject(err)))
            .then(data => {
                promptModalEl.hide();
                fetchUserPrompts(); // Refresh list
            })
            .catch(err => {
                console.error(`Error ${method === 'POST' ? 'creating' : 'updating'} prompt:`, err);
                alert(`Error ${method === 'POST' ? 'creating' : 'updating'} prompt: ` + (err.error || err.message || "Unknown error"));
            })
            .finally(() => {
                promptSaveBtn.disabled = false;
                promptSaveBtn.innerHTML = "Save Prompt";
            });
    });
}

// Function needs to be global for onclick
window.onEditPrompt = function (promptId) {
    if (!promptModalEl || !promptIdEl || !promptNameEl || !promptContentEl) return;
    fetch(`/api/prompts/${promptId}`)
        .then(r => r.ok ? r.json() : r.json().then(err => Promise.reject(err)))
        .then(data => {
            const modalLabel = document.getElementById("promptModalLabel");
                if (modalLabel) modalLabel.textContent = `Edit Prompt: ${escapeHtml(data.name)}`;
            promptIdEl.value = data.id;
            promptNameEl.value = data.name;
            if (simplemde) {
                simplemde.value(data.content || "");
            } else {
                promptContentEl.value = data.content || ""; // Fallback
            }
            promptModalEl.show();
        })
        .catch(err => {
            console.error("Error retrieving prompt for edit:", err);
            alert("Error retrieving prompt: " + (err.error || err.message || "Unknown error"));
        });
};

// Function needs to be global for onclick
window.onDeletePrompt = function (promptId, event) {
    if (!confirm("Are you sure you want to delete this prompt?")) return;

    const deleteBtn = event ? event.target.closest('button') : null;
    if (deleteBtn) {
        deleteBtn.disabled = true;
        // Optionally add spinner icon
        deleteBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>`;
    }

    fetch(`/api/prompts/${promptId}`, { method: "DELETE" })
        .then(r => r.ok ? r.json() : r.json().then(err => Promise.reject(err)))
        .then(data => {
            fetchUserPrompts(); // Refresh list
        })
        .catch(err => {
            console.error("Error deleting prompt:", err);
            alert("Error deleting prompt: " + (err.error || err.message || "Unknown error"));
            if (deleteBtn) {
                    deleteBtn.disabled = false; // Re-enable on error
                    deleteBtn.innerHTML = '<i class="bi bi-trash-fill"></i> Delete'; // Restore text/icon
            }
        });
};