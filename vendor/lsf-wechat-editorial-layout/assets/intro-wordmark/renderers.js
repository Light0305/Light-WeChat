// wordmarks.js — dependency-free Canvas 2D renderers for two lab wordmarks.
//   createTumble(canvas, props) -> { update(props), draw(timeMs), destroy() }
//   createMolten(canvas, props) -> { update(props), draw(timeMs), destroy() }
// The host owns the clock: draw(t) takes deterministic elapsed ms, so the same t
// always produces the same frame (RAF playback and GIF export alike).
// Sizing: pass { width, height, dpr } in update()/props, or leave them out to use
// the canvas backing store as it is. Neither renderer touches the DOM except to
// size the canvas you hand it.

/* ------------------------------------------------------------------ shared */

const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
const clamp01 = (v) => clamp(v, 0, 1);
const lerp = (a, b, t) => a + (b - a) * t;
const smoothstep = (x) => { x = clamp01(x); return x * x * (3 - 2 * x); };
const mod = (a, n) => ((a % n) + n) % n;

function makeCanvas(w, h, factory) {
  w = Math.max(1, Math.ceil(w)); h = Math.max(1, Math.ceil(h));
  if (factory) return factory(w, h);
  if (typeof OffscreenCanvas !== 'undefined') return new OffscreenCanvas(w, h);
  const c = document.createElement('canvas'); c.width = w; c.height = h; return c;
}
function ensureSize(c, w, h) {
  w = Math.max(1, Math.ceil(w)); h = Math.max(1, Math.ceil(h));
  if (c.width < w || c.height < h) { c.width = Math.max(c.width, w); c.height = Math.max(c.height, h); }
  return c;
}

export function splitGraphemes(str) {
  str = String(str ?? '');
  if (typeof Intl !== 'undefined' && Intl.Segmenter) {
    return Array.from(new Intl.Segmenter(undefined, { granularity: 'grapheme' }).segment(str), (s) => s.segment);
  }
  return Array.from(str); // code points; keeps surrogate pairs whole
}

function prefersReducedMotion() {
  try { return typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches; }
  catch { return false; }
}

// Re-run a layout when a web font finishes loading (canvas measures synchronously).
function watchFont(fontStr, sample, onReady) {
  if (typeof document === 'undefined' || !document.fonts || !document.fonts.load) return;
  let ok = true;
  try { ok = document.fonts.check(fontStr, sample); } catch { ok = true; }
  if (ok) return;
  document.fonts.load(fontStr, sample).then(onReady, () => {});
}

function applySize(canvas, props) {
  if (props.width == null || props.height == null) return;
  const dpr = props.dpr ?? (typeof devicePixelRatio !== 'undefined' ? devicePixelRatio : 1);
  const w = Math.max(1, Math.round(props.width * dpr)), h = Math.max(1, Math.round(props.height * dpr));
  if (canvas.width !== w) canvas.width = w;
  if (canvas.height !== h) canvas.height = h;
}

function fontFamily(canvas, value) {
  return value.replace(/var\(\s*(--[\w-]+)\s*\)/g, (_, name) =>
    typeof getComputedStyle === 'function' && canvas instanceof HTMLElement
      ? getComputedStyle(canvas).getPropertyValue(name).trim() || 'sans-serif'
      : 'sans-serif'
  );
}

/* ---------------------------------------------------------- colour / Oklab */

let _probe = null;
function parseColor(c, factory) {
  if (Array.isArray(c)) return c.slice(0, 3);
  let s = String(c).trim();
  let m = /^#([0-9a-f]{3,8})$/i.exec(s);
  if (!m) {
    if (!_probe) _probe = makeCanvas(1, 1, factory).getContext('2d');
    _probe.fillStyle = '#000'; _probe.fillStyle = s; s = String(_probe.fillStyle);
    m = /^#([0-9a-f]{6})$/i.exec(s);
    if (!m) {
      const r = /rgba?\(([^)]+)\)/.exec(s);
      if (r) return r[1].split(',').slice(0, 3).map((v) => +v);
      return [0, 0, 0];
    }
  }
  let h = m[1];
  if (h.length <= 4) h = h.split('').map((x) => x + x).join('');
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
}
const toLin = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
const toSrgb = (v) => 255 * (v <= 0.0031308 ? 12.92 * v : 1.055 * Math.pow(v, 1 / 2.4) - 0.055);
function rgbToOklab([r, g, b]) {
  r = toLin(r); g = toLin(g); b = toLin(b);
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  return [0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s,
    1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s,
    0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s];
}
function oklabToRgb([L, a, b]) {
  const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s = (L - 0.0894841775 * a - 1.291485548 * b) ** 3;
  return [toSrgb(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s),
    toSrgb(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s),
    toSrgb(-0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s)].map((v) => clamp(Math.round(v), 0, 255));
}
const css = ([r, g, b]) => `rgb(${r},${g},${b})`;

