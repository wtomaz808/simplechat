// chat-documents.js

export const docScopeSelect = document.getElementById("doc-scope-select");
const searchDocumentsBtn = document.getElementById("search-documents-btn");
const docSelectEl = document.getElementById("document-select");
const filtersToggleLabel = document.getElementById("filters-toggle-label");
const classificationSelect = document.getElementById("classification-select");
const authorFilter = document.getElementById("author-filter");
const titleFilter = document.getElementById("title-filter");
const keywordsFilter = document.getElementById("keywords-filter");
const organizationFilter = document.getElementById("organization-filter");

const categoriesStr = window.document_classification_categories || "";
const classificationCategories = categoriesStr.split(",");

export function populateDocumentSelectScope() {
  const scopeSel = document.getElementById("doc-scope-select");
  const docSel = document.getElementById("document-select");
  if (!scopeSel || !docSel) return;

  docSel.innerHTML = "";

  const noneOpt = document.createElement("option");
  noneOpt.value = "";
  noneOpt.textContent = "All Documents";
  docSel.appendChild(noneOpt);

  const scopeVal = scopeSel.value || "all";

  let finalDocs = [];
  if (scopeVal === "all") {
    const pDocs = personalDocs.map((d) => ({
      id: d.id,
      label: `[Personal] ${d.file_name}`,
    }));
    const gDocs = groupDocs.map((d) => ({
      id: d.id,
      label: `[Group: ${activeGroupName}] ${d.file_name}`,
    }));
    finalDocs = pDocs.concat(gDocs);
  } else if (scopeVal === "personal") {
    finalDocs = personalDocs.map((d) => ({
      id: d.id,
      label: `[Personal] ${d.file_name}`,
    }));
  } else if (scopeVal === "group") {
    finalDocs = groupDocs.map((d) => ({
      id: d.id,
      label: `[Group: ${activeGroupName}] ${d.file_name}`,
    }));
  }

  finalDocs.forEach((doc) => {
    const opt = document.createElement("option");
    opt.value = doc.id;
    opt.textContent = doc.label;
    docSel.appendChild(opt);
  });
}

export function loadPersonalDocs() {
  return fetch("/api/documents")
    .then((r) => r.json())
    .then((data) => {
      if (data.error) {
        console.warn("Error fetching user docs:", data.error);
        personalDocs = [];
        return;
      }
      personalDocs = data.documents || [];
    })
    .catch((err) => {
      console.error("Error loading personal docs:", err);
      personalDocs = [];
    });
}

export function loadGroupDocs() {
  return fetch("/api/groups")
    .then((r) => r.json())
    .then((groups) => {
      const activeGroup = groups.find((g) => g.isActive);
      if (activeGroup) {
        activeGroupName = activeGroup.name || "Active Group";
        return fetch("/api/group_documents")
          .then((r) => r.json())
          .then((data) => {
            if (data.error) {
              console.warn("Error fetching group docs:", data.error);
              groupDocs = [];
              return;
            }
            groupDocs = data.documents || [];
          })
          .catch((err) => {
            console.error("Error loading group docs:", err);
            groupDocs = [];
          });
      } else {
        activeGroupName = "";
        groupDocs = [];
      }
    })
    .catch((err) => {
      console.error("Error loading groups:", err);
      groupDocs = [];
    });
}

export function loadAllDocs() {
  const hasDocControls =
    document.getElementById("search-documents-btn") ||
    document.getElementById("doc-scope-select") ||
    document.getElementById("document-select");

  if (!hasDocControls) {
    return Promise.resolve();
  }

  return loadPersonalDocs().then(() => loadGroupDocs());
}

if (docScopeSelect) {
  docScopeSelect.addEventListener("change", populateDocumentSelectScope);
}

