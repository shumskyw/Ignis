// Ignis AI Chat Interface - JavaScript
class IgnisChat {
    constructor() {
        this.apiBase = 'http://localhost:8000'; // API server URL
        this.messagesContainer = document.getElementById('messagesContainer');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.buttonLoader = document.getElementById('buttonLoader');
        this.charCount = document.getElementById('charCount');
        this.memoryModal = document.getElementById('memoryModal');
        this.memoryStatus = document.getElementById('memoryStatus');
        this.userNameInput = document.getElementById('userNameInput');

        this.isTyping = false;
        this.messageHistory = [];

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.scrollToBottom();
        this.updateCharCount();
    }

    setupEventListeners() {
        // Send message on Enter key
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Send message on button click
        this.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });

        // Update character count
        this.messageInput.addEventListener('input', () => {
            this.updateCharCount();
            this.updateSendButton();
        });

        // Profile picture (settings)
        const avatarElement = document.getElementById('profileAvatar');
        if (avatarElement) {
            avatarElement.addEventListener('click', () => {
                this.openSettings();
            });
        }

        // Memory modal close
        document.getElementById('memoryModalClose').addEventListener('click', () => {
            this.hideMemoryModal();
        });

        // Close modal when clicking outside
        this.memoryModal.addEventListener('click', (e) => {
            if (e.target === this.memoryModal) {
                this.hideMemoryModal();
            }
        });

        // Settings modal
        document.getElementById('settingsModalClose').addEventListener('click', () => {
            this.closeSettings();
        });

        document.getElementById('closeSettingsBtn').addEventListener('click', () => {
            this.closeSettings();
        });

        document.getElementById('saveSettingsBtn').addEventListener('click', () => {
            this.saveSettings();
        });

        document.getElementById('settingsModal').addEventListener('click', (e) => {
            if (e.target === document.getElementById('settingsModal')) {
                this.closeSettings();
            }
        });

        // Temperature slider
        document.getElementById('temperatureSlider').addEventListener('input', () => {
            this.updateTemperatureDisplay();
        });
    }

    updateCharCount() {
        const count = this.messageInput.value.length;
        this.charCount.textContent = count;
        this.charCount.style.color = count > 900 ? '#ff3b30' : '#8e8e93';
    }

    updateSendButton() {
        const hasText = this.messageInput.value.trim().length > 0;
        this.sendButton.disabled = !hasText;
        this.sendButton.style.opacity = hasText ? '1' : '0.5';
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isTyping) return;

        // Add user message to UI
        this.addMessage(message, 'user');
        this.messageHistory.push({ role: 'user', content: message });

        // Clear input
        this.messageInput.value = '';
        this.updateCharCount();
        this.updateSendButton();

        // Show typing indicator
        this.showTyping();

        try {
            // Send to API
            const response = await this.callChatAPI(message);

            // Hide typing indicator
            this.hideTyping();

            // Check for name update commands in the response
            const nameUpdateMatch = response.match(/I've updated your name to ([^.!?]+)/i);
            if (nameUpdateMatch) {
                const newName = nameUpdateMatch[1].trim();
                this.userNameInput.value = newName;
                // Remove the name update part from the displayed response
                const cleanResponse = response.replace(/I've updated your name to [^.!?]+[.!?]\s*/i, '');
                this.addMessage(this.filterHallucinations(cleanResponse), 'ai');
            } else {
                // Add AI response to UI
                this.addMessage(this.filterHallucinations(response), 'ai');
            }

            this.messageHistory.push({ role: 'assistant', content: response });

        } catch (error) {
            console.error('Chat error:', error);
            this.hideTyping();

            // Show error message
            this.addMessage('Sorry, I encountered an error. Please try again.', 'ai', true);
        }
    }

    async callChatAPI(message) {
        const userName = this.userNameInput.value.trim() || 'User';
        const response = await fetch(`${this.apiBase}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                mode: 'default',
                user_name: userName
            })
        });

        if (!response.ok) {
            throw new Error(`API request failed: ${response.status}`);
        }

        const data = await response.json();
        return data.response;
    }

    addMessage(content, sender, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message-group ${sender}-message-group`;

        // Add sender name
        const nameDiv = document.createElement('div');
        nameDiv.className = 'message-sender';
        const userName = this.userNameInput.value.trim() || 'You';
        nameDiv.textContent = sender === 'user' ? userName : 'Ignis';
        messageDiv.appendChild(nameDiv);

        // Create message bubble container
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = `message-bubble ${sender}-message`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;

        if (isError) {
            contentDiv.style.backgroundColor = '#ff6b6b';
        }

        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = this.getCurrentTime();

        bubbleDiv.appendChild(contentDiv);
        bubbleDiv.appendChild(timeDiv);
        messageDiv.appendChild(bubbleDiv);

        // Remove welcome message if this is the first real message
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    showTyping() {
        this.isTyping = true;
        this.sendButton.classList.add('loading');
        this.sendButton.disabled = true;
        this.scrollToBottom();
    }

    hideTyping() {
        this.isTyping = false;
        this.sendButton.classList.remove('loading');
        this.updateSendButton(); // Re-enable button based on input content
    }

    scrollToBottom() {
        setTimeout(() => {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }, 100);
    }

    getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    async showMemoryStatus() {
        try {
            const response = await fetch(`${this.apiBase}/memory`);
            if (!response.ok) {
                throw new Error(`API request failed: ${response.status}`);
            }
            const data = await response.json();
            let statusText = `Memory Status: ${data.count} conversations stored\n\n`;
            if (data.memories.length > 0) {
                statusText += 'Recent conversations:\n';
                data.memories.slice(-3).forEach((mem, index) => {
                    statusText += `${index + 1}. ${mem.content.substring(0, 100)}...\n`;
                });
            }
            this.memoryStatus.textContent = statusText;
        } catch (error) {
            console.error('Memory status error:', error);
            this.memoryStatus.textContent = 'Unable to load memory status.';
        }

        this.memoryModal.style.display = 'block';
    }

    hideMemoryModal() {
        this.memoryModal.style.display = 'none';
    }

    // Settings Modal Functions
    openSettings() {
        // Load current settings from server
        this.loadSettings();
        const modal = document.getElementById('settingsModal');
        if (modal) {
            modal.style.display = 'block';
        }
    }

    closeSettings() {
        document.getElementById('settingsModal').style.display = 'none';
    }

    async loadSettings() {
        try {
            // First try to load from localStorage
            const localSettings = this.loadLocalSettings();
            if (localSettings) {
                console.log('Loading settings from localStorage');
                this.applySettingsToForm(localSettings);
                return;
            }

            // Fallback to server settings
            const response = await fetch(`${this.apiBase}/settings`);
            if (response.ok) {
                const settings = await response.json();
                console.log('Loading settings from server');
                this.applySettingsToForm(settings);
                // Save server settings to localStorage as defaults
                this.saveLocalSettings(settings);
            }
        } catch (error) {
            console.warn('Could not load settings:', error);
            // Try localStorage as fallback
            const localSettings = this.loadLocalSettings();
            if (localSettings) {
                this.applySettingsToForm(localSettings);
            }
        }
    }

    applySettingsToForm(settings) {
        document.getElementById('temperatureSlider').value = settings.generation?.temperature || 0.7;
        document.getElementById('maxTokensInput').value = settings.generation?.max_tokens || 512;
        document.getElementById('memoryModeSelect').value = settings.memory?.mode || 'dual';
        document.getElementById('responseStyleSelect').value = settings.generation?.style || 'balanced';
        this.updateTemperatureDisplay();
    }

    loadLocalSettings() {
        try {
            const settings = localStorage.getItem('ignis_settings');
            return settings ? JSON.parse(settings) : null;
        } catch (error) {
            console.warn('Could not load local settings:', error);
            return null;
        }
    }

    saveLocalSettings(settings) {
        try {
            localStorage.setItem('ignis_settings', JSON.stringify(settings));
        } catch (error) {
            console.warn('Could not save local settings:', error);
        }
    }

    async saveSettings() {
        const settings = {
            generation: {
                temperature: parseFloat(document.getElementById('temperatureSlider').value),
                max_tokens: parseInt(document.getElementById('maxTokensInput').value),
                style: document.getElementById('responseStyleSelect').value
            },
            memory: {
                mode: document.getElementById('memoryModeSelect').value
            }
        };

        // Save to localStorage immediately
        this.saveLocalSettings(settings);
        console.log('Settings saved to localStorage');

        try {
            const response = await fetch(`${this.apiBase}/settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            if (response.ok) {
                console.log('Settings saved to server');
                alert('Settings saved successfully!');
            } else {
                console.warn('Failed to save to server, but saved locally');
                alert('Settings saved locally (server unavailable)');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            alert('Settings saved locally (server error)');
        }
    }

    updateTemperatureDisplay() {
        const value = document.getElementById('temperatureSlider').value;
        document.getElementById('temperatureValue').textContent = value;
    }

    filterHallucinations(response) {
        // Remove common hallucination patterns but be less aggressive
        let cleaned = response;

        // Remove "OUTPUT:" prefixes
        cleaned = cleaned.replace(/^OUTPUT:\s*/i, '');

        // Only remove very specific hallucination patterns, not legitimate responses
        // Remove patterns that clearly indicate the AI is role-playing as the user
        cleaned = cleaned.replace(/\bJin:\s*[^.!?]*[.!?]/g, ''); // Remove if it starts with "Jin: [something]"
        cleaned = cleaned.replace(/\bUser:\s*[^.!?]*[.!?]/g, ''); // Remove if it starts with "User: [something]"

        // Clean up extra whitespace
        cleaned = cleaned.replace(/\s+/g, ' ').trim();

        // If the response became empty or too short after filtering, provide a fallback
        if (cleaned.length < 5) {
            cleaned = "I'm here to help! How can I assist you?";
        }

        return cleaned;
    }

    // Utility method to check API connectivity
    async checkAPIStatus() {
        try {
            const response = await fetch(`${this.apiBase}/status`);
            if (response.ok) {
                const data = await response.json();
                console.log('API Status:', data);
                return true;
            }
        } catch (error) {
            console.error('API not available:', error);
        }
        return false;
    }
}

// Initialize chat when page loads
document.addEventListener('DOMContentLoaded', () => {
    const chat = new IgnisChat();
    window.chatInstance = chat; // Make available globally

    // Check API status on load - disabled for debugging
    // chat.checkAPIStatus().then(available => {
    //     if (!available) {
    //         console.warn('Ignis API not available. Make sure the API server is running with: python main.py --interface api');
    //     }
    // });
});

// Handle page visibility changes (optional enhancement)
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden, could pause/resume operations if needed
    } else {
        // Page is visible again
    }
});