// Fritsch–Carlson monotone cubic through (xs, ys), clamped outside the table.
function monotoneCurve(xs, ys) {
  const n = xs.length, d = [], m = new Array(n);
  for (let i = 0; i < n - 1; i++) d[i] = (ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]);
  m[0] = d[0]; m[n - 1] = d[n - 2];
  for (let i = 1; i < n - 1; i++) m[i] = d[i - 1] * d[i] <= 0 ? 0 : (d[i - 1] + d[i]) / 2;
  for (let i = 0; i < n - 1; i++) {
    if (d[i] === 0) { m[i] = m[i + 1] = 0; continue; }
    const a = m[i] / d[i], b = m[i + 1] / d[i], h = a * a + b * b;
    if (h > 9) { const t = 3 / Math.sqrt(h); m[i] = t * a * d[i]; m[i + 1] = t * b * d[i]; }
  }
  return (x) => {
    if (x <= xs[0]) return ys[0];
    if (x >= xs[n - 1]) return ys[n - 1];
    let i = 0; while (x > xs[i + 1]) i++;
    const hh = xs[i + 1] - xs[i], t = (x - xs[i]) / hh, t2 = t * t, t3 = t2 * t;
    return (2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * hh * m[i] + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * hh * m[i + 1];
  };
}
function linearCurve(xs, ys) {
  const n = xs.length;
  return (x) => {
    if (x <= xs[0]) return ys[0];
    if (x >= xs[n - 1]) return ys[n - 1];
    let i = 0; while (x > xs[i + 1]) i++;
    return lerp(ys[i], ys[i + 1], (x - xs[i]) / (xs[i + 1] - xs[i]));
  };
}

/* ================================================================ TUMBLE */

const TUMBLE_DEFAULTS = {
  text: 'CHOP\nCHOP',            // string with \n, or an array of lines
  face: '#855BFF', plate: '#B9FF29', ink: '#000000', ground: '#469FFE',
  fontFamily: '"Luckiest Guy", "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", "Microsoft YaHei", sans-serif',
  fontWeight: '400',
  tracking: -0.025,             // em
  capHeight: 0.244,             // of the square side
  pitch: 1.132,                 // baseline-to-baseline, in cap heights
  span: 3.26,                   // max line width, in cap heights (longer text shrinks)
  loop: 1760, turn: 440, turnStart: 0.26, stagger: 80, lineStagger: 120,
  rtl: true,                    // the stagger runs from the right-hand glyph to the left
  direction: 1,                 // +1 / -1 flips the sense of the X-axis turn
  bob: 0.19,                    // em to either side of the lockup's centre
  extrude: [0.065, -0.085, 0.24], // em: x, y (negative = up), z depth
  band: 0.098, hairline: 0.014, // em
  colorMs: 700,
  halfResPlateAbove: 720,       // device px of the square; plate dilated at half res above this
  reducedMotion: undefined,     // undefined = follow prefers-reduced-motion
  createCanvas: undefined,      // optional (w, h) => canvas factory for workers/tests
};

const COLOR_KEYS = ['face', 'plate', 'ink', 'ground'];

