// chat-conversations.js

import { showToast } from "./chat-toast.js";
import { loadMessages } from "./chat-messages.js";

const newConversationBtn = document.getElementById("new-conversation-btn");

export function loadConversations() {
  fetch("/api/get_conversations")
    .then((response) => response.json())
    .then((data) => {
      const conversationsList = document.getElementById("conversations-list");
      if (!conversationsList) return;

      conversationsList.innerHTML = "";
      data.conversations.forEach((convo) => {
        conversationsList.appendChild(createConversationItem(convo));
      });
    })
    .catch((error) => {
      console.error("Error loading conversations:", error);
    });
}

export function createConversationItem(convo) {
  // Create the list item container
  const convoItem = document.createElement("div");
  convoItem.classList.add("list-group-item", "conversation-item");
  convoItem.setAttribute("data-conversation-id", convo.id);

  convoItem.dataset.classifications = JSON.stringify(convo.classification || []);

  // Left part: (title + timestamp)
  const leftDiv = document.createElement("div");
  leftDiv.classList.add("d-flex", "flex-column");

  const titleSpan = document.createElement("span");
  titleSpan.classList.add("conversation-title");
  titleSpan.textContent = convo.title;

  let classificationPills = null;

  if (window.enable_document_classification) {
    classificationPills = createClassificationPills(convo.classification);
  }

  const dateSpan = document.createElement("small");
  const date = new Date(convo.last_updated);
  dateSpan.textContent = date.toLocaleString();

  leftDiv.appendChild(titleSpan);
  if (window.enable_document_classification && classificationPills) {
    leftDiv.appendChild(classificationPills);
  }
  leftDiv.appendChild(dateSpan);

  // Right part: (three dots with dropdown)
  const rightDiv = document.createElement("div");
  rightDiv.classList.add("dropdown");

  // Button (no 'dropdown-toggle' class => no caret arrow)
  const dropdownBtn = document.createElement("button");
  dropdownBtn.classList.add("btn", "btn-light", "btn-sm");
  dropdownBtn.type = "button";
  dropdownBtn.setAttribute("data-bs-toggle", "dropdown");
  dropdownBtn.setAttribute("data-bs-display", "static");
  dropdownBtn.setAttribute("aria-expanded", "false");
  dropdownBtn.innerHTML = `<i class="bi bi-three-dots"></i>`;

  // The dropdown menu
  const dropdownMenu = document.createElement("ul");
  dropdownMenu.classList.add("dropdown-menu", "dropdown-menu-end", "my-dropdown-menu");

  // Edit link
  const editLi = document.createElement("li");
  const editA = document.createElement("a");
  editA.classList.add("dropdown-item", "edit-btn");
  editA.textContent = "Edit title";
  editA.href = "#";
  editLi.appendChild(editA);

  // Delete link
  const deleteLi = document.createElement("li");
  const deleteA = document.createElement("a");
  deleteA.classList.add("dropdown-item", "delete-btn", "text-danger");
  deleteA.textContent = "Delete";
  deleteA.href = "#";
  deleteLi.appendChild(deleteA);

  dropdownMenu.appendChild(editLi);
  dropdownMenu.appendChild(deleteLi);

  rightDiv.appendChild(dropdownBtn);
  rightDiv.appendChild(dropdownMenu);

  // Combine left + right
  const wrapper = document.createElement("div");
  wrapper.classList.add("d-flex", "justify-content-between", "align-items-center");
  wrapper.appendChild(leftDiv);
  wrapper.appendChild(rightDiv);

  convoItem.appendChild(wrapper);

  // 1) Select conversation on main click, unless clicked inside .dropdown-menu
  convoItem.addEventListener("click", (event) => {
    if (event.target.closest(".dropdown-menu")) {
      return; // clicked inside the menu; don't select convo
    }
    selectConversation(convo.id);
  });

  // 2) Edit
  editA.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    // Close the dropdown menu
    closeDropdownMenu(dropdownBtn);
    // Enter edit mode
    enterEditMode(convoItem, convo, dropdownBtn);
  });

  // 3) Delete
  deleteA.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    // Close the dropdown menu
    closeDropdownMenu(dropdownBtn);
    // Proceed with delete
    deleteConversation(convo.id);
  });

  return convoItem;
}

