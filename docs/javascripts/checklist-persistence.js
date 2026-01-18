/**
 * FranChina Checklist Persistence Script
 * 
 * 功能：
 * 1. 自动加载和保存复选框状态 (LocalStorage)
 * 2. 移除复选框的 disabled 属性，使其可交互
 * 3. 适配 MkDocs Material 的 Instant Loading (SPA 模式)
 * 
 * 修复说明：
 * MkDocs Material 的 Instant Loading 会替换整个 .md-content 容器，
 * 导致之前的 MutationObserver 失效。
 * 
 * 解决方案：
 * 1. 观察 document.body 而不是 .md-content
 * 2. 监听 URL 变化（popstate + hashchange）
 * 3. 使用短暂的轮询确保 DOM 已经渲染
 */

(function () {
    const STORAGE_KEY = 'franchina_checklist_state';

    // 核心初始化函数
    function initChecklist() {
        const checkboxes = document.querySelectorAll('.md-typeset .task-list-item input[type="checkbox"]');

        // 如果当前页面没有复选框，直接返回
        if (checkboxes.length === 0) {
            return false;
        }

        // 检查是否已经初始化过（防止重复绑定事件）
        if (checkboxes[0].dataset.checklistInitialized === 'true') {
            return true; // 已初始化
        }

        // 加载状态
        const savedStateString = localStorage.getItem(STORAGE_KEY);
        const savedState = savedStateString ? JSON.parse(savedStateString) : {};

        checkboxes.forEach(function (checkbox, index) {
            const itemId = 'checklist_item_' + index;

            // 1. 恢复状态
            if (savedState[itemId] === true) {
                checkbox.checked = true;
            }

            // 2. 激活复选框 (移除 disabled)
            checkbox.disabled = false;

            // 3. 标记为已初始化
            checkbox.dataset.checklistInitialized = 'true';

            // 4. 绑定事件：状态改变时保存
            checkbox.addEventListener('change', function () {
                savedState[itemId] = checkbox.checked;
                localStorage.setItem(STORAGE_KEY, JSON.stringify(savedState));
            });
        });

        console.log('FranChina Checklist: 已初始化 ' + checkboxes.length + ' 个检查项');
        return true;
    }

    // 使用轮询确保 DOM 已经渲染
    // 这是最可靠的方法，因为 Instant Loading 的渲染时机不确定
    function initWithRetry(maxRetries, delay) {
        let retries = 0;

        function attempt() {
            const success = initChecklist();
            if (!success && retries < maxRetries) {
                retries++;
                setTimeout(attempt, delay);
            }
        }

        attempt();
    }

    // 监听 URL 变化（Instant Loading 会触发 popstate 或自定义事件）
    // 方案 1：使用 MutationObserver 监听整个 body
    function setupBodyObserver() {
        const observer = new MutationObserver(function (mutations) {
            // 检查是否有新的 task-list-item 被添加
            for (const mutation of mutations) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // 使用 requestAnimationFrame 确保 DOM 更新完成
                    requestAnimationFrame(function () {
                        initWithRetry(5, 100);
                    });
                    break;
                }
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    // 方案 2：监听 URL 变化
    function setupURLListener() {
        let lastURL = location.href;

        // 使用 setInterval 轮询检测 URL 变化
        // 这是最可靠的方法，因为 Instant Loading 可能不触发 popstate
        setInterval(function () {
            if (location.href !== lastURL) {
                lastURL = location.href;
                // URL 变化后，等待一小段时间让 DOM 渲染完成
                setTimeout(function () {
                    initWithRetry(10, 100);
                }, 200);
            }
        }, 100);
    }

    // 初始化
    function init() {
        // 首次加载时初始化
        initWithRetry(10, 100);

        // 设置 URL 变化监听（主要方案）
        setupURLListener();

        // 设置 body 观察者作为备用方案
        setupBodyObserver();
    }

    // 页面加载完成后启动
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
