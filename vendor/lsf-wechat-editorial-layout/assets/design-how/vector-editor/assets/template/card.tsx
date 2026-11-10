// Vector editor (https://design.how/vault/vector-editor), card.tsx.
// FIXED. Change the VARIABLE values in params instead (SHAPE, VIEW_BOX, SHAPE_W, PAD, FRAME, GROUND).
'use client';

import './fonts.css';
import {useEffect, useRef, useState} from 'react';
import {usePause} from './runtime/use-pause';
import {VectorEditor} from './editor';
import {FRAME, GROUND, PAD, SHAPE, SHAPE_W, VIEW_BOX} from './params';
import {parsePath} from './parse';
import {SelectionFrame} from './selection-frame';

const H = Math.round(SHAPE_W * (VIEW_BOX[3] / VIEW_BOX[2]));
const FW = SHAPE_W + PAD * 2;
const FH = H + PAD * 2;
const PATH = parsePath(SHAPE);

class Fit {
  private readonly ro: ResizeObserver;
  constructor(private readonly host: HTMLElement, private readonly onScale: (s: number) => void) {
    this.ro = new ResizeObserver(() => this.measure());
    this.ro.observe(host);
  }
  measure() {
    const width = this.host.clientWidth - 24;
    const height = this.host.clientHeight - 24;
    // The badge extends below the frame, so include it when fitting the scene.
    this.onScale(Math.max(0.05, Math.min(width / (FW + FRAME.handleSize), height / (FH + 30 + FRAME.handleSize / 2))));
  }
  destroy() { this.ro.disconnect(); }
}

export default function VectorEditorCard({className, text}: {className?: string; text?: string}) {
  const box = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);
  const [intro, setIntro] = useState(0);
  usePause(box, run => { if (run) setIntro(i => i + 1); });

  useEffect(() => {
    const host = box.current;
    if (!host) return;
    const fit = new Fit(host, setScale);
    fit.measure();
    return () => fit.destroy();
  }, []);

  return <div ref={box} role="img" aria-label={text || "A shape selected in a design tool: a blue frame with corner handles and a size badge around a blob, a star and a rounded square showing their bezier anchors and handles."} className={className} style={{position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%', overflow: 'hidden', background: GROUND}}>
    <div style={{flex: 'none', transform: `translateY(${-(30 - FRAME.handleSize / 2) * scale / 2}px) scale(${scale})`, transformOrigin: 'center', pointerEvents: 'none'}}>
      <SelectionFrame key={intro} style={FRAME} width={FW} height={FH}>
        <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', width: FW, height: FH}}>
          {text ? <svg viewBox={`0 0 ${SHAPE_W} ${H}`} width={SHAPE_W} height={H} aria-hidden="true">
            <text x="50%" y="50%" textAnchor="middle" dominantBaseline="central"
              fontFamily="system-ui, sans-serif" fontWeight="600"
              fontSize={Math.min(H * 0.68, (SHAPE_W - 12) / Array.from(text).length)}
              fill="#235e9b">{text}</text>
          </svg> : <VectorEditor path={PATH} onChange={() => {}} viewBox={VIEW_BOX} width={SHAPE_W} height={H} rigScale={0.5}/>}
        </div>
      </SelectionFrame>
    </div>
  </div>;
}
