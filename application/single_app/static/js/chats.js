// js/chats.js

let personalDocs = [];
let groupDocs = [];
let activeGroupName = "";
let currentConversationId = null;

/*************************************************
 *  LOAD / DISPLAY CONVERSATIONS
 *************************************************/
function loadConversations() {
  fetch("/api/get_conversations")
    .then((response) => response.json())
    .then((data) => {
      const conversationsList = document.getElementById("conversations-list");
      if (!conversationsList) return; // Guard in case template is missing

      conversationsList.innerHTML = ""; // Clear existing list
      data.conversations.forEach((convo) => {
        const convoItem = document.createElement("div");
        convoItem.classList.add("list-group-item", "conversation-item");
        convoItem.setAttribute("data-conversation-id", convo.id);
        convoItem.setAttribute("data-conversation-title", convo.title);

        const date = new Date(convo.last_updated);
        convoItem.innerHTML = `
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <span>${convo.title}</span><br>
              <small>${date.toLocaleString()}</small>
            </div>
            <button
              class="btn btn-danger btn-sm delete-btn"
              data-conversation-id="${convo.id}"
            >
              <i class="bi bi-trash"></i>
            </button>
          </div>
        `;
        conversationsList.appendChild(convoItem);
      });
    })
    .catch((error) => {
      console.error("Error loading conversations:", error);
    });
}

/*************************************************
 *  DOC SCOPE & POPULATING SELECT
 *************************************************/
function populateDocumentSelectScope() {
  const scopeSel = document.getElementById("doc-scope-select");
  const docSel = document.getElementById("document-select");
  // Guard in case these elements do not exist in the DOM
  if (!scopeSel || !docSel) return;

  docSel.innerHTML = "";

  // Always add a "None" or "No Document Selected"
  const noneOpt = document.createElement("option");
  noneOpt.value = "";
  noneOpt.textContent = "All Documents";
  docSel.appendChild(noneOpt);

  const scopeVal = scopeSel.value || "all";

  let finalDocs = [];
  if (scopeVal === "all") {
    // Merge personal + group docs
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

  // Add them to "document-select"
  finalDocs.forEach((doc) => {
    const opt = document.createElement("option");
    opt.value = doc.id;
    opt.textContent = doc.label;
    docSel.appendChild(opt);
  });
}

// Listen for user selecting a different scope
const docScopeSelect = document.getElementById("doc-scope-select");
if (docScopeSelect) {
  docScopeSelect.addEventListener("change", populateDocumentSelectScope);
}

/*************************************************
 *  LOADING PERSONAL & GROUP DOCS
 *************************************************/
function loadPersonalDocs() {
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

function loadGroupDocs() {
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
        // If user has no active group
        activeGroupName = "";
        groupDocs = [];
      }
    })
    .catch((err) => {
      console.error("Error loading groups:", err);
      groupDocs = [];
    });
}

// Load both personal & group docs in sequence
function loadAllDocs() {
  // If there's no place to show documents, or if doc features are disabled,
  // you might not want to call these at all. But let's guard anyway:
  const hasDocControls =
    document.getElementById("search-documents-btn") ||
    document.getElementById("doc-scope-select") ||
    document.getElementById("document-select");

  if (!hasDocControls) {
    // If there's no doc UI, just skip
    return Promise.resolve();
  }

  return loadPersonalDocs().then(() => loadGroupDocs());
}

/*************************************************
 *  TOGGLE BUTTONS: SEARCH DOCUMENTS, WEB SEARCH, IMAGE GEN
 *************************************************/
const searchDocumentsBtn = document.getElementById("search-documents-btn");
if (searchDocumentsBtn) {
  searchDocumentsBtn.addEventListener("click", function () {
    this.classList.toggle("active");

    const docScopeSel = document.getElementById("doc-scope-select");
    const docSelectEl = document.getElementById("document-select");
    if (!docScopeSel || !docSelectEl) return;

    if (this.classList.contains("active")) {
      docScopeSel.style.display = "inline-block";
      docSelectEl.style.display = "inline-block";
      // Now that we know docs are loaded, populate:
      populateDocumentSelectScope();
    } else {
      docScopeSel.style.display = "none";
      docSelectEl.style.display = "none";
      docSelectEl.innerHTML = "";
    }
  });
}

