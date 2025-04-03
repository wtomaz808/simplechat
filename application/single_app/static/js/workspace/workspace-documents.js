// static/js/workspace/workspace-documents.js

import { escapeHtml } from "./workspace-utils.js";

// ... (keep existing variables like currentPage, pageSize, activePolls, DOM elements) ...
let currentPage = 1;
let pageSize = 10;
const activePolls = new Set();

const paginationContainer = document.getElementById("pagination-container");
const pageSizeSelect = document.getElementById("page-size-select");
const fileInput = document.getElementById("file-input");
const uploadBtn = document.getElementById("upload-btn");
const uploadStatusSpan = document.getElementById("upload-status");
const documentsTableBody = document.querySelector("#documents-table tbody");
const docMetadataModalEl = document.getElementById("docMetadataModal") ? new bootstrap.Modal(document.getElementById("docMetadataModal")) : null;
const docMetadataForm = document.getElementById("doc-metadata-form");

function isColorLight(hexColor) {
    if (!hexColor) return true; // Default to light if no color
    const cleanHex = hexColor.startsWith('#') ? hexColor.substring(1) : hexColor;
    if (cleanHex.length < 3) return true;

    let r, g, b;
    try {
        if (cleanHex.length === 3) {
            r = parseInt(cleanHex[0] + cleanHex[0], 16);
            g = parseInt(cleanHex[1] + cleanHex[1], 16);
            b = parseInt(cleanHex[2] + cleanHex[2], 16);
        } else if (cleanHex.length >= 6) {
            r = parseInt(cleanHex.substring(0, 2), 16);
            g = parseInt(cleanHex.substring(2, 4), 16);
            b = parseInt(cleanHex.substring(4, 6), 16);
        } else {
            return true; // Invalid hex length
        }
    } catch (e) {
        console.warn("Could not parse hex color:", hexColor, e);
        return true; // Default to light on parsing error
    }

    if (isNaN(r) || isNaN(g) || isNaN(b)) return true; // Parsing failed

    // Calculate luminance using the standard formula (perceived brightness)
    const luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
    // console.log(`Color: ${hexColor}, R:${r} G:${g} B:${b}, Lum: ${luminance.toFixed(3)}`);
    return luminance > 0.5; // Threshold can be adjusted (0.5 is common)
}

// ------------- Event Listeners -------------
if (pageSizeSelect) {
    pageSizeSelect.addEventListener("change", (e) => {
        pageSize = parseInt(e.target.value, 10);
        currentPage = 1;
        fetchUserDocuments();
    });
}

