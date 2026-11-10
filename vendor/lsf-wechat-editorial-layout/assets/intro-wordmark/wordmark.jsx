import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { createRoot } from 'react-dom/client';
import { GIFEncoder, applyPalette, quantize } from 'gifenc';
import luckiest from '@fontsource/luckiest-guy/files/luckiest-guy-latin-400-normal.woff2';
import manrope from '@fontsource-variable/manrope/files/manrope-latin-wght-normal.woff2';
import { createMolten, createTumble, subscribeSharedClock } from './renderers.js';
import { createCarousel, createRoll } from './vault-effects.js';
import { VaultDemo } from './vault-demos.jsx';
import { captureVault } from './capture-vault.js';
import { createEmbossBanner, embossReady, prepareLogo } from './emboss-banner.js';
import { KEY_MS as smearFrameMs, LOOP_KEYS as smearFrames, STILL_KEY as smearStillKey } from '../design-how/smear-type/assets/template/params';

const factories = { tumble: createTumble, molten: createMolten, carousel: createCarousel, roll: createRoll, emboss: createEmbossBanner };
const introModes = { '01': 'tumble', '02': 'molten', '03': 'carousel', '04': 'roll', emboss: 'emboss' };
const adaptedVault = { 'word-carousel': '03', 'roll-type': '04' };
const sceneModes = new Set(['carousel', 'roll']);
const banner = { width: 640, height: 260 };
const previewBundle = document.currentScript?.textContent;
const vaultDurations = {
  'tile-field': 4000, 'pixel-scan': 3000, typer: 5400,
  'design-tiles': 3200, 'blur-glow': 1800, 'dot-cut': 15000, 'pixel-threshold': 2520,
  'glass-type': 15000, 'reality-split': 6480, 'stamp-type': 21700, 'loud-burst': 6000,
  'wild-type': 3480, 'swing-type': 3000, 'flood-type': 12500, 'verb-type': 6480,
  'cloud-type': 4080, 'flip-type': 5100, 'warp-type': 3000,
  'stack-type': 1920, 'rush-type': 3400, 'bond-type': 4000, 'dash-cascade': 2500,
  'chroma-glow': 10560,
  'smear-type': smearFrameMs * smearFrames,
};
const wordCycles = new Set(['blur-glow', 'pixel-threshold', 'swing-type', 'dash-cascade']);
const gifColors = { tumble: 64, emboss: 64, 'chroma-glow': 48, 'dot-cut': 64 };
let fontsReady;
function loadFonts() {
  fontsReady ??= Promise.allSettled([
    new FontFace('Wordmark Luckiest', `url(${luckiest})`).load(),
    new FontFace('Wordmark Manrope', `url(${manrope})`, { weight: '200 800' }).load(),
  ]).then(fonts => {
    for (const font of fonts) {
      if (font.status === 'fulfilled') document.fonts.add(font.value);
    }
  });
  return fontsReady;
}

const fontFamilies = {
  tumble: '"Wordmark Luckiest", "Arial Black", "Microsoft YaHei", "PingFang SC", sans-serif',
  molten: '"Wordmark Manrope", "Microsoft YaHei", "PingFang SC", sans-serif',
};

function renderOptions(mode, text, options = {}) {
  const common = { dpr: 1, fontFamily: fontFamilies[mode] || fontFamilies.molten, ...options };
  if (mode === 'molten') return text == null ? common : { ...common, words: Array.isArray(text) ? text : [text] };
  const fontWeight = /[\p{Script=Han}]/u.test(String(text)) ? '900' : '400';
  return { fontWeight, ...common, text: text ?? 'CHOP' };
}

function bannerOptions(mode) {
  if (mode === 'tumble') return { capHeight: .3, span: 5.9, fitVertical: true };
  return mode === 'molten' ? { size: 2.15 } : {};
}