const webSearchBtn = document.getElementById("search-web-btn");
if (webSearchBtn) {
  webSearchBtn.addEventListener("click", function () {
    this.classList.toggle("active");
  });
}

const imageGenBtn = document.getElementById("image-generate-btn");
if (imageGenBtn) {
  imageGenBtn.addEventListener("click", function () {
    // Toggle on/off
    this.classList.toggle("active");

    const isImageGenEnabled = this.classList.contains("active");

    // Example: disable other buttons if image gen is on
    const docBtn = document.getElementById("search-documents-btn");
    const webBtn = document.getElementById("search-web-btn");
    const fileBtn = document.getElementById("choose-file-btn");

    if (isImageGenEnabled) {
      if (docBtn) {
        docBtn.disabled = true;
        docBtn.classList.remove("active");
      }
      if (webBtn) {
        webBtn.disabled = true;
        webBtn.classList.remove("active");
      }
      if (fileBtn) {
        fileBtn.disabled = true;
        fileBtn.classList.remove("active");
      }
    } else {
      if (docBtn) docBtn.disabled = false;
      if (webBtn) webBtn.disabled = false;
      if (fileBtn) fileBtn.disabled = false;
    }
  });
}

/*************************************************
 *  SELECTING A CONVERSATION
 *************************************************/
function selectConversation(conversationId) {
  currentConversationId = conversationId;

  const userInputEl = document.getElementById("user-input");
  const sendBtnEl = document.getElementById("send-btn");
  if (userInputEl) userInputEl.disabled = false;
  if (sendBtnEl) sendBtnEl.disabled = false;

  // Get the conversation title
  const convoItem = document.querySelector(
    `.conversation-item[data-conversation-id="${conversationId}"]`
  );
  const conversationTitle = convoItem
    ? convoItem.getAttribute("data-conversation-title")
    : "Conversation";

  const currentTitleEl = document.getElementById("current-conversation-title");
  if (currentTitleEl) {
    currentTitleEl.textContent = conversationTitle;
  }

  loadMessages(conversationId);
  highlightSelectedConversation(conversationId);
}

function highlightSelectedConversation(conversationId) {
  const items = document.querySelectorAll(".conversation-item");
  items.forEach((item) => {
    if (item.getAttribute("data-conversation-id") === conversationId) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });
}

/*************************************************
 *  APPEND MESSAGE
 *************************************************/
function scrollChatToBottom() {
  const chatbox = document.getElementById("chatbox");
  if (chatbox) {
    chatbox.scrollTop = chatbox.scrollHeight;
  }
}

function appendMessage(sender, messageContent, modelName = null) {
  // If there's no chatbox at all, just bail out
  const chatbox = document.getElementById("chatbox");
  if (!chatbox) return;

  const messageDiv = document.createElement("div");
  messageDiv.classList.add("mb-2");

  let avatarImg = "";
  let avatarAltText = "";
  let messageClass = "";
  let senderLabel = "";
  let messageContentHtml = "";

  if (sender === "System") {
    // skip system messages if you prefer
    return;
  }

  if (sender === "image") {
    // AI image
    messageClass = "ai-message";
    senderLabel = `AI <span style="color: #6c757d; font-size: 0.8em;">(${modelName})</span>`;
    avatarImg = "/static/images/ai-avatar.png";

    // Render an image
    const imageHtml = `
      <img 
        src="${messageContent}" 
        alt="Generated Image" 
        class="generated-image" 
        style="width: 25%; cursor: pointer;"
        data-image-src="${messageContent}"
        onload="scrollChatToBottom()"
      />
    `;
    messageContentHtml = imageHtml;
  } else if (sender === "You") {
    // user message
    messageClass = "user-message";
    senderLabel = "You";
    avatarAltText = "User Avatar";
    avatarImg = "/static/images/user-avatar.png";

    const sanitizedContent = DOMPurify.sanitize(marked.parse(messageContent));
    messageContentHtml = sanitizedContent;
  } else if (sender === "AI") {
    // assistant message
    messageClass = "ai-message";
    avatarAltText = "AI Avatar";
    avatarImg = "/static/images/ai-avatar.png";

    if (modelName) {
      senderLabel = `AI <span style="color: #6c757d; font-size: 0.8em;">(${modelName})</span>`;
    } else {
      senderLabel = "AI";
    }

    let cleaned = messageContent.trim().replace(/\n{3,}/g, "\n\n");
    const withCitations = parseCitations(cleaned);
    const htmlContent = DOMPurify.sanitize(marked.parse(withCitations));
    messageContentHtml = htmlContent;
  } else if (sender === "File") {
    // file message
    messageClass = "file-message";
    senderLabel = "File Added";

    const filename = messageContent.filename;
    const fileId = messageContent.file_id;
    messageContentHtml = `
      <a 
        href="#"
        class="file-link"
        data-conversation-id="${currentConversationId}"
        data-file-id="${fileId}"
      >
        ${filename}
      </a>
    `;
  }

  messageDiv.classList.add("message", messageClass);
  messageDiv.innerHTML = `
    <div class="message-content ${
      sender === "You" || sender === "File" ? "flex-row-reverse" : ""
    }">
      ${
        sender !== "File"
          ? `<img src="${avatarImg}" alt="${avatarAltText}" class="avatar">`
          : ""
      }
      <div class="message-bubble">
        <div class="message-sender">${senderLabel}</div>
        <div class="message-text">${messageContentHtml}</div>
      </div>
    </div>
  `;

  chatbox.appendChild(messageDiv);
  scrollChatToBottom();
}