if (docMetadataForm && docMetadataModalEl) { // Check both exist
    docMetadataForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const docSaveBtn = document.getElementById("doc-save-btn");
        if (!docSaveBtn) return;
        docSaveBtn.disabled = true;
        docSaveBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Saving...`;

        const docId = document.getElementById("doc-id").value;
        const payload = {
            title: document.getElementById("doc-title")?.value.trim() || null,
            abstract: document.getElementById("doc-abstract")?.value.trim() || null,
            keywords: document.getElementById("doc-keywords")?.value.trim() || null,
            publication_date: document.getElementById("doc-publication-date")?.value.trim() || null,
            authors: document.getElementById("doc-authors")?.value.trim() || null,
        };

        // Process keywords and authors into arrays
        if (payload.keywords) {
            payload.keywords = payload.keywords.split(",").map(kw => kw.trim()).filter(Boolean);
        } else {
             payload.keywords = []; // Ensure it's an array or null if backend expects it
        }
        if (payload.authors) {
            payload.authors = payload.authors.split(",").map(a => a.trim()).filter(Boolean);
        } else {
             payload.authors = []; // Ensure it's an array or null
        }

        // Add classification if enabled
        if (window.enable_document_classification === 'true') { // Check boolean true
            const classificationSelect = document.getElementById("doc-classification");
            payload.document_classification = classificationSelect?.value || null;
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

// *** MODIFIED UPLOAD BUTTON HANDLER ***
if (uploadBtn && fileInput && uploadStatusSpan) {
    uploadBtn.addEventListener("click", async () => {
        const files = fileInput.files;
        if (!files || files.length === 0) {
            alert("Please select at least one file to upload.");
            return;
        }

        uploadBtn.disabled = true;
        uploadBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Preparing...`;
        uploadStatusSpan.textContent = `Preparing ${files.length} file(s)...`;

        const formData = new FormData();
        const filesToUpload = [];
        let conversionErrors = 0;
        let filesProcessed = 0;

        for (const file of files) {
            filesProcessed++;
            
            uploadStatusSpan.textContent = `Preparing file: ${escapeHtml(file.name)} (${filesProcessed}/${files.length})...`;
            filesToUpload.push(file);
        } // End file processing loop

        // --- Rest of the upload logic (check filesToUpload, append, fetch, handle response, finally) ---
        // (This part remains the same as in the previous version)

         if (filesToUpload.length === 0) {
            uploadStatusSpan.textContent = "No files selected or processed.";
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = "Upload Document(s)";
            fileInput.value = "";
            return;
        }

        filesToUpload.forEach(file => {
            formData.append("file", file, file.name);
        });

        uploadStatusSpan.textContent = `Uploading ${filesToUpload.length} file(s)...`;
        uploadBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Uploading...`;

        try {
            const response = await fetch("/api/documents/upload", {
                method: "POST",
                body: formData,
            });
            const data = await response.json();
            if (!response.ok) {
                 throw new Error(data.error || `Server responded with status ${response.status}`);
            }

            const docIds = data.document_ids || (data.document_id ? [data.document_id] : []);
            const successCount = docIds.length;
            const totalUploaded = filesToUpload.length;

            if (successCount > 0) {
                console.log(`Successfully started server processing for ${successCount} document(s).`);
                fetchUserDocuments();
                docIds.forEach(docId => pollDocumentStatus(docId));
            }

            let finalMessage = "";
            if (successCount === totalUploaded) finalMessage += `Uploaded ${successCount} file(s) for processing.`;
            else if (successCount < totalUploaded) finalMessage += `Server accepted ${successCount}/${totalUploaded} uploaded file(s).`;
            if (data.errors && data.errors.length > 0) finalMessage += ` Server errors: ${data.errors.join(', ')}`;

            uploadStatusSpan.textContent = finalMessage.trim() || "Upload processed.";
            fileInput.value = "";

        } catch (err) {
            console.error("Upload failed:", err);
            const errorMsg = `Upload failed: ${err.message || "Unknown network or server error"}`;
            alert(errorMsg);
            uploadStatusSpan.textContent = errorMsg;
        } finally {
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = "Upload Document(s)";
        }
    });
}

// ------------- Document Functions (fetchUserDocuments, renderDocumentRow, etc.) -------------
// Keep the existing functions fetchUserDocuments, renderDocumentRow, renderPaginationControls,
// toggleDetails, pollDocumentStatus, onEditDocument, onExtractMetadata, deleteDocument, redirectToChat
// ... (Paste the existing functions here, no changes needed to them based on the conversion logic) ...

// --- PASTE THE FOLLOWING FUNCTIONS FROM YOUR ORIGINAL CODE HERE ---
// fetchUserDocuments()
// renderDocumentRow(doc)
// renderPaginationControls(page, pageSize, totalCount)
// window.toggleDetails = function (docId) { ... }
// pollDocumentStatus(documentId)
// window.onEditDocument = function(docId) { ... }
// window.onExtractMetadata = function (docId, event) { ... }
// window.deleteDocument = function(documentId, event) { ... } // Note: Removed 'event' param if not used
// window.redirectToChat = function(documentId) { ... }
// --- END PASTE ---


// Make fetchUserDocuments globally available for workspace-init.js or other modules
window.fetchUserDocuments = fetchUserDocuments;


// ------------- START: PASTE YOUR EXISTING FUNCTIONS HERE -------------

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

function renderDocumentRow(doc) {
    if (!documentsTableBody) return;
    const docId = doc.id;
    // Robust check for percentage complete
    const pctString = String(doc.percentage_complete);
    const pct = /^\d+(\.\d+)?$/.test(pctString) ? parseFloat(pctString) : 0;
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
                    (hasError ? `<span class="text-danger" title="Processing Error: ${escapeHtml(docStatus)}"><i class="bi bi-exclamation-triangle-fill"></i></span>`
                             : `<span class="text-muted" title="Processing: ${escapeHtml(docStatus)}"><i class="bi bi-hourglass-split"></i></span>`)
            }
        </td>
        <td class="align-middle" title="${escapeHtml(doc.file_name || "")}">${escapeHtml(doc.file_name || "")}</td>
        <td class="align-middle" title="${escapeHtml(doc.title || "")}">${escapeHtml(doc.title || "N/A")}</td>
        <td class="align-middle">
            <button class="btn btn-sm btn-danger" onclick="window.deleteDocument('${docId}', event)" title="Delete Document">
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
        // Check using boolean comparison now that we use tojson
        if (window.enable_document_classification === 'true') {
                classificationDisplayHTML += `<p class="mb-1"><strong>Classification:</strong> `; // Start the paragraph
                const currentLabel = doc.document_classification || null;
                const categories = window.classification_categories || []; // Ensure it's an array
                const category = categories.find(cat => cat.label === currentLabel);

                if (category) {
                    const bgColor = category.color || '#6c757d'; // Default to secondary color if missing
                    const useDarkText = isColorLight(bgColor);
                    const textColorClass = useDarkText ? 'text-dark' : '';
                    classificationDisplayHTML += `<span class="classification-badge ${textColorClass}" style="background-color: ${escapeHtml(bgColor)};">${escapeHtml(category.label)}</span>`;
                } else if (currentLabel) {
                    // If label exists but no matching category (config mismatch?)
                    classificationDisplayHTML += `<span class="badge bg-warning text-dark" title="Category config not found">${escapeHtml(currentLabel)} (?)</span>`;
                } else {
                    classificationDisplayHTML += `<span class="badge bg-secondary">None</span>`;
                }
                classificationDisplayHTML += `</p>`; // End the paragraph
            }
            // No 'else' needed, classification is just omitted if not enabled

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
                    <div class="d-flex flex-wrap gap-2">
                         <button class="btn btn-sm btn-info" onclick="window.onEditDocument('${docId}')" title="Edit Metadata">
                            <i class="bi bi-pencil-fill"></i> Edit Metadata
                         </button>
        `;

        // Check using boolean comparison
        if (window.enable_extract_meta_data === 'true') {
            detailsHtml += `
                <button class="btn btn-sm btn-warning" onclick="window.onExtractMetadata('${docId}', event)" title="Re-run Metadata Extraction">
                    <i class="bi bi-magic"></i> Extract Metadata
                </button>
            `;
        }

        detailsHtml += `</div></div></td>`; // Close flex wrapper, main div, td
        detailsRow.innerHTML = detailsHtml;
        documentsTableBody.appendChild(detailsRow);
    }

    // Progress/status row if incomplete or has error
    if (!isComplete || hasError) {
        const statusRow = document.createElement("tr");
        statusRow.id = `status-row-${docId}`;
        // Display error prominently if it occurred
        if (hasError) {
             statusRow.innerHTML = `
                <td colspan="4">
                    <div class="alert alert-danger alert-sm py-1 px-2 mb-0 small" role="alert">
                        <i class="bi bi-exclamation-triangle-fill me-1"></i> Error: ${escapeHtml(docStatus)}
                    </div>
                </td>`;
        } else if (pct < 100) { // Only show progress if not complete and no error
             statusRow.innerHTML = `
                <td colspan="4">
                    <div class="progress" style="height: 10px;" title="Status: ${escapeHtml(docStatus)} (${pct.toFixed(0)}%)">
                        <div id="progress-bar-${docId}" class="progress-bar progress-bar-striped progress-bar-animated bg-info" role="progressbar" style="width: ${pct}%;" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                    <div class="text-muted text-end small" id="status-text-${docId}">${escapeHtml(docStatus)} (${pct.toFixed(0)}%)</div>
                </td>`;
        } else {
             // Should generally not reach here if logic is correct, but as a fallback:
             statusRow.innerHTML = `
                <td colspan="4">
                    <small class="text-muted">Status: Finalizing...</small>
                </td>`;
        }

        documentsTableBody.appendChild(statusRow);

        // Start polling only if processing is actually ongoing (not complete, not error)
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

    // Previous Button
    const prevLi = document.createElement('li');
    prevLi.classList.add('page-item');
    if (page <= 1) prevLi.classList.add('disabled');
    const prevA = document.createElement('a');
    prevA.classList.add('page-link');
    prevA.href = '#';
    prevA.innerHTML = '«'; // Previous arrow
    prevA.addEventListener('click', (e) => {
        e.preventDefault();
        if (currentPage > 1) {
            currentPage -= 1;
            fetchUserDocuments();
        }
    });
    prevLi.appendChild(prevA);

    // Next Button
    const nextLi = document.createElement('li');
    nextLi.classList.add('page-item');
    if (page >= totalPages) nextLi.classList.add('disabled');
    const nextA = document.createElement('a');
    nextA.classList.add('page-link');
    nextA.href = '#';
    nextA.innerHTML = '»'; // Next arrow
    nextA.addEventListener('click', (e) => {
        e.preventDefault();
        if (currentPage < totalPages) {
            currentPage += 1;
            fetchUserDocuments();
        }
    });
    nextLi.appendChild(nextA);


    // Determine page numbers to display
    const maxPagesToShow = 5; // Max number of page links shown (excluding prev/next)
    let startPage = 1;
    let endPage = totalPages;

    if (totalPages > maxPagesToShow) {
        let maxPagesBeforeCurrent = Math.floor(maxPagesToShow / 2);
        let maxPagesAfterCurrent = Math.ceil(maxPagesToShow / 2) - 1;

        if (page <= maxPagesBeforeCurrent) {
            // Near the beginning
            startPage = 1;
            endPage = maxPagesToShow;
        } else if (page + maxPagesAfterCurrent >= totalPages) {
            // Near the end
            startPage = totalPages - maxPagesToShow + 1;
            endPage = totalPages;
        } else {
            // In the middle
            startPage = page - maxPagesBeforeCurrent;
            endPage = page + maxPagesAfterCurrent;
        }
    }

    // Create pagination UL element
    const ul = document.createElement('ul');
    ul.classList.add('pagination', 'pagination-sm', 'mb-0'); // mb-0 to remove bottom margin if needed

    // Add Previous button
    ul.appendChild(prevLi);

    // Add first page and ellipsis if needed
    if (startPage > 1) {
        const firstLi = document.createElement('li');
        firstLi.classList.add('page-item');
        const firstA = document.createElement('a');
        firstA.classList.add('page-link');
        firstA.href = '#';
        firstA.textContent = '1';
        firstA.addEventListener('click', (e) => { e.preventDefault(); currentPage = 1; fetchUserDocuments(); });
        firstLi.appendChild(firstA);
        ul.appendChild(firstLi);
        if (startPage > 2) {
             const ellipsisLi = document.createElement('li');
             ellipsisLi.classList.add('page-item', 'disabled');
             ellipsisLi.innerHTML = `<span class="page-link">...</span>`;
             ul.appendChild(ellipsisLi);
        }
    }

    // Add page number links
    for (let p = startPage; p <= endPage; p++) {
        const li = document.createElement('li');
        li.classList.add('page-item');
        if (p === page) {
            li.classList.add('active');
            li.setAttribute('aria-current', 'page');
        }
        const a = document.createElement('a');
        a.classList.add('page-link');
        a.href = '#';
        a.textContent = p;
        a.addEventListener('click', (e) => {
            e.preventDefault();
            if (currentPage !== p) {
                currentPage = p;
                fetchUserDocuments();
            }
        });
        li.appendChild(a);
        ul.appendChild(li);
    }

    // Add last page and ellipsis if needed
    if (endPage < totalPages) {
         if (endPage < totalPages - 1) {
             const ellipsisLi = document.createElement('li');
             ellipsisLi.classList.add('page-item', 'disabled');
             ellipsisLi.innerHTML = `<span class="page-link">...</span>`;
             ul.appendChild(ellipsisLi);
         }
        const lastLi = document.createElement('li');
        lastLi.classList.add('page-item');
        const lastA = document.createElement('a');
        lastA.classList.add('page-link');
        lastA.href = '#';
        lastA.textContent = totalPages;
        lastA.addEventListener('click', (e) => { e.preventDefault(); currentPage = totalPages; fetchUserDocuments(); });
        lastLi.appendChild(lastA);
        ul.appendChild(lastLi);
    }


    // Add Next button
    ul.appendChild(nextLi);

    // Append the UL to the container
    paginationContainer.appendChild(ul);
}


