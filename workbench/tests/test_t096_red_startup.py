"""Actual runner/helper callbacks with supplied external boundaries only.
No daemon, PTY, ps, native CLI, Electron or model. Only subprocess: Git source.
Failure list: all startup errors accepted as red; wrong mode accepted; partial
spawn accepted; missing expectation allowed; UI receipt replaces history oracle;
unapproved/repeated/mismatched screen key sent; readiness releases queued input or
an unreviewed screen; profile wait bypassed/loops forever.
"""
import argparse
import ast
import base64
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; FOLDER=ROOT/'evidence/2026-10-16-batch16/T-096'
sys.path.insert(0,str(FOLDER))
import restart_cleanup as support
import startup_controls as controls
source=(FOLDER/'run_restart.py').read_text(encoding='utf-8')

class Globals(ast.NodeTransformer):
    def visit_Nonlocal(self,node): return ast.copy_location(ast.Global(names=node.names),node)

def function(text,name):
    main=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='main')
    return next(n for n in main.body if isinstance(n,ast.FunctionDef) and n.name==name)

def load(node,namespace):
    tree=ast.fix_missing_locations(ast.Module(body=[Globals().visit(node)],type_ignores=[]))
    exec(compile(tree,'runner-callback','exec'),namespace)

REFUSAL=dict(ok=False,error='daemon_call_failed',details='Error: socket exists; query its owner, do not replace it')

def start(text,mode='red',reply=REFUSAL,credential=False,live=False,endpoint='stale_socket'):
    home=Path(tempfile.mkdtemp(prefix='t096-red-unit-',dir='/private/tmp'))
    if credential: (home/'operator-2.json').write_text('unit fixture',encoding='utf-8')
    namespace=dict(args=SimpleNamespace(expect_red=mode=='red'),fixture=home,env={},daemon_live=False,daemon_start_unconfirmed=False,
        result=dict(daemon_start_receipt=dict(epoch=1,pid=201)),owned=[dict(pid=201)],commands=[dict(id=47)],Path=Path,json=json,
        run=lambda *a,**kw:SimpleNamespace(returncode=1,stdout=json.dumps(reply)),cli=['fixture-node','fixture-cli'],
        call=lambda *a,**kw:(_ for _ in ()).throw(RuntimeError('baseline pre-spawn refusal')),
        alive=lambda owner:live,endpoint_state=lambda *a:dict({'control.sock':dict(state=endpoint)}),
        dead_endpoint_rejection=support.dead_endpoint_rejection)
    load(function(text,'start_daemon'),namespace)
    error=None
    try: value=namespace['start_daemon'](2)
    except BaseException as caught: error=caught; value='failed'
    if mode=='red' and reply==REFUSAL and not credential and not live and endpoint=='stale_socket':
        assert error is None and value is None and not namespace['daemon_start_unconfirmed'], 'Verified pre-spawn dead endpoint must be recorded as expected red'
        assert namespace['result']['observed_behavior']=='NO_GO'
    else:
        assert error is not None and namespace['daemon_start_unconfirmed'], 'Unexpected/partial startup must remain unconfirmed'
    return namespace


def strict_oracle(text,terminal):
    calls=[node for node in ast.walk(ast.parse(text)) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='check' and node.args and isinstance(node.args[0],ast.BinOp) and isinstance(node.args[0].right,ast.Constant) and node.args[0].right.value=='_native_history_visible']
    assert len(calls)==1, 'Strict native history oracle must remain present exactly once'
    def check(name,value): assert value, 'Missing independently supplied history nonce must fail'
    namespace=dict(check=check,record=dict(preset='ideation',id='L'),histories={'L':dict(nonce='NONCE_FROM_EXTERNAL_FIXTURE')},view=dict(terminal=terminal))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.Expr(value=calls[0])],type_ignores=[])),'history-oracle','exec'),namespace)