/*************************************************
 *  LOADING MESSAGES FOR CONVERSATION
 *************************************************/
function loadMessages(conversationId) {
  fetch(`/conversation/${conversationId}/messages`)
    .then((response) => response.json())
    .then((data) => {
      const chatbox = document.getElementById("chatbox");
      if (!chatbox) return; // no chatbox, bail

      chatbox.innerHTML = ""; // Clear existing messages
      data.messages.forEach((msg) => {
        if (msg.role === "user") {
          appendMessage("You", msg.content);
        } else if (msg.role === "assistant") {
          appendMessage("AI", msg.content, msg.model_deployment_name);
        } else if (msg.role === "file") {
          appendMessage("File", msg);
        } else if (msg.role === "image") {
          appendMessage("image", msg.content, msg.model_deployment_name);
        }
      });
    })
    .catch((error) => {
      console.error("Error loading messages:", error);
    });
}

/*************************************************
 *  CITATION PARSING
 *************************************************/
function parseCitations(message) {
  /*
    Matches patterns like:
    (Source: FILENAME, Page(s): X) [#doc_1] [#doc_2]
  */
  const citationRegex =
    /\(Source:\s*([^,]+),\s*Page(?:s)?:\s*([^)]+)\)\s*((?:\[#\S+?\]\s*)+)/g;

  return message.replace(
    citationRegex,
    (whole, filename, pages, bracketSection) => {
      const idMatches = bracketSection.match(/\[#([^\]]+)\]/g);
      if (!idMatches) return whole;

      // Build clickable links for each bracket
      const citationLinks = idMatches
        .map((m) => {
          const rawId = m.slice(2, -1);
          const pageNumber = rawId.split("_").pop();
          return `<a href="#" class="citation-link" data-citation-id="${rawId}">[Page ${pageNumber}]</a>`;
        })
        .join(" ");

      return `(Source: ${filename}, Pages: ${pages}) ${citationLinks}`;
    }
  );
}

/*************************************************
 *  DELETE A CONVERSATION
 *************************************************/
// We'll attach the event to the conversation list container if it exists
const conversationsList = document.getElementById("conversations-list");
if (conversationsList) {
  conversationsList.addEventListener("click", (event) => {
    const delBtn = event.target.closest(".delete-btn");
    if (delBtn) {
      event.stopPropagation();
      const conversationId = delBtn.getAttribute("data-conversation-id");
      deleteConversation(conversationId);
    } else {
      const convoItem = event.target.closest(".conversation-item");
      if (convoItem) {
        const conversationId = convoItem.getAttribute("data-conversation-id");
        selectConversation(conversationId);
      }
    }
  });
}

function deleteConversation(conversationId) {
  if (confirm("Are you sure you want to delete this conversation?")) {
    fetch(`/api/conversations/${conversationId}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
    })
      .then((response) => {
        if (response.ok) {
          // remove from list
          const convoItem = document.querySelector(
            `.conversation-item[data-conversation-id="${conversationId}"]`
          );
          if (convoItem) {
            convoItem.remove();
          }
          // If it was the currently selected conversation, clear the UI
          if (currentConversationId === conversationId) {
            currentConversationId = null;
            const userInput = document.getElementById("user-input");
            const sendBtn = document.getElementById("send-btn");
            if (userInput) userInput.disabled = true;
            if (sendBtn) sendBtn.disabled = true;

            const currentTitleEl = document.getElementById(
              "current-conversation-title"
            );
            if (currentTitleEl) {
              currentTitleEl.textContent = "Select a conversation";
            }
            const chatbox = document.getElementById("chatbox");
            if (chatbox) {
              chatbox.innerHTML = "";
            }
          }
        } else {
          alert("Failed to delete the conversation.");
        }
      })
      .catch((error) => {
        console.error("Error deleting conversation:", error);
        alert("Error deleting the conversation.");
      });
  }
}

/*************************************************
 *  CITED TEXT FUNCTIONS
 *************************************************/
function fetchCitedText(citationId) {
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
        alert(data.error);
      } else {
        alert("Unexpected response from server.");
      }
    })
    .catch((error) => {
      hideLoadingIndicator();
      console.error("Error fetching cited text:", error);
      alert("Error fetching cited text.");
    });
}

function showCitedTextPopup(citedText, fileName, pageNumber) {
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

/*************************************************
 *  LOADING / HIDING INDICATORS
 *************************************************/
function showLoadingIndicator() {
  let loadingSpinner = document.getElementById("loading-spinner");
  if (!loadingSpinner) {
    loadingSpinner = document.createElement("div");
    loadingSpinner.id = "loading-spinner";
    loadingSpinner.innerHTML = `
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    `;
    loadingSpinner.style.position = "fixed";
    loadingSpinner.style.top = "50%";
    loadingSpinner.style.left = "50%";
    loadingSpinner.style.transform = "translate(-50%, -50%)";
    loadingSpinner.style.zIndex = "1050";
    document.body.appendChild(loadingSpinner);
  } else {
    loadingSpinner.style.display = "block";
  }
}
function hideLoadingIndicator() {
  const loadingSpinner = document.getElementById("loading-spinner");
  if (loadingSpinner) {
    loadingSpinner.style.display = "none";
  }
}
function showLoadingIndicatorInChatbox() {
  const chatbox = document.getElementById("chatbox");
  if (!chatbox) return;

  const loadingIndicator = document.createElement("div");
  loadingIndicator.classList.add("loading-indicator");
  loadingIndicator.id = "loading-indicator";

  loadingIndicator.innerHTML = `
    <div class="spinner-border text-primary" role="status">
      <span class="visually-hidden">AI is typing...</span>
    </div>
    <span>AI is typing...</span>
  `;
  chatbox.appendChild(loadingIndicator);
  chatbox.scrollTop = chatbox.scrollHeight;
}
function hideLoadingIndicatorInChatbox() {
  const loadingIndicator = document.getElementById("loading-indicator");
  if (loadingIndicator) {
    loadingIndicator.remove();
  }
}

/*************************************************
 *  SENDING A MESSAGE
 *************************************************/
function sendMessage() {
  const userInput = document.getElementById("user-input");
  if (!userInput || !currentConversationId) return;

  const textVal = userInput.value.trim();
  if (textVal === "") return;

  appendMessage("You", textVal);
  userInput.value = "";
  showLoadingIndicatorInChatbox();

  // Check doc search
  let hybridSearchEnabled = false;
  const sdbtn = document.getElementById("search-documents-btn");
  if (sdbtn && sdbtn.classList.contains("active")) {
    hybridSearchEnabled = true;
  }

  // If doc is selected
  let selectedDocumentId = null;
  if (hybridSearchEnabled) {
    const docSel = document.getElementById("document-select");
    if (docSel && docSel.value !== "" && docSel.value !== "All Documents") {
      selectedDocumentId = docSel.value;
    }
  }

  // Bing search?
  let bingSearchEnabled = false;
  const wbbtn = document.getElementById("search-web-btn");
  if (wbbtn && wbbtn.classList.contains("active")) {
    bingSearchEnabled = true;
  }

  // Image gen?
  let imageGenEnabled = false;
  const igbtn = document.getElementById("image-generate-btn");
  if (igbtn && igbtn.classList.contains("active")) {
    imageGenEnabled = true;
  }

  fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: textVal,
      conversation_id: currentConversationId,
      hybrid_search: hybridSearchEnabled,
      selected_document_id: selectedDocumentId,
      bing_search: bingSearchEnabled,
      image_generation: imageGenEnabled,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      hideLoadingIndicatorInChatbox();
      if (data.reply) {
        appendMessage("AI", data.reply, data.model_deployment_name);
      }
      if (data.image_url) {
        appendMessage("image", data.image_url);
        // Optionally reload messages after generating an image
        setTimeout(() => {
          loadMessages(currentConversationId);
        }, 500);
      }
      if (data.conversation_id) {
        currentConversationId = data.conversation_id;
      }
      if (data.conversation_title) {
        const convTitleEl = document.getElementById("current-conversation-title");
        if (convTitleEl) {
          convTitleEl.textContent = data.conversation_title;
        }
        // Update the item in the list
        const convoItem = document.querySelector(
          `.conversation-item[data-conversation-id="${currentConversationId}"]`
        );
        if (convoItem) {
          const d = new Date();
          convoItem.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <span>${data.conversation_title}</span><br>
                <small>${d.toLocaleString()}</small>
              </div>
              <button
                class="btn btn-danger btn-sm delete-btn"
                data-conversation-id="${currentConversationId}"
              >
                <i class="bi bi-trash"></i>
              </button>
            </div>
          `;
          convoItem.setAttribute(
            "data-conversation-title",
            data.conversation_title
          );
        }
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      hideLoadingIndicatorInChatbox();
      appendMessage("Error", "Could not get a response.");
    });
}

/*************************************************
 *  USER INPUT EVENT LISTENERS
 *************************************************/
const sendBtn = document.getElementById("send-btn");
if (sendBtn) {
  sendBtn.addEventListener("click", sendMessage);
}

const userInputEl = document.getElementById("user-input");
if (userInputEl) {
  userInputEl.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      sendMessage();
    }
  });
}

