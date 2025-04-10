// chat-messages.js

import { parseCitations } from "./chat-citations.js";
import { renderFeedbackIcons } from "./chat-feedback.js";
import { showLoadingIndicatorInChatbox, hideLoadingIndicatorInChatbox } from "./chat-loading-indicator.js";
import { docScopeSelect, getDocumentMetadata } from "./chat-documents.js";
import { promptSelect } from "./chat-prompts.js";
import { createNewConversation, selectConversation, addConversationToList  } from "./chat-conversations.js";
import { isColorLight, toBoolean, escapeHtml } from "./chat-utils.js";
import { showToast } from "./chat-toast.js"; 

let currentConversationId = null; // Global variable to hold the current conversation ID

export const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const promptSelectionContainer = document.getElementById("prompt-selection-container");
const chatbox = document.getElementById("chatbox");

function createCitationsHtml(hybridCitations = [], webCitations = [], messageId) {
  let citationsHtml = '';
  let hasCitations = false;

  if (hybridCitations && hybridCitations.length > 0) {
      hasCitations = true;
      hybridCitations.forEach((cite, index) => {
          const citationId = cite.citation_id || `${cite.chunk_id}_${cite.page_number || index}`; // Fallback ID
          const displayText = `${escapeHtml(cite.file_name)}, Page ${cite.page_number || 'N/A'}`;
          // Use <a> styled as a button to keep event listener compatibility easily
          citationsHtml += `
              <a href="#"
                 class="btn btn-sm citation-button hybrid-citation-link"
                 data-citation-id="${escapeHtml(citationId)}"
                 title="View source: ${displayText}">
                  <i class="bi bi-file-earmark-text me-1"></i>${displayText}
              </a>`;
      });
  }

  if (webCitations && webCitations.length > 0) {
      hasCitations = true;
      webCitations.forEach(cite => {
          const title = escapeHtml(cite.title || cite.url);
          const url = escapeHtml(cite.url);
          // Use <a> styled as a button, opening in new tab
          citationsHtml += `
              <a href="${url}" target="_blank" rel="noopener noreferrer"
                 class="btn btn-sm citation-button web-citation-link"
                 title="Open web source: ${title}">
                 <i class="bi bi-globe me-1"></i>${title}
              </a>`;
      });
  }

  // Wrap the buttons in a flex container for layout
  return hasCitations ? `<div class="d-flex flex-wrap gap-2">${citationsHtml}</div>` : '';
}

export function loadMessages(conversationId) {
  // Assuming the API returns the full message objects including augmented data
  fetch(`/conversation/${conversationId}/messages`)
      .then((response) => response.ok ? response.json() : Promise.reject('Failed to load messages'))
      .then((data) => {
          // const chatbox = document.getElementById("chatbox"); // Already defined above
          if (!chatbox) return;

          chatbox.innerHTML = ""; // Clear previous messages
          data.messages.forEach((msg) => {
               // Pass the necessary fields, including the new ones
              appendMessage(
                  msg.role === "user" ? "You" :
                  msg.role === "assistant" ? "AI" :
                  msg.role === "file" ? "File" :
                  msg.role === "image" ? "image" :
                  msg.role === "safety" ? "safety" : "System", // Handle different roles
                  msg.content, // Content or file object
                  msg.model_deployment_name,
                  msg.id, // Use msg.id as messageId
                  msg.augmented,
                  msg.hybrid_citations,
                  msg.web_search_citations
              );
          });
          scrollChatToBottom(); // Scroll after loading all
      })
      .catch((error) => {
          console.error("Error loading messages:", error);
           if (chatbox) chatbox.innerHTML = `<div class="text-center p-3 text-danger">Error loading messages.</div>`;
      });
}

function scrollChatToBottom() {
    const chatbox = document.getElementById("chatbox");
    if (chatbox) {
      chatbox.scrollTop = chatbox.scrollHeight;
    }
  }

