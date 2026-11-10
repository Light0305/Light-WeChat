function paintScreenshotBackground(ctx, background, width, height) {
  if (background instanceof HTMLImageElement) {
    const scale = Math.max(width / background.naturalWidth, height / background.naturalHeight);
    const w = background.naturalWidth * scale;
    const h = background.naturalHeight * scale;
    ctx.drawImage(background, (width - w) / 2, (height - h) / 2, w, h);
    return;
  }
  ctx.fillStyle = background.base;
  ctx.fillRect(0, 0, width, height);
  for (const {color, opacity, blur, x, y, size, blend} of background.layers) {
    const cx = width * x / 100;
    const cy = height * y / 100;
    const radius = Math.max(width, height) * size / 100;
    const glow = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
    for (const [stop, strength] of [[0, 1], [.42, .72], [.78, .22], [1, 0]]) {
      glow.addColorStop(stop, color + Math.round(2.55 * opacity * strength).toString(16).padStart(2, '0'));
    }
    const softness = Math.min(width, height) * blur * .0016;
    ctx.save();
    ctx.globalCompositeOperation = blend;
    ctx.filter = `blur(${softness}px)`;
    ctx.fillStyle = glow;
    ctx.fillRect(-softness, -softness, width + 2 * softness, height + 2 * softness);
    ctx.restore();
  }
  if (background.grain) {
    const tile = document.createElement('canvas');
    tile.width = tile.height = 96;
    const grain = tile.getContext('2d');
    const pixels = grain.createImageData(96, 96);
    // Use a fixed noise pattern so preview and export do not flicker on redraw.
    let seed = 1297;
    for (let i = 0; i < pixels.data.length; i += 4) {
      seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
      pixels.data.fill(seed >>> 31 ? 255 : 0, i, i + 3);
      pixels.data[i + 3] = Math.round(8 + background.grain * .62);
    }
    grain.putImageData(pixels, 0, 0);
    const pattern = ctx.createPattern(tile, 'repeat');
    pattern.setTransform(new DOMMatrix().scale(Math.max(1, Math.round(width / 400))));
    ctx.save();
    ctx.globalCompositeOperation = 'soft-light';
    ctx.fillStyle = pattern;
    ctx.fillRect(0, 0, width, height);
    ctx.restore();
  }
}

function startScreenshotBackgrounds(form) {
  const picker = form.querySelector('#screenshot-background-options');
  const figures = [...document.querySelectorAll('.background-preview')];
  const choices = form.elements.namedItem('screenshot-background');
  const catalog = JSON.parse(picker.dataset.backgrounds);
  const sources = JSON.parse(picker.dataset.backgroundSources);
  delete picker.dataset.backgrounds;
  const assets = new Map();

  function getBackground(id) {
    const entry = catalog[id];
    if (typeof entry !== 'string') return Promise.resolve(entry);
    if (!assets.has(id)) {
      const image = new Image();
      image.src = entry;
      assets.set(id, image.decode().then(() => image));
    }
    return assets.get(id);
  }

  for (const preview of form.querySelectorAll('.choices-backgrounds [data-option-preview]')) {
    const id = preview.closest('label').querySelector('input').value;
    getBackground(id).then(background => {
      const sample = document.createElement('canvas');
      sample.className = 'background-sample';
      sample.width = 215;
      sample.height = 100;
      paintScreenshotBackground(sample.getContext('2d'), background, sample.width, sample.height);
      preview.append(sample);
    }).catch(() => { preview.textContent = '背景无法加载'; });
  }

  function setupFigure(figure, index) {
    const controls = figure.querySelector('[data-screenshot-controls]')
      ?? picker.querySelector('[data-screenshot-controls]');
    const canvas = figure.querySelector('.screenshot-frame');
    const file = controls.querySelector('[data-screenshot-file]');
    const save = controls.querySelector('[data-screenshot-export]');
    const status = controls.querySelector('[data-screenshot-status]');
    const sourceLinks = figure.querySelector('.screenshot-source');
    const exampleCredit = sourceLinks.querySelector('.screenshot-example-credit');
    const artworkCredit = sourceLinks.querySelector('[data-background-source]');
    let screenshot = figure.querySelector('.screenshot-original');
    let revision = 0;
    let fileRevision = 0;
    let loadingFile = false;

    async function draw() {
      const version = ++revision;
      const id = choices.value;
      const source = screenshot;
      save.disabled = true;
      try {
        const [background] = await Promise.all([getBackground(id), source.decode()]);
        if (version !== revision) return;
        const {naturalWidth: w, naturalHeight: h} = source;
        const border = Math.min(w, h) * .08;
        const scale = Math.min(1200 / (w + 2 * border), 4096 / (h + 2 * border));
        const width = canvas.width = Math.round((w + 2 * border) * scale);
        const height = canvas.height = Math.round((h + 2 * border) * scale);
        const inset = border * scale;
        const radius = Math.min(w, h) * scale * .03;
        const ctx = canvas.getContext('2d');
        ctx.beginPath();
        ctx.roundRect(0, 0, width, height, Math.min(32, radius + inset / 3));
        ctx.clip();
        paintScreenshotBackground(ctx, background, width, height);
        const clip = new Path2D();
        clip.roundRect(inset, inset, w * scale, h * scale, radius);
        ctx.fillStyle = '#fff';
        if (id === '01') {
          ctx.shadowColor = '#FFB86BAA';
          ctx.shadowBlur = inset * 1.2;
        } else {
          ctx.shadowColor = '#05141852';
          ctx.shadowBlur = inset * .85;
          ctx.shadowOffsetY = inset * .2;
        }
        ctx.fill(clip);
        ctx.shadowColor = 'transparent';
        ctx.clip(clip);
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(source, inset, inset, w * scale, h * scale);
        const artwork = sources[id];
        artworkCredit.hidden = !artwork;
        if (artwork) {
          const [name, url] = artwork;
          artworkCredit.href = url;
          artworkCredit.textContent = `${name} · 馆藏原作`;
        }
        sourceLinks.hidden = artworkCredit.hidden && (!exampleCredit || exampleCredit.hidden);
        save.disabled = loadingFile;
      } catch {
        if (version === revision) status.textContent = '无法显示这张截图或背景，请更换后重试';
      }
    }

    file.addEventListener('change', async () => {
      const imageFile = file.files[0];
      if (!imageFile) return;
      const version = ++fileRevision;
      file.value = '';
      loadingFile = true;
      save.disabled = true;
      status.textContent = '';
      const url = URL.createObjectURL(imageFile);
      const image = new Image();
      try {
        image.src = url;
        await image.decode();
        if (version !== fileRevision) return;
        screenshot = image;
        if (exampleCredit) exampleCredit.hidden = true;
      } catch {
        if (version === fileRevision) status.textContent = '无法打开图片，请选择有效的 PNG、JPG 或 WebP';
      } finally {
        URL.revokeObjectURL(url);
        if (version === fileRevision) {
          loadingFile = false;
          await draw();
        }
      }
    });

    save.addEventListener('click', () => {
      const id = choices.value;
      canvas.toBlob(blob => {
        if (!blob) {
          status.textContent = 'PNG 导出失败，请重试';
          return;
        }
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = figures.length > 1 ? `截图-${index + 1}-背景-${id}.png` : `截图背景-${id}.png`;
        link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      }, 'image/png');
    });
    return draw;
  }

  const drawFigures = figures.map(setupFigure);
  return () => Promise.all(drawFigures.map(draw => draw()));
}
