import { createChapterMarkerRenderer } from "./render-gif.mjs";

const gallery = new URL("https://initialis.azlen.me/#54852375");

async function readJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`无法读取 ${url}（HTTP ${response.status}）`);
  return response.json();
}

function letterLabel(number) {
  let label = "";
  while (number > 0) {
    number--;
    label = String.fromCharCode(65 + number % 26) + label;
    number = Math.floor(number / 26);
  }
  return label;
}

export async function drawGalleryChapters(mode, count) {
  if (mode !== "initialis" && mode !== "numbers") throw new Error("请选择字母或数字模式");
  if (!Number.isInteger(count) || count < 1 || count > 999) throw new Error("章节数需为 1–999");

  const [breed, fonts, kept] = await Promise.all([
    import(new URL("src/breed.js", gallery)),
    import(new URL("render/src/fonts.js", gallery)),
    readJson(new URL("render/data/kept.json", gallery)),
  ]);
  const seed = gallery.hash.slice(1);
  breed.setKept(kept);
  const field = new breed.Field(breed.decodeGen(seed), breed.fieldFonts(await fonts.fontList()));
  const candidates = [];
  for (let q = -3; q <= 3; q++) {
    for (let r = -3; r <= 3; r++) {
      if (breed.hexDist(q, r) > 3) continue;
      const params = field.at(q, r);
      if (params.orn === "none" && params.lFill === "none") continue;
      candidates.push({ cell: [q, r], params });
    }
  }
  if (!candidates.length) throw new Error("INITIĀLIS 画廊没有可抽取的样式");

  let remaining = [];
  let previous;
  const chapters = Array.from({ length: count }, (_, index) => {
    if (!remaining.length) remaining = candidates.slice();
    const pool = remaining.length > 1 ? remaining.filter(item => item !== previous) : remaining;
    const chosen = pool[Math.floor(Math.random() * pool.length)];
    remaining.splice(remaining.indexOf(chosen), 1);
    previous = chosen;
    const label = mode === "initialis" ? letterLabel(index + 1) : String(index + 1);
    return { label, ...chosen };
  });
  return { source: gallery.href, mode, chapters };
}

export async function createGalleryMarkerRenderer(mode, upstream) {
  if (mode === "numbers" && !upstream) throw new Error("数字模式需要已补入数字字形的 INITIĀLIS 引擎地址");
  const [render, base] = await Promise.all([
    createChapterMarkerRenderer(upstream || new URL("./", gallery)),
    readJson(new URL("initialis/preset.json", import.meta.url)),
  ]);
  return async ({ label, params }) => {
    if (mode === "initialis") {
      const images = [];
      for (const letter of label) images.push(await render(letter, { ...base, params }));
      return images;
    }
    const size = Math.min(params.size, label.length === 1 ? 0.67 : 0.70);
    return [await render(label, { ...base, params: { ...params, font: "cinzel-900", size } })];
  };
}
