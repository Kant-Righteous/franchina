---
hide:
  - navigation
  - toc
---

# 汇率计算器

<div class="currency-wrapper">
    <!-- 顶部汇率展示 -->
    <div class="rates-hero">
        <div class="rate-card">
            <div class="flag-icon">💶</div>
            <div class="rate-content">
                <div class="rate-label">欧元/人民币</div>
                <div class="rate-value" id="rate-eur">加载中...</div>
            </div>
        </div>
        <div class="rate-card">
            <div class="flag-icon">💵</div>
            <div class="rate-content">
                <div class="rate-label">美元/人民币</div>
                <div class="rate-value" id="rate-usd">加载中...</div>
            </div>
        </div>
    </div>
    
    <div class="update-status" id="lastUpdate">正在获取最新汇率...</div>

    <!-- 计算器区域 -->
    <div class="calc-section">
        <div class="calc-card">
            <div class="input-row">
                <div class="input-group">
                    <label>金额</label>
                    <input type="number" id="amount" value="100" placeholder="0">
                </div>
                
                <div class="currency-picker">
                    <label>持有</label>
                    <div class="select-wrapper">
                        <select id="fromCurrency">
                            <option value="EUR">欧元(EUR)</option>
                            <option value="USD">美元(USD)</option>
                            <option value="CNY">人民币(CNY)</option>
                        </select>
                    </div>
                </div>

                <button id="swapBtn" class="swap-action" title="交换">
                    <span class="swap-icon">⇄</span>
                </button>

                <div class="currency-picker">
                    <label>兑换为</label>
                    <div class="select-wrapper">
                        <select id="toCurrency">
                            <option value="CNY">人民币(CNY)</option>
                            <option value="EUR">欧元(EUR)</option>
                            <option value="USD">美元(USD)</option>
                        </select>
                    </div>
                </div>
            </div>

            <div class="result-display" id="result-container">
                <span class="currency-symbol" id="res-symbol">¥</span>
                <span class="result-number" id="result">--</span>
            </div>
        </div>
    </div>

    <!-- 历史图表区域 -->
    <div class="chart-section">
        <div class="chart-card">
            <div class="chart-header">
                <div class="chart-title">历史走势</div>
                <div class="chart-controls">
                    <div class="pair-selector">
                        <button class="pair-btn active" data-pair="EUR_CNY">EUR/CNY</button>
                        <button class="pair-btn" data-pair="EUR_USD">EUR/USD</button>
                        <button class="pair-btn" data-pair="USD_CNY">USD/CNY</button>
                    </div>
                    <div class="range-selector">
                        <button class="range-btn" data-range="30">1M</button>
                        <button class="range-btn" data-range="180">6M</button>
                        <button class="range-btn active" data-range="1095">3Y</button>
                        <button class="range-btn" data-range="0">ALL</button>
                    </div>
                </div>
            </div>
            <div id="chart-container">
                <div class="chart-tooltip" id="chart-tooltip"></div>
                <div class="chart-x-axis" id="chart-x-axis">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    </div>

    <div class="legal-footer">
        <p>数据来源：ExchangeRate-API </p>
        <p>汇率仅供参考</p>
        <p>免责声明：本工具提供的汇率数据仅供参考，不作为交易依据。请注意，银行和交易所通常会在交易汇率的基础上收取一定的点差（上浮汇率）。使用本数据前请谨慎评估风险。</p>
        <p>本网站不对因使用本数据而产生的任何直接或间接损失承担法律责任。</p>
    </div>
</div>

