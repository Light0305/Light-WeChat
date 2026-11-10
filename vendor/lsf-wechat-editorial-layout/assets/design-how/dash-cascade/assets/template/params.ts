// Dash cascade (https://design.how/vault/dash-cascade), params.ts.
// VARIABLE: WORDS, INK, BG, HUE_SPREAD_DEG, HUE_DRIFT_S, FPS. Change these freely. Everything else here is FIXED: it is the effect, so changing it makes a different visual.
export const REF_W = 600;
export const REF_H = 337;
export const FPS = 10;
export const FRAMES = 25;

export const BG = "#ffffff";
export const INK = "#f2c94c";

export const HUE_WAVES: {
  u: number;
  v: number;
  speed: number;
  weight: number;
}[] = [
  { u: 0.9, v: 0.35, speed: 1.0, weight: 0.5 },
  { u: -0.55, v: 1.3, speed: -1.37, weight: 0.32 },
  { u: 1.7, v: -0.8, speed: 0.61, weight: 0.18 },
];

export const HUE_SPREAD_DEG = 14;

export const LIGHT_SPREAD = 0.035;

export const HUE_LAYERS = 7;

export const HUE_DRIFT_S = 60;

export const HOVER_SAT_LIFT = 0.07;
export const HOVER_DRIFT_GAIN = 1.6;
export const HOVER_EASE_S = 0.5;

export const ROW_Y = [76.5, 97, 117, 137.5, 158, 178, 198.5, 219, 239, 259.5];
export const DASH_H = 18;

export const AXIS = 281.5;

export const CONTENT_MID = 168;

export const WAVE = [
  0.001, 0.003, 0.009, 0.028, 0.07, 0.148, 0.334, 0.674, 0.872, 0.95, 0.985,
  0.998, 0.998, 0.985, 0.95, 0.873, 0.676, 0.33, 0.129, 0.052, 0.016, 0.003,
  0.001, 0.0, 0.001,
];
export const WAVE_LEAD = 6.5;

export const DOWN_AT = 4.85;
export const DOWN_RATE = 0.58;
export const DOWN_TILT = 0.003;
export const UP_AT = 4.56;
export const UP_RATE = 0.42;
export const PINCH_DOWN: [number, number] = [4.98, 0.68];
export const PINCH_UP: [number, number] = [4.73, 0.4];

