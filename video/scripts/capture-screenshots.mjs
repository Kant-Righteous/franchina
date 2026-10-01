// Captures real FranChina pages for the promo video.
// Usage: node scripts/capture-screenshots.mjs [baseUrl]
// Default base URL is the production site; pass http://127.0.0.1:8000 to use `mkdocs serve`.
import { existsSync, mkdirSync } from "node:fs";
import path from "node:path";
import puppeteer from "puppeteer-core";

const BASE = (process.argv[2] ?? "https://franchina.qzz.io").replace(/\/$/, "");
const OUT = path.resolve(import.meta.dirname, "../public/screenshots");

const CHROME_CANDIDATES = [
  process.env.CHROME_PATH,
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/usr/bin/google-chrome",
].filter(Boolean);

const shots = [
  { name: "home", url: "/", height: 900 },
  { name: "home-full", url: "/", fullPage: true },
  { name: "visa", url: "/pages/admin/before/visa/", height: 900 },
  { name: "first-week", url: "/pages/admin/after/first-week/", height: 900 },
  { name: "bank", url: "/pages/life/finance/bank/", height: 900 },
  { name: "anti-fraud-housing", url: "/pages/life/anti-fraud/housing/", height: 900 },
  { name: "residence", url: "/pages/admin/after/residence/", height: 900 },
  { name: "toulouse-index", url: "/pages/toulouse/", height: 900 },
  { name: "toulouse-transport", url: "/pages/toulouse/transport/", height: 900, scrollTo: "#tisseo" },
  { name: "toulouse-safety", url: "/pages/toulouse/safety/", height: 900 },
  { name: "toulouse-food-safety", url: "/pages/toulouse/food-safety/", height: 900, wait: 4000 },
  { name: "toulouse-cssa", url: "/pages/toulouse/cssa/", height: 900 },
  { name: "currency", url: "/pages/life/finance/currency-calculator/", height: 1000, wait: 3000 },
];

const executablePath = CHROME_CANDIDATES.find((p) => existsSync(p));
if (!executablePath) throw new Error("No Chrome/Edge found; set CHROME_PATH");
mkdirSync(OUT, { recursive: true });

const browser = await puppeteer.launch({ executablePath, headless: true });
try {
  for (const shot of shots) {
    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: shot.height ?? 900, deviceScaleFactor: 2 });
    await page.goto(BASE + shot.url, { waitUntil: "networkidle0", timeout: 60_000 });
    await page.addStyleTag({ content: "*{caret-color:transparent!important} .md-top{display:none!important}" });
    if (shot.scrollTo) {
      await page.evaluate((sel) => {
        const el = document.querySelector(sel);
        if (el) window.scrollTo(0, el.getBoundingClientRect().top + window.scrollY - 140);
      }, shot.scrollTo);
    }
    await new Promise((r) => setTimeout(r, shot.wait ?? 1200));
    const file = path.join(OUT, `${shot.name}.png`);
    await page.screenshot({ path: file, fullPage: Boolean(shot.fullPage) });
    console.log("saved", path.relative(process.cwd(), file));
    await page.close();
  }
} finally {
  await browser.close();
}