/**
 * Helper to force-close the Bootstrap dropdown.
 */
function closeDropdownMenu(dropdownBtn) {
  // If you are using Bootstrap 5 and have the Dropdown instance:
  const dropdownInstance = bootstrap.Dropdown.getInstance(dropdownBtn);
  if (dropdownInstance) {
    dropdownInstance.hide();
  } else {
    // Fallback: manually remove "show" classes if needed
    // dropdownBtn.parentElement.classList.remove("show");
    // const menu = dropdownBtn.parentElement.querySelector(".dropdown-menu");
    // if (menu) menu.classList.remove("show");
  }
}

/**
 * Switch the conversation item into "editing" mode:
 *  - Replace the <span> with an <input>
 *  - Hide the three-dot dropdown button
 *  - Add a Save button
 */
export function enterEditMode(convoItem, convo, dropdownBtn) {
  // If we are already editing a conversation, don’t do multiple at once
  if (currentlyEditingId && currentlyEditingId !== convo.id) {
    showToast("Finish editing the other conversation first.", "warning");
    return;
  }
  currentlyEditingId = convo.id;

  // Hide the three-dot dropdown button
  dropdownBtn.style.display = "none";

  // Get the span with .conversation-title
  const titleSpan = convoItem.querySelector(".conversation-title");
  // Create an input for editing
  const input = document.createElement("input");
  input.type = "text";
  input.value = convo.title;
  input.classList.add("form-control", "form-control-sm");
  input.style.maxWidth = "200px";

  // Insert the input in place of the span
  titleSpan.replaceWith(input);

  // Create a Save button
  const saveBtn = document.createElement("button");
  saveBtn.classList.add("btn", "btn-primary", "btn-sm", "ms-2");
  saveBtn.textContent = "Save";

  // We'll place it near the dropdown or after the input
  const parentDiv = convoItem.querySelector(".d-flex.justify-content-between");
  parentDiv.appendChild(saveBtn);

  // On Save, call updateConversationTitle
  saveBtn.addEventListener("click", async () => {
    const newTitle = input.value.trim();
    if (!newTitle) {
      showToast("Title cannot be empty.", "warning");
      return;
    }

    try {
      await updateConversationTitle(convo.id, newTitle);
      // success => revert to normal view
      convo.title = newTitle; // update local data
      exitEditMode(convoItem, convo, dropdownBtn);
    } catch (err) {
      console.error(err);
      showToast("Failed to update title.", "danger");
    }
  });
}

/**
 * Restore the conversation item to non-editing mode:
 *  - Replace the <input> with the updated <span>
 *  - Remove the Save button
 *  - Show the three-dot dropdown button
 */
export function exitEditMode(convoItem, convo, dropdownBtn) {
  currentlyEditingId = null;
  // Find the input
  const input = convoItem.querySelector("input.form-control");
  if (!input) return;

  // Create a new <span> with updated text
  const newSpan = document.createElement("span");
  newSpan.classList.add("conversation-title");
  newSpan.textContent = convo.title;

  // Replace the input with the new span
  input.replaceWith(newSpan);

  // Remove the Save button
  const saveBtn = convoItem.querySelector("button.btn-primary");
  if (saveBtn) {
    saveBtn.remove();
  }

  // Show the three-dot dropdown button again
  dropdownBtn.style.display = "";
}


/**
 * Call the API to PUT/PATCH the conversation title
 */
export async function updateConversationTitle(conversationId, newTitle) {
  const response = await fetch(`/api/conversations/${conversationId}`, {
    method: "PUT", // or PATCH
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title: newTitle }),
  });
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.error || "Failed to update conversation");
  }
  return response.json();
}

export function addConversationToList(conversationId, title = null) {
  const conversationsList = document.getElementById("conversations-list");
  if (!conversationsList) return;

  const items = document.querySelectorAll(".conversation-item");
  items.forEach((i) => i.classList.remove("active"));

  const convo = {
    id: conversationId,
    title: title || "New conversation",
    last_updated: new Date().toISOString(),
  };
  const convoItem = createConversationItem(convo);
  convoItem.classList.add("active");
  conversationsList.prepend(convoItem);
}

