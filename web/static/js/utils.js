/**
 * 工具函数库
 */

// ========================================
// 文件处理
// ========================================

/**
 * 验证文件类型
 */
function validateFileType(file, allowedTypes) {
    const fileExtension = file.name.split('.').pop().toLowerCase();
    return allowedTypes.includes(fileExtension);
}

/**
 * 验证文件大小
 */
function validateFileSize(file, maxSize) {
    return file.size <= maxSize;
}

/**
 * 获取文件扩展名
 */
function getFileExtension(filename) {
    return filename.split('.').pop().toLowerCase();
}

/**
 * 格式化时间戳
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// ========================================
// API请求封装
// ========================================

/**
 * API请求类
 */
class API {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
    }

    /**
     * GET请求
     */
    async get(endpoint, options = {}) {
        return this.request('GET', endpoint, null, options);
    }

    /**
     * POST请求
     */
    async post(endpoint, data, options = {}) {
        return this.request('POST', endpoint, data, options);
    }

    /**
     * PUT请求
     */
    async put(endpoint, data, options = {}) {
        return this.request('PUT', endpoint, data, options);
    }

    /**
     * DELETE请求
     */
    async delete(endpoint, options = {}) {
        return this.request('DELETE', endpoint, null, options);
    }

    /**
     * 通用请求方法
     */
    async request(method, endpoint, data = null, options = {}) {
        const url = `${this.baseURL}${endpoint}`;

        const config = {
            method,
            headers: {
                ...options.headers
            },
            ...options
        };

        // 如果有数据且不是FormData，设置JSON头
        if (data && !(data instanceof FormData)) {
            config.headers['Content-Type'] = 'application/json';
            config.body = JSON.stringify(data);
        } else if (data) {
            config.body = data;
        }

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // 如果是下载文件，返回blob
            if (options.responseType === 'blob') {
                return await response.blob();
            }

            // 默认返回JSON
            return await response.json();

        } catch (error) {
            console.error('API请求失败:', error);
            throw error;
        }
    }
}

// 创建全局API实例
const api = new API();

// ========================================
// 本地存储管理
// ========================================

/**
 * 本地存储管理类
 */
class Storage {
    /**
     * 保存数据
     */
    static set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.error('存储失败:', e);
            return false;
        }
    }

    /**
     * 获取数据
     */
    static get(key, defaultValue = null) {
        try {
            const value = localStorage.getItem(key);
            return value ? JSON.parse(value) : defaultValue;
        } catch (e) {
            console.error('读取失败:', e);
            return defaultValue;
        }
    }

    /**
     * 删除数据
     */
    static remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('删除失败:', e);
            return false;
        }
    }

    /**
     * 清空所有数据
     */
    static clear() {
        try {
            localStorage.clear();
            return true;
        } catch (e) {
            console.error('清空失败:', e);
            return false;
        }
    }
}

// ========================================
// 会话历史管理
// ========================================

/**
 * 会话历史管理
 */
class SessionHistory {
    constructor() {
        this.storageKey = 'dita_converter_history';
        this.maxItems = 10;
    }

    /**
     * 获取历史记录
     */
    getHistory() {
        return Storage.get(this.storageKey, []);
    }

    /**
     * 添加会话
     */
    addSession(session) {
        const history = this.getHistory();

        // 添加到开头
        history.unshift({
            ...session,
            timestamp: Date.now()
        });

        // 限制数量
        if (history.length > this.maxItems) {
            history.splice(this.maxItems);
        }

        Storage.set(this.storageKey, history);
    }

    /**
     * 删除会话
     */
    removeSession(sessionId) {
        const history = this.getHistory();
        const filtered = history.filter(s => s.session_id !== sessionId);
        Storage.set(this.storageKey, filtered);
    }

    /**
     * 清空历史
     */
    clearHistory() {
        Storage.remove(this.storageKey);
    }
}

// 创建全局历史管理实例
const sessionHistory = new SessionHistory();

// ========================================
// 剪贴板操作
// ========================================

/**
 * 复制文本到剪贴板
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('已复制到剪贴板', 'success');
        return true;
    } catch (error) {
        console.error('复制失败:', error);
        showNotification('复制失败', 'error');
        return false;
    }
}

// ========================================
// 下载文件
// ========================================

/**
 * 下载文件
 */
function downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * 从Blob下载文件
 */
function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    downloadFile(url, filename);
    window.URL.revokeObjectURL(url);
}

// ========================================
// 动画工具
// ========================================

/**
 * 平滑滚动到元素
 */
function scrollToElement(element, offset = 0) {
    const targetPosition = element.getBoundingClientRect().top + window.pageYOffset - offset;

    window.scrollTo({
        top: targetPosition,
        behavior: 'smooth'
    });
}

/**
 * 淡入动画
 */
function fadeIn(element, duration = 300) {
    element.style.opacity = 0;
    element.style.display = 'block';

    let start = null;

    function animate(timestamp) {
        if (!start) start = timestamp;
        const progress = timestamp - start;

        element.style.opacity = Math.min(progress / duration, 1);

        if (progress < duration) {
            requestAnimationFrame(animate);
        }
    }

    requestAnimationFrame(animate);
}

/**
 * 淡出动画
 */
function fadeOut(element, duration = 300) {
    let start = null;
    const initialOpacity = parseFloat(window.getComputedStyle(element).opacity);

    function animate(timestamp) {
        if (!start) start = timestamp;
        const progress = timestamp - start;

        element.style.opacity = initialOpacity * (1 - progress / duration);

        if (progress < duration) {
            requestAnimationFrame(animate);
        } else {
            element.style.display = 'none';
        }
    }

    requestAnimationFrame(animate);
}

// ========================================
// 表单验证
// ========================================

/**
 * 验证邮箱
 */
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * 验证URL
 */
function validateURL(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

// ========================================
// 导出
// ========================================

window.utils = {
    formatFileSize,
    validateFileType,
    validateFileSize,
    getFileExtension,
    formatTimestamp,
    api,
    Storage,
    sessionHistory,
    copyToClipboard,
    downloadFile,
    downloadBlob,
    scrollToElement,
    fadeIn,
    fadeOut,
    validateEmail,
    validateURL
};