report=dict(status='INCOMPLETE',argv=sys.argv,scope='runner/startup controls over supplied boundaries, no real CLI resume proof',checks=[])
try:
    old=subprocess.check_output(['git','show','f6c2c6a63:evidence/2026-10-16-batch16/T-096/run_restart.py'],cwd=ROOT,text=True)
    try: start(old)
    except AssertionError as error: report['known_bad']=dict(revision='f6c2c6a63',rejected=str(error).startswith('Verified pre-spawn'),error=str(error))
    assert report['known_bad']['rejected']
    start(source)
    actual_main=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='main')
    run_body=next(n for n in actual_main.body if isinstance(n,ast.Try)).body
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='unlink' for node in run_body for n in ast.walk(node)), 'Baseline dead endpoints must not be removed before testing restart'
    report['checks'].append('baseline_endpoints_not_precleaned')
    for options in [dict(mode='restore'),dict(credential=True),dict(live=True),dict(endpoint='live'),dict(reply=dict(ok=False,error='daemon_call_failed',details='Error: daemon start deadline'))]: start(source,**options)
    report['checks']+=['observed_red_accepted','other_errors_modes_and_partial_start_refused']
    main=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='main')
    prefix=[]
    for node in main.body:
        prefix.append(node)
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='args' for t in node.targets): break
    arguments=['runner','--source','/fixture','--output','/fixture','--claude','/fixture/cli','--label','x','--approval-ref','ref','--claude-version','2.1.302']
    with patch.object(sys,'argv',arguments),contextlib.redirect_stderr(io.StringIO()):
        try: exec(compile(ast.fix_missing_locations(ast.Module(body=prefix,type_ignores=[])),'runner-parser','exec'),dict(argparse=argparse,Path=Path,__doc__='unit'))
        except SystemExit as error: assert error.code==2
        else: raise AssertionError('Expectation must be mandatory before any resource starts')
    report['checks'].append('expectation_required')
    try: strict_oracle(source,'Choose the text style that looks best with your terminal')
    except AssertionError: pass
    else: raise AssertionError('Onboarding text cannot replace native history')
    strict_oracle(source,'history NONCE_FROM_EXTERNAL_FIXTURE end')
    weak=source.replace("histories[record['id']]['nonce'] in view['terminal'])",'True)')
    try:
        try: strict_oracle(weak,'no history')
        except AssertionError: pass
        else: raise AssertionError('Weak nonce mutant accepted absent history')
    except AssertionError as error: report['nonce_mutant']=dict(rejected=True,error=str(error))
    assert report['nonce_mutant']['rejected']
    report['checks']+=['theme_is_not_history','strict_nonce_retained','weak_nonce_mutant_refused']
    home=Path(tempfile.mkdtemp(prefix='t078-2-t096-unit-',dir='/private/tmp')).resolve(); output=home/'evidence'/'run'; output.mkdir(parents=True)
    controls.BASE=home/'evidence'
    record=dict(id='launch',task='task',session='native',thread='thread',preset='ideation',role='controller',attempt=None,authentication='isolated fake API only',worktree=str(home/'repo'))
    context=dict(schema=1,fixture=str(home),state=str(home/'state'),task='task',launch='launch',session='native',thread='thread',preset='ideation',operator_credential=str(home/'operator-1.json'),output=str(output))
    context_path=output/'ideation.startup.json'; context_path.write_text(json.dumps(context),encoding='utf-8')
    raw=b'\x1b[31mChoose the text style\x1b[0m\r\n'; mutations=[]
    status=dict(state='unknown',active=None,queued=[],writing=False,user_draft=False)
    def request(state,command,credential,**fields):
        if command=='launch_show': return dict(launch=record)
        if command=='pane_process_info': return dict(leader=201,failed=None,native_session='native')
        if command=='pane_output': return dict(start_offset=0,next_offset=len(raw),total_bytes=len(raw),data_base64=base64.b64encode(raw).decode('ascii'))
        if command=='pane_status': return status
        assert command in ['pane_screen_key','pane_release']; mutations.append(dict(command=command,**fields)); return dict(ok=True,written=True)
    controls.operator_request=request
    captured=controls.capture(context_path,'theme')
    screen=Path(captured['screen']); template=Path(captured['approval_template'])
    approved=json.loads(template.read_text(encoding='utf-8'))
    try: controls.key(screen,template)
    except RuntimeError: pass
    else: raise AssertionError('An unapproved template must never send a key')
    assert not mutations
    approved.update(approved_by='executor',approval_ref='principal screen approval',basis='inspected this raw theme screen',key='ArrowUp',purpose='onboarding-theme',selected_label='Auto (match terminal)')
    approval=output/'approved.json'; approval.write_text(json.dumps(approved),encoding='utf-8')
    controls.key(screen,approval)
    assert len(mutations)==1 and mutations[0]['key']=='ArrowUp' and base64.b64decode(mutations[0]['screen_base64'])==raw
    try: controls.key(screen,approval)
    except RuntimeError: pass
    else: raise AssertionError('A repeated receipt must never send a second key')
    assert len(mutations)==1
    raw=b'Native prompt ready; no queued input.\r\n'
    captured=controls.capture(context_path,'prompt-ready')
    ready_screen=Path(captured['screen']); ready_template=Path(captured['approval_template'])
    try: controls.ready(ready_screen,ready_template)
    except RuntimeError: pass
    else: raise AssertionError('Readiness requires its own explicit approval')
    ready_approved=json.loads(ready_template.read_text(encoding='utf-8'))
    ready_approved.update(approved_by='executor',approval_ref='principal readiness approval',basis='inspected native prompt after trust',action='startup-ready')
    ready_approval=output/'ready-approved.json'; ready_approval.write_text(json.dumps(ready_approved),encoding='utf-8')
    for change in [dict(queued=['unsent']),dict(active='busy'),dict(writing=True),dict(user_draft=True),dict(state='idle')]:
        original=status.copy(); status.update(change)
        try: controls.ready(ready_screen,ready_approval)
        except RuntimeError: pass
        else: raise AssertionError('Readiness must not release input or an active pane')
        status=original
    original_raw=raw; raw+=b'Changed after approval'
    try: controls.ready(ready_screen,ready_approval)
    except RuntimeError: pass
    else: raise AssertionError('A changed readiness screen must be refused')
    raw=original_raw
    assert len(mutations)==1
    controls.ready(ready_screen,ready_approval)
    assert len(mutations)==2 and mutations[-1]['command']=='pane_release' and 'principal readiness approval' in mutations[-1]['reason']
    try: controls.ready(ready_screen,ready_approval)
    except RuntimeError: pass
    else: raise AssertionError('Readiness release cannot be repeated')
    assert len(mutations)==2
    def profile_wait(trusted=False,released=False,post=False,release_seq=8):
        clock=[0]; queried=[]; saved=[]
        def request(state,command,credential,**kwargs):
            queried.append(command)
            keys=[]
            if len(queried)>1:
                if trusted: keys.append(dict(launch='launch',type='controller_screen_key_written',seq=7,data=dict(key='Enter',purpose='workspace-trust',screen_id='approved')))
                if released: keys.append(dict(launch='launch',type='executor_action',seq=release_seq,data=dict(action='initial_release')))
            return dict(events=keys)
        ns=dict(output=output,fixture=home,source=home,env={'A2A_OPERATOR_CREDENTIAL':str(home/'operator-1.json')},
            args=SimpleNamespace(startup_wait_seconds=4),result=dict(keys=[]),requests=[dict(method='POST')] if post else [],
            operator_request=request,Path=Path,json=json,time=SimpleNamespace(monotonic=lambda:clock[0],sleep=lambda seconds:clock.__setitem__(0,clock[0]+seconds)),
            write_json=lambda path,payload:saved.append((path,payload)))
        load(function(source,'wait_for_profile'),ns)
        with contextlib.redirect_stdout(io.StringIO()):
            if trusted and released and release_seq>7 and not post: ns['wait_for_profile'](record); assert ns['result']['keys'] and queried==['orchestration_events']*2
            else:
                try: ns['wait_for_profile'](record)
                except (TimeoutError,RuntimeError): pass
                else: raise AssertionError('Profile wait must not bypass missing approval or zero model budget')
        assert all(command=='orchestration_events' for command in queried), 'Runner must never send a startup key itself'
    profile_wait(trusted=True,released=True); profile_wait(); profile_wait(trusted=True); profile_wait(released=True); profile_wait(trusted=True,released=True,release_seq=6); profile_wait(trusted=True,released=True,post=True)
    report['checks']+=['profile_wait_requires_trust_then_readiness_receipts','profile_wait_bounded','profile_wait_zero_model_budget']
    report['checks']+=['readiness_requires_new_explicit_approval','readiness_refuses_queued_active_or_changed_screen','readiness_empty_queue_only','no_repeated_readiness_release']
    report['checks']+=['raw_screen_preserved','no_automatic_approval','one_bound_approved_key','no_repeated_key']
    report['status']='PASS'
except BaseException as error: report['error']=str(error); report['traceback']=__import__('traceback').format_exc()
with Path(sys.argv[1]).open('x',encoding='utf-8') as destination: destination.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False)); sys.exit(0 if report['status']=='PASS' else 1)
