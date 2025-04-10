// chat-prompts.js

import { userInput} from "./chat-messages.js";

let userPrompts = [];
let groupPrompts = [];

const promptSelectionContainer = document.getElementById("prompt-selection-container");
export const promptSelect = document.getElementById("prompt-select"); // Keep export if needed elsewhere
const searchPromptsBtn = document.getElementById("search-prompts-btn");

export function loadUserPrompts() {
  return fetch("/api/prompts")
    .then(r => r.json())
    .then(data => {
      if (data.prompts) {
        userPrompts = data.prompts;
      }
    })
    .catch(err => console.error("Error loading user prompts:", err));
}

export function loadGroupPrompts() {
  return fetch("/api/group_prompts")
    .then(r => r.json())
    .then(data => {
      if (data.prompts) {
        groupPrompts = data.prompts;
      }
    })
    .catch(err => console.error("Error loading group prompts:", err));
}

export function populatePromptSelect() {
  if (!promptSelect) return;

  promptSelect.innerHTML = "";
  const defaultOpt = document.createElement("option");
  defaultOpt.value = "";
  defaultOpt.textContent = "Select a Prompt...";
  promptSelect.appendChild(defaultOpt);

  const combined = [...userPrompts.map(p => ({...p, scope: "Personal"})),
                    ...groupPrompts.map(p => ({...p, scope: "Group"}))];
  
  // combined.sort((a, b) => a.name.localeCompare(b.name)); 

  combined.forEach(promptObj => {
    const opt = document.createElement("option");
    opt.value = promptObj.id;
    opt.textContent = `[${promptObj.scope}] ${promptObj.name}`;
    opt.dataset.promptContent = promptObj.content;
    promptSelect.appendChild(opt);
  });
}

export function initializePromptInteractions() {
  console.log("Attempting to initialize prompt interactions..."); // Debug log

  if (searchPromptsBtn && promptSelectionContainer && userInput && promptSelect) {
    console.log("Elements found, adding prompt button listener."); // Debug log

    // Existing button click to open/close the prompt dropdown
    searchPromptsBtn.addEventListener("click", function() {
      const isActive = this.classList.toggle("active");
      if (isActive) {
        // Show the prompt-selection container
        promptSelectionContainer.style.display = "block";
        populatePromptSelect();
        userInput.classList.add("with-prompt-active");
        userInput.focus();
      } else {
        promptSelectionContainer.style.display = "none";
        promptSelect.selectedIndex = 0;
        userInput.classList.remove("with-prompt-active");
        userInput.focus();
      }
    });

    promptSelect.addEventListener("change", () => {
      const selectedOption = promptSelect.options[promptSelect.selectedIndex];
      if (selectedOption && selectedOption.value) {
        const promptContent = selectedOption.dataset.promptContent || "";
      }
    });
  } else {
    if (!searchPromptsBtn) console.error("Prompt Init Error: search-prompts-btn not found.");
    if (!promptSelectionContainer) console.error("Prompt Init Error: prompt-selection-container not found.");
    if (!userInput) console.error("Prompt Init Error: userInput (imported from chat-messages) is not available.");
    if (!promptSelect) console.error("Prompt Init Error: promptSelect not found.");
  }
}
