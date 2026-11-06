#!/usr/bin/env python3
"""Verify all pinned upstream copies and compiled template provenance."""
from pathlib import Path
import hashlib
import json
import re
import sys


def verify():
    skill=Path(__file__).resolve().parents[1]
    manifest=json.loads((skill/'vendor/manifest.json').read_text(encoding='utf-8'))
    errors=[];count=0
    for name,repo in manifest['repositories'].items():
        for relative,expected in repo['files'].items():
            path=skill/'vendor'/name/relative
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
                errors.append(name+'/'+relative)
            count+=1
    components=json.loads((skill/'tools/wechat-publisher/wechat_publisher/gzh_components.json').read_text(encoding='utf-8'))
    for name,theme in components['themes'].items():
        path=skill/'vendor/gzh-design'/theme['source']
        source=path.read_text(encoding='utf-8')
        fences=re.findall(r'```html\s*\n(.*?)```',source,re.S)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=theme['source_sha256']:
            errors.append('template source '+name)
        for component in theme['components'].values():
            if component['html']!=fences[component['fence']].strip():
                errors.append('compiled template '+name)
    return {'passed':not errors,'repositories':len(manifest['repositories']),'original_files':count,
            'themes':len(components['themes']),'errors':errors}


if __name__=='__main__':
    result=verify();print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(0 if result['passed'] else 1)
