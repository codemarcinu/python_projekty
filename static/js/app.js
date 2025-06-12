// Konfiguracja
const config = {
    wsUrl: `ws://${window.location.host}/ws/${generateUserId()}`,
    reconnectAttempts: 3,
    reconnectDelay: 1000,
    messageHistory: [],
    maxHistoryLength: 100
};

// Elementy DOM
const elements = {
    connectionStatus: document.getElementById('connectionStatus'),
    modelInfo: document.getElementById('modelInfo'),
    chatHistory: document.getElementById('chatHistory'),
    messageInput: document.getElementById('messageInput'),
    sendButton: document.getElementById('sendMessage'),
    themeToggle: document.getElementById('themeToggle'),
    clearChat: document.getElementById('clearChat'),
    exportChat: document.getElementById('exportChat'),
    featureCards: document.querySelectorAll('.feature-card')
};

// Inicjalizacja WebSocket
let ws = null;
let reconnectCount = 0;

// Funkcje pomocnicze
function generateUserId() {
    return 'user_' + Math.random().toString(36).substr(2, 9);
}

function updateConnectionStatus(connected) {
    elements.connectionStatus.textContent = connected ? 'Połączony' : 'Rozłączony';
    elements.connectionStatus.className = connected ? 'status-connected' : 'status-disconnected';
}

function addMessageToHistory(message, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${isUser ? 'user-message' : 'ai-message'}`;
    
    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = message;
    
    const timestamp = document.createElement('div');
    timestamp.className = 'message-timestamp';
    timestamp.textContent = new Date().toLocaleTimeString();
    
    messageDiv.appendChild(content);
    messageDiv.appendChild(timestamp);
    elements.chatHistory.appendChild(messageDiv);
    
    // Scroll do najnowszej wiadomości
    elements.chatHistory.scrollTop = elements.chatHistory.scrollHeight;
    
    // Zapisz w historii
    config.messageHistory.push({
        content: message,
        isUser,
        timestamp: new Date().toISOString()
    });
    
    // Ogranicz długość historii
    if (config.messageHistory.length > config.maxHistoryLength) {
        config.messageHistory.shift();
    }
}

// Obsługa WebSocket
function connectWebSocket() {
    ws = new WebSocket(config.wsUrl);
    
    ws.onopen = () => {
        updateConnectionStatus(true);
        reconnectCount = 0;
        console.log('WebSocket connected');
    };
    
    ws.onclose = () => {
        updateConnectionStatus(false);
        console.log('WebSocket disconnected');
        
        // Próba ponownego połączenia
        if (reconnectCount < config.reconnectAttempts) {
            reconnectCount++;
            setTimeout(connectWebSocket, config.reconnectDelay * reconnectCount);
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'message') {
                addMessageToHistory(data.content);
            } else if (data.type === 'error') {
                addMessageToHistory(`Błąd: ${data.message}`, false);
            }
        } catch (error) {
            console.error('Error parsing message:', error);
        }
    };
}

// Obsługa dark mode
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const icon = elements.themeToggle.querySelector('.theme-icon');
    icon.textContent = theme === 'light' ? '🌙' : '☀️';
}

// Obsługa wiadomości
function sendMessage() {
    const message = elements.messageInput.value.trim();
    if (!message) return;
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ content: message }));
        addMessageToHistory(message, true);
        elements.messageInput.value = '';
    } else {
        addMessageToHistory('Błąd: Brak połączenia z serwerem', false);
    }
}

// Obsługa eksportu historii
function exportChatHistory() {
    const history = config.messageHistory.map(msg => ({
        ...msg,
        timestamp: new Date(msg.timestamp).toLocaleString()
    }));
    
    const blob = new Blob([JSON.stringify(history, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-history-${new Date().toISOString()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Event Listeners
elements.sendButton.addEventListener('click', sendMessage);
elements.messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

elements.themeToggle.addEventListener('click', toggleTheme);
elements.clearChat.addEventListener('click', () => {
    elements.chatHistory.innerHTML = '';
    config.messageHistory = [];
});

elements.exportChat.addEventListener('click', exportChatHistory);

elements.featureCards.forEach(card => {
    card.addEventListener('click', () => {
        const feature = card.dataset.feature;
        // TODO: Implementacja funkcji
        console.log(`Feature clicked: ${feature}`);
    });
});

// Inicjalizacja
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    connectWebSocket();
}); 