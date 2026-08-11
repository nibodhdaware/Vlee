import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import puppeteer from "puppeteer";
import { execSync } from "child_process";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, "out");
const FRAMES = 780;  // PHASES.LEVEL[1]
const W = 1280, H = 720;

async function main() {
  if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });

  // launch headless chromium with SwiftShader
  const browser = await puppeteer.launch({
    headless: "new",
    args: [
      "--use-gl=swiftshader",
      "--enable-webgl",
      "--disable-gpu-sandbox",
      "--no-sandbox",
      `--window-size=${W},${H}`,
    ],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: W, height: H, deviceScaleFactor: 1 });
  await page.goto("file://" + path.join(__dirname, "index.html"), {
    waitUntil: "networkidle0",
  });

  // wait for sim init
  await page.waitForFunction(() => window.__sim !== undefined);
  const sim = await page.evaluateHandle(() => window.__sim);
  console.log("Sim loaded, capturing", FRAMES, "frames...");

  for (let i = 1; i <= FRAMES; i++) {
    await sim.evaluate(h => h.step());
    const dataUrl = await page.evaluate(() => window.__captureFrame());
    const b64 = dataUrl.split(",")[1];
    const buf = Buffer.from(b64, "base64");
    fs.writeFileSync(path.join(OUT, `frame_${String(i).padStart(4, "0")}.png`), buf);
    if (i % 50 === 0) console.log(`  ${i}/${FRAMES}`);
  }

  await browser.close();
  console.log("Frames written to", OUT);

  // stitch with ffmpeg
  const mp4 = path.join(__dirname, "vlee_physics_climb.mp4");
  execSync(`ffmpeg -y -framerate 30 -i ${OUT}/frame_%04d.png -c:v libx264 -pix_fmt yuv420p -profile:v main ${mp4}`, { stdio: "inherit" });
  console.log("MP4:", mp4);
}

main().catch(e => { console.error(e); process.exit(1); });