window.toggleDetails = function (docId) {
    const detailsRow = document.getElementById(`details-row-${docId}`);
    const arrowIcon = document.getElementById(`arrow-icon-${docId}`);
    if (!detailsRow || !arrowIcon) return;

    if (detailsRow.style.display === "none") {
        detailsRow.style.display = ""; // Use "" to revert to default table row display
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

    const intervalId = setInterval(() => {
        // Check if the document row still exists (it might be removed by deletion or page change)
        const docRow = document.getElementById(`doc-row-${documentId}`);
        const statusRow = document.getElementById(`status-row-${documentId}`);
        if (!docRow && !statusRow) { // If neither row exists, stop polling
            // console.log(`Stopping poll for ${documentId}: Rows not found.`);
            clearInterval(intervalId);
            activePolls.delete(documentId);
            return;
        }


        fetch(`/api/documents/${documentId}`)
            .then(r => {
                if (r.status === 404) { // Handle case where doc was deleted during polling
                    return Promise.reject(new Error('Document not found (likely deleted).'));
                }
                return r.ok ? r.json() : r.json().then(err => Promise.reject(err));
             })
            .then(doc => {
                // Robust check for percentage complete
                 const pctString = String(doc.percentage_complete);
                 const pct = /^\d+(\.\d+)?$/.test(pctString) ? parseFloat(pctString) : 0;
                 const docStatus = doc.status || "";
                 const isComplete = pct >= 100 || docStatus.toLowerCase().includes("complete") || docStatus.toLowerCase().includes("error");
                 const hasError = docStatus.toLowerCase().includes("error");

                // --- Update Progress/Status if NOT complete ---
                if (!isComplete && statusRow) {
                     const progressBar = statusRow.querySelector(`#progress-bar-${documentId}`);
                     const statusText = statusRow.querySelector(`#status-text-${documentId}`);

                     if (progressBar) {
                        progressBar.style.width = pct + "%";
                        progressBar.setAttribute("aria-valuenow", pct);
                        progressBar.parentNode.setAttribute('title', `Status: ${escapeHtml(docStatus)} (${pct.toFixed(0)}%)`); // Update progress bar title
                     }
                     if (statusText) {
                        statusText.textContent = `${escapeHtml(docStatus)} (${pct.toFixed(0)}%)`;
                     }
                }
                // --- Handle Completion ---
                else {
                    // console.log(`Polling detected completion/error for ${documentId}. Status: ${docStatus}`);
                    clearInterval(intervalId);
                    activePolls.delete(documentId);

                    // Remove the status/progress row as it's no longer needed.
                    if (statusRow) {
                        statusRow.remove();
                    }

                    // Re-render the specific document row to update icons and buttons
                    // This is safer than a full table refresh if many docs are polling
                     if (docRow) {
                        const parent = docRow.parentNode;
                        const detailsRow = document.getElementById(`details-row-${documentId}`);
                        // Remove existing rows for this doc before re-rendering
                        docRow.remove();
                        if (detailsRow) detailsRow.remove();
                        // Re-render using the latest doc data
                        renderDocumentRow(doc);
                     } else {
                         // If original row somehow gone, just refresh whole table
                         console.warn(`Doc row ${documentId} not found after completion, refreshing full list.`);
                         fetchUserDocuments();
                     }

                    // Optional: Add a visual cue for completion/error?
                    // const mainRow = document.getElementById(`doc-row-${documentId}`);
                    // if (mainRow) mainRow.classList.add(hasError ? 'table-danger' : 'table-success'); // Add temporary highlight

                }
            })
            .catch(err => {
                console.error(`Error polling document ${documentId}:`, err);
                clearInterval(intervalId);
                activePolls.delete(documentId);

                // Update UI to show polling failed if the status row still exists
                if (statusRow) {
                    statusRow.innerHTML = `<td colspan="4"><div class="alert alert-warning alert-sm py-1 px-2 mb-0 small" role="alert"><i class="bi bi-exclamation-triangle-fill me-1"></i>Could not retrieve status: ${escapeHtml(err.message || 'Polling failed')}</div></td>`;
                }
                // Update main row icon to show warning if it exists
                 if (docRow && docRow.cells[0]) {
                    // Avoid overwriting if it's already showing a processing error from the server
                     const currentIcon = docRow.cells[0].querySelector('span.text-danger i.bi-exclamation-triangle-fill');
                     if (!currentIcon) {
                         docRow.cells[0].innerHTML = '<span class="text-warning" title="Status Unavailable"><i class="bi bi-question-circle-fill"></i></span>';
                     }
                 }
            });
    }, 5000); // Poll every 5 seconds
}

window.onEditDocument = function(docId) {
    if (!docMetadataModalEl) {
        console.error("Metadata modal element not found.");
        return;
    }
    // Show loading state in modal?
    fetch(`/api/documents/${docId}`)
        .then(r => r.ok ? r.json() : r.json().then(err => Promise.reject(err)))
        .then(doc => {
            // Populate form fields, checking if elements exist
            const docIdInput = document.getElementById("doc-id");
            const docTitleInput = document.getElementById("doc-title");
            const docAbstractInput = document.getElementById("doc-abstract");
            const docKeywordsInput = document.getElementById("doc-keywords");
            const docPubDateInput = document.getElementById("doc-publication-date");
            const docAuthorsInput = document.getElementById("doc-authors");
            const classificationSelect = document.getElementById("doc-classification");

            if (docIdInput) docIdInput.value = doc.id;
            if (docTitleInput) docTitleInput.value = doc.title || "";
            if (docAbstractInput) docAbstractInput.value = doc.abstract || "";
            if (docKeywordsInput) docKeywordsInput.value = Array.isArray(doc.keywords) ? doc.keywords.join(", ") : (doc.keywords || "");
            if (docPubDateInput) docPubDateInput.value = doc.publication_date || "";
            if (docAuthorsInput) docAuthorsInput.value = Array.isArray(doc.authors) ? doc.authors.join(", ") : (doc.authors || "");

            // Check boolean correctly for classification
            if (window.enable_document_classification === 'true' && classificationSelect) {
                classificationSelect.value = doc.document_classification || "";
                // If the saved value is not in the options, reset to default "-- Select --"
                if (classificationSelect.selectedIndex === -1 && classificationSelect.options.length > 0) {
                    classificationSelect.value = "";
                }
                classificationSelect.closest('.mb-3').style.display = ''; // Ensure visible
            } else if (classificationSelect) {
                 classificationSelect.closest('.mb-3').style.display = 'none'; // Hide if not enabled
            }

            docMetadataModalEl.show();
        })
        .catch(err => {
            console.error("Error retrieving document for edit:", err);
            alert("Error retrieving document details: " + (err.error || err.message || "Unknown error"));
        });
}

window.onExtractMetadata = function (docId, event) {
    // Check boolean correctly
    if (window.enable_extract_meta_data !== 'true') {
        alert("Metadata extraction is not enabled.");
        return;
    }

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
        // Add CSRF token header if needed
    })
        .then(r => r.ok ? r.json() : r.json().then(err => Promise.reject(err)))
        .then(data => {
            console.log("Metadata extraction started/completed:", data);
            // Refresh the document list to show potentially updated metadata after a short delay
            // This assumes the backend updates the doc record synchronously or starts a background task
            // that will eventually be picked up by fetchUserDocuments or polling
            setTimeout(fetchUserDocuments, 1000); // Refresh after 1 second
            alert(data.message || "Metadata extraction process initiated.");

            // Hide details view as it might be outdated now
            const detailsRow = document.getElementById(`details-row-${docId}`);
            const arrowIcon = document.getElementById(`arrow-icon-${docId}`);
            if (detailsRow && detailsRow.style.display !== "none") {
                if (arrowIcon) window.toggleDetails(docId); // Use toggle to collapse it
            }

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

window.deleteDocument = function(documentId, event) { // Keep event param for button handling
    if (!confirm("Are you sure you want to delete this document? This action cannot be undone.")) return;

    const deleteBtn = event ? event.target.closest('button') : null;
    if (deleteBtn) {
        deleteBtn.disabled = true;
        // Make spinner smaller and match text color potentially
        deleteBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>`;
    }

    // Stop polling for this document if it's active
    if (activePolls.has(documentId)) {
        // Need to find the interval ID if stored, otherwise just remove from Set
         activePolls.delete(documentId); // Prevent new updates during deletion
         // Finding the actual interval ID to clear it here is complex without storing it globally.
         // Rely on the 404 check in the poll function to eventually stop it.
    }


    fetch(`/api/documents/${documentId}`, { method: "DELETE" })
        .then(response => {
            if (!response.ok) {
                // Try to parse error from JSON response
                return response.json().then(data => Promise.reject(data)).catch(() => {
                     // If JSON parsing fails, create a generic error
                     return Promise.reject({ error: `Server responded with status ${response.status}` });
                });
            }
            return response.json(); // Or response.text() if it returns simple confirmation
        })
        .then(data => {
            console.log("Document deleted successfully:", data);
            // Remove the rows directly for faster UI update
            const docRow = document.getElementById(`doc-row-${documentId}`);
            const detailsRow = document.getElementById(`details-row-${documentId}`);
            const statusRow = document.getElementById(`status-row-${documentId}`);
            if (docRow) docRow.remove();
            if (detailsRow) detailsRow.remove();
            if (statusRow) statusRow.remove();

            // Optional: Refresh the whole list if pagination counts might change significantly
            // fetchUserDocuments();
             // Check if table body is now empty
             if (documentsTableBody && documentsTableBody.childElementCount === 0) {
                 fetchUserDocuments(); // Refresh to show "No documents" message
             }

        })
        .catch(error => {
            console.error("Error deleting document:", error);
            alert("Error deleting document: " + (error.error || error.message || "Unknown error"));
            if (deleteBtn) { // Re-enable button on error ONLY if it still exists
                 const btnExists = document.body.contains(deleteBtn);
                 if (btnExists) {
                     deleteBtn.disabled = false;
                     deleteBtn.innerHTML = '<i class="bi bi-trash-fill"></i>'; // Restore icon
                 }
            }
        });
}

window.redirectToChat = function(documentId) {
    // Redirect to the chat page, passing the document ID as a query parameter
    // The chat page JS will need to read this parameter and potentially pre-select the document.
    window.location.href = `/chats?search_documents=true&doc_scope=personal&document_id=${documentId}`;
}

// ------------- END: PASTE YOUR EXISTING FUNCTIONS HERE -------------