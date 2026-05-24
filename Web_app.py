from flask import Flask, render_template_string, request, jsonify, session, send_file
import os
import json
import uuid
from datetime import datetime
from ai import AdvancedGroqChat, ModelType, Colors
import threading

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for sessions

# Global chat instance (single user mode)
# Your API key is already in ai.py, but let's make sure
API_KEY = "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"
chat_instance = None

def get_chat():
    global chat_instance
    if chat_instance is None:
        chat_instance = AdvancedGroqChat(api_key=API_KEY)
    return chat_instance

# HTML template with modern design
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>AI Chatbot - Groq Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }

        /* Mobile-first container */
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 16px;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        /* Header with sidebar toggle for mobile */
        .header {
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 12px 20px;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .logo-icon {
            font-size: 28px;
        }

        .logo-text {
            font-weight: 700;
            font-size: 1.2rem;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        .menu-btn {
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            padding: 8px;
            border-radius: 50%;
            transition: background 0.2s;
        }

        .menu-btn:hover {
            background: rgba(0,0,0,0.05);
        }

        /* Sidebar (hidden on mobile by default) */
        .sidebar {
            position: fixed;
            top: 0;
            left: -280px;
            width: 280px;
            height: 100%;
            background: white;
            box-shadow: 2px 0 20px rgba(0,0,0,0.1);
            transition: left 0.3s ease;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }

        .sidebar.open {
            left: 0;
        }

        .sidebar-header {
            padding: 20px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .close-sidebar {
            background: none;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
        }

        .sidebar-content {
            padding: 16px;
            flex: 1;
        }

        .conv-list {
            list-style: none;
        }

        .conv-item {
            padding: 12px;
            margin-bottom: 8px;
            background: #f8f9fa;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .conv-item:hover {
            background: #e9ecef;
        }

        .conv-item.active {
            background: linear-gradient(135deg, #667eea20, #764ba220);
            border-left: 3px solid #667eea;
        }

        .conv-name {
            flex: 1;
            font-size: 0.9rem;
            word-break: break-word;
        }

        .conv-actions {
            display: flex;
            gap: 8px;
        }

        .conv-actions button {
            background: none;
            border: none;
            cursor: pointer;
            font-size: 16px;
            opacity: 0.6;
        }

        .new-conv-btn {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 20px;
        }

        /* Main chat area */
        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: rgba(255,255,255,0.92);
            border-radius: 24px;
            overflow: hidden;
            box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        }

        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        /* Message bubbles */
        .message {
            display: flex;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message.user {
            justify-content: flex-end;
        }

        .message.assistant {
            justify-content: flex-start;
        }

        .bubble {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 20px;
            line-height: 1.4;
            word-wrap: break-word;
        }

        .user .bubble {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border-bottom-right-radius: 4px;
        }

        .assistant .bubble {
            background: #f1f3f5;
            color: #333;
            border-bottom-left-radius: 4px;
        }

        .message-time {
            font-size: 0.7rem;
            margin-top: 4px;
            opacity: 0.6;
        }

        /* Input area */
        .input-area {
            padding: 16px;
            background: white;
            border-top: 1px solid #e9ecef;
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }

        .input-wrapper {
            flex: 1;
            position: relative;
        }

        textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid #e9ecef;
            border-radius: 24px;
            font-family: inherit;
            font-size: 1rem;
            resize: none;
            outline: none;
            transition: border 0.2s;
        }

        textarea:focus {
            border-color: #667eea;
        }

        button {
            background: none;
            border: none;
            cursor: pointer;
        }

        .send-btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            transition: transform 0.2s;
        }

        .send-btn:hover {
            transform: scale(1.05);
        }

        /* Control bar */
        .controls {
            background: rgba(255,255,255,0.9);
            border-radius: 16px;
            padding: 10px 16px;
            margin-top: 12px;
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            font-size: 0.85rem;
        }

        .control-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        select, input {
            padding: 6px 12px;
            border-radius: 20px;
            border: 1px solid #ddd;
            font-size: 0.85rem;
        }

        .export-btn {
            background: #28a745;
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
        }

        /* Loading indicator */
        .typing-indicator {
            background: #f1f3f5;
            border-radius: 20px;
            padding: 12px 16px;
            display: inline-flex;
            gap: 4px;
        }

        .typing-indicator span {
            width: 8px;
            height: 8px;
            background: #999;
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out;
        }

        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes bounce {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }

        /* Overlay for sidebar on mobile */
        .overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 999;
            display: none;
        }

        .overlay.active {
            display: block;
        }

        /* Desktop adjustments */
        @media (min-width: 768px) {
            .sidebar {
                position: relative;
                left: 0;
                width: 300px;
                box-shadow: none;
                background: white;
                border-radius: 24px;
                margin-right: 16px;
                height: auto;
            }
            .container {
                flex-direction: row;
            }
            .menu-btn {
                display: none;
            }
            .close-sidebar {
                display: none;
            }
            .overlay {
                display: none !important;
            }
            .chat-area {
                flex: 1;
            }
        }
    </style>
</head>
<body>
    <div class="overlay" id="overlay"></div>
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <span>Conversations</span>
            <button class="close-sidebar" id="closeSidebarBtn">✕</button>
        </div>
        <div class="sidebar-content">
            <button class="new-conv-btn" id="newConvBtn">+ New Conversation</button>
            <ul class="conv-list" id="convList">
                <li>Loading...</li>
            </ul>
        </div>
    </div>

    <div class="container">
        <div class="header">
            <div class="logo">
                <span class="logo-icon">🤖</span>
                <span class="logo-text">AI Assistant</span>
            </div>
            <button class="menu-btn" id="menuBtn">☰</button>
        </div>

        <div class="chat-area">
            <div class="messages-container" id="messagesContainer">
                <div class="message assistant">
                    <div class="bubble">Hello! I'm your AI assistant. How can I help you today?</div>
                </div>
            </div>

            <div class="input-area">
                <div class="input-wrapper">
                    <textarea id="messageInput" placeholder="Type your message..." rows="1"></textarea>
                </div>
                <button class="send-btn" id="sendBtn">➤</button>
            </div>

            <div class="controls">
                <div class="control-group">
                    <span>🤖 Model:</span>
                    <select id="modelSelect">
                        <option value="llama-3.1-8b-instant">Llama 3.1 8B</option>
                        <option value="llama-3.1-70b-versatile">Llama 3.1 70B</option>
                        <option value="mixtral-8x7b-32768">Mixtral 8x7B</option>
                        <option value="gemma2-9b-it">Gemma 2 9B</option>
                    </select>
                </div>
                <div class="control-group">
                    <span>🌡️ Temp:</span>
                    <input type="range" id="tempSlider" min="0" max="1" step="0.1" value="0.7">
                    <span id="tempValue">0.7</span>
                </div>
                <div class="control-group">
                    <button class="export-btn" id="exportBtn">📎 Export</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // State
        let activeConvId = null;
        let conversations = {};
        let isLoading = false;

        // DOM elements
        const messagesContainer = document.getElementById('messagesContainer');
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        const convList = document.getElementById('convList');
        const menuBtn = document.getElementById('menuBtn');
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('overlay');
        const closeSidebarBtn = document.getElementById('closeSidebarBtn');
        const newConvBtn = document.getElementById('newConvBtn');
        const modelSelect = document.getElementById('modelSelect');
        const tempSlider = document.getElementById('tempSlider');
        const tempValue = document.getElementById('tempValue');
        const exportBtn = document.getElementById('exportBtn');

        // Load conversations from server
        async function loadConversations() {
            try {
                const res = await fetch('/api/conversations');
                const data = await res.json();
                conversations = data.conversations;
                activeConvId = data.active_id;
                renderConversationList();
                if (activeConvId && conversations[activeConvId]) {
                    renderMessages(conversations[activeConvId].messages);
                }
            } catch (err) {
                console.error('Failed to load conversations:', err);
            }
        }

        function renderConversationList() {
            convList.innerHTML = '';
            for (const [id, conv] of Object.entries(conversations)) {
                const li = document.createElement('li');
                li.className = 'conv-item';
                if (id === activeConvId) li.classList.add('active');
                li.innerHTML = `
                    <span class="conv-name">${escapeHtml(conv.name)}</span>
                    <div class="conv-actions">
                        <button onclick="renameConv('${id}')" title="Rename">✏️</button>
                        <button onclick="deleteConv('${id}')" title="Delete">🗑️</button>
                    </div>
                `;
                li.addEventListener('click', (e) => {
                    if (e.target.tagName !== 'BUTTON') switchConv(id);
                });
                convList.appendChild(li);
            }
            if (Object.keys(conversations).length === 0) {
                convList.innerHTML = '<li style="padding:12px;text-align:center;">No conversations</li>';
            }
        }

        function renderMessages(messages) {
            messagesContainer.innerHTML = '';
            for (const msg of messages) {
                if (msg.role === 'system') continue;
                addMessageToUI(msg.role, msg.content, false);
            }
            scrollToBottom();
        }

        function addMessageToUI(role, content, saveToServer = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            const time = new Date().toLocaleTimeString();
            messageDiv.innerHTML = `
                <div class="bubble">
                    ${escapeHtml(content)}
                    <div class="message-time">${time}</div>
                </div>
            `;
            messagesContainer.appendChild(messageDiv);
            scrollToBottom();
        }

        function showTypingIndicator() {
            const indicator = document.createElement('div');
            indicator.className = 'message assistant';
            indicator.id = 'typingIndicator';
            indicator.innerHTML = `
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            `;
            messagesContainer.appendChild(indicator);
            scrollToBottom();
        }

        function hideTypingIndicator() {
            const indicator = document.getElementById('typingIndicator');
            if (indicator) indicator.remove();
        }

        function scrollToBottom() {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        async function sendMessage() {
            if (isLoading) return;
            const content = messageInput.value.trim();
            if (!content) return;

            messageInput.value = '';
            addMessageToUI('user', content, false);
            isLoading = true;
            showTypingIndicator();

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: content,
                        model: modelSelect.value,
                        temperature: parseFloat(tempSlider.value)
                    })
                });
                const data = await res.json();
                hideTypingIndicator();
                if (data.reply) {
                    addMessageToUI('assistant', data.reply, false);
                    // Update active conversation messages
                    if (activeConvId && conversations[activeConvId]) {
                        conversations[activeConvId].messages.push(
                            { role: 'user', content: content },
                            { role: 'assistant', content: data.reply }
                        );
                    }
                } else if (data.error) {
                    addMessageToUI('assistant', 'Error: ' + data.error, false);
                }
            } catch (err) {
                hideTypingIndicator();
                addMessageToUI('assistant', 'Network error. Please try again.', false);
            } finally {
                isLoading = false;
                // Reload conversations to update any changes (like trimming)
                loadConversations();
            }
        }

        async function switchConv(convId) {
            try {
                const res = await fetch('/api/conversations/switch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ conv_id: convId })
                });
                const data = await res.json();
                if (data.success) {
                    activeConvId = convId;
                    loadConversations();
                    // Close sidebar on mobile
                    sidebar.classList.remove('open');
                    overlay.classList.remove('active');
                }
            } catch (err) {
                console.error(err);
            }
        }

        async function newConversation() {
            const name = prompt('Conversation name:', new Date().toLocaleString());
            try {
                const res = await fetch('/api/conversations', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name || 'New Chat' })
                });
                const data = await res.json();
                if (data.conv_id) {
                    activeConvId = data.conv_id;
                    loadConversations();
                }
            } catch (err) {
                console.error(err);
            }
        }

        async function renameConv(convId) {
            const newName = prompt('New name:', conversations[convId]?.name);
            if (!newName) return;
            try {
                await fetch(`/api/conversations/${convId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: newName })
                });
                loadConversations();
            } catch (err) {
                console.error(err);
            }
        }

        async function deleteConv(convId) {
            if (!confirm('Delete this conversation?')) return;
            try {
                await fetch(`/api/conversations/${convId}`, { method: 'DELETE' });
                if (activeConvId === convId) activeConvId = null;
                loadConversations();
            } catch (err) {
                console.error(err);
            }
        }

        async function exportConversation() {
            if (!activeConvId) {
                alert('No active conversation');
                return;
            }
            window.open(`/api/export/${activeConvId}?format=txt`, '_blank');
        }

        // Event listeners
        sendBtn.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        menuBtn.addEventListener('click', () => {
            sidebar.classList.add('open');
            overlay.classList.add('active');
        });
        closeSidebarBtn.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        });
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        });
        newConvBtn.addEventListener('click', newConversation);
        tempSlider.addEventListener('input', () => {
            tempValue.textContent = tempSlider.value;
        });
        exportBtn.addEventListener('click', exportConversation);

        // Auto-resize textarea
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });

        // Initial load
        loadConversations();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/conversations')
def get_conversations():
    chat = get_chat()
    convs = {}
    for cid, conv in chat.conversations.items():
        convs[cid] = {
            "id": conv.id,
            "name": conv.name,
            "messages": [{"role": m.role, "content": m.content} for m in conv.messages],
            "created_at": conv.created_at.isoformat()
        }
    return jsonify({
        "conversations": convs,
        "active_id": chat.active_conversation_id
    })

@app.route('/api/conversations', methods=['POST'])
def create_conversation():
    chat = get_chat()
    data = request.json
    name = data.get('name', 'New Chat')
    conv_id = chat.create_conversation(name)
    return jsonify({"success": True, "conv_id": conv_id})

@app.route('/api/conversations/<conv_id>', methods=['PUT'])
def rename_conversation(conv_id):
    chat = get_chat()
    data = request.json
    chat.rename_conversation(conv_id, data['name'])
    return jsonify({"success": True})

@app.route('/api/conversations/<conv_id>', methods=['DELETE'])
def delete_conversation(conv_id):
    chat = get_chat()
    chat.delete_conversation(conv_id)
    return jsonify({"success": True})

@app.route('/api/conversations/switch', methods=['POST'])
def switch_conversation():
    chat = get_chat()
    data = request.json
    chat.switch_conversation(data['conv_id'])
    return jsonify({"success": True})

@app.route('/api/chat', methods=['POST'])
def chat():
    chat = get_chat()
    data = request.json
    user_message = data.get('message', '')
    model_name = data.get('model', 'llama-3.1-8b-instant')
    temperature = data.get('temperature', 0.7)
    
    # Map model name to ModelType
    model_map = {
        'llama-3.1-8b-instant': ModelType.LLAMA_31_8B,
        'llama-3.1-70b-versatile': ModelType.LLAMA_31_70B,
        'llama3-8b-8192': ModelType.LLAMA_3_8B,
        'llama3-70b-8192': ModelType.LLAMA_3_70B,
        'mixtral-8x7b-32768': ModelType.MIXTRAL_8x7B,
        'gemma2-9b-it': ModelType.GEMMA_2_9B
    }
    model = model_map.get(model_name, ModelType.LLAMA_31_8B)
    
    reply = chat.send_message(user_message, model=model, temperature=temperature)
    if reply is None:
        return jsonify({"error": "Failed to get response"}), 500
    return jsonify({"reply": reply})

@app.route('/api/export/<conv_id>')
def export_conversation(conv_id):
    chat = get_chat()
    format_type = request.args.get('format', 'txt')
    filename = chat.export_conversation(conv_id, format=format_type)
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    print("=" * 50)
    print("🤖 AI Chatbot Web Server Starting...")
    print("📱 Open on your computer: http://localhost:5000")
    print("📱 To access from phone: Find your computer's IP address and use http://YOUR_IP:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=8000, debug=True)