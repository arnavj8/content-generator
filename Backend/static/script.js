document.addEventListener('DOMContentLoaded', () => {
    const chatButton = document.getElementById('chat-button');
    const chatContainer = document.getElementById('chat-container');
    const closeChat = document.getElementById('close-chat');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const chatMessages = document.getElementById('chat-messages');
    const statusMessage = document.getElementById('status-message');
    // const statusDisplay = document.getElementById('status-display');
    initializeKnowledgeBase();

    let checkStatusInterval;
    let statusCheckInProgress = false;

    // function updateStatus(message, isError = false) {
    //     statusDisplay.textContent = message;
    //     statusDisplay.className = `text-${isError ? 'red' : 'gray'}-600`;
    // }

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
    });
    
    closeChat.addEventListener('click', () => {
        chatContainer.classList.add('hidden');
    });
    
    function addMessageToChat(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex items-start mb-4 ${sender === 'user' ? 'justify-end' : ''}`;
        
        const messageContent = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        
        messageDiv.innerHTML = `
            <div class="${sender === 'user' ? 
                'bg-blue-500 text-white' : 
                'bg-blue-100 text-gray-800'} rounded-lg py-2 px-4 chat-message">
                ${messageContent}
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
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
                addMessageToChat(data.response, 'bot');
            } else {
                addMessageToChat('Received empty response from server.', 'bot');
            }
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