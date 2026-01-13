---
hide:
  - navigation
  - toc
---

# 汇率计算器

<div class="currency-wrapper">
    <!-- Top Rates Display -->
    <div class="rates-hero">
        <div class="rate-card">
            <div class="flag-icon">💶</div>
            <div class="rate-content">
                <div class="rate-label">欧元/人民币</div>
                <div class="rate-value" id="rate-eur">loading...</div>
            </div>
        </div>
        <div class="rate-card">
            <div class="flag-icon">💵</div>
            <div class="rate-content">
                <div class="rate-label">美元/人民币</div>
                <div class="rate-value" id="rate-usd">loading...</div>
            </div>
        </div>
    </div>
    
    <div class="update-status" id="lastUpdate">正在获取最新汇率...</div>

    <!-- Calculator Section -->
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

    <div class="legal-footer">
        <p>数据来源：ExchangeRate-API | 仅供参考</p>
        <p style="margin-top: 0.5rem; max-width: 600px; margin-left: auto; margin-right: auto; line-height: 1.5;">免责声明：本工具提供的汇率数据仅供参考，不作为交易依据。本网站不对因使用本数据而产生的任何直接或间接损失承担法律责任。</p>
    </div>
</div>

<style>
    /* Global Variables & Reset */
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
        max-width: 960px; /* Increased max-width */
        margin: 2rem auto;
        padding: 0 1rem;
        color: var(--c-text);
    }

    /* Dark Mode Adaptation */
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

    /* Hero Section - Rate Cards */
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

    /* Calculator Section */
    .calc-section {
        max-width: 100%;
        margin: 0 auto;
    }

    .calc-card {
        background: var(--c-bg-card);
        border-radius: 24px;
        padding: 2.5rem 2rem; /* Reduced vertical padding */
        box-shadow: var(--c-shadow);
        border: 1px solid var(--c-border);
    }

    .input-row {
        display: flex;
        align-items: flex-start;
        gap: 1.5rem; /* Increased gap */
        margin-bottom: 2.5rem;
        flex-wrap: wrap;
        justify-content: center; /* Center items when wrapping */
    }

    .input-group, .currency-picker {
        flex: 1 1 200px; /* Allow shrinking but prefer 200px, grow if space */
        min-width: 180px; /* Increased min-width to force wrap earlier */
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

    /* Modern Inputs */
    input[type="number"], select {
        width: 100%;
        height: 52px; /* Fixed height for consistency */
        padding: 0 0.6rem; /* Vertical padding handled by line-height/height interaction or flex */
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
        line-height: 48px; /* Vertically center text (accounting for border) */
        font-family: inherit; /* Ensure same font family */
    }

    input[type="number"]:focus, select:focus {
        border-color: var(--c-primary);
        outline: none;
        box-shadow: 0 0 0 4px var(--c-primary-light);
    }

    input[type="number"]:hover, select:hover {
        border-color: var(--c-text-light);
    }

    /* Custom Select Arrow */
    .select-wrapper {
        position: relative;
        width: 100%;
    }
    
    /* Remove number input spinner */
    input[type=number]::-webkit-inner-spin-button, 
    input[type=number]::-webkit-outer-spin-button { 
        -webkit-appearance: none; 
        margin: 0; 
    }
    input[type=number] {
        -moz-appearance: textfield;
    }

    /* Swap Button */
    .swap-action {
        background: var(--c-primary-light);
        border: none;
        cursor: pointer;
        width: 44px; /* Slightly smaller */
        height: 44px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--c-primary);
        margin-top: 43px; /* Adjusted to center between inputs */
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

    /* Result Display */
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
        word-break: break-all; /* Prevent overflow of long numbers */
        flex-wrap: wrap; /* Allow wrapping if needed */
    }

    .result-number {
        font-size: 3.5rem; /* Slightly reduced */
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

    /* Footer */
    .legal-footer {
        margin-top: 2.5rem;
        text-align: center;
        font-size: 0.75rem;
        color: var(--c-text-light);
        opacity: 0.6;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .currency-wrapper {
            padding: 0 0.5rem;
        }
        
        .calc-card {
            padding: 1.5rem;
        }

        .input-row {
            flex-direction: column; /* Stack vertically */
            align-items: stretch; /* Full width items */
            gap: 0; /* Remove gap, handle via margins if needed */
        }
        
        .input-group, .currency-picker {
            width: 100%;
            flex: none; /* Disable flex growing logic on mobile */
        }
        
        .swap-action {
            margin: 1rem auto; /* Proper spacing, centered */
            transform: rotate(90deg);
            width: 40px;
            height: 40px;
        }
        
        .swap-action:hover {
            transform: rotate(270deg) scale(1.1);
        }

        .result-number {
            font-size: 2.5rem;
        }
        
        .currency-symbol {
            font-size: 1.5rem;
        }
    }
</style>

<script>
    (function() {
        // Scoping to prevent global namespace pollution
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
                // Fetch with timestamp to avoid caching
                const resp = await fetch('/assets/littleTools/CurrencyCalculator/rates.json?v=' + Date.now());
                if (!resp.ok) throw new Error('Network error');
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
            // Calculate base rates (1 Foreign = ? CNY)
            if (rateData.CNY && rateData.EUR && rateData.USD) {
                const eurToCny = rateData.CNY / rateData.EUR;
                const usdToCny = rateData.CNY / rateData.USD;
                
                els.rateEur.textContent = eurToCny.toFixed(4);
                els.rateUsd.textContent = usdToCny.toFixed(4);
            }
            
            // Update time
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
            if (!rateData.CNY) return; // Not ready

            const amount = parseFloat(els.amount.value);
            if (isNaN(amount)) {
                els.result.textContent = '---';
                return;
            }

            const fromCode = els.from.value;
            const toCode = els.to.value;

            // Algorithm: Amount / Rate(From) * Rate(To)
            // (Base is EUR usually in many APIs, but here rates are relative to base, so:
            // Input(From) -> Base -> Output(To)
            // Val_Base = Amount / Rate_From
            // Val_To = Val_Base * Rate_To
            
            const valInBase = amount / rateData[fromCode];
            const result = valInBase * rateData[toCode];

            // Display
            els.result.textContent = result.toLocaleString('zh-CN', {
                maximumFractionDigits: 2,
                minimumFractionDigits: 2
            });
            
            // Symbol
            const symbols = { 'CNY': '¥', 'EUR': '€', 'USD': '$' };
            els.resSymbol.textContent = symbols[toCode] || '';
        }

        // Listeners
        els.amount.addEventListener('input', calculate);
        els.from.addEventListener('change', calculate);
        els.to.addEventListener('change', calculate);
        
        els.swap.addEventListener('click', () => {
            const t = els.from.value;
            els.from.value = els.to.value;
            els.to.value = t;
            
            // Rotate icon animation
            const icon = els.swap.querySelector('.swap-icon');
            if(icon) {
                 icon.style.transition = 'transform 0.3s';
                 icon.style.transform = 'rotate(180deg)';
                 setTimeout(() => icon.style.transform = 'none', 300);
            }
            
            calculate();
        });

        // Run
        init();
    })();
</script>
