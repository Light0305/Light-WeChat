import { ROW_Y, DASH_H, REF_W } from '../design-how/dash-cascade/assets/template/params';
import { splitGraphemes } from './renderers.js';
import type { DashScene } from './dash-cascade-engine';

export function dashCascadeProps(lines: string[]) {
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d', { willReadFrequently: true })!;
  const font = '900 180px "Microsoft YaHei", Arial, sans-serif';
  context.font = font;
  const scenes = lines.map(line => {
    const glyphs = splitGraphemes(line).map((text: string) => ({ text, metric: context.measureText(text) }));
    const widths = glyphs.map(({ text, metric }) => {
      if (!text.trim()) return Math.max(32, metric.width);
      return Math.max(12, Math.ceil(metric.actualBoundingBoxLeft + metric.actualBoundingBoxRight));
    });
    const ascent = Math.max(1, ...glyphs.map(({ metric }) => metric.actualBoundingBoxAscent));
    const descent = Math.max(0, ...glyphs.map(({ metric }) => metric.actualBoundingBoxDescent));
    const tracking = DASH_H + 14;
    const inkWidth = widths.reduce((total, width) => total + width, 0) + tracking * (widths.length - 1);
    const width = Math.max(REF_W, inkWidth + 2 * (DASH_H + 36));
    const rows: DashScene['rows'] = ROW_Y.map(() => []);
    const top = ROW_Y[0] - DASH_H / 2;
    const height = ROW_Y.at(-1)! - top + DASH_H / 2;
    let left = (REF_W - inkWidth) / 2;
    for (const [index, { text, metric }] of glyphs.entries()) {
      const span = widths[index];
      if (text.trim()) {
        canvas.width = span + 2;
        canvas.height = Math.ceil(ROW_Y.at(-1)!) + 1;
        context.font = font;
        context.textBaseline = 'alphabetic';
        context.translate(0, top);
        context.scale(1, height / (ascent + descent));
        context.fillText(text, metric.actualBoundingBoxLeft + 1, ascent);
        const mask = context.getImageData(0, 0, canvas.width, canvas.height).data;
        const delayGroup = Math.min(2, Math.floor(index * 3 / glyphs.length));
        for (const [row, y] of ROW_Y.entries()) {
          let start = -1;
          for (let x = 0; x <= canvas.width; x++) {
            const filled = x < canvas.width && mask[(Math.round(y) * canvas.width + x) * 4 + 3] > 100;
            if (filled && start < 0) start = x;
            if (!filled && start >= 0) {
              rows[row].push([left + start - 1, left + x - 2, delayGroup]);
              start = -1;
            }
          }
        }
      }
      left += span + tracking;
    }
    return { rows, width };
  });
  return { scenes, lines };
}
