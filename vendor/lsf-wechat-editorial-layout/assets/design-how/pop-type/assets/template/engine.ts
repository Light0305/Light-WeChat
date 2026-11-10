// Pop type (https://design.how/vault/pop-type), engine.ts.
// FIXED. Change the VARIABLE values in params instead (PALETTE, GROUND, WORD, CONTACT_MS, SQUASH, SWELL_PEAK, FONT_VAR).
import {
  FONT_WEIGHT,
  FRAME_MS,
  GROUND,
  LOOP_MS,
  MARK,
  POP_CENTRE,
  POP_DASH,
  POP_MS,
  POP_RADIUS,
  POP_SPOKES,
  SCENE_H,
  SCENE_W,
  STILL_MS,
  WORD,
  bentBounds,
  bentStrips,
  dropPose,
  frameStart,
  layoutWord,
  markAt,
  popAt,
  poseBox,
  setFor,
  shadowOffset,
  shadowPose,
  swellAmp,
  type Box,
  type GlyphMetrics,
} from "./params";

const MEASURE_PX = 200;
const OVERSAMPLE = 1.6;
const SPRITE_PAD = 4;
const SCENE_CENTER_X = SCENE_W / 2;
const SCENE_CENTER_Y = SCENE_H / 2;
const BURST_EXTENT = POP_RADIUS.at1 + (POP_DASH.length + POP_DASH.width) / 2;
const STAGE_HALF_HEIGHT = Math.max(SCENE_CENTER_Y, Math.abs(POP_CENTRE.y - SCENE_CENTER_Y) + BURST_EXTENT);

interface Sprite {
  canvas: HTMLCanvasElement;
  ink: { x: number; y: number; w: number; h: number };
}

export class PopType {
  private ctx: CanvasRenderingContext2D | null;
  private raf = 0;
  private running = false;
  private t0 = 0;
  private elapsed = 0;
  private dpr = 1;
  private w = 0;
  private h = 0;
  private metrics: GlyphMetrics[] = [];
  private rests: Box[] = [];
  private stageHalfWidth = SCENE_CENTER_X;
  private sprites = new Map<string, Sprite>();
  private lastFrame = -1;

  readonly ok: boolean;

  constructor(
    private canvas: HTMLCanvasElement,
    private family: string = "sans-serif",
  ) {
    this.ctx = canvas.getContext("2d");
    this.ok = !!this.ctx;
    if (this.ok) {
      this.measure();
      this.resize();
    }
  }

  private font(px: number): string {
    return `${FONT_WEIGHT} ${px}px ${this.family}`;
  }

  refreshFont(family?: string) {
    if (family) this.family = family;
    this.measure();
    if (!this.running) this.renderStill();
  }

  resize() {
    const c = this.canvas;
    const box = c.getBoundingClientRect();
    const w = Math.max(1, Math.round(box.width));
    const h = Math.max(1, Math.round(box.height));
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    if (w === this.w && h === this.h && dpr === this.dpr) return;
    this.w = w;
    this.h = h;
    this.dpr = dpr;
    c.width = Math.round(w * dpr);
    c.height = Math.round(h * dpr);
    this.sprites.clear();
    this.lastFrame = -1;
    if (!this.running) this.renderStill();
  }

  private measure() {
    const g = document.createElement("canvas").getContext("2d");
    if (!g) return;
    g.font = this.font(MEASURE_PX);
    g.textBaseline = "alphabetic";
    g.textAlign = "left";
    this.metrics = WORD.map(chunk => {
      const m = g.measureText(chunk);
      return {
        left: -m.actualBoundingBoxLeft / MEASURE_PX,
        right: (chunk.trim() ? m.actualBoundingBoxRight : m.width) / MEASURE_PX,
        top: -m.actualBoundingBoxAscent / MEASURE_PX,
        bottom: m.actualBoundingBoxDescent / MEASURE_PX,
      };
    });
    this.rests = layoutWord(this.metrics).boxes;
    this.stageHalfWidth = this.measureStageHalfWidth();
    this.sprites.clear();
  }

  private measureStageHalfWidth(): number {
    const markReach = MARK.gap + MARK.spread + MARK.len;
    const reach = (box: Box) => Math.max(SCENE_CENTER_X - box.x0, box.x1 - SCENE_CENTER_X);
    let half = Math.max(SCENE_CENTER_X, Math.abs(POP_CENTRE.x - SCENE_CENTER_X) + BURST_EXTENT);
    for (const rest of this.rests) half = Math.max(half, reach(rest) + markReach);
    // Fit the widest rendered pose once, so the scale stays steady through the loop.
    for (let t = 0; t < POP_MS; t += FRAME_MS) {
      const swell = swellAmp(t);
      this.forEachGlyph(t, swell, (_i, _shadow, box) => {
        half = Math.max(half, reach(swell ? bentBounds(box, swell) : box));
      });
    }
    return half;
  }

  private scale(): number {
    return Math.min(this.canvas.width * 0.92 / (this.stageHalfWidth * 2), this.canvas.height * 0.96 / (STAGE_HALF_HEIGHT * 2));
  }