export function createTumble(canvas, initial = {}) {
  const ctx = canvas.getContext('2d');
  let P = { ...TUMBLE_DEFAULTS, ...initial };
  let layout = null, layoutKey = '', fontGen = 0, destroyed = false;

  // colour state in Oklab
  const col = {};
  for (const k of COLOR_KEYS) { const lab = rgbToOklab(parseColor(P[k], P.createCanvas)); col[k] = { from: lab, to: lab, cur: lab, start: 0, pending: false }; }
  let lastT = 0;

  function colorsAt(t) {
    const out = {}; let moving = false;
    for (const k of COLOR_KEYS) {
      const c = col[k];
      if (c.pending) { c.start = t; c.pending = false; }
      if (t < c.start) c.start = t;
      const u = P.colorMs > 0 ? clamp01((t - c.start) / P.colorMs) : 1;
      c.cur = u === 1 ? c.to : c.from.map((channel, i) => lerp(channel, c.to[i], u));
      if (u < 1) moving = true;
      out[k] = css(oklabToRgb(c.cur));
    }
    out.moving = moving;
    return out;
  }

  const reduced = () => (P.reducedMotion ?? prefersReducedMotion());
  let resolvedFamily = fontFamily(canvas, P.fontFamily);
  const fontStr = (px) => `${P.fontWeight} ${px}px ${resolvedFamily}`;
  const lines = () => {
    const text = Array.isArray(P.text) ? P.text.slice(0, 2) : String(P.text).split('\n').slice(0, 2);
    if (text.length === 1) text.push(text[0]);
    return text.map(splitGraphemes);
  };

  function buildLayout() {
    const S = Math.min(canvas.width, canvas.height);
    const key = [S, canvas.width, canvas.height, JSON.stringify(P.text), P.fontFamily, P.fontWeight, P.tracking, P.capHeight, P.pitch, P.span, P.extrude.join(), P.band, P.hairline, P.fitVertical, P.bob, fontGen].join('|');
    if (key === layoutKey && layout) return layout;
    layoutKey = key;
    const m = ctx;
    m.save();
    m.font = fontStr(100);
    const capRatio = (m.measureText('H').actualBoundingBoxAscent || 72) / 100;
    let capH = P.capHeight * S;
    let em = capH / capRatio;
    const L = lines();
    const measureLine = (gs, emPx) => {
      m.font = fontStr(emPx);
      let x = 0; const out = [];
      for (const g of gs) { const w = m.measureText(g).width; out.push({ g, x, w }); x += w + P.tracking * emPx; }
      return { glyphs: out, width: Math.max(0, x - P.tracking * emPx) };
    };
    let widest = 0;
    for (const gs of L) widest = Math.max(widest, measureLine(gs, em).width);
    const maxW = P.span * capH;
    if (widest > maxW) { const k = maxW / widest; em *= k; capH *= k; }
    if (P.fitVertical) {
      m.font = fontStr(em);
      const [, ey, ez] = P.extrude;
      let radius = 0;
      for (const glyph of L.flat()) {
        if (!glyph.trim()) continue;
        const { actualBoundingBoxAscent: ascent, actualBoundingBoxDescent: descent } = m.measureText(glyph);
        const edge = Math.max(Math.abs(ascent - capH / 2), Math.abs(descent + capH / 2));
        radius = Math.max(radius, Math.hypot(edge + Math.abs(ey * em), ez * em / 2));
      }
      const travel = (L.length - 1) * P.pitch * capH / 2 + radius
        + (Math.abs(ey) / 2 + Math.abs(P.bob) + P.band + P.hairline) * em;
      const scale = Math.min(1, canvas.height * .47 / Math.max(1, travel));
      em *= scale;
      capH *= scale;
    }
    const pitch = P.pitch * capH;
    const [ex, ey] = P.extrude;
    // centre the rest silhouette (face + extrusion) in the square
    const cx = canvas.width / 2 - (ex * em) / 2, cy = canvas.height / 2 - (ey * em) / 2;
    const n = L.length, glyphs = [];
    m.font = fontStr(em);
    L.forEach((gs, li) => {
      const ml = measureLine(gs, em);
      const baseline = cy + (li - (n - 1) / 2) * pitch + capH / 2;
      const x0 = cx - ml.width / 2;
      const visible = ml.glyphs.filter((q) => q.g.trim() !== '');
      ml.glyphs.forEach((q) => {
        if (q.g.trim() === '') return;
        const tm = m.measureText(q.g);
        const l = Math.ceil(tm.actualBoundingBoxLeft ?? 0) + 2, r = Math.ceil(tm.actualBoundingBoxRight ?? q.w) + 2;
        const a = Math.ceil(tm.actualBoundingBoxAscent ?? capH) + 2, d = Math.ceil(tm.actualBoundingBoxDescent ?? 0) + 2;
        const mask = makeCanvas(l + r, a + d, P.createCanvas);
        const mc = mask.getContext('2d');
        mc.font = fontStr(em); mc.fillStyle = '#000'; mc.textBaseline = 'alphabetic';
        mc.fillText(q.g, l, a);
        const order = visible.indexOf(q);
        glyphs.push({
          mask, mw: l + r, mh: a + d,
          // mask top-left in canvas space at rest
          left: x0 + q.x - l, top: baseline - a,
          pivotY: baseline - capH / 2,   // rotation axis: the cap's vertical middle
          line: li, order: P.rtl ? visible.length - 1 - order : order,
          bufs: null, rest: null, restKey: '',
        });
      });
    });
    m.restore();
    layout = { S, em, capH, glyphs };
    watchFont(fontStr(Math.round(em)), L.flat().join('') || 'H', () => { if (!destroyed) { fontGen++; layoutKey = ''; } });
    return layout;
  }

  // Union of the buffer with copies of itself along (vx, vy), by self-draw doubling.
  function sweep(c, cctx, vx, vy, bounds) {
    const len = Math.hypot(vx, vy);
    if (len < 0.5) return;
    const passes = Math.ceil(Math.log2(len / 0.7 + 1));
    const samples = 2 ** passes - 1;
    for (let i = 0; i < passes; i++) {
      const dx = vx * 2 ** i / samples, dy = vy * 2 ** i / samples;
      const x = Math.max(0, Math.floor(bounds.left)), y = Math.max(0, Math.floor(bounds.top));
      const w = Math.min(c.width, Math.ceil(bounds.right)) - x, h = Math.min(c.height, Math.ceil(bounds.bottom)) - y;
      cctx.drawImage(c, x, y, w, h, x + dx, y + dy, w, h);
      bounds.left += Math.min(0, dx); bounds.top += Math.min(0, dy);
      bounds.right += Math.max(0, dx); bounds.bottom += Math.max(0, dy);
    }
  }
  // Minkowski dilation by a disc of radius r, as a 12-sided zonogon of six segment sweeps.
  // Content must have been drawn pre-shifted by dilateShift(r) so the result stays centred.
  const DIRS = 6;
  const segLen = (r) => 2 * r * Math.tan(Math.PI / (2 * DIRS));
  function dilateShift(r) {
    const L = segLen(r); let sx = 0, sy = 0;
    for (let k = 0; k < DIRS; k++) { const a = (k * Math.PI) / DIRS; sx -= (L / 2) * Math.cos(a); sy -= (L / 2) * Math.sin(a); }
    return [sx, sy];
  }
  function dilate(c, cctx, r, bounds) {
    if (r < 0.25) return;
    const L = segLen(r);
    for (let k = 0; k < DIRS; k++) { const a = (k * Math.PI) / DIRS; sweep(c, cctx, L * Math.cos(a), L * Math.sin(a), bounds); }
  }
  function tint(cctx, color, w, h) {
    cctx.globalCompositeOperation = 'source-in';
    cctx.fillStyle = color; cctx.fillRect(0, 0, w, h);
    cctx.globalCompositeOperation = 'source-over';
  }

  // Render one glyph's plate + solid (+ near cap) at angle th into its own tight buffers.
  function renderGlyph(g, th, colors, em, S) {
    const [exE, eyE, ezE] = P.extrude;
    const ex = exE * em, ey = eyE * em, ez = ezE * em, zc = ez / 2;
    const cos = Math.cos(th), sin = Math.sin(th);
    const hair = P.hairline * em, rPlate = (P.band + P.hairline) * em;
    // projected sweep vector and front-cap vertical shift (rotation about y = pivot, z = zc)
    const vx = ex, vy = ey * cos + ez * sin;
    const capShift = -zc * sin;
    // silhouette face squash: never fully zero so the edge-on sides still sweep
    const minC = 1.2 / g.mh;
    const sCos = Math.abs(cos) < minC ? (cos < 0 ? -minC : minC) : cos;
    // face bounds (canvas space) for scale sCos about pivotY
    const fy0 = g.pivotY + (g.top - g.pivotY) * sCos + capShift;
    const fy1 = g.pivotY + (g.top + g.mh - g.pivotY) * sCos + capShift;
    const yA = Math.min(fy0, fy1), yB = Math.max(fy0, fy1);
    const x0 = g.left + Math.min(0, vx), x1 = g.left + g.mw + Math.max(0, vx);
    const y0 = yA + Math.min(0, vy), y1 = yB + Math.max(0, vy);
    const pad = Math.ceil(rPlate) + 3;
    const bx = Math.floor(x0) - pad, by = Math.floor(y0) - pad;
    const bw = Math.ceil(x1) + pad - bx, bh = Math.ceil(y1) + pad - by;

    const half = S > P.halfResPlateAbove ? 0.5 : 1;
    if (!g.bufs) g.bufs = { A: makeCanvas(bw, bh, P.createCanvas), B: makeCanvas(bw * half + 2, bh * half + 2, P.createCanvas), C: makeCanvas(bw, bh, P.createCanvas) };
    const { A, B, C } = g.bufs;
    ensureSize(A, bw, bh); ensureSize(C, bw, bh); ensureSize(B, bw * half + 2, bh * half + 2);
    const a = A.getContext('2d'), b = B.getContext('2d'), c = C.getContext('2d');
    for (const q of [a, b, c]) { q.setTransform(1, 0, 0, 1, 0, 0); q.globalCompositeOperation = 'source-over'; q.globalAlpha = 1; }
    a.clearRect(0, 0, A.width, A.height); b.clearRect(0, 0, B.width, B.height); c.clearRect(0, 0, C.width, C.height);

    const drawFace = (q, scaleY, shiftX, shiftY, k) => {
      // face mask projected at sweep fraction k, buffer-local
      q.save();
      q.translate(-bx + shiftX + k * vx, -by + shiftY + k * vy + g.pivotY + capShift);
      q.scale(1, scaleY);
      q.drawImage(g.mask, g.left, g.top - g.pivotY);
      q.restore();
    };

    // 1. silhouette S into C (black), pre-shifted for the hairline dilation
    const [hsx, hsy] = dilateShift(hair);
    drawFace(c, sCos, hsx, hsy, 0);
    const bounds = { left: g.left - bx + hsx, top: yA - by + hsy, right: g.left + g.mw - bx + hsx, bottom: yB - by + hsy };
    sweep(C, c, vx, vy, bounds);
    // 2. plate: grow the moving silhouette by stamping it around a ring.
    const x = Math.floor(bounds.left), y = Math.floor(bounds.top);
    const w = Math.ceil(bounds.right) - x, h = Math.ceil(bounds.bottom) - y;
    const plateX = (x - hsx) * half, plateY = (y - hsy) * half;
    const radius = rPlate * half;
    b.drawImage(C, x, y, w, h, plateX, plateY, w * half, h * half);
    const stamps = Math.max(12, Math.ceil(2 * Math.PI * radius / 2.4));
    for (let i = 0; i < stamps; i++) {
      const a = 2 * Math.PI * i / stamps;
      b.drawImage(C, x, y, w, h, plateX + radius * Math.cos(a), plateY + radius * Math.sin(a), w * half, h * half);
    }
    tint(b, colors.plate, B.width, B.height);
    // 3. solid: S dilated by the hairline, in ink
    a.drawImage(C, x, y, w, h, x, y, w, h);
    dilate(A, a, hair, bounds);
    tint(a, colors.ink, A.width, A.height);
    // 4. near cap only (never the far one). Back cap is near when its depth faces the viewer.
    const backNear = eyE * sin - ezE * cos > 0;
    if (Math.abs(cos) > 1e-3) {
      c.clearRect(0, 0, C.width, C.height);
      drawFace(c, cos, 0, 0, backNear ? 1 : 0);
      tint(c, colors.face, C.width, C.height);
      a.drawImage(C, 0, 0);
    }
    return { A, B, bx, by, bw, bh, half };
  }

  function draw(timeMs = 0) {
    if (destroyed) return;
    const t = reduced() ? 0 : +timeMs || 0;
    lastT = t;
    const lay = buildLayout();
    const colors = colorsAt(+timeMs || 0);
    const { em, S } = lay;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1;
    ctx.fillStyle = colors.ground; ctx.fillRect(0, 0, canvas.width, canvas.height);

    const colorKey = colors.face + colors.plate + colors.ink;
    const frames = [];
    for (const g of lay.glyphs) {
      let th = 0;
      const bobY = reduced() ? 0 : -P.bob * em * Math.cos(2 * Math.PI * t / P.loop);
      if (!reduced()) {
        const delay = g.order * P.stagger + g.line * P.lineStagger;
        const tau = mod(t - delay, P.loop);
        const p = clamp01((tau - P.turnStart * P.loop) / P.turn);
        const e = 1 - (1 - p) * (1 - p);          // quad-out: edge-on at p = 0.134 and 0.5
        th = P.direction * 2 * Math.PI * (p >= 1 ? 0 : e);
      }
      let fr;
      if (th === 0) {
        const rk = colorKey + '|' + layoutKey;
        if (g.restKey !== rk || !g.rest) {
          const r = renderGlyph(g, 0, colors, em, S);
          // copy into a persistent rest cache
          const RA = g.rest?.A ?? makeCanvas(r.bw, r.bh, P.createCanvas);
          const RB = g.rest?.B ?? makeCanvas(r.B.width, r.B.height, P.createCanvas);
          ensureSize(RA, r.bw, r.bh); ensureSize(RB, r.B.width, r.B.height);
          const ra = RA.getContext('2d'), rb = RB.getContext('2d');
          ra.clearRect(0, 0, RA.width, RA.height); rb.clearRect(0, 0, RB.width, RB.height);
          ra.drawImage(r.A, 0, 0); rb.drawImage(r.B, 0, 0);
          g.rest = { ...r, A: RA, B: RB };
          if (!colors.moving) g.restKey = rk; else g.restKey = '';
        }
        fr = g.rest;
      } else {
        fr = renderGlyph(g, th, colors, em, S);
        // the live buffers get reused next frame; snapshot is not needed because we
        // composite this glyph's plate and solid before rendering the next glyph's
        // buffers only if they share storage — each glyph owns its own buffers.
      }
      frames.push({ fr, bobY });
    }
    // all plates before all solids, so neighbouring plates merge into one sticker
    ctx.imageSmoothingEnabled = true;
    for (const { fr, bobY } of frames) {
      const s = 1 / fr.half;
      ctx.drawImage(fr.B, 0, 0, fr.B.width, fr.B.height, fr.bx, fr.by + bobY, fr.B.width * s, fr.B.height * s);
    }
    for (const { fr, bobY } of frames) ctx.drawImage(fr.A, fr.bx, fr.by + bobY);
  }

  function update(next = {}) {
    for (const k of COLOR_KEYS) {
      if (next[k] != null && next[k] !== P[k]) {
        const lab = rgbToOklab(parseColor(next[k], P.createCanvas));
        col[k].from = col[k].cur; col[k].to = lab; col[k].pending = true;
      }
    }
    P = { ...P, ...next };
    if (next.fontFamily !== undefined) resolvedFamily = fontFamily(canvas, P.fontFamily);
    applySize(canvas, P);
  }

  applySize(canvas, P);
  return {
    update, draw,
    isMixing: () => COLOR_KEYS.some(k => col[k].pending || col[k].cur !== col[k].to),
    destroy() { destroyed = true; layout = null; },
  };
}

