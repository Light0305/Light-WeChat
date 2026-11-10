// Dash cascade (https://design.how/vault/dash-cascade), card.tsx.
// FIXED. Change the VARIABLE values in params instead (WORDS, INK, BG, HUE_SPREAD_DEG, HUE_DRIFT_S, FPS).
'use client';

import {useEffect, useRef} from 'react';
import {prefersReducedMotion, usePause} from '../design-how/dash-cascade/assets/template/runtime/use-pause';
import {DashCascade, type DashScene} from './dash-cascade-engine';
import {BG} from '../design-how/dash-cascade/assets/template/params';

export default function DashCascadeCard({scenes, lines}: {scenes: DashScene[]; lines: string[]}) {
  const box = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const engine = useRef<DashCascade | null>(null);
  const running = usePause(box, run => (run ? engine.current?.start() : engine.current?.stop()));

  useEffect(() => {
    const element = canvas.current;
    if (!element) return;
    const raf = requestAnimationFrame(() => {
      const next = new DashCascade(element, scenes);
      engine.current = next;
      if (!next.ok) return;
      if (prefersReducedMotion()) next.renderStill();
      else if (running.current) next.start();
    });

    let timer = 0;
    const onResize = () => { window.clearTimeout(timer); timer = window.setTimeout(() => engine.current?.resize(), 120); };
    window.addEventListener('resize', onResize);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', onResize);
      window.clearTimeout(timer);
      engine.current?.destroy();
      engine.current = null;
    };
  }, [running, scenes]);

  return <div
    ref={box}
    role="img"
    aria-label={lines.join(" / ")}
    onPointerEnter={() => engine.current?.setHover(true)}
    onPointerLeave={() => engine.current?.setHover(false)}

    style={{width: '100%', height: '100%', backgroundColor: BG}}
  >
    <canvas ref={canvas} style={{display: 'block', width: '100%', height: '100%'}}/>
  </div>;
}
