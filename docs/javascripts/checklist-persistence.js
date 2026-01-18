/**
 * FranChina Checklist Persistence Script
 * 
 * 这个脚本用于保存用户在 "准备清单" 页面勾选的状态。
 * 即使刷新页面或关闭浏览器，勾选的内容也会保留。
 * 
 * 原理：
 * 1. 并没有把数据发给服务器（保护隐私，且不需要后端支持）。
 * 2. 而是利用浏览器的 "LocalStorage"（本地存储）功能，把数据存在用户自己的电脑里。
 */

document.addEventListener("DOMContentLoaded", function () {
    // 1. 定义一个唯一的存储键名（Key）
    // LocalStorage 就像一个大的字典，我们需要一个独特的名字来存我们的数据，
    // 避免跟网站其他功能冲突。
    const STORAGE_KEY = 'franchina_checklist_state';

    // 2. 获取页面上所有的复选框 (checkbox)
    // 这里的选择器 'input[type="checkbox"]' 意思是选中所有类型为 checkbox 的输入框
    const checkboxes = document.querySelectorAll('.md-typeset input[type="checkbox"]');

    // 如果当前页面没有复选框，就直接结束，不做任何事
    if (checkboxes.length === 0) return;

    // 3. 从本地存储加载之前保存的状态
    // localStorage.getItem(...) 会读取字符串，如果没有存过，它是 null
    const savedStateString = localStorage.getItem(STORAGE_KEY);

    // 把读取到的 JSON 字符串转换回 JavaScript 对象 (如果没存过，就设为空对象 {})
    // parsing 意思是 "解析"
    const savedState = savedStateString ? JSON.parse(savedStateString) : {};

    // 4. 遍历页面上每一个复选框，恢复它的状态
    checkboxes.forEach(function (checkbox, index) {
        // 为了区分不同的复选框，我们需要给每个框一个 ID。
        // 因为 Markdown 生成的 HTML 没带 ID，我们就用它的 "位置索引" (这是第几个框)
        // 或者更有鲁棒性的方法是结合所在的标题，但简单起见，这里用 "checklist_item_序号"
        // 注意：如果你改了 Markdown 内容的顺序，保存的状态可能会错位。
        // 但对于静态内容的 checklist，这通常够用了。
        const itemId = 'checklist_item_' + index;

        // 如果我们在 savedState 里找到了这个 ID，说明之前勾选过
        if (savedState[itemId] === true) {
            checkbox.checked = true;
        }

        // 关键修正：移除 disabled 属性，让用户可以点击
        checkbox.disabled = false;

        // 5. 给每个复选框添加 "监听器" (Listener)
        // 当用户点击勾选/取消勾选时，会触发 'change' 事件
        checkbox.addEventListener('change', function () {
            // 更新 savedState 对象
            // 如果 checkbox.checked 是 true，就存 true
            savedState[itemId] = checkbox.checked;

            // 6. 立即把最新的状态保存回浏览器的 LocalStorage
            // JSON.stringify 把对象变成字符串，因为 LocalStorage 只能存字符串
            localStorage.setItem(STORAGE_KEY, JSON.stringify(savedState));
        });
    });

    console.log('FranChina Checklist System: 已加载并就绪。状态将保存在本地。');
});
