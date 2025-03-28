// chat-onload.js

import { loadConversations } from "./chat-conversations.js";
// Import handleDocumentSelectChange
import { loadAllDocs, populateDocumentSelectScope, handleDocumentSelectChange } from "./chat-documents.js";
import { getUrlParameter } from "./chat-utils.js"; // Assuming getUrlParameter is in chat-utils.js now
import { loadUserPrompts, loadGroupPrompts } from "./chat-prompts.js";

window.onload = function () {
    loadConversations();

    Promise.all([
      loadAllDocs(),
      loadUserPrompts(),
      loadGroupPrompts()
    ])
      .then(() => {
        // Get URL parameters
        const localSearchDocsParam = getUrlParameter("search_documents") === "true";
        const localDocScopeParam = getUrlParameter("doc_scope") || "";
        const localDocumentIdParam = getUrlParameter("document_id") || "";

        // Get references to the DOM elements
        const localSearchDocsBtn = document.getElementById("search-documents-btn");
        const localDocScopeSel = document.getElementById("doc-scope-select");
        const localDocSelectEl = document.getElementById("document-select");
        // --- Get reference to the container ---
        const searchDocumentsContainer = document.getElementById("search-documents-container");

        // Check if parameters exist and elements are found
        if (localSearchDocsParam && localSearchDocsBtn && localDocScopeSel && localDocSelectEl && searchDocumentsContainer) {

          // 1. Activate the toggle button visually
          localSearchDocsBtn.classList.add("active");

          // --- 2. Explicitly show the container ---
          searchDocumentsContainer.style.display = "block";

          // 3. Set the scope dropdown value (if provided)
          if (localDocScopeParam) {
            localDocScopeSel.value = localDocScopeParam;
          }

          // 4. Populate the document dropdown based on the selected scope
          //    This function ALREADY calls handleDocumentSelectChange internally,
          //    which sets the classification based on the default selection ("All Docs")
          populateDocumentSelectScope();

          // 5. Set the specific document in the dropdown (if provided)
          if (localDocumentIdParam) {
             // Check if the option actually exists before setting it
             if ([...localDocSelectEl.options].some(option => option.value === localDocumentIdParam)) {
                 localDocSelectEl.value = localDocumentIdParam;
             } else {
                 console.warn(`Document ID "${localDocumentIdParam}" not found in the dropdown for scope "${localDocScopeSel.value}".`);
                 // Optionally default back to "All Documents" or show a message
                 // localDocSelectEl.value = "";
             }
          }

          // --- 6. Manually trigger the classification update AGAIN ---
          //    This ensures the classification UI reflects the document
          //    selected via the URL parameter.
          handleDocumentSelectChange();

        }
      })
      .catch((err) => {
        console.error("Error loading initial data:", err);
        // Optionally display an error to the user
      });
  };