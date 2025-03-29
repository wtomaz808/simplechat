// workspace-init.js

// ------------- Initial Load -------------
document.addEventListener('DOMContentLoaded', () => {
    // Call fetch functions made available on the window object by other files
    if (typeof window.fetchUserDocuments === 'function') {
        window.fetchUserDocuments();
    } else {
        console.error("fetchUserDocuments function not found. Check workspace-documents.js");
    }

    if (typeof window.fetchUserPrompts === 'function') {
        window.fetchUserPrompts();
    } else {
        console.error("fetchUserPrompts function not found. Check workspace-prompts.js");
    }

    // Optional: Add listener for tab switching if needed for specific actions
    const workspaceTabs = document.querySelectorAll('#workspaceTab button[data-bs-toggle="tab"]');
    workspaceTabs.forEach(tabEl => {
        tabEl.addEventListener('shown.bs.tab', event => {
            const targetTabId = event.target.id;
            // console.log(`Switched to tab: ${targetTabId}`);
            // Example: Refresh data only when tab becomes visible (can reduce initial load)
            // if (targetTabId === 'documents-tab-btn' && typeof window.fetchUserDocuments === 'function') {
            //     window.fetchUserDocuments();
            // } else if (targetTabId === 'prompts-tab-btn' && typeof window.fetchUserPrompts === 'function') {
            //     window.fetchUserPrompts();
            // }
        });
    });
});