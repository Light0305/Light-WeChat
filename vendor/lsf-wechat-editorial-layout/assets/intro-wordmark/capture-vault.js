// Render the selected card in its own document so export can advance its clock
// without affecting the preview, the user's settings or the other cards.
function frameClock(win) {
  let now = 1;
  let id = 0;
  const frames = new Map();
  const timers = new Map();
  const nativeMatch = win.matchMedia.bind(win);
  const getContext = win.HTMLCanvasElement.prototype.getContext;

  Object.defineProperty(win.performance, 'now', { value: () => now });
  Object.defineProperty(win, 'devicePixelRatio', { value: 1 });
  win.matchMedia = query => query === '(prefers-reduced-motion: reduce)'
    ? nativeMatch('not all') : nativeMatch(query);
  win.IntersectionObserver = class {
    constructor(callback) { this.callback = callback; }
    observe(target) { this.callback([{ target, isIntersecting: true, intersectionRatio: 1 }]); }
    disconnect() {}
  };
  win.HTMLCanvasElement.prototype.getContext = function(type, options) {
    return getContext.call(this, type, type.startsWith('webgl')
      ? { ...options, preserveDrawingBuffer: true } : options);
  };

  win.requestAnimationFrame = callback => {
    frames.set(++id, callback);
    return id;
  };
  win.cancelAnimationFrame = key => frames.delete(key);
  const addTimer = (callback, delay, repeat, args) => {
    const interval = Math.max(1, Number(delay) || 0);
    timers.set(++id, { callback, args, at: now + interval, interval: repeat ? interval : 0 });
    return id;
  };
  win.setTimeout = (callback, delay, ...args) => addTimer(callback, delay, false, args);
  win.setInterval = (callback, delay, ...args) => addTimer(callback, delay, true, args);
  win.clearTimeout = win.clearInterval = key => timers.delete(key);
  win.requestIdleCallback = callback => win.setTimeout(() => callback({ didTimeout: false, timeRemaining: () => 8 }), 1);
  win.cancelIdleCallback = win.clearTimeout;

  return {
    step(delay) {
      const until = now + delay;
      for (const [key, timer] of [...timers].sort((a, b) => a[1].at - b[1].at)) {
        if (timer.at > until || !timers.has(key)) continue;
        now = Math.max(now, timer.at);
        if (timer.interval) timer.at += timer.interval;
        else timers.delete(key);
        timer.callback(...timer.args);
      }
      now = until;
      const scheduled = [...frames.keys()];
      for (const key of scheduled) {
        const callback = frames.get(key);
        frames.delete(key);
        callback?.(now);
      }
      return now;
    },
  };
}

const snapshotProperties = `
  display position inset top right bottom left z-index width height min-width min-height max-width
  max-height margin padding box-sizing border border-radius overflow background-color color color-scheme
  opacity visibility transform transform-origin transform-box font-family font-weight font-size
  font-variant-numeric line-height letter-spacing text-align text-anchor dominant-baseline white-space
  align-items justify-content align-self flex flex-direction gap grid-template-columns fill stroke
  stroke-width vertical-align
`.trim().split(/\s+/);

function snapshotMarkup(scene, win) {
  const copy = scene.cloneNode(true);
  const sources = [scene, ...scene.querySelectorAll('*')];
  const copies = [copy, ...copy.querySelectorAll('*')];
  sources.forEach((element, i) => {
    const computed = win.getComputedStyle(element);
    const target = copies[i];
    for (const name of snapshotProperties) {
      const value = computed.getPropertyValue(name);
      if (value) target.style.setProperty(name, value);
    }
    target.style.setProperty('animation', 'none');
    target.style.setProperty('transition', 'none');
  });
  copy.querySelectorAll('style').forEach(style => style.remove());
  return new XMLSerializer().serializeToString(copy);
}

async function paintMarkup(scene, win, ctx, width, height) {
  const markup = snapshotMarkup(scene, win);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}"><foreignObject width="100%" height="100%">${markup}</foreignObject></svg>`;
  const image = new Image();
  image.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
  await image.decode();
  ctx.drawImage(image, 0, 0);
}

