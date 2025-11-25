/**
 * 文件上传处理
 * 处理文件选择、验证和上传功能
 */

// ========================================
// 全局变量
// ========================================

let selectedFile = null;
let uploadProgress = 0;

// ========================================
// 初始化
// ========================================

document.addEventListener('DOMContentLoaded', function () {
    console.log('初始化上传模块...');
    initUploadZone();
    initFileInput();
    initUploadButton();
});

// ========================================
// 上传区域初始化
// ========================================

/**
 * 初始化上传区域
 */
function initUploadZone() {
    const uploadZone = document.getElementById('uploadZone');
    if (!uploadZone) {
        console.warn('未找到上传区域');
        return;
    }

    console.log('初始化上传区域');

    // 防止默认拖拽行为
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // 拖拽进入时添加高亮效果
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadZone.addEventListener(eventName, () => {
            uploadZone.classList.add('drag-over');
        }, false);
    });

    // 拖拽离开或放下时移除高亮效果
    ['dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, () => {
            uploadZone.classList.remove('drag-over');
        }, false);
    });

    // 处理文件拖放
    uploadZone.addEventListener('drop', handleDrop, false);

    // 点击上传区域触发文件选择
    uploadZone.addEventListener('click', () => {
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.click();
        }
    });
}

/**
 * 初始化文件输入
 */
function initFileInput() {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput) {
        console.warn('未找到文件输入元素');
        return;
    }

    console.log('初始化文件输入');

    fileInput.addEventListener('change', function (e) {
        if (e.target.files && e.target.files.length > 0) {
            handleFiles(e.target.files);
        }
    });
}

/**
 * 初始化上传按钮
 */
function initUploadButton() {
    const uploadBtn = document.getElementById('uploadBtn');
    if (!uploadBtn) {
        console.warn('未找到上传按钮');
        return;
    }

    console.log('初始化上传按钮');

    uploadBtn.addEventListener('click', uploadFile);
    uploadBtn.disabled = true; // 初始禁用
}

// ========================================
// 事件处理
// ========================================

/**
 * 阻止默认行为
 */
function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

/**
 * 处理文件拖放
 */
