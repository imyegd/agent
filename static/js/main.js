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

// ===== 发送消息 =====
async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message || isProcessing) return;

    // 首次发送时移除欢迎卡片
    document.querySelector('.welcome-card')?.remove();

    addMessage(message, 'user');
    chatInput.value = '';
    chatInput.style.height = 'auto';

    isProcessing = true;
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    showTyping();

    try {
        const res  = await fetch(`${API_BASE}/api/chat`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ message }),
        });
        const data = await res.json();
        hideTyping();

        if (data.success) {
            addMessage(data.response, 'assistant', data.images || []);
        } else {
            addMessage(`出现错误：${data.error || '未知错误'}`, 'assistant');
            showNotification('请求失败', 'error');
        }
    } catch {
        hideTyping();
        addMessage('网络连接失败，请确认服务是否正常运行。', 'assistant');
        showNotification('网络错误', 'error');
    } finally {
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