  private sprite(i: number, colour: string): Sprite {
    const key = `${i}:${colour}`;
    const hit = this.sprites.get(key);
    if (hit) return hit;
    const m = this.metrics[i];
    const rest = this.rests[i];
    const s = this.scale() * OVERSAMPLE;
    const fontPx = ((rest.bottom - rest.top) * s) / (m.bottom - m.top);
    const w = (m.right - m.left) * fontPx;
    const h = (m.bottom - m.top) * fontPx;
    const c = document.createElement("canvas");
    c.width = Math.ceil(w + 2 * SPRITE_PAD);
    c.height = Math.ceil(h + 2 * SPRITE_PAD);
    const g = c.getContext("2d");
    if (g) {
      g.font = this.font(fontPx);
      g.textBaseline = "alphabetic";
      g.textAlign = "left";
      g.fillStyle = colour;
      g.fillText(WORD[i], SPRITE_PAD - m.left * fontPx, SPRITE_PAD - m.top * fontPx);
    }
    const sp = { canvas: c, ink: { x: SPRITE_PAD, y: SPRITE_PAD, w, h } };
    this.sprites.set(key, sp);
    return sp;
  }

  private glyph(ctx: CanvasRenderingContext2D, i: number, colour: string, box: Box, A: number) {
    const bw = box.x1 - box.x0;
    const bh = box.bottom - box.top;
    if (bw <= 0 || bh <= 0) return;
    const sp = this.sprite(i, colour);
    const { ink } = sp;
    if (Math.abs(A) < 1e-3) {
      ctx.drawImage(sp.canvas, ink.x, ink.y, ink.w, ink.h, box.x0, box.top, bw, bh);
      return;
    }
    for (const st of bentStrips(box, A)) {
      const sy0 = ink.y + ink.h * st.from;
      const sy1 = ink.y + ink.h * st.to;
      ctx.drawImage(sp.canvas, ink.x, sy0, ink.w, sy1 - sy0, st.box.x0, st.box.top, st.box.x1 - st.box.x0, st.box.bottom - st.box.top);
    }
  }

  render(t: number, run = 0) {
    const ctx = this.ctx;
    if (!ctx) return;
    const f = frameStart(t);
    const k = this.scale();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = GROUND;
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    if (!this.rests.length) return;
    ctx.setTransform(k, 0, 0, k, this.canvas.width / 2 - SCENE_CENTER_X * k, this.canvas.height / 2 - SCENE_CENTER_Y * k);

    const set = setFor(run);
    if (f < POP_MS) this.word(ctx, f, set.face, set.shadow);
    else this.pop(ctx, f - POP_MS, setFor(run + 1).face);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
  }

  private forEachGlyph(t: number, swell: number, draw: (i: number, shadow: boolean, box: Box) => void) {
    const off = shadowOffset(swell);
    for (let i = 0; i < this.rests.length; i++) {
      if (!WORD[i].trim()) continue;
      const rest = this.rests[i];
      const sp = shadowPose(i, t);
      if (sp.live) {
        const b = poseBox(rest, sp);
        draw(i, true, { x0: b.x0 + off.x, x1: b.x1 + off.x, top: b.top + off.y, bottom: b.bottom + off.y });
      }
      const fp = dropPose(i, t);
      if (fp.live) draw(i, false, poseBox(rest, fp));
    }
  }

  private word(ctx: CanvasRenderingContext2D, t: number, face: string, shadow: string) {
    const A = swellAmp(t);
    this.forEachGlyph(t, A, (i, isShadow, box) => this.glyph(ctx, i, isShadow ? shadow : face, box, A));
    ctx.fillStyle = shadow;
    for (let i = 0; i < this.rests.length; i++) {
      if (!WORD[i].trim()) continue;
      const m = markAt(i, t);
      if (!m) continue;
      const rest = this.rests[i];
      const y = rest.bottom + 2;
      ctx.globalAlpha = m.alpha;
      ctx.fillRect(rest.x0 - m.spread - m.len, y, m.len, MARK.width);
      ctx.fillRect(rest.x1 + m.spread, y, m.len, MARK.width);
    }
    ctx.globalAlpha = 1;
  }

  private pop(ctx: CanvasRenderingContext2D, tau: number, colour: string) {
    const ring = popAt(tau);
    if (!ring || ring.alpha <= 0) return;
    ctx.save();
    ctx.globalAlpha = ring.alpha;
    ctx.strokeStyle = colour;
    ctx.lineWidth = POP_DASH.width;
    ctx.lineCap = "butt";
    ctx.beginPath();
    for (let i = 0; i < POP_SPOKES; i++) {
      const a = (i / POP_SPOKES) * Math.PI * 2;
      const c = Math.cos(a);
      const s = Math.sin(a);
      ctx.moveTo(POP_CENTRE.x + c * (ring.r - POP_DASH.length / 2), POP_CENTRE.y + s * (ring.r - POP_DASH.length / 2));
      ctx.lineTo(POP_CENTRE.x + c * (ring.r + POP_DASH.length / 2), POP_CENTRE.y + s * (ring.r + POP_DASH.length / 2));
    }
    ctx.stroke();
    ctx.restore();
  }

  start() {
    if (this.running || !this.ok) return;
    this.running = true;
    this.t0 = performance.now();
    const tick = (now: number) => {
      if (!this.running) return;
      const total = this.elapsed + (now - this.t0);
      const frame = Math.floor(total / FRAME_MS);
      if (frame !== this.lastFrame) {
        this.lastFrame = frame;
        const run = Math.floor(total / LOOP_MS);
        this.render(total - run * LOOP_MS, run);
      }
      this.raf = requestAnimationFrame(tick);
    };
    this.raf = requestAnimationFrame(tick);
  }

  stop() {
    if (this.running) this.elapsed += performance.now() - this.t0;
    this.running = false;
    cancelAnimationFrame(this.raf);
  }

  renderStill() {
    this.render(STILL_MS, 0);
  }

  destroy() {
    this.stop();
    this.metrics = [];
    this.rests = [];
    this.sprites.clear();
    this.ctx = null;
  }
}
