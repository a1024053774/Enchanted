#!/usr/bin/env python3
"""Read only this probe's native records; never use screen text as the oracle."""
import argparse
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import time

BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('probe',BASE/'probe.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)

def stamp():return dt.datetime.now(dt.timezone.utc).isoformat()
def append(path,value):
    with path.open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(value,ensure_ascii=False)+'\n');stream.flush();os.fsync(stream.fileno())
def manifest(label):return json.loads((BASE/label/'launch.json').read_text(encoding='utf-8'))
def entries(label):
    file=BASE/label/'native-events.jsonl'
    return [json.loads(line) for line in file.read_text(encoding='utf-8').splitlines()] if file.exists() else []
def messages(label):
    result=[];cli=manifest(label)['cli']
    for entry in entries(label):
        r=entry['record']
        if cli=='codex':
            p=r.get('payload',{})
            if r['type']!='response_item' or p.get('role')!='user':continue
            kinds=p.get('internal_chat_message_metadata_passthrough',{}).get('content_item_kinds',[])
            if 'user.text' not in kinds:continue
            text=''.join(c['text'] for c in p['content'] if c['type']=='input_text')
        else:
            if r.get('type')!='user' or r.get('isMeta'):continue
            content=r.get('message',{}).get('content')
            if isinstance(content,str):text=content
            elif isinstance(content,list) and not any(c['type']=='tool_result' for c in content):text=''.join(c['text'] for c in content if c['type']=='text')
            else:continue
        result.append(dict(text=text,line=entry['line'],source=entry['file'],received_at=entry['received_at']))
    return result
def wait(label,state,seconds=60):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        r=probe.control(label,{'op':'status'})
        if r['state']==state:return r
        time.sleep(.25)
    raise SystemExit('Structured state not reached: '+state)
def inject(label,text,state='idle',denial_ref=None):
    wait(label,'idle' if state=='never_after_denial' else state)
    registration=probe.control(label,dict(op='inject',state=state,method='M3',text=text,
                               experiment='rev2',denial_ref=denial_ref))
    if 'error' in registration:raise SystemExit(json.dumps(registration))
    started=time.monotonic();exact=[];embedded=[]
    while time.monotonic()-started<60:
        observed=messages(label);exact=[m for m in observed if m['text']==text];embedded=[m for m in observed if text in m['text']]
        if exact or embedded:break
        time.sleep(.25)
    matched=exact or embedded
    result=dict(**registration,label=label,observed_text=matched[0]['text'] if matched else None,
                observed_sources=matched,outcome='ok' if len(exact)==1 else 'merged' if embedded else 'other',
                cutoff_at=stamp(),observation_seconds=time.monotonic()-started)
    append(BASE/label/'observations.jsonl',result);append(BASE/'r7-injections.jsonl',result)
    print(json.dumps(dict(cli=result['cli'],label=label,state=state,outcome=result['outcome']),ensure_ascii=False),flush=True)
    return result
def snapshot(label,trial):
    m=manifest(label);target=BASE/label/f'outside-marker-{trial}.txt'
    record=dict(captured_at=stamp(),trial=trial,target=str(target),marker_exists=target.exists(),
                marker_text=target.read_text(encoding='utf-8') if target.exists() else None,
                status=probe.control(label,{'op':'status'}),native_tail=entries(label)[-16:],
                terminal_controls=[json.loads(s) for s in (BASE/label/'terminal-controls.jsonl').read_text(encoding='utf-8').splitlines()])
    path=BASE/label/f'denial-{trial}.json';path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return path,record

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['inject','wait','snapshot']);parser.add_argument('label');parser.add_argument('--text');parser.add_argument('--state',default='idle');parser.add_argument('--denial-ref');parser.add_argument('--trial',type=int)
    args=parser.parse_args()
    if args.operation=='inject':inject(args.label,args.text,args.state,args.denial_ref)
    elif args.operation=='wait':print(json.dumps(wait(args.label,args.state),ensure_ascii=False))
    else:
        path,r=snapshot(args.label,args.trial);print(path,r['marker_exists'])