export function appendMessage(
    sender,
    messageContent,
    modelName = null,
    messageId = null,
    augmented = false,
    hybridCitations = [],
    webCitations = []
) {
    if (!chatbox || sender === "System") return;

    const messageDiv = document.createElement("div");
    messageDiv.classList.add("mb-2", "message");
    messageDiv.setAttribute('data-message-id', messageId || `msg-${Date.now()}`);

    let avatarImg = "";
    let avatarAltText = "";
    let messageClass = ""; // <<< ENSURE THIS IS DECLARED HERE
    let senderLabel = "";
    let messageContentHtml = "";
    // let postContentHtml = ""; // Not needed for the general structure anymore

    // --- Handle AI message separately ---
    if (sender === "AI") {
        messageClass = "ai-message";
        avatarAltText = "AI Avatar";
        avatarImg = "/static/images/ai-avatar.png";
        senderLabel = modelName ? `AI <span style="color: #6c757d; font-size: 0.8em;">(${modelName})</span>` : "AI";

        // Parse content
        let cleaned = messageContent.trim().replace(/\n{3,}/g, "\n\n");
        cleaned = cleaned.replace(/(\bhttps?:\/\/\S+)(%5D|\])+/gi, (_, url) => url);
        const withInlineCitations = parseCitations(cleaned);
        const htmlContent = DOMPurify.sanitize(marked.parse(withInlineCitations));
        const mainMessageHtml = `<div class="message-text">${htmlContent}</div>`; // Renamed for clarity

        // --- Footer Content (Copy, Feedback, Citations) ---
        const feedbackHtml = renderFeedbackIcons(messageId, currentConversationId);
        const hiddenTextId = `copy-md-${messageId || Date.now()}`;
        const copyButtonHtml = `
            <button class="copy-btn me-2" data-hidden-text-id="${hiddenTextId}" title="Copy AI response as Markdown">
                <i class="bi bi-copy"></i>
            </button>
            <textarea id="${hiddenTextId}" style="display:none;">${escapeHtml(withInlineCitations)}</textarea>
        `;
        const copyAndFeedbackHtml = `<div class="message-actions d-flex align-items-center">${copyButtonHtml}${feedbackHtml}</div>`;

        const citationsButtonsHtml = createCitationsHtml(hybridCitations, webCitations, messageId);
        let citationToggleHtml = '';
        let citationContentContainerHtml = '';

        if (augmented && citationsButtonsHtml) {
            const citationsContainerId = `citations-${messageId || Date.now()}`;
            citationToggleHtml = `<div class="citation-toggle-container"><button class="btn btn-sm btn-outline-secondary citation-toggle-btn" title="Show sources" aria-expanded="false" aria-controls="${citationsContainerId}"><i class="bi bi-journal-text"></i></button></div>`;
            citationContentContainerHtml = `<div class="citations-container mt-2 pt-2 border-top" id="${citationsContainerId}" style="display: none;">${citationsButtonsHtml}</div>`;
        }

        const footerContentHtml = `<div class="message-footer d-flex justify-content-between align-items-center">${copyAndFeedbackHtml}${citationToggleHtml}</div>`;

        // Build AI message inner HTML
        messageDiv.innerHTML = `
            <div class="message-content">
                <img src="${avatarImg}" alt="${avatarAltText}" class="avatar">
                <div class="message-bubble">
                    <div class="message-sender">${senderLabel}</div>
                    ${mainMessageHtml}
                    ${citationContentContainerHtml}
                    ${footerContentHtml}
                </div>
            </div>`;

         messageDiv.classList.add(messageClass); // Add AI message class
         chatbox.appendChild(messageDiv); // Append AI message

        // --- Attach Event Listeners specifically for AI message ---
        attachCodeBlockCopyButtons(messageDiv.querySelector('.message-text'));
        const copyBtn = messageDiv.querySelector(".copy-btn");
        copyBtn?.addEventListener("click", () => { /* ... copy logic ... */
            const hiddenTextarea = document.getElementById(copyBtn.dataset.hiddenTextId);
            if (!hiddenTextarea) return;
            navigator.clipboard.writeText(hiddenTextarea.value)
                .then(() => {
                    copyBtn.innerHTML = '<i class="bi bi-check-lg text-success"></i>'; // Use check-lg
                    copyBtn.title = "Copied!";
                    setTimeout(() => {
                        copyBtn.innerHTML = '<i class="bi bi-copy"></i>';
                        copyBtn.title = "Copy AI response as Markdown";
                    }, 2000);
                })
                .catch(err => {
                    console.error("Error copying text:", err);
                    showToast("Failed to copy text.", "warning");
                });
         });
        const toggleBtn = messageDiv.querySelector('.citation-toggle-btn');
        if (toggleBtn) { toggleBtn.addEventListener('click', () => { /* ... toggle logic ... */
                const targetId = toggleBtn.getAttribute('aria-controls');
                const citationsContainer = messageDiv.querySelector(`#${targetId}`);
                if (!citationsContainer) return;
                const isExpanded = citationsContainer.style.display !== 'none';
                citationsContainer.style.display = isExpanded ? 'none' : 'block';
                toggleBtn.setAttribute('aria-expanded', !isExpanded);
                toggleBtn.title = isExpanded ? "Show sources" : "Hide sources";
                toggleBtn.innerHTML = isExpanded ? '<i class="bi bi-journal-text"></i>' : '<i class="bi bi-chevron-up"></i>';
                if (!isExpanded) { scrollChatToBottom(); }
            });
        }

        scrollChatToBottom();
        return; // <<< EXIT EARLY FOR AI MESSAGES

    // --- Handle ALL OTHER message types ---
    } else {
        // Determine variables based on sender type
        if (sender === "You") {
            messageClass = "user-message";
            senderLabel = "You";
            avatarAltText = "User Avatar";
            avatarImg = "/static/images/user-avatar.png";
            messageContentHtml = DOMPurify.sanitize(marked.parse(escapeHtml(messageContent)));
        } else if (sender === "File") {
            messageClass = "file-message";
            senderLabel = "File Added";
            avatarImg = ""; // No avatar for file messages
            avatarAltText = "";
            const filename = escapeHtml(messageContent.filename);
            const fileId = escapeHtml(messageContent.id);
            messageContentHtml = `<a href="#" class="file-link" data-conversation-id="${currentConversationId}" data-file-id="${fileId}"><i class="bi bi-file-earmark-arrow-up me-1"></i>${filename}</a>`;
        } else if (sender === "image") { // Make sure this matches the case used in loadMessages/actuallySendMessage
             messageClass = "image-message"; // Use a distinct class if needed, or reuse ai-message
             senderLabel = modelName ? `AI <span style="color: #6c757d; font-size: 0.8em;">(${modelName})</span>` : "Image"; // Or just "Image"
             avatarImg = "/static/images/ai-avatar.png"; // Or a specific image icon
             avatarAltText = "Generated Image";
             messageContentHtml = `<img src="${messageContent}" alt="Generated Image" class="generated-image" style="width: 170px; height: 170px; cursor: pointer;" data-image-src="${messageContent}" onload="scrollChatToBottom()" />`;
        } else if (sender === "safety") {
            messageClass = "safety-message";
            senderLabel = "Content Safety";
            avatarAltText = "Content Safety Avatar";
            avatarImg = "/static/images/alert.png";
            const linkToViolations = `<br><small><a href="/safety_violations" target="_blank" rel="noopener" style="font-size: 0.85em; color: #6c757d;">View My Safety Violations</a></small>`;
            messageContentHtml = DOMPurify.sanitize(marked.parse(messageContent + linkToViolations));
        } else if (sender === "Error") {
            messageClass = "error-message";
            senderLabel = "System Error";
            avatarImg = "/static/images/alert.png";
            avatarAltText = "Error Avatar";
            messageContentHtml = `<span class="text-danger">${escapeHtml(messageContent)}</span>`;
        } else {
            // This block should ideally not be reached if all sender types are handled
            console.warn("Unknown message sender type:", sender); // Keep the warning
            messageClass = "unknown-message"; // Fallback class
            senderLabel = "System";
            avatarImg = "/static/images/ai-avatar.png";
            avatarAltText = "System Avatar";
            messageContentHtml = escapeHtml(messageContent); // Default safe display
        }

        // --- Build the General Message Structure ---
        // This runs for "You", "File", "image", "safety", "Error", and the fallback "unknown"
        messageDiv.classList.add(messageClass); // Add the determined class

        // Set innerHTML using the variables determined above
        messageDiv.innerHTML = `
            <div class="message-content ${sender === "You" || sender === "File" ? "flex-row-reverse" : ""}">
                ${avatarImg ? `<img src="${avatarImg}" alt="${avatarAltText}" class="avatar">` : ""}
                <div class="message-bubble">
                    <div class="message-sender">${senderLabel}</div>
                    <div class="message-text">${messageContentHtml}</div>
                </div>
            </div>`;

        // Append and scroll (common actions for non-AI)
        chatbox.appendChild(messageDiv);
        scrollChatToBottom();
    } // End of the large 'else' block for non-AI messages
}



