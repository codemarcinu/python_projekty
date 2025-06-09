// WebSocket Connection
const ws = new WebSocket(`ws://${window.location.host}/ws`);

ws.onopen = () => {
    console.log('WebSocket Connected');
    updateStats();
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleWebSocketMessage(data);
};

ws.onclose = () => {
    console.log('WebSocket Disconnected');
    setTimeout(() => {
        window.location.reload();
    }, 5000);
};

// File Upload Handling
const dropZone = document.getElementById('dropZone');
const fileList = document.getElementById('fileList');

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', handleFileDrop);
dropZone.addEventListener('click', triggerFileInput);

function handleFileDrop(e) {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    handleFiles(files);
}

function triggerFileInput() {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.accept = '.pdf,.txt,.doc,.docx';
    input.onchange = (e) => handleFiles(e.target.files);
    input.click();
}

function handleFiles(files) {
    Array.from(files).forEach(file => {
        if (file.size > 50 * 1024 * 1024) { // 50MB limit
            showNotification('Plik jest za duży. Maksymalny rozmiar to 50MB.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                addFileToList(file.name, data.file_id);
                showNotification('Plik został przesłany pomyślnie', 'success');
            } else {
                showNotification('Błąd podczas przesyłania pliku', 'error');
            }
        })
        .catch(error => {
            console.error('Upload error:', error);
            showNotification('Błąd podczas przesyłania pliku', 'error');
        });
    });
}

function addFileToList(filename, fileId) {
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.innerHTML = `
        <i class="icon icon-file"></i>
        <span>${filename}</span>
        <button onclick="deleteFile('${fileId}')" class="delete-btn">
            <i class="icon icon-trash"></i>
        </button>
    `;
    fileList.appendChild(fileItem);
}

// Chat Functions
function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    const model = document.getElementById('modelSelect').value;

    if (!message) return;

    // Add user message to chat
    addMessageToChat('user', message);
    messageInput.value = '';

    // Send to WebSocket
    ws.send(JSON.stringify({
        type: 'message',
        content: message,
        model: model,
        use_rag: true
    }));
}

function addMessageToChat(role, content) {
    const chatHistory = document.getElementById('chatHistory');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-role">${role === 'user' ? 'Ty' : 'AI'}</div>
            <div class="message-text">${content}</div>
        </div>
    `;
    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Stats Update
function updateStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            document.querySelector('.model-status').textContent = 
                `${data.active_model} ● ${data.status}`;
            document.querySelector('.doc-count').textContent = data.doc_count;
            document.querySelector('.memory-usage').textContent = data.memory_usage;
        })
        .catch(error => console.error('Stats update error:', error));
}

// WebSocket Message Handler
function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'message':
            addMessageToChat('ai', data.content);
            break;
        case 'stats':
            updateStats();
            break;
        case 'error':
            showNotification(data.message, 'error');
            break;
    }
}

// Utility Functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Initialize
setInterval(updateStats, 30000); // Update stats every 30 seconds
updateStats();

class WebSocketManager {
    constructor() {
        this.ws = null;
        this.conversationId = this.generateConversationId();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // 1 sekunda
    }
    
    generateConversationId() {
        return 'conv_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }
    
    connect() {
        try {
            // POPRAWNY protokół WebSocket
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/${this.conversationId}`;
            
            console.log('Connecting to WebSocket:', wsUrl);
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = (event) => {
                console.log('WebSocket connected successfully');
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus(false);
            };
            
            this.ws.onclose = (event) => {
                console.log('WebSocket closed:', event.code, event.reason);
                this.updateConnectionStatus(false);
                this.attemptReconnect();
            };
            
        } catch (error) {
            console.error('Error creating WebSocket connection:', error);
            this.updateConnectionStatus(false);
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('Max reconnection attempts reached');
            this.showError('Połączenie WebSocket zostało utracone. Odśwież stronę.');
        }
    }
    
    sendMessage(message, useAgent = true) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const data = {
                message: message,
                use_agent: useAgent,
                timestamp: new Date().toISOString()
            };
            
            try {
                this.ws.send(JSON.stringify(data));
                return true;
            } catch (error) {
                console.error('Error sending WebSocket message:', error);
                return false;
            }
        } else {
            console.error('WebSocket not connected');
            this.showError('Brak połączenia WebSocket. Próbuję połączyć ponownie...');
            this.connect();
            return false;
        }
    }
    
    handleMessage(data) {
        if (data.error) {
            console.error('Server error:', data.error);
            this.showError(data.error);
        } else if (data.response) {
            this.displayMessage('assistant', data.response);
        }
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            statusElement.textContent = connected ? 'Połączony' : 'Rozłączony';
            statusElement.className = connected ? 'status-connected' : 'status-disconnected';
        }
    }
    
    showError(message) {
        // Pokaż błąd w interfejsie
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        
        const chatContainer = document.getElementById('chatHistory');
        if (chatContainer) {
            chatContainer.appendChild(errorDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }
    
    displayMessage(sender, message) {
        const chatContainer = document.getElementById('chatHistory');
        if (!chatContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const timestamp = new Date().toLocaleTimeString();
        messageDiv.innerHTML = `
            <div class="message-content">${message}</div>
            <div class="message-timestamp">${timestamp}</div>
        `;
        
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

// Inicjalizacja WebSocket Manager
let wsManager;

document.addEventListener('DOMContentLoaded', function() {
    // Utwórz WebSocket Manager
    wsManager = new WebSocketManager();
    wsManager.connect();
    
    // Event listener dla wysyłania wiadomości
    const sendButton = document.getElementById('sendMessage');
    const messageInput = document.getElementById('messageInput');
    const agentToggle = document.getElementById('useAgent');
    
    if (sendButton) {
        sendButton.addEventListener('click', () => {
            const message = messageInput.value.trim();
            if (message) {
                wsManager.displayMessage('user', message);
                wsManager.sendMessage(message, agentToggle.checked);
                messageInput.value = '';
            }
        });
    }
    
    if (messageInput) {
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendButton.click();
            }
        });
    }
}); 