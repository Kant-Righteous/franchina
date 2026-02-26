#!/usr/bin/env python3
"""
从欧洲中央银行(ECB)获取历史汇率数据
用于初始化或更新 history.json

Usage:
    python fetch_history.py              # 获取全部历史数据 (2015至今)
    python fetch_history.py --update     # 只获取最近30天的数据用于更新
"""

import urllib.request
import json
import os
import sys
import math
from datetime import datetime, timedelta

# ECB API 配置
ECB_API_BASE = "https://data-api.ecb.europa.eu/service/data/EXR"
PAIRS = {
    "EUR_USD": "D.USD.EUR.SP00.A",
    "EUR_CNY": "D.CNY.EUR.SP00.A"
}

# 文件路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(SCRIPT_DIR, "history.json")


def fetch_ecb_data(pair_code: str, start_date: str, end_date: str) -> list:
    """从ECB获取指定货币对的历史数据"""
    url = f"{ECB_API_BASE}/{pair_code}?startPeriod={start_date}&endPeriod={end_date}&format=jsondata"
    print(f"Fetching {pair_code} from {start_date} to {end_date}...")
    
    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=60) as response:
            data = json.loads(response.read().decode())
            
            # 解析ECB响应格式
            observations = data['dataSets'][0]['series']['0:0:0:0:0']['observations']
            time_periods = data['structure']['dimensions']['observation'][0]['values']
            
            result = []
            for idx, period in enumerate(time_periods):
                date = period['id']
                rate = observations.get(str(idx), [None])[0]
                if rate is not None:
                    result.append({"date": date, "rate": rate})
            
            print(f"  Retrieved {len(result)} records")
            return result
            
    except Exception as e:
        print(f"Error fetching {pair_code}: {e}")
        return []


def load_existing_history() -> dict:
    """加载现有历史数据"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"lastUpdate": "", "EUR_CNY": [], "EUR_USD": [], "USD_CNY": []}


def save_history(data: dict):
    """保存历史数据"""
    data['lastUpdate'] = datetime.now().strftime('%Y-%m-%d')
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"Saved to {HISTORY_FILE}")


def merge_data(existing: list, new_data: list) -> list:
    """合并现有数据和新数据，去重"""
    existing_dates = {item['date'] for item in existing}
    merged = existing.copy()
    
    added = 0
    for item in new_data:
        if item['date'] not in existing_dates:
            merged.append(item)
            added += 1
    
    # 按日期排序
    merged.sort(key=lambda x: x['date'])
    print(f"  Added {added} new records")
    return merged


def build_usd_cny(history: dict):
    eur_cny = history.get("EUR_CNY", [])
    eur_usd = history.get("EUR_USD", [])
    if not eur_cny or not eur_usd:
        history["USD_CNY"] = []
        return

    usd_map = {item.get("date"): item.get("rate") for item in eur_usd}
    usd_cny = []

    for item in eur_cny:
        date = item.get("date")
        rate = item.get("rate")
        usd_rate = usd_map.get(date)
        if date is None or rate is None or usd_rate in (None, 0):
            continue
        usd_value = rate / usd_rate
        if math.isfinite(usd_value):
            usd_cny.append({"date": date, "rate": usd_value})

    history["USD_CNY"] = usd_cny


def main():
    update_mode = '--update' in sys.argv
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    if update_mode:
        # 更新模式：获取最近30天数据
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        print("=== Update Mode: Fetching last 30 days ===")
        history = load_existing_history()
    else:
        # 完整模式：获取2015年至今所有数据
        start_date = "2015-01-01"
        print("=== Full Mode: Fetching all history since 2015 ===")
        history = {"lastUpdate": "", "EUR_CNY": [], "EUR_USD": [], "USD_CNY": []}
    
    # 获取每个货币对的数据
    for pair_name, pair_code in PAIRS.items():
        new_data = fetch_ecb_data(pair_code, start_date, today)
        if new_data:
            history[pair_name] = merge_data(history.get(pair_name, []), new_data)
    
    build_usd_cny(history)
    save_history(history)
    
    # 输出统计
    print("\n=== Summary ===")
    print(f"EUR_CNY: {len(history.get('EUR_CNY', []))} records")
    print(f"EUR_USD: {len(history.get('EUR_USD', []))} records")
    print(f"USD_CNY: {len(history.get('USD_CNY', []))} records")
    print(f"Last Update: {history['lastUpdate']}")


if __name__ == "__main__":
    main()
