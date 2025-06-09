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
        this.conversationId = this.generateConversationId();
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isConnected = false;
    }

    generateConversationId() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${this.conversationId}`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.updateConnectionStatus(true);
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('Error parsing message:', error);
                this.showError('Błąd przetwarzania wiadomości');
            }
        };

        this.ws.onclose = () => {
            console.log('WebSocket closed');
            this.isConnected = false;
            this.updateConnectionStatus(false);
            this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showError('Błąd połączenia WebSocket');
        };
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            setTimeout(() => this.connect(), this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('Max reconnection attempts reached');
            this.showError('Połączenie WebSocket zostało utracone. Odśwież stronę.');
        }
    }
    
    sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const data = {
                message: message,
                use_agent: true,
                timestamp: new Date().toISOString()
            };
            
            this.ws.send(JSON.stringify(data));
            return true;
        }
        return false;
    }
    
    handleMessage(data) {
        if (data.error) {
            this.showError(data.error);
        } else if (data.response) {
            this.displayMessage('assistant', data.response);
        } else if (data.type === 'stats') {
            this.updateStatsDisplay(data.data);
        }
    }
    
    displayMessage(sender, message) {
        const chatHistory = document.getElementById('chatHistory');
        if (!chatHistory) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-role">${sender === 'user' ? 'Ty' : 'AI'}</div>
                <div class="message-text">${message}</div>
                <div class="message-time">${new Date().toLocaleTimeString()}</div>
            </div>
        `;
        
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
    
    updateConnectionStatus(connected) {
        const status = document.getElementById('connectionStatus');
        if (status) {
            status.textContent = connected ? 'Połączony' : 'Rozłączony';
            status.className = connected ? 'status-connected' : 'status-disconnected';
        }
    }
    
    showError(message) {
        const notification = document.createElement('div');
        notification.className = 'notification error';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
    
    updateStats() {
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                this.updateStatsDisplay(data);
            })
            .catch(error => {
                console.error('Error fetching stats:', error);
            });
    }
    
    updateStatsDisplay(data) {
        const modelInfo = document.getElementById('modelInfo');
        const activeModels = document.getElementById('activeModels');
        const docCount = document.getElementById('docCount');
        const conversations = document.getElementById('conversations');
        
        if (modelInfo) modelInfo.textContent = data.active_model || 'Gemma3:12B';
        if (activeModels) activeModels.textContent = data.active_models || '2';
        if (docCount) docCount.textContent = data.doc_count || '0';
        if (conversations) conversations.textContent = data.conversations || '1';
    }
}

// Initialize WebSocket manager
let wsManager;

document.addEventListener('DOMContentLoaded', function() {
    wsManager = new WebSocketManager();
    
    // Event listeners
    const sendButton = document.getElementById('sendMessage');
    const messageInput = document.getElementById('messageInput');
    
    if (sendButton && messageInput) {
        sendButton.addEventListener('click', () => {
            const message = messageInput.value.trim();
            if (message) {
                wsManager.displayMessage('user', message);
                wsManager.sendMessage(message);
                messageInput.value = '';
            }
        });
        
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendButton.click();
            }
        });
    }
    
    // Update stats every 30 seconds
    setInterval(() => wsManager.updateStats(), 30000);
}); 