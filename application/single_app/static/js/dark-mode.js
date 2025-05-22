// Dark mode functionality
const USER_SETTINGS_KEY_DARK_MODE = 'darkModeEnabled';

// DOM Elements
const darkModeToggle = document.getElementById('darkModeToggle');
const lightModeIcon = document.getElementById('lightModeIcon');
const darkModeIcon = document.getElementById('darkModeIcon');
const htmlRoot = document.getElementById('htmlRoot');

// Function to toggle dark mode
function toggleDarkMode() {
    const isDarkMode = htmlRoot.getAttribute('data-bs-theme') === 'dark';
    const newMode = isDarkMode ? 'light' : 'dark';
    
    // Update the theme
    htmlRoot.setAttribute('data-bs-theme', newMode);
    
    // Update icons
    if (newMode === 'dark') {
        lightModeIcon.classList.add('d-none');
        darkModeIcon.classList.remove('d-none');
    } else {
        lightModeIcon.classList.remove('d-none');
        darkModeIcon.classList.add('d-none');
    }
    
    // Save the preference
    saveUserSetting({ [USER_SETTINGS_KEY_DARK_MODE]: newMode === 'dark' });
}

// Load dark mode preference
async function loadDarkModePreference() {
    try {
        const response = await fetch('/api/user/settings');
        if (response.ok) {
            const data = await response.json();
            const settings = data.settings || {};
            const isDarkMode = settings[USER_SETTINGS_KEY_DARK_MODE] === true;
            
            // Apply the theme
            htmlRoot.setAttribute('data-bs-theme', isDarkMode ? 'dark' : 'light');
            
            // Update icons
            if (isDarkMode) {
                lightModeIcon.classList.add('d-none');
                darkModeIcon.classList.remove('d-none');
            } else {
                lightModeIcon.classList.remove('d-none');
                darkModeIcon.classList.add('d-none');
            }
        }
    } catch (error) {
        console.error('Error loading dark mode preference:', error);
    }
}

// Initialize dark mode
document.addEventListener('DOMContentLoaded', () => {
    if (darkModeToggle) {
        // Add click event listener to toggle
        darkModeToggle.addEventListener('click', toggleDarkMode);
        
        // Load user preference
        loadDarkModePreference();
    }
});