/*************************************************
 *  LOADING DOCUMENTS FOR DROPDOWN
 *************************************************/
function loadDocuments() {
  fetch("/api/documents")
    .then((response) => response.json())
    .then((data) => {
      const documentSelect = document.getElementById("document-select");
      if (!documentSelect) return;

      documentSelect.innerHTML = "";

      // Add a "None" default
      const defaultOption = document.createElement("option");
      defaultOption.value = "";
      defaultOption.textContent = "None";
      documentSelect.appendChild(defaultOption);

      data.documents.forEach((doc) => {
        const option = document.createElement("option");
        option.value = doc.id;
        option.textContent = doc.file_name;
        documentSelect.appendChild(option);
      });

      // Check URL params
      const searchDocuments = getUrlParameter("search_documents") === "true";
      const documentId = getUrlParameter("document_id");
      if (searchDocuments && documentId) {
        const sdbtn = document.getElementById("search-documents-btn");
        if (sdbtn) {
          sdbtn.classList.add("active");
        }
        documentSelect.style.display = "block";
        documentSelect.value = documentId;
      }
    })
    .catch((error) => {
      console.error("Error loading documents:", error);
    });
}

// Utility for reading URL params
function getUrlParameter(name) {
  name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
  const regex = new RegExp("[\\?&]" + name + "=([^&#]*)");
  const results = regex.exec(location.search);
  return results === null
    ? ""
    : decodeURIComponent(results[1].replace(/\+/g, " "));
}

