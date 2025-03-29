// workspace-documents.js

// Make sure global settings from HTML script block are available
// window.classification_categories
// window.enable_document_classification
// window.enable_extract_meta_data

import { escapeHtml } from "./workspace-utils.js";

let currentPage = 1;
let pageSize = 10;
const activePolls = new Set(); // Store active poll intervals

// ------------- DOM Elements (Documents Tab) -------------
const paginationContainer = document.getElementById("pagination-container");
const pageSizeSelect = document.getElementById("page-size-select");
const fileInput = document.getElementById("file-input");
const uploadBtn = document.getElementById("upload-btn");
const uploadStatusSpan = document.getElementById("upload-status");
const documentsTableBody = document.querySelector("#documents-table tbody");
const docMetadataModalEl = document.getElementById("docMetadataModal") ? new bootstrap.Modal(document.getElementById("docMetadataModal")) : null;
const docMetadataForm = document.getElementById("doc-metadata-form");

// Check if elements exist before adding listeners
if (!documentsTableBody || !docMetadataModalEl || !docMetadataForm || !paginationContainer || !pageSizeSelect || !fileInput || !uploadBtn || !uploadStatusSpan) {
    console.warn("Workspace Documents Tab: One or more essential DOM elements not found. Script might not function correctly.");
    // return; // Or decide how to handle missing elements
}

function isColorLight(hexColor) {
    if (!hexColor || hexColor.length < 4) return true;
    let r, g, b;
    if (hexColor.length === 4) {
        r = parseInt(hexColor[1] + hexColor[1], 16);
        g = parseInt(hexColor[2] + hexColor[2], 16);
        b = parseInt(hexColor[3] + hexColor[3], 16);
    } else {
        r = parseInt(hexColor.substring(1, 3), 16);
        g = parseInt(hexColor.substring(3, 5), 16);
        b = parseInt(hexColor.substring(5, 7), 16);
    }
    const brightness = ((r * 299) + (g * 587) + (b * 114)) / 1000;
    return brightness > 150;
}

// ------------- Event Listeners -------------
if (pageSizeSelect) {
    pageSizeSelect.addEventListener("change", (e) => {
        pageSize = parseInt(e.target.value, 10);
        currentPage = 1;
        fetchUserDocuments();
    });
}

if (docMetadataForm) {
    docMetadataForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const docSaveBtn = document.getElementById("doc-save-btn");
        if (!docSaveBtn) return;
        docSaveBtn.disabled = true;
        docSaveBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Saving...`;

        const docId = document.getElementById("doc-id").value;
        const payload = {
            title: document.getElementById("doc-title").value.trim(),
            abstract: document.getElementById("doc-abstract").value.trim(),
            keywords: document.getElementById("doc-keywords").value.trim(),
            publication_date: document.getElementById("doc-publication-date").value.trim(),
            authors: document.getElementById("doc-authors").value.trim(),
        };

        if (typeof payload.keywords === "string") {
            payload.keywords = payload.keywords.split(",").map(kw => kw.trim()).filter(Boolean);
        }
        if (typeof payload.authors === "string") {
            payload.authors = payload.authors.split(",").map(a => a.trim()).filter(Boolean);
        }

        if (window.enable_document_classification == 'True') { // Check against string 'True'
                const classificationSelect = document.getElementById("doc-classification");
                if(classificationSelect) {
                payload.document_classification = classificationSelect.value;
                }
        }

        fetch(`/api/documents/${docId}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        })
            .then(r => r.ok ? r.json() : r.json().then(err => Promise.reject(err)))
            .then(updatedDoc => {
                if (docMetadataModalEl) docMetadataModalEl.hide();
                fetchUserDocuments(); // Refresh the table
            })
            .catch(err => {
                console.error("Error updating document:", err);
                alert("Error updating document: " + (err.error || err.message || "Unknown error"));
            })
            .finally(() => {
                docSaveBtn.disabled = false;
                docSaveBtn.textContent = "Save Metadata";
            });
    });
}

