// chat-messages.js

import { parseCitations } from "./chat-citations.js";
import { renderFeedbackIcons } from "./chat-feedback.js";
import { showLoadingIndicatorInChatbox, hideLoadingIndicatorInChatbox } from "./chat-loading-indicator.js";
import { docScopeSelect } from "./chat-documents.js";
import { promptSelect } from "./chat-prompts.js";
import { createNewConversation  } from "./chat-conversations.js";
import { isColorLight } from "./chat-utils.js";

export const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

export function loadMessages(conversationId) {
  fetch(`/conversation/${conversationId}/messages`)
    .then((response) => response.json())
    .then((data) => {
      const chatbox = document.getElementById("chatbox");
      if (!chatbox) return;

      chatbox.innerHTML = "";
      data.messages.forEach((msg) => {
        if (msg.role === "user") {
          appendMessage("You", msg.content);
        } else if (msg.role === "assistant") {
          appendMessage("AI", msg.content, msg.model_deployment_name, msg.message_id);
        } else if (msg.role === "file") {
          appendMessage("File", msg);
        } else if (msg.role === "image") {
          appendMessage("image", msg.content, msg.model_deployment_name);
        } else if (msg.role === "safety") {
          appendMessage("safety", msg.content);
        }
      });
    })
    .catch((error) => {
      console.error("Error loading messages:", error);
    });
}

