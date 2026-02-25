// ===== 全局状态 =====
const API_BASE = '';
let isProcessing = false;

// ===== DOM 引用 =====
const chatMessages = document.getElementById('chat-messages');
const chatInput    = document.getElementById('chat-input');
const sendBtn      = document.getElementById('send-btn');
const resetBtn     = document.getElementById('reset-btn');

// ===== 通知 =====
const NOTIF_ICONS = {
    success: 'fa-circle-check',
    error:   'fa-circle-exclamation',
    info:    'fa-circle-info',
};

function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    const el = document.createElement('div');
    el.className = `notification ${type}`;
    el.innerHTML = `<i class="fas ${NOTIF_ICONS[type] || NOTIF_ICONS.info}"></i><span>${message}</span>`;
    container.appendChild(el);

    setTimeout(() => {
        el.style.transition = 'opacity 0.28s, transform 0.28s';
        el.style.opacity    = '0';
        el.style.transform  = 'translateX(20px)';
        setTimeout(() => el.remove(), 280);
    }, 3000);
}

// ===== 消息渲染 =====
function renderMarkdown(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/```([\s\S]*?)```/g, (_, code) => `<pre>${code}</pre>`)
        .replace(/`([^`\n]+)`/g, '<code>$1</code>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
}

function addMessage(content, type = 'assistant', images = []) {
    const row = document.createElement('div');
    row.className = `message ${type}-message`;

    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.innerHTML = `<i class="fas ${type === 'user' ? 'fa-user' : 'fa-robot'}"></i>`;

    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.innerHTML = renderMarkdown(content);

    if (images && images.length > 0) {
        const imgWrap = document.createElement('div');
        imgWrap.className = 'message-images';
        images.forEach(src => {
            const img = document.createElement('img');
            img.src     = src;
            img.alt     = '分析图表';
            img.loading = 'lazy';
            img.addEventListener('click', () => openImageModal(src));
            img.onerror = () => {
                imgWrap.innerHTML = '<p style="color:var(--text-3);font-size:13px;margin-top:8px;">图片加载失败</p>';
            };
            imgWrap.appendChild(img);
        });
        bubble.appendChild(imgWrap);
    }

    row.appendChild(avatar);
    row.appendChild(bubble);
    chatMessages.appendChild(row);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ===== 打字指示器 =====
function showTyping() {
    const row = document.createElement('div');
    row.className = 'message assistant-message typing-indicator';
    row.id = 'typing-indicator';
    row.innerHTML = `
        <div class="avatar"><i class="fas fa-robot"></i></div>
        <div class="bubble">
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
        </div>`;
    chatMessages.appendChild(row);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTyping() {
    document.getElementById('typing-indicator')?.remove();
}

// ===== 图片放大 =====
function openImageModal(src) {
    const overlay = document.createElement('div');
    overlay.style.cssText = [
        'position:fixed', 'inset:0',
        'background:rgba(0,0,0,0.82)',
        'display:flex', 'align-items:center', 'justify-content:center',
        'z-index:10000', 'cursor:zoom-out',
        'animation:fadeIn 0.2s ease',
    ].join(';');

    const img = document.createElement('img');
    img.src = src;
    img.style.cssText = 'max-width:92%;max-height:92%;object-fit:contain;border-radius:12px;box-shadow:0 20px 60px rgba(0,0,0,0.5)';

    overlay.appendChild(img);
    document.body.appendChild(overlay);
    overlay.addEventListener('click', () => overlay.remove());

    const onEsc = e => {
        if (e.key === 'Escape') {
            overlay.remove();
            document.removeEventListener('keydown', onEsc);
        }
    };
    document.addEventListener('keydown', onEsc);
}

// ===== 欢迎卡片工厂 =====
function buildWelcomeCard(subtitle = '您可以用自然语言查询和分析束流数据，例如：') {
    const div = document.createElement('div');
    div.className = 'welcome-card';
    div.innerHTML = `
        <div class="welcome-icon"><i class="fas fa-atom"></i></div>
        <h2>束流数据分析助手</h2>
        <p>${subtitle}</p>
        <div class="welcome-chips">
            <span class="chip">查询8月31日两点到三点的束流数据</span>
            <span class="chip">检测该时段是否存在异常</span>
            <span class="chip">用SHAP方法诊断异常特征</span>
            <span class="chip">feature6 是什么意思？</span>
        </div>`;
    return div;
}

// ===== 点击示例 chip 填入输入框（事件委托） =====
chatMessages.addEventListener('click', e => {
    const chip = e.target.closest('.chip');
    if (!chip) return;
    chatInput.value = chip.textContent.trim();
    chatInput.focus();
    chatInput.dispatchEvent(new Event('input'));
});

// ===== 工具步骤块 =====

/**
 * 在消息区追加一个工具步骤块，返回 { row, stepsBody, stepMap }
 * stepMap: tool_name -> step DOM element
 */
function createStepsBlock() {
    const row = document.createElement('div');
    row.className = 'message assistant-message';

    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.innerHTML = '<i class="fas fa-robot"></i>';

    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.style.padding = '0';
    bubble.style.background = 'transparent';
    bubble.style.boxShadow = 'none';

    const block = document.createElement('div');
    block.className = 'tool-steps';

    const header = document.createElement('div');
    header.className = 'tool-steps-header';
    header.innerHTML = `
        <span class="steps-icon">⚙️</span>
        <span class="steps-label">正在调用工具…</span>
        <span class="steps-toggle">▼</span>`;

    const body = document.createElement('div');
    body.className = 'tool-steps-body';

    header.addEventListener('click', () => block.classList.toggle('collapsed'));

    block.appendChild(header);
    block.appendChild(body);
    bubble.appendChild(block);
    row.appendChild(avatar);
    row.appendChild(bubble);
    chatMessages.appendChild(row);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return { row, block, header, stepsBody: body, stepMap: {} };
}

function addStepItem(stepsBody, stepMap, toolName) {
    const item = document.createElement('div');
    item.className = 'step-item';
    item.innerHTML = `
        <div class="step-dot running"></div>
        <div class="step-body">
            <div class="step-name">${toolName}</div>
            <div class="step-summary">运行中…</div>
        </div>
        <div class="step-duration"></div>`;
    stepsBody.appendChild(item);
    stepMap[toolName] = item;
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function resolveStepItem(stepMap, toolName, type, payload) {
    const item = stepMap[toolName];
    if (!item) return;
    const dot     = item.querySelector('.step-dot');
    const summary = item.querySelector('.step-summary');
    const dur     = item.querySelector('.step-duration');

    dot.classList.remove('running');
    if (type === 'done') {
        dot.classList.add('done');
        summary.textContent = payload.summary || '';
        if (payload.duration_ms != null) {
            dur.textContent = `${(payload.duration_ms / 1000).toFixed(2)}s`;
        }
    } else {
        dot.classList.add('error');
        summary.className = 'step-error';
        summary.textContent = payload.error || '执行失败';
    }
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ===== 发送消息（SSE 流式版本） =====
function sendMessage() {
    const message = chatInput.value.trim();
    if (!message || isProcessing) return;

    document.querySelector('.welcome-card')?.remove();

    addMessage(message, 'user');
    chatInput.value = '';
    chatInput.style.height = 'auto';

    isProcessing = true;
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    showTyping();

    let stepsCtx = null;   // 工具步骤块上下文

    const url = `${API_BASE}/api/chat/stream?message=${encodeURIComponent(message)}`;
    const es   = new EventSource(url);

    es.onmessage = (e) => {
        if (e.data === '[DONE]') {
            es.close();
            done();
            return;
        }

        let event;
        try { event = JSON.parse(e.data); } catch { return; }

        if (event.type === 'tool_start') {
            hideTyping();
            if (!stepsCtx) stepsCtx = createStepsBlock();
            addStepItem(stepsCtx.stepsBody, stepsCtx.stepMap, event.tool);

        } else if (event.type === 'tool_done') {
            if (stepsCtx) resolveStepItem(stepsCtx.stepMap, event.tool, 'done', event);

        } else if (event.type === 'tool_error') {
            if (stepsCtx) resolveStepItem(stepsCtx.stepMap, event.tool, 'error', event);

        } else if (event.type === 'answer') {
            es.close();
            hideTyping();

            // 折叠步骤块并更新标题
            if (stepsCtx) {
                const count = Object.keys(stepsCtx.stepMap).length;
                stepsCtx.header.querySelector('.steps-label').textContent =
                    `已调用 ${count} 个工具`;
                stepsCtx.block.classList.add('collapsed');
            }

            // 显示最终答案
            const images = (event.images || []).map(p => {
                if (!p.startsWith('/')) return `/${p}`;
                return p;
            });
            addMessage(event.content, 'assistant', images);
            done();

        } else if (event.type === 'error') {
            es.close();
            hideTyping();
            addMessage(`出现错误：${event.error || '未知错误'}`, 'assistant');
            showNotification('请求失败', 'error');
            done();
        }
    };

    es.onerror = () => {
        es.close();
        hideTyping();
        if (!stepsCtx) {
            addMessage('网络连接失败，请确认服务是否正常运行。', 'assistant');
        }
        showNotification('连接中断', 'error');
        done();
    };

    function done() {
        isProcessing = false;
        sendBtn.disabled = false;
        sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
        chatInput.focus();
    }
}

sendBtn.addEventListener('click', sendMessage);

chatInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// 输入框自动伸缩
chatInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 140) + 'px';
});

// ===== 清空对话 =====
resetBtn.addEventListener('click', async () => {
    if (!confirm('确定要清空对话历史吗？')) return;

    try {
        const res  = await fetch(`${API_BASE}/api/reset`, { method: 'POST' });
        const data = await res.json();

        if (data.success) {
            chatMessages.innerHTML = '';
            chatMessages.appendChild(buildWelcomeCard('对话已重置，有什么可以帮您分析的吗？'));
            showNotification('对话已清空', 'success');
        }
    } catch {
        showNotification('重置失败，请重试', 'error');
    }
});

// ===== 初始化 =====
window.addEventListener('DOMContentLoaded', async () => {
    chatInput.focus();

    // 加载数据集信息
    try {
        const res  = await fetch(`${API_BASE}/api/data/info`);
        const data = await res.json();
        const info = data.data_info || data;

        if (info && info.total_records) {
            const tr    = info.time_range || {};
            const start = (tr.start || '').slice(0, 10);
            const end   = (tr.end   || '').slice(0, 10);
            document.getElementById('data-info').textContent =
                `${info.total_records.toLocaleString()} 条记录 · ${start} ~ ${end}`;
        } else {
            document.getElementById('data-info').textContent = '数据信息不可用';
        }
    } catch {
        document.getElementById('data-info').textContent = '数据信息不可用';
    }
});
