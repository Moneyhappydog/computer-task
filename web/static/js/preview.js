/**
 * 文件预览功能
 */

class FilePreviewer {
    constructor() {
        this.modal = null;
        this.initModal();
    }
    
    initModal() {
        // 创建预览模态框
        const modalHTML = `
            <div id="filePreviewModal" class="preview-modal" style="display: none;">
                <div class="preview-modal-overlay" onclick="filePreviewer.close()"></div>
                <div class="preview-modal-content">
                    <div class="preview-modal-header">
                        <h3 id="previewFileName"><i class="fas fa-file"></i><span>文件预览</span></h3>
                        <button class="preview-modal-close" onclick="filePreviewer.close()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="preview-modal-body">
                        <div id="previewLoading" class="preview-loading">
                            <i class="fas fa-spinner fa-spin"></i> 加载中...
                        </div>
                        <div id="previewContent" class="preview-content"></div>
                        <div id="previewError" class="preview-error" style="display: none;"></div>
                    </div>
                    <div class="preview-modal-footer">
                        <button class="btn btn-secondary" onclick="filePreviewer.close()">关闭</button>
                    </div>
                </div>
            </div>
        `;
        
        // 添加样式
        const style = document.createElement('style');
        style.textContent = `
            .preview-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .preview-modal-overlay {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.7);
                backdrop-filter: blur(4px);
            }
            
            .preview-modal-content {
                position: relative;
                background: white;
                border-radius: 12px;
                width: 90%;
                max-width: 1200px;
                max-height: 90vh;
                display: flex;
                flex-direction: column;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                z-index: 10001;
            }
            
            .preview-modal-header {
                padding: 1.5rem 2rem;
                border-bottom: 1px solid #e0e0e0;
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 12px 12px 0 0;
                gap: 1rem;
            }
            
            .preview-modal-header h3 {
                margin: 0;
                font-size: 1.25rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                flex: 1;
                min-width: 0;
                overflow: hidden;
                max-width: calc(100% - 60px);
            }
            
            .preview-modal-header h3 i {
                flex-shrink: 0;
            }
            
            .preview-modal-header h3 span {
                display: inline-block;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                max-width: 100%;
                min-width: 0;
            }
            
            .preview-modal-close {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                width: 36px;
                height: 36px;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background 0.2s;
                flex-shrink: 0;
                margin-left: auto;
            }
            
            .preview-modal-close:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            
            .preview-modal-body {
                flex: 1;
                padding: 1.5rem;
                overflow-y: auto;
                min-height: 400px;
            }
            
            .preview-loading {
                text-align: center;
                padding: 3rem;
                color: #666;
                font-size: 1.1rem;
            }
            
            .preview-loading i {
                margin-right: 0.5rem;
                font-size: 1.5rem;
            }
            
            .preview-content {
                display: none;
            }
            
            .preview-content.active {
                display: block;
            }
            
            .preview-code {
                background: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 1rem;
                font-family: 'Courier New', 'Consolas', monospace;
                font-size: 0.9rem;
                line-height: 1.6;
                overflow-x: auto;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            
            .preview-image {
                max-width: 100%;
                height: auto;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }
            
            .preview-markdown {
                padding: 1rem;
                line-height: 1.8;
                color: #333;
            }
            
            .preview-markdown h1, .preview-markdown h2, .preview-markdown h3 {
                margin-top: 1.5rem;
                margin-bottom: 1rem;
                color: #2c3e50;
            }
            
            .preview-markdown code {
                background: #f4f4f4;
                padding: 0.2rem 0.4rem;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
            }
            
            .preview-markdown pre {
                background: #f8f9fa;
                padding: 1rem;
                border-radius: 8px;
                overflow-x: auto;
            }
            
            .preview-error {
                padding: 2rem;
                text-align: center;
                color: #dc3545;
                background: #f8d7da;
                border: 1px solid #f5c6cb;
                border-radius: 8px;
            }
            
            .preview-modal-footer {
                padding: 1rem 2rem;
                border-top: 1px solid #e0e0e0;
                display: flex;
                justify-content: flex-end;
                gap: 1rem;
            }
            
            .btn {
                padding: 0.5rem 1.5rem;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 0.95rem;
                transition: all 0.2s;
            }
            
            .btn-secondary {
                background: #6c757d;
                color: white;
            }
            
            .btn-secondary:hover {
                background: #5a6268;
            }
            
            .preview-btn {
                padding: 0.4rem 0.8rem;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 0.85rem;
                display: inline-flex;
                align-items: center;
                gap: 0.4rem;
                transition: all 0.2s;
            }
            
            .preview-btn:hover {
                background: #5568d3;
                transform: translateY(-1px);
            }
            
            .preview-btn i {
                font-size: 0.9rem;
            }
        `;
        
        document.head.appendChild(style);
        
        // 添加到body
        const modal = document.createElement('div');
        modal.innerHTML = modalHTML;
        document.body.appendChild(modal);
        
        this.modal = document.getElementById('filePreviewModal');
    }
    
