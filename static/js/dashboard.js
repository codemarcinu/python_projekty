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

// Theme Management
const themeToggle = document.querySelector('.theme-toggle');
const body = document.body;

// Check for saved theme preference
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'light') {
    body.classList.remove('dark-theme');
}

themeToggle.addEventListener('click', () => {
    body.classList.toggle('dark-theme');
    localStorage.setItem('theme', body.classList.contains('dark-theme') ? 'dark' : 'light');
});

// Chat Interface
const messageInput = document.getElementById('messageInput');
const chatHistory = document.getElementById('chatHistory');
const sendButton = document.querySelector('.send-button');

// Auto-resize textarea
messageInput.addEventListener('input', () => {
    messageInput.style.height = 'auto';
    messageInput.style.height = messageInput.scrollHeight + 'px';
});

// Handle Enter key
messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    // Dodaj wiadomość użytkownika do historii
    addMessage('user', message);
    
    // Wyślij wiadomość do backendu przez WebSocket
    wsManager.sendMessage(message);
    
    // Wyczyść input
    messageInput.value = '';
    messageInput.style.height = 'auto';
}

function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const icon = role === 'user' ? '👤' : '🤖';
    const name = role === 'user' ? 'Ty' : 'AI Assistant';
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="message-icon">${icon}</span>
            <span class="message-name">${name}</span>
            <span class="message-time">${new Date().toLocaleTimeString()}</span>
        </div>
        <div class="message-content">${content}</div>
    `;
    
    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

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

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
});

dropZone.addEventListener('click', () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.accept = '.pdf,.txt';
    
    input.onchange = (e) => {
        const files = Array.from(e.target.files);
        handleFiles(files);
    };
    
    input.click();
});

function handleFiles(files) {
    files.forEach(file => {
        if (file.size > 50 * 1024 * 1024) { // 50MB limit
            alert(`Plik ${file.name} jest za duży. Maksymalny rozmiar to 50MB.`);
            return;
        }
        
        addFileToList(file);
    });
}

function addFileToList(file) {
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    
    const fileSize = formatFileSize(file.size);
    const fileType = file.name.split('.').pop().toUpperCase();
    
    fileItem.innerHTML = `
        <div class="file-icon">
            <i class="icon icon-file-text"></i>
        </div>
        <div class="file-info">
            <div class="file-name">${file.name}</div>
            <div class="file-meta">${fileSize} • ${fileType}</div>
        </div>
        <div class="file-actions">
            <button class="btn btn-icon" title="Usuń">
                <i class="icon icon-trash"></i>
            </button>
        </div>
    `;
    
    fileList.appendChild(fileItem);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Model Selection
const modelSelect = document.getElementById('modelSelect');
modelSelect.addEventListener('change', (e) => {
    // Handle model change (implement API call)
    console.log('Selected model:', e.target.value);
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Add initial system message
    addMessage('ai', 'Witaj! Jestem Twoim asystentem AI. Jak mogę Ci pomóc?');

    // Update stats every 30 seconds
    setInterval(() => wsManager.updateStats(), 30000);
    wsManager.updateStats();
});

// Sidebar Collapse
const sidebarCollapseBtn = document.getElementById('sidebarCollapseBtn');
const bodyRoot = document.getElementById('bodyRoot');

// Przywróć stan z localStorage
if (localStorage.getItem('sidebarCollapsed') === 'true') {
    bodyRoot.classList.add('sidebar-collapsed');
}

sidebarCollapseBtn.addEventListener('click', () => {
    bodyRoot.classList.toggle('sidebar-collapsed');
    const collapsed = bodyRoot.classList.contains('sidebar-collapsed');
    localStorage.setItem('sidebarCollapsed', collapsed ? 'true' : 'false');
}); 