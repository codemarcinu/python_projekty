// WebSocket Connection
class WebSocketManager {
    constructor() {
        this.conversationId = this.generateConversationId();
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isConnected = false;
        this.connect();
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
        const wsUrl = `${protocol}//${window.location.host}/web/ws/${this.conversationId}`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
                this.showNotification('Połączono z serwerem', 'success');
            };

            this.ws.onmessage = (event) => {
                try {
                    // Try to parse as JSON first
                    let data;
                    try {
                        data = JSON.parse(event.data);
                    } catch {
                        // If not JSON, treat as plain text message
                        data = {
                            type: 'message',
                            content: event.data
                        };
                    }
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Error handling message:', error);
                    this.showError('Błąd przetwarzania wiadomości');
                }
            };

            this.ws.onclose = (event) => {
                console.log('WebSocket closed:', event.code, event.reason);
                this.isConnected = false;
                this.updateConnectionStatus(false);
                
                // Don't reconnect if the connection was closed normally
                if (event.code === 1000) {
                    this.showNotification('Połączenie zamknięte', 'info');
                    return;
                }
                
                this.attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.showError('Błąd połączenia WebSocket');
            };
        } catch (error) {
            console.error('Error creating WebSocket:', error);
            this.showError('Nie można utworzyć połączenia WebSocket');
            this.attemptReconnect();
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms...`);
            this.showNotification(`Próba ponownego połączenia (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`, 'info');
            setTimeout(() => this.connect(), delay);
        } else {
            this.showError('Nie można połączyć się z serwerem. Odśwież stronę.');
        }
    }

    sendMessage(message) {
        if (!this.isConnected) {
            this.showError('Brak połączenia z serwerem');
            return;
        }

        try {
            this.ws.send(JSON.stringify({
                type: 'message',
                content: message,
                model: 'gemma3:12b',
                use_rag: true
            }));
        } catch (error) {
            console.error('Error sending message:', error);
            this.showError('Błąd wysyłania wiadomości');
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'message':
                this.displayMessage('ai', data.content);
                break;
            case 'stats':
                this.updateStatsDisplay(data);
                break;
            case 'error':
                this.showError(data.message);
                break;
            default:
                console.warn('Unknown message type:', data.type);
        }
    }

    displayMessage(sender, message) {
        const chatHistory = document.getElementById('chatHistory');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-role">${sender === 'user' ? 'Ty' : 'AI'}</div>
                <div class="message-text">${message}</div>
            </div>
        `;
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        statusElement.textContent = connected ? 'Połączony' : 'Rozłączony';
        statusElement.className = connected ? 'status-connected' : 'status-disconnected';
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    updateStats() {
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                this.updateStatsDisplay(data);
            })
            .catch(error => {
                console.error('Stats update error:', error);
                this.showError('Błąd aktualizacji statystyk');
            });
    }

    updateStatsDisplay(data) {
        document.getElementById('activeModels').textContent = data.active_models || 0;
        document.getElementById('docCount').textContent = data.doc_count || 0;
        document.getElementById('conversations').textContent = data.conversations || 0;
    }
}

// Initialize WebSocket connection
const wsManager = new WebSocketManager();

// Chat Functions
function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();

    if (!message) return;

    // Add user message to chat
    wsManager.displayMessage('user', message);
    messageInput.value = '';

    // Send to WebSocket
    wsManager.sendMessage(message);
}

// File Upload Handling
const dropZone = document.getElementById('dropZone');
const fileList = document.getElementById('fileList');

if (dropZone) {
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', handleFileDrop);
    dropZone.addEventListener('click', triggerFileInput);
}

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
            wsManager.showError('Plik jest za duży. Maksymalny rozmiar to 50MB.');
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
            if (data.status === 'success') {
                addFileToList(file.name);
                wsManager.showNotification('Plik został przesłany pomyślnie', 'success');
            } else {
                wsManager.showError('Błąd podczas przesyłania pliku');
            }
        })
        .catch(error => {
            console.error('Upload error:', error);
            wsManager.showError('Błąd podczas przesyłania pliku');
        });
    });
}

function addFileToList(filename) {
    if (!fileList) return;
    
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.innerHTML = `
        <i class="icon icon-file"></i>
        <span>${filename}</span>
        <button onclick="deleteFile('${filename}')" class="delete-btn">
            <i class="icon icon-trash"></i>
        </button>
    `;
    fileList.appendChild(fileItem);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendMessage');

    if (messageInput && sendButton) {
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        sendButton.addEventListener('click', sendMessage);
    }

    // Update stats every 30 seconds
    setInterval(() => wsManager.updateStats(), 30000);
    wsManager.updateStats();
}); 