#!/usr/bin/env python3
"""Run the predeclared rev-4 cases through the single PTY backend."""
import argparse
import importlib.util
import json
from pathlib import Path
import shlex
import time

BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('native',BASE/'rev2-runner.py')
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
STOP=BASE/'rev4-stop.json'

def control(label,op,**kw):
    result=n.probe.control(label,dict(op=op,**kw))
    if result.get('error') or result.get('halt'):raise RuntimeError(json.dumps(result,ensure_ascii=False))
    return result

def check_stop():
    if STOP.exists():raise RuntimeError('Another rev-4 probe reached a stop condition')

def wait_for(label,predicate,seconds=90):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        check_stop();status=control(label,'status')
        if predicate(status):return status
        time.sleep(.05)
    raise RuntimeError('Required structured observation missing at cutoff')

def native_match(label,ident,ended):
    item=control(label,'item',id=ident)
    if ended:
        wait_for(label,lambda s:any(x['item_id']==ident and x['stop'] for x in s['submissions']))
    deadline=time.monotonic()+60;matched=[]
    while time.monotonic()<deadline:
        check_stop();control(label,'status')
        matched=[r for r in n.messages(label) if r['text']==item['registered_text']]
        if matched:break
        time.sleep(.05)
    item=control(label,'item',id=ident)
    if ended and len(matched)==1:
        entry=next(e for e in n.entries(label) if e['file']==matched[0]['source'] and e['line']==matched[0]['line'])
        rec=entry['record'];cli=n.manifest(label)['cli']
        native_id=rec['payload']['internal_chat_message_metadata_passthrough']['turn_id'] if cli=='codex' else rec['promptId']
        st=control(label,'status');sub=next(x for x in st['submissions'] if x['item_id']==ident)
        hook_id=sub['stop']['payload']['turn_id' if cli=='codex' else 'prompt_id']
        if native_id!=hook_id:raise RuntimeError('Stop does not match the native submitted message')
    result=dict(**item,label=label,observed_text=matched[0]['text'] if matched else None,
        observed_sources=matched,outcome='ok' if len(matched)==1 else 'other',cutoff_at=n.stamp())
    n.append(BASE/label/'observations.jsonl',result)
    # Simulated human messages are separate user inputs, never counted as injected text.
    n.append(BASE/('r7-injections.jsonl' if item['source']=='inject' else 'rev4-user-inputs.jsonl'),result)
    if result['outcome']!='ok':raise RuntimeError('Input is not one exact native user message')
    print(json.dumps(dict(label=label,id=ident,state=item['state'],source=item['source'],outcome=result['outcome'],queued_ms=item['queued_ms']),ensure_ascii=False),flush=True)
    return result

def prompt(text,state,source='inject',case_id=None,role=None):
    return dict(text=text,state=state,source=source,case_id=case_id,role=role)

