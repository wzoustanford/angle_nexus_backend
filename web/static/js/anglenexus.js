// AngleNexus JavaScript - Agent Chat Functionality

// Configuration
const API_BASE_URL = '/api/chat';

// Daimon Agent State
let daimonOpen = false;

// Avvocato Agent State
let avvocatoOpen = false;

// Weaver Agent State
let weaverOpen = false;

// LocalStorage keys
const WEAVER_STORAGE_KEY = 'weaver_chat_history';
const MAX_STORED_MESSAGES = 200; // Limit storage size

/**
 * Load Weaver chat history from LocalStorage
 */
function loadWeaverHistory() {
    try {
        const stored = localStorage.getItem(WEAVER_STORAGE_KEY);
        if (!stored) return [];
        
        const messages = JSON.parse(stored);
        return Array.isArray(messages) ? messages : [];
    } catch (e) {
        console.error('Error loading Weaver history:', e);
        return [];
    }
}

/**
 * Save Weaver chat history to LocalStorage
 */
function saveWeaverHistory(messages) {
    try {
        // Keep only the last MAX_STORED_MESSAGES
        const toStore = messages.slice(-MAX_STORED_MESSAGES);
        localStorage.setItem(WEAVER_STORAGE_KEY, JSON.stringify(toStore));
    } catch (e) {
        console.error('Error saving Weaver history:', e);
        // If storage is full, try clearing old messages
        if (e.name === 'QuotaExceededError') {
            try {
                const reducedMessages = messages.slice(-50);
                localStorage.setItem(WEAVER_STORAGE_KEY, JSON.stringify(reducedMessages));
            } catch (e2) {
                console.error('Still failed after reducing messages:', e2);
            }
        }
    }
}

/**
 * Clear Weaver chat history
 */
function clearWeaverHistory() {
    try {
        localStorage.removeItem(WEAVER_STORAGE_KEY);
        const msgs = document.getElementById('weaverMsgs');
        msgs.innerHTML = `
            <div class="w-welcome">
                <h4>🕸️ Weaver Intelligence</h4>
                <p>I gather and synthesize information from multiple sources. Ask me to research companies, analyze market data, or compile comprehensive reports.</p>
            </div>
        `;
    } catch (e) {
        console.error('Error clearing Weaver history:', e);
    }
}

/**
 * Restore Weaver chat messages from history
 */
function restoreWeaverMessages() {
    const msgs = document.getElementById('weaverMsgs');
    const history = loadWeaverHistory();
    
    if (history.length === 0) return;
    
    // Clear welcome message
    const welcome = msgs.querySelector('.w-welcome');
    if (welcome) welcome.remove();
    
    // Restore each message
    history.forEach(msg => {
        const msgDiv = document.createElement('div');
        msgDiv.className = `w-msg ${msg.role}`;
        msgDiv.innerHTML = `<div class="w-msg-content">${escapeHtml(msg.content)}</div>`;
        msgs.appendChild(msgDiv);
    });
    
    msgs.scrollTop = msgs.scrollHeight;
}

/**
 * Toggle Daimon chat window
 */
function toggleDaimon() {
    const box = document.getElementById('daimonBox');
    const arr = document.getElementById('daimonArr');
    
    daimonOpen = !daimonOpen;
    
    if (daimonOpen) {
        box.classList.add('show');
        arr.classList.add('rot');
        // Focus input when opened
        setTimeout(() => {
            document.getElementById('daimonIn').focus();
        }, 300);
    } else {
        box.classList.remove('show');
        arr.classList.remove('rot');
    }
}

/**
 * Send message to Daimon agent
 */