if (uploadBtn && fileInput && uploadStatusSpan) {
    uploadBtn.addEventListener("click", () => {
        const files = fileInput.files;
        if (!files || files.length === 0) {
            alert("Please select at least one file to upload.");
            return;
        }

        uploadBtn.disabled = true;
        uploadStatusSpan.textContent = `Uploading ${files.length} file(s)...`;
        uploadBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Uploading...`;

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append("file", files[i]);
        }

        fetch("/api/documents/upload", {
            method: "POST",
            body: formData,
        })
            .then(response => response.ok ? response.json() : response.json().then(err => Promise.reject(err)))
            .then(data => {
                const docIds = data.document_ids || (data.document_id ? [data.document_id] : []);
                const successCount = docIds.length;
                const totalCount = files.length;

                if (successCount > 0) {
                    console.log(`Successfully started processing for ${successCount} document(s).`);
                    fetchUserDocuments(); // Refresh list immediately for placeholders
                    docIds.forEach(docId => pollDocumentStatus(docId)); // Poll each new doc
                }

                if (data.errors && data.errors.length > 0) {
                    alert(`Upload partially failed:\n- ${data.errors.join('\n- ')}`);
                } else if (successCount === 0 && data.error) {
                    alert("Upload failed: " + data.error);
                } else if (successCount < totalCount) {
                    alert(`Successfully uploaded ${successCount} out of ${totalCount} files. Some may have failed.`);
                }

                fileInput.value = ""; // Clear file input
            })
            .catch(err => {
                console.error("Upload failed:", err);
                alert("Upload failed: " + (err.error || err.message || "Unknown error"));
            })
            .finally(() => {
                uploadBtn.disabled = false;
                uploadBtn.innerHTML = "Upload Document(s)";
                uploadStatusSpan.textContent = "";
            });
    });
}

// ------------- Document Functions -------------
function fetchUserDocuments() {
    if (!documentsTableBody) return; // Don't proceed if table body isn't found
    documentsTableBody.innerHTML = '<tr><td colspan="4" class="text-center p-4"><div class="spinner-border spinner-border-sm" role="status"><span class="visually-hidden">Loading...</span></div> Loading documents...</td></tr>';

    fetch(`/api/documents?page=${currentPage}&page_size=${pageSize}`)
        .then(response => response.ok ? response.json() : response.json().then(err => Promise.reject(err)))
        .then(data => {
            documentsTableBody.innerHTML = ""; // Clear loading/existing rows
            if (!data.documents || data.documents.length === 0) {
                documentsTableBody.innerHTML = '<tr><td colspan="4" class="text-center p-4 text-muted">No documents found. Upload a document to get started.</td></tr>';
            } else {
                data.documents.forEach(doc => renderDocumentRow(doc));
            }
            renderPaginationControls(data.page, data.page_size, data.total_count);
        })
        .catch(error => {
            console.error("Error fetching documents:", error);
            documentsTableBody.innerHTML = `<tr><td colspan="4" class="text-center text-danger p-4">Error loading documents: ${error.error || error.message || 'Unknown error'}</td></tr>`;
            renderPaginationControls(1, pageSize, 0); // Show empty pagination
        });
}
// Make fetchUserDocuments globally available for workspace-init.js
window.fetchUserDocuments = fetchUserDocuments;

function renderDocumentRow(doc) {
    if (!documentsTableBody) return;
    const docId = doc.id;
    const pct = parseInt(doc.percentage_complete, 10) || 0;
    const docStatus = doc.status || "";
    const isComplete = pct >= 100 || docStatus.toLowerCase().includes("complete") || docStatus.toLowerCase().includes("error"); // Treat error as complete for UI purposes
    const hasError = docStatus.toLowerCase().includes("error");

    // Main document row
    const docRow = document.createElement("tr");
    docRow.id = `doc-row-${docId}`;
    docRow.innerHTML = `
        <td class="align-middle">
            ${isComplete && !hasError ?
                `<button class="btn btn-link p-0" onclick="window.toggleDetails('${docId}')" title="Show/Hide Details">
                    <span id="arrow-icon-${docId}" class="bi bi-chevron-right"></span>
                    </button>` :
                    (hasError ? '<span class="text-danger" title="Processing Error"><i class="bi bi-exclamation-triangle-fill"></i></span>' : '<span class="text-muted" title="Processing..."><i class="bi bi-hourglass-split"></i></span>')
            }
        </td>
        <td class="align-middle" title="${escapeHtml(doc.file_name || "")}">${escapeHtml(doc.file_name || "")}</td>
        <td class="align-middle" title="${escapeHtml(doc.title || "")}">${escapeHtml(doc.title || "")}</td>
        <td class="align-middle">
            <button class="btn btn-sm btn-danger" onclick="window.deleteDocument('${docId}')" title="Delete Document">
                <i class="bi bi-trash-fill"></i>
            </button>
            ${isComplete && !hasError ?
                `<button class="btn btn-sm btn-primary ms-1" onclick="window.redirectToChat('${docId}')" title="Search in Chat">
                    <i class="bi bi-chat-dots-fill"></i> Chat
                    </button>` :
                ''
            }
        </td>
    `;
    documentsTableBody.appendChild(docRow);

    // Details row (collapsible) - only if complete and no error
    if (isComplete && !hasError) {
        const detailsRow = document.createElement("tr");
        detailsRow.id = `details-row-${docId}`;
        detailsRow.style.display = "none"; // Initially hidden

        let classificationDisplayHTML = '';
        if (window.enable_document_classification == 'True') {
                classificationDisplayHTML += `<p><strong>Classification:</strong> `; // Start the paragraph
                const currentLabel = doc.document_classification || null;
                const categories = window.classification_categories || []; // Ensure it's an array
                const category = categories.find(cat => cat.label === currentLabel);

                if (category) {
                    const bgColor = category.color;
                    const textColorClass = isColorLight(bgColor) ? 'text-dark' : '';
                    classificationDisplayHTML += `<span class="classification-badge ${textColorClass}" style="background-color: ${escapeHtml(bgColor)};">${escapeHtml(category.label)}</span>`;
                } else if (currentLabel) {
                    classificationDisplayHTML += `<span class="badge bg-warning text-dark" title="Category definition not found">${escapeHtml(currentLabel)} (?)</span>`;
                } else {
                    classificationDisplayHTML += `<span class="badge bg-secondary">None</span>`;
                }
                classificationDisplayHTML += `</p>`; // End the paragraph
            } else {
                classificationDisplayHTML = '<p><strong>Classification:</strong> Not Enabled</p>';
            }


        let detailsHtml = `
            <td colspan="4">
                <div class="bg-light p-3 border rounded small">
                    ${classificationDisplayHTML}
                    <p class="mb-1"><strong>Version:</strong> ${escapeHtml(doc.version || "N/A")}</p>
                    <p class="mb-1"><strong>Authors:</strong> ${escapeHtml(Array.isArray(doc.authors) ? doc.authors.join(", ") : doc.authors || "N/A")}</p>
                    <p class="mb-1"><strong>Pages:</strong> ${escapeHtml(doc.number_of_pages || "N/A")}</p>
                    <p class="mb-1"><strong>Citations:</strong> ${doc.enhanced_citations ? '<span class="badge bg-success">Enhanced</span>' : '<span class="badge bg-secondary">Standard</span>'}</p>
                    <p class="mb-1"><strong>Publication Date:</strong> ${escapeHtml(doc.publication_date || "N/A")}</p>
                    <p class="mb-1"><strong>Keywords:</strong> ${escapeHtml(Array.isArray(doc.keywords) ? doc.keywords.join(", ") : doc.keywords || "N/A")}</p>
                    <p class="mb-0"><strong>Abstract:</strong> ${escapeHtml(doc.abstract || "N/A")}</p>
                    <hr class="my-2">
                    <button class="btn btn-sm btn-info" onclick="window.onEditDocument('${docId}')" title="Edit Metadata">
                        <i class="bi bi-pencil-fill"></i> Edit Metadata
                    </button>
        `;

        if (window.enable_extract_meta_data == 'True') { // Check string 'True'
            detailsHtml += `
                <button class="btn btn-sm btn-warning ms-2" onclick="window.onExtractMetadata('${docId}', event)" title="Re-run Metadata Extraction">
                    <i class="bi bi-magic"></i> Extract Metadata
                </button>
            `;
        }

        detailsHtml += `</div></td>`;
        detailsRow.innerHTML = detailsHtml;
        documentsTableBody.appendChild(detailsRow);
    }

    // Progress/status row if incomplete or has error
    if (!isComplete || hasError) {
        const statusRow = document.createElement("tr");
        statusRow.id = `status-row-${docId}`;
        statusRow.innerHTML = `
            <td colspan="4">
                ${hasError ?
                    `<div class="alert alert-danger alert-sm py-1 px-2 mb-0" role="alert">
                        <i class="bi bi-exclamation-triangle-fill me-1"></i> Error: ${escapeHtml(docStatus)}
                        </div>` :
                    (pct < 100 ?
                        `<div class="progress" style="height: 10px;">
                            <div id="progress-bar-${docId}" class="progress-bar progress-bar-striped progress-bar-animated bg-info" role="progressbar" style="width: ${pct}%;" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100"></div>
                        </div>
                        <small class="text-muted" id="status-text-${docId}">Status: ${escapeHtml(docStatus)} (${pct}%)</small>` :
                        `<small class="text-muted">Status: Processing...</small>`
                    )
                }
            </td>
        `;
        documentsTableBody.appendChild(statusRow);

        if (!isComplete && !hasError) {
            pollDocumentStatus(docId);
        }
    }
}

function renderPaginationControls(page, pageSize, totalCount) {
    if (!paginationContainer) return;
    paginationContainer.innerHTML = ""; // clear old
    const totalPages = Math.ceil(totalCount / pageSize);

    if (totalPages <= 1) return; // Don't show pagination if only one page

    // Previous
    const prevBtn = document.createElement("button");
    prevBtn.innerHTML = '« <span class="d-none d-sm-inline">Previous</span>';
    prevBtn.classList.add("btn", "btn-sm", "btn-outline-secondary");
    prevBtn.disabled = (page <= 1);
    prevBtn.onclick = () => {
        if (currentPage > 1) {
            currentPage -= 1;
            fetchUserDocuments();
        }
    };
    paginationContainer.appendChild(prevBtn);

    // Page Numbers
    const maxButtons = 5;
    let startPage = Math.max(1, page - Math.floor(maxButtons / 2));
    let endPage = Math.min(totalPages, startPage + maxButtons - 1);
    startPage = Math.max(1, endPage - maxButtons + 1);

    if (startPage > 1) {
        const ellipsisStart = document.createElement('span');
        ellipsisStart.classList.add('align-self-end', 'px-1');
        ellipsisStart.innerHTML = '…';
        paginationContainer.appendChild(ellipsisStart);
    }

    for (let p = startPage; p <= endPage; p++) {
        const pageBtn = document.createElement("button");
        pageBtn.textContent = p;
        pageBtn.classList.add("btn", "btn-sm", p === page ? "btn-primary" : "btn-outline-secondary");
        pageBtn.onclick = () => {
            currentPage = p;
            fetchUserDocuments();
        };
        paginationContainer.appendChild(pageBtn);
    }

    if (endPage < totalPages) {
        const ellipsisEnd = document.createElement('span');
        ellipsisEnd.classList.add('align-self-end', 'px-1');
        ellipsisEnd.innerHTML = '…';
        paginationContainer.appendChild(ellipsisEnd);
    }

    // Next
    const nextBtn = document.createElement("button");
    nextBtn.innerHTML = '<span class="d-none d-sm-inline">Next</span> »';
    nextBtn.classList.add("btn", "btn-sm", "btn-outline-secondary");
    nextBtn.disabled = (page >= totalPages);
    nextBtn.onclick = () => {
        if (currentPage < totalPages) {
            currentPage += 1;
            fetchUserDocuments();
        }
    };
    paginationContainer.appendChild(nextBtn);
}

// Function needs to be global for onclick
window.toggleDetails = function (docId) {
    const detailsRow = document.getElementById(`details-row-${docId}`);
    const arrowIcon = document.getElementById(`arrow-icon-${docId}`);
    if (!detailsRow || !arrowIcon) return;

    if (detailsRow.style.display === "none") {
        detailsRow.style.display = "";
        arrowIcon.classList.remove("bi-chevron-right");
        arrowIcon.classList.add("bi-chevron-down");
    } else {
        detailsRow.style.display = "none";
        arrowIcon.classList.remove("bi-chevron-down");
        arrowIcon.classList.add("bi-chevron-right");
    }
};

function pollDocumentStatus(documentId) {
    if (activePolls.has(documentId)) return; // Already polling
    activePolls.add(documentId);
    // console.log(`Starting polling for ${documentId}`);

    const pollInterval = setInterval(() => {
        fetch(`/api/documents/${documentId}`)
            .then(r => r.ok ? r.json() : r.json().then(err => Promise.reject(err)))
            .then(doc => {
                const pct = parseInt(doc.percentage_complete, 10) || 0;
                const docStatus = doc.status || "";
                // Determine completion status (includes error state as 'complete' for polling purposes)
                const isComplete = pct >= 100 || docStatus.toLowerCase().includes("complete") || docStatus.toLowerCase().includes("error");
                // Specifically check if the completion state is due to an error
                const hasError = docStatus.toLowerCase().includes("error");

                // --- Update Progress/Status if NOT complete ---
                if (!isComplete) {
                    const progressBar = document.getElementById(`progress-bar-${documentId}`);
                    const statusText = document.getElementById(`status-text-${documentId}`);

                    if (progressBar) {
                        progressBar.style.width = pct + "%";
                        progressBar.setAttribute("aria-valuenow", pct);
                    }
                    if (statusText) {
                        statusText.textContent = `Status: ${escapeHtml(docStatus)} (${pct}%)`;
                    }
                }
                // --- Handle Completion ---
                else {
                    // console.log(`Polling detected completion for ${documentId}. Status: ${docStatus}`);
                    clearInterval(pollInterval);
                    activePolls.delete(documentId);

                    // Remove the status/progress row immediately.
                    const statusRow = document.getElementById(`status-row-${documentId}`);
                    if (statusRow) {
                        statusRow.remove();
                    } else {
                        // console.warn(`Status row not found for completed document ${documentId}`);
                    }

                    console.log(`Triggering documents refresh after completion of ${documentId}.`);
                    fetchUserDocuments();

                }
            })
            .catch(err => {
                console.error(`Error polling document ${documentId}:`, err);
                clearInterval(pollInterval);
                activePolls.delete(documentId);

                // Update UI to show polling failed
                const statusRow = document.getElementById(`status-row-${documentId}`);
                if (statusRow) {
                    statusRow.innerHTML = `<td colspan="4"><div class="alert alert-warning alert-sm py-1 px-2 mb-0" role="alert"><i class="bi bi-exclamation-triangle-fill me-1"></i>Could not retrieve status.</div></td>`;
                }
                // Update main row icon to show warning?
                const mainRow = document.getElementById(`doc-row-${documentId}`);
                if (mainRow && mainRow.cells[0]) {
                    // Avoid overwriting if it's already showing a processing error from the server
                    const currentIcon = mainRow.cells[0].querySelector('span.text-danger i.bi-exclamation-triangle-fill');
                    if (!currentIcon) {
                         mainRow.cells[0].innerHTML = '<span class="text-warning" title="Status Unavailable"><i class="bi bi-question-circle-fill"></i></span>';
                    }
                }
            });
    }, 5000); // Poll every 5 seconds
}
// Make pollDocumentStatus globally available if needed elsewhere, though currently internal call
// window.pollDocumentStatus = pollDocumentStatus;


// Function needs to be global for onclick
window.onEditDocument = function(docId) {
    if (!docMetadataModalEl) return;
    fetch(`/api/documents/${docId}`)
        .then(r => r.ok ? r.json() : r.json().then(err => Promise.reject(err)))
        .then(doc => {
            document.getElementById("doc-id").value = doc.id;
            document.getElementById("doc-title").value = doc.title || "";
            document.getElementById("doc-abstract").value = doc.abstract || "";
            document.getElementById("doc-keywords").value = Array.isArray(doc.keywords) ? doc.keywords.join(", ") : (doc.keywords || "");
            document.getElementById("doc-publication-date").value = doc.publication_date || "";
            document.getElementById("doc-authors").value = Array.isArray(doc.authors) ? doc.authors.join(", ") : (doc.authors || "");

            if (window.enable_document_classification == 'True') {
                const classificationSelect = document.getElementById("doc-classification");
                if (classificationSelect) {
                    classificationSelect.value = doc.document_classification || "";
                    if (classificationSelect.selectedIndex === -1 && classificationSelect.options.length > 0) {
                        classificationSelect.value = "";
                    }
                }
            }

            docMetadataModalEl.show();
        })
        .catch(err => {
            console.error("Error retrieving document for edit:", err);
            alert("Error retrieving document details: " + (err.error || err.message || "Unknown error"));
        });
}

// Function needs to be global for onclick
window.onExtractMetadata = function (docId, event) {
    if (!confirm("Run metadata extraction for this document? This may overwrite existing metadata.")) {
        return;
    }
    const extractBtn = event ? event.target.closest('button') : null;
    if (extractBtn) {
        extractBtn.disabled = true;
        extractBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>Extracting...`;
    }

    fetch(`/api/documents/${docId}/extract_metadata`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })
        .then(r => r.ok ? r.json() : r.json().then(err => Promise.reject(err)))
        .then(data => {
            console.log("Metadata extraction started/completed:", data);
            fetchUserDocuments(); // Refresh to show updates
            // Hide details as they might be outdated now
            const detailsRow = document.getElementById(`details-row-${docId}`);
            if (detailsRow) detailsRow.style.display = 'none';
            const arrowIcon = document.getElementById(`arrow-icon-${docId}`);
            if (arrowIcon) arrowIcon.className = 'bi bi-chevron-right';
            // Optional success message
            // alert(data.message || "Metadata extraction initiated.");
        })
        .catch(err => {
            console.error("Error calling extract metadata:", err);
            alert("Error extracting metadata: " + (err.error || err.message || "Unknown error"));
        })
        .finally(() => {
            if (extractBtn) {
                extractBtn.disabled = false;
                extractBtn.innerHTML = '<i class="bi bi-magic"></i> Extract Metadata';
            }
        });
};

// Function needs to be global for onclick
window.deleteDocument = function(documentId, event) {
    if (!confirm("Are you sure you want to delete this document? This action cannot be undone.")) return;

    const deleteBtn = event ? event.target.closest('button') : null;
    if (deleteBtn) {
        deleteBtn.disabled = true;
        deleteBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>`; // Just spinner
    }

    fetch(`/api/documents/${documentId}`, { method: "DELETE" })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => Promise.reject(data));
            }
            return response.json();
        })
        .then(data => {
            fetchUserDocuments(); // Refresh the table
        })
        .catch(error => {
            console.error("Error deleting document:", error);
            alert("Error deleting document: " + (error.error || error.message || "Unknown error"));
            if (deleteBtn) { // Re-enable button on error
                deleteBtn.disabled = false;
                deleteBtn.innerHTML = '<i class="bi bi-trash-fill"></i>'; // Restore icon
            }
        });
}

// Function needs to be global for onclick
window.redirectToChat = function(documentId) {
    window.location.href = `/chats?search_documents=true&doc_scope=personal&document_id=${documentId}`;
}