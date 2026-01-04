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
                this.updateProgress(data.progress, data.message, data.layers);
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
                    this.filename = data.filename; // 保存文件名
                }

                // 更新进度（传递层数据）
                // 从后端返回的 layers 中提取数据
                const layersData = {};
                if (data.layers) {
                    Object.keys(data.layers).forEach(layerKey => {
                        const layerInfo = data.layers[layerKey];
                        layersData[layerKey] = {
                            progress: layerInfo.progress || 0,
                            message: layerInfo.message || '',
                            status: layerInfo.status || 'pending',
                            data: layerInfo.data || {}
                        };
                    });
                }
                
                this.updateProgress(data.progress, data.message, layersData);

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

    // 更新进度
    updateProgress(progress, message, layersData) {
        console.log('📊 更新进度:', progress, '% -', message);
        console.log('📋 层进度数据:', layersData);

        // 更新进度文本
        const progressText = document.querySelector('.overall-progress-percentage');
        if (progressText) {
            progressText.textContent = `${progress}%`;
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

        // 更新各层进度（使用真实的层进度数据）
        this.updateLayerProgress(layersData);
        
        // 如果进度数据中包含详细信息，也更新统计
        if (layersData) {
            Object.keys(layersData).forEach(layerKey => {
                const layerData = layersData[layerKey];
                if (layerData && layerData.data) {
                    const layerNum = parseInt(layerKey.replace('layer', ''));
                    this.updateLayerStatsFromData(layerNum, layerData.data);
                }
            });
        }
    }

    // 更新各层进度
    updateLayerProgress(layersData) {
        // 如果没有层数据，不重置现有进度
        if (!layersData) {
            return;
        }

        const layers = document.querySelectorAll('.layer-card');

        layers.forEach((layer, index) => {
            const layerNum = index + 1;
            const layerKey = `layer${layerNum}`;

            // 获取真实的层进度数据
            const layerData = layersData ? layersData[layerKey] : null;

            // 只在有层数据时更新
            if (layerData) {
                let layerProgress = layerData.progress || 0;
                let layerMessage = layerData.message || '';
                let layerStatus = layerData.status || 'pending';
                let layerDetails = layerData.data || {};

                const layerBar = layer.querySelector('.layer-progress-fill');
                const layerText = layer.querySelector('.progress-text');
                const statusEl = layer.querySelector('.layer-status');

                if (layerBar) {
                    layerBar.style.width = `${layerProgress}%`;
                }
                if (layerText) {
                    layerText.textContent = `${Math.round(layerProgress)}%`;
                }

                // 更新状态文字和样式
                if (statusEl) {
                    if (layerProgress === 0) {
                        statusEl.textContent = '等待中';
                        statusEl.className = 'layer-status';
                        layer.classList.remove('active', 'completed', 'error');
                    } else if (layerProgress < 100) {
                        statusEl.textContent = '处理中...';
                        statusEl.className = 'layer-status processing';
                        layer.classList.add('active');
                        layer.classList.remove('completed', 'error');
                    } else if (layerStatus === 'error') {
                        statusEl.textContent = '✗ 失败';
                        statusEl.className = 'layer-status error';
                        layer.classList.remove('active', 'completed');
                        layer.classList.add('error');
                    } else {
                        statusEl.textContent = '✓ 已完成';
                        statusEl.className = 'layer-status completed';
                        layer.classList.remove('active', 'error');
                        layer.classList.add('completed');
                    }
                }

                // 更新层消息
                const layerMessageEl = layer.querySelector('.layer-message');
                if (layerMessageEl) {
                    layerMessageEl.textContent = layerMessage;
                }

                // 更新各层的统计信息（从进度回调的data中获取）
                this.updateLayerStatsFromData(layerNum, layerDetails);
            }
        });
    }

    // 从进度数据中更新层统计信息
    updateLayerStatsFromData(layerNum, data) {
        if (!data) return;

        switch (layerNum) {
            case 1: // Layer 1: 预处理
                if (data.file_type) {
                    const el = document.getElementById('layer1-file-type');
                    if (el) el.textContent = data.file_type.toUpperCase();
                }
                if (data.markdown_length) {
                    const el = document.getElementById('layer1-text-length');
                    if (el) el.textContent = this.formatFileSize(data.markdown_length);
                }
                break;

            case 2: // Layer 2: 语义分析
                if (data.total_chunks !== undefined) {
                    const el = document.getElementById('layer2-chunk-count');
                    if (el) el.textContent = data.total_chunks;
                }
                if (data.type_distribution) {
                    const dist = data.type_distribution;
                    const distText = Object.entries(dist)
                        .map(([k, v]) => `${k}: ${v}`)
                        .join(', ');
                    const el = document.getElementById('layer2-type-dist');
                    if (el) el.textContent = distText || '--';
                }
                if (data.overall_avg_confidence !== undefined) {
                    const el = document.getElementById('layer2-confidence');
                    if (el) el.textContent = (data.overall_avg_confidence * 100).toFixed(1) + '%';
                }
                break;

            case 3: // Layer 3: DITA转换
                if (data.success_count !== undefined) {
                    const el = document.getElementById('layer3-dita-count');
                    if (el) el.textContent = data.success_count;
                }
                if (data.total !== undefined) {
                    const el = document.getElementById('layer3-total-count');
                    if (el) el.textContent = data.total;
                }
                if (data.success_rate !== undefined) {
                    const el = document.getElementById('layer3-success-rate');
                    if (el) el.textContent = Math.round(data.success_rate * 100) + '%';
                }
                break;

            case 4: // Layer 4: 质量保证
                if (data.avg_quality !== undefined) {
                    const el = document.getElementById('layer4-quality-score');
                    if (el) el.textContent = Math.round(data.avg_quality) + '/100';
                }
                if (data.success !== undefined) {
                    const el = document.getElementById('layer4-success-count');
                    if (el) el.textContent = data.success;
                }
                if (data.total !== undefined) {
                    const el = document.getElementById('layer4-total-count');
                    if (el) el.textContent = data.total;
                }
                break;
        }
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
        if (!data || !data.success) return;

        switch (layerNum) {
            case 1: // Layer 1: 预处理层
                if (data.file_type) {
                    const el = document.getElementById('layer1-file-type');
                    if (el) el.textContent = data.file_type.toUpperCase();
                }
                if (data.markdown_length) {
                    const el = document.getElementById('layer1-text-length');
                    if (el) el.textContent = this.formatFileSize(data.markdown_length);
                }
                break;

            case 2: // Layer 2: 语义分析层
                if (data.total_chunks !== undefined) {
                    const el = document.getElementById('layer2-chunk-count');
                    if (el) el.textContent = data.total_chunks;
                }
                if (data.statistics) {
                    const stats = data.statistics;
                    if (stats.type_distribution) {
                        const dist = stats.type_distribution;
                        const distText = Object.entries(dist)
                            .map(([k, v]) => `${k}: ${v}`)
                            .join(', ');
                        const el = document.getElementById('layer2-type-dist');
                        if (el) el.textContent = distText || '--';
                    }
                    if (stats.overall_avg_confidence !== undefined) {
                        const el = document.getElementById('layer2-confidence');
                        if (el) el.textContent = (stats.overall_avg_confidence * 100).toFixed(1) + '%';
                    }
                }
                break;

            case 3: // Layer 3: DITA转换层
                if (data.success !== undefined && data.total !== undefined) {
                    const el = document.getElementById('layer3-dita-count');
                    if (el) el.textContent = `${data.success}/${data.total}`;
                }
                if (data.total !== undefined) {
                    const el = document.getElementById('layer3-total-count');
                    if (el) el.textContent = data.total;
                }
                if (data.success_rate !== undefined) {
                    const el = document.getElementById('layer3-success-rate');
                    if (el) el.textContent = Math.round(data.success_rate * 100) + '%';
                }
                break;

            case 4: // Layer 4: 质量保证层
                if (data.avg_quality_score !== undefined) {
                    const el = document.getElementById('layer4-quality-score');
                    if (el) el.textContent = Math.round(data.avg_quality_score) + '/100';
                }
                if (data.success !== undefined) {
                    const el = document.getElementById('layer4-success-count');
                    if (el) el.textContent = data.success;
                }
                if (data.total !== undefined) {
                    const el = document.getElementById('layer4-total-count');
                    if (el) el.textContent = data.total;
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

        // 更新进度到100%，并保持各层的完成状态
        this.updateProgress(100, '转换完成！', {
            'layer1': { 'status': 'completed', 'progress': 100, 'message': '✅ 预处理完成' },
            'layer2': { 'status': 'completed', 'progress': 100, 'message': '✅ 语义分析完成' },
            'layer3': { 'status': 'completed', 'progress': 100, 'message': '✅ DITA转换完成' },
            'layer4': { 'status': 'completed', 'progress': 100, 'message': '✅ 质量保证完成' }
        });

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

        // 加载各层结果文件
        await this.loadLayerResults();
    }

    // 加载各层结果文件
    async loadLayerResults() {
        console.log('📂 加载结果文件...');

        for (let layer = 1; layer <= 4; layer++) {
            try {
                const response = await fetch(`/api/layer/${this.sessionId}/layer${layer}`);
                const data = await response.json();

                if (data.success) {
                    this.displayLayerResults(layer, data);
                }
            } catch (error) {
                console.error(`❌ 加载Layer ${layer}结果失败:`, error);
            }
        }
    }

    // 显示层结果文件
    async displayLayerResults(layer, layerData) {
        const resultsContainer = document.getElementById(`results-layer${layer}`);
        if (!resultsContainer) return;

        // 清空现有内容
        resultsContainer.innerHTML = '';

        // 根据层类型显示不同的结果
        switch (layer) {
            case 1:
                // Layer 1: 预处理结果
                await this.displayPreprocessingResults(resultsContainer, layerData);
                break;
            case 2:
                // Layer 2: 语义分析结果
                await this.displaySemanticResults(resultsContainer, layerData);
                break;
            case 3:
                // Layer 3: DITA转换结果
                await this.displayDITAResults(resultsContainer, layerData);
                break;
            case 4:
                // Layer 4: 质量保证结果
                await this.displayQualityResults(resultsContainer, layerData);
                break;
        }
    }

    // 显示预处理结果
    async displayPreprocessingResults(container, data) {
        // 获取文件列表
        try {
            const filesResponse = await fetch(`/api/layer/${this.sessionId}/layer1/files`);
            const filesData = await filesResponse.json();
            
            if (filesData.success && filesData.files && filesData.files.length > 0) {
                // 显示预览和下载按钮
                const previewBtn = document.getElementById('preview-layer1');
                const downloadBtn = document.getElementById('download-layer1');
                if (previewBtn) previewBtn.style.display = 'inline-flex';
                if (downloadBtn) downloadBtn.style.display = 'inline-flex';
                
                // 查找.md文件
                const mdFiles = filesData.files.filter(f => f.name.endsWith('.md') || f.type === 'md' || f.type === 'markdown');
                
                if (mdFiles.length > 0) {
                    // 如果有md文件，显示所有md文件
                    mdFiles.forEach(file => {
                        const fileItem = this.createFileItem(file, 'layer1');
                        container.appendChild(fileItem);
                    });
                } else {
                    // 如果没有md文件，显示所有文件
                    filesData.files.forEach(file => {
                        const fileItem = this.createFileItem(file, 'layer1');
                        container.appendChild(fileItem);
                    });
                }
            } else {
                // 如果没有文件列表，显示默认项，尝试推断文件名
                const fileItem = document.createElement('div');
                fileItem.className = 'result-file-item';
                
                // 尝试从filename推断markdown文件名
                let markdownFileName = null;
                if (this.filename) {
                    // 移除文件扩展名，添加.md
                    const baseName = this.filename.replace(/\.[^/.]+$/, '');
                    markdownFileName = `${baseName}.md`;
                }
                
                // 添加预览按钮（使用推断的文件名或尝试第一个可能的文件名）
                const previewBtn = markdownFileName ? `
                    <button class="btn btn-sm btn-primary preview-btn" onclick="filePreviewer.preview('${this.sessionId}', 'layer1', '${markdownFileName}', '预处理后的Markdown').catch(err => { 
                        console.error('预览失败:', err); 
                        alert('预览失败: 文件不存在或路径错误');
                    })">
                        <i class="fas fa-eye"></i> 预览
                    </button>
                ` : '';
                
                fileItem.innerHTML = `
                    <div class="file-icon"><i class="fas fa-file-alt"></i></div>
                    <div class="file-info">
                        <div class="file-name">预处理后的Markdown</div>
                        <div class="file-size">${data.markdown_length ? this.formatFileSize(data.markdown_length) : '未知'}</div>
                    </div>
                    <div class="file-actions">
                        ${previewBtn}
                        <button class="btn btn-sm btn-primary" onclick="window.location.href='/api/download/layer/${this.sessionId}/layer1'">下载</button>
                    </div>
                `;
                container.appendChild(fileItem);
            }
        } catch (error) {
            console.error('获取文件列表失败:', error);
        }
    }

    // 显示语义分析结果
    async displaySemanticResults(container, data) {
        try {
            const filesResponse = await fetch(`/api/layer/${this.sessionId}/layer2/files`);
            const filesData = await filesResponse.json();
            
            if (filesData.success && filesData.files.length > 0) {
                // 显示预览和下载按钮
                const previewBtn = document.getElementById('preview-layer2');
                const downloadBtn = document.getElementById('download-layer2');
                if (previewBtn) previewBtn.style.display = 'inline-flex';
                if (downloadBtn) downloadBtn.style.display = 'inline-flex';
                
                filesData.files.forEach(file => {
                    const fileItem = this.createFileItem(file, 'layer2');
                    container.appendChild(fileItem);
                });
            } else {
                // 如果没有文件列表，显示默认项，尝试预览常见的JSON文件
                const fileItem = document.createElement('div');
                fileItem.className = 'result-file-item';
                
                // 尝试预览layer2_result.json
                const previewBtn = `
                    <button class="btn btn-sm btn-primary preview-btn" onclick="filePreviewer.preview('${this.sessionId}', 'layer2', 'layer2_result.json', '语义分析结果').catch(err => { 
                        console.error('预览失败:', err); 
                    })">
                        <i class="fas fa-eye"></i> 预览
                    </button>
                `;
                
                fileItem.innerHTML = `
                    <div class="file-icon"><i class="fas fa-brain"></i></div>
                    <div class="file-info">
                        <div class="file-name">语义分析结果 (${data.total_chunks || 0} 个分块)</div>
                    </div>
                    <div class="file-actions">
                        ${previewBtn}
                        <button class="btn btn-sm btn-primary" onclick="window.location.href='/api/download/layer/${this.sessionId}/layer2'">下载</button>
                    </div>
                `;
                container.appendChild(fileItem);
            }
        } catch (error) {
            console.error('获取文件列表失败:', error);
        }
    }

    // 显示DITA转换结果
    async displayDITAResults(container, data) {
        try {
            const filesResponse = await fetch(`/api/layer/${this.sessionId}/layer3/files`);
            const filesData = await filesResponse.json();
            
            if (filesData.success && filesData.files.length > 0) {
                // 显示预览和下载按钮
                const previewBtn = document.getElementById('preview-layer3');
                const downloadBtn = document.getElementById('download-layer3');
                if (previewBtn) previewBtn.style.display = 'inline-flex';
                if (downloadBtn) downloadBtn.style.display = 'inline-flex';
                
                filesData.files.forEach(file => {
                    const fileItem = this.createFileItem(file, 'layer3');
                    container.appendChild(fileItem);
                });
            } else {
                // 如果没有文件列表，显示默认项，尝试预览全部
                const fileItem = document.createElement('div');
                fileItem.className = 'result-file-item';
                
                // DITA文件通常有多个，使用预览全部功能
                const previewBtn = `
                    <button class="btn btn-sm btn-primary preview-btn" onclick="if(window.processor) window.processor.previewLayerAll(3)">
                        <i class="fas fa-eye"></i> 预览
                    </button>
                `;
                
                fileItem.innerHTML = `
                    <div class="file-icon"><i class="fas fa-code"></i></div>
                    <div class="file-info">
                        <div class="file-name">DITA转换结果 (${data.success || 0} 个成功)</div>
                    </div>
                    <div class="file-actions">
                        ${previewBtn}
                        <button class="btn btn-sm btn-primary" onclick="window.location.href='/api/download/layer/${this.sessionId}/layer3'">下载</button>
                    </div>
                `;
                container.appendChild(fileItem);
            }
        } catch (error) {
            console.error('获取文件列表失败:', error);
        }
    }

    // 显示质量保证结果
    async displayQualityResults(container, data) {
        try {
            const filesResponse = await fetch(`/api/layer/${this.sessionId}/layer4/files`);
            const filesData = await filesResponse.json();
            
            if (filesData.success && filesData.files.length > 0) {
                // 显示预览和下载按钮
                const previewBtn = document.getElementById('preview-layer4');
                const downloadBtn = document.getElementById('download-layer4');
                if (previewBtn) previewBtn.style.display = 'inline-flex';
                if (downloadBtn) downloadBtn.style.display = 'inline-flex';
                
                filesData.files.forEach(file => {
                    const fileItem = this.createFileItem(file, 'layer4');
                    container.appendChild(fileItem);
                });
            } else {
                // 如果没有文件列表，显示默认项，尝试预览质量报告JSON文件
                const fileItem = document.createElement('div');
                fileItem.className = 'result-file-item';
                
                // 尝试预览layer4_result.json或quality_report.json
                const previewBtn = `
                    <button class="btn btn-sm btn-primary preview-btn" onclick="filePreviewer.preview('${this.sessionId}', 'layer4', 'layer4_result.json', '质量评估报告').catch(() => filePreviewer.preview('${this.sessionId}', 'layer4', 'quality_report.json', '质量评估报告')).catch(err => { 
                        console.error('预览失败:', err); 
                    })">
                        <i class="fas fa-eye"></i> 预览
                    </button>
                `;
                
                fileItem.innerHTML = `
                    <div class="file-icon"><i class="fas fa-shield-alt"></i></div>
                    <div class="file-info">
                        <div class="file-name">质量评估报告</div>
                        <div class="file-size">${data.total ? this.formatFileSize(data.total) : '未知'}</div>
                    </div>
                    <div class="file-actions">
                        ${previewBtn}
                        <button class="btn btn-sm btn-primary" onclick="window.location.href='/api/download/layer/${this.sessionId}/layer4'">下载</button>
                    </div>
                `;
                container.appendChild(fileItem);
            }
        } catch (error) {
            console.error('获取文件列表失败:', error);
        }
    }
    
    // 创建文件项（带预览按钮）
    createFileItem(file, layer) {
        const fileItem = document.createElement('div');
        fileItem.className = 'result-file-item';
        
        // 根据文件类型选择图标
        let icon = 'fa-file';
        if (file.type === 'dita' || file.type === 'xml') {
            icon = 'fa-code';
        } else if (file.type === 'json') {
            icon = 'fa-file-code';
        } else if (file.type === 'md' || file.type === 'markdown') {
            icon = 'fa-file-alt';
        } else if (['png', 'jpg', 'jpeg', 'gif'].includes(file.type)) {
            icon = 'fa-image';
        }
        
        const canPreview = ['dita', 'xml', 'json', 'md', 'markdown', 'png', 'jpg', 'jpeg', 'gif'].includes(file.type);
        
        // 转义文件路径和文件名，防止XSS，同时规范化路径（统一为正斜杠用于URL）
        const normalizedPath = file.path.replace(/\\/g, '/'); // Windows路径转URL路径
        const escapedPath = normalizedPath.replace(/'/g, "\\'").replace(/"/g, '&quot;');
        const escapedName = file.name.replace(/'/g, "\\'").replace(/"/g, '&quot;');
        
        fileItem.innerHTML = `
            <div class="file-icon"><i class="fas ${icon}"></i></div>
            <div class="file-info">
                <div class="file-name">${escapedName}</div>
                <div class="file-size">${this.formatFileSize(file.size)}</div>
            </div>
            <div class="file-actions">
                ${canPreview ? `<button class="btn btn-sm btn-primary preview-btn" onclick="filePreviewer.preview('${this.sessionId}', '${layer}', '${escapedPath}', '${escapedName}')">
                    <i class="fas fa-eye"></i> 预览
                </button>` : ''}
                <button class="btn btn-sm btn-primary" onclick="window.location.href='/api/download/layer/${this.sessionId}/${layer}'">下载</button>
            </div>
        `;
        return fileItem;
    }

    // 预览整个Layer的所有文件
    async previewLayerAll(layer) {
        try {
            // 获取该layer的所有文件
            const filesResponse = await fetch(`/api/layer/${this.sessionId}/layer${layer}/files`);
            const filesData = await filesResponse.json();
            
            if (!filesData.success || !filesData.files || filesData.files.length === 0) {
                alert('该层没有可预览的文件');
                return;
            }
            
            // 过滤出可预览的文件
            const previewableFiles = filesData.files.filter(file => {
                const fileType = file.type.toLowerCase();
                return ['dita', 'xml', 'json', 'md', 'markdown', 'png', 'jpg', 'jpeg', 'gif'].includes(fileType);
            });
            
            if (previewableFiles.length === 0) {
                alert('该层没有可预览的文件类型');
                return;
            }
            
            // 调用预览组件的预览全部功能
            if (typeof filePreviewer !== 'undefined' && filePreviewer.previewLayerAll) {
                filePreviewer.previewLayerAll(this.sessionId, `layer${layer}`, previewableFiles, `Layer ${layer} 全部结果`);
            } else {
                // 如果预览组件不支持预览全部，则预览第一个文件
                const firstFile = previewableFiles[0];
                filePreviewer.preview(this.sessionId, `layer${layer}`, firstFile.path, firstFile.name);
            }
        } catch (error) {
            console.error(`预览Layer ${layer}失败:`, error);
            alert(`预览失败: ${error.message}`);
        }
    }

    // 下载文件
    async downloadFile(fileType, sessionId, index = 0) {
        try {
            const response = await fetch(`/api/process/download/${sessionId}?type=${fileType}&index=${index}`);
            if (!response.ok) throw new Error('下载失败');

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;

            // 设置文件名
            let fileName = `${sessionId}_${fileType}`;
            switch (fileType) {
                case 'markdown':
                    fileName += '.md';
                    break;
                case 'semantic':
                    fileName += '.json';
                    break;
                case 'dita':
                    fileName += `_${index + 1}.xml`;
                    break;
                case 'quality':
                    fileName += '.json';
                    break;
                default:
                    fileName += '.txt';
            }

            a.download = fileName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('❌ 下载失败:', error);
            this.showNotification('下载失败', 'error');
        }
    }

    // 格式化文件大小
    formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        else if (bytes < 1048576) return (bytes / 1024).toFixed(2) + ' KB';
        else return (bytes / 1048576).toFixed(2) + ' MB';
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

        // 预处理结果
        if (data.layer_name === 'layer1' && data.markdown) {
            content += `
                <div class="result-section">
                    <h6>预处理结果</h6>
                    <div class="result-content">
                        <pre>${this.escapeHtml(data.markdown.substring(0, 1000))}...</pre>
                    </div>
                </div>
            `;
        }

        // 语义分块结果
        if (data.layer_name === 'layer2' && data.chunks) {
            content += `
                <div class="result-section">
                    <h6>语义分块结果</h6>
                    <div class="result-stats">
                        <div class="stat-item">
                            <div class="stat-value">${data.total_chunks}</div>
                            <div class="stat-label">分块数量</div>
                        </div>
                    </div>
                    <div class="result-content">${data.chunks.slice(0, 3).map((chunk, i) => `块${i + 1}: ${this.escapeHtml(chunk.content.substring(0, 100))}...`).join('\n\n')}</div>
                </div>
            `;
        }

        // DITA转换结果
        if (data.layer_name === 'layer3' && data.total > 0) {
            content += `
                <div class="result-section">
                    <h6>DITA转换结果</h6>
                    <div class="result-stats">
                        <div class="stat-item">
                            <div class="stat-value">${data.total}</div>
                            <div class="stat-label">DITA文件</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${data.success_rate}%</div>
                            <div class="stat-label">成功率</div>
                        </div>
                    </div>
                </div>
            `;
        }

        // 质量评估结果
        if (data.layer_name === 'layer4' && data.total > 0) {
            content += `
                <div class="result-section">
                    <h6>质量评估结果</h6>
                    <div class="result-stats">
                        <div class="stat-item">
                            <div class="stat-value">${data.avg_quality_score || 0}/100</div>
                            <div class="stat-label">总体评分</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${data.success}</div>
                            <div class="stat-label">成功</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${data.failed}</div>
                            <div class="stat-label">失败</div>
                        </div>
                    </div>
                    ${data.summary ? `<div class="result-content">${this.escapeHtml(JSON.stringify(data.summary, null, 2))}</div>` : ''}
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