if (searchDocumentsBtn) {
  searchDocumentsBtn.addEventListener("click", function () {
    this.classList.toggle("active");

    const searchDocContainer = document.getElementById("search-documents-container");
    const docScopeSel = document.getElementById("doc-scope-select");
    const docSelectEl = document.getElementById("document-select");
    
    if (!docScopeSel || !docSelectEl || !searchDocContainer) return;

    if (this.classList.contains("active")) {
      searchDocContainer.style.display = "block";
      docScopeSel.style.display = "inline-block";
      docSelectEl.style.display = "inline-block";
      populateDocumentSelectScope();
    } else {
      searchDocContainer.style.display = "none";
      docScopeSel.style.display = "none";
      docSelectEl.style.display = "none";
      docSelectEl.innerHTML = "";
    }
  });
}

function handleDocumentSelectChange() {
  const docId = docSelectEl.value.trim();

  if (!docId) {
    // ====== FILTER MODE ======
    filtersToggleLabel.textContent = "Filters";
    
    // classification is a multi-select with checkboxes. 
    // You can do plain multi-select or bootstrap plugin for a checkbox dropdown.
    classificationSelect.style.display = "inline-block";
    classificationSelect.disabled = false;
    classificationSelect.multiple = true; // Make it multi-select
    classificationSelect.innerHTML = ""; 
    
    classificationCategories.forEach(cat => {
      const opt = document.createElement("option");
      opt.value = cat;
      opt.textContent = cat;
      classificationSelect.appendChild(opt);
    });
    
    // Make text fields editable and empty
    makeInputEditable(authorFilter, "");
    makeInputEditable(titleFilter, "");
    makeInputEditable(keywordsFilter, "");
    makeInputEditable(organizationFilter, "");

  } else {
    // ====== DOCUMENT METADATA MODE ======
    filtersToggleLabel.textContent = "Document Metadata";

    // classification is just a single text: 
    // We'll look up the document from personalDocs/groupDocs
    const matchedDoc = findDocumentById(docId);
    if (!matchedDoc) {
      // fallback, if doc is not found
      console.warn("Selected doc not found in personalDocs/groupDocs:", docId);
      return;
    }

    // 1) classification 
    classificationSelect.multiple = false;
    classificationSelect.innerHTML = "";
    if (matchedDoc.document_classification) {
      const opt = document.createElement("option");
      opt.value = matchedDoc.document_classification;
      opt.textContent = matchedDoc.document_classification;
      classificationSelect.appendChild(opt);
    }
    // Disable the classification field so user can't change
    classificationSelect.disabled = true;

    // 2) Fill read-only fields with doc metadata
    const authorsJoined = (matchedDoc.authors || []).join(", ");
    makeInputReadOnly(authorFilter, authorsJoined);

    makeInputReadOnly(titleFilter, matchedDoc.title || "");
    
    // Keywords might be an array, so join with commas
    const keywordsJoined = (matchedDoc.keywords || []).join(", ");
    makeInputReadOnly(keywordsFilter, keywordsJoined);

    makeInputReadOnly(organizationFilter, matchedDoc.organization || "");
  }
}

// Helper to find doc by ID in personal or group docs:
function findDocumentById(docId) {
  // search personalDocs
  let doc = personalDocs.find(d => d.id === docId);
  if (!doc) {
    // search groupDocs
    doc = groupDocs.find(d => d.id === docId);
  }
  return doc;
}

// Helper: Make text input editable and optionally set value
function makeInputEditable(inputEl, val) {
  inputEl.value = val || "";
  inputEl.readOnly = false;
  // Optional: remove any tooltip 
  inputEl.removeAttribute("title");
  // Show the field 
  inputEl.style.display = "inline-block";
}

// Helper: Make text input read-only, set value, and show tooltip on hover
function makeInputReadOnly(inputEl, val) {
  inputEl.value = val || "";
  inputEl.readOnly = true;
  inputEl.setAttribute("title", val);  // hover shows the entire value
  // Optionally style it differently or remove placeholder
  inputEl.placeholder = "";
  // Show the field 
  inputEl.style.display = "inline-block";
}

if (docSelectEl) {
  docSelectEl.addEventListener("change", handleDocumentSelectChange);
}