async function sendDaimon() {
    const input = document.getElementById('daimonIn');
    const msgs = document.getElementById('daimonMsgs');
    const sendBtn = document.getElementById('daimonSnd');
    
    const text = input.value.trim();
    if (!text) return;
    
    // Clear welcome message if it exists
    const welcome = msgs.querySelector('.d-welcome');
    if (welcome) welcome.remove();
    
    // Add user message
    const uMsg = document.createElement('div');
    uMsg.className = 'd-msg user';
    uMsg.innerHTML = `<div class="d-msg-content">${escapeHtml(text)}</div>`;
    msgs.appendChild(uMsg);
    
    input.value = '';
    input.disabled = true;
    sendBtn.disabled = true;
    
    // Add loading indicator
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'd-msg assistant loading-msg';
    loadingMsg.innerHTML = '<div class="d-msg-content"><div class="loading-ring"></div> Analyzing...</div>';
    msgs.appendChild(loadingMsg);
    msgs.scrollTop = msgs.scrollHeight;
    
    try {
        const response = await fetch(`${API_BASE_URL}/daimon`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                message: text,
                model_name: 'o3-mini'
            })
        });
        
        // Remove loading indicator
        loadingMsg.remove();
        
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }
        
        const data = await response.json();
        
        // Add assistant response
        const aMsg = document.createElement('div');
        aMsg.className = 'd-msg assistant';
        aMsg.innerHTML = `<div class="d-msg-content">${escapeHtml(data.message || 'No response received')}</div>`;
        msgs.appendChild(aMsg);
        
    } catch (e) {
        console.error('Daimon error:', e);
        loadingMsg.remove();
        
        const errMsg = document.createElement('div');
        errMsg.className = 'd-msg assistant';
        errMsg.innerHTML = '<div class="d-msg-content">Sorry, I encountered an error. Please try again.</div>';
        msgs.appendChild(errMsg);
    }
    
    input.disabled = false;
    sendBtn.disabled = false;
    input.focus();
    msgs.scrollTop = msgs.scrollHeight;
}

/**
 * Toggle Avvocato chat window
 */
function toggleAvvocato() {
    const box = document.getElementById('avvocatoBox');
    const arr = document.getElementById('avvocatoArr');
    
    avvocatoOpen = !avvocatoOpen;
    
    if (avvocatoOpen) {
        box.classList.add('show');
        arr.classList.add('rot');
        // Focus input when opened
        setTimeout(() => {
            document.getElementById('avvocatoIn').focus();
        }, 300);
    } else {
        box.classList.remove('show');
        arr.classList.remove('rot');
    }
}

/**
 * Toggle Weaver chat window
 */
function toggleWeaver() {
    const box = document.getElementById('weaverBox');
    const arr = document.getElementById('weaverArr');
    
    weaverOpen = !weaverOpen;
    
    if (weaverOpen) {
        box.classList.add('show');
        arr.classList.add('rot');
        
        // Restore chat history on first open
        const msgs = document.getElementById('weaverMsgs');
        const hasMessages = msgs.querySelector('.w-msg');
        if (!hasMessages) {
            restoreWeaverMessages();
        }
        
        // Focus input when opened
        setTimeout(() => {
            document.getElementById('weaverIn').focus();
        }, 300);
    } else {
        box.classList.remove('show');
        arr.classList.remove('rot');
    }
}

/**
 * Send message to Avvocato agent
 */
async function sendAvvocato() {
    const input = document.getElementById('avvocatoIn');
    const msgs = document.getElementById('avvocatoMsgs');
    const sendBtn = document.getElementById('avvocatoSnd');
    
    const text = input.value.trim();
    if (!text) return;
    
    // Clear welcome message if it exists
    const welcome = msgs.querySelector('.a-welcome');
    if (welcome) welcome.remove();
    
    // Add user message
    const uMsg = document.createElement('div');
    uMsg.className = 'a-msg user';
    uMsg.innerHTML = `<div class="a-msg-content">${escapeHtml(text)}</div>`;
    msgs.appendChild(uMsg);
    
    input.value = '';
    input.disabled = true;
    sendBtn.disabled = true;
    
    // Add loading indicator
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'a-msg assistant loading-msg';
    loadingMsg.innerHTML = '<div class="a-msg-content"><div class="loading-ring"></div> Consulting legal references...</div>';
    msgs.appendChild(loadingMsg);
    msgs.scrollTop = msgs.scrollHeight;
    
    try {
        const response = await fetch(`${API_BASE_URL}/avvocato`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                message: text,
                model_name: 'o3-mini'
            })
        });
        
        // Remove loading indicator
        loadingMsg.remove();
        
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }
        
        const data = await response.json();
        
        // Add assistant response
        const aMsg = document.createElement('div');
        aMsg.className = 'a-msg assistant';
        aMsg.innerHTML = `<div class="a-msg-content">${escapeHtml(data.message || 'No response received')}</div>`;
        msgs.appendChild(aMsg);
        
    } catch (e) {
        console.error('Avvocato error:', e);
        loadingMsg.remove();
        
        const errMsg = document.createElement('div');
        errMsg.className = 'a-msg assistant';
        errMsg.innerHTML = '<div class="a-msg-content">Sorry, I encountered an error. Please try again.</div>';
        msgs.appendChild(errMsg);
    }
    
    input.disabled = false;
    sendBtn.disabled = false;
    input.focus();
    msgs.scrollTop = msgs.scrollHeight;
}

