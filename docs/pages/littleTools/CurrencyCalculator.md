---
hide:
  - navigation
---

# 汇率计算器

<div class="calculator-container">
    <div class="calculator-card">
        <div class="header-section">
            <span class="icon">💶</span>
            <span class="icon-arrow">⇄</span>
            <span class="icon">💴</span>
        </div>
        <div class="input-group">
            <label>金额</label>
            <input type="number" id="amount" value="100" placeholder="请输入金额">
        </div>
        
        <div class="currency-row">
            <div class="currency-select">
                <label>持有</label>
                <select id="fromCurrency">
                    <option value="EUR">🇪🇺 欧元 (EUR)</option>
                    <option value="CNY">🇨🇳 人民币 (CNY)</option>
                </select>
            </div>
            
            <button id="swapBtn" class="swap-btn" title="交换货币">
                ⇄
            </button>
            
            <div class="currency-select">
                <label>兑换为</label>
                <select id="toCurrency">
                    <option value="CNY">🇨🇳 人民币 (CNY)</option>
                    <option value="EUR">🇪🇺 欧元 (EUR)</option>
                </select>
            </div>
        </div>

        <div class="result-section">
            <div class="result-value" id="result">--</div>
            <div class="rate-info" id="rateInfo">正在获取最新汇率...</div>
            <div class="update-time" id="lastUpdate"></div>
        </div>
    </div>
</div>

<style>
    .calculator-container {
        display: flex;
        justify-content: center;
        padding: 2rem 0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    .calculator-card {
        background: rgba(255, 255, 255, 0.8);
        -webkit-backdrop-filter: blur(10px);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        width: 100%;
        max-width: 400px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.18);
        transition: transform 0.3s ease;
    }

    .calculator-card:hover {
        transform: translateY(-5px);
    }

    .header-section {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 1rem;
        margin-bottom: 2rem;
        font-size: 2rem;
    }

    .icon-arrow {
        color: var(--md-primary-fg-color, #5c6bc0);
        font-size: 1.5rem;
    }

    .input-group {
        margin-bottom: 1.5rem;
    }

    .input-group label, .currency-select label {
        display: block;
        margin-bottom: 0.5rem;
        color: var(--md-typeset-color, #444);
        font-weight: 500;
        font-size: 0.9rem;
    }

    input[type="number"] {
        width: 100%;
        padding: 12px 16px;
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        font-size: 1.2rem;
        font-weight: 600;
        color: #333;
        transition: all 0.3s ease;
        background: rgba(255, 255, 255, 0.9);
    }

    input[type="number"]:focus {
        border-color: var(--md-primary-fg-color, #5c6bc0);
        outline: none;
        box-shadow: 0 0 0 4px rgba(92, 107, 192, 0.1);
    }

    .currency-row {
        display: flex;
        align-items: flex-end;
        gap: 0.8rem;
        margin-bottom: 2rem;
    }

    .currency-select {
        flex: 1;
    }

    select {
        width: 100%;
        padding: 10px;
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        background-color: white;
        cursor: pointer;
        font-size: 0.95rem;
    }

    .swap-btn {
        background: var(--md-primary-fg-color, #5c6bc0);
        color: white;
        border: none;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        transition: all 0.3s ease;
        margin-bottom: 2px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .swap-btn:hover {
        transform: rotate(180deg);
        background: var(--md-primary-fg-color--light, #7986cb);
    }

    .result-section {
        text-align: center;
        padding-top: 1rem;
        border-top: 1px solid rgba(0,0,0,0.05);
    }

    .result-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: var(--md-primary-fg-color, #5c6bc0);
        margin-bottom: 0.5rem;
        line-height: 1.2;
    }

    .rate-info {
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 0.3rem;
    }

    .update-time {
        color: #999;
        font-size: 0.8rem;
    }
    
    /* Dark mode adjustments override */
    [data-md-color-scheme="slate"] .calculator-card {
        background: rgba(30, 30, 30, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    [data-md-color-scheme="slate"] input, 
    [data-md-color-scheme="slate"] select {
        background: rgba(0, 0, 0, 0.2);
        border-color: #444;
        color: #eee;
    }
    
    [data-md-color-scheme="slate"] .input-group label,
    [data-md-color-scheme="slate"] .currency-select label {
        color: #bbb;
    }
    
    [data-md-color-scheme="slate"] .result-value {
        color: var(--md-primary-fg-color--light, #7986cb);
    }
    
    [data-md-color-scheme="slate"] .rate-info {
        color: #aaa;
    }
</style>

<script>
    const amountInput = document.getElementById('amount');
    const fromSelect = document.getElementById('fromCurrency');
    const toSelect = document.getElementById('toCurrency');
    const resultDiv = document.getElementById('result');
    const rateInfoDiv = document.getElementById('rateInfo');
    const lastUpdateDiv = document.getElementById('lastUpdate');
    const swapBtn = document.getElementById('swapBtn');

    let rates = {};

    async function fetchRates() {
        try {
            // Use absolute path for assets and add timestamp to prevent caching
            // /assets/... ensures we look at the site root, regardless of current page depth
            const response = await fetch('/assets/littleTools/CurrencyCalculator/rates.json?v=' + new Date().getTime());
            
            if (!response.ok) {
                 throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.result === 'success') {
                rates = data.rates;
                updateCalculation();
                
                const date = new Date(data.time_last_update_utc);
                lastUpdateDiv.textContent = '更新时间: ' + date.toLocaleString('zh-CN', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    // hour: '2-digit',
                    // minute: '2-digit'
                });
            } else {
                rateInfoDiv.textContent = '获取汇率失败';
            }
        } catch (error) {
            console.error('Error fetching rates:', error);
            rateInfoDiv.textContent = '无法加载汇率数据';
        }
    }

    function updateCalculation() {
        if (!rates.EUR) return;

        const amount = parseFloat(amountInput.value);
        if (isNaN(amount)) {
            resultDiv.textContent = '---';
            return;
        }

        const fromCurrency = fromSelect.value;
        const toCurrency = toSelect.value;
        
        // Calculate rate relative to EUR (base)
        // If converting From A to B: Amount / Rate(A) * Rate(B)
        const rate = rates[toCurrency] / rates[fromCurrency];
        const result = amount * rate;
        
        // Format result: if > 100, 2 decimals, else 4 decimals
        const displayResult = result.toLocaleString('zh-CN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        
        resultDiv.textContent = `${toCurrency === 'CNY' ? '¥' : '€'}${displayResult}`;
        
        rateInfoDiv.textContent = `1 ${fromCurrency} = ${rate.toFixed(4)} ${toCurrency}`;
    }

    // Event Listeners
    amountInput.addEventListener('input', updateCalculation);
    fromSelect.addEventListener('change', updateCalculation);
    toSelect.addEventListener('change', updateCalculation);

    swapBtn.addEventListener('click', () => {
        const temp = fromSelect.value;
        fromSelect.value = toSelect.value;
        toSelect.value = temp;
        
        // Add minimal animation
        swapBtn.style.transform = 'rotate(180deg)';
        setTimeout(() => swapBtn.style.transform = 'none', 300);
        
        updateCalculation();
    });

    // Initialize
    fetchRates();
</script>