def run(label,operation,sequence):
    manifest=n.manifest(label);cli=manifest['cli']
    if operation=='bootstrap':
        item=control(label,'submit',**prompt('只回复「T074 rev4 就绪」，不要调用工具。','bootstrap','user_sim'))
        native_match(label,item['id'],True);return
    wait_for(label,lambda s:s['gate_state']=='idle')
    if operation=='idle3':
        for i in range(3):
            item=control(label,'submit',**prompt(f'⟦主控 #{sequence+i}⟧ rev4 空闲样本 {i+1}：中文完整送达。只回复收到，不调用工具。','gated_idle',case_id=f'idle-{i+1}',role='B'))
            native_match(label,item['id'],True)
        return
    count=3 if operation=='race3' else 2
    state={'race3':'gated_race','user2':'gated_user_submit','esc2':'gated_after_esc'}[operation]
    for i in range(count):
        check_stop();wait_for(label,lambda s:s['gate_state']=='idle')
        case_id=f'{operation}-{i+1}';number=sequence+2*i
        marker=Path(manifest['fixture'])/f'rev4-{case_id}.txt'
        if operation=='esc2':
            assert not marker.exists()
            cmd=shlex.join(['python3','-c','from pathlib import Path; Path('+repr(str(marker))+').write_text("T074 rev4 marker",encoding="utf-8")'])
            extra='使用 exec_command 并传 sandbox_permissions="require_escalated"、justification="T074 rev4 夹具批准探针"。' if cli=='codex' else '使用 Bash；本会话 ask 规则要求批准。'
            text_a=f'⟦主控 #{number}⟧ 只执行一次 {cmd}。{extra} 取消后立即结束，不重试、不换工具。'
        else:
            text_a=f'⟦主控 #{number}⟧ rev4 {case_id} 的 A：只回复「A {i+1} 完成」，不要调用工具。'
        text_b=f'⟦主控 #{number+1}⟧ rev4 {case_id} 的 B：独立新消息，中文「完整送达」。只回复收到，不调用工具。'
        a_source='user_sim' if operation=='user2' else 'inject'
        pair=control(label,'pair',a=prompt(text_a,state,a_source,case_id,'A'),b=prompt(text_b,state,'inject',case_id,'B'))
        n.append(BASE/label/'case-events.jsonl',dict(at=n.stamp(),stage='pair-returned',case_id=case_id,pair=pair))
        if pair['b_phase']!='queued':raise RuntimeError('B was not blocked immediately after A CR')
        if operation!='esc2':
            native_match(label,pair['a_id'],True);native_match(label,pair['b_id'],True)
            continue
        deadline=time.monotonic()+90;event=None
        while time.monotonic()<deadline:
            check_stop();control(label,'status')
            f=BASE/label/'turn-hooks.jsonl'
            hooks=[json.loads(l) for l in f.read_text().splitlines()] if f.exists() else []
            events=[h for h in hooks if h['payload']['hook_event_name']=='PermissionRequest' and str(marker) in json.dumps(h['payload'].get('tool_input',{}),ensure_ascii=False)]
            if events:event=events[-1];break
            if marker.exists():raise RuntimeError('Approval marker executed before Esc')
            time.sleep(.05)
        if not event:raise RuntimeError('No matching PermissionRequest at cutoff')
        esc=control(label,'control',source='user_sim',bytes='\x1b',reason=f'Explicit Esc for {case_id}; never approval Enter')
        started=time.monotonic();hold_start=n.stamp()
        while time.monotonic()-started<30.1:
            check_stop();st=control(label,'status');b=control(label,'item',id=pair['b_id'])
            if st['gate_state']!='busy' or b['written'] or marker.exists():raise RuntimeError('Esc hold invariant failed')
            time.sleep(.1)
        held=dict(at=n.stamp(),stage='after-30s-hold',case_id=case_id,hold_start=hold_start,hold_seconds=time.monotonic()-started,
            permission_event=event,esc=esc,status=control(label,'status'),b=control(label,'item',id=pair['b_id']),marker_exists=marker.exists())
        n.append(BASE/label/'case-events.jsonl',held)
        # Require native interruption/rejection before the simulated user's explicit release.
        records=[e['record'] for e in n.entries(label)]
        if cli=='codex':
            interrupted=any(x['type']=='event_msg' and x['payload']['type']=='turn_aborted' and x['timestamp']>=hold_start[:19] for x in records)
        else:
            uses=[c for x in records if x.get('type')=='assistant' for c in x['message']['content'] if c.get('type')=='tool_use' and str(marker) in json.dumps(c.get('input',{}))]
            interrupted=bool(uses) and any(c.get('type')=='tool_result' and c.get('tool_use_id')==uses[-1]['id'] and c.get('is_error') for x in records if x.get('type')=='user' and isinstance(x['message']['content'],list) for c in x['message']['content'])
        if not interrupted:raise RuntimeError('No native rejection/interruption before release')
        action=control(label,'release',reason=f'Probe simulates user action after {case_id} Esc and verified 30s hold')
        n.append(BASE/label/'case-events.jsonl',dict(at=n.stamp(),stage='release',case_id=case_id,action=action))
        native_match(label,pair['a_id'],False);native_match(label,pair['b_id'],True)
        if marker.exists():raise RuntimeError('Marker executed around release')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('operation',choices=['bootstrap','idle3','race3','user2','esc2']);p.add_argument('--sequence',type=int,default=0);args=p.parse_args()
    try:run(args.label,args.operation,args.sequence)
    except Exception as error:
        failure=dict(at=n.stamp(),label=args.label,operation=args.operation,error=repr(error))
        n.append(BASE/args.label/'runner-failures.jsonl',failure)
        if not STOP.exists():
            with STOP.open('x') as f:json.dump(failure,f,ensure_ascii=False)
        print(json.dumps(failure,ensure_ascii=False),flush=True)
        raise