/**
 * Send message to Weaver agent
 */
async function sendWeaver() {
    const input = document.getElementById('weaverIn');
    const msgs = document.getElementById('weaverMsgs');
    const sendBtn = document.getElementById('weaverSnd');
    
    const text = input.value.trim();
    if (!text) return;
    
    // Load existing history
    const history = loadWeaverHistory();
    
    // Clear welcome message if it exists
    const welcome = msgs.querySelector('.w-welcome');
    if (welcome) welcome.remove();
    
    // Add user message
    const uMsg = document.createElement('div');
    uMsg.className = 'w-msg user';
    uMsg.innerHTML = `<div class="w-msg-content">${escapeHtml(text)}</div>`;
    msgs.appendChild(uMsg);
    
    // Save user message to history
    history.push({
        role: 'user',
        content: text,
        timestamp: new Date().toISOString()
    });
    saveWeaverHistory(history);
    
    input.value = '';
    input.disabled = true;
    sendBtn.disabled = true;
    
    // Add loading indicator
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'w-msg assistant loading-msg';
    loadingMsg.innerHTML = '<div class="w-msg-content"><div class="loading-ring"></div> Gathering information...</div>';
    msgs.appendChild(loadingMsg);
    msgs.scrollTop = msgs.scrollHeight;
    
    try {
        // Weaver uses the /chat endpoint with /weaver prefix
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                message: `/weaver ${text}`,
                model_name: 'o3-mini'
            })
        });
        
        // Remove loading indicator
        loadingMsg.remove();
        
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }
        
        const data = await response.json();
        const responseText = data.message || 'No response received';
        
        // Add assistant response
        const aMsg = document.createElement('div');
        aMsg.className = 'w-msg assistant';
        aMsg.innerHTML = `<div class="w-msg-content">${escapeHtml(responseText)}</div>`;
        msgs.appendChild(aMsg);
        
        // Save assistant message to history
        history.push({
            role: 'assistant',
            content: responseText,
            timestamp: new Date().toISOString()
        });
        saveWeaverHistory(history);
        
    } catch (e) {
        console.error('Weaver error:', e);
        loadingMsg.remove();
        
        const errorText = 'Sorry, I encountered an error. Please try again.';
        const errMsg = document.createElement('div');
        errMsg.className = 'w-msg assistant';
        errMsg.innerHTML = `<div class="w-msg-content">${errorText}</div>`;
        msgs.appendChild(errMsg);
        
        // Save error message to history
        history.push({
            role: 'assistant',
            content: errorText,
            timestamp: new Date().toISOString()
        });
        saveWeaverHistory(history);
    }
    
    input.disabled = false;
    sendBtn.disabled = false;
    input.focus();
    msgs.scrollTop = msgs.scrollHeight;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Initialize on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    // Navbar scroll effect
    window.addEventListener('scroll', function() {
        const navbar = document.getElementById('navbar');
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
    
    // Smooth scroll for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Enter key support for chat inputs
    document.getElementById('daimonIn').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendDaimon();
    });
    
    document.getElementById('avvocatoIn').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendAvvocato();
    });
    
    document.getElementById('weaverIn').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendWeaver();
    });
    
    console.log('AngleNexus initialized successfully');
    console.log('Agents: Daimon ✓, Avvocato ✓, Weaver ✓, Sophon (coming soon)');
});
