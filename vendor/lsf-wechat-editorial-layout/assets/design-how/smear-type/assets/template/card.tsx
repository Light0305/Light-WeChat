// Smear type (https://design.how/vault/smear-type), card.tsx.
// FIXED. Change the VARIABLE values in params instead (DEFAULT_LINES, DEFAULT_GROUND, DEFAULT_RIBBON, DEFAULT_RIM, DEFAULT_TYPE, DEFAULT_INK, KEY_MS, CAP, WIDEN, EMBOLDEN, BLUR, FONT_WEIGHT, FONT_VAR, LAYERS_URL, INK_URL).
'use client';
import './fonts.css';
import {useEffect, useRef} from 'react';
import {prefersReducedMotion, usePause} from './runtime/use-pause';
import {SmearType, type SmearColours} from './engine';
import {DEFAULT_GROUND, DEFAULT_LINES, FONT_VAR, FONT_WEIGHT} from './params';
import layersUrl from './layers.webp';
import inkUrl from './ink.webp';

export type SmearTypeProps = {
  lines?: readonly [string, string];
  colours?: SmearColours;
  weight?: number;
  speed?: number;
  fontVar?: string;
  className?: string;
};

export default function SmearTypeCard({lines = DEFAULT_LINES, colours, weight = FONT_WEIGHT, speed = 1, fontVar = FONT_VAR, className}: SmearTypeProps) {
  const box = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const engine = useRef<SmearType | null>(null);
  const running = usePause(box, run => {
    if (run) engine.current?.start();
    else {
      engine.current?.stop();
      if (prefersReducedMotion()) engine.current?.renderStill();
    }
  });

  useEffect(() => {
    const element = canvas.current;
    if (!element) return;
    let cancelled = false;
    const probe = document.createElement('span');
    probe.style.cssText = `position:absolute;visibility:hidden;font-family:var(${fontVar})`;
    probe.textContent = 'Ag';
    document.body.appendChild(probe);
    const family = getComputedStyle(probe).fontFamily || 'sans-serif';
    probe.remove();

    const build = () => {
      if (cancelled) return;
      const next = new SmearType(element, {family, lines, colours, weight, speed, layersUrl, inkUrl});
      engine.current = next;
      if (!next.ok) {
        element.dataset.exportReady = 'error';
        return;
      }
      if (prefersReducedMotion()) next.renderStill();
      else if (running.current) next.start();
    };
    const first = family.split(',')[0].replace(/["']/g, '').trim();
    if (document.fonts?.load) document.fonts.load(`${weight} 1em "${first}"`).then(build, build);
    else build();

    let timer = 0;
    const onResize = () => { window.clearTimeout(timer); timer = window.setTimeout(() => engine.current?.resize(), 120); };
    window.addEventListener('resize', onResize);
    return () => {
      cancelled = true;
      window.removeEventListener('resize', onResize);
      window.clearTimeout(timer);
      engine.current?.destroy();
      engine.current = null;
    };
  }, [lines, colours, weight, speed, fontVar, running]);

  return <div
    ref={box}
    role="img"
    aria-label={lines.filter(Boolean).join(' ')}
    className={className}
    style={{width: '100%', height: '100%', backgroundColor: colours?.ground ?? DEFAULT_GROUND, userSelect: 'none'}}
  >
    <canvas ref={canvas} data-export-ready="pending" style={{display: 'block', width: '100%', height: '100%', touchAction: 'pan-y'}}/>
  </div>;
}