export function Wordmark({ mode, text, wide = false, thumbnail = false, ...options }) {
  const element = useRef(null);
  const renderer = useRef(null);
  const [visible, setVisible] = useState(false);
  const refresh = useRef(null);
  const previousText = useRef(text);
  const props = renderOptions(mode, text, wide ? { ...bannerOptions(mode), ...options } : options);
  const latest = useRef(props);
  latest.current = props;

  useEffect(() => {
    const canvas = element.current;
    const motion = matchMedia('(prefers-reduced-motion: reduce)');
    const still = () => thumbnail || motion.matches;
    let frame;
    let unsubscribe;
    let alive = true;
    let origin;
    const shared = mode === 'molten' && (text == null || Array.isArray(text));
    const paint = time => {
      const active = renderer.current;
      if (!active) return;
      origin ??= time;
      active.draw(time - origin);
      if (!still() || active.isMixing?.()) frame = requestAnimationFrame(paint);
    };
    const restart = (reset = false) => {
      if (reset) origin = undefined;
      cancelAnimationFrame(frame);
      unsubscribe?.();
      unsubscribe = null;
      if (shared && !still()) {
        unsubscribe = subscribeSharedClock(time => renderer.current?.draw(time));
      } else {
        frame = requestAnimationFrame(paint);
      }
    };
    const measure = () => {
      const width = Math.max(1, Math.min(thumbnail ? 192 : 800, Math.round(canvas.clientWidth * Math.min(2, devicePixelRatio))));
      const height = wide ? Math.max(1, Math.round(width * banner.height / banner.width)) : width;
      return { width, height };
    };
    const resize = () => {
      if (!renderer.current) return;
      const size = measure();
      if (canvas.width !== size.width || canvas.height !== size.height) {
        renderer.current.update({ ...latest.current, ...size, reducedMotion: still() });
        restart();
      }
    };
    const resizeObserver = new ResizeObserver(resize);
    const intersection = new IntersectionObserver(entries => setVisible(entries[0].isIntersecting));
    intersection.observe(canvas);

    if (visible) {
      Promise.all([loadFonts(), mode === 'emboss' ? embossReady : null]).then(() => {
        if (!alive) return;
        try {
          renderer.current = factories[mode](canvas, { ...latest.current, ...measure(), reducedMotion: still() });
          canvas.dataset.ready = 'true';
        } catch (error) {
          console.error(error);
          canvas.dataset.error = 'true';
          return;
        }
        resizeObserver.observe(canvas);
        restart();
      });
    }
    const motionChanged = () => {
      renderer.current?.update({ ...latest.current, reducedMotion: still() });
      restart();
    };
    refresh.current = restart;
    motion.addEventListener('change', motionChanged);
    document.fonts.addEventListener('loadingdone', motionChanged);
    return () => {
      alive = false;
      cancelAnimationFrame(frame);
      unsubscribe?.();
      resizeObserver.disconnect();
      intersection.disconnect();
      motion.removeEventListener('change', motionChanged);
      document.fonts.removeEventListener('loadingdone', motionChanged);
      renderer.current?.destroy();
      renderer.current = null;
    };
  }, [mode, visible, wide, thumbnail, text == null || Array.isArray(text)]);

  useEffect(() => {
    renderer.current?.update(props);
    const textChanged = previousText.current !== text;
    previousText.current = text;
    if (thumbnail || (mode === 'molten' && textChanged) || matchMedia('(prefers-reduced-motion: reduce)').matches) {
      refresh.current?.(mode === 'molten' && textChanged);
    }
  });

  const ratio = wide ? `${banner.width} / ${banner.height}` : '1';
  return <canvas ref={element} className={`intro-canvas ${mode}`} style={{ aspectRatio: ratio }}
    role="img" aria-label={Array.isArray(text) ? text.join(' ') : text} />;
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 30000);
}

function gifWriter(number, name, colors) {
  const { width, height } = banner;
  const encoder = GIFEncoder();
  return {
    write(pixels, delay) {
      const palette = quantize(pixels, colors);
      encoder.writeFrame(applyPalette(pixels, palette), width, height, { palette, delay, repeat: 0 });
    },
    save() {
      encoder.finish();
      downloadBlob(new Blob([encoder.bytes()], { type: 'image/gif' }), `${number}-${name}.gif`);
    },
  };
}

