/**
 * 转换处理页面脚本
 */

class ConversionProcessor {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.statusInterval = null;
        this.socket = null;

        this.init();
    }

    init() {
        console.log('🔄 初始化转换处理器:', this.sessionId);

        // 初始化 Socket.IO（如果可用）
        if (typeof io !== 'undefined') {
            this.initSocket();
        }

        // 获取初始状态
        this.checkStatus();

        // 开始轮询状态
        this.startStatusPolling();

        // 自动开始转换
        this.startConversion();
    }

    // 初始化 Socket.IO
    initSocket() {
        this.socket = io();

        this.socket.on('connect', () => {
            console.log('✅ Socket 连接成功');
        });

        this.socket.on('progress_update', (data) => {
            if (data.session_id === this.sessionId) {
                console.log('📊 Socket 进度更新:', data);
                this.updateProgress(data.progress, data.message);
            }
        });

        this.socket.on('conversion_complete', (data) => {
            if (data.session_id === this.sessionId) {
                console.log('✅ Socket 转换完成');
                this.onComplete();
            }
        });

        this.socket.on('conversion_error', (data) => {
            if (data.session_id === this.sessionId) {
                console.error('❌ Socket 转换错误:', data.error);
                this.onError(data.error);
            }
        });
    }

    // 开始转换
    async startConversion() {
        try {
            console.log('🚀 发送转换请求...');

            // 显示状态消息
            const messageBox = document.querySelector('.current-message-box');
            if (messageBox) {
                messageBox.style.display = 'block';
                document.getElementById('statusTitle').textContent = '处理中...';
                document.getElementById('statusText').textContent = '正在初始化转换...';
            }

            const response = await fetch(`/api/process/start/${this.sessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            });

            const data = await response.json();

            if (data.success) {
                console.log('✅ 转换已启动');
                showNotification('转换已开始', 'success');
            } else {
                console.error('❌ 启动失败:', data.error);
                showNotification(data.error || '启动转换失败', 'error');
                this.onError(data.error);
            }
        } catch (error) {
            console.error('❌ 启动转换异常:', error);
            showNotification('启动转换失败: ' + error.message, 'error');
            this.onError(error.message);
        }
    }

    // 开始状态轮询
    startStatusPolling() {
        // 清除旧的轮询
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
        }

        // 每秒轮询一次
        this.statusInterval = setInterval(() => {
            this.checkStatus();
        }, 1000);
    }

    // 检查状态
    async checkStatus() {
        try {
            const response = await fetch(`/api/process/status/${this.sessionId}`);
            const data = await response.json();

            if (data.success) {
                // 更新文件名
                const filenameEl = document.getElementById('filename');
                if (filenameEl && data.filename) {
                    filenameEl.textContent = data.filename;
                }

                // 更新进度
                this.updateProgress(data.progress, data.message);

                // 检查是否完成
                if (data.status === 'completed') {
                    this.onComplete();
                } else if (data.status === 'error') {
                    this.onError(data.error);
                }
            }
        } catch (error) {
            console.error('❌ 状态查询失败:', error);
        }
    }

    // 更新进度显示
    updateProgress(progress, message) {
        console.log(`📊 进度更新: ${progress}% - ${message}`);

        // 更新总进度
        const totalProgressEl = document.querySelector('.total-progress');
        if (totalProgressEl) {
            totalProgressEl.textContent = `${progress}%`;
        }

        // 更新总进度条
        const progressFill = document.querySelector('.progress-fill');
        if (progressFill) {
            progressFill.style.width = `${progress}%`;
        }

        // 更新消息
        if (message) {
            const messageEl = document.querySelector('.current-message');
            if (messageEl) {
                messageEl.textContent = message;
            }

            const messageBox = document.querySelector('.current-message-box');
            if (messageBox && progress > 0) {
                messageBox.style.display = 'block';
            }
        }

        // 更新各层进度（基于实际进度）
        this.updateLayerProgress(progress);
    }

    // 更新各层进度
    updateLayerProgress(totalProgress) {
        const layers = document.querySelectorAll('.layer-card');
        
        layers.forEach((layer, index) => {
            const layerNum = index + 1;
            let layerProgress = 0;
            
            // 根据总进度计算各层进度
            if (totalProgress <= 20) {
                // 第一层：0-20%
                layerProgress = totalProgress * 5;
            } else if (totalProgress <= 40) {
                // 第二层：20-40%
                if (index === 0) layerProgress = 100; // 第一层完成
                else if (index === 1) layerProgress = (totalProgress - 20) * 5;
            } else if (totalProgress <= 70) {
                // 第三层：40-70%
                if (index <= 1) layerProgress = 100; // 前两层完成
                else if (index === 2) layerProgress = (totalProgress - 40) * 3.33;
            } else if (totalProgress <= 90) {
                // 第四层：70-90%
                if (index <= 2) layerProgress = 100; // 前三层完成
                else if (index === 3) layerProgress = (totalProgress - 70) * 5;
            } else {
                // 完成：90-100%
                layerProgress = 100;
            }

            const layerBar = layer.querySelector('.layer-progress-fill');
            const layerText = layer.querySelector('.progress-text');
            const layerStatus = layer.querySelector('.layer-status');

            if (layerBar) {
                layerBar.style.width = `${layerProgress}%`;
            }
            if (layerText) {
                layerText.textContent = `${Math.round(layerProgress)}%`;
            }

            // 更新状态文字和样式
            if (layerStatus) {
                if (layerProgress === 0) {
                    layerStatus.textContent = '等待中';
                    layerStatus.className = 'layer-status';
                    layer.classList.remove('active', 'completed');
                } else if (layerProgress < 100) {
                    layerStatus.textContent = '处理中...';
                    layerStatus.className = 'layer-status processing';
                    layer.classList.add('active');
                    layer.classList.remove('completed');
                } else {
                    layerStatus.textContent = '✓ 已完成';
                    layerStatus.className = 'layer-status completed';
                    layer.classList.remove('active');
                    layer.classList.add('completed');
                }
            }
        });
    }

    // 更新层统计信息
    async updateLayerStats() {
        try {
            // 获取各层结果
            const layers = ['layer1', 'layer2', 'layer3', 'layer4'];
            
            for (let i = 0; i < layers.length; i++) {
                const response = await fetch(`/api/layer/${this.sessionId}/${layers[i]}`);
                if (response.ok) {
                    const data = await response.json();
                    this.updateLayerStatsDisplay(i + 1, data);
                }
            }
        } catch (error) {
            console.error('更新层统计信息失败:', error);
        }
    }

    // 更新层统计显示
    updateLayerStatsDisplay(layerNum, data) {
        const layerCard = document.querySelector(`.layer-card:nth-child(${layerNum})`);
        if (!layerCard) return;

        const statsEl = layerCard.querySelector('.layer-stats');
        if (!statsEl) return;

        switch (layerNum) {
            case 1: // 预处理层
                if (data.file_type) {
                    statsEl.innerHTML = `<span class="file-type">文件类型: <strong>${data.file_type}</strong></span>`;
                }
                break;
            case 2: // 语义分析层
                if (data.chunks && data.chunks.length > 0) {
                    statsEl.innerHTML = `<span class="chunk-count">分块数量: <strong>${data.chunks.length}</strong></span>`;
                }
                break;
            case 3: // DITA转换层
                if (data.conversion_stats) {
                    const successRate = data.conversion_stats.success_rate || 0;
                    statsEl.innerHTML = `<span class="conversion-rate">成功率: <strong>${successRate}%</strong></span>`;
                }
                break;
            case 4: // 质量保证层
                if (data.quality_score) {
                    const score = data.quality_score.overall || 0;
                    statsEl.innerHTML = `<span class="quality-score">质量评分: <strong>${score}/100</strong></span>`;
                }
                break;
        }
    }

    // 转换完成
    async onComplete() {
        console.log('✅ 转换完成');

        // 停止轮询
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }

        // 更新进度到100%
        this.updateProgress(100, '转换完成！');

        // 更新层统计信息
        await this.updateLayerStats();

        // 更新状态消息
        const messageBox = document.querySelector('.current-message-box');
        if (messageBox) {
            messageBox.className = 'status-message success current-message-box';
            messageBox.style.display = 'block';
            document.getElementById('statusTitle').innerHTML = '<i class="fas fa-check-circle"></i> 转换完成！';
            document.getElementById('statusText').textContent = '您的文档已成功转换为DITA格式';
        }

        // 显示操作按钮
        const actionButtons = document.getElementById('actionButtons');
        const downloadBtn = document.getElementById('downloadBtn');

        if (actionButtons) {
            actionButtons.style.display = 'flex';
        }

        if (downloadBtn) {
            downloadBtn.style.display = 'inline-block';
            downloadBtn.href = `/api/download/${this.sessionId}`;
        }

        // 添加点击事件到各层卡片
        this.addLayerClickEvents();

        // 显示成功通知
        showNotification('转换完成！可以下载了', 'success');

        // 添加完成状态
        document.body.classList.add('conversion-complete');
    }

    // 添加层卡片点击事件
    addLayerClickEvents() {
        const layerCards = document.querySelectorAll('.layer-card.completed');
        layerCards.forEach((card, index) => {
            card.style.cursor = 'pointer';
            card.addEventListener('click', () => {
                this.showLayerDetails(index + 1);
            });
        });
    }

    // 显示层详情
    async showLayerDetails(layerNum) {
        try {
            const layerNames = ['layer1', 'layer2', 'layer3', 'layer4'];
            const layerTitles = ['预处理层', '语义分析层', 'DITA转换层', '质量保证层'];
            
            const response = await fetch(`/api/layer/${this.sessionId}/${layerNames[layerNum - 1]}`);
            if (!response.ok) {
                throw new Error('获取层详情失败');
            }

            const data = await response.json();
            this.showModal(layerTitles[layerNum - 1], data);

        } catch (error) {
            console.error('显示层详情失败:', error);
            showNotification('获取详情失败', 'error');
        }
    }

    // 显示模态框
    showModal(title, data) {
        const modal = document.getElementById('resultModal');
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = document.getElementById('modalBody');

        modalTitle.textContent = title;
        modalBody.innerHTML = this.generateModalContent(data);

        // 显示模态框
        modal.classList.add('show');

        // 添加关闭事件
        const closeBtn = modal.querySelector('.btn-close');
        closeBtn.onclick = () => {
            modal.classList.remove('show');
        };

        // 点击背景关闭
        modal.onclick = (e) => {
            if (e.target === modal) {
                modal.classList.remove('show');
            }
        };
    }

    // 生成模态框内容
    generateModalContent(data) {
        let content = '';

        // 基本信息部分
        if (data.file_type) {
            content += `
                <div class="result-section">
                    <h6>文件信息</h6>
                    <div class="result-stats">
                        <div class="stat-item">
                            <div class="stat-value">${data.file_type}</div>
                            <div class="stat-label">文件类型</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${data.word_count || 0}</div>
                            <div class="stat-label">字数统计</div>
                        </div>
                    </div>
                </div>
            `;
        }

        // 预处理结果
        if (data.markdown_content) {
            content += `
                <div class="result-section">
                    <h6>预处理结果</h6>
                    <div class="result-content">${this.escapeHtml(data.markdown_content.substring(0, 1000))}${data.markdown_content.length > 1000 ? '...' : ''}</div>
                </div>
            `;
        }

        // 语义分析结果
        if (data.chunks && data.chunks.length > 0) {
            content += `
                <div class="result-section">
                    <h6>语义分块结果</h6>
                    <div class="result-stats">
                        <div class="stat-item">
                            <div class="stat-value">${data.chunks.length}</div>
                            <div class="stat-label">分块数量</div>
                        </div>
                    </div>
                    <div class="result-content">${data.chunks.slice(0, 3).map((chunk, i) => `块${i+1}: ${this.escapeHtml(chunk.content.substring(0, 100))}...`).join('\n\n')}</div>
                </div>
            `;
        }

        // DITA转换结果
        if (data.dita_files && data.dita_files.length > 0) {
            content += `
                <div class="result-section">
                    <h6>DITA转换结果</h6>
                    <div class="result-stats">
                        <div class="stat-item">
                            <div class="stat-value">${data.dita_files.length}</div>
                            <div class="stat-label">DITA文件</div>
                        </div>
                        ${data.conversion_stats ? `<div class="stat-item"><div class="stat-value">${data.conversion_stats.success_rate}%</div><div class="stat-label">成功率</div></div>` : ''}
                    </div>
                </div>
            `;
        }

        // 质量评估结果
        if (data.quality_score) {
            content += `
                <div class="result-section">
                    <h6>质量评估结果</h6>
                    <div class="result-stats">
                        <div class="stat-item">
                            <div class="stat-value">${data.quality_score.overall || 0}/100</div>
                            <div class="stat-label">总体评分</div>
                        </div>
                        ${data.quality_score.structure ? `<div class="stat-item"><div class="stat-value">${data.quality_score.structure}/100</div><div class="stat-label">结构评分</div></div>` : ''}
                        ${data.quality_score.content ? `<div class="stat-item"><div class="stat-value">${data.quality_score.content}/100</div><div class="stat-label">内容评分</div></div>` : ''}
                    </div>
                    ${data.issues && data.issues.length > 0 ? `<div class="result-content">发现的问题：${data.issues.map(issue => `• ${this.escapeHtml(issue)}`).join('\n')}</div>` : ''}
                </div>
            `;
        }

        return content || '<div class="result-section"><p>暂无详细数据</p></div>';
    }

    // HTML转义
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 转换错误
    onError(error) {
        console.error('❌ 转换失败:', error);

        // 停止轮询
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }

        // 更新状态消息
        const messageBox = document.querySelector('.current-message-box');
        if (messageBox) {
            messageBox.className = 'status-message error current-message-box';
            messageBox.style.display = 'block';
            document.getElementById('statusTitle').innerHTML = '<i class="fas fa-exclamation-circle"></i> 处理失败';
            document.getElementById('statusText').textContent = error || '发生未知错误';
        }

        // 显示新建按钮
        const actionButtons = document.getElementById('actionButtons');
        if (actionButtons) {
            actionButtons.style.display = 'flex';
        }

        // 隐藏下载按钮
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            downloadBtn.style.display = 'none';
        }

        // 显示错误通知
        showNotification('转换失败: ' + error, 'error');

        // 添加错误状态
        document.body.classList.add('conversion-error');
    }

    // 清理
    destroy() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
        }
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function () {
    // 从 URL 获取 session_id
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');

    if (sessionId) {
        console.log('📋 Session ID:', sessionId);
        window.processor = new ConversionProcessor(sessionId);
    } else {
        console.warn('⚠️ 未找到 session_id');
        showNotification('缺少会话ID，即将返回首页', 'error');
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
    }
});

// 页面卸载时清理
window.addEventListener('beforeunload', function () {
    if (window.processor) {
        window.processor.destroy();
    }
});