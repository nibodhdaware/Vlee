import puppeteer from "puppeteer";
const browser = await puppeteer.launch({ headless: "new", args: ["--no-sandbox", "--enable-unsafe-swiftshader"] });
const page = await browser.newPage();
page.on("pageerror", e => console.log("[pageerror]", String(e).slice(0, 300)));
await page.goto("http://localhost:8765/index.html", { waitUntil: "domcontentloaded" });
await new Promise(r => setTimeout(r, 6000));
await page.screenshot({ path: "/tmp/sim_dbg.png" });
await browser.close();
