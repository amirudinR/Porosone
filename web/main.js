const chatContainer = document.getElementById('chat-container');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const statusBadge = document.getElementById('connection-status');

const hitlModal = document.getElementById('hitl-modal');
const hitlModalContent = document.getElementById('hitl-modal-content');
const hitlMessage = document.getElementById('hitl-message');
const btnApprove = document.getElementById('btn-approve');
const btnReject = document.getElementById('btn-reject');

let ws;
let isAgentTyping = false;

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        statusBadge.textContent = 'Online';
        statusBadge.classList.replace('text-gray-500', 'text-green-600');
        statusBadge.classList.replace('bg-gray-100', 'bg-green-50');
        statusBadge.classList.replace('border-gray-300', 'border-green-200');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'agent_message' || data.type === 'agent_log') {
            appendMessage(data.message, 'agent', data.type === 'agent_log');
            isAgentTyping = false;
        }
        else if (data.type === 'hitl_request') {
            showHitlModal(data.message);
        }
        else if (data.type === 'system') {
            appendSystemMessage(data.message);
            isAgentTyping = false;
        }
    };

    ws.onclose = () => {
        statusBadge.textContent = 'Offline';
        statusBadge.classList.replace('text-green-600', 'text-gray-500');
        statusBadge.classList.replace('bg-green-50', 'bg-gray-100');
        statusBadge.classList.replace('border-green-200', 'border-gray-300');
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (err) => {
        console.error("WebSocket Error:", err);
    };
}

function appendMessage(text, sender, isLog = false) {
    const wrapper = document.createElement('div');
    wrapper.className = `flex ${sender === 'user' ? 'justify-end' : 'justify-start'}`;

    const bubble = document.createElement('div');

    if (sender === 'user') {
        bubble.className = 'bg-gray-100 text-gray-800 px-5 py-3 rounded-2xl rounded-tr-none max-w-2xl text-sm leading-relaxed';
        bubble.textContent = text;
    } else {
        // Implementasi textContent yang lebih aman untuk mencegah manipulasi HTML dari LLM
        const safeText = document.createTextNode(text);

        if (isLog) {
            bubble.className = 'bg-transparent text-gray-400 p-2 rounded text-xs font-mono max-w-3xl overflow-x-auto whitespace-pre-wrap';
            bubble.appendChild(safeText);
        } else {
            bubble.className = 'bg-gray-50 text-gray-700 px-5 py-4 rounded-2xl rounded-tl-none max-w-2xl text-sm leading-relaxed border border-gray-100';
            bubble.appendChild(safeText);
        }
    }

    wrapper.appendChild(bubble);
    chatContainer.appendChild(wrapper);
    scrollToBottom();
}

function appendSystemMessage(text) {
    const wrapper = document.createElement('div');
    wrapper.className = 'flex justify-center my-6';
    const badge = document.createElement('div');
    badge.className = 'text-gray-400 text-[10px] font-medium uppercase tracking-[0.2em]';
    badge.textContent = text;
    wrapper.appendChild(badge);
    chatContainer.appendChild(wrapper);
    scrollToBottom();
}

function scrollToBottom() {
    chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: 'smooth'
    });
}

function showHitlModal(message) {
    hitlMessage.textContent = message;

    hitlModal.classList.remove('hidden');

    hitlModal.style.display = 'flex';
    hitlModal.style.opacity = '1';
    hitlModal.style.visibility = 'visible';

    hitlModalContent.style.display = 'block';
    hitlModalContent.style.opacity = '1';
    hitlModalContent.style.visibility = 'visible';
    hitlModalContent.style.transform = 'scale(1)';

    void hitlModal.offsetWidth;
    hitlModal.classList.replace('opacity-0', 'opacity-100');
    hitlModalContent.classList.replace('scale-95', 'scale-100');
}

function hideHitlModal() {
    hitlModal.classList.replace('opacity-100', 'opacity-0');
    hitlModalContent.classList.replace('scale-100', 'scale-95');
    setTimeout(() => {
        hitlModal.style.display = 'none';
    }, 300);
}

chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text || isAgentTyping || ws.readyState !== WebSocket.OPEN) return;

    appendMessage(text, 'user');
    ws.send(JSON.stringify({ type: 'user_prompt', message: text }));

    chatInput.value = '';
    isAgentTyping = true;
});

btnApprove.addEventListener('click', () => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'hitl_response', status: 'approved' }));
        appendSystemMessage("Otorisasi: Disetujui");
        hideHitlModal();
    }
});

btnReject.addEventListener('click', () => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'hitl_response', status: 'rejected' }));
        appendSystemMessage("Otorisasi: Ditolak");
        hideHitlModal();
    }
});

connectWebSocket();