<style>
    /* 全局变量与重置 */
    .currency-wrapper {
        --c-primary: #2563EB;
        --c-primary-light: #EFF6FF;
        --c-text: #1E293B;
        --c-text-light: #64748B;
        --c-bg-card: #FFFFFF;
        --c-border: #E2E8F0;
        --c-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.08);
        --c-shadow-hover: 0 20px 40px -5px rgba(0, 0, 0, 0.12);
        
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        max-width: 960px; /* 放大最大宽度 */
        margin: 2rem auto;
        padding: 0 1rem;
        color: var(--c-text);
    }

    /* 深色模式适配 */
    [data-md-color-scheme="slate"] .currency-wrapper {
        --c-primary: #60A5FA;
        --c-primary-light: rgba(96, 165, 250, 0.1);
        --c-text: #F1F5F9;
        --c-text-light: #94A3B8;
        --c-bg-card: #1E293B;
        --c-border: #334155;
        --c-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.3);
        --c-shadow-hover: 0 20px 40px -5px rgba(0, 0, 0, 0.4);
    }

    /* 顶部卡片区域 */
    .rates-hero {
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        margin-bottom: 2rem;
        flex-wrap: wrap;
    }

    .rate-card {
        background: var(--c-bg-card);
        border: 1px solid var(--c-border);
        border-radius: 16px;
        padding: 1rem 1.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        box-shadow: var(--c-shadow);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        min-width: 180px;
    }

    .rate-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--c-shadow-hover);
        border-color: var(--c-primary);
    }

    .flag-icon {
        font-size: 2rem;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
    }

    .rate-content {
        display: flex;
        flex-direction: column;
    }

    .rate-label {
        font-size: 0.75rem;
        color: var(--c-text-light);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }

    .rate-value {
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--c-text);
        font-feature-settings: "tnum";
    }

    .update-status {
        text-align: center;
        font-size: 0.8rem;
        color: var(--c-text-light);
        opacity: 0.8;
        margin-bottom: 2rem;
        margin-top: -1rem;
    }

    /* 计算器区域 */
    .calc-section {
        max-width: 100%;
        margin: 0 auto;
    }

    .calc-card {
        background: var(--c-bg-card);
        border-radius: 24px;
        padding: 2.5rem 2rem; /* 减少纵向内边距 */
        box-shadow: var(--c-shadow);
        border: 1px solid var(--c-border);
    }

    .input-row {
        display: flex;
        align-items: flex-start;
        gap: 1.5rem; /* 增加间距 */
        margin-bottom: 2.5rem;
        flex-wrap: wrap;
        justify-content: center; /* 换行时居中对齐 */
    }

    .input-group, .currency-picker {
        flex: 1 1 200px; /* 允许收缩，优先 200px 并可扩展 */
        min-width: 180px; /* 提高最小宽度以更早换行 */
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .currency-wrapper label {
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--c-text-light);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* 现代输入框 */
    input[type="number"], select {
        width: 100%;
        height: 52px; /* 统一高度 */
        padding: 0 0.6rem; /* 纵向内边距由高度与行高控制 */
        border: 2px solid var(--c-border);
        background: var(--c-bg-card);
        border-radius: 12px;
        font-size: 1rem;
        font-weight: 600;
        color: var(--c-text);
        transition: all 0.2s ease;
        appearance: none;
        box-sizing: border-box;
        text-align: center;
        line-height: 48px; /* 垂直居中（考虑边框） */
        font-family: inherit; /* 继承字体 */
    }

    input[type="number"]:focus, select:focus {
        border-color: var(--c-primary);
        outline: none;
        box-shadow: 0 0 0 4px var(--c-primary-light);
    }

    input[type="number"]:hover, select:hover {
        border-color: var(--c-text-light);
    }

    /* 自定义下拉箭头容器 */
    .select-wrapper {
        position: relative;
        width: 100%;
    }
    
    /* 隐藏数字输入框上下按钮 */
    input[type=number]::-webkit-inner-spin-button, 
    input[type=number]::-webkit-outer-spin-button { 
        -webkit-appearance: none; 
        margin: 0; 
    }
    input[type=number] {
        -moz-appearance: textfield;
    }

    /* 交换按钮 */
    .swap-action {
        background: var(--c-primary-light);
        border: none;
        cursor: pointer;
        width: 44px; /* 略小 */
        height: 44px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--c-primary);
        margin-top: 43px; /* 调整为输入框间居中 */
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        flex-shrink: 0;
    }

    .swap-action:hover {
        background: var(--c-primary);
        color: #fff;
        transform: rotate(180deg) scale(1.1);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }

    .swap-icon {
        font-size: 1.2rem;
        line-height: 1;
    }

    /* 结果展示 */
    .result-display {
        text-align: center;
        padding: 1.5rem;
        background: var(--c-primary-light);
        border-radius: 16px;
        border: 1px dashed var(--c-primary);
        display: flex;
        align-items: baseline;
        justify-content: center;
        gap: 0.5rem;
        word-break: break-all; /* 连续数字强制换行 */
        overflow-wrap: anywhere; /* 必要时任意位置换行 */
        flex-wrap: wrap; /* 允许换行 */
    }

    .result-number {
        max-width: 100%; /* 限制为容器宽度 */
        white-space: normal; /* 确保可换行 */
        text-align: center; /* 换行后居中 */
        font-size: clamp(2rem, 12vw, 3.5rem); /* 响应式字号 */
        font-weight: 800;
        background: linear-gradient(135deg, var(--c-primary) 0%, #1E40AF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.1;
        font-feature-settings: "tnum";
    }

    [data-md-color-scheme="slate"] .result-number {
        background: linear-gradient(135deg, #60A5FA 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .currency-symbol {
        font-size: 1.8rem;
        color: var(--c-text-light);
        font-weight: 500;
    }

    /* 页脚 */
    .legal-footer {
        margin-top: 0.25rem;
        text-align: center;
        font-size: 0.3rem;
        color: var(--c-text-light);
        opacity: 0.5;
    }

    .legal-footer p {
        margin: 0.15rem 0;
        line-height: 1.3;
    }

    /* 响应式 */
    @media (max-width: 768px) {
        .currency-wrapper {
            padding: 0 0.25rem; /* 最小化左右内边距 */
        }
        
        .calc-card {
            padding: 1.5rem 0.5rem; /* 最小化左右内边距 */
            background: transparent;
            border: none;
            box-shadow: none;
        }
        
        input[type="number"], select {
            height: 56px; /* 更大的触控高度 */
            font-size: 1.1rem; /* 更大的字号 */
        }

        .input-row {
            flex-direction: column; /* 纵向堆叠 */
            align-items: stretch; /* 子项占满宽度 */
            gap: 0; /* 移除间距，必要时用外边距控制 */
        }
        
        .input-group, .currency-picker {
            width: 100%;
            flex: none; /* 移动端禁用扩展逻辑 */
        }
        
        .result-display {
            background: transparent;
            border: none;
            padding: 0.5rem 0;
            border-radius: 0;
        }

        .swap-action {
            margin: 1rem auto; /* 合理间距并居中 */
            transform: rotate(90deg);
            width: 40px;
            height: 40px;
        }
        
        .swap-action:hover {
            transform: rotate(270deg) scale(1.1);
        }

        /* 字号由 clamp() 在基础样式中控制 */
        
        .currency-symbol {
            font-size: 1.5rem;
        }
    }

    /* 历史记录图表区块 */
    .chart-section {
        margin-top: 2rem;
    }

    /* 图表卡片容器 */
    .chart-card {
        background: var(--c-bg-card);
        border-radius: 24px;
        padding: 1.5rem;
        box-shadow: var(--c-shadow);
        border: 1px solid var(--c-border);
    }

    /* 标题与控件容器 */
    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        flex-wrap: wrap;
        gap: 1rem;
    }

    /* 标题文本 */
    .chart-title {
        font-size: 1.0rem;
        font-weight: 700;
        color: var(--c-text);
    }

    /* 控件区 */
    .chart-controls {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
    }

    /* 币对/区间按钮组 */
    .pair-selector, .range-selector { /* 组容器选择器 */
        display: flex; /* 使用弹性布局 */
        gap: 0.25rem; /* 按钮间距 */
        background: var(--c-primary-light); /* 组底色 */
        border-radius: 8px; /* 组圆角 */
        padding: 0.1rem; /* 组内边距 */
    } /* 组容器结束 */

    /* 币对/区间按钮基础样式 */
    .pair-btn, .range-btn { /* 按钮选择器 */
        padding: 0.4rem 0.8rem; /* 点击热区 */
        border: none; /* 去除边框 */
        background: transparent; /* 透明底色 */
        border-radius: 6px; /* 按钮圆角 */
        font-size: 0.7rem; /* 字号 */
        font-weight: 500; /* 字重 */
        color: var(--c-text-light); /* 文本颜色 */
        cursor: pointer; /* 指针样式 */
        transition: all 0.4s ease; /* 过渡动画 */
    } /* 按钮基础样式结束 */

    /* 悬停仅提升文字色，避免影响布局 */
    .pair-btn:hover, .range-btn:hover { /* 悬停选择器 */
        color: var(--c-primary); /* 悬停文字色 */
    } /* 悬停样式结束 */

    /* 选中态以主色背景提示当前选择 */
    .pair-btn.active, .range-btn.active { /* 选中态选择器 */
        background: var(--c-primary); /* 选中底色 */
        color: #fff; /* 选中文本色 */
    } /* 选中态结束 */

    /* 图表画布容器 */
    #chart-container {
        height: 360px;
        width: 100%;
        position: relative;
        box-sizing: border-box;
    }

    /* 自绘 X 轴标签层 */
    .chart-x-axis {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        height: 12px;
        padding: 0 0.55rem 0.2rem;
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        color: var(--c-text-light);
        font-size: 0.55rem;
        pointer-events: none;
        z-index: 5;
        background: linear-gradient(to top, var(--c-bg-card) 70%, rgba(255,255,255,0));
    }

    /* 深色模式下的 X 轴遮罩 */
    [data-md-color-scheme="slate"] .chart-x-axis {
        background: linear-gradient(to top, var(--c-bg-card) 70%, rgba(0,0,0,0));
    }

    /* 悬停/点击提示框 */
    .chart-tooltip {
        display: none;
        position: absolute;
        background: var(--c-bg-card);
        border: 1px solid var(--c-border);
        border-radius: 8px;
        padding: 0.5rem 0.75rem;
        font-size: 0.8rem;
        box-shadow: var(--c-shadow);
        z-index: 10;
        pointer-events: none;
    }

    /* 移动端适配 */
    @media (max-width: 768px) {
        /* 标题与控件改为纵向排列 */
        .chart-header {
            flex-direction: column;
            align-items: flex-start;
        }

        /* 控件区铺满 */
        .chart-controls {
            width: 100%;
        }

        /* 按钮组布局 */
        .pair-selector {
            width: 100%;
            flex-wrap: nowrap;
            overflow: hidden;
            justify-content: flex-start;
            column-gap: 0.2rem;
        }

        .range-selector {
            width: 100%;
            flex-wrap: wrap;
            overflow: hidden;
            justify-content: flex-start;
            row-gap: 0.25rem;
        }

        /* 币对按钮保持单行显示，缩小字号与内边距 */
        .pair-btn {
            flex: 0 0 auto; 
            text-align: center;
            white-space: nowrap;
            font-size: 0.7rem;
            padding: 0.2rem 0.4rem;
        }

        /* 区间按钮可等分换行，保证可点击面积 */
        .range-btn {
            flex: 1 1 auto;
            text-align: center;
            font-size: 0.7rem;
            padding: 0.2rem 0.4rem;
        }

        /* 图表高度在移动端收紧 */
        #chart-container {
            height: 300px;
        }

        /* 移动端卡片去除外层装饰 */
        .chart-card {
            padding: 1rem 0.5rem;
            background: transparent;
            border: none;
            box-shadow: none;
        }
    }
