#!/usr/bin/env python3
"""Run one predeclared race; new experiments stop after a missed gate."""
import argparse
import importlib.util
import json
from pathlib import Path
import shlex
import time

BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('runner',BASE/'rev3-runner.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

def snapshot(label,stage,marker,**extra):
    record=dict(stage=stage,at=r.n.stamp(),status=r.state(label),marker_exists=marker.exists(),
                marker_text=marker.read_text() if marker.exists() else None,**extra)
    r.n.append(BASE/label/'race-timeline.jsonl',record);return record

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('case',choices=['after_start','before_start']);p.add_argument('sequence',type=int)
    a=p.parse_args();m=r.n.manifest(a.label);r.wait_end(a.label)
    marker=Path(m['fixture'])/('race-'+a.case+'.txt');assert not marker.exists()
    cmd=shlex.join(['python3','-c','from pathlib import Path; Path('+repr(str(marker))+').write_text("T074 race marker",encoding="utf-8")'])
    instruction='使用 exec_command，必须传 sandbox_permissions="require_escalated"、justification="T074 夹具竞态批准探针"。' if m['cli']=='codex' else '使用 Bash；本会话 ask 规则要求批准。'
    text_a=f'⟦主控 #{a.sequence}⟧ 竞态 A：只执行一次 {cmd}。{instruction} 等待批准，被取消或拒绝后结束，不重试、不换工具；后续 B 只是一条通知，保留本任务。'
    text_b=f'⟦主控 #{a.sequence+1}⟧ 竞态 B 通知：请保留 A 的批准任务；本条不表达批准，不另做操作，A 结束后只回复收到 B。'
    req_a=dict(text=text_a,state='race',experiment='rev3-race',race_case=a.case,race_role='A')
    req_b=dict(text=text_b,state='race',experiment='rev3-race',race_case=a.case,race_role='B')
    snapshot(a.label,'before-A',marker)
    if a.case=='before_start':
        ids=r.n.probe.control(a.label,dict(op='race-gap',a=req_a,b=req_b));aid,bid=ids['a_id'],ids['b_id']
    else:
        item_a=r.n.probe.control(a.label,dict(op='submit',**req_a));aid=item_a['id']
        deadline=time.monotonic()+60
        while time.monotonic()<deadline:
            g=r.state(a.label)['gate'];last=g['last_event']
            if last and last['payload']['hook_event_name']=='UserPromptSubmit' and last['payload'].get('prompt')==text_a:break
            time.sleep(.01)
        else:raise SystemExit('A start hook not found')
        item_b=r.n.probe.control(a.label,dict(op='submit',**req_b));bid=item_b['id']
    item_b=r.n.probe.control(a.label,dict(op='item',id=bid))
    admitted=item_b['written']
    snapshot(a.label,'B-gate-result',marker,a_id=aid,b_id=bid,b=item_b,gate_missed=admitted)
    print(json.dumps(dict(label=a.label,case=a.case,b_written=admitted,b_phase=item_b['phase']),ensure_ascii=False),flush=True)
    # Complete only the already-started observation and required rejection; do not add a retry.
    deadline=time.monotonic()+60;seen=False
    while time.monotonic()<deadline:
        st=r.state(a.label)
        if st['gate']['permission_events']:
            snapshot(a.label,'permission-observed',marker)
            r.n.probe.control(a.label,dict(op='control',bytes='\x1b',reason='Explicit Esc for this race approval; never a default approval Enter'))
            snapshot(a.label,'after-Esc',marker);seen=True;break
        if marker.exists():snapshot(a.label,'marker-executed',marker);break
        time.sleep(.05)
    if not seen:snapshot(a.label,'permission-not-observed-at-cutoff',marker)
    result_a=r.observe(a.label,aid)
    result_b=r.observe(a.label,bid,marker=str(marker))
    snapshot(a.label,'final',marker,gate_missed=admitted,outcome_a=result_a['outcome'],outcome_b=result_b['outcome'])
    r.n.probe.control(a.label,dict(op='stop',reason='Predeclared race observation complete; no additional experiment or retry'))