/* ================================================================ MOLTEN */

const MOLTEN_DEFAULTS = {
  words: ['MOLTEN', 'FORGE', 'EMBER'],
  word: undefined,              // controlled: set to show one word; a change restarts the melt
  swapMs: 3000, loopMs: 4000,
  background: '#000000',        // or 'transparent'
  fontFamily: '"Inter", "Helvetica Neue", Arial, "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif',
  fontWeight: '800',
  size: 1,                      // lowercase size multiplier
  caps: 'auto',                 // 'auto' (caps metrics when the word has no lowercase), true, false
  stretchX: 1.25, fit: 0.74,
  blur: 0.22, ghostTail: 0.06, heat: 1.3, gamma: 1.4, crispStart: 0.65,
  anisotropy: 2,                // vertical blur = horizontal / anisotropy (smear runs sideways)
  levels: 20, qRows: 160,
  reducedMotion: undefined,
  createCanvas: undefined,
};

const RAMP = [
  [0.055, 120, 200, 190, 0], [0.105, 165, 235, 222, 0.45], [0.19, 181, 240, 216, 0.9], [0.3, 187, 242, 197, 1],
  [0.4, 205, 247, 140, 1], [0.48, 225, 251, 92, 1], [0.59, 232, 200, 85, 1], [0.665, 240, 140, 88, 1],
  [0.735, 249, 50, 90, 1], [0.87, 250, 30, 95, 1], [0.93, 253, 150, 190, 1], [0.97, 255, 252, 252, 1], [1.0, 214, 213, 214, 1],
];
const SETTLED = [214, 213, 214];
function ramp(n) {
  if (n <= RAMP[0][0]) return RAMP[0].slice(1);
  for (let i = 1; i < RAMP.length; i++) {
    if (n <= RAMP[i][0]) {
      const a = RAMP[i - 1], b = RAMP[i], t = (n - a[0]) / (b[0] - a[0]);
      return [lerp(a[1], b[1], t), lerp(a[2], b[2], t), lerp(a[3], b[3], t), lerp(a[4], b[4], t)];
    }
  }
  return RAMP[RAMP.length - 1].slice(1);
}

