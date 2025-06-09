// Default agent state
let useAgentByDefault = true;
let ws = null;

function initializeInterface() {
    // Set agent checkbox as checked by default
    const agentCheckbox = document.getElementById('useAgent');
    if (agentCheckbox) {
        agentCheckbox.checked = true;
    }
    
    // Add visual indicator for active agent mode
    updateAgentStatus(true);
}

function updateAgentStatus(isActive) {
    const statusElement = document.getElementById('agentStatus');
    if (statusElement) {
        statusElement.textContent = isActive ? 'Agent Aktywny' : 'Agent Nieaktywny';
        statusElement.className = isActive ? 'agent-active' : 'agent-inactive';
    }
}

function initializeWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${generateConversationId()}`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('WebSocket connection established');
        checkAgentStatus();
    };
    
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.error) {
                showError(data.error);
            } else if (data.response) {
                addMessageToChat('assistant', data.response);
                hideAgentProcessing();
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
            showError('Błąd przetwarzania odpowiedzi');
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        showError('Błąd połączenia WebSocket');
    };
    
    ws.onclose = () => {
        console.log('WebSocket connection closed');
    };
}

function generateConversationId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message) {
        showError('Proszę wprowadzić wiadomość');
        return;
    }
    
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        console.error('WebSocket nie jest połączony');
        showError('Błąd połączenia. Odśwież stronę.');
        return;
    }
    
    try {
        // Check checkbox status or use default value
        const agentCheckbox = document.getElementById('useAgent');
        const useAgent = agentCheckbox ? agentCheckbox.checked : useAgentByDefault;
        
        const data = {
            message: message,
            use_agent: useAgent,
            timestamp: new Date().toISOString()
        };
        
        ws.send(JSON.stringify(data));
        messageInput.value = '';
        addMessageToChat('user', message);
        
        // Show agent processing indicator
        if (useAgent) {
            showAgentProcessing();
        }
        
    } catch (error) {
        console.error('Błąd wysyłania wiadomości:', error);
        showError('Błąd wysyłania wiadomości');
    }
}

function showAgentProcessing() {
    const processingDiv = document.createElement('div');
    processingDiv.id = 'agentProcessing';
    processingDiv.className = 'agent-processing';
    processingDiv.innerHTML = '🤖 Agent analizuje i wybiera narzędzia...';
    
    const chatContainer = document.getElementById('chatContainer');
    chatContainer.appendChild(processingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function hideAgentProcessing() {
    const processingDiv = document.getElementById('agentProcessing');
    if (processingDiv) {
        processingDiv.remove();
    }
}

function addMessageToChat(role, content) {
    const chatContainer = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const roleIndicator = role === 'user' ? '👤' : '🤖';
    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="role-indicator">${roleIndicator}</span>
            <span class="role-name">${role === 'user' ? 'Ty' : 'Asystent'}</span>
        </div>
        <div class="message-content">${content}</div>
    `;
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    const chatContainer = document.getElementById('chatContainer');
    chatContainer.appendChild(errorDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

async function checkAgentStatus() {
    try {
        const response = await fetch('/api/agent/status');
        const data = await response.json();
        
        if (data.status === 'success') {
            const agentData = data.data;
            console.log('Agent status:', agentData);
            
            // Show available tools
            if (agentData.available_tools.length > 0) {
                console.log('Available tools:', agentData.available_tools.join(', '));
                showAvailableTools(agentData.available_tools);
            }
        }
    } catch (error) {
        console.error('Error checking agent status:', error);
    }
}

function showAvailableTools(tools) {
    const toolsContainer = document.getElementById('availableTools');
    if (toolsContainer) {
        toolsContainer.innerHTML = `
            <div class="tools-header">Dostępne narzędzia:</div>
            <div class="tools-list">
                ${tools.map(tool => `<div class="tool-item">${tool}</div>`).join('')}
            </div>
        `;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeInterface();
    initializeWebSocket();
    
    // Add event listener for message input
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
    
    // Add event listener for send button
    const sendButton = document.getElementById('sendButton');
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }
    
    // Add event listener for agent toggle
    const agentCheckbox = document.getElementById('useAgent');
    if (agentCheckbox) {
        agentCheckbox.addEventListener('change', function() {
            updateAgentStatus(this.checked);
        });
    }
}); 