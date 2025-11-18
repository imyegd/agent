// ===== 全局变量 =====
const API_BASE = '';
let isProcessing = false;

// ===== 工具函数 =====
function showLoading() {
    document.getElementById('loading-overlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.add('hidden');
}

function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function formatTime(dateString) {
    return new Date(dateString).toLocaleString('zh-CN');
}

// ===== Tab 切换 =====
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;
        
        // 更新按钮状态
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // 切换内容
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        document.getElementById(`${tabName}-tab`).classList.add('active');
    });
});

// ===== 聊天功能 =====
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const resetBtn = document.getElementById('reset-btn');

function addMessage(content, type = 'assistant') {
    const message = document.createElement('div');
    message.className = `message ${type}-message`;
    
    const icon = document.createElement('i');
    icon.className = type === 'user' ? 'fas fa-user' : 'fas fa-robot';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    // 处理markdown和换行
    const formattedContent = content
        .replace(/\n/g, '<br>')
        .replace(/```([\s\S]*?)```/g, '<pre>$1</pre>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    messageContent.innerHTML = formattedContent;
    
    message.appendChild(icon);
    message.appendChild(messageContent);
    chatMessages.appendChild(message);
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message || isProcessing) return;
    
    // 添加用户消息
    addMessage(message, 'user');
    chatInput.value = '';
    
    isProcessing = true;
    sendBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        
        if (data.success) {
            addMessage(data.response, 'assistant');
        } else {
            addMessage(`错误：${data.error}`, 'assistant');
            showNotification('发送失败', 'error');
        }
    } catch (error) {
        addMessage('网络错误，请检查连接', 'assistant');
        showNotification('网络错误', 'error');
    } finally {
        isProcessing = false;
        sendBtn.disabled = false;
        chatInput.focus();
    }
}

sendBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// 自动调整输入框高度
chatInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 150) + 'px';
});

// 重置对话
resetBtn.addEventListener('click', async () => {
    if (!confirm('确定要清空对话历史吗？')) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/reset`, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            chatMessages.innerHTML = `
                <div class="message system-message">
                    <i class="fas fa-robot"></i>
                    <div class="message-content">
                        <p>对话已重置。有什么可以帮助您的吗？</p>
                    </div>
                </div>
            `;
            showNotification('对话已重置', 'success');
        }
    } catch (error) {
        showNotification('重置失败', 'error');
    }
});

// ===== 波动分析功能 =====
const analyzeStartTime = document.getElementById('analyze-start-time');
const analyzeEndTime = document.getElementById('analyze-end-time');
const analyzeBtn = document.getElementById('analyze-btn');
const analyzeResult = document.getElementById('analyze-result');

// 快速选择时间
document.querySelectorAll('.quick-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const range = btn.dataset.range;
        const now = new Date();
        const end = now.toISOString().slice(0, 16);
        
        let start = new Date(now);
        switch(range) {
            case '1h': start.setHours(start.getHours() - 1); break;
            case '6h': start.setHours(start.getHours() - 6); break;
            case '1d': start.setDate(start.getDate() - 1); break;
            case '7d': start.setDate(start.getDate() - 7); break;
        }
        
        analyzeStartTime.value = start.toISOString().slice(0, 16);
        analyzeEndTime.value = end;
    });
});

analyzeBtn.addEventListener('click', async () => {
    const startTime = analyzeStartTime.value.replace('T', ' ') + ':00';
    const endTime = analyzeEndTime.value.replace('T', ' ') + ':00';
    
    if (!startTime || !endTime) {
        showNotification('请选择时间范围', 'error');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE}/api/visualize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ start_time: startTime, end_time: endTime })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayAnalyzeResult(data);
            showNotification('分析完成', 'success');
        } else {
            analyzeResult.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>分析失败：${data.message || data.error}</p>
                </div>
            `;
            showNotification('分析失败', 'error');
        }
    } catch (error) {
        analyzeResult.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-circle"></i>
                <p>网络错误：${error.message}</p>
            </div>
        `;
        showNotification('网络错误', 'error');
    } finally {
        hideLoading();
    }
});

function displayAnalyzeResult(data) {
    let html = '<div style="color: var(--text-primary);">';
    
    // 文本报告
    if (data.text_report) {
        html += `<pre style="white-space: pre-wrap; font-family: monospace; line-height: 1.8;">${data.text_report}</pre>`;
    }
    
    // 图表
    if (data.plot_path) {
        html += `
            <div style="margin-top: 20px;">
                <h3 style="color: var(--primary-color); margin-bottom: 15px;">
                    <i class="fas fa-chart-area"></i> 可视化图表
                </h3>
                <img src="/${data.plot_path}" alt="分析图表" style="width: 100%; border-radius: 8px;">
            </div>
        `;
    }
    
    html += '</div>';
    analyzeResult.innerHTML = html;
}

// ===== 知识库功能 =====
const knowledgeQuery = document.getElementById('knowledge-query');
const knowledgeSearchBtn = document.getElementById('knowledge-search-btn');
const knowledgeResult = document.getElementById('knowledge-result');

async function searchKnowledge() {
    const query = knowledgeQuery.value.trim();
    if (!query) {
        showNotification('请输入搜索内容', 'error');
        return;
    }
    
    const docType = document.querySelector('input[name="doc-type"]:checked').value;
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE}/api/knowledge/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query,
                top_k: 5,
                doc_type: docType || null
            })
        });
        
        const data = await response.json();
        
        if (data.success && data.results_count > 0) {
            displayKnowledgeResults(data.results);
            showNotification(`找到 ${data.results_count} 条结果`, 'success');
        } else {
            knowledgeResult.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <p>未找到相关内容</p>
                </div>
            `;
        }
    } catch (error) {
        showNotification('搜索失败', 'error');
    } finally {
        hideLoading();
    }
}

function displayKnowledgeResults(results) {
    let html = '';
    
    results.forEach((result, index) => {
        html += `
            <div class="knowledge-item">
                <span class="score">相关度: ${(result.score * 100).toFixed(1)}%</span>
                <h4>${index + 1}. ${result.metadata.type === 'feature' ? result.metadata.name : result.metadata.problem || result.metadata.term || '知识条目'}</h4>
                <p>${result.content}</p>
            </div>
        `;
    });
    
    knowledgeResult.innerHTML = html;
}

knowledgeSearchBtn.addEventListener('click', searchKnowledge);
knowledgeQuery.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        searchKnowledge();
    }
});

// ===== 初始化 =====
window.addEventListener('DOMContentLoaded', async () => {
    // 加载数据集信息
    try {
        const response = await fetch(`${API_BASE}/api/data/info`);
        const data = await response.json();
        
        if (data.total_records) {
            document.getElementById('data-info').textContent = 
                `数据集: ${data.total_records} 条记录 | 时间范围: ${data.time_range.start.slice(0, 10)} ~ ${data.time_range.end.slice(0, 10)}`;
        }
    } catch (error) {
        console.error('加载数据信息失败:', error);
    }
    
    // 设置默认时间范围
    const now = new Date();
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    
    analyzeEndTime.value = now.toISOString().slice(0, 16);
    analyzeStartTime.value = yesterday.toISOString().slice(0, 16);
});

