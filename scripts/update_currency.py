import urllib.request
import json
import os
import time
from datetime import datetime

# Configuration
API_URL = "https://open.er-api.com/v6/latest/EUR"
OUTPUT_DIR = os.path.join("docs", "assets", "littleTools", "CurrencyCalculator")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "rates.json")

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

def main():


    data = fetch_rates()
    if data and data.get('result') == 'success':
        # Add a custom timestamp string for easy display if needed, 
        # though the API provides 'time_last_update_utc'
        save_rates(data)
    else:
        print("Failed to update rates.")
        exit(1)

if __name__ == "__main__":
    main()
