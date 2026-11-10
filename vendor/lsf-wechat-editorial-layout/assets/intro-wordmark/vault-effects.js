import { WordCarousel } from "../design-how/word-carousel/assets/template/engine";
import { LOOP } from "../design-how/word-carousel/assets/template/params";
import { RollType } from "../design-how/roll-type/assets/template/engine";
import { DEFAULT_PHRASES, loopMs } from "../design-how/roll-type/assets/template/params";

function words(value) {
  return (Array.isArray(value) ? value : [value]).filter(Boolean);
}

export function createCarousel(canvas, initial) {
  const engine = new WordCarousel(canvas);
  let reduced = false;
  function update(props) {
    const list = words(props.text);
    engine.setWords(Array.from({ length: 4 }, (_, index) => list[index % list.length]));
    if (props.width && props.height) engine.setSize(props.width, props.height);
    if (props.reducedMotion !== undefined) reduced = props.reducedMotion;
  }
  update(initial);
  return {
    update,
    draw: time => reduced ? engine.renderStill() : engine.render(time),
    duration: () => LOOP * 1000,
    destroy: () => engine.destroy(),
  };
}

export function createRoll(canvas, initial) {
  let engine;
  let previous;
  let phrases;
  let reduced = false;
  function update(props) {
    const next = JSON.stringify(props.text);
    if (next !== previous) {
      previous = next;
      phrases = words(props.text).map((text, index) => ({
        ...DEFAULT_PHRASES[index % DEFAULT_PHRASES.length],
        lines: [[text]],
      }));
      engine?.destroy();
      engine = new RollType(canvas, { phrases, family: props.fontFamily, weight: 800 });
    }
    if (props.width && props.height) {
      canvas.width = props.width;
      canvas.height = props.height;
    }
    if (props.reducedMotion !== undefined) reduced = props.reducedMotion;
  }
  update(initial);
  return {
    update,
    draw: time => reduced ? engine.renderStill() : engine.render(time),
    duration: () => loopMs(phrases),
    destroy: () => engine.destroy(),
  };
}

// Article banner adaptation of the Emboss silhouette and moving-light effect.
export function createLogoEmboss(canvas, initial) {
  const ctx = canvas.getContext("2d");
  const mask = document.createElement("canvas");
  const alpha = mask.getContext("2d");
  const layers = ["#fff", "#6e6c84", "#b6b4cc"].map(color => ({
    color, canvas: document.createElement("canvas"),
  }));
  let props = {};
  function update(next) {
    const rebuild = next.logo !== props.logo || next.text !== props.text
      || (next.width && next.width !== canvas.width) || (next.height && next.height !== canvas.height);
    props = { ...props, ...next };
    if (next.width && next.width !== canvas.width) canvas.width = next.width;
    if (next.height && next.height !== canvas.height) canvas.height = next.height;
    if (!rebuild) return;
    const { width, height } = canvas;
    mask.width = width;
    mask.height = height;
    if (props.logo) {
      const { naturalWidth, naturalHeight } = props.logo;
      const scale = Math.min(width * .62 / naturalWidth, height * .61 / naturalHeight);
      const w = naturalWidth * scale;
      const h = naturalHeight * scale;
      alpha.drawImage(props.logo, (width - w) / 2, (height - h) / 2, w, h);
    } else {
      alpha.font = `800 ${Math.round(height * .36)}px ${props.fontFamily}`;
      alpha.textAlign = "center";
      alpha.textBaseline = "middle";
      alpha.fillText(String(props.text), width / 2, height / 2, width * .78);
    }
    for (const layer of layers) {
      layer.canvas.width = width;
      layer.canvas.height = height;
      const shade = layer.canvas.getContext("2d");
      shade.drawImage(mask, 0, 0);
      shade.globalCompositeOperation = "source-in";
      shade.fillStyle = layer.color;
      shade.fillRect(0, 0, width, height);
    }
  }
  update(initial);
  return {
    update,
    duration: () => 2400,
    destroy() {},
    draw(time) {
      const { width, height } = canvas;
      const phase = props.reducedMotion ? 0 : time / 2400 * Math.PI * 2;
      const light = Math.cos(phase) * .25 + .5;
      const ground = ctx.createLinearGradient(0, 0, width, height);
      ground.addColorStop(0, "#eeedf7");
      ground.addColorStop(light, "#d8d6e7");
      ground.addColorStop(1, "#c4c2d8");
      ctx.fillStyle = ground;
      ctx.fillRect(0, 0, width, height);
      const dx = Math.cos(phase) * height * .015;
      const dy = Math.sin(phase) * height * .009 + height * .009;
      ctx.drawImage(layers[0].canvas, -dx, -dy);
      ctx.drawImage(layers[1].canvas, dx, dy);
      ctx.drawImage(layers[2].canvas, 0, 0);
    },
  };
}