function handleDrop(e) {
    console.log('文件拖放');
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

/**
 * 处理文件选择
 */
function handleFiles(files) {
    if (!files || files.length === 0) {
        console.warn('没有选择文件');
        return;
    }

    const file = files[0];
    console.log('选择文件:', file.name, '大小:', file.size);

    // 验证文件
    if (!validateFile(file)) {
        return;
    }

    // 保存选中的文件
    selectedFile = file;

    // 显示文件信息
    displayFileInfo(file);

    // 启用上传按钮
    enableUploadButton();
}

// ========================================
// 文件验证
// ========================================

/**
 * 验证文件
 */
function validateFile(file) {
    // 允许的文件类型
    const allowedTypes = ['pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg'];

    // 最大文件大小 (50MB)
    const maxSize = 50 * 1024 * 1024;

    // 检查文件类型
    const fileExtension = file.name.split('.').pop().toLowerCase();
    if (!allowedTypes.includes(fileExtension)) {
        console.error('不支持的文件类型:', fileExtension);
        showNotification(
            `不支持的文件类型。支持的格式: ${allowedTypes.join(', ')}`,
            'error'
        );
        return false;
    }

    // 检查文件大小
    if (file.size > maxSize) {
        console.error('文件过大:', file.size);
        showNotification('文件大小超过限制（最大50MB）', 'error');
        return false;
    }

    // 检查文件名
    if (file.name.length > 255) {
        console.error('文件名过长');
        showNotification('文件名过长（最多255个字符）', 'error');
        return false;
    }

    console.log('文件验证通过');
    return true;
}

// ========================================
// UI 更新
// ========================================

/**
 * 显示文件信息
 */
function displayFileInfo(file) {
    const fileInfo = document.getElementById('fileInfo');
    if (!fileInfo) {
        console.warn('未找到文件信息容器');
        return;
    }

    // 获取文件图标
    const fileIcon = getFileIcon(file.name);

    // 创建文件信息HTML
    fileInfo.innerHTML = `
        <div class="selected-file">
            <div class="file-icon">
                <i class="fas ${fileIcon}"></i>
            </div>
            <div class="file-details">
                <div class="file-name" title="${file.name}">${file.name}</div>
                <div class="file-size">${formatFileSize(file.size)}</div>
            </div>
            <button class="btn btn-icon" onclick="removeFile()" title="移除文件">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;

    // 显示文件信息
    fileInfo.style.display = 'block';

    // 添加淡入动画
    setTimeout(() => {
        fileInfo.classList.add('show');
    }, 10);
}

/**
 * 启用上传按钮
 */
function enableUploadButton() {
    const uploadBtn = document.getElementById('uploadBtn');
    if (uploadBtn) {
        uploadBtn.disabled = false;
        uploadBtn.style.display = 'inline-flex';

        // 添加动画效果
        uploadBtn.style.opacity = '0';
        uploadBtn.style.transform = 'translateY(10px)';

        setTimeout(() => {
            uploadBtn.style.transition = 'all 0.3s ease';
            uploadBtn.style.opacity = '1';
            uploadBtn.style.transform = 'translateY(0)';
        }, 10);
    }
}

/**
 * 移除文件
 */
function removeFile() {
    console.log('移除文件');

    // 清空选中的文件
    selectedFile = null;

    // 隐藏文件信息
    const fileInfo = document.getElementById('fileInfo');
    if (fileInfo) {
        fileInfo.classList.remove('show');
        setTimeout(() => {
            fileInfo.style.display = 'none';
            fileInfo.innerHTML = '';
        }, 300);
    }

    // 重置文件输入
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.value = '';
    }

    // 禁用上传按钮
    const uploadBtn = document.getElementById('uploadBtn');
    if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.style.display = 'none';
    }
}

// ========================================
// 文件上传
// ========================================

/**
 * 上传文件
 */
async function uploadFile() {
    if (!selectedFile) {
        console.warn('没有选择文件');
        showNotification('请先选择文件', 'warning');
        return;
    }

    console.log('开始上传文件:', selectedFile.name);

    // 获取上传按钮
    const uploadBtn = document.getElementById('uploadBtn');

    // 禁用按钮，添加加载状态
    if (uploadBtn) {
        uploadBtn.classList.add('loading');
        uploadBtn.disabled = true;
    }

    // 显示加载提示
    showLoading('正在上传文件...');

    try {
        // 创建FormData
        const formData = new FormData();
        formData.append('file', selectedFile);

        console.log('发送上传请求到: /api/upload');

        // 发送请求
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        console.log('响应状态:', response.status);
        console.log('响应类型:', response.headers.get('Content-Type'));

        // 检查响应类型
        const contentType = response.headers.get('Content-Type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('服务器返回非JSON响应:', text.substring(0, 200));
            throw new Error('服务器返回了非JSON响应');
        }

        // 解析JSON响应
        const result = await response.json();
        console.log('上传响应:', result);

        // 隐藏加载提示
        hideLoading();

        // 移除按钮加载状态
        if (uploadBtn) {
            uploadBtn.classList.remove('loading');
        }

        // 处理响应
        if (response.ok && result.success) {
            // 上传成功
            console.log('上传成功，会话ID:', result.session_id);
            showNotification('上传成功！正在跳转...', 'success');

            // 保存会话信息到sessionStorage
            sessionStorage.setItem('current_session_id', result.session_id);
            sessionStorage.setItem('current_filename', result.filename);
            sessionStorage.setItem('current_filesize', result.file_size);

            // 延迟跳转，让用户看到成功提示
            setTimeout(() => {
                window.location.href = `/process?session_id=${result.session_id}`;
            }, 1000);

        } else {
            // 上传失败
            const errorMsg = result.error || '上传失败，请重试';
            console.error('上传失败:', errorMsg);
            showNotification(errorMsg, 'error');

            // 重新启用按钮
            if (uploadBtn) {
                uploadBtn.disabled = false;
            }
        }

    } catch (error) {
        // 捕获异常
        console.error('上传错误:', error);

        hideLoading();

        // 移除按钮加载状态
        if (uploadBtn) {
            uploadBtn.classList.remove('loading');
            uploadBtn.disabled = false;
        }

        // 显示错误提示
        showNotification(`上传失败: ${error.message}`, 'error');
    }
}

// ========================================
// 工具函数
// ========================================

/**
 * 根据文件名获取图标
 */
function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();

    const iconMap = {
        'pdf': 'fa-file-pdf',
        'doc': 'fa-file-word',
        'docx': 'fa-file-word',
        'png': 'fa-file-image',
        'jpg': 'fa-file-image',
        'jpeg': 'fa-file-image',
        'txt': 'fa-file-alt',
        'default': 'fa-file'
    };

    return iconMap[ext] || iconMap['default'];
}

/**
 * 格式化文件大小
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';

    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const k = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + units[i];
}

/**
 * 显示通知
 */
function showNotification(message, type = 'info') {
    // 如果main.js中已定义showNotification，使用它
    if (typeof window.showNotification === 'function') {
        window.showNotification(message, type);
        return;
    }

    // 否则使用简单的alert
    console.log(`[${type.toUpperCase()}] ${message}`);

    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${getNotificationIcon(type)}"></i>
        <span>${message}</span>
    `;

    document.body.appendChild(notification);

    // 自动移除
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

/**
 * 获取通知图标
 */
function getNotificationIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'times-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * 显示加载提示
 */
function showLoading(message = '加载中...') {
    // 如果main.js中已定义showLoading，使用它
    if (typeof window.showLoading === 'function') {
        window.showLoading(message);
        return;
    }

    // 否则使用简单的实现
    let overlay = document.getElementById('loadingOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-spinner">
                <div></div>
                <div></div>
                <div></div>
                <div></div>
            </div>
            <div class="loading-text">${message}</div>
        `;
        document.body.appendChild(overlay);
    } else {
        overlay.querySelector('.loading-text').textContent = message;
        overlay.style.display = 'flex';
    }
}

/**
 * 隐藏加载提示
 */
function hideLoading() {
    // 如果main.js中已定义hideLoading，使用它
    if (typeof window.hideLoading === 'function') {
        window.hideLoading();
        return;
    }

    // 否则使用简单的实现
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// ========================================
// 导出到全局作用域
// ========================================

window.uploadModule = {
    uploadFile,
    removeFile,
    validateFile,
    formatFileSize,
    getFileIcon
};

console.log('✓ 上传模块加载完成');