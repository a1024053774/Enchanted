#!/usr/bin/env python3
"""Observe gate decisions and native receipt without retrying a message."""
import argparse
import datetime as dt
import importlib.util
import json
from pathlib import Path
import time

BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('native',BASE/'rev2-runner.py')
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)

def state(label):return n.probe.control(label,{'op':'status'})
def wait_end(label,after=None,seconds=60):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        g=state(label)['gate'];last=g['last_event']
        if g['allowed'] and (after is None or last['received_at']>after):return g
        time.sleep(.05)
    raise SystemExit('No matching Stop event before cutoff')

def observe(label,ident,seconds=60,marker=None):
    begin=time.monotonic();exact=[];embedded=[];attachments=[]
    while time.monotonic()-begin<seconds:
        item=n.probe.control(label,{'op':'item','id':ident})
        msgs=n.messages(label);text=item['registered_text']
        exact=[m for m in msgs if m['text']==text];embedded=[m for m in msgs if text in m['text']]
        attachments=[dict(text=e['record']['attachment']['prompt'],source=e['file'],line=e['line'],received_at=e['received_at'],record=e['record']) for e in n.entries(label) if e['record'].get('type')=='attachment' and e['record'].get('attachment',{}).get('type')=='queued_command' and e['record']['attachment'].get('prompt')==text]
        if exact or embedded or attachments:break
        time.sleep(.1)
    matched=exact or embedded or attachments
    result=dict(**item,label=label,observed_text=matched[0]['text'] if matched else None,
                observed_sources=matched,outcome='ok' if len(exact)==1 else 'merged' if embedded else 'other',
                cutoff_at=n.stamp(),observation_seconds=time.monotonic()-begin)
    if attachments and not exact and not embedded:
        result['native_record_type']='attachment.queued_command'
        result['reason']='delivered_mid_turn_attachment, not a separate ordinary user record'
    if item['queued_at'] and not item['written']:
        result['queued_seconds']=(dt.datetime.fromisoformat(result['cutoff_at'].replace('Z','+00:00'))-dt.datetime.fromisoformat(item['queued_at'].replace('Z','+00:00'))).total_seconds()
        result['reason']='Still queued under the literal hook rule; no bytes written'
    if marker:
        p=Path(marker);result['marker']={'path':str(p),'exists':p.exists(),'text':p.read_text() if p.exists() else None}
        if p.exists() and not exact:result['outcome']='taken_as_approval'
    n.append(BASE/label/'observations.jsonl',result);n.append(BASE/'r7-injections.jsonl',result)
    print(json.dumps({k:result.get(k) for k in ['label','id','state','outcome','written','queued_seconds']},ensure_ascii=False),flush=True)
    return result

def submit(label,text,state_name='idle_gated',diagnostic_running=False):
    item=n.probe.control(label,dict(op='submit',text=text,state=state_name,
                                   diagnostic_running=diagnostic_running,experiment='rev3'))
    return observe(label,item['id'])

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['idle5','submit','observe','wait']);parser.add_argument('label');parser.add_argument('--sequence',type=int);parser.add_argument('--text');parser.add_argument('--state',default='idle_gated');parser.add_argument('--id',type=int);parser.add_argument('--running',action='store_true')
    a=parser.parse_args()
    if a.operation=='wait':print(json.dumps(wait_end(a.label),ensure_ascii=False))
    elif a.operation=='observe':observe(a.label,a.id)
    elif a.operation=='submit':submit(a.label,a.text,a.state,a.running)
    else:
        wait_end(a.label)
        for index in range(5):
            result=submit(a.label,f'⟦主控 #{a.sequence+index}⟧ 空闲门禁样本 {index+1}：中文「完整送达」。只回复收到，不调用工具。')
            if result['outcome']!='ok':raise SystemExit('Idle sample did not arrive; stop without resend')
            wait_end(a.label,after=result['submitted_at'])
