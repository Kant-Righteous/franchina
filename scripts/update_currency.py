import urllib.request
import json
import os
import time
from datetime import datetime

# Configuration
API_URL = "https://open.er-api.com/v6/latest/EUR"
OUTPUT_DIR = os.path.join("docs", "assets", "littleTools", "CurrencyCalculator")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "rates.json")
HISTORY_FILE = os.path.join(OUTPUT_DIR, "history.json")

def fetch_rates():
    print(f"Fetching rates from {API_URL}...")
    try:
        with urllib.request.urlopen(API_URL) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                return data
            else:
                print(f"Error: Status code {response.status}")
                return None
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def save_rates(data):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Rates saved to {OUTPUT_FILE}")


def update_history(rates_data):
    """将当天汇率追加到历史数据文件"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 加载现有历史数据
    history = {"lastUpdate": "", "EUR_CNY": [], "EUR_USD": []}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except Exception as e:
            print(f"Warning: Could not read history file: {e}")
    
    rates = rates_data.get('rates', {})
    
    # 检查今天是否已有数据
    for pair_name, currency_code in [("EUR_CNY", "CNY"), ("EUR_USD", "USD")]:
        if currency_code not in rates:
            continue
            
        rate_value = rates[currency_code]
        existing_dates = {item['date'] for item in history.get(pair_name, [])}
        
        if today not in existing_dates:
            if pair_name not in history:
                history[pair_name] = []
            history[pair_name].append({"date": today, "rate": rate_value})
            history[pair_name].sort(key=lambda x: x['date'])
            print(f"Added {pair_name}: {today} = {rate_value}")
        else:
            print(f"Skipped {pair_name}: {today} already exists")
    
    # 保存历史数据
    history['lastUpdate'] = today
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False)
    print(f"History updated: {HISTORY_FILE}")


def main():
    data = fetch_rates()
    if data and data.get('result') == 'success':
        save_rates(data)
        update_history(data)
    else:
        print("Failed to update rates.")
        exit(1)


if __name__ == "__main__":
    main()