    async preview(sessionId, layer, filepath, filename) {
        // 确保模态框已初始化
        if (!this.modal) {
            console.error('预览模态框未初始化');
            return;
        }
        
        // 显示模态框
        this.modal.style.display = 'flex';
        document.getElementById('previewFileName').innerHTML = `<i class="fas fa-file"></i><span>${filename || filepath}</span>`;
        
        // 显示加载状态
        document.getElementById('previewLoading').style.display = 'block';
        document.getElementById('previewContent').classList.remove('active');
        document.getElementById('previewError').style.display = 'none';
        
        try {
            // 规范化路径，确保使用正斜杠
            const normalizedPath = filepath.replace(/\\/g, '/');
            // 调用预览API
            const response = await fetch(`/api/preview/${sessionId}/${layer}/${encodeURIComponent(normalizedPath)}`);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || '预览失败');
            }
            
            // 隐藏加载状态
            document.getElementById('previewLoading').style.display = 'none';
            
            // 根据文件类型渲染内容
            const contentDiv = document.getElementById('previewContent');
            contentDiv.innerHTML = '';
            contentDiv.classList.add('active');
            
            if (data.type === 'image') {
                const img = document.createElement('img');
                img.src = `data:${data.mime_type};base64,${data.content}`;
                img.className = 'preview-image';
                img.alt = filename;
                contentDiv.appendChild(img);
            } else if (data.type === 'markdown') {
                // 简单的Markdown渲染（可以使用marked.js等库进行更完整的渲染）
                const mdDiv = document.createElement('div');
                mdDiv.className = 'preview-markdown';
                mdDiv.innerHTML = this.simpleMarkdownRender(data.content);
                contentDiv.appendChild(mdDiv);
            } else if (data.type === 'json') {
                // JSON格式化显示
                const code = document.createElement('pre');
                code.className = 'preview-code';
                try {
                    const jsonObj = JSON.parse(data.content);
                    code.textContent = JSON.stringify(jsonObj, null, 2);
                } catch (e) {
                    code.textContent = data.content;
                }
                contentDiv.appendChild(code);
            } else {
                // XML或其他文本
                const code = document.createElement('pre');
                code.className = 'preview-code';
                code.textContent = data.content;
                contentDiv.appendChild(code);
            }
            
        } catch (error) {
            document.getElementById('previewLoading').style.display = 'none';
            const errorDiv = document.getElementById('previewError');
            errorDiv.textContent = `预览失败: ${error.message}`;
            errorDiv.style.display = 'block';
        }
    }
    
    async previewRepair(docName, jobId, filepath, filename) {
        // 显示模态框
        this.modal.style.display = 'flex';
        document.getElementById('previewFileName').innerHTML = `<i class="fas fa-file"></i><span>${filename || filepath}</span>`;
        
        // 显示加载状态
        document.getElementById('previewLoading').style.display = 'block';
        document.getElementById('previewContent').classList.remove('active');
        document.getElementById('previewError').style.display = 'none';
        
        try {
            // 调用预览API
            const response = await fetch(`/repair/preview/${docName}/${jobId}/${filepath}`);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || '预览失败');
            }
            
            // 隐藏加载状态
            document.getElementById('previewLoading').style.display = 'none';
            
            // 根据文件类型渲染内容
            const contentDiv = document.getElementById('previewContent');
            contentDiv.innerHTML = '';
            contentDiv.classList.add('active');
            
            if (data.type === 'image') {
                const img = document.createElement('img');
                img.src = `data:${data.mime_type};base64,${data.content}`;
                img.className = 'preview-image';
                img.alt = filename;
                contentDiv.appendChild(img);
            } else if (data.type === 'markdown') {
                const mdDiv = document.createElement('div');
                mdDiv.className = 'preview-markdown';
                mdDiv.innerHTML = this.simpleMarkdownRender(data.content);
                contentDiv.appendChild(mdDiv);
            } else if (data.type === 'json') {
                const code = document.createElement('pre');
                code.className = 'preview-code';
                try {
                    const jsonObj = JSON.parse(data.content);
                    code.textContent = JSON.stringify(jsonObj, null, 2);
                } catch (e) {
                    code.textContent = data.content;
                }
                contentDiv.appendChild(code);
            } else {
                const code = document.createElement('pre');
                code.className = 'preview-code';
                code.textContent = data.content;
                contentDiv.appendChild(code);
            }
            
        } catch (error) {
            document.getElementById('previewLoading').style.display = 'none';
            const errorDiv = document.getElementById('previewError');
            errorDiv.textContent = `预览失败: ${error.message}`;
            errorDiv.style.display = 'block';
        }
    }
    
    simpleMarkdownRender(text) {
        // 简单的Markdown渲染（只处理基本格式）
        let html = text
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^\* (.*$)/gim, '<li>$1</li>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');
        
        return `<p>${html}</p>`;
    }
    
    // 预览Markdown内容（直接传入内容，不通过API）
    previewMarkdownContent(sessionId, layer, markdownContent, filename) {
        // 确保模态框已初始化
        if (!this.modal) {
            console.error('预览模态框未初始化');
            return;
        }
        
        // 显示模态框
        this.modal.style.display = 'flex';
        document.getElementById('previewFileName').innerHTML = `<i class="fas fa-file-alt"></i><span>${filename || 'Markdown预览'}</span>`;
        
        // 隐藏加载状态
        document.getElementById('previewLoading').style.display = 'none';
        document.getElementById('previewContent').classList.remove('active');
        document.getElementById('previewError').style.display = 'none';
        
        // 渲染Markdown内容
        const contentDiv = document.getElementById('previewContent');
        contentDiv.innerHTML = '';
        contentDiv.classList.add('active');
        
        const mdDiv = document.createElement('div');
        mdDiv.className = 'preview-markdown';
        mdDiv.innerHTML = this.simpleMarkdownRender(markdownContent);
        contentDiv.appendChild(mdDiv);
    }
    
    close() {
        if (this.modal) {
            this.modal.style.display = 'none';
        }
    }
    
    // 预览整个Layer的所有文件
    async previewLayerAll(sessionId, layer, files, title) {
        // 确保模态框已初始化
        if (!this.modal) {
            console.error('预览模态框未初始化');
            return;
        }
        
        // 显示模态框
        this.modal.style.display = 'flex';
        document.getElementById('previewFileName').innerHTML = `<i class="fas fa-folder-open"></i><span>${title || '预览全部'} (${files.length} 个文件)</span>`;
        
        // 显示加载状态
        document.getElementById('previewLoading').style.display = 'block';
        document.getElementById('previewContent').classList.remove('active');
        document.getElementById('previewError').style.display = 'none';
        
        try {
            // 创建标签页结构
            const contentDiv = document.getElementById('previewContent');
            contentDiv.innerHTML = '';
            
            // 创建标签页导航
            const tabsNav = document.createElement('div');
            tabsNav.className = 'preview-tabs-nav';
            tabsNav.style.cssText = 'display: flex; gap: 0.5rem; border-bottom: 2px solid #e0e0e0; padding: 0.5rem 0; margin-bottom: 1rem; overflow-x: auto;';
            
            // 创建内容区域
            const tabsContent = document.createElement('div');
            tabsContent.className = 'preview-tabs-content';
            tabsContent.style.cssText = 'min-height: 400px;';
            
            // 加载所有文件
            const fileContents = [];
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                try {
                    const normalizedPath = file.path.replace(/\\/g, '/');
                    const response = await fetch(`/api/preview/${sessionId}/${layer}/${encodeURIComponent(normalizedPath)}`);
                    const data = await response.json();
                    
                    if (response.ok) {
                        fileContents.push({
                            file: file,
                            data: data,
                            index: i
                        });
                    }
                } catch (error) {
                    console.error(`加载文件 ${file.name} 失败:`, error);
                }
            }
            
            if (fileContents.length === 0) {
                throw new Error('没有成功加载任何文件');
            }
            
            // 隐藏加载状态
            document.getElementById('previewLoading').style.display = 'none';
            
            // 创建标签页和内容
            fileContents.forEach((fileContent, index) => {
                const file = fileContent.file;
                const data = fileContent.data;
                
                // 创建标签按钮
                const tabBtn = document.createElement('button');
                tabBtn.className = 'preview-tab-btn';
                tabBtn.textContent = file.name;
                tabBtn.style.cssText = index === 0 
                    ? 'padding: 0.5rem 1rem; border: none; border-bottom: 2px solid #667eea; background: transparent; color: #667eea; cursor: pointer; font-weight: 500; white-space: nowrap;'
                    : 'padding: 0.5rem 1rem; border: none; border-bottom: 2px solid transparent; background: transparent; color: #666; cursor: pointer; white-space: nowrap;';
                tabBtn.onclick = () => {
                    // 切换标签页
                    tabsNav.querySelectorAll('.preview-tab-btn').forEach((btn, idx) => {
                        if (idx === index) {
                            btn.style.cssText = 'padding: 0.5rem 1rem; border: none; border-bottom: 2px solid #667eea; background: transparent; color: #667eea; cursor: pointer; font-weight: 500; white-space: nowrap;';
                        } else {
                            btn.style.cssText = 'padding: 0.5rem 1rem; border: none; border-bottom: 2px solid transparent; background: transparent; color: #666; cursor: pointer; white-space: nowrap;';
                        }
                    });
                    tabsContent.querySelectorAll('.preview-tab-pane').forEach((pane, idx) => {
                        pane.style.display = idx === index ? 'block' : 'none';
                    });
                };
                tabsNav.appendChild(tabBtn);
                
                // 创建内容面板
                const tabPane = document.createElement('div');
                tabPane.className = 'preview-tab-pane';
                tabPane.style.display = index === 0 ? 'block' : 'none';
                
                // 渲染文件内容
                if (data.type === 'image') {
                    const img = document.createElement('img');
                    img.src = `data:${data.mime_type};base64,${data.content}`;
                    img.className = 'preview-image';
                    img.alt = file.name;
                    tabPane.appendChild(img);
                } else if (data.type === 'markdown') {
                    const mdDiv = document.createElement('div');
                    mdDiv.className = 'preview-markdown';
                    mdDiv.innerHTML = this.simpleMarkdownRender(data.content);
                    tabPane.appendChild(mdDiv);
                } else if (data.type === 'json') {
                    const code = document.createElement('pre');
                    code.className = 'preview-code';
                    try {
                        const jsonObj = JSON.parse(data.content);
                        code.textContent = JSON.stringify(jsonObj, null, 2);
                    } catch (e) {
                        code.textContent = data.content;
                    }
                    tabPane.appendChild(code);
                } else {
                    const code = document.createElement('pre');
                    code.className = 'preview-code';
                    code.textContent = data.content;
                    tabPane.appendChild(code);
                }
                
                tabsContent.appendChild(tabPane);
            });
            
            contentDiv.appendChild(tabsNav);
            contentDiv.appendChild(tabsContent);
            contentDiv.classList.add('active');
            
        } catch (error) {
            document.getElementById('previewLoading').style.display = 'none';
            const errorDiv = document.getElementById('previewError');
            errorDiv.textContent = `预览失败: ${error.message}`;
            errorDiv.style.display = 'block';
        }
    }
}

// 创建全局实例
const filePreviewer = new FilePreviewer();

// ESC键关闭
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && filePreviewer.modal && filePreviewer.modal.style.display !== 'none') {
        filePreviewer.close();
    }
});



