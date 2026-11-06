#!/usr/bin/env python3
"""Prepare AIHOT scoring inputs and evaluate real, separately obtained receipts."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

SKILL = Path(__file__).resolve().parents[1]


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def prepare(materials, out):
    rows = json.loads(materials.read_text(encoding='utf-8'))
    if not isinstance(rows, list):
        raise ValueError('materials must be an array of original material records')
    out.mkdir(parents=True, exist_ok=True)
    prompt = (SKILL/'assets/prompts/selection-score.md').read_text(encoding='utf-8').replace('{{siteName}}','Chuan Lab')
    packets = []
    ids = set()
    for row in rows:
        cid = str(row.get('caseId', ''))
        if not cid or cid in ids:
            raise ValueError('Every material requires a unique caseId')
        ids.add(cid)
        material = row.get('material', {})
        if not material.get('title') or not (material.get('bodyOriginal') or material.get('bodyZh')):
            raise ValueError('Title-only materials wait for full text: '+cid)
        # Scoring is blind to source tier/name. Those affect only the outer gate.
        blind = {key:material.get(key) for key in ('title','originalTitle','publishedAt','bodyZh','bodyOriginal')}
        key = hashlib.sha256(cid.encode()).hexdigest()[:16]
        folder = out/key
        folder.mkdir(exist_ok=True)
        text = prompt+'\n\n<untrusted_material>\n'+json.dumps(blind,ensure_ascii=False,indent=2)+'\n</untrusted_material>\n'
        for round_number in (1,2):
            (folder/f'pass-{round_number}.md').write_text(text,encoding='utf-8')
        packets.append({'caseId':cid,'folder':key,'input_sha256':digest(blind),'sourceTier':row.get('sourceFacts',{}).get('sourceTier'),
                        'event_verified':row.get('event_verified',False),'adds_new_information':row.get('adds_new_information',False)})
    manifest={'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'cases':packets}
    manifest['sha256']=digest(manifest)
    save(out/'manifest.json',manifest)
    save(out/'receipt-format.json',{'input_manifest_sha256':manifest['sha256'],'scores':{row['caseId']:{'attentionScore':None} for row in packets}})
    (out/'instructions.md').write_text('每份 pass 输入分别评分，第二轮不带第一轮回执。只记录实际得到的 attentionScore。\n'
        '只有实际使用独立模型请求才给 evaluate 加 --independent；当前单会话两轮复核不能标独立。\n'
        '按 receipt-format.json 包装两份真实回执。不要把 null 填成凭空编造的分数。\n',encoding='utf-8')
    return manifest


def evaluate(out, first, second, independent=False):
    manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    receipts=[json.loads(p.read_text(encoding='utf-8')) for p in (first,second)]
    for receipt in receipts:
        if receipt.get('input_manifest_sha256')!=manifest['sha256']:
            raise ValueError('Scores refer to different material/prompt inputs')
    source=(SKILL/'vendor/aihot/industry/selection.ts').read_text(encoding='utf-8')
    thresholds={key:int(value) for key,value in re.findall(r'\b(T1_5|T1|T2):\s*(\d+)',source)}
    results=[]
    for case in manifest['cases']:
        scores=[]
        for receipt in receipts:
            answer=receipt.get('scores',{}).get(case['caseId'],{})
            if set(answer)!={'attentionScore'}:
                raise ValueError('Original AIHOT score contract requires attentionScore only')
            score=answer['attentionScore']
            if isinstance(score,bool) or not isinstance(score,int) or not 0<=score<=100:
                raise ValueError('An actual integer score from 0 through 100 is required')
            scores.append(score)
        threshold=thresholds.get(case['sourceTier'])
        qualified=threshold is not None and sum(scores)>=2*threshold
        results.append({**case,'scores':scores,'average':sum(scores)//2,'threshold':threshold,
                        'score_qualified':qualified,'selected':qualified and case['event_verified'] and case['adds_new_information']})
    result={'input_manifest_sha256':manifest['sha256'],'independent':independent,
            'calibration':'Original AIHOT starting thresholds; not yet calibrated against Chuan Lab outcomes', 'results':results}
    save(out/'selection-results.json',result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    commands=p.add_subparsers(dest='command',required=True)
    prep=commands.add_parser('prepare');prep.add_argument('--materials',type=Path,required=True);prep.add_argument('--out',type=Path,required=True)
    check=commands.add_parser('evaluate');check.add_argument('--out',type=Path,required=True)
    check.add_argument('--scores1',type=Path,required=True);check.add_argument('--scores2',type=Path,required=True)
    check.add_argument('--independent',action='store_true')
    args=p.parse_args()
    result=prepare(args.materials,args.out) if args.command=='prepare' else evaluate(args.out,args.scores1,args.scores2,args.independent)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    main()