async function renderWordmarkFrames(mode, text, onFrame, logo, still) {
  await Promise.all([loadFonts(), mode === 'emboss' ? embossReady : null]);
  const { width, height } = banner;
  const canvas = Object.assign(document.createElement('canvas'), banner);
  const context = canvas.getContext('2d', { willReadFrequently: true });
  const renderer = factories[mode](canvas, renderOptions(mode, text, { ...bannerOptions(mode), width, height, logo, reducedMotion: false }));
  const duration = renderer.duration?.() ?? (mode === 'tumble' ? 1760 : 3000);
  const delay = 40;
  try {
    if (still) {
      renderer.draw(mode === 'molten' ? 1600 : 600);
      onFrame(context.getImageData(0, 0, width, height).data);
      return;
    }
    for (let time = 0; time < duration; time += delay) {
      renderer.draw(time);
      const pixels = context.getImageData(0, 0, width, height).data;
      onFrame(pixels, Math.min(delay, duration - time));
      if (time % 200 === 0) await new Promise(resolve => setTimeout(resolve, 0));
    }
  } finally {
    renderer.destroy();
  }
}

async function savePng(pixels, filename) {
  const { width, height } = banner;
  const canvas = Object.assign(document.createElement('canvas'), banner);
  canvas.getContext('2d').putImageData(new ImageData(pixels, width, height), 0, 0);
  const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
  if (!blob) throw new Error('PNG encoding failed');
  downloadBlob(blob, filename);
}

const savedSignatureKey = 'lsf-wechat-editorial-layout:signature';

