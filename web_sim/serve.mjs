import http from "http";
import { fileURLToPath } from "url";
import { dirname, join, resolve } from "path";
import { createReadStream, statSync } from "fs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname);
const PORT = 8765;

const MIME = {
  ".js": "application/javascript",
  ".mjs": "application/javascript",
  ".html": "text/html",
  ".css": "text/css",
  ".png": "image/png",
  ".stl": "application/octet-stream",
  ".wasm": "application/wasm",
  ".json": "application/json",
  ".map": "application/json",
};

const server = http.createServer((req, res) => {
  let url = req.url.split("?")[0];
  if (url === "/") url = "/index.html";
  const file = join(ROOT, url);
  if (!file.startsWith(ROOT)) { res.writeHead(403); return res.end(); }
  try {
    const st = statSync(file);
    if (st.isDirectory()) { res.writeHead(404); return res.end(); }
    const ext = file.slice(file.lastIndexOf("."));
    res.writeHead(200, { "Content-Type": MIME[ext] || "application/octet-stream" });
    createReadStream(file).pipe(res);
  } catch (e) {
    res.writeHead(404);
    res.end("Not found");
  }
});

server.listen(PORT, () => console.log(`Serving ${ROOT} at http://localhost:${PORT}`));