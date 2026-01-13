---
hide:
  - navigation
  - toc
---

# 汇率计算器

<div class="currency-wrapper">
    <!-- Top Rates Display -->
    <div class="rates-hero">
        <div class="rate-display">
            <div class="flag-icon">💶</div>
            <div class="rate-content">
                <div class="rate-title">欧元/人民币</div>
                <div class="rate-number" id="rate-eur">loading...</div>
            </div>
        </div>
        <div class="divider"></div>
        <div class="rate-display">
            <div class="flag-icon">💵</div>
            <div class="rate-content">
                <div class="rate-title">美元/人民币</div>
                <div class="rate-number" id="rate-usd">loading...</div>
            </div>
        </div>
    </div>
    
    <div class="update-status" id="lastUpdate">正在获取最新汇率...</div>

    <!-- Calculator Section -->
    <div class="calc-section">
        <div class="input-row">
            <div class="input-group">
                <label>金额</label>
                <input type="number" id="amount" value="100" placeholder="0">
            </div>
            
            <div class="currency-picker">
                <label>持有</label>
                <select id="fromCurrency">
                    <option value="EUR">欧元 (EUR)</option>
                    <option value="USD">美元 (USD)</option>
                    <option value="CNY">人民币 (CNY)</option>
                </select>
            </div>

            <button id="swapBtn" class="swap-action" title="交换">
                <span class="swap-icon">⇄</span>
            </button>

            <div class="currency-picker">
                <label>兑换为</label>
                <select id="toCurrency">
                    <option value="CNY">人民币 (CNY)</option>
                    <option value="EUR">欧元 (EUR)</option>
                    <option value="USD">美元 (USD)</option>
                </select>
            </div>
        </div>

        <div class="result-display" id="result-container">
            <span class="currency-symbol" id="res-symbol">¥</span>
            <span class="result-number" id="result">--</span>
        </div>
    </div>

    <div class="legal-footer">
        <p>数据来源：ExchangeRate-API</p>
        <p>免责声明：本站提供的汇率仅供参考，并不作为任何交易依据。实际交易汇率请以银行或金融机构实时牌价为准。如有因使用本页面数据而造成的任何经济损失，本站概不负责。</p>
    </div>
</div>

<style>
    .currency-wrapper {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem 1rem;
    }

    /* Top Hero Section */
    .rates-hero {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 3rem;
        margin-bottom: 2rem;
        flex-wrap: wrap;
    }

    .rate-display {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .flag-icon {
        font-size: 3.5rem;
        line-height: 1;
        margin-right: 0.5rem;
    }
    
    .flag-svg {
        display: none;
    }

    .rate-content {
        display: flex;
        flex-direction: column;
    }

    .rate-title {
        font-size: 0.8rem;
        color: var(--md-typeset-color);
        opacity: 0.7;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }

    .rate-number {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--md-typeset-color);
        line-height: 1;
        font-feature-settings: "tnum";
    }

    .divider {
        width: 1px;
        height: 60px;
        background-color: var(--md-default-fg-color--lightest);
        display: none; /* Hidden on mobile by default */
    }

    @media (min-width: 600px) {
        .divider {
            display: block;
        }
    }

    .update-status {
        text-align: center;
        font-size: 0.8rem;
        color: var(--md-typeset-color);
        opacity: 0.4;
        margin-bottom: 4rem;
        font-style: italic;
    }

    /* Calculator Section */
    .calc-section {
        max-width: 100%; /* Allow full width to fit single line */
        margin: 0 auto;
    }

    .input-row {
        display: flex;
        align-items: flex-end;
        gap: 0.8rem; /* Reduce gap to fit items */
        margin-bottom: 3rem;
        flex-wrap: wrap;
    }

    /* Amount input - give it more space */
    .input-group {
        flex: 1.2;
        min-width: 120px;
    }

    /* Currency pickers - equal size */
    .currency-picker {
        flex: 1.5;
        min-width: 160px; 
    }

    .input-row label {
        display: block;
        font-size: 0.85rem;
        margin-bottom: 0.8rem;
        color: var(--md-typeset-color);
        opacity: 0.6;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        white-space: nowrap; /* Prevent label wrapping */
    }

    input[type="number"], select {
        width: 100%;
        padding: 12px 0;
        border: none;
        border-bottom: 2px solid var(--md-default-fg-color--lightest);
        background: transparent;
        font-size: 1.6rem;
        font-weight: 600;
        color: var(--md-typeset-color);
        border-radius: 0;
        transition: all 0.3s;
        appearance: none;
        font-family: inherit;
    }

    select {
        text-align: center;
        cursor: pointer;
    }

    input[type="number"]:focus, select:focus {
        outline: none;
        border-bottom-color: var(--md-primary-fg-color);
    }
    
    /* Remove number input spinner */
    input[type=number]::-webkit-inner-spin-button, 
    input[type=number]::-webkit-outer-spin-button { 
        -webkit-appearance: none; 
        margin: 0; 
    }

    .swap-action {
        background: none;
        border: none;
        cursor: pointer;
        padding: 10px;
        margin-bottom: 5px;
        color: var(--md-primary-fg-color);
        opacity: 0.6;
        transition: all 0.3s;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
    }

    .swap-action:hover {
        opacity: 1;
        background-color: var(--md-default-fg-color--lightest);
    }
    
    .swap-icon {
        font-size: 1.5rem;
    }

    /* Result Display */
    .result-display {
        text-align: center;
        font-size: 5rem;
        font-weight: 700;
        color: var(--md-primary-fg-color);
        line-height: 1;
        margin-top: 2rem;
        display: flex;
        align-items: flex-start;
        justify-content: center;
        gap: 0.5rem;
        text-shadow: 0 10px 30px rgba(0,0,0,0.05);
    }
    
    .currency-symbol {
        font-size: 2.5rem;
        opacity: 0.6;
        font-weight: 400;
        margin-top: 10px; /* Optical alignment */
    }

    /* Legal Footer */
    .legal-footer {
        margin-top: 4rem;
        text-align: center;
        font-size: 0.75rem;
        color: var(--md-typeset-color);
        opacity: 0.5;
        line-height: 1.6;
        padding-top: 2rem;
        border-top: 1px dashed var(--md-default-fg-color--lightest);
    }
    
    .legal-footer p {
        margin: 0.5rem 0;
    }

    /* Dark Mode specific tweaks if needed */
    [data-md-color-scheme="slate"] input[type="number"], 
    [data-md-color-scheme="slate"] select {
        color: #fff;
    }
    
    /* Responsive tweaks */
    @media (max-width: 600px) {
        .result-display {
            font-size: 3.5rem;
        }
        .currency-symbol {
            font-size: 2rem;
        }
        .rates-hero {
            flex-direction: column;
            gap: 2rem;
        }
        .divider {
            display: none;
        }
        .input-row {
            flex-direction: column;
            gap: 2rem;
        }
        .input-group, .currency-picker {
            width: 100%;
        }
        .swap-action {
            transform: rotate(90deg);
            margin: -1rem auto;
            z-index: 10;
            background: var(--md-default-bg-color);
        }
        .swap-action:hover {
            transform: rotate(90deg) scale(1.1);
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