/*************************************************
 *  CREATE A NEW CONVERSATION
 *************************************************/
const newConversationBtn = document.getElementById("new-conversation-btn");
if (newConversationBtn) {
  newConversationBtn.addEventListener("click", () => {
    fetch("/api/create_conversation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
    })
      .then((response) => {
        if (!response.ok) {
          return response.json().then((errData) => {
            throw new Error(errData.error || "Failed to create conversation");
          });
        }
        return response.json();
      })
      .then((data) => {
        if (data.conversation_id) {
          // automatically select
          selectConversation(data.conversation_id);

          const conversationsList = document.getElementById("conversations-list");
          if (!conversationsList) return;

          // Add it to top of the conversation list
          const convoItem = document.createElement("div");
          convoItem.classList.add(
            "list-group-item",
            "conversation-item",
            "active"
          );
          convoItem.setAttribute("data-conversation-id", data.conversation_id);

          const date = new Date();
          convoItem.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <span>${data.conversation_id}</span><br>
                <small>${date.toLocaleString()}</small>
              </div>
              <button
                class="btn btn-danger btn-sm delete-btn"
                data-conversation-id="${data.conversation_id}"
              >
                <i class="bi bi-trash"></i>
              </button>
            </div>
          `;
          conversationsList.prepend(convoItem);

          // remove 'active' from others
          const items = document.querySelectorAll(".conversation-item");
          items.forEach((item) => {
            if (
              item.getAttribute("data-conversation-id") !== data.conversation_id
            ) {
              item.classList.remove("active");
            }
          });
        } else {
          throw new Error("Conversation ID not received");
        }
      })
      .catch((error) => {
        console.error("Error creating conversation:", error);
        alert(`Failed to create a new conversation: ${error.message}`);
      });
  });
}

/*************************************************
 *  FILE UPLOAD LOGIC
 *************************************************/
const chooseFileBtn = document.getElementById("choose-file-btn");
if (chooseFileBtn) {
  chooseFileBtn.addEventListener("click", function () {
    const fileInput = document.getElementById("file-input");
    if (fileInput) fileInput.click();
  });
}

const fileInputEl = document.getElementById("file-input");
if (fileInputEl) {
  fileInputEl.addEventListener("change", function () {
    const file = fileInputEl.files[0];
    const fileBtn = document.getElementById("choose-file-btn");
    const uploadBtn = document.getElementById("upload-btn");
    if (!fileBtn || !uploadBtn) return;

    if (file) {
      fileBtn.classList.add("active");
      fileBtn.querySelector(".file-btn-text").textContent = file.name;
      uploadBtn.style.display = "block";
    } else {
      resetFileButton();
    }
  });
}

function resetFileButton() {
  const fileInputEl = document.getElementById("file-input");
  if (fileInputEl) {
    fileInputEl.value = "";
  }
  const fileBtn = document.getElementById("choose-file-btn");
  if (fileBtn) {
    fileBtn.classList.remove("active");
    fileBtn.querySelector(".file-btn-text").textContent = "";
  }
  const uploadBtn = document.getElementById("upload-btn");
  if (uploadBtn) {
    uploadBtn.style.display = "none";
  }
}

const uploadBtn = document.getElementById("upload-btn");
if (uploadBtn) {
  uploadBtn.addEventListener("click", () => {
    const fileInput = document.getElementById("file-input");
    if (!fileInput) return;

    const file = fileInput.files[0];
    if (!file) {
      alert("Please select a file to upload.");
      return;
    }
    if (!currentConversationId) {
      alert("Please select or start a conversation before uploading a file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("conversation_id", currentConversationId);

    fetch("/upload", {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        // For debugging:
        let clonedResponse = response.clone();
        return response.json().then((data) => {
          if (!response.ok) {
            console.error("Upload failed:", data.error || "Unknown error");
            alert("Error uploading file: " + (data.error || "Unknown error"));
            throw new Error(data.error || "Upload failed");
          }
          return data;
        });
      })
      .then((data) => {
        console.log("Upload response data:", data);
        if (data.conversation_id) {
          currentConversationId = data.conversation_id;
          loadMessages(currentConversationId);
        } else {
          console.error("No conversation_id returned from server.");
          alert("Error: No conversation ID returned from server.");
        }
        resetFileButton();
      })
      .catch((error) => {
        console.error("Error:", error);
        alert("Error uploading file: " + error.message);
        resetFileButton();
      });
  });
}

/*************************************************
 *  CITATION LINKS & FILE LINKS
 *************************************************/
const chatboxEl = document.getElementById("chatbox");
if (chatboxEl) {
  // Catch clicks on citation/file links
  chatboxEl.addEventListener("click", (event) => {
    if (event.target && event.target.matches("a.citation-link")) {
      event.preventDefault();
      const citationId = event.target.getAttribute("data-citation-id");
      fetchCitedText(citationId);
    } else if (event.target && event.target.matches("a.file-link")) {
      event.preventDefault();
      const fileId = event.target.getAttribute("data-file-id");
      const conversationId = event.target.getAttribute("data-conversation-id");
      fetchFileContent(conversationId, fileId);
    }
  });

  // If user clicks on the generated image
  chatboxEl.addEventListener("click", (event) => {
    if (event.target.classList.contains("generated-image")) {
      const imageSrc = event.target.getAttribute("data-image-src");
      showImagePopup(imageSrc);
    }
  });
}

function showImagePopup(imageSrc) {
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

function fetchFileContent(conversationId, fileId) {
  showLoadingIndicator();
  fetch("/api/get_file_content", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      conversation_id: conversationId,
      file_id: fileId,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      hideLoadingIndicator();

      if (data.file_content && data.filename) {
        showFileContentPopup(data.file_content, data.filename, data.is_table);
      } else if (data.error) {
        alert(data.error);
      } else {
        alert("Unexpected response from server.");
      }
    })
    .catch((error) => {
      hideLoadingIndicator();
      console.error("Error fetching file content:", error);
      alert("Error fetching file content.");
    });
}

function showFileContentPopup(fileContent, filename, isTable) {
  let modalContainer = document.getElementById("file-modal");
  if (!modalContainer) {
    modalContainer = document.createElement("div");
    modalContainer.id = "file-modal";
    modalContainer.classList.add("modal", "fade");
    modalContainer.tabIndex = -1;
    modalContainer.setAttribute("aria-hidden", "true");

    modalContainer.innerHTML = `
      <div class="modal-dialog modal-dialog-scrollable modal-xl modal-fullscreen-sm-down">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Uploaded File: ${filename}</h5>
            <button
              type="button"
              class="btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <div id="file-content"></div>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(modalContainer);
  } else {
    const modalTitle = modalContainer.querySelector(".modal-title");
    if (modalTitle) {
      modalTitle.textContent = `Uploaded File: ${filename}`;
    }
  }

  const fileContentElement = document.getElementById("file-content");
  if (!fileContentElement) return;

  if (isTable) {
    fileContentElement.innerHTML = `<div class="table-responsive">${fileContent}</div>`;
    // If using DataTables
    $(document).ready(function () {
      $("#file-content table").DataTable({
        responsive: true,
        scrollX: true,
      });
    });
  } else {
    fileContentElement.innerHTML = `<pre style="white-space: pre-wrap;">${fileContent}</pre>`;
  }

  const modal = new bootstrap.Modal(modalContainer);
  modal.show();
}

/*************************************************
 *  BOOTSTRAP TOOLTIPS
 *************************************************/
document.addEventListener("DOMContentLoaded", function () {
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});

/*************************************************
 *  ON PAGE LOAD
 *************************************************/
window.onload = function () {
  // 1) Always load conversation list
  loadConversations();

  // 2) Conditionally load docs (only if doc UI is in DOM)
  loadAllDocs().then(() => {
    // Then read URL params:
    const searchDocsParam = getUrlParameter("search_documents") === "true";
    const docScopeParam = getUrlParameter("doc_scope") || ""; // e.g. "personal","group","all",""
    const documentIdParam = getUrlParameter("document_id") || "";

    const searchDocsBtn = document.getElementById("search-documents-btn");
    const docScopeSel = document.getElementById("doc-scope-select");
    const docSelectEl = document.getElementById("document-select");

    if (searchDocsParam && searchDocsBtn && docScopeSel && docSelectEl) {
      // 1) Turn on "Search Documents"
      searchDocsBtn.classList.add("active");

      // 2) Show doc scope & doc select
      docScopeSel.style.display = "inline-block";
      docSelectEl.style.display = "inline-block";

      // 3) If doc_scope param is present, set it
      if (docScopeParam) {
        docScopeSel.value = docScopeParam;
      }

      // 4) Populate the final doc list
      populateDocumentSelectScope();

      // 5) If there's a doc ID, select it
      if (documentIdParam) {
        docSelectEl.value = documentIdParam;
      }
    }
  });
};