const H_CURVE = monotoneCurve([-0.1, 0, 0.15, 0.3, 0.5, 0.7, 0.85, 1, 1.12], [520, 280, 390, 470, 570, 660, 725, 790, 862]);
const R_CURVE = monotoneCurve([0, 0.25, 0.5, 0.75, 1], [400, 230, 170, 200, 330]);

// Separable gaussian approximation: three box passes per axis, on Float32 data.
function boxSizes(sigma) {
  const n = 3, wIdeal = Math.sqrt((12 * sigma * sigma) / n + 1);
  let wl = Math.floor(wIdeal); if (wl % 2 === 0) wl--;
  const wu = wl + 2, mIdeal = (12 * sigma * sigma - n * wl * wl - 4 * n * wl - 3 * n) / (-4 * wl - 4);
  const m = Math.round(mIdeal), out = [];
  for (let i = 0; i < n; i++) out.push(((i < m ? wl : wu) - 1) / 2);
  return out;
}
function boxPass(src, dst, w, h, r, horizontal) {
  if (r <= 0) { dst.set(src); return; }
  const inv = 1 / (2 * r + 1);
  const outer = horizontal ? h : w, inner = horizontal ? w : h;
  const stride = horizontal ? 1 : w, lineStep = horizontal ? w : 1;
  for (let o = 0; o < outer; o++) {
    const base = o * lineStep;
    let acc = 0;
    for (let k = -r; k <= r; k++) { const j = clamp(k, 0, inner - 1); acc += k < 0 || k >= inner ? 0 : src[base + j * stride]; }
    for (let i = 0; i < inner; i++) {
      dst[base + i * stride] = acc * inv;
      const add = i + r + 1, sub = i - r;
      if (add < inner) acc += src[base + add * stride];
      if (sub >= 0) acc -= src[base + sub * stride];
    }
  }
}
function gaussBlur(data, w, h, sx, sy) {
  let a = Float32Array.from(data), b = new Float32Array(a.length);
  if (sx >= 0.35) for (const r of boxSizes(sx)) { boxPass(a, b, w, h, Math.round(r), true); [a, b] = [b, a]; }
  if (sy >= 0.35) for (const r of boxSizes(sy)) { boxPass(a, b, w, h, Math.round(r), false); [a, b] = [b, a]; }
  const out = new Uint8ClampedArray(a.length);
  for (let i = 0; i < a.length; i++) out[i] = a[i] + 0.5;
  return out;
}

