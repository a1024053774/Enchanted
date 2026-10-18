"""Runner regression: supplied process/socket boundaries, no real ps/PTY/GUI.

Failure list: None/partial nonblocking stdout, expected crash treated as failure,
layout diagnostics skip daemon_stop, stream close skips later cleanup, unknown
owner permits mutation, unconfirmed writer archived, stop receipt loss, archive
failure, operator identity omitted. Only subprocess: read known-bad source via Git.
"""
import ast
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/'evidence/2026-10-16-batch16/T-096'
spec=importlib.util.spec_from_file_location('t096_cleanup',FOLDER/'restart_cleanup.py')
support=importlib.util.module_from_spec(spec); spec.loader.exec_module(support)

class SavedBytes(io.BytesIO):
    def close(self):
        self.saved=self.getvalue(); super().close()

class Pipe:
    def __init__(self,values): self.values=list(values); self.closed=False
    def read(self,*unused):
        value=self.values.pop(0) if self.values else b''
        if isinstance(value,BaseException): raise value
        return value
    def close(self): self.closed=True


def observer(values=(None,),code=-9):
    process=SimpleNamespace(stdout=Pipe(values),stdin=io.BytesIO(),returncode=code,poll=lambda:code,wait=lambda **unused:code)
    return SimpleNamespace(process=process,owner=dict(pid=101,started='fixture birth',command='fixture Electron',driver='fixture',executable='fixture'),
        ready_confirmed=True,exit_confirmed=False,stdout=SavedBytes(),stderr=SavedBytes(),log=io.StringIO(),
        selector=SimpleNamespace(close=lambda:None),max_stdout_bytes=65536,close=lambda:(_ for _ in ()).throw(RuntimeError('observer_exit_nonzero')))

class Globals(ast.NodeTransformer):
    def visit_Nonlocal(self,node): return ast.copy_location(ast.Global(names=node.names),node)


def nested(source,name):
    main=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='main')
    return next(n for n in main.body if isinstance(n,ast.FunctionDef) and n.name==name)


def crash(source):
    item=observer(); gone=set(); ns=dict(observer=item,observer_expected_crash=False,observer_start_unconfirmed=False,result={},owned=[],
        run=lambda argv:SimpleNamespace(stdout='101 1\n102 101\n'),
        identify=lambda pid:None if pid in gone else dict(pid=pid,started='fixture birth',command='fixture Electron'),register=lambda owner,kind:owner,
        kill=lambda owner:gone.add(owner['pid']),alive=lambda owner:False,wait=lambda fn,*args,**kw:fn(),
        close_observer=support.close_observer,read_process=lambda pid:None,normal_quit=lambda *a,**kw:None)
    tree=ast.fix_missing_locations(ast.Module(body=[Globals().visit(nested(source,'crash_window'))],type_ignores=[]))
    exec(compile(tree,'runner-crash','exec'),ns); ns['crash_window']()
    assert ns['observer'] is None, 'Exited Electron must release its observer'
    assert item.process.stdout.closed and item.stdout.closed
    return item


