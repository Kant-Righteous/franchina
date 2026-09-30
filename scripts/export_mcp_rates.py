"""Export the official exchange rates collected by the FranChina MCP as JSON.

The script runs on the production host, usually piped over SSH:

    ssh host 'python3 -' < scripts/export_mcp_rates.py > mcp_rates.json

It opens the SQLite database read-only, keeps the sources updated on the most
recent collection date, picks one rate type per source, and prints the result
to stdout. Every rate means "1 foreign currency = rate CNY". Only the standard
library is used.
"""

import argparse
import json
import os
import sqlite3
import sys
from collections import defaultdict
from contextlib import closing
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

DEFAULT_DB_PATH = "/var/lib/franchina/rates.sqlite"
HISTORY_DAYS = 90
CURRENCIES = ("EUR", "USD")

# 每个来源只展示一种价格，按此顺序选用第一个当日有数据的类型
PREFERRED_RATE_TYPES = (
    "spot_sell",
    "card_conversion",
    "alipay_settlement",
    "reference",
    "spot_buy",
)

BANK_SPOT_SELL = {
    "name": "现汇卖出价",
    "frequency": "工作日多次更新 · 本站每日采集",
    "description": (
        "{source}外汇牌价中的现汇卖出价，由银行在市场报价基础上加点差得出。"
        "用人民币购汇（如给法国账户汇款）时适用，结汇换回人民币的价格会略低。"
    ),
}

# source -> 中文名称、读者可访问的官网页面（未设置时使用数据库中的 source_url）
SOURCES = {
    "BOC": {"name": "中国银行"},
    "ICBC": {
        "name": "工商银行",
        "website": "https://www.icbc.com.cn/column/1438058341489590354.html",
    },
    "CIB": {"name": "兴业银行"},
    "UNIONPAY": {"name": "银联"},
    "ALIPAY": {"name": "支付宝"},
    "European Central Bank": {"name": "欧洲央行"},
}

RATE_TYPES = {
    ("BOC", "spot_sell"): BANK_SPOT_SELL,
    ("ICBC", "spot_sell"): BANK_SPOT_SELL,
    ("CIB", "spot_sell"): BANK_SPOT_SELL,
    ("UNIONPAY", "card_conversion"): {
        "name": "银联卡境外交易汇率",
        "rate_label": "银联卡境外交易汇率",
        "frequency": "工作日更新 · 周末沿用周五",
        "description": (
            "银联国际公布的银联卡境外交易汇率，每个工作日更新一次。"
            "用人民币银联卡在法国刷卡或取现时按此折算，不含发卡行可能另收的手续费。"
        ),
    },
    ("ALIPAY", "alipay_settlement"): {
        "name": "境外支付汇率",
        "frequency": "本站每日采集",
        "description": (
            "支付宝境外线下支付时的参考汇率，数据取自第三方汇率网站的汇总。"
            "在法国用支付宝付款时适用，实际扣款以付款页面显示为准。"
        ),
    },
    ("European Central Bank", "reference"): {
        "name": "参考汇率",
        "frequency": "工作日约 16:00 更新",
        "description": (
            "欧洲中央银行每个工作日公布的欧元参考汇率，由各国央行协商得出。"
            "常用于统计和对账，不是银行实际买卖价格。"
        ),
    },
}

SOURCE_ORDER = list(SOURCES)


def open_read_only(db_path):
    path = Path(db_path)
    if not path.is_file():
        raise FileNotFoundError(f"database not found: {db_path}")
    uri = f"{path.resolve().as_uri()}?mode=ro"
    return sqlite3.connect(uri, uri=True, timeout=30)


def parse_rate(value):
    try:
        rate = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not rate.is_finite() or rate <= 0:
        return None
    return float(rate)


def describe(source, rate_type):
    name = SOURCES.get(source, {}).get("name", source)
    meta = RATE_TYPES.get((source, rate_type))
    if meta is None:
        return {
            "label": name,
            "rate_label": f"{name} {rate_type}",
            "type_label": rate_type,
            "frequency": "",
            "description": "",
        }
    return {
        "label": name,
        "rate_label": meta.get("rate_label", f"{name}{meta['name']}"),
        "type_label": meta["name"],
        "frequency": meta["frequency"],
        "description": meta["description"].format(source=name),
    }


def source_rank(source):
    return (SOURCE_ORDER.index(source) if source in SOURCE_ORDER else len(SOURCE_ORDER), source)


def rate_type_rank(rate_type):
    if rate_type in PREFERRED_RATE_TYPES:
        return (PREFERRED_RATE_TYPES.index(rate_type), rate_type)
    return (len(PREFERRED_RATE_TYPES), rate_type)


def load_rows(connection):
    latest = connection.execute(
        'SELECT MAX("date") FROM exchange_rates WHERE currency IN (?, ?)',
        CURRENCIES,
    ).fetchone()[0]
    if not latest:
        return None, []
    start = (date.fromisoformat(latest) - timedelta(days=HISTORY_DAYS - 1)).isoformat()
    rows = connection.execute(
        """
        SELECT "date", source, currency, rate_type, rate, source_url
        FROM exchange_rates
        WHERE currency IN (?, ?) AND "date" >= ? AND "date" <= ?
        ORDER BY "date", currency
        """,
        (*CURRENCIES, start, latest),
    ).fetchall()
    return latest, rows


def build_sources(latest, rows):
    # source -> rate_type -> date -> currency -> rate
    groups = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    urls = {}
    for day, source, currency, rate_type, raw_rate, source_url in rows:
        rate = parse_rate(raw_rate)
        if rate is None:
            continue
        groups[source][rate_type][day][currency] = rate
        if day == latest:
            urls.setdefault((source, rate_type), source_url)

    sources = []
    for source in sorted(groups, key=source_rank):
        current_types = [t for t, by_day in groups[source].items() if latest in by_day]
        if not current_types:
            continue
        rate_type = min(current_types, key=rate_type_rank)
        by_day = groups[source][rate_type]
        source_url = urls.get((source, rate_type), "")
        sources.append(
            {
                "id": source,
                "source": source,
                "rate_type": rate_type,
                **describe(source, rate_type),
                "source_url": source_url,
                "website": SOURCES.get(source, {}).get("website", source_url),
                "latest_date": latest,
                "rates": {
                    currency: {"rate": rate, "date": latest}
                    for currency, rate in sorted(by_day[latest].items())
                },
                "history": [
                    {"date": day, **values}
                    for day, values in sorted(by_day.items())
                ],
            }
        )
    return sources


def export(db_path, now=None):
    with closing(open_read_only(db_path)) as connection:
        latest, rows = load_rows(connection)
    generated_at = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    return {
        "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
        "latest_date": latest,
        "sources": build_sources(latest, rows) if latest else [],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--db",
        default=os.environ.get("FRANCHINA_MCP_DB_PATH", DEFAULT_DB_PATH),
        help="SQLite database path (default: %(default)s)",
    )
    args = parser.parse_args(argv)
    try:
        payload = export(args.db)
    except (OSError, sqlite3.Error) as error:
        print(f"export_mcp_rates: {error}", file=sys.stderr)
        return 1
    output = json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
    sys.stdout.buffer.write(output.encode("utf-8"))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