export function createMolten(canvas, initial = {}) {
  const ctx = canvas.getContext('2d');
  let P = { ...MOLTEN_DEFAULTS, ...initial };
  let destroyed = false, fontGen = 0;
  const cache = new Map(); // word -> layout
  let lut = null, lutKey = '';
  let controlledWord = P.word, controlledStart = null;
  let reducedPainted = '';
  let image = null;

  const reduced = () => (P.reducedMotion ?? prefersReducedMotion());
  const isCaps = (w) => (P.caps === 'auto' ? w === w.toUpperCase() && w !== w.toLowerCase() : !!P.caps);

  function exposure(q) {
    const hs = P.heat / 1.6;
    return linearCurve([0, 0.04, 0.1, 0.18, 0.28, 0.38, 0.48, 0.56, 1], [0, 0.5, 1.0, 1.4 * hs, P.heat, 1.35 * hs, 1.05, 1.0, 1.0])(q);
  }
  function sigmaNorm(q) {
    const s = smoothstep((q - 0.18) / 0.47);
    return (1 - s) * (1 - 0.35 * q) + s * P.ghostTail * (1 - q);
  }

  function buildLut() {
    const key = [P.heat, P.gamma, P.crispStart, P.qRows].join('|');
    if (key === lutKey && lut) return lut;
    lutKey = key;
    const rows = P.qRows, L = new Float32Array(rows * 256 * 4);
    for (let r = 0; r < rows; r++) {
      const q = r / (rows - 1), ex = exposure(q);
      const w = smoothstep((q - P.crispStart) / (1 - P.crispStart));
      for (let v = 0; v < 256; v++) {
        const n = Math.min(1, ex * Math.pow(v / 255, P.gamma));
        const [cr, cg, cb, ca] = ramp(n);
        const i = (r * 256 + v) * 4;
        L[i] = lerp(cr, SETTLED[0], w); L[i + 1] = lerp(cg, SETTLED[1], w); L[i + 2] = lerp(cb, SETTLED[2], w);
        L[i + 3] = ca; // coverage crossfades to the separately cached raw alpha during paint
      }
    }
    return (lut = L);
  }

  function layoutFor(word) {
    const W = canvas.width, Hh = canvas.height;
    const key = [word, W, Hh, P.fontFamily, P.fontWeight, P.size, P.caps, P.stretchX, P.fit, P.blur, P.anisotropy, P.levels, fontGen].join('|');
    const hit = cache.get(word);
    if (hit && hit.key === key) return hit;
    const s = Math.min(W, Hh) / 800;
    const caps = isCaps(word);
    let em = caps ? 75 * s * 1.36 * P.size : 75 * s * 1.55 * P.size;
    const family = fontFamily(canvas, P.fontFamily);
    const font = (px) => `${P.fontWeight} ${px}px ${family}`;
    ctx.save(); ctx.font = font(em);
    let tm = ctx.measureText(word);
    let inkW = ((tm.actualBoundingBoxLeft ?? 0) + (tm.actualBoundingBoxRight ?? tm.width)) * P.stretchX;
    const maxW = P.fit * W;
    if (inkW > maxW) { em *= maxW / inkW; ctx.font = font(em); tm = ctx.measureText(word); inkW = ((tm.actualBoundingBoxLeft ?? 0) + (tm.actualBoundingBoxRight ?? tm.width)) * P.stretchX; }
    ctx.restore();
    const baseline = Hh / 2 + em * (caps ? 0.36 : 0.28);
    const inkL = W / 2 - inkW / 2;
    const textX = inkL + (tm.actualBoundingBoxLeft ?? 0) * P.stretchX; // pen x
    const asc = tm.actualBoundingBoxAscent ?? em * 0.75, desc = tm.actualBoundingBoxDescent ?? em * 0.2;
    const maxSigma = P.blur * em;
    const padX = Math.ceil(3 * maxSigma) + 2, padY = Math.ceil((3 * maxSigma) / P.anisotropy) + 2;
    const rx0 = Math.max(0, Math.floor(inkL - padX)), rx1 = Math.min(W, Math.ceil(inkL + inkW + padX));
    const ry0 = Math.max(0, Math.floor(baseline - asc - padY)), ry1 = Math.min(Hh, Math.ceil(baseline + desc + padY));
    const rw = Math.max(1, rx1 - rx0), rh = Math.max(1, ry1 - ry0);

    const c = makeCanvas(rw, rh, P.createCanvas), cc = c.getContext('2d');
    cc.font = font(em); cc.fillStyle = '#fff'; cc.textBaseline = 'alphabetic';
    cc.setTransform(P.stretchX, 0, 0, 1, textX - rx0, baseline - ry0);
    cc.fillText(word, 0, 0);
    const px = cc.getImageData(0, 0, rw, rh).data;
    const raw = new Uint8ClampedArray(rw * rh);
    for (let i = 0; i < raw.length; i++) raw[i] = px[i * 4 + 3];

    // blur levels: sigma_k = maxSigma * (k / (L-1))^1.5 — denser near sharp, where the eye is picky
    const L = P.levels, levels = [raw], sig = [0];
    for (let k = 1; k < L; k++) {
      const sg = maxSigma * Math.pow(k / (L - 1), 1.5);
      sig.push(sg);
      levels.push(gaussBlur(raw, rw, rh, sg, sg / P.anisotropy));
    }
    cc.setTransform(1, 0, 0, 1, 0, 0);
    cc.globalCompositeOperation = 'source-in';
    cc.fillStyle = css(SETTLED);
    cc.fillRect(0, 0, rw, rh);
    const lay = { key, word, em, maxSigma, inkL, inkW, rx0, ry0, rw, rh, levels, sig, settled: c };
    cache.set(word, lay);
    if (cache.size > 8) cache.delete(cache.keys().next().value);
    if (typeof document !== 'undefined' && document.fonts) {
      try { if (!document.fonts.check(font(Math.round(em)), word)) document.fonts.load(font(Math.round(em)), word).then(() => { if (!destroyed) { fontGen++; reducedPainted = ''; } }, () => {}); } catch { /* ignore */ }
    }
    return lay;
  }

  function levelFor(lay, sigmaPx) {
    if (sigmaPx < 1.5 * lay.em / 102) return 0;
    const k = (P.levels - 1) * Math.pow(Math.min(1, sigmaPx / lay.maxSigma), 1 / 1.5);
    return k;
  }

  function paint(word, tReveal) {
    const W = canvas.width, Hh = canvas.height;
    const lay = layoutFor(word), L = buildLut();
    const transparent = P.background === 'transparent' || P.background == null;
    const bg = transparent ? [0, 0, 0] : parseColor(P.background, P.createCanvas);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1;
    if (transparent) ctx.clearRect(0, 0, W, Hh); else { ctx.fillStyle = css(bg); ctx.fillRect(0, 0, W, Hh); }
    if (tReveal >= 1192) {
      ctx.drawImage(lay.settled, lay.rx0, lay.ry0);
      return;
    }

    const { rw, rh, rx0, ry0, levels } = lay;
    if (!image || image.width !== rw || image.height !== rh) image = ctx.createImageData(rw, rh);
    const out = image.data;
    const rows = P.qRows, maxRow = rows - 1;
    const levelsN = P.levels;
    for (let x = 0; x < rw; x++) {
      const xn = (rx0 + x + 0.5 - lay.inkL) / lay.inkW;
      const q = (tReveal - H_CURVE(xn)) / R_CURVE(clamp01(xn));
      if (q <= 0) {
        for (let y = 0; y < rh; y++) { const o = (y * rw + x) * 4; out[o] = bg[0]; out[o + 1] = bg[1]; out[o + 2] = bg[2]; out[o + 3] = transparent ? 0 : 255; }
        continue;
      }
      const qc = Math.min(1, q);
      const crisp = smoothstep((qc - P.crispStart) / (1 - P.crispStart));
      const sPx = sigmaNorm(qc) * P.blur * lay.em;
      const lf = Math.min(levelsN - 1, levelFor(lay, sPx));
      const l0 = Math.floor(lf), l1 = Math.min(levelsN - 1, l0 + 1), lt = lf - l0;
      const A0 = levels[l0], A1 = levels[l1];
      const rf = qc * maxRow, r0 = Math.floor(rf), r1 = Math.min(maxRow, r0 + 1), rt = rf - r0;
      const b0 = r0 * 1024, b1 = r1 * 1024;
      for (let y = 0; y < rh; y++) {
        const i = y * rw + x, o = i * 4;
        const av = A0[i] + (A1[i] - A0[i]) * lt;
        const v0 = av | 0, v1 = v0 < 255 ? v0 + 1 : 255, vt = av - v0;
        // bilinear over (q row, alpha)
        const i00 = b0 + v0 * 4, i01 = b0 + v1 * 4, i10 = b1 + v0 * 4, i11 = b1 + v1 * 4;
        const w00 = (1 - rt) * (1 - vt), w01 = (1 - rt) * vt, w10 = rt * (1 - vt), w11 = rt * vt;
        const thermalAlpha = L[i00 + 3] * w00 + L[i01 + 3] * w01 + L[i10 + 3] * w10 + L[i11 + 3] * w11;
        const ca = lerp(thermalAlpha, levels[0][i] / 255, crisp);
        if (ca <= 0.0005) { out[o] = bg[0]; out[o + 1] = bg[1]; out[o + 2] = bg[2]; out[o + 3] = transparent ? 0 : 255; continue; }
        const cr = L[i00] * w00 + L[i01] * w01 + L[i10] * w10 + L[i11] * w11;
        const cg = L[i00 + 1] * w00 + L[i01 + 1] * w01 + L[i10 + 1] * w10 + L[i11 + 1] * w11;
        const cb = L[i00 + 2] * w00 + L[i01 + 2] * w01 + L[i10 + 2] * w10 + L[i11 + 2] * w11;
        if (transparent) { out[o] = cr; out[o + 1] = cg; out[o + 2] = cb; out[o + 3] = ca * 255; }
        else { out[o] = bg[0] + (cr - bg[0]) * ca; out[o + 1] = bg[1] + (cg - bg[1]) * ca; out[o + 2] = bg[2] + (cb - bg[2]) * ca; out[o + 3] = 255; }
      }
    }
    ctx.putImageData(image, rx0, ry0);
  }

  function draw(timeMs = 0) {
    if (destroyed) return;
    const t = +timeMs || 0;
    const words = P.words && P.words.length ? P.words : [''];
    if (reduced()) {
      const w = P.word ?? words[0];
      const k = w + '|' + canvas.width + 'x' + canvas.height + '|' + fontGen + '|' + P.background;
      if (reducedPainted !== k) { paint(w, P.loopMs - 1); reducedPainted = k; }
      return;
    }
    reducedPainted = '';
    if (P.word != null) {
      if (P.word !== controlledWord || controlledStart == null || t < controlledStart) { controlledWord = P.word; controlledStart = t; }
      paint(P.word, Math.min(P.loopMs - 1, t - controlledStart));
      return;
    }
    // Uncontrolled: the word index is a pure function of the host clock, so every copy
    // driven by the same clock shows the same word. The reveal loop (4000) outlasts the
    // swap (3000), so a swap always lands on the settled wordmark.
    const idx = Math.floor(t / P.swapMs);
    const word = words[mod(idx, words.length)];
    paint(word, mod(t, P.swapMs) % P.loopMs);
  }

  function update(next = {}) {
    P = { ...P, ...next };
    applySize(canvas, P);
    reducedPainted = '';
  }

  applySize(canvas, P);
  return { update, draw, destroy() { destroyed = true; cache.clear(); lut = null; image = null; } };
}

/* -------------------------------------------------- shared molten clock */
// For several Molten copies on one page: one module-level timer that every copy
// subscribes to, so they can never drift onto different words.
const _subs = new Set(); let _raf = 0, _t0 = 0;
export function subscribeSharedClock(fn) {
  _subs.add(fn);
  if (!_raf && typeof requestAnimationFrame === 'function') {
    _t0 = performance.now();
    const tick = (now) => { const t = now - _t0; for (const f of _subs) f(t); _raf = _subs.size ? requestAnimationFrame(tick) : 0; };
    _raf = requestAnimationFrame(tick);
  }
  return () => { _subs.delete(fn); if (!_subs.size && _raf) { cancelAnimationFrame(_raf); _raf = 0; } };
}
