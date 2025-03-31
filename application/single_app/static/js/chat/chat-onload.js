// chat-onload.js

import { loadConversations } from "./chat-conversations.js";
// Import handleDocumentSelectChange
import { loadAllDocs, populateDocumentSelectScope, handleDocumentSelectChange } from "./chat-documents.js";
import { getUrlParameter } from "./chat-utils.js"; // Assuming getUrlParameter is in chat-utils.js now
import { loadUserPrompts, loadGroupPrompts, initializePromptInteractions } from "./chat-prompts.js";

window.addEventListener('DOMContentLoaded', () => {
  console.log("DOM Content Loaded. Starting initializations."); // Log start

  loadConversations(); // Load conversations immediately

  // Load documents and prompts
  Promise.all([
      loadAllDocs(),
      loadUserPrompts(),
      loadGroupPrompts()
  ])
  .then(() => {
      console.log("Initial data (Docs, Prompts) loaded successfully."); // Log success

      // --- Initialize Document-related UI ---
      // This part handles URL params for documents - KEEP IT
      const localSearchDocsParam = getUrlParameter("search_documents") === "true";
      const localDocScopeParam = getUrlParameter("doc_scope") || "";
      const localDocumentIdParam = getUrlParameter("document_id") || "";
      const localSearchDocsBtn = document.getElementById("search-documents-btn");
      const localDocScopeSel = document.getElementById("doc-scope-select");
      const localDocSelectEl = document.getElementById("document-select");
      const searchDocumentsContainer = document.getElementById("search-documents-container");

      if (localSearchDocsParam && localSearchDocsBtn && localDocScopeSel && localDocSelectEl && searchDocumentsContainer) {
          console.log("Handling document URL parameters."); // Log
          localSearchDocsBtn.classList.add("active");
          searchDocumentsContainer.style.display = "block";
          if (localDocScopeParam) {
              localDocScopeSel.value = localDocScopeParam;
          }
          populateDocumentSelectScope(); // Populate based on scope (might be default or from URL)

          if (localDocumentIdParam) {
               // Wait a tiny moment for populateDocumentSelectScope potentially async operations (less ideal, but sometimes needed)
               // A better approach would be if populateDocumentSelectScope returned a promise
               // setTimeout(() => {
                   if ([...localDocSelectEl.options].some(option => option.value === localDocumentIdParam)) {
                       localDocSelectEl.value = localDocumentIdParam;
                   } else {
                       console.warn(`Document ID "${localDocumentIdParam}" not found for scope "${localDocScopeSel.value}".`);
                   }
                   // Ensure classification updates after setting document
                   handleDocumentSelectChange();
               // }, 0); // Tiny delay
          } else {
              // If no specific doc ID, still might need to trigger change if scope changed
               handleDocumentSelectChange();
          }
      } else {
          // If not loading from URL params, maybe still populate default scope?
          populateDocumentSelectScope();
      }
      // --- End Document-related UI ---


      // --- Call the prompt initialization function HERE ---
      console.log("Calling initializePromptInteractions...");
      initializePromptInteractions();


      console.log("All initializations complete."); // Log end

  })
  .catch((err) => {
      console.error("Error during initial data loading or setup:", err);
      // Maybe try to initialize prompts even if doc loading fails? Depends on requirements.
      // console.log("Attempting to initialize prompts despite data load error...");
      // initializePromptInteractions();
  });
});