export let WORDS: [number, number, number][][][] = [
  [
    [[20, 64, 0], [237, 389, 1], [473, 517, 2]],
    [[20, 64, 0], [237, 281, 1], [345, 389, 1], [473, 517, 2]],
    [[20, 64, 0], [237, 281, 1], [345, 389, 1], [473, 517, 2]],
    [[20, 64, 0], [237, 281, 1], [345, 389, 1], [473, 517, 2]],
    [[20, 64, 0], [237, 281, 1], [345, 389, 1], [473, 517, 2]],
    [[20, 64, 0], [237, 281, 1], [345, 389, 1], [473, 517, 2]],
    [[20, 64, 0], [237, 281, 1], [345, 389, 1], [473, 517, 2]],
    [[20, 64, 0], [237, 281, 1], [345, 389, 1], [473, 517, 2]],
    [[20, 205, 0], [237, 281, 1], [345, 389, 1], [473, 582, 2]],
    [[20, 205, 0], [237, 389, 1], [473, 582, 2]],
  ],
  [
    [[90.5, 134.5, 0], [237, 281, 1], [281, 389, 1], [473, 582, 2]],
    [[82.7, 142.3, 0], [237, 281, 1], [345, 389, 1], [473, 582, 2]],
    [[74.8, 150.2, 0], [237, 281, 1], [345, 389, 1], [505.5, 549.5, 2]],
    [[67.0, 111.0, 0], [114.0, 158.0, 0], [237, 281, 1], [345, 389, 1], [505.5, 549.5, 2]],
    [[59.2, 103.2, 0], [121.8, 165.8, 0], [237, 281, 1], [281, 389, 1], [505.5, 549.5, 2]],
    [[51.3, 95.3, 0], [129.7, 173.7, 0], [237, 281, 1], [505.5, 549.5, 2]],
    [[43.5, 181.5, 0], [237, 281, 1], [281.0, 325.0, 1], [505.5, 549.5, 2]],
    [[35.7, 189.3, 0], [237, 281, 1], [302.3, 346.3, 1], [505.5, 549.5, 2]],
    [[27.8, 71.8, 0], [153.2, 197.2, 0], [237, 281, 1], [323.7, 367.7, 1], [505.5, 549.5, 2]],
    [[20.0, 64.0, 0], [161.0, 205.0, 0], [237, 281, 1], [345.0, 389.0, 1], [505.5, 549.5, 2]],
  ],
  [
    [[20, 205, 0], [237, 281, 1], [281, 389, 1], [473.0, 517.0, 2], [538.0, 582.0, 2]],
    [[20, 205, 0], [237, 281, 1], [345, 389, 1], [481.1, 525.1, 2], [529.9, 573.9, 2]],
    [[90.5, 134.5, 0], [237, 281, 1], [345, 389, 1], [489.2, 565.8, 2]],
    [[90.5, 134.5, 0], [237, 281, 1], [345, 389, 1], [497.4, 557.6, 2]],
    [[90.5, 134.5, 0], [237, 281, 1], [281, 389, 1], [505.5, 549.5, 2]],
    [[90.5, 134.5, 0], [237, 281, 1], [505.5, 549.5, 2]],
    [[90.5, 134.5, 0], [237, 281, 1], [281.0, 325.0, 1], [505.5, 549.5, 2]],
    [[90.5, 134.5, 0], [237, 281, 1], [302.3, 346.3, 1], [505.5, 549.5, 2]],
    [[90.5, 134.5, 0], [237, 281, 1], [323.7, 367.7, 1], [505.5, 549.5, 2]],
    [[90.5, 134.5, 0], [237, 281, 1], [345.0, 389.0, 1], [505.5, 549.5, 2]],
  ],
  [
    [[20, 205, 0], [237, 389, 1], [473.0, 517.0, 2], [538.0, 582.0, 2]],
    [[20, 205, 0], [237, 281, 1], [345, 389, 1], [481.1, 525.1, 2], [529.9, 573.9, 2]],
    [[90.5, 134.5, 0], [237, 281, 1], [345, 389, 1], [489.2, 565.8, 2]],
    [[90.5, 134.5, 0], [237, 281, 1], [345, 389, 1], [497.4, 557.6, 2]],
    [[90.5, 134.5, 0], [237, 281, 1], [345, 389, 1], [505.5, 549.5, 2]],
    [[90.5, 134.5, 0], [237, 281, 1], [345, 389, 1], [505.5, 549.5, 2]],
    [[90.5, 134.5, 0], [237, 281, 1], [345, 389, 1], [505.5, 549.5, 2]],
    [[90.5, 134.5, 0], [237, 281, 1], [345, 389, 1], [505.5, 549.5, 2]],
    [[90.5, 134.5, 0], [237, 281, 1], [345, 389, 1], [505.5, 549.5, 2]],
    [[90.5, 134.5, 0], [237, 389, 1], [505.5, 549.5, 2]],
  ],
];

export const LOOPS_PER_WORD = 1;

export const LETTER_CENTER = [112.5, 313, 495];

// Sample the user's glyph mask into the same ten rows and three delay groups.
export function setPreviewCopy(lines: readonly string[]) {
  const canvas = document.createElement("canvas");
  canvas.width = REF_W;
  canvas.height = REF_H;
  const ctx = canvas.getContext("2d", { willReadFrequently: true })!;
  ctx.font = '900 180px "Microsoft YaHei", Arial, sans-serif';
  ctx.textAlign = "center";
  ctx.textBaseline = "alphabetic";

  WORDS = lines.map(line => {
    ctx.clearRect(0, 0, REF_W, REF_H);
    const metrics = ctx.measureText(line);
    const ascent = metrics.actualBoundingBoxAscent || 130;
    const descent = metrics.actualBoundingBoxDescent || 0;
    const height = ROW_Y[ROW_Y.length - 1] - ROW_Y[0] + DASH_H;
    ctx.save();
    ctx.translate(REF_W / 2, ROW_Y[0] - DASH_H / 2);
    ctx.scale(1, height / (ascent + descent));
    ctx.fillText(line, 0, ascent, REF_W - 44);
    ctx.restore();

    const pixels = ctx.getImageData(0, 0, REF_W, REF_H).data;
    const width = Math.min(metrics.width, REF_W - 44);
    const left = (REF_W - width) / 2;
    return ROW_Y.map(y => {
      const runs: [number, number, number][] = [];
      let start = -1;
      for (let x = 0; x <= REF_W; x++) {
        const filled = x < REF_W && pixels[(Math.round(y) * REF_W + x) * 4 + 3] > 100;
        if (filled && start < 0) start = x;
        if (!filled && start >= 0) {
          const group = Math.max(0, Math.min(2, Math.floor((((start + x) / 2 - left) / width) * 3)));
          runs.push([start, x - 1, group]);
          start = -1;
        }
      }
      return runs;
    });
  });
}