def final_cleanup(source,unconfirmed=None,expected_red=False,crashed=False):
    main=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='main')
    final=next(n for n in main.body if isinstance(n,ast.Try)).finalbody
    item=observer(); actions=[]; close_calls=[]; stopped=False
    def close(*args,**kwargs):
        close_calls.append('close_observer')
        return support.close_observer(*args,**kwargs)
    owner=dict(pid=201,started='daemon birth',command='fixture daemon')
    fixture=Path(tempfile.mkdtemp(prefix='t096-cleanup-unit-',dir='/private/tmp'))
    def request(state,command,credential,**fields):
        nonlocal stopped
        actions.append(command)
        if command=='daemon_status': return dict(ok=True,pid=201)
        assert command=='daemon_stop'; stopped=True; return dict(ok=True)
    def call(command,**unused):
        actions.append(command)
        if command=='pane_layout': raise RuntimeError('caller_identity_required')
        return dict(ok=True)
    def wait(fn,*unused,**kw): assert fn(), 'fixture writer must already be absent after stop'
    ns=dict(observer=item,observer_expected_crash=True,observer_start_unconfirmed=False,reopen_close_unconfirmed=False,daemon_start_unconfirmed=False,expected_layout=[],daemon_live=True,
        result=dict(status='INCOMPLETE',error='original failure',cleanup_complete=False),args=SimpleNamespace(expect_red=False,label='unit'),
        call=call,check=lambda name,ok:None,operator_request=request,env={'A2A_OPERATOR_CREDENTIAL':str(fixture/'operator-1.json')},
        fixture=fixture,owned=[owner],alive=lambda o:not stopped,wait=wait,Path=Path,
        close_observer=close,read_process=lambda pid:None,identify=lambda pid:None,normal_quit=lambda *a,**kw:None,
        finish_cleanup=support.finish_cleanup,archive_fixture=lambda *args:dict(bytes=9,files=1,comparison=True),
        write_json=lambda *args:None,HERE=fixture,output=fixture,source=fixture,summary=fixture/'summary.json',
        api=None,requests=[],commands=[],sys=sys,json=json,shlex=__import__('shlex'))
    if expected_red or crashed:
        stopped=True
        (fixture/'state').mkdir(); (fixture/'state/control.sock').write_bytes(b'dead IPC fixture'); (fixture/'operator-1.json').write_bytes(b'private fixture')
        ns['daemon_live']=False
        endpoints={'control.sock':{'state':'stale_socket'}}
        ns['result']['daemon_start_receipt']=dict(epoch=1,pid=201)
        if expected_red: ns['result']['expected_red']=dict(daemon=201,endpoints=endpoints)
        else:
            ns['result']['backend_crash']=dict(epoch=1,pids=[201]); ns['daemon_live']=True
        ns['endpoint_state']=lambda *a:endpoints
        def copy_view(root,destination,excluded):
            assert set(excluded)=={'state/control.sock','operator-1.json'}
            assert (root/'operator-1.json').exists() and (root/'state/control.sock').exists()
            return dict(bytes=9,files=1,comparison=True)
        ns['copy_view']=copy_view
    if unconfirmed=='electron': ns.update(observer=None,observer_start_unconfirmed=True)
    if unconfirmed=='reopen-quit': ns.update(reopen_close_unconfirmed=True)
    if unconfirmed=='daemon': ns.update(daemon_start_unconfirmed=True)
    tree=ast.fix_missing_locations(ast.Module(body=[Globals().visit(n) for n in final],type_ignores=[]))
    with contextlib.redirect_stdout(io.StringIO()): exec(compile(tree,'runner-finally','exec'),ns)
    if unconfirmed:
        if unconfirmed=='reopen-quit': assert close_calls==[], 'Unconfirmed reopen quit must not send a second quit request'
        assert 'daemon_stop' not in actions and not ns['result']['cleanup_complete'] and ns['result']['handoff'], 'Unconfirmed spawn must be handed back, never declared absent'
        return
    if expected_red or crashed:
        assert 'daemon_stop' not in actions and ns['result']['cleanup_complete'] and (fixture/'operator-1.json').exists() and (fixture/'state/control.sock').exists(), 'Verified expected red must archive without changing its dead source endpoints'
        assert ns['result']['status']=='INCOMPLETE'
        return
    assert 'daemon_stop' in actions, 'Confirmed dead Electron plus a layout diagnostic must still stop the daemon'
    assert ns['result']['cleanup_complete'], 'All absent writers must be archived after safe stop'
    assert ns['result']['status']=='INCOMPLETE', 'A failed run must not be upgraded by successful cleanup'

