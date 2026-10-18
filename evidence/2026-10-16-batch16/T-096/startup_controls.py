#!/usr/bin/env python3
"""CONTROLLER ONLY: capture one owned startup screen, or send ONE approved key.

No CLI/Electron/model start, login, prompt submit, policy bypass or global writes.
Capture: <=16 pane_output reads (<=1 MiB), one native-process identity query.
Key: exactly one of ArrowUp/ArrowDown/Enter, using the existing pane_screen_key
operator entry and one explicit approval file bound to raw screen/session/path.
No automatic key choice, default Enter, retries or onboarding-state edits.
Ready: one separately approved initial pane_release; queue/active/input must
be empty and the reviewed screen unchanged. It sends no model prompt.
A changed screen or rejected approval stops; inspect a new capture before acting.
Only the live initial epoch of a T-096 isolated fake-API fixture is accepted.
"""
import argparse
import base64
import json
from pathlib import Path
import re
import sys
import uuid

sys.dont_write_bytecode=True
from restart_cleanup import operator_request

BASE=Path('/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096')


def bound_context(path):
    context=json.loads(path.read_text(encoding='utf-8'))
    fixture=Path(context['fixture'])
    if not str(fixture).startswith('/private/tmp/t078-2-t096-') or fixture.resolve()!=fixture:
        raise RuntimeError('isolated T-096 fixture required')
    if context['state']!=str(fixture/'state') or context['operator_credential']!=str(fixture/'operator-1.json'):
        raise RuntimeError('initial epoch context binding mismatch')
    if not Path(context['output']).resolve().is_relative_to(BASE) or Path(context['output']).resolve()==BASE:
        raise RuntimeError('run output must remain under T-096 external evidence')
    state=fixture/'state'; credential=Path(context['operator_credential'])
    record=operator_request(state,'launch_show',credential,launch=context['launch'])['launch']
    if any(record[key]!=context[key] for key in ['task','session','thread','preset']) or record['id']!=context['launch'] or record['role']!='controller' or record['attempt'] is not None or record['authentication']!='isolated fake API only' or record['worktree']!=str(fixture/'repo'):
        raise RuntimeError('live controller launch does not match startup context')
    info=operator_request(state,'pane_process_info',credential,thread=context['thread'])
    if not info.get('leader') or info.get('failed') or info['native_session']!=context['session']:
        raise RuntimeError('live native controller identity unconfirmed')
    return context


def capture(context_path,name):
    if not re.fullmatch('[a-zA-Z0-9_-]+',name): raise RuntimeError('simple new capture name required')
    context=bound_context(context_path); state=Path(context['state']); credential=Path(context['operator_credential'])
    directory=Path(context['output'])/'startup-screens'/context['preset']; directory.mkdir(parents=True,exist_ok=True)
    raw=directory/(name+'.raw'); screen=directory/(name+'.screen.json')
    if raw.exists() or screen.exists(): raise RuntimeError('capture already exists; choose a new name')
    data=bytearray(); offset=0
    for unused in range(16):
        value=operator_request(state,'pane_output',credential,launch=context['launch'],offset=offset,max_bytes=65536)
        if value['start_offset']!=offset: raise RuntimeError('output cursor changed')
        data.extend(base64.b64decode(value['data_base64'],validate=True)); offset=value['next_offset']
        if offset==value['total_bytes']: break
    else: raise RuntimeError('screen exceeds capture budget')
    with raw.open('xb') as output: output.write(data)
    # Display text is advisory only. Authorization is tied to the complete raw
    # bytes; the daemon independently verifies them immediately before the key.
    text=data.decode('utf-8',errors='strict')
    display=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',text)
    display=re.sub(r'\x1b\][^\x07]*(?:\x07|\x1b\\)','',display)
    display=''.join(c if ord(c)>=32 or c in '\n\r\t' else f'<0x{ord(c):02x}>' for c in display)
    directory.joinpath(name+'.txt').write_text(display,encoding='utf-8')
    material=dict(schema=1,context=str(context_path.resolve()),screen_id=str(uuid.uuid4()),screen_file=str(raw),bytes=len(data),display_only=str(directory/(name+'.txt')))
    with screen.open('x',encoding='utf-8') as output: output.write(json.dumps(material,ensure_ascii=False,indent=2)+'\n')
    template=dict(launch=context['launch'],session=context['session'],directory=str(Path(context['fixture'])/'repo'),screen_id=material['screen_id'],screen_file=str(raw),
        approved_by=None,approval_ref=None,basis=None,key=None,purpose=None,selected_label=None)
    with directory.joinpath(name+'.approval-template.json').open('x',encoding='utf-8') as output: output.write(json.dumps(template,ensure_ascii=False,indent=2)+'\n')
    return dict(status='PASS',scope='screen capture only; no key authorized',screen=str(screen),display=material['display_only'],approval_template=str(directory/(name+'.approval-template.json')))


