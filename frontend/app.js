const API = '';

// ── Auth ──────────────────────────────────────────────────────────────────────
const { createClient } = supabase;
let _supabase = null;
let _session = null;

async function initAuth() {
    try {
        const configRes = await fetch('/api/config');
        const config = await configRes.json();
        if (!config.supabase_url || !config.supabase_key || config.supabase_url.includes('PLACEHOLDER')) {
            throw new Error("Invalid or unconfigured Supabase credentials.");
        }
        _supabase = createClient(config.supabase_url, config.supabase_key);
        
        const { data } = await _supabase.auth.getSession();
        if (!data || !data.session) {
            window.location.href = '/login';
            return;
        }
        _session = data.session;
        
        // Show user email in sidebar
        const nameEl = document.querySelector('.user-name');
        if (nameEl) nameEl.textContent = _session.user.email.split('@')[0];
    } catch (err) {
        console.error("Auth initialization failed, redirecting to login:", err);
        window.location.href = '/login';
    }
}

function authHeaders() {
    return { 'Authorization': `Bearer ${_session?.access_token || ''}` };
}

async function logout() {
    try {
        if (_supabase) {
            await _supabase.auth.signOut();
        }
    } catch (e) {
        console.error("Supabase signOut error:", e);
    }
    window.location.href = '/login';
}

// DOM Elements
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const docList = document.getElementById('docList');
const docCountBadge = document.getElementById('docCountBadge');
const uploadProgress = document.getElementById('uploadProgress');
const progressBarFill = document.getElementById('progressBarFill');

const newChatBtn = document.getElementById('newChatBtn');
const chatMessages = document.getElementById('chatMessages');
const welcomeScreen = document.getElementById('welcomeScreen');
const suggestionsArea = document.getElementById('suggestions');
const questionInput = document.getElementById('questionInput');
const sendBtn = document.getElementById('sendBtn');
const toastContainer = document.getElementById('toastContainer');

const SUGGESTIONS = [
  "Summarize the key findings from the latest uploads.",
  "List any important deadlines or dates.",
  "Are there any financial metrics mentioned?",
  "What are the main risks identified in the documents?",
];

let isGenerating = false;

// Initialization
document.addEventListener('DOMContentLoaded', async () => {
    await initAuth();
    if (!_session) return;
    loadDocuments();
    renderSuggestions();
});

// Toast Notifications
function showToast(msg, type = 'info') {
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    t.innerHTML = `<span>${type==='error'?'⚠️': type==='success'?'✅':'ℹ️'}</span> ${msg}`;
    toastContainer.appendChild(t);
    setTimeout(() => {
        t.style.opacity = '0';
        setTimeout(() => t.remove(), 300);
    }, 3000);
}

// Sidebar logic
uploadZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', () => {
    if(fileInput.files.length) handleFiles(Array.from(fileInput.files));
    fileInput.value = '';
});

// Drag & Drop
uploadZone.addEventListener('dragover', (e) => { e.preventDefault(); uploadZone.style.borderColor = "var(--accent)"; });
uploadZone.addEventListener('dragleave', () => { uploadZone.style.borderColor = "var(--border)"; });
uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.style.borderColor = "var(--border)";
    if(e.dataTransfer.files.length) handleFiles(Array.from(e.dataTransfer.files));
});

async function handleFiles(files) {
    for (const file of files) {
        uploadProgress.style.display = 'block';
        progressBarFill.style.width = '20%';
        
        try {
            const fd = new FormData();
            fd.append('file', file);

            // Fake progress animation
            let p = 20;
            const intv = setInterval(() => { if(p < 90) { p+=5; progressBarFill.style.width = p+'%'; } }, 200);

            const res = await fetch(`${API}/api/upload`, { method: 'POST', body: fd, headers: authHeaders() });
            const text = await res.text();
            let data;
            try { data = JSON.parse(text); } catch { throw new Error('Backend is waking up. Please wait a moment and try again.'); }
            
            clearInterval(intv);
            progressBarFill.style.width = '100%';
            
            if(!res.ok) throw new Error(data.detail || 'Upload failed');
            
            showToast(`${file.name} uploaded — indexing in progress…`, 'success');
            await loadDocuments();

        } catch (err) {
            const msg = err.message === 'Failed to fetch'
            ? 'Backend is waking up. Please wait ~30 seconds and try again.'
            : `Failed: ${err.message}`;
        showToast(msg, 'error');
        } finally {
            setTimeout(() => { uploadProgress.style.display = 'none'; progressBarFill.style.width = '0'; }, 1000);
        }
    }
}

let _pollTimer = null;

async function loadDocuments() {
    try {
        const res = await fetch(`${API}/api/documents`, { headers: authHeaders() });
        const data = await res.json();
        const docs = data.documents || [];
        const readyDocs = docs.filter(d => d.ready);
        docCountBadge.textContent = readyDocs.length;

        docList.innerHTML = docs.map(d => `
            <div class="doc-item">
                <div class="doc-name">
                    <svg viewBox="0 0 24 24" fill="none"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/></svg>
                    <span>${d.filename}${d.ready ? '' : ' <em style="opacity:0.5;font-size:0.8em">(indexing…)</em>'}</span>
                </div>
                <button class="del-btn" onclick="deleteDoc('${d.doc_id}', '${d.filename.replace(/'/g,"\\'")}')" title="Delete document">
                    <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><polyline points="3,6 5,6 21,6" stroke="currentColor" stroke-width="2"/><path d="M19,6l-1,14H6L5,6" stroke="currentColor" stroke-width="2"/><path d="M10,11v6M14,11v6" stroke="currentColor" stroke-width="2"/></svg>
                </button>
            </div>
        `).join('');

        // If any doc is still indexing, keep polling
        const indexing = docs.some(d => !d.ready);
        if (indexing) {
            if (!_pollTimer) _pollTimer = setInterval(loadDocuments, 4000);
        } else {
            clearInterval(_pollTimer);
            _pollTimer = null;
        }
    } catch (e) {
        console.error("Failed to load documents", e);
    }
}

