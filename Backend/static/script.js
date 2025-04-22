document.addEventListener('DOMContentLoaded', () => {
    const chatButton = document.getElementById('chat-button');
    const chatContainer = document.getElementById('chat-container');
    const closeChat = document.getElementById('close-chat');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const chatMessages = document.getElementById('chat-messages');
    const statusMessage = document.getElementById('status-message');
    const clickSound = document.getElementById("click-sound");
    const typingSound = document.getElementById("typing-sound");
    const botSound = document.getElementById("bot-sound");
    clickSound.volume = 0.7;
    typingSound.volume = 0.1;
    // botSound.volume = 0.3;
    initializeKnowledgeBase();

    let checkStatusInterval;
    let statusCheckInProgress = false;


    function checkStatus() {
        if (statusCheckInProgress) return;
        
        statusCheckInProgress = true;
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                console.log('Status check:', data);
                
                statusCheckInProgress = false;
                
                if (data.initialized) {
                    // updateStatus('Knowledge base ready');
                    statusMessage.textContent = '';
                    userInput.disabled = false;
                    sendButton.disabled = false;
                    clearInterval(checkStatusInterval);
                    
                    if (!document.querySelector('.welcome-message')) {
                        const welcomeMessage = document.createElement('div');
                        welcomeMessage.classList.add('welcome-message');
                        welcomeMessage.innerHTML = `
                            <div class="flex items-start mb-4">
                                <div class="bg-blue-100 text-gray-800 rounded-lg py-2 px-4 chat-message">
                                    Hello! I'm ready to help you with questions about the repository. What would you like to know?
                                </div>
                            </div>
                        `;
                        chatMessages.appendChild(welcomeMessage);
                        
                    }
                } else if (data.status === 'failed') {
                    // updateStatus(`Initialization failed: ${data.message}`, true);
                    statusMessage.textContent = data.message;
                    clearInterval(checkStatusInterval);
                    userInput.disabled = true;
                    sendButton.disabled = true;
                } else {
                    // updateStatus('Initializing knowledge base...');
                    statusMessage.textContent = 'Please wait while the system initializes...';
                    
                    if (data.status === 'not_started') {
                        initializeKnowledgeBase();
                    }
                }
            })
            .catch(error => {
                console.error('Error checking status:', error);
                // updateStatus('Error checking status', true);
                statusCheckInProgress = false;
                clearInterval(checkStatusInterval);
            });
    }

    function initializeKnowledgeBase() {
        fetch('/api/initialize', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    checkStatusInterval = setInterval(checkStatus, 5000);
                } else {
                    // updateStatus('Failed to initialize', true);
                    statusMessage.textContent = data.message;
                }
            })
            .catch(error => {
                console.error('Error initializing KB:', error);
                // updateStatus('Error initializing knowledge base', true);
            });
    }

    // Start status checking
    checkStatus();
    
    // Toggle chat visibility
    chatButton.addEventListener('click', () => {
        chatContainer.classList.toggle('hidden');
        if (!chatContainer.classList.contains('hidden')) {
            userInput.focus();
        }
        clickSound.currentTime = 0; // rewind to start
        clickSound.play().catch((err) => {
        console.error("Sound play failed:", err);
        if (botSound) {
              botSound.currentTime = 0;
              botSound.play();
            }
        });
        

    });
    
    closeChat.addEventListener('click', () => {
        if (clickSound) {
                  clickSound.currentTime = 0;
                  clickSound.play();
                }
        
                if (typingSound) {
                  typingSound.pause();
                  typingSound.currentTime = 0;
                }
        chatContainer.classList.add('hidden');

    });
    function playTyping() {
        if (typingSound) {
          typingSound.currentTime = 0;
          typingSound.play().catch((e) => console.warn("Typing sound failed:", e));
        }
      }
    
      function stopTyping() {
        if (typingSound) {
          typingSound.pause();
          typingSound.currentTime = 0;
   }
    }
    // function addMessageToChat(text, sender) {
    //     const messageDiv = document.createElement('div');
    //     messageDiv.className = `flex items-start mb-4 ${sender === 'user' ? 'justify-end' : ''}`;
        
    //     const messageContent = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        
    //     messageDiv.innerHTML = `
    //         <div class="${sender === 'user' ? 
    //             'bg-blue-500 text-white' : 
    //             'bg-blue-100 text-gray-800'} rounded-lg py-2 px-4 chat-message">
    //             ${messageContent}
    //         </div>
    //     `;
        
    //     chatMessages.appendChild(messageDiv);
    //     chatMessages.scrollTop = chatMessages.scrollHeight;
    // }
    function addMessageToChat(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex items-start mb-4 ${sender === 'user' ? 'justify-end' : ''}`;
        
        const messageContent = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        
        messageDiv.innerHTML = `
            <div class="${sender === 'user' ? 
                'bg-blue-500 text-white' : 
                'bg-blue-100 text-gray-800'} rounded-lg py-2 px-4 chat-message">
                ${sender === 'user' ? messageContent : '<span class="typing-text"></span>'}
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    
        if (sender === 'bot') {
            const typingElement = messageDiv.querySelector('.typing-text');
            let index = 0;
            const speed = 10; 
            
            function typeWriter() {
                if (index < messageContent.length) {
                    typingElement.innerHTML += messageContent.charAt(index);
                    index++;
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                    setTimeout(typeWriter, speed);
                }
            }
            
            typeWriter();
        }
    }
    
    function sendMessage() {
        const message = userInput.value.trim();
        if (!message || userInput.disabled) return;
        
        addMessageToChat(message, 'user');
        userInput.value = '';
        userInput.disabled = true;
        sendButton.disabled = true;
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'flex items-start mb-4';
        typingDiv.innerHTML = `
            <div class="bg-blue-100 text-gray-800 rounded-lg py-2 px-4 chat-message typing-indicator">
                <span>.</span><span>.</span><span>.</span>
            </div>
        `;
        typingDiv.id = 'typing-indicator';
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: message })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const indicator = document.getElementById('typing-indicator');
            if (indicator) indicator.remove();
            
            if (data.response) {
                playTyping();
                // playTyping()
                addMessageToChat(data.response, 'bot');
            } else {
                addMessageToChat('Received empty response from server.', 'bot');
            }
            stopTyping()
        })
        .catch(error => {
            console.error('Error:', error);
            const indicator = document.getElementById('typing-indicator');
            if (indicator) indicator.remove();
            addMessageToChat('Sorry, there was an error processing your request: ' + error.message, 'bot');
        })
        .finally(() => {
            userInput.disabled = false;
            sendButton.disabled = false;
            userInput.focus();
        });
    }
    
    
    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

});