report=dict(status='INCOMPLETE',scope='actual runner AST and cleanup helpers with supplied boundaries; no actual residual cleanup',checks=[])
try:
    old=subprocess.check_output(['git','show','10c0168db:evidence/2026-10-16-batch16/T-096/run_restart.py'],cwd=ROOT,text=True)
    for name,exercise,error_type in [('none_stdout',crash,TypeError),('cleanup_aborted',final_cleanup,AssertionError)]:
        try: exercise(old)
        except error_type as error:
            report.setdefault('known_bad',{})[name]=dict(revision='10c0168db',rejected=True,error=str(error))
    assert len(report.get('known_bad',{}))==2, 'Both reported defects must reject the known-bad runner'
    current=(FOLDER/'run_restart.py').read_text(encoding='utf-8')
    unsafe=current.replace("            if reopen_close_unconfirmed: raise RuntimeError('prior Electron quit unconfirmed; no repeated quit or archive')\n",'')
    assert unsafe!=current
    try: final_cleanup(unsafe,'reopen-quit')
    except AssertionError as error: report['reopen_quit_mutant']=dict(rejected=str(error).startswith('Unconfirmed reopen quit must not send'),error=str(error))
    assert report.get('reopen_quit_mutant',{}).get('rejected'), 'Repeated quit mutant must be rejected'
    crash(current); final_cleanup(current)
    final_cleanup(current,'electron'); final_cleanup(current,'daemon'); final_cleanup(current,'reopen-quit'); final_cleanup(current,expected_red=True)
    report['checks'].append('unconfirmed_reopen_quit_no_second_quit_or_daemon_stop')
    final_cleanup(current,crashed=True)
    old_crash=subprocess.check_output(['git','show','da6a095fc:evidence/2026-10-16-batch16/T-096/run_restart.py'],cwd=ROOT,text=True)
    try: final_cleanup(old_crash,crashed=True)
    except AssertionError as error: report['crash_cleanup_known_bad']=dict(revision='da6a095fc',rejected=True,error=str(error))
    assert report['crash_cleanup_known_bad']['rejected']
    report['checks'].append('kill_exception_with_all_writers_exited_still_archives')
    report['checks'].append('expected_red_archives_without_source_changes')
    report['checks'].append('unconfirmed_spawn_handoff')
    report['checks']+=['none_stdout_crash_fixed','finally_stops_daemon_after_layout_error','failed_run_stays_incomplete']
    for values,expected,eof in [([None],b'',False),([b'late bytes',None],b'late bytes',False),([b'tail',b''],b'tail',True),([BlockingIOError()],b'',False)]:
        item=observer(values)
        result=support.close_observer(item,expected_crash=True,read_process=lambda pid:None,normal_quit=lambda *a,**kw:None)
        assert result['exited'] and not result['diagnostics'] and result['stdout_eof']==eof and item.stdout.saved==expected
    report['checks'].append('partial_none_eof_and_would_block')
    item=observer()
    try: support.close_observer(item,expected_crash=True,read_process=lambda pid:dict(pid=101,started='replacement',command='other'),normal_quit=lambda *a,**kw:None)
    except RuntimeError: pass
    else: raise AssertionError('Replaced PID must not be adopted')
    assert not item.process.stdout.closed
    report['checks'].append('changed_owner_handed_back')
    def cleanup_case(stage):
        actions=[]
        def action(name,value=None):
            actions.append(name)
            if name==stage: raise RuntimeError('injected '+name)
            return value
        value=support.finish_cleanup(close_electron=lambda:action('electron',dict(exited=True,diagnostics=['expected failure preserved'])),
            stop_daemon=lambda:action('stop'),confirm_writers=lambda:action('writers'),archive=lambda:action('archive'))
        return value,actions
    for stage,expected,complete in [('electron',['electron'],False),('stop',['electron','stop','writers','archive'],True),
        ('writers',['electron','stop','writers'],False),('archive',['electron','stop','writers','archive'],False)]:
        value,actions=cleanup_case(stage)
        assert actions==expected and value['cleanup_complete']==complete
        assert value['handoff'] if not complete else value['diagnostics']
    report['checks']+=['unknown_electron_no_mutation','lost_stop_receipt_independent_exit_check','live_writer_no_archive','archive_failure_handoff']
    home=Path(tempfile.mkdtemp(prefix='t096-operator-unit-',dir='/private/tmp')); state=home/'state'; state.mkdir()
    credential=home/'operator.json'; identity=dict(kind='operator',state=str(state),epoch='fixture-epoch',token='fixture-token-not-a-login')
    credential.write_text(json.dumps(identity),encoding='utf-8'); credential.chmod(0o600)
    sent=[]
    class Client:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def settimeout(self,*args): pass
        def connect(self,path): assert path==str(state/'control.sock')
        def sendall(self,data): sent.append(json.loads(data))
        def recv(self,*args): return b'{"ok":true,"stopping":true}\n'
    with patch.object(support.socket,'socket',return_value=Client()):
        assert support.operator_request(state,'daemon_stop',credential)['stopping'] is True
    assert sent[0]['identity']==identity and sent[0]['input']==dict(command='daemon_stop')
    credential.chmod(0o644)
    with patch.object(support.socket,'socket',side_effect=AssertionError('unsafe credential must not connect')):
        try: support.operator_request(state,'daemon_stop',credential)
        except RuntimeError: pass
        else: raise AssertionError('Non-private operator credential was accepted')
    credential.unlink()
    report['checks']+=['operator_identity_sent_privately','unsafe_credential_refused']
    report['status']='PASS'
except BaseException as error:
    report['error']=str(error); report['traceback']=__import__('traceback').format_exc()
with Path(sys.argv[1]).open('x',encoding='utf-8') as destination: destination.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False)); sys.exit(0 if report['status']=='PASS' else 1)
