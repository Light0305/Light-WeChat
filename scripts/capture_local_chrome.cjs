#!/usr/bin/env node
"use strict";

// Dependency-free mobile preview capture through the locally installed Chrome CDP.
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawn } = require("node:child_process");
const { pathToFileURL } = require("node:url");

function argsOf(argv) {
  const args = {};
  for (let index = 0; index < argv.length; index += 2) {
    if (!argv[index]?.startsWith("--") || !argv[index + 1]) throw new Error("Expected --key value pairs");
    args[argv[index].slice(2)] = argv[index + 1];
  }
  return args;
}

function chromePath(explicit) {
  const candidates = [
    explicit,
    process.env.CHUANLAB_BROWSER,
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    ...String(process.env.PATH || '').split(path.delimiter).flatMap(dir =>
      ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'microsoft-edge']
        .map(name => path.join(dir, name))),
  ].filter(Boolean);
  const found = candidates.find((candidate) => fs.existsSync(candidate));
  if (!found) throw new Error("No local Chrome or Edge executable found; pass --browser");
  return found;
}

async function waitForPort(profile, child) {
  const portFile = path.join(profile, "DevToolsActivePort");
  for (let attempt = 0; attempt < 100; attempt += 1) {
    if (child.exitCode !== null) throw new Error(`Chrome exited: ${child.exitCode}`);
    if (fs.existsSync(portFile)) return Number(fs.readFileSync(portFile, "utf8").split(/\r?\n/)[0]);
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error("Chrome did not expose a debugging port within 10 seconds");
}

function connect(url) {
  return new Promise((resolve, reject) => {
    const socket = new WebSocket(url);
    const pending = new Map();
    let nextId = 1;
    socket.addEventListener("error", (event) => reject(new Error(`CDP WebSocket error: ${event.message || "unknown"}`)), { once: true });
    socket.addEventListener("open", () => {
      socket.addEventListener("message", (event) => {
        const message = JSON.parse(event.data);
        if (!message.id || !pending.has(message.id)) return;
        const [done, fail, timeout] = pending.get(message.id);
        clearTimeout(timeout);
        pending.delete(message.id);
        if (message.error) fail(new Error(`${message.error.message} (${message.error.code})`));
        else done(message.result || {});
      });
      resolve({
        send(method, params = {}) {
          return new Promise((done, fail) => {
            const id = nextId++;
            const timeout = setTimeout(() => {
              pending.delete(id);
              fail(new Error(`CDP timeout: ${method}`));
            }, 15000);
            pending.set(id, [done, fail, timeout]);
            socket.send(JSON.stringify({ id, method, params }));
          });
        },
        close() { socket.close(); },
      });
    }, { once: true });
  });
}

async function evaluate(cdp, expression) {
  const result = await cdp.send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text || "Page evaluation failed");
  return result.result.value;
}

async function ready(cdp, expectedUrl) {
  for (let attempt = 0; attempt < 100; attempt += 1) {
    const done = await evaluate(cdp, `location.href === ${JSON.stringify(expectedUrl)} && document.readyState === 'complete' && document.body && Array.from(document.images).every(image => image.complete)`);
    if (done) return;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error("Page or its images did not load within 10 seconds");
}

async function capture(cdp, file) {
  const { data } = await cdp.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false, fromSurface: true });
  fs.writeFileSync(file, Buffer.from(data, "base64"));
}

