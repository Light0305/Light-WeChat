import React, { useLayoutEffect, useState } from 'react';
import TileFieldCard from '../design-how/tile-field/assets/template/card';
import { setPreviewCopy as setTileFieldCopy } from '../design-how/tile-field/assets/template/params';
import PixelScanCard from '../design-how/pixel-scan/assets/template/card';
import { setPreviewCopy as setPixelScanCopy } from '../design-how/pixel-scan/assets/template/params';
import TyperCard from '../design-how/typer/assets/template/card';
import { setPreviewCopy as setTyperCopy } from '../design-how/typer/assets/template/params';
import DesignTilesCard from '../design-how/design-tiles/assets/template/card';
import { setPreviewCopy as setDesignTilesCopy } from '../design-how/design-tiles/assets/template/params';
import BlurGlowCard from '../design-how/blur-glow/assets/template/card';
import { setPreviewCopy as setBlurGlowCopy } from '../design-how/blur-glow/assets/template/params';
import DotCutCard from '../design-how/dot-cut/assets/template/card';
import { setPreviewCopy as setDotCutCopy } from '../design-how/dot-cut/assets/template/scenes';
import PixelThresholdCard from '../design-how/pixel-threshold/assets/template/card';
import { setPreviewCopy as setPixelThresholdCopy } from '../design-how/pixel-threshold/assets/template/cycle';
import GlassTypeCard from '../design-how/glass-type/assets/template/card';
import { setPreviewCopy as setGlassTypeCopy } from '../design-how/glass-type/assets/template/params';
import RealitySplitCard from '../design-how/reality-split/assets/template/card';
import { setPreviewCopy as setRealitySplitCopy } from '../design-how/reality-split/assets/template/params';
import StampTypeCard from '../design-how/stamp-type/assets/template/card';
import { setPreviewCopy as setStampTypeCopy } from '../design-how/stamp-type/assets/template/params';
import LoudBurstCard from '../design-how/loud-burst/assets/template/card';
import { setPreviewCopy as setLoudBurstCopy } from '../design-how/loud-burst/assets/template/params';
import WildTypeCard from '../design-how/wild-type/assets/template/card';
import { setPreviewCopy as setWildTypeCopy } from '../design-how/wild-type/assets/template/params';
import SwingTypeCard from '../design-how/swing-type/assets/template/card';
import { setPreviewCopy as setSwingTypeCopy } from '../design-how/swing-type/assets/template/params';
import FloodTypeCard from '../design-how/flood-type/assets/template/card';
import { setPreviewCopy as setFloodTypeCopy } from '../design-how/flood-type/assets/template/params';
import VerbTypeCard from '../design-how/verb-type/assets/template/card';
import { setPreviewCopy as setVerbTypeCopy } from '../design-how/verb-type/assets/template/params';
import CloudTypeCard from '../design-how/cloud-type/assets/template/card';
import { setPreviewCopy as setCloudTypeCopy } from '../design-how/cloud-type/assets/template/params';
import FlipTypeCard from '../design-how/flip-type/assets/template/card';
import { setPreviewCopy as setFlipTypeCopy } from '../design-how/flip-type/assets/template/params';
import WarpTypeCard from '../design-how/warp-type/assets/template/card';
import StackTypeCard from '../design-how/stack-type/assets/template/card';
import RushTypeCard from '../design-how/rush-type/assets/template/card';
import { setPreviewCopy as setRushTypeCopy } from '../design-how/rush-type/assets/template/params';
import BondTypeCard from '../design-how/bond-type/assets/template/card';
import { setPreviewCopy as setBondTypeCopy } from '../design-how/bond-type/assets/template/params';
import DashCascadeCard from './dash-cascade-card';
import { dashCascadeProps } from './dash-cascade-layout';
import ChromaGlowCard from '../design-how/chroma-glow/assets/template/card';
import { setPreviewCopy as setChromaGlowCopy } from '../design-how/chroma-glow/assets/template/params';
import SmearTypeCard from '../design-how/smear-type/assets/template/card';

function chunks(text, slots) {
  const glyphs = Array.from(text);
  const count = Math.min(slots, glyphs.length);
  return Array.from({ length: count }, (_, i) =>
    glyphs.slice(Math.round(i * glyphs.length / count), Math.round((i + 1) * glyphs.length / count)).join(''));
}