export function sendMessage() {
  if (!userInput) {
      console.error("User input element not found.");
      return;
  }
  let userText = userInput.value.trim();
  let promptText = "";
  let combinedMessage = "";

  if (promptSelectionContainer && promptSelectionContainer.style.display !== "none" && promptSelect && promptSelect.selectedIndex > 0) {
      const selectedOpt = promptSelect.options[promptSelect.selectedIndex];
      promptText = selectedOpt?.dataset?.promptContent?.trim() || "";
  }

  if (userText && promptText) {
      combinedMessage = userText + "\n\n" + promptText;
  } else {
      combinedMessage = userText || promptText;
  }
  combinedMessage = combinedMessage.trim();

  if (!combinedMessage) {
      return;
  }

  if (!currentConversationId) {
      createNewConversation(() => {
          actuallySendMessage(combinedMessage);
      });
  } else {
      actuallySendMessage(combinedMessage);
  }

  userInput.value = "";
  userInput.style.height = '';
  if (promptSelect) {
      promptSelect.selectedIndex = 0;
  }
  // Keep focus on input
  userInput.focus();
}



export function actuallySendMessage(finalMessageToSend) {
  // const chatbox = document.getElementById("chatbox"); // Defined above
  // const userInput = document.getElementById("user-input"); // Defined above
  appendMessage("You", finalMessageToSend); // Append user message first
  userInput.value = "";
  userInput.style.height = '';
  showLoadingIndicatorInChatbox();

  // ... (keep existing logic for hybridSearchEnabled, selectedDocumentId, classificationsToSend, bingSearchEnabled, imageGenEnabled)
  let hybridSearchEnabled = false;
  const sdbtn = document.getElementById("search-documents-btn");
  if (sdbtn && sdbtn.classList.contains("active")) {
      hybridSearchEnabled = true;
  }

  let selectedDocumentId = null;
  let classificationsToSend = null; // Variable to hold classification value
  const docSel = document.getElementById("document-select");
  const classificationInput = document.getElementById("classification-select"); // Get the input

  if (hybridSearchEnabled && docSel && classificationInput) {
      const selectedDocOption = docSel.options[docSel.selectedIndex];
      if (selectedDocOption && selectedDocOption.value !== "") {
          selectedDocumentId = selectedDocOption.value;
          classificationsToSend = classificationInput.value === "N/A" ? null : classificationInput.value;
      } else {
          selectedDocumentId = null;
          classificationsToSend = classificationInput.value || null;
      }
  }

  let bingSearchEnabled = false;
  const wbbtn = document.getElementById("search-web-btn");
  if (wbbtn && wbbtn.classList.contains("active")) {
      bingSearchEnabled = true;
  }

  let imageGenEnabled = false;
  const igbtn = document.getElementById("image-generate-btn");
  if (igbtn && igbtn.classList.contains("active")) {
      imageGenEnabled = true;
  }


  fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
          message: finalMessageToSend,
          conversation_id: currentConversationId,
          hybrid_search: hybridSearchEnabled,
          selected_document_id: selectedDocumentId,
          classifications: classificationsToSend,
          bing_search: bingSearchEnabled,
          image_generation: imageGenEnabled,
          doc_scope: docScopeSelect ? docScopeSelect.value : 'all',
          active_group_id: window.activeGroupId
      }),
  })
  .then((response) => {
      if (!response.ok) {
          // Handle non-OK responses, try to parse JSON error
          return response.json().then(errData => {
               // Throw an error object including the status and parsed data
               const error = new Error(errData.error || `HTTP error! status: ${response.status}`);
               error.status = response.status;
               error.data = errData; // Attach full error data
               throw error;
          }).catch(() => {
               // If JSON parsing fails, throw a generic error
               throw new Error(`HTTP error! status: ${response.status}`);
          });
      }
      return response.json(); // Parse JSON for successful responses
  })
  .then((data) => { // Only successful responses reach here
      hideLoadingIndicatorInChatbox();

      if (data.reply) {
          // *** Pass the new fields to appendMessage ***
          appendMessage(
              "AI",
              data.reply,
              data.model_deployment_name,
              data.message_id,
              data.augmented, // Pass augmented flag
              data.hybrid_citations, // Pass hybrid citations
              data.web_search_citations // Pass web citations
          );
      }
      if (data.image_url) {
          // Assuming image messages don't have citations in this flow
           appendMessage("image", data.image_url, data.model_deployment_name, data.message_id);
      }

      // Update conversation list item and header if needed
      if (data.conversation_id) {
          currentConversationId = data.conversation_id; // Update current ID
          const convoItem = document.querySelector(`.conversation-item[data-conversation-id="${currentConversationId}"]`);
          if (convoItem) {
              let updated = false;
              // Update Title
              if (data.conversation_title && convoItem.getAttribute("data-conversation-title") !== data.conversation_title) {
                  convoItem.setAttribute("data-conversation-title", data.conversation_title);
                  const titleEl = convoItem.querySelector(".conversation-title");
                  if (titleEl) titleEl.textContent = data.conversation_title;
                  updated = true;
              }
               // Update Classifications
              if (data.classification) { // Check if API returned classification
                  const currentClassificationJson = convoItem.dataset.classifications || '[]';
                  const newClassificationJson = JSON.stringify(data.classification);
                  if (currentClassificationJson !== newClassificationJson) {
                      convoItem.dataset.classifications = newClassificationJson;
                      updated = true;
                  }
              }
              // Update Timestamp (optional, could be done on load)
              const dateEl = convoItem.querySelector("small");
              if (dateEl) dateEl.textContent = new Date().toLocaleString([], { dateStyle: 'short', timeStyle: 'short' });

              if (updated) {
                  selectConversation(currentConversationId); // Re-select to update header
              }
          } else {
              // New conversation case
              addConversationToList(currentConversationId, data.conversation_title, data.classification || []);
              selectConversation(currentConversationId); // Select the newly added one
          }
      }
  })
  .catch((error) => {
      hideLoadingIndicatorInChatbox();
      console.error("Error sending message:", error);

      // Display specific error messages based on status or content
      if (error.status === 403 && error.data) { // Check for status and data from thrown error
           const categories = (error.data.triggered_categories || [])
               .map((catObj) => `${catObj.category} (severity=${catObj.severity})`)
               .join(", ");
           const reasonMsg = Array.isArray(error.data.reason)
               ? error.data.reason.join(", ")
               : error.data.reason;

          appendMessage(
              "safety", // Use 'safety' sender type
               `Your message was blocked by Content Safety.\n\n` +
               `**Categories triggered**: ${categories}\n` +
               `**Reason**: ${reasonMsg}`,
              null, // No model name for safety message
              error.data.message_id // Use message_id if provided in error
          );
      } else {
          // General error message
           appendMessage("Error", `Could not get a response. ${error.message || ''}`);
      }
  });
}