export function selectConversation(conversationId) {
  currentConversationId = conversationId;

  const convoItem = document.querySelector(
    `.conversation-item[data-conversation-id="${conversationId}"]`
  );
  const conversationTitleSpan = convoItem
    ? convoItem.querySelector(".conversation-title")
    : null;
  const conversationTitle = conversationTitleSpan
    ? conversationTitleSpan.textContent
    : "Conversation";

  const currentTitleEl = document.getElementById("current-conversation-title");
  if (currentTitleEl) {
    currentTitleEl.textContent = conversationTitle;
  }

  const classificationsEl = document.getElementById("current-conversation-classifications");
  if (classificationsEl) {
    // Clear anything old
    classificationsEl.innerHTML = "";

    if (window.enable_document_classification){
      const classData = convoItem.dataset.classifications;
      if (classData) {
        const classifications = JSON.parse(classData);
        classifications.forEach(cls => {
          const pill = document.createElement("span");
          pill.classList.add("badge", "rounded-pill", "bg-info", "me-1");
          pill.textContent = cls;
          classificationsEl.appendChild(pill);
        });
      }
    }
  }

  loadMessages(conversationId);
  highlightSelectedConversation(conversationId);
}

export function highlightSelectedConversation(conversationId) {
  const items = document.querySelectorAll(".conversation-item");
  items.forEach((item) => {
    if (item.getAttribute("data-conversation-id") === conversationId) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });
}

export function deleteConversation(conversationId) {
  if (!confirm("Are you sure you want to delete this conversation?")) {
    return;
  }

  fetch(`/api/conversations/${conversationId}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
  })
    .then((response) => {
      if (response.ok) {
        const convoItem = document.querySelector(
          `.conversation-item[data-conversation-id="${conversationId}"]`
        );
        if (convoItem) {
          convoItem.remove();
        }

        if (currentConversationId === conversationId) {
          currentConversationId = null;
          const titleEl = document.getElementById("current-conversation-title");
          if (titleEl) {
            titleEl.textContent =
              "Start typing to create a new conversation or select one on the left";
          }
          const chatbox = document.getElementById("chatbox");
          if (chatbox) {
            chatbox.innerHTML = "";
          }
        }
      } else {
        showToast("Failed to delete the conversation.", "danger");
      }
    })
    .catch((error) => {
      console.error("Error deleting conversation:", error);
      showToast("Error deleting the conversation.", "danger");
    });
}

export async function createNewConversation(callback) {
  try {
    const response = await fetch("/api/create_conversation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
    });
    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.error || "Failed to create conversation");
    }

    const data = await response.json();
    if (!data.conversation_id) {
      throw new Error("No conversation_id returned from server.");
    }

    currentConversationId = data.conversation_id;
    addConversationToList(data.conversation_id);

    const currentTitleEl = document.getElementById("current-conversation-title");
    if (currentTitleEl) {
      currentTitleEl.textContent = "New Conversation";
    }

    const chatbox = document.getElementById("chatbox");
    if (chatbox) {
      chatbox.innerHTML = "";
    }

    if (typeof callback === "function") {
      callback();
    } else {
      loadMessages(data.conversation_id);
    }
  } catch (error) {
    console.error("Error creating conversation:", error);
    showToast(`Failed to create a new conversation: ${error.message}`, "danger");
  }
}

function createClassificationPills(classifications) {
  const container = document.createElement("div");
  container.classList.add("classification-container");
  
  if (classifications && Array.isArray(classifications)) {
    classifications.forEach((classification) => {
      const pill = document.createElement("span");
      // You can change the bg color class, e.g. "bg-info", "bg-secondary", etc.
      pill.classList.add("badge", "rounded-pill", "bg-info", "me-1");
      pill.textContent = classification;
      container.appendChild(pill);
    });
  }
  
  return container;
}

if (newConversationBtn) {
  newConversationBtn.addEventListener("click", () => {
    createNewConversation();
  });
}