</style>

<script>
    (function() {
        // 作用域隔离，避免污染全局命名空间
        const els = {
            rateEur: document.getElementById('rate-eur'),
            rateUsd: document.getElementById('rate-usd'),
            lastUpdate: document.getElementById('lastUpdate'),
            amount: document.getElementById('amount'),
            from: document.getElementById('fromCurrency'),
            to: document.getElementById('toCurrency'),
            swap: document.getElementById('swapBtn'),
            result: document.getElementById('result'),
            resSymbol: document.getElementById('res-symbol')
        };
        
        let rateData = {};

        async function init() {
            try {
                // 添加时间戳避免缓存
                const resp = await fetch('/assets/littleTools/CurrencyCalculator/rates.json?v=' + Date.now());
                if (!resp.ok) throw new Error('网络错误');
                const data = await resp.json();
                
                if (data.result === 'success') {
                    rateData = data.rates;
                    updateHeader(data.time_last_update_utc);
                    calculate();
                }
            } catch (e) {
                console.error(e);
                els.lastUpdate.textContent = '无法获取最新汇率数据';
            }
        }

        function updateHeader(timeStr) {
            // 计算基础汇率（1 外币 = ? 人民币）
            if (rateData.CNY && rateData.EUR && rateData.USD) {
                const eurToCny = rateData.CNY / rateData.EUR;
                const usdToCny = rateData.CNY / rateData.USD;
                
                els.rateEur.textContent = eurToCny.toFixed(4);
                els.rateUsd.textContent = usdToCny.toFixed(4);
            }
            
            // 更新时间
            if (timeStr) {
                const date = new Date(timeStr);
                els.lastUpdate.textContent = '更新时间: ' + date.toLocaleString('zh-CN', {
                    year: 'numeric',
                     month: '2-digit',
                    day: '2-digit'
                });
            }
        }

        function calculate() {
            if (!rateData.CNY) return; // 尚未就绪

            const amount = parseFloat(els.amount.value);
            if (isNaN(amount)) {
                els.result.textContent = '---';
                return;
            }

            const fromCode = els.from.value;
            const toCode = els.to.value;

            // 算法：金额 / 汇率(源) * 汇率(目标)
            // （许多接口以欧元为基准，这里汇率相对基准货币）
            // 输入(源) -> 基准 -> 输出(目标)
            // 基准值 = 金额 / 源汇率
            // 目标值 = 基准值 * 目标汇率
            
            const valInBase = amount / rateData[fromCode];
            const result = valInBase * rateData[toCode];

            // 展示结果
            els.result.textContent = result.toLocaleString('zh-CN', {
                maximumFractionDigits: 2,
                minimumFractionDigits: 2
            });
            
            // 货币符号
            const symbols = { 'CNY': '¥', 'EUR': '€', 'USD': '$' };
            els.resSymbol.textContent = symbols[toCode] || '';
        }

        // 事件监听
        els.amount.addEventListener('input', calculate);
        els.from.addEventListener('change', calculate);
        els.to.addEventListener('change', calculate);
        
        els.swap.addEventListener('click', () => {
            const t = els.from.value;
            els.from.value = els.to.value;
            els.to.value = t;
            
            // 交换图标旋转动画
            const icon = els.swap.querySelector('.swap-icon');
            if(icon) {
                 icon.style.transition = 'transform 0.3s';
                 icon.style.transform = 'rotate(180deg)';
                 setTimeout(() => icon.style.transform = 'none', 300);
            }
            
            calculate();
        });

        // 启动
        init();
    })();

    // ========== 历史曲线图模块 ==========
    (function() {
        // 图表实例与数据状态
        let chart = null;
        let lineSeries = null;
        let historyData = null;
        let currentPair = 'EUR_CNY';
        let currentRange = 1095; // 3年默认

        // DOM 引用
        const container = document.getElementById('chart-container');
        const tooltip = document.getElementById('chart-tooltip');
        const xAxis = document.getElementById('chart-x-axis');
        const pairBtns = document.querySelectorAll('.pair-btn');
        const rangeBtns = document.querySelectorAll('.range-btn');
        let tooltipLocked = false;
        const axisHeight = 12;
        let currentFilteredData = [];

        // 标准化轻量图表的时间字段，统一为 YYYY-MM-DD
        function normalizeDate(time) {
            if (typeof time === 'string') return time;
            if (typeof time === 'number') {
                const date = new Date(time * 1000);
                if (Number.isNaN(date.getTime())) return '';
                return date.toISOString().split('T')[0];
            }
            if (time && typeof time === 'object' && 'year' in time) {
                const month = String(time.month).padStart(2, '0');
                const day = String(time.day).padStart(2, '0');
                return `${time.year}-${month}-${day}`;
            }
            return '';
        }

        // 根据刻度级别输出更友好的时间点展示
        function formatTickMark(time, tickMarkType) {
            const dateStr = normalizeDate(time);
            if (!dateStr) return '';
            if (typeof LightweightCharts === 'undefined' || !LightweightCharts.TickMarkType) {
                return dateStr;
            }
            if (tickMarkType == null) {
                return dateStr;
            }
            const parts = dateStr.split('-');
            const year = parts[0];
            const month = parts[1];
            const day = parts[2];
            if (tickMarkType === LightweightCharts.TickMarkType.Year) {
                return year;
            }
            if (tickMarkType === LightweightCharts.TickMarkType.Month) {
                return `${year}-${month}`;
            }
            return `${month}-${day}`;
        }

        // 统一获取不同序列返回值中的数值字段
        function getSeriesValue(seriesData) {
            if (seriesData == null) return null;
            if (typeof seriesData === 'number') return seriesData;
            if (typeof seriesData === 'object') {
                if ('value' in seriesData && Number.isFinite(seriesData.value)) return seriesData.value;
                if ('close' in seriesData && Number.isFinite(seriesData.close)) return seriesData.close;
            }
            return null;
        }

        // 更新悬停/点击时的时间戳提示位置与内容
        function updateTooltip(param, lockState) {
            if (!tooltip) return;
            if (!param || !param.time || !param.point || !lineSeries) {
                if (!lockState) tooltip.style.display = 'none';
                return;
            }
            const seriesData = param.seriesData.get(lineSeries);
            const value = getSeriesValue(seriesData);
            if (value == null) {
                if (!lockState) tooltip.style.display = 'none';
                return;
            }
            const dateStr = normalizeDate(param.time);
            if (!dateStr) {
                if (!lockState) tooltip.style.display = 'none';
                return;
            }
            tooltip.innerHTML = `${dateStr}<br>${value.toFixed(4)}`;
            tooltip.style.display = 'block';

            const containerWidth = container.clientWidth;
            const containerHeight = container.clientHeight;
            const tooltipWidth = tooltip.offsetWidth;
            const tooltipHeight = tooltip.offsetHeight;
            let left = param.point.x + 12;
            let top = param.point.y + 12;
            if (left + tooltipWidth > containerWidth) left = param.point.x - tooltipWidth - 12;
            if (left < 0) left = 0;
            if (top + tooltipHeight > containerHeight) top = param.point.y - tooltipHeight - 12;
            if (top < 0) top = 0;
            tooltip.style.left = `${left}px`;
            tooltip.style.top = `${top}px`;
        }

        // 更新自绘 X 轴标签
        function updateXAxis(data) {
            if (!xAxis) return;
            const labels = xAxis.querySelectorAll('span');
            if (!data || data.length === 0 || labels.length < 3) {
                xAxis.style.display = 'none';
                return;
            }
            const start = data[0];
            const end = data[data.length - 1];
            const mid = data[Math.floor(data.length / 2)];
            labels[0].textContent = normalizeDate(start.time);
            labels[1].textContent = normalizeDate(mid.time);
            labels[2].textContent = normalizeDate(end.time);
            xAxis.style.display = 'flex';
        }

        // 获取当前可视区间的数据切片
        function getVisibleRangeData(data) {
            if (!chart || !data || data.length === 0) return data;
            const range = chart.timeScale().getVisibleRange();
            if (!range) return data;
            const from = normalizeDate(range.from);
            const to = normalizeDate(range.to);
            if (!from || !to) return data;
            let startIndex = data.findIndex(d => d.time >= from);
            if (startIndex < 0) startIndex = 0;
            let endIndex = -1;
            for (let i = data.length - 1; i >= 0; i -= 1) {
                if (data[i].time <= to) {
                    endIndex = i;
                    break;
                }
            }
            if (endIndex < 0) endIndex = data.length - 1;
            if (startIndex > endIndex) return data;
            return data.slice(startIndex, endIndex + 1);
        }

        // 根据可视区间刷新 X 轴
        function updateXAxisByRange() {
            updateXAxis(getVisibleRangeData(currentFilteredData));
        }

        // 由 EUR/CNY 与 EUR/USD 合成 USD/CNY 序列
        function buildUsdCny(data) {
            if (!data || !Array.isArray(data.EUR_CNY) || !Array.isArray(data.EUR_USD)) return;

            const usdMap = new Map(data.EUR_USD.map(item => [item.date, item.rate]));
            const usdCny = [];

            data.EUR_CNY.forEach(item => {
                const usdRate = usdMap.get(item.date);
                if (!usdRate) return;
                const rate = item.rate / usdRate;
                if (Number.isFinite(rate)) {
                    usdCny.push({ date: item.date, rate: rate });
                }
            });

            if (usdCny.length > 0) {
                data.USD_CNY = usdCny;
            }
        }

        // 加载历史数据并初始化图表
        async function loadHistoryData() {
            try {
                const resp = await fetch('/assets/littleTools/CurrencyCalculator/history.json?v=' + Date.now());
                if (!resp.ok) throw new Error('无法加载历史数据');
                historyData = await resp.json();
                buildUsdCny(historyData);
                initChart();
                renderChart();
            } catch(e) {
                console.error('图表错误:', e);
                container.innerHTML = '<div style="padding:2rem;text-align:center;color:#888;">无法加载历史数据</div>';
            }
        }

        // 初始化图表，必要时动态加载库
        function initChart() {
            if (!container || typeof LightweightCharts === 'undefined') {
                // 未加载 LightweightCharts，使用兜底加载
                loadLightweightCharts();
                return;
            }
            createChart();
        }

        // 动态加载 lightweight-charts
        function loadLightweightCharts() {
            const script = document.createElement('script');
            script.src = 'https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js';
            script.onload = createChart;
            document.head.appendChild(script);
        }

        // 创建图表并配置主题与交互
        function createChart() {
            if (!container || chart) return;

            // 从 CSS 变量获取颜色
            const isDark = document.documentElement.getAttribute('data-md-color-scheme') === 'slate';
            const bgColor = isDark ? '#1E293B' : '#FFFFFF';
            const textColor = isDark ? '#94A3B8' : '#64748B';
            const lineColor = isDark ? '#60A5FA' : '#2563EB';
            const gridColor = isDark ? '#334155' : '#E2E8F0';
            const isMobile = window.matchMedia('(max-width: 768px)').matches;
            const layoutOptions = {
                background: { type: 'solid', color: bgColor },
                textColor: textColor,
            };
            if (isMobile) {
                // 移动端缩小字号以减少纵轴占用
                layoutOptions.fontSize = 10;
            }
            const rightPriceScaleOptions = {
                borderColor: gridColor,
                borderVisible: true,
            };
            if (isMobile) {
                // 移动端收窄纵轴宽度并保持完整标签
                rightPriceScaleOptions.minimumWidth = 44;
                rightPriceScaleOptions.entireTextOnly = true;
            }

            const chartHeight = Math.max(220, container.clientHeight - axisHeight);
            chart = LightweightCharts.createChart(container, {
                width: container.clientWidth,
                height: chartHeight || 320,
                layout: layoutOptions,
                grid: {
                    vertLines: { color: gridColor },
                    horzLines: { color: gridColor },
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                },
                rightPriceScale: rightPriceScaleOptions,
                timeScale: {
                    visible: true,
                    borderColor: gridColor,
                    borderVisible: true,
                    timeVisible: false,
                    secondsVisible: false,
                    rightOffset: 5,
                    barSpacing: 6,
                    minBarSpacing: 3,
                    ticksVisible: true,
                    fixLeftEdge: true,
                    fixRightEdge: true,
                },
                handleScroll: { mouseWheel: true, pressedMouseMove: true },
                handleScale: { mouseWheel: true, pinch: true },
            });

            // 面积曲线序列
            lineSeries = chart.addAreaSeries({
                lineColor: lineColor,
                topColor: isDark ? 'rgba(96, 165, 250, 0.3)' : 'rgba(37, 99, 235, 0.2)',
                bottomColor: isDark ? 'rgba(96, 165, 250, 0.0)' : 'rgba(37, 99, 235, 0.0)',
                lineWidth: 2,
                priceFormat: { type: 'price', precision: 4, minMove: 0.0001 },
            });

            // 鼠标移动：展示时间戳提示
            chart.subscribeCrosshairMove(param => {
                if (tooltipLocked) return;
                updateTooltip(param, false);
            });

            // 鼠标点击：锁定时间戳提示，再次点击空白取消
            chart.subscribeClick(param => {
                if (!param || !param.time) {
                    tooltipLocked = false;
                    if (tooltip) tooltip.style.display = 'none';
                    return;
                }
                tooltipLocked = true;
                updateTooltip(param, true);
            });
            chart.timeScale().subscribeVisibleTimeRangeChange(() => {
                updateXAxisByRange();
            });

            // 监听容器尺寸变化并刷新图表
            const resizeObserver = new ResizeObserver(() => {
                if (chart && container) {
                    const nextHeight = Math.max(220, container.clientHeight - axisHeight);
                    chart.applyOptions({ width: container.clientWidth, height: nextHeight });
                    updateXAxisByRange();
                }
            });
            resizeObserver.observe(container);

            // 主题切换时重建图表以应用颜色
            const themeObserver = new MutationObserver(() => {
                if (chart) {
                    chart.remove();
                    chart = null;
                    lineSeries = null;
                    createChart();
                    renderChart();
                }
            });
            themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-md-color-scheme'] });

            renderChart();
        }

        // 根据币对与时间区间渲染图表
        function renderChart() {
            if (!historyData || !lineSeries) return;

            const pairData = historyData[currentPair] || [];
            if (pairData.length === 0) return;

            const filteredData = currentRange === 0
                ? pairData.map(d => ({
                    time: d.date,
                    value: d.rate
                }))
                : (() => {
                    const now = new Date();
                    const cutoffDate = new Date(now);
                    cutoffDate.setDate(cutoffDate.getDate() - currentRange);
                    const cutoffStr = cutoffDate.toISOString().split('T')[0];
                    return pairData
                        .filter(d => d.date >= cutoffStr)
                        .map(d => ({
                            time: d.date,
                            value: d.rate
                        }));
                })();

            if (filteredData.length > 0) {
                currentFilteredData = filteredData;
                lineSeries.setData(filteredData);
                chart.timeScale().fitContent();
                tooltipLocked = false;
                if (tooltip) tooltip.style.display = 'none';
                updateXAxisByRange();
            }
        }

        // 币对切换事件
        pairBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                pairBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentPair = btn.dataset.pair;
                renderChart();
            });
        });

        // 时间区间切换事件
        rangeBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                rangeBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentRange = parseInt(btn.dataset.range, 10);
                renderChart();
            });
        });

        // 初始化入口
        loadHistoryData();
    })();
</script>
