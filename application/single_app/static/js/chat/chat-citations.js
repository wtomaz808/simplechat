// chat-citations.js

import { showToast } from "./chat-toast.js";
import { showLoadingIndicator, hideLoadingIndicator } from "./chat-loading-indicator.js";
import { toBoolean } from "./chat-utils.js";
import { fetchFileContent } from "./chat-input-actions.js";

const chatboxEl = document.getElementById("chatbox");

export function parseDocIdAndPage(citationId) {
  const underscoreIndex = citationId.lastIndexOf("_");
  if (underscoreIndex === -1) {
    return { docId: null, pageNumber: null };
  }
  const docId = citationId.substring(0, underscoreIndex);
  const pageNumber = citationId.substring(underscoreIndex + 1);
  return { docId, pageNumber };
}

export function parseCitations(message) {
  // Regex to match patterns like:
  //   (Source: FILENAME, Pages: 6)
  //   (Source: FILENAME, Pages: 28-29)
  //   (Source: FILENAME, Pages: 7, 9)
  // followed by bracketed references, e.g. [#someId_7; #someId_9]
  //
  // 1) "filename" is captured by ([^,]+)
  // 2) "pages"   is captured by ([^)]+)
  // 3) The bracket section is captured by ((?:\[#.*?\]\s*)+)
  const citationRegex = /\(Source:\s*([^,]+),\s*Page(?:s)?:\s*([^)]+)\)\s*((?:\[#.*?\]\s*)+)/gi;

  return message.replace(citationRegex, (whole, filename, pages, bracketSection) => {
    // 1) Build filename piece, possibly clickable
    let filenameHtml;
    if (/^https?:\/\/.+/i.test(filename.trim())) {
      filenameHtml = `<a href="${filename.trim()}" target="_blank" rel="noopener noreferrer">${filename.trim()}</a>`;
    } else {
      filenameHtml = filename.trim();
    }

    // 2) Build map: pageNumber => citationRef
    const bracketMatches = bracketSection.match(/\[#.*?\]/g) || [];
    const pageToRefMap = {};

    bracketMatches.forEach((match) => {
      // e.g. "[#doc_28; #doc_29]" => remove "[#" and "]"
      let inner = match.slice(2, -1).trim();
      // split on comma or semicolon
      const refs = inner.split(/[;,]/);
      refs.forEach((r) => {
        let ref = r.trim();
        if (ref.startsWith('#')) ref = ref.slice(1);
        // E.g. "doc_28" => pageNumber = "28"
        const parts = ref.split('_');
        const pageNumber = parts.pop();
        pageToRefMap[pageNumber] = ref;
      });
    });

    // Helper to discover prefix from a reference (e.g., "doc_28" => "doc_")
    function getDocPrefix(ref) {
      const underscoreIndex = ref.lastIndexOf('_');
      return underscoreIndex === -1 ? ref : ref.slice(0, underscoreIndex + 1);
    }

    // 3) Handle each comma-delimited token => single pages or dash ranges
    const pagesTokens = pages.split(/,/).map(tok => tok.trim());
    const linkedTokens = pagesTokens.map(token => {
      // Check if the token is a range: e.g. "1-4", "1–4", or "1—4"
      const dashParts = token.split(/[–—-]/).map(p => p.trim());

      // If exactly two parts, treat as a range
      if (dashParts.length === 2 && dashParts[0] && dashParts[1]) {
        const startNum = parseInt(dashParts[0], 10);
        const endNum   = parseInt(dashParts[1], 10);

        if (!isNaN(startNum) && !isNaN(endNum)) {
          // Try to discover a doc prefix from start or end
          let discoveredPrefix = '';
          if (pageToRefMap[startNum]) {
            discoveredPrefix = getDocPrefix(pageToRefMap[startNum]);
          } else if (pageToRefMap[endNum]) {
            discoveredPrefix = getDocPrefix(pageToRefMap[endNum]);
          }

          // Build anchors for all pages in the range
          const increment = startNum <= endNum ? 1 : -1;
          const pageAnchors = [];
          for (let p = startNum; increment > 0 ? p <= endNum : p >= endNum; p += increment) {
            if (!pageToRefMap[p] && discoveredPrefix) {
              // If no explicit reference, extrapolate
              pageToRefMap[p] = discoveredPrefix + p;
            }
            pageAnchors.push(buildAnchorIfExists(String(p), pageToRefMap[p]));
          }

          // Join as "1, 2, 3, 4"
          return pageAnchors.join(', ');
        }
      }

      // Single page
      const singleNum = parseInt(token, 10);
      if (!isNaN(singleNum)) {
        const ref = pageToRefMap[singleNum];
        return buildAnchorIfExists(token, ref);
      }

      // Fallback if not a valid page or range
      return token;
    });

    // 4) Join them with ", " if multiple tokens
    const linkedPagesText = linkedTokens.join(', ');

    return `(Source: ${filenameHtml}, Pages: ${linkedPagesText})`;
  });
}


export function buildAnchorIfExists(pageStr, citationId) {
  if (!citationId) {
    // no bracket reference for this page => leave it as plain text
    return pageStr;
  }
  return `<a href="#" class="citation-link" data-citation-id="${citationId}" target="_blank" rel="noopener noreferrer">${pageStr}</a>`;
}

export function fetchCitedText(citationId) {
  showLoadingIndicator();
  fetch("/api/get_citation", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ citation_id: citationId }),
  })
    .then((response) => response.json())
    .then((data) => {
      hideLoadingIndicator();

      if (data.cited_text && data.file_name && data.page_number !== undefined) {
        showCitedTextPopup(data.cited_text, data.file_name, data.page_number);
      } else if (data.error) {
        showToast(data.error, "danger");
      } else {
        showToast("Unexpected response from server.", "danger");
      }
    })
    .catch((error) => {
      hideLoadingIndicator();
      console.error("Error fetching cited text:", error);
      showToast("Error fetching cited text.", "danger");
    });
}

export function showCitedTextPopup(citedText, fileName, pageNumber) {
  let modalContainer = document.getElementById("citation-modal");
  if (!modalContainer) {
    modalContainer = document.createElement("div");
    modalContainer.id = "citation-modal";
    modalContainer.classList.add("modal", "fade");
    modalContainer.tabIndex = -1;
    modalContainer.setAttribute("aria-hidden", "true");

    modalContainer.innerHTML = `
      <div class="modal-dialog modal-dialog-scrollable modal-xl modal-fullscreen-sm-down">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Source: ${fileName}, Page: ${pageNumber}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <pre id="cited-text-content"></pre>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(modalContainer);
  } else {
    const modalTitle = modalContainer.querySelector(".modal-title");
    if (modalTitle) {
      modalTitle.textContent = `Source: ${fileName}, Page: ${pageNumber}`;
    }
  }

  const citedTextContent = document.getElementById("cited-text-content");
  if (citedTextContent) {
    citedTextContent.textContent = citedText;
  }

  const modal = new bootstrap.Modal(modalContainer);
  modal.show();
}

export function showImagePopup(imageSrc) {
  let modalContainer = document.getElementById("image-modal");
  if (!modalContainer) {
    modalContainer = document.createElement("div");
    modalContainer.id = "image-modal";
    modalContainer.classList.add("modal", "fade");
    modalContainer.tabIndex = -1;
    modalContainer.setAttribute("aria-hidden", "true");

    modalContainer.innerHTML = `
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-body text-center">
            <img
              id="image-modal-img"
              src=""
              alt="Generated Image"
              class="img-fluid"
            />
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(modalContainer);
  }
  const modalImage = modalContainer.querySelector("#image-modal-img");
  if (modalImage) {
    modalImage.src = imageSrc;
  }
  const modal = new bootstrap.Modal(modalContainer);
  modal.show();
}

export function showPdfModal(docId, pageNumber) {
  const fetchUrl = `/view_pdf?doc_id=${encodeURIComponent(docId)}&page=${encodeURIComponent(pageNumber)}`;

  let pdfModal = document.getElementById("pdf-modal");
  if (!pdfModal) {
    pdfModal = document.createElement("div");
    pdfModal.id = "pdf-modal";
    pdfModal.classList.add("modal", "fade");
    pdfModal.tabIndex = -1;
    pdfModal.setAttribute("aria-hidden", "true");
    pdfModal.innerHTML = `
      <div class="modal-dialog modal-dialog-scrollable modal-xl modal-fullscreen-sm-down">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Citation +/- one page</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body" style="height:80vh;">
            <iframe
              id="pdf-iframe"
              src=""
              style="width:100%; height:100%; border:none;"
            ></iframe>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(pdfModal);
  }

  showLoadingIndicator();

  fetch(fetchUrl)
    .then(async (resp) => {
      hideLoadingIndicator();

      if (!resp.ok) {
        throw new Error(`Failed to load PDF. Status: ${resp.status}`);
      }

      const newPage = resp.headers.get("X-Sub-PDF-Page") || "1";
      const blob = await resp.blob();
      const pdfBlobUrl = URL.createObjectURL(blob);
      const iframeSrc = pdfBlobUrl + `#page=${newPage}`;
      const iframe = pdfModal.querySelector("#pdf-iframe");
      if (iframe) {
        iframe.src = iframeSrc;
      }
      const modalInstance = new bootstrap.Modal(pdfModal);
      modalInstance.show();
    })
    .catch((error) => {
      hideLoadingIndicator();
      console.error("Error fetching PDF:", error);
      showToast(`Error fetching PDF: ${error.message}`, "danger");
    });
}

if (chatboxEl) {
  chatboxEl.addEventListener("click", (event) => {
    if (event.target && event.target.matches("a.citation-link")) {
      event.preventDefault();
      const citationId = event.target.getAttribute("data-citation-id");

      const { docId, pageNumber } = parseDocIdAndPage(citationId);
      if (toBoolean(window.enableEnhancedCitations)) {
        showPdfModal(docId, pageNumber);
      } else {
        fetchCitedText(citationId);
      }
    } else if (event.target && event.target.matches("a.file-link")) {
      event.preventDefault();
      const fileId = event.target.getAttribute("data-file-id");
      const conversationId = event.target.getAttribute("data-conversation-id");
      fetchFileContent(conversationId, fileId);
    }
    if (event.target.classList.contains("generated-image")) {
      const imageSrc = event.target.getAttribute("data-image-src");
      showImagePopup(imageSrc);
    }
  });
}
  