// Add this to your script.js
const toggleSidebar = () => {
    const sidebar = document.querySelector('aside');
    sidebar.classList.toggle('-translate-x-full');
}

// Add a button for mobile menu toggle
const addMobileMenuButton = () => {
    const button = document.createElement('button');
    button.className = 'lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-slate-800 text-white';
    button.innerHTML = `
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
        </svg>
    `;
    button.onclick = toggleSidebar;
    document.body.appendChild(button);
}

// Initialize mobile menu
if (window.innerWidth < 1024) {
    addMobileMenuButton();
}

// ################### API KEYS HANDLGIN ###########################

// Function to save API keys to localStorage
function saveAPIKeys(geminiKey, huggingfaceKey) {
    localStorage.setItem('geminiApiKey', geminiKey);
    localStorage.setItem('huggingfaceApiKey', huggingfaceKey);
}

// Function to load API keys from localStorage
function loadAPIKeys() {
    const geminiKey = localStorage.getItem('geminiApiKey') || '';
    const huggingfaceKey = localStorage.getItem('huggingfaceApiKey') || '';
    
    // Set the input values
    document.getElementById('geminiApiKey').value = geminiKey;
    document.getElementById('huggingfaceApiKey').value = huggingfaceKey;
}

// Function to handle API key changes
function handleAPIKeyChange() {
    const geminiInput = document.getElementById('geminiApiKey');
    const huggingfaceInput = document.getElementById('huggingfaceApiKey');
    
    saveAPIKeys(geminiInput.value, huggingfaceInput.value);
}

class NotificationManager {
    constructor() {
        this.createContainer();
    }

    createContainer() {
        // Create container if it doesn't exist
        if (!document.getElementById('notificationsContainer')) {
            const container = document.createElement('div');
            container.id = 'notificationsContainer';
            container.className = 'm-4 space-y-2 fixed top-4 right-4 z-50';
            document.body.appendChild(container);
        }
    }

    show(message, type = 'info') {
        const container = document.getElementById('notificationsContainer');
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification rounded-lg p-4 flex items-center gap-3 ${
            type === 'error' ? 'bg-red-50 text-red-700 border border-red-200' : 
            type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 
            'bg-blue-50 text-blue-700 border border-blue-200'
        }`;
        
        // Create icon based on notification type
        const icon = document.createElement('div');
        icon.className = 'flex-shrink-0';
        if (type === 'error') {
            icon.innerHTML = `<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
            </svg>`;
        } else if (type === 'success') {
            icon.innerHTML = `<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
            </svg>`;
        } else {
            icon.innerHTML = `<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2h-1v-3a1 1 0 00-1-1z" clip-rule="evenodd"></path>
            </svg>`;
        }
        
        // Create message element
        const messageEl = document.createElement('div');
        messageEl.textContent = message;
        messageEl.className = 'flex-1 text-sm font-medium';
        
        // Append elements
        notification.appendChild(icon);
        notification.appendChild(messageEl);
        container.appendChild(notification);
        
        // Animation
        setTimeout(() => notification.classList.add('show'), 10);
        
        // Remove after 5 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }
}

// Create global instance
window.notifications = new NotificationManager();