def key(screen_path,approval_path):
    screen=json.loads(screen_path.read_text(encoding='utf-8')); context=bound_context(Path(screen['context']))
    approved=json.loads(approval_path.read_text(encoding='utf-8'))
    expected=dict(launch=context['launch'],session=context['session'],directory=str(Path(context['fixture'])/'repo'),screen_id=screen['screen_id'],screen_file=screen['screen_file'])
    if any(approved.get(k)!=v for k,v in expected.items()) or approved.get('approved_by')!='executor' or not approved.get('approval_ref') or not approved.get('basis'):
        raise RuntimeError('explicit per-screen executor approval required')
    if approved.get('key') not in ['ArrowUp','ArrowDown','Enter'] or approved.get('purpose') not in ['onboarding-theme','onboarding-notice','workspace-trust'] or not approved.get('selected_label'):
        raise RuntimeError('one explicit startup key/purpose/selection required')
    receipt=screen_path.with_name(screen_path.stem+'.key-receipt.json')
    if receipt.exists(): raise RuntimeError('key receipt already exists; no repeated action')
    raw=Path(screen['screen_file']).read_bytes()
    reply=operator_request(Path(context['state']),'pane_screen_key',Path(context['operator_credential']),thread=context['thread'],key=approved['key'],purpose=approved['purpose'],
        screen_id=screen['screen_id'],screen_base64=base64.b64encode(raw).decode('ascii'),authorization_ref=approved['approval_ref'],selected_label=approved['selected_label'])
    with receipt.open('x',encoding='utf-8') as output: output.write(json.dumps(dict(approval=approved,result=reply),ensure_ascii=False,indent=2)+'\n')
    return dict(status='PASS',scope='one explicitly approved key; no model prompt submitted',receipt=str(receipt))



def ready(screen_path,approval_path):
    screen=json.loads(screen_path.read_text(encoding='utf-8')); context=bound_context(Path(screen['context']))
    approved=json.loads(approval_path.read_text(encoding='utf-8'))
    expected=dict(launch=context['launch'],session=context['session'],directory=str(Path(context['fixture'])/'repo'),screen_id=screen['screen_id'],screen_file=screen['screen_file'])
    if any(approved.get(k)!=v for k,v in expected.items()) or approved.get('approved_by')!='executor' or approved.get('action')!='startup-ready' or not approved.get('approval_ref') or not approved.get('basis'):
        raise RuntimeError('explicit post-startup screen readiness approval required')
    state=Path(context['state']); credential=Path(context['operator_credential'])
    status=operator_request(state,'pane_status',credential,thread=context['thread'])
    if status['state']!='unknown' or status.get('active') or status.get('queued') or status.get('writing') or status.get('user_draft'):
        raise RuntimeError('readiness release requires an empty, inactive startup pane')
    current=operator_request(state,'pane_output',credential,launch=context['launch'],offset=0,max_bytes=65536)
    if current['next_offset']!=current['total_bytes'] or base64.b64decode(current['data_base64'])!=Path(screen['screen_file']).read_bytes():
        raise RuntimeError('readiness screen changed; capture and approve a fresh screen')
    receipt=screen_path.with_name(screen_path.stem+'.ready-receipt.json')
    if receipt.exists(): raise RuntimeError('readiness receipt exists; no repeated release')
    reply=operator_request(state,'pane_release',credential,thread=context['thread'],reason=approved['approval_ref']+'; '+approved['basis'])
    with receipt.open('x',encoding='utf-8') as output: output.write(json.dumps(dict(approval=approved,result=reply),ensure_ascii=False,indent=2)+'\n')
    return dict(status='PASS',scope='explicit startup readiness release with no queued prompt; not a resume verdict',receipt=str(receipt))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    read=sub.add_parser('capture'); read.add_argument('--context',type=Path,required=True); read.add_argument('--name',required=True)
    write=sub.add_parser('key'); write.add_argument('--screen',type=Path,required=True); write.add_argument('--approval-file',type=Path,required=True)
    release=sub.add_parser('ready'); release.add_argument('--screen',type=Path,required=True); release.add_argument('--approval-file',type=Path,required=True)
    args=parser.parse_args()
    try:
        result=capture(args.context,args.name) if args.command=='capture' else key(args.screen,args.approval_file) if args.command=='key' else ready(args.screen,args.approval_file)
    except BaseException as error:
        result=dict(status='INCOMPLETE',error=str(error),policy='No retry or substitute key; preserve raw screen and inspect before acting')
    print(json.dumps(result,ensure_ascii=False)); return 0 if result['status']=='PASS' else 1

if __name__=='__main__': sys.exit(main())