function attachCodeBlockCopyButtons(parentElement) {
  if (!parentElement) return; // Add guard clause
  const codeBlocks = parentElement.querySelectorAll("pre code");
  codeBlocks.forEach((codeBlock) => {
      const pre = codeBlock.parentElement;
      if (pre.querySelector('.copy-code-btn')) return; // Don't add if already exists

      pre.style.position = "relative";
      const copyBtn = document.createElement("button");
      copyBtn.innerHTML = '<i class="bi bi-copy"></i>';
      copyBtn.classList.add("copy-code-btn", "btn", "btn-sm", "btn-outline-secondary"); // Add Bootstrap classes
      copyBtn.title = "Copy code";
      copyBtn.style.position = "absolute";
      copyBtn.style.top = "5px";
      copyBtn.style.right = "5px";
      copyBtn.style.lineHeight = "1"; // Prevent extra height
      copyBtn.style.padding = "0.15rem 0.3rem"; // Smaller padding


      copyBtn.addEventListener("click", (e) => {
          e.stopPropagation(); // Prevent clicks bubbling up
          const codeToCopy = codeBlock.innerText; // Use innerText to get rendered text
          navigator.clipboard.writeText(codeToCopy)
              .then(() => {
                  copyBtn.innerHTML = '<i class="bi bi-check-lg text-success"></i>';
                  copyBtn.title = "Copied!";
                  setTimeout(() => {
                      copyBtn.innerHTML = '<i class="bi bi-copy"></i>';
                      copyBtn.title = "Copy code";
                  }, 2000);
              })
              .catch((err) => {
                  console.error("Error copying code:", err);
                  showToast("Failed to copy code.", "warning");
              });
      });
      pre.appendChild(copyBtn);
  });
}


if (sendBtn) {
  sendBtn.addEventListener("click", sendMessage);
}

if (userInput) {
  userInput.addEventListener("keydown", function (e) {
    // Check if Enter key is pressed
    if (e.key === "Enter") {
      // Check if Shift key is NOT pressed
      if (!e.shiftKey) {
        // Prevent default behavior (inserting a newline)
        e.preventDefault();
        // Send the message
        sendMessage();
      }
      // If Shift key IS pressed, do nothing - allow the default behavior (inserting a newline)
    }
  });
}