function wordChunks(text, slots) {
  const words = text.split(/\s+/);
  if (words.length === 1) return chunks(text, slots);
  return words.length <= slots ? words : [...words.slice(0, slots - 1), words.slice(slots - 1).join(' ')];
}

function smearProps([text]) {
  const glyphs = Array.from(text);
  if (glyphs.length <= 11) return { lines: [text, ''], weight: 800 };
  const middle = Math.floor(glyphs.length / 2);
  const breaks = glyphs.map((glyph, index) => /\s/.test(glyph) ? index : -1)
    .filter(index => index >= glyphs.length / 3 && index <= glyphs.length * 2 / 3);
  const split = breaks.sort((a, b) => Math.abs(a - middle) - Math.abs(b - middle))[0] ?? middle;
  return { lines: [glyphs.slice(0, split).join('').trim(), glyphs.slice(split).join('').trim()], weight: 800 };
}

const demos = {
  'tile-field': { Card: TileFieldCard, setCopy: setTileFieldCopy },
  'pixel-scan': { Card: PixelScanCard, setCopy: setPixelScanCopy },
  typer: { Card: TyperCard, setCopy: setTyperCopy },
  'design-tiles': { Card: DesignTilesCard, setCopy: ([text]) => setDesignTilesCopy(wordChunks(text, 5)) },
  'blur-glow': { Card: BlurGlowCard, setCopy: setBlurGlowCopy },
  'dot-cut': { Card: DotCutCard, setCopy: setDotCutCopy },
  'pixel-threshold': { Card: PixelThresholdCard, setCopy: setPixelThresholdCopy },
  'glass-type': { Card: GlassTypeCard, setCopy: setGlassTypeCopy },
  'reality-split': { Card: RealitySplitCard, setCopy: setRealitySplitCopy },
  'stamp-type': { Card: StampTypeCard, setCopy: setStampTypeCopy },
  'loud-burst': { Card: LoudBurstCard, setCopy: lines => setLoudBurstCopy(lines.map(line => wordChunks(line, 5))) },
  'wild-type': { Card: WildTypeCard, setCopy: setWildTypeCopy },
  'swing-type': { Card: SwingTypeCard, setCopy: setSwingTypeCopy },
  'flood-type': { Card: FloodTypeCard, setCopy: setFloodTypeCopy },
  'verb-type': { Card: VerbTypeCard, setCopy: lines => setVerbTypeCopy((i, slots) => chunks(lines[i % lines.length], slots)) },
  'cloud-type': { Card: CloudTypeCard, setCopy: ([text]) => setCloudTypeCopy(text) },
  'flip-type': { Card: FlipTypeCard, setCopy: setFlipTypeCopy },
  'warp-type': { Card: WarpTypeCard, props: lines => ({
    phrases: Array.from({ length: 6 }, (_, scene) =>
      Array.from({ length: scene === 2 ? 3 : 2 }, (_, row) => lines[(scene + row) % lines.length])),
  }) },
  'stack-type': { Card: StackTypeCard, props: lines => ({ phrases: lines.map(text => ({ text })) }) },
  'rush-type': { Card: RushTypeCard, setCopy: setRushTypeCopy },
  'bond-type': { Card: BondTypeCard, setCopy: setBondTypeCopy },
  'dash-cascade': { Card: DashCascadeCard, props: dashCascadeProps },
  'chroma-glow': { Card: ChromaGlowCard, setCopy: setChromaGlowCopy },
  'smear-type': { Card: SmearTypeCard, props: smearProps },
};

export function VaultDemo({ id, text }) {
  const { Card, setCopy, props } = demos[id];
  const requested = JSON.stringify(Array.isArray(text) ? text : [text]);
  const [applied, setApplied] = useState(null);

  useLayoutEffect(() => {
    function apply() {
      const lines = JSON.parse(requested);
      setCopy?.(lines);
      setApplied({ key: requested, props: props?.(lines) });
    }

    if (!applied) {
      apply();
      return;
    }
    // Let a burst of keystrokes finish before rebuilding the selected engine's glyphs.
    const timer = setTimeout(apply, 160);
    return () => clearTimeout(timer);
  }, [requested, setCopy, props]);

  return (
    <div className="vault-demo" data-vault-demo={id}>
      {applied && <Card key={applied.key} {...applied.props} />}
    </div>
  );
}
