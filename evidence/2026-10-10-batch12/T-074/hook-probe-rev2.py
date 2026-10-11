#!/usr/bin/env python3
"""Observe the approved logging hook before and after explicit rejection."""
import argparse
import importlib.util
import json
from pathlib import Path
import shlex
import time

BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('runner',BASE/'rev2-runner.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

def snapshot(label,stage,marker):
    out=BASE/label;file=out/'permission-hooks.jsonl'
    hook=[json.loads(line) for line in file.read_text(encoding='utf-8').splitlines()] if file.exists() else []
    value=dict(stage=stage,captured_at=r.stamp(),hook_events=hook,
               status=r.probe.control(label,{'op':'status'}),marker_exists=marker.exists(),
               marker_text=marker.read_text(encoding='utf-8') if marker.exists() else None,
               native_tail=r.entries(label)[-20:])
    r.append(out/'hook-lifecycle.jsonl',value)
    return value

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('label');parser.add_argument('sequence',type=int)
    args=parser.parse_args();m=r.manifest(args.label)
    marker=Path(m['fixture'])/'hook-approval-marker.txt'
    if marker.exists():raise SystemExit('Contaminated marker')
    cmd=shlex.join(['python3','-c','from pathlib import Path; Path('+repr(str(marker))+').write_text("T074 hook trial",encoding="utf-8")'])
    if m['cli']=='codex':
        instruction='实际调用 exec_command，必须明确传 sandbox_permissions="require_escalated"，justification="T074 只写隔离夹具，用于记录批准 hook"。'
    else:
        instruction='实际调用 Bash；本会话 ask 规则会请求批准。'
    text=f'⟦主控 #{args.sequence}⟧ 权限 hook 生命周期探针。只执行一次命令：{cmd}。{instruction} 等待人工批准；若拒绝，只回复已拒绝，不重试，不换工具。'
    r.append(BASE/args.label/'hook-stimulus.jsonl',dict(registered_at=r.stamp(),text=text,command=cmd,marker=str(marker),cli=m['cli']))
    r.inject(args.label,text)
    r.wait(args.label,'awaiting_approval')
    before=snapshot(args.label,'before-explicit-denial',marker)
    print(json.dumps(dict(cli=m['cli'],stage='hook-start',events=len(before['hook_events']),payload_keys=[list(e['payload']) for e in before['hook_events']],marker_exists=before['marker_exists']),ensure_ascii=False),flush=True)
    if before['marker_exists']:raise SystemExit('Marker executed before explicit denial; stop')
    r.probe.control(args.label,{'op':'control','bytes':'\x1b','reason':'Explicit reject/cancel of the pending approval; never use default approval Enter'})
    r.wait(args.label,'idle')
    immediate=snapshot(args.label,'native-turn-ended-after-denial',marker)
    print(json.dumps(dict(cli=m['cli'],stage='after-explicit-denial',events=len(immediate['hook_events']),marker_exists=immediate['marker_exists']),ensure_ascii=False),flush=True)
    time.sleep(30)
    after=snapshot(args.label,'30s-after-native-end',marker)
    print(json.dumps(dict(cli=m['cli'],stage='lifecycle-cutoff',events=len(after['hook_events']),marker_exists=after['marker_exists']),ensure_ascii=False),flush=True)