export async function captureVault({ id, text, width, height, bundle, duration, onFrame, still = false, frameMs = 40, stillAt }) {
  const frame = document.createElement('iframe');
  frame.setAttribute('aria-hidden', 'true');
  frame.tabIndex = -1;
  frame.style.cssText = `position:fixed;left:-${width + 20}px;top:0;width:${width}px;height:${height}px;border:0;pointer-events:none`;
  document.body.append(frame);
  const yieldTask = () => new Promise(resolve => setTimeout(resolve, 0));

  try {
    const win = frame.contentWindow;
    const doc = win.document;
    doc.open();
    doc.write('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"></head><body></body></html>');
    doc.close();
    doc.documentElement.dataset.animationExport = '';
    const clock = frameClock(win);
    const style = doc.createElement('style');
    style.textContent = [...document.head.querySelectorAll('style')].map(node => node.textContent).join('\n')
      + '\nhtml,body{margin:0;width:100%;height:100%;overflow:hidden;color-scheme:light} .vault-demo{height:100%;border-radius:0} [data-vault-export]{width:100%;height:100%}';
    doc.head.append(style);
    const host = doc.createElement('div');
    host.dataset.vaultExport = id;
    host.dataset.text = JSON.stringify(text);
    doc.body.append(host);
    const script = doc.createElement('script');
    script.textContent = bundle;
    doc.body.append(script);

    for (let attempt = 0; !host.firstElementChild?.firstElementChild && attempt < 60; attempt++) await yieldTask();
    const scene = host.firstElementChild?.firstElementChild;
    if (!scene) throw new Error('GIF scene did not mount');
    await doc.fonts.ready;
    await yieldTask();
    const assetSurface = scene.querySelector('canvas[data-export-ready]');
    if (assetSurface) {
      const deadline = performance.now() + 5000;
      while (assetSurface.dataset.exportReady === 'pending' && performance.now() < deadline) await yieldTask();
      if (assetSurface.dataset.exportReady !== 'true') throw new Error('Animation textures did not load');
    }
    const delay = frameMs;
    const gifDelay = duration > 8000 ? 80 : delay;
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    const animationStart = new WeakMap();
    let visible = false;

    for (let time = 0; time < duration; time += delay) {
      const now = clock.step(time ? delay : 1);
      // React commits changes to the DOM-based effects on a separate task.
      if (time % 160 === 0 || id === 'typer') await yieldTask();
      if (time % gifDelay !== 0) continue;
      const surface = scene.querySelector('canvas');
      const background = win.getComputedStyle(scene).backgroundColor;
      ctx.fillStyle = '#fff';
      ctx.fillRect(0, 0, width, height);
      ctx.fillStyle = background;
      ctx.fillRect(0, 0, width, height);

      if (surface) {
        const box = surface.getBoundingClientRect();
        if (surface.width > 0 && surface.height > 0) {
          ctx.drawImage(surface, box.x, box.y, box.width, box.height);
        }
      } else {
        for (const animation of scene.getAnimations({ subtree: true })) {
          if (!animationStart.has(animation)) {
            animationStart.set(animation, now);
            animation.pause();
          }
          animation.currentTime = now - animationStart.get(animation);
        }
        await paintMarkup(scene, win, ctx, width, height);
      }

      const pixels = ctx.getImageData(0, 0, width, height).data;
      if (still) {
        if (time < (stillAt ?? Math.min(600, duration / 2))) continue;
        for (let i = 4; i < pixels.length; i += 16) {
          if (pixels[i] !== pixels[0] || pixels[i + 1] !== pixels[1] || pixels[i + 2] !== pixels[2]) {
            onFrame(pixels);
            return;
          }
        }
        continue;
      }
      if (!visible) {
        for (let i = 4; i < pixels.length; i += 16) {
          if (pixels[i] !== pixels[0] || pixels[i + 1] !== pixels[1] || pixels[i + 2] !== pixels[2]) {
            visible = true;
            break;
          }
        }
      }
      onFrame(pixels, Math.min(gifDelay, duration - time));
    }
    if (!visible) throw new Error('Opening animation did not render');
  } finally {
    frame.remove();
  }
}
