// Snapshots the exchange rates shown on the FranChina currency calculator.
// Usage: node scripts/fetch-rates.mjs [baseUrl]
import { writeFileSync } from "node:fs";
import path from "node:path";

const BASE = (process.argv[2] ?? "https://franchina.qzz.io").replace(/\/$/, "");
const DATA = `${BASE}/assets/life/finance/currency-calculator/`;
const OUT = path.resolve(import.meta.dirname, "../src/data/rates.json");

const get = async (name) => {
  const res = await fetch(DATA + name);
  if (!res.ok) throw new Error(`${name}: HTTP ${res.status}`);
  return res.json();
};

const [live, official] = await Promise.all([get("rates.json"), get("mcp_rates.json")]);
const round = (n) => Math.round(n * 10000) / 10000;

const sources = [
  {
    id: "live",
    label: "实时汇率",
    rateLabel: "市场中间价",
    eur: round(live.rates.CNY / live.rates.EUR),
    usd: round(live.rates.CNY / live.rates.USD),
  },
  ...official.sources.map((s) => ({
    id: s.id,
    label: s.label,
    rateLabel: s.type_label,
    eur: s.rates.EUR?.rate ?? null,
    usd: s.rates.USD?.rate ?? null,
  })),
];

const snapshot = { date: official.latest_date, sources };
writeFileSync(OUT, JSON.stringify(snapshot, null, 2) + "\n");
console.log(`saved ${sources.length} sources for ${snapshot.date}`);
