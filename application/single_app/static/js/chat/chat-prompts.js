// chat-prompts.js

import { userInput} from "./chat-messages.js";

export const promptSelect = document.getElementById("prompt-select");
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

  const combined = [...userPrompts.map(p => ({...p, scope: "User"})),
                    ...groupPrompts.map(p => ({...p, scope: "Group"}))];

  combined.forEach(promptObj => {
    const opt = document.createElement("option");
    opt.value = promptObj.id;
    opt.textContent = `[${promptObj.scope}] ${promptObj.name}`;
    opt.dataset.promptContent = promptObj.content;
    promptSelect.appendChild(opt);
  });
}

if (searchPromptsBtn) {
  searchPromptsBtn.addEventListener("click", function() {
    if (!promptSelect || !userInput) return;

    const isActive = this.classList.toggle("active");

    if (isActive) {
      userInput.style.display = "none";
      promptSelect.style.display = "inline-block";
      populatePromptSelect();
      userInput.value = "";
    } else {
      userInput.style.display = "inline-block";
      promptSelect.style.display = "none";
      promptSelect.selectedIndex = 0;
    }
  });
}