async function deleteDoc(id, name) {
    if(!confirm(`Remove ${name} from vector store?`)) return;
    try {
        await fetch(`${API}/api/documents/${id}`, { method:'DELETE', headers: authHeaders() });
        showToast(`Removed ${name}`, 'success');
        loadDocuments();
    } catch(e) {
        showToast('Delete failed', 'error');
    }
}

// Chat UI
function renderSuggestions() {
    suggestionsArea.innerHTML = SUGGESTIONS.map(s => 
        `<div class="suggestion-card" onclick="setQuery('${s.replace(/'/g, "\\'")}')">${s}</div>`
    ).join('');
}

function setQuery(text) {
    questionInput.value = text;
    questionInput.focus();
    checkInput();
}

function checkInput() {
    sendBtn.disabled = questionInput.value.trim().length === 0 || isGenerating;
    questionInput.style.height = 'auto';
    questionInput.style.height = Math.min(questionInput.scrollHeight, 200) + 'px';
}

questionInput.addEventListener('input', checkInput);
questionInput.addEventListener('keydown', (e) => {
    if(e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if(!sendBtn.disabled) submitQuery();
    }
});
sendBtn.addEventListener('click', submitQuery);

newChatBtn.addEventListener('click', () => {
    chatMessages.innerHTML = '';
    chatMessages.appendChild(welcomeScreen);
    welcomeScreen.style.display = 'flex';
});

async function submitQuery() {
    const text = questionInput.value.trim();
    if(!text || isGenerating) return;

    // Reset input
    questionInput.value = '';
    checkInput();
    isGenerating = true;

    // Hide welcome
    welcomeScreen.style.display = 'none';

    // Append User Profile
    appendMessageHTML('user', `<div style="white-space: pre-wrap;">${esc(text)}</div>`);
    
    // Append AI Loading
    const aiBoxId = appendAIBox();
    scrollToBottom();

    try {
        const res = await fetch(`${API}/api/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...authHeaders() },
            body: JSON.stringify({ question: text })
        });
        const text2 = await res.text();
        let data;
        try { data = JSON.parse(text2); } catch { throw new Error('Server returned an invalid response. The backend may be starting up — please try again in a moment.'); }
        
        if(!res.ok) throw new Error(data.detail || "Failed to get response");
        
        updateAIBox(aiBoxId, data.answer, data.sources);
    } catch(e) {
        const errMsg = (e.message === 'Failed to fetch')
            ? '**Backend is waking up**\n\nThe server is starting from sleep. Please wait ~30 seconds and try again.'
            : `**Error**\n\n${e.message}`;
        updateAIBox(aiBoxId, errMsg, null, true);
    } finally {
        isGenerating = false;
        checkInput();
        scrollToBottom();
    }
}

// Message Generators
function appendMessageHTML(role, htmlContent) {
    const wrap = document.createElement('div');
    wrap.className = `message-wrapper ${role}`;
    
    if(role === 'user') {
        wrap.innerHTML = `
        <div class="message-inner">
            <div class="message-content">${htmlContent}</div>
        </div>`;
    } else {
        wrap.innerHTML = `
        <div class="message-inner">
            <div class="msg-avatar">
                <svg viewBox="0 0 24 24" fill="none"><path d="M12 2a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2 2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zM4 10a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V10z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </div>
            <div class="message-content markdown-body">${htmlContent}</div>
        </div>`;
    }
    chatMessages.appendChild(wrap);
}

function appendAIBox() {
    const id = 'msg-' + Date.now();
    const wrap = document.createElement('div');
    wrap.className = `message-wrapper ai`;
    wrap.id = id;
    wrap.innerHTML = `
    <div class="message-inner">
        <div class="msg-avatar">
            <svg viewBox="0 0 40 40" fill="none" width="22" height="22">
                <path d="M10 14h20M10 20h14M10 26h17" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/>
                <circle cx="30" cy="26" r="5" fill="#fff"/>
            </svg>
        </div>
        <div class="message-content" id="content-${id}">
            <span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>
        </div>
    </div>`;
    chatMessages.appendChild(wrap);
    return id;
}

function updateAIBox(id, markdown, sources, isError=false) {
    const contentBox = document.getElementById(`content-${id}`);
    if(!contentBox) return;

    if (isError) {
        contentBox.innerHTML = marked.parse(markdown);
        contentBox.style.color = "var(--danger)";
        return;
    }

    // Render marked
    const rendered = marked.parse(markdown);
    
    let sourcesHTML = "";
    if (sources && sources.length) {
        sourcesHTML = `<div class="sources-list">`;
        sources.forEach((s, idx) => {
            sourcesHTML += `
            <div class="source-tag">
                <svg viewBox="0 0 24 24" fill="none" width="12" height="12"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/></svg>
                <span>${esc(s.filename)}</span>
                <div class="source-tooltip"><strong>Source ${idx+1}</strong><br/>"${esc(s.excerpt)}"</div>
            </div>`;
        });
        sourcesHTML += `</div>`;
    }

    contentBox.innerHTML = rendered + sourcesHTML;
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function esc(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
