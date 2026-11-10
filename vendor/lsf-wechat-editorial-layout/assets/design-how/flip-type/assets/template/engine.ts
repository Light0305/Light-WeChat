// Flip type (https://design.how/vault/flip-type), engine.ts.
// FIXED. Change the VARIABLE values in params instead (GROUND, INK, PLAY_RATE, BREATH, BOUNCE, FONT_VAR).
import {
  FONT_SIZE,
  FONT_WEIGHT,
  FRAMES,
  FRAME_MS,
  GROUND,
  INK,
  LOOP_MS,
  POKE,
  STILL_FRAME,
  lettersAt,
  pokeSeq,
  resting,
  wordParts,
  type Glyph,
  type Poke,
} from "./params";

export class FlipType {
  private ctx: CanvasRenderingContext2D | null;
  private raf = 0;
  private running = false;
  private t0 = 0;
  private elapsed = 0;
  private dpr = 1;
  private w = 0;
  private h = 0;
  private lastFrame = -1;
  private pokes: Poke[] = [];
  private lastPoke = new Map<number, number>();
  private glyphMetrics = new Map<string, TextMetrics>();
  private pens: number[][] = [];
  private halfWidth = 1;
  private ascent = 1;
  private descent = 0;
  private minRow = 0;
  private maxRow = 1;
  private scale = 1;
  private rowScale = 1;
  private top = 0;
  private readonly font: string;
  private readonly parts = wordParts;

  readonly ok: boolean;

  constructor(
    private canvas: HTMLCanvasElement,
    private family: string,
  ) {
    this.ctx = canvas.getContext("2d");
    this.font = `${FONT_WEIGHT} ${FONT_SIZE}px ${this.family}`;
    this.ok = !!this.ctx;
    if (this.ok) {
      this.measure();
      this.resize();
    }
  }

  private metric(glyph: string): TextMetrics {
    const cached = this.glyphMetrics.get(glyph);
    if (cached) return cached;
    const measured = this.ctx!.measureText(glyph);
    this.glyphMetrics.set(glyph, measured);
    return measured;
  }

  private measure() {
    const ctx = this.ctx!;
    ctx.font = this.font;
    ctx.fontKerning = "none";
    ctx.textAlign = "left";
    this.pens = this.parts.map(parts => {
      const widths = parts.map(part => this.metric(part).width);
      let pen = -widths.reduce((sum, width) => sum + width, 0) / 2;
      return widths.map(width => {
        const x = pen;
        pen += width;
        return x;
      });
    });
    const pokeMetrics = Array.from("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz", glyph => this.metric(glyph));
    const extraLeft = Math.max(...pokeMetrics.map(metric => metric.actualBoundingBoxLeft));
    const extraRight = Math.max(...pokeMetrics.map(metric => metric.actualBoundingBoxRight));
    this.ascent = Math.max(1, ...pokeMetrics.map(metric => metric.actualBoundingBoxAscent));
    this.descent = Math.max(0, ...pokeMetrics.map(metric => metric.actualBoundingBoxDescent));
    this.minRow = Infinity;
    this.maxRow = -Infinity;
    for (let frame = 0; frame < FRAMES; frame++) {
      for (const glyph of lettersAt(frame, [], this.parts)) {
        const x = this.pens[glyph.word][glyph.slot];
        const metric = this.metric(glyph.glyph);
        this.halfWidth = Math.max(this.halfWidth, -x + Math.max(extraLeft, metric.actualBoundingBoxLeft),
          x + Math.max(extraRight, metric.actualBoundingBoxRight));
        this.ascent = Math.max(this.ascent, metric.actualBoundingBoxAscent);
        this.descent = Math.max(this.descent, metric.actualBoundingBoxDescent);
        this.minRow = Math.min(this.minRow, glyph.y);
        this.maxRow = Math.max(this.maxRow, glyph.y);
      }
    }
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
    const inkHeight = this.ascent + this.descent;
    this.scale = Math.min(c.width * 0.92 / (2 * this.halfWidth), c.height * 0.26 / inkHeight);
    this.rowScale = (c.height * 0.88 - inkHeight * this.scale) / Math.max(1, this.maxRow - this.minRow);
    this.top = c.height * 0.06 + this.ascent * this.scale;
    this.lastFrame = -1;
    if (!this.running) this.renderStill();
  }

  frame(): number {
    const total = this.running ? this.elapsed + (performance.now() - this.t0) : this.elapsed;
    return Math.floor((total % LOOP_MS) / FRAME_MS);
  }

  poke(x: number, y: number) {
    if (!this.running) return;
    x = (x - 0.5) * this.canvas.width / this.scale;
    y *= this.canvas.height;
    const f = this.frame();
    for (const g of lettersAt(f, this.pokes, this.parts)) {
      if (!resting(g, this.parts)) continue;
      const pen = this.pens[g.word][g.slot];
      const baseline = this.baseline(g.y);
      const ink = this.metric(g.glyph);
      if (x < pen - ink.actualBoundingBoxLeft || x > pen + ink.actualBoundingBoxRight
        || y < baseline - ink.actualBoundingBoxAscent * this.scale || y > baseline + ink.actualBoundingBoxDescent * this.scale) continue;
      const key = g.word * 16 + g.slot;
      const last = this.lastPoke.get(key);
      if (last !== undefined && ((f - last + FRAMES) % FRAMES) < POKE.cooldown) return;
      this.lastPoke.set(key, f);
      this.pokes.push({ slot: g.slot, word: g.word, at: f, seq: pokeSeq(g.slot, f, g.glyph) });
      this.lastFrame = -1;
      return;
    }
  }

  private baseline(y: number): number {
    return this.top + (y - this.minRow) * this.rowScale;
  }

  private paint(frame: number) {
    const ctx = this.ctx;
    if (!ctx) return;
    const k = this.scale;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = GROUND;
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    ctx.setTransform(k, 0, 0, k, this.canvas.width / 2, 0);
    ctx.font = this.font;
    ctx.fontKerning = "none";
    ctx.textBaseline = "alphabetic";
    ctx.textAlign = "left";
    ctx.fillStyle = INK;
    const glyphs: Glyph[] = lettersAt(frame, this.pokes, this.parts);
    for (const g of glyphs) ctx.fillText(g.glyph, this.pens[g.word][g.slot], this.baseline(g.y) / k);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    if (this.pokes.length) {
      this.pokes = this.pokes.filter((p) => ((frame - p.at + FRAMES) % FRAMES) < POKE.hold * p.seq.length + 1);
    }
  }

  render(frame: number) {
    this.paint(((Math.floor(frame) % FRAMES) + FRAMES) % FRAMES);
  }

  renderStill() {
    this.render(STILL_FRAME);
  }

  start() {
    if (this.running || !this.ok) return;
    this.running = true;
    this.t0 = performance.now();
    this.lastFrame = -1;
    const tick = () => {
      if (!this.running) return;
      const frame = this.frame();
      if (frame !== this.lastFrame) {
        this.lastFrame = frame;
        this.paint(frame);
      }
      this.raf = requestAnimationFrame(tick);
    };
    this.raf = requestAnimationFrame(tick);
  }

  stop() {
    if (this.running) this.elapsed = (this.elapsed + (performance.now() - this.t0)) % LOOP_MS;
    this.running = false;
    cancelAnimationFrame(this.raf);
  }

  destroy() {
    this.stop();
    this.ctx = null;
  }
}