async function main() {
  const args = argsOf(process.argv.slice(2));
  if (!args.input || !args.out) throw new Error("Usage: capture_local_chrome.cjs --input <preview.html> --out <directory> [--width 390] [--height 844]");
  const input = path.resolve(args.input);
  const out = path.resolve(args.out);
  const width = Number(args.width || 390);
  const height = Number(args.height || 844);
  if (!fs.existsSync(input) || !Number.isInteger(width) || !Number.isInteger(height) || width < 200 || height < 200) throw new Error("Invalid input or viewport");
  fs.mkdirSync(out, { recursive: true });
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), "chuan-chrome-"));
  const child = spawn(chromePath(args.browser), [
    "--headless=new", "--disable-gpu", "--no-first-run", "--disable-extensions",
    '--disable-background-networking', '--disable-sync', '--disable-default-apps',
    "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank",
  ], { windowsHide: true, stdio: "ignore" });
  let cdp;
  try {
    const port = await waitForPort(profile, child);
    const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
    const target = targets.find((item) => item.type === "page");
    if (!target) throw new Error("Chrome opened no page target");
    cdp = await connect(target.webSocketDebuggerUrl);
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width, height, deviceScaleFactor: 1, mobile: !args.selector, screenWidth: width, screenHeight: height,
    });
    const inputUrl = pathToFileURL(input).href;
    await cdp.send("Page.navigate", { url: inputUrl });
    await ready(cdp, inputUrl);
    await evaluate(cdp, "document.fonts.ready.then(() => true)");
    if (args.selector) {
      // Suppress scrollbar-induced reflow when CDP temporarily expands the
      // viewport for a frame below the fold (otherwise centered frames shift).
      await evaluate(cdp, "document.documentElement.style.overflow='hidden'");
      const bounds = await evaluate(cdp, `(() => {
        const node = document.querySelector(${JSON.stringify(args.selector)});
        if (!node) throw new Error('Export selector not found');
        const r = node.getBoundingClientRect();
        return {x:r.x+scrollX,y:r.y+scrollY,width:r.width,height:r.height,
          scrollWidth:node.scrollWidth,scrollHeight:node.scrollHeight,
          brokenImages:Array.from(node.querySelectorAll('img')).filter(i=>!i.naturalWidth).length};
      })()`);
      if (bounds.brokenImages || bounds.scrollWidth > bounds.width || bounds.scrollHeight > bounds.height) {
        throw new Error(`Cover frame overflow or broken image: ${JSON.stringify(bounds)}`);
      }
      const {data} = await cdp.send('Page.captureScreenshot', {
        format:'png',captureBeyondViewport:true,fromSurface:true,
        clip:{x:bounds.x,y:bounds.y,width:bounds.width,height:bounds.height,scale:1}
      });
      fs.writeFileSync(path.join(out,'render.png'),Buffer.from(data,'base64'));
      fs.writeFileSync(path.join(out,'visual-audit.json'),JSON.stringify(bounds,null,2));
      return;
    }
    const metrics = await evaluate(cdp, `({
      viewportWidth: innerWidth,
      viewportHeight: innerHeight,
      scrollWidth: document.documentElement.scrollWidth,
      scrollHeight: document.documentElement.scrollHeight,
      visibleTextLength: document.body.innerText.trim().length,
      brokenImages: Array.from(document.images).filter(image => image.naturalWidth === 0).length,
      checkpoints: Array.from(document.querySelectorAll('table, pre, h2, [data-cl-section]')).map(element => ({
        tag: element.tagName.toLowerCase(), top: element.getBoundingClientRect().top + scrollY
      })),
      firstParagraphMargin: document.querySelector('p') ? getComputedStyle(document.querySelector('p')).marginBottom : null,
      evidenceTops: Array.from(document.images)
        .filter(image => !/(transition-|ornament-|contact-card)/i.test(image.getAttribute('src') || ''))
        .map(image => image.getBoundingClientRect().top + scrollY)
    })`);
    if (metrics.viewportWidth !== width || metrics.scrollWidth > width || metrics.brokenImages || !metrics.visibleTextLength) {
      throw new Error(`Visual audit failed: ${JSON.stringify(metrics)}`);
    }
    await capture(cdp, path.join(out, "first-screen.png"));
    metrics.firstEvidenceTop = metrics.evidenceTops[0] ?? null;
    for (const [index, top] of metrics.evidenceTops.entries()) {
      await evaluate(cdp, `scrollTo(0, ${Math.max(0, Math.round(top - 100))})`);
      await new Promise((resolve) => setTimeout(resolve, 150));
      await capture(cdp, path.join(out, `evidence-${index + 1}-screen.png`));
      if (index === 0) await capture(cdp, path.join(out, "evidence-screen.png"));
    }
    for (const [index, checkpoint] of metrics.checkpoints.entries()) {
      await evaluate(cdp, `scrollTo(0, ${Math.max(0, Math.round(checkpoint.top - 50))})`);
      await new Promise((resolve) => setTimeout(resolve, 100));
      await capture(cdp, path.join(out, `${checkpoint.tag}-${index + 1}-screen.png`));
    }
    await evaluate(cdp, "scrollTo(0, document.documentElement.scrollHeight)");
    await new Promise((resolve) => setTimeout(resolve, 150));
    await capture(cdp, path.join(out, "ending-screen.png"));
    if (metrics.scrollHeight <= 16000) {
      const { data } = await cdp.send("Page.captureScreenshot", {
        format: "png", captureBeyondViewport: true, fromSurface: true,
        clip: { x: 0, y: 0, width, height: metrics.scrollHeight, scale: 1 },
      });
      fs.writeFileSync(path.join(out, "full-page.png"), Buffer.from(data, "base64"));
    }
    fs.writeFileSync(path.join(out, "visual-audit.json"), JSON.stringify(metrics, null, 2) + "\n", "utf8");
    process.stdout.write(JSON.stringify({ out, ...metrics }, null, 2) + "\n");
  } finally {
    cdp?.close();
    child.kill();
    // Only remove the exact temporary profile created above, never a computed workspace path.
    if (path.dirname(profile) === os.tmpdir() && path.basename(profile).startsWith("chuan-chrome-")) {
      try { fs.rmSync(profile, { recursive: true, force: true }); } catch { /* Chrome may still be exiting. */ }
    }
  }
}

main().catch((error) => { process.stderr.write(`${error.stack || error.message}\n`); process.exitCode = 1; });