function IntroEditor({ author, preview, presets, articleLines, library }) {
  const choices = [
    ...presets.slice(0, 2).map(entry => ({ ...entry, number: entry.id })),
    ...library.map(entry => ({ ...entry, id: adaptedVault[entry.id] || entry.id, vaultId: entry.id })),
  ].sort((a, b) => Number(a.number) - Number(b.number));
  const [value, setValue] = useState(() => {
    try {
      return localStorage.getItem(savedSignatureKey)?.trim() || author;
    } catch {
      return author;
    }
  });
  const [saveStatus, setSaveStatus] = useState('');
  const [exporting, setExporting] = useState('');
  const [status, setStatus] = useState('');
  const [presetId, setPresetId] = useState(presets[0].id);
  const deferredArticle = host.dataset.articleWorkflow === 'deferred';
  const [source, setSource] = useState(deferredArticle && articleLines.length ? 'article' : 'manual');
  const [articleDraft, setArticleDraft] = useState(articleLines.join('\n'));
  const [manualDraft, setManualDraft] = useState(null);
  const [logoUrl, setLogoUrl] = useState('');
  const [logo, setLogo] = useState(null);
  const [logoStatus, setLogoStatus] = useState('');
  const uploadVersion = useRef(0);
  const mode = introModes[presetId];
  const vaultEffect = library.find(entry => entry.id === presetId);
  const displayText = value.trim() || author;
  const sceneDraft = source === 'article' ? articleDraft : manualDraft ?? displayText;
  const setSceneDraft = source === 'article' ? setArticleDraft : setManualDraft;
  const scenes = sceneDraft.split('\n').map(line => line.trim()).filter(Boolean).slice(0, 4);
  const firstLine = source === 'article' ? scenes[0] || displayText : displayText;
  const textFor = (style, kind) => sceneModes.has(style) || kind === 'scenes'
    ? (scenes.length ? scenes : [displayText]) : firstLine;
  const wantsArticle = deferredArticle && source === 'article';
  const articlePending = wantsArticle && !scenes.length;
  const previewPending = articlePending && !(mode === 'emboss' && logo);
  const effectiveText = textFor(mode, vaultEffect?.kind);
  const hasScenes = Array.isArray(effectiveText);
  const introText = articlePending ? '' : Array.isArray(effectiveText) ? effectiveText.join(' / ') : effectiveText;

  useEffect(() => {
    let active = true;
    setLogo(null);
    if (logoUrl) {
      const image = new Image();
      image.src = logoUrl;
      image.decode().then(() => {
        if (active) setLogo(image);
      }).catch(() => {
        if (active) setLogoStatus('Logo 读取失败，请重新上传');
      });
    }
    return () => { active = false; };
  }, [logoUrl]);

  useEffect(() => {
    host.dispatchEvent(new Event('intro-preset-change'));
  }, [presetId]);

  useEffect(() => {
    host.readIntroState = () => ({ value, presetId, source, articleDraft, manualDraft, logoUrl, articleWorkflow: deferredArticle ? 'deferred' : undefined, hasScenes });
    const restore = event => {
      const saved = event.detail;
      uploadVersion.current++;
      setValue(saved.value);
      setPresetId(choices.some(choice => choice.id === saved.presetId) ? saved.presetId : presets[0].id);
      setSource(saved.source);
      const wasDemoCopy = deferredArticle && saved.articleWorkflow !== 'deferred'
        && saved.articleDraft === '选图要准\n给截图留一点边\n标题给出下一步\n在手机上再看';
      setArticleDraft(wasDemoCopy ? '' : saved.articleDraft ?? '');
      setManualDraft(saved.manualDraft);
      setLogoUrl(saved.logoUrl);
      setLogoStatus('');
    };
    host.addEventListener('restore-intro-state', restore);
    return () => {
      host.removeEventListener('restore-intro-state', restore);
      delete host.readIntroState;
    };
  }, [value, presetId, source, articleDraft, manualDraft, logoUrl, choices, presets, deferredArticle, hasScenes]);

  async function uploadLogo(event) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    const current = ++uploadVersion.current;
    setLogoStatus('正在读取 Logo');
    try {
      const url = await prepareLogo(file);
      if (current !== uploadVersion.current) return;
      setLogoUrl(url);
      setLogoStatus('已载入 Logo');
    } catch (error) {
      if (current === uploadVersion.current) setLogoStatus(error.message || 'Logo 读取失败');
    }
  }

  function saveSignature() {
    const text = value.trim();
    if (!text) {
      setSaveStatus('请先输入署名');
      return;
    }
    try {
      localStorage.setItem(savedSignatureKey, text);
      setValue(text);
      setSaveStatus('已保存');
    } catch {
      setSaveStatus('浏览器未能保存署名');
    }
  }

  async function exportSelected(format) {
    const still = format === 'PNG';
    setExporting(format);
    setStatus('');
    try {
      const selected = choices.find(entry => entry.id === presetId);
      const gif = still ? null : gifWriter(selected.number, selected.name, gifColors[mode || presetId] ?? 128);
      let stillPixels;
      const onFrame = still ? pixels => { stillPixels = pixels; } : gif.write;
      if (mode) {
        await renderWordmarkFrames(mode, effectiveText, onFrame, logo, still);
      } else {
        const scenes = wordCycles.has(presetId) && Array.isArray(effectiveText) ? effectiveText.length : 1;
        await captureVault({
          id: presetId, text: effectiveText, ...banner, bundle: previewBundle,
          duration: vaultDurations[presetId] * scenes, onFrame, still,
          ...(presetId === 'smear-type' ? { frameMs: smearFrameMs, stillAt: smearStillKey * smearFrameMs } : {}),
        });
      }
      if (still) await savePng(stillPixels, `${selected.number}-${selected.name}.png`);
      else gif.save();
      setStatus(`${format} 已导出`);
    } catch (error) {
      console.error(error);
      setStatus(`${format} 导出失败，请重试`);
    } finally {
      setExporting('');
    }
  }

  function choice(preset) {
    const style = introModes[preset.id];
    return <label className="choice" key={preset.id} data-vault-option={preset.vaultId}>
      <input type="radio" name="intro" value={preset.id} checked={preset.id === presetId}
        onChange={() => setPresetId(preset.id)} />
      <span className="choice-card">
        <span className="choice-preview" aria-hidden="true">
          {style && style !== 'emboss'
            ? <Wordmark mode={style} text={articlePending ? displayText : textFor(style)} wide thumbnail />
            : <img className="vault-demo" src={preset.thumbnail} width="192" height="78" alt="" loading="lazy" decoding="async" />}
        </span>
        <span className="choice-name">{preset.number} {preset.name}</span>
      </span>
    </label>;
  }

  const styleGallery = <div className="choices intro-choices">{choices.map(choice)}</div>;
  const sourceControls = <div className="intro-source">
    <div className="segmented" role="group" aria-label="文案来源">
      <button type="button" aria-pressed={source === 'manual'} onClick={() => setSource('manual')}>自己写</button>
      <button type="button" aria-pressed={source === 'article'} onClick={() => setSource('article')}>Agent 提炼文章</button>
    </div>
  </div>;
  const signatureField = <>
    <div className="intro-input-row">
      <input id="intro-text" type="text" aria-label="署名文字" value={value} placeholder={author} maxLength={32}
        onChange={event => {
          setValue(event.target.value);
          if (manualDraft !== null) {
            const lines = manualDraft.split('\n');
            lines[0] = event.target.value;
            setManualDraft(lines.join('\n'));
          }
          setSaveStatus('');
        }} />
      <button type="button" className="intro-save" onClick={saveSignature}>保存</button>
    </div>
    <p className="field-hint">文字会实时显示在文章开篇</p>
    <p className="intro-status intro-save-status" role="status">{saveStatus}</p>
  </>;
  const sceneField = (source === 'article' || sceneModes.has(mode) || vaultEffect?.kind === 'scenes') &&
    <label className="intro-lines">
      {source === 'article' ? '文章短句' : '分镜文字'}{(!wantsArticle || hasScenes) && '（每行一句）'}
      <textarea rows={wantsArticle ? 2 : 4} value={sceneDraft}
        placeholder={wantsArticle ? '粘贴 Agent 返回的文案，也可以手动修改' : undefined}
        onChange={event => setSceneDraft(event.target.value)} />
    </label>;
  const effectControls = <>
    {mode === 'emboss' && <div className="emboss-upload">
      <label className="logo-picker">上传 Logo
        <input type="file" aria-label="上传 Logo" accept="image/png,image/jpeg,image/webp" onChange={uploadLogo} />
      </label>
      {logoUrl && <button type="button" onClick={() => {
        uploadVersion.current++;
        setLogoUrl('');
        setLogoStatus('已移除 Logo');
      }}>移除 Logo</button>}
      <span className="intro-status" role="status">{logoStatus}</span>
    </div>}
    <div className="intro-actions">
      {['GIF', 'PNG'].map(format => <button key={format} type="button" className="intro-export-btn"
        disabled={Boolean(exporting || previewPending || (mode === 'emboss' && logoUrl && !logo))}
        onClick={() => exportSelected(format)}>
        {exporting === format ? '正在导出' : `导出 ${format}`}
      </button>)}
      <p className="intro-status" role="status">{status}</p>
    </div>
  </>;

  return <>
    {createPortal(previewPending
      ? <p className="intro-preview-pending" role="status">等待回填开篇文案</p>
      : mode
        ? <Wordmark key={mode} mode={mode} text={effectiveText} wide logo={mode === 'emboss' ? logo : undefined} />
        : <VaultDemo key={presetId} id={presetId} text={effectiveText} />, preview)}
    <input type="hidden" data-intro-text value={introText} />
    <div className="style-step" id="intro-copy-settings">
      <div className="step-head"><span className="step-label"><b aria-hidden="true">1</b>文案来源</span></div>
      {sourceControls}
    </div>
    <div className="style-step">
      <div className="step-head">
        <span className="step-label"><b aria-hidden="true">2</b>{wantsArticle ? '文章短句' : '署名文字'}</span>
      </div>
      {wantsArticle ? sceneField : signatureField}
      {!wantsArticle && sceneField}
      {articlePending && <p className="field-hint">复制选择后，交给 Agent 按文章提炼</p>}
    </div>
    <div className="style-step">
      <div className="step-head"><span className="step-label"><b aria-hidden="true">3</b>动效</span></div>
      {styleGallery}
      {effectControls}
    </div>
  </>;
}

const captureHost = document.querySelector('[data-vault-export]');
const host = document.querySelector('[data-intro-wordmark]');
if (captureHost) createRoot(captureHost).render(<VaultDemo id={captureHost.dataset.vaultExport}
  text={JSON.parse(captureHost.dataset.text)} />);
else if (host) createRoot(host).render(<IntroEditor author={host.dataset.author}
  preview={document.getElementById('preview-intro')} presets={JSON.parse(host.dataset.presets)}
  articleLines={JSON.parse(host.dataset.articleLines)} library={JSON.parse(host.dataset.vault)} />);
