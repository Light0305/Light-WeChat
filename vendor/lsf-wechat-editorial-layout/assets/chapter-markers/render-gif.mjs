export async function createChapterMarkerRenderer(upstream) {
  const { render } = await import(new URL("lib/initialis.js", upstream));
  const { GIFEncoder, quantize, applyPalette } = await import(new URL("render/vendor/gifenc.esm.js", upstream));
  return async (text, { size, frames, frameMs, holdMs, params }) => {
    const context = new OffscreenCanvas(size, size).getContext("2d", { willReadFrequently: true });
    const samples = [];
    for (let frame = 0; frame < frames; frame++) {
      const time = (1 - Math.cos(Math.PI * frame / (frames - 1))) / 2;
      const bitmap = await render({ ...params, text }, { size, paper: false, time });
      context.clearRect(0, 0, size, size);
      context.drawImage(bitmap, 0, 0);
      bitmap.close();
      samples.push(context.getImageData(0, 0, size, size).data);
    }

    const colors = quantize(samples.at(-1), 255, { format: "rgb444" });
    const palette = [[0, 0, 0], ...colors];
    const indexed = samples.map((rgba) => {
      const pixels = applyPalette(rgba, colors, "rgb444");
      for (let i = 0; i < pixels.length; i++) {
        pixels[i] = rgba[i * 4 + 3] < 128 ? 0 : pixels[i] + 1;
      }
      return pixels;
    });
    const gif = GIFEncoder();
    const write = (index, delay) => gif.writeFrame(indexed[index], size, size, {
      palette: index === 0 ? palette : null, delay, transparent: true, transparentIndex: 0, dispose: 2, repeat: 0
    });
    for (let i = 0; i < frames; i++) write(i, i === frames - 1 ? holdMs : frameMs);
    for (let i = frames - 2; i > 0; i--) write(i, frameMs);
    gif.finish();
    return new Blob([gif.bytes()], { type: "image/gif" });
  };
}
