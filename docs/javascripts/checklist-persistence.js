/**
 * FranChina Checklist Persistence Script
 * 
 * 功能：
 * 1. 自动加载和保存复选框状态 (LocalStorage)
 * 2. 移除复选框的 disabled 属性，使其可交互
 * 3. 适配 MkDocs Material 的 Instant Loading (SPA 模式)
 */

(function () {
    const STORAGE_KEY = 'franchina_checklist_state';

    // 核心初始化函数
    function initChecklist() {
        // 修正选择器：使用 .task-list-item 覆盖 ol 和 ul
        const checkboxes = document.querySelectorAll('.md-typeset .task-list-item input[type="checkbox"]');

        // 如果当前页面没有复选框，直接返回
        if (checkboxes.length === 0) return;

        // 加载状态
        const savedStateString = localStorage.getItem(STORAGE_KEY);
        const savedState = savedStateString ? JSON.parse(savedStateString) : {};

        checkboxes.forEach(function (checkbox, index) {
            // 生成唯一 ID (基于索引)
            // 注意：如果列表内容发生增减，索引对应的项会改变，这是静态生成站点的局限性。
            const itemId = 'checklist_item_' + index;

            // 1. 恢复状态
            if (savedState[itemId] === true) {
                checkbox.checked = true;
            }

            // 2. 激活复选框 (移除 disabled)
            checkbox.disabled = false;

            // 3. 绑定事件：状态改变时保存
            checkbox.addEventListener('change', function () {
                savedState[itemId] = checkbox.checked;
                localStorage.setItem(STORAGE_KEY, JSON.stringify(savedState));
            });
        });

        console.log('FranChina Checklist: 已初始化 ' + checkboxes.length + ' 个检查项 (Instant Loading 适配版)');
    }

    // 事件监听
    // 1. 首次加载
    document.addEventListener("DOMContentLoaded", initChecklist);

    // 2. 适配 MkDocs Material 的 Instant Loading (页面切换不刷新)
    // 当页面通过 AJAX 切换时，DOMContentLoaded 不会触发，而是触发 DOMContentSwitch
    document.addEventListener("DOMContentSwitch", initChecklist);

})();
