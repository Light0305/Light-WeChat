#!/usr/bin/env python3
"""Fill Guizang's actual Swiss/Editorial seed, export independent cover frames."""
import argparse
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

SKILL = Path(__file__).resolve().parents[1]
VENDOR = SKILL / "vendor/guizang"
sys.path.insert(0, str(SKILL / 'shared'))
from settings import load_settings


def lines(values):
    return "<br>".join(html.escape(str(value)) for value in values)


def build(spec, output, mode):
    if not spec.get('image') and spec.get('typography_cover') is not True:
        raise ValueError('Text-only template covers are opt-in. Generate a subject-led imagegen cover by default; use typography_cover:true only for an intentionally chosen typography poster.')
    output.mkdir(parents=True, exist_ok=True)
    seed = VENDOR / "assets" / f"template-{'swiss' if mode == 'swiss' else 'editorial'}-card.html"
    source = seed.read_text(encoding="utf-8")
    source = re.sub(r'<link[^>]*>', '', source)
    source = re.sub(r'<script src="https:[^>]*></script>', '', source)
    source = re.sub(r'<title>.*?</title>', '<title>' + html.escape(spec['title']) + '</title>', source)
    serif = mode == "editorial"
    if serif:
        source = source.replace('data-theme="ink-classic"', 'data-theme="indigo-porcelain"')
    extra = """<style>
    :root{--sans:'Microsoft YaHei UI','Microsoft YaHei',sans-serif;--sans-zh:var(--sans);
      --serif-zh:'Noto Serif SC','SimSun',serif;--serif-en:Georgia,serif;--mono:Consolas,monospace}
    .poster.wide .content{display:flex;flex-direction:column}
    .cl-main{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(0,1fr);gap:80px;align-items:center;flex:1}
    .cl-copy{min-width:0}.cl-evidence{min-width:0;border-top:2px solid var(--ink);padding-top:28px}
    .cl-evidence .body{padding:18px 0;border-bottom:1px solid var(--line,var(--grey-2));font-size:32px}
    .cl-evidence img{display:block;max-width:100%;max-height:540px;object-fit:contain;object-position:center 50%}
    .cl-foot{margin-top:auto;padding-top:22px;border-top:1px solid var(--line,var(--grey-2));display:flex;justify-content:space-between}
    .poster.square .content{display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center}
    .poster.square .h-display{font-size:156px;line-height:1.18}
    .poster.wide .h-display{font-size:124px;line-height:1.18}
    .poster.wide .h-statement{font-size:144px;line-height:1.12}
    .cl-copy .h-statement,.cl-copy .h-display{margin-bottom:40px}
    </style>"""
    source = source.replace('</head>', extra + '</head>')
    if spec.get('feed_safe', True):
        # The current draft backend submits the wide image only. Keep its main
        # title inside the central 900px square; the standalone 1:1 is a separate
        # deliverable and must not be misrepresented as the uploaded thumbnail.
        safe = '''<style>
        .poster.wide .cl-main{display:flex;flex-direction:column;justify-content:center;gap:36px}
        .poster.wide .cl-copy{width:900px;text-align:center}
        .poster.wide .h-statement{font-size:128px;line-height:1.12}
        .poster.wide .h-display{font-size:124px;line-height:1.12}
        .poster.wide .cl-copy .h-statement,.poster.wide .cl-copy .h-display{margin-bottom:26px}
        .poster.wide .cl-evidence{display:flex;align-items:center;justify-content:space-between;width:100%;gap:24px;border-top:1px solid var(--line,var(--grey-2));padding-top:18px}
        .poster.wide .cl-evidence .body{font-size:24px;border:0;padding:0}
        .poster.wide .cl-evidence .kicker,.poster.wide .cl-evidence .t-cat{font-size:20px;margin:0}
        .poster.wide .cl-evidence img{max-height:180px}
        </style>'''
        source = source.replace('</head>', safe + '</head>')
    titleclass = 'h-display' if serif else 'h-statement'
    squareclass = 'h-display' if serif else 'h-hero'
    labelclass = 'kicker' if serif else 't-cat'
    metaclass = 'label' if serif else 't-meta'
    bg = '<div class="grain"></div><div class="paper-wash"></div>' if serif else ''
    notes = spec.get('notes', [])
    if spec.get('image'):
        evidence = '<figure class="frame-img"><img src="' + html.escape(Path(spec['image']).resolve().as_uri(), quote=True) + '" alt="原始证据图"></figure>'
    else:
        evidence = '<p class="' + labelclass + '">' + html.escape(spec.get('evidence_label', 'READING NOTES')) + '</p>'
        evidence += ''.join('<p class="body">' + html.escape(str(note)) + '</p>' for note in notes)
    frames = f'''<main class="sheet">
    <section class="poster wide" id="wechat-21x9" data-recipe="{'M01' if serif else 'S03'}">
    {bg}<div class="content">
      <div class="{'issue-row' if serif else 'chrome-min'}"><span>{html.escape(spec.get('publication', load_settings().brand_name))}</span><span>{html.escape(spec.get('eyebrow','ENGINEERING'))}</span></div>
      <div class="cl-main"><div class="cl-copy"><h1 class="{titleclass}">{lines(spec['headline'])}</h1>
      <p class="{'h-sub' if serif else 'lead'}">{html.escape(spec.get('subtitle',''))}</p></div>
      <div class="cl-evidence">{evidence}</div></div>
      <div class="cl-foot"><span class="{metaclass}">{html.escape(spec.get('footer','研究 · 实践 · 判断'))}</span><span class="{metaclass}">{html.escape(spec.get('publication', load_settings().brand_name))}</span></div>
    </div></section>
    <section class="poster square" id="wechat-1x1" data-recipe="{'M04' if serif else 'S01'}">
    {bg}<div class="content"><h1 class="{squareclass}">{lines(spec['short_headline'])}</h1></div></section>
    </main>'''
    # Replace the seed placeholder deck as a whole; preserve the full upstream CSS.
    source = re.sub(r'<main class="sheet">[\s\S]*?</main>', lambda _: frames, source, count=1)
    # The grain/paper-wash is a deterministic local atmosphere layer. No CDN runtime.
    source = re.sub(r'<script[\s\S]*?</script>', '', source)
    path = output / 'index.html'
    path.write_text(source, encoding='utf-8')
    (output / 'cover-spec.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding='utf-8')
    for selector, name in (('#wechat-21x9', 'cover.png'), ('#wechat-1x1', 'cover-square.png')):
        scratch = output / ('render-' + name.removesuffix('.png'))
        subprocess.run(['node', str(SKILL / 'scripts/capture_local_chrome.cjs'), '--input', str(path),
            '--out', str(scratch), '--width', '2400', '--height', '1600', '--selector', selector], check=True)
        shutil.copy2(scratch / 'render.png', output / name)
    pair = '<!doctype html><meta charset="utf-8"><title>Chuan Lab 封面对</title><body style="margin:0;background:#e9e9e6;padding:24px;font:16px system-ui"><div style="display:flex;align-items:center;gap:24px"><img style="width:65%;height:auto" src="cover.png"><img style="width:30%;height:auto" src="cover-square.png"></div></body>'
    (output / 'pair-preview.html').write_text(pair, encoding='utf-8')
    return path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--spec', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--mode', choices=['swiss', 'editorial'], default='swiss')
    args = p.parse_args()
    spec = json.loads(args.spec.read_text(encoding='utf-8'))
    print(build(spec, args.out.resolve(), args.mode))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    main()