export function appendMessage(sender, messageContent, modelName = null, messageId = null) {
  const chatbox = document.getElementById("chatbox");
  if (!chatbox) return;

  const messageDiv = document.createElement("div");
  messageDiv.classList.add("mb-2");

  let avatarImg = "";
  let avatarAltText = "";
  let messageClass = "";
  let senderLabel = "";
  let messageContentHtml = "";
  let feedbackHtml = "";

  if (sender === "System") {
    return;
  }

  if (sender === "safety") {
    messageClass = "ai-message";
    senderLabel = "Content Safety";
    avatarAltText = "Content Safety Avatar";
    avatarImg = "/static/images/alert.png";
    const linkToViolations = `
      <br>
      <small>
        <a href="/safety_violations" target="_blank" rel="noopener" style="font-size: 0.85em; color: #6c757d;">
          View My Safety Violations
        </a>
      </small>
    `;

    messageContentHtml = DOMPurify.sanitize(
      marked.parse(messageContent + linkToViolations)
    );
  } else if (sender === "image") {
    messageClass = "ai-message";
    senderLabel = modelName
      ? `AI <span style="color: #6c757d; font-size: 0.8em;">(${modelName})</span>`
      : "AI";
    avatarImg = "/static/images/ai-avatar.png";

    const imageHtml = `
      <img 
        src="${messageContent}" 
        alt="Generated Image" 
        class="generated-image" 
        style="width: 170px; height: 170px; cursor: pointer;"
        data-image-src="${messageContent}"
        onload="scrollChatToBottom()"
      />
    `;
    messageContentHtml = imageHtml;
  } else if (sender === "You") {
    messageClass = "user-message";
    senderLabel = "You";
    avatarAltText = "User Avatar";
    avatarImg = "/static/images/user-avatar.png";
    messageContentHtml = DOMPurify.sanitize(marked.parse(messageContent));
  } else if (sender === "AI") {
    messageClass = "ai-message";
    avatarAltText = "AI Avatar";
    avatarImg = "/static/images/ai-avatar.png";
    senderLabel = modelName
      ? `AI <span style="color: #6c757d; font-size: 0.8em;">(${modelName})</span>`
      : "AI";

    feedbackHtml = renderFeedbackIcons(messageId, currentConversationId);

    let cleaned = messageContent.trim().replace(/\n{3,}/g, "\n\n");
    cleaned = cleaned.replace(/(\bhttps?:\/\/\S+)(%5D|\])+/gi, (_, url) => url);
    const withCitations = parseCitations(cleaned);
    const htmlContent = DOMPurify.sanitize(marked.parse(withCitations));
    messageContentHtml = htmlContent;
    const hiddenTextId = `copy-md-${messageId || Date.now()}`;

    const copyButtonHtml = `
      <button class="copy-btn me-3"
              data-hidden-text-id="${hiddenTextId}"
              title="Copy entire AI response as Markdown">
        <i class="bi bi-copy"></i>
      </button>
      <textarea id="${hiddenTextId}" style="display:none;">${withCitations}</textarea>
    `;

    const copyAndFeedbackHtml = `
      <div class="copy-and-feedback" style="display: inline-flex; align-items: center; margin-top: 6px;">
        ${copyButtonHtml}
        ${feedbackHtml}
      </div>
    `;

    messageDiv.classList.add("message", messageClass);
    messageDiv.innerHTML = `
      <div class="message-content">
        <img src="${avatarImg}" alt="${avatarAltText}" class="avatar">
        <div class="message-bubble">
          <div class="message-sender">${senderLabel}</div>
          <div class="message-text">${htmlContent}</div>
          ${copyAndFeedbackHtml}
        </div>
      </div>
    `;
    
    chatbox.appendChild(messageDiv);

    attachCodeBlockCopyButtons(messageDiv);

    const copyBtn = messageDiv.querySelector(".copy-btn");
    copyBtn?.addEventListener("click", () => {
      const hiddenTextarea = document.getElementById(copyBtn.dataset.hiddenTextId);
      if (!hiddenTextarea) return;
      const markdownToCopy = hiddenTextarea.value;

      navigator.clipboard.writeText(markdownToCopy)
        .then(() => {
          console.log("Copied AI response to clipboard!");
          
          // Show a check icon for 2s
          copyBtn.innerHTML = '<i class="bi bi-check"></i>';
          setTimeout(() => {
            copyBtn.innerHTML = '<i class="bi bi-copy"></i>';
          }, 2000);
        })
        .catch(err => console.error("Error copying text:", err));
    });

    scrollChatToBottom();
    return;

  } else if (sender === "File") {
    messageClass = "file-message";
    senderLabel = "File Added";
    const filename = messageContent.filename;
    const fileId = messageContent.id;
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
        ${feedbackHtml || ""}
      </div>
    </div>
  `;

  chatbox.appendChild(messageDiv);
  
  scrollChatToBottom();
}

export function sendMessage() {
  const userInput = document.getElementById("user-input");
  
  let textVal = "";
  if (promptSelect && promptSelect.style.display !== "none") {
    const selectedOpt = promptSelect.options[promptSelect.selectedIndex];
    textVal = selectedOpt?.dataset?.promptContent?.trim() || "";
  } else if (userInput) {
    textVal = userInput.value.trim();
  }

  if (!textVal) return;

  if (!currentConversationId) {
    createNewConversation(() => {
      actuallySendMessage(textVal);
    });
  } else {
    actuallySendMessage(textVal);
  }
}

export function actuallySendMessage(textVal) {
  const userInput = document.getElementById("user-input");
  appendMessage("You", textVal);
  userInput.value = "";
  userInput.style.height = '';
  showLoadingIndicatorInChatbox();

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
      // Specific document selected
      selectedDocumentId = selectedDocOption.value;
      // The classificationInput already holds the single classification (or N/A)
      classificationsToSend = classificationInput.value === "N/A" ? null : classificationInput.value;
    } else {
      // "All Documents" selected
      selectedDocumentId = null; // Explicitly null
      // The classificationInput holds the comma-separated list (or empty string if none selected)
      classificationsToSend = classificationInput.value || null; // Send null if empty string
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
      message: textVal,
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
      const cloned = response.clone();
      return cloned.json().then((data) => ({
        ok: response.ok,
        status: response.status,
        data,
      }));
    })
    .then(({ ok, status, data }) => {
      hideLoadingIndicatorInChatbox();

      if (!ok) {
        if (status === 403) {
          const categories = (data.triggered_categories || [])
            .map((catObj) => `${catObj.category} (severity=${catObj.severity})`)
            .join(", ");
          const reasonMsg = Array.isArray(data.reason)
            ? data.reason.join(", ")
            : data.reason;

          appendMessage(
            "System",
            `Your message was blocked by Content Safety.\n\n +
              **Categories triggered**: ${categories}\n +
              **Reason**: ${reasonMsg}`,
            data.message_id
          );
        } else {
          appendMessage(
            "System",
            `An error occurred: ${data.error || "Unknown error"}.`
          );
        }
      } else {
        if (data.reply) {
          appendMessage("AI", data.reply, data.model_deployment_name, data.message_id);
        }
        if (data.image_url) {
          appendMessage("image", data.image_url, data.model_deployment_name, data.message_id);
        }

        if (data.conversation_id) {
          currentConversationId = data.conversation_id;
        }

        // *** Update Conversation List Item and Header ***
        if (currentConversationId) {
          const convoItem = document.querySelector(`.conversation-item[data-conversation-id="${currentConversationId}"]`);
          if (convoItem) {
              let updated = false;
              // Update Title if changed
              if (data.conversation_title && convoItem.getAttribute("data-conversation-title") !== data.conversation_title) {
                  convoItem.setAttribute("data-conversation-title", data.conversation_title);
                  const titleEl = convoItem.querySelector(".conversation-title");
                  if (titleEl) titleEl.textContent = data.conversation_title;
                  updated = true;
              }
              // Update Classifications if changed
              if (data.classification) { // Check if API returned classification
                  const currentClassificationJson = convoItem.dataset.classifications || '[]';
                  const newClassificationJson = JSON.stringify(data.classification);
                  if (currentClassificationJson !== newClassificationJson) {
                      convoItem.dataset.classifications = newClassificationJson;
                      updated = true;
                  }
              }
              // Update Timestamp
              const dateEl = convoItem.querySelector("small");
              if (dateEl) dateEl.textContent = new Date().toLocaleString([], { dateStyle: 'short', timeStyle: 'short' });

              // Move updated item to top? Optional, but common UX
              // conversationsList.prepend(convoItem);

              // If anything updated, refresh the header display by re-selecting
              if (updated) {
                  selectConversation(currentConversationId);
              }
          } else {
              // Conversation item doesn't exist, might be a new convo response
                addConversationToList(currentConversationId, data.conversation_title, data.classification || []);
                selectConversation(currentConversationId);
          }
        }
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      hideLoadingIndicatorInChatbox();
      appendMessage("Error", "Could not get a response.");
    });
}

function attachCodeBlockCopyButtons(parentElement) {
  // Find all <pre><code>...</code></pre> blocks inside this message
  const codeBlocks = parentElement.querySelectorAll("pre code");
  codeBlocks.forEach((codeBlock) => {
    const pre = codeBlock.parentElement;
    // Make <pre> position: relative so the copy button can be positioned
    pre.style.position = "relative";
    
    // Create a button with an icon
    const copyBtn = document.createElement("button");
    copyBtn.innerHTML = '<i class="bi bi-copy"></i>';
    copyBtn.classList.add("copy-code-btn");
    copyBtn.title = "Copy code";

    // Position it in the top-right corner of the <pre>
    copyBtn.style.position = "absolute";
    copyBtn.style.top = "5px";
    copyBtn.style.right = "5px";

    // (Optional) style: remove default button chrome
    copyBtn.style.background = "none";
    copyBtn.style.border = "none";
    copyBtn.style.padding = "0.25rem";
    copyBtn.style.cursor = "pointer";
    copyBtn.style.color = "#6c757d"; // match your theme if you like

    // When clicked, copy the <code> text
    copyBtn.addEventListener("click", () => {
      const codeToCopy = codeBlock.innerText.trim();
      navigator.clipboard.writeText(codeToCopy)
        .then(() => {
          // Show a check mark for 2s
          copyBtn.innerHTML = '<i class="bi bi-check"></i>';
          setTimeout(() => {
            copyBtn.innerHTML = '<i class="bi bi-copy"></i>';
          }, 2000);
        })
        .catch((err) => {
          console.error("Error copying code:", err);
        });
    });

    // Insert the button in the <pre>
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