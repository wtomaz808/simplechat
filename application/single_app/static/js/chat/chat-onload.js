// chat-onload.js

import { loadConversations } from "./chat-conversations.js";
import { loadAllDocs, populateDocumentSelectScope } from "./chat-documents.js";
import { getUrlParameter } from "./chat-input-actions.js";
import { loadUserPrompts, loadGroupPrompts } from "./chat-prompts.js";

window.onload = function () {
    loadConversations();
  
    Promise.all([
      loadAllDocs(),
      loadUserPrompts(),
      loadGroupPrompts()
    ])
      .then(() => {
        const localSearchDocsParam = getUrlParameter("search_documents") === "true";
        const localDocScopeParam = getUrlParameter("doc_scope") || "";
        const localDocumentIdParam = getUrlParameter("document_id") || "";
  
        const localSearchDocsBtn = document.getElementById("search-documents-btn");
        const localDocScopeSel = document.getElementById("doc-scope-select");
        const localDocSelectEl = document.getElementById("document-select");
  
        if (localSearchDocsParam && localSearchDocsBtn && localDocScopeSel && localDocSelectEl) {
          localSearchDocsBtn.classList.add("active");
          localDocScopeSel.style.display = "inline-block";
          localDocSelectEl.style.display = "inline-block";
  
          if (localDocScopeParam) {
            localDocScopeSel.value = localDocScopeParam;
          }
          populateDocumentSelectScope();
  
          if (localDocumentIdParam) {
            localDocSelectEl.value = localDocumentIdParam;
          }
        }
      })
      .catch((err) => {
        console.error("Error loading initial data:", err);
      });
  };