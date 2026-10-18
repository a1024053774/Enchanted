"""LOCAL T-096 kill/finally rehearsal, using real private Python process trees.

Inventory: no vendor CLI, model, daemon or Electron. Four isolated Python parents
with one Python child each, sequentially, plus bounded ps of their recorded PIDs.
No terminal keys or TCP network. Parent exposes only private synthetic Unix
daemon_status/daemon_stop receipts for exercising the runner's actual cleanup
(<=2 operator requests per case, each <=30s).
<=240 ps per scenario, <=12s exit waits. SIGKILL only
through the candidate runner's identity-checked kill, on this test's own tree.
Failure cleanup uses the private parent pipe to close/reap its child and exit;
no signal retry or process-group kill. Unknown exit produces an explicit handoff.
Source fixture in /private/tmp; stopped archive and raw reports on the mounted
external evidence volume. No credentials from users. Output: raw JSON plus an
optional small repository summary, exact argv, no overwrite.

Failure cases: parent death exits child before its kill slot; real unreaped zombie
changes ps command; child already exited/reaped; stable live command replacement
must never be signalled. Candidate finally must confirm every PID absent and copy
the stopped fixture without its dead IPC/private synthetic operator credential.
"""
import argparse
import ast
import contextlib
import io
import json
import os
from pathlib import Path
import selectors
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/'evidence/2026-10-16-batch16/T-096'
sys.path.insert(0,str(FOLDER))
from restart_cleanup import probe_process, close_observer, finish_cleanup, operator_request
from archive_failed_02 import endpoint_state, copy_view
from run_red import archive_fixture


def node(kind,fixture=None,fd=None):
    if kind=='child':
        os.read(fd,1); os.close(fd); return 0
    if kind=='replacement':
        print(json.dumps(dict(event='replacement',pid=os.getpid())),flush=True)
        if sys.stdin.readline().strip()!='shutdown': raise RuntimeError('replacement expected shutdown')
        return 0
    listener=socket.socket(socket.AF_UNIX)
    listener.bind(str(fixture/'state/control.sock')); listener.listen(1)
    reader,writer=os.pipe()
    child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--node','child','--fd',str(reader)],
        pass_fds=(reader,),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    os.close(reader)
    print(json.dumps(dict(event='spawned',parent=os.getpid(),child=child.pid)),flush=True)
    inputs=selectors.DefaultSelector(); inputs.register(sys.stdin,selectors.EVENT_READ); inputs.register(listener,selectors.EVENT_READ)
    deadline=time.monotonic()+90
    while time.monotonic()<deadline:
        available=inputs.select(1)
        if not available: continue
        key=available[0][0]
        if key.fileobj is listener:
            with listener.accept()[0] as client:
                client.settimeout(3); raw=b''
                while b'\n' not in raw:
                    part=client.recv(65536)
                    if not part or len(raw)+len(part)>65536: raise RuntimeError('invalid private request')
                    raw+=part
                request=json.loads(raw.split(b'\n')[0])
                expected=json.loads((fixture/'operator-1.json').read_text(encoding='utf-8'))
                assert request['identity']==expected, 'Private synthetic operator identity required'
                command=request['input']['command']
                assert command in ['daemon_status','daemon_stop']
                client.sendall((json.dumps(dict(ok=True,pid=os.getpid(),stopping=command=='daemon_stop'))+'\n').encode())
            if command=='daemon_status': continue
            command='shutdown'
            (fixture/'state/control.sock').unlink(); (fixture/'state/daemon.pid').unlink()
        else:
            line=sys.stdin.readline()
            command=line.strip() if line else 'shutdown'
        if command in ['exit-child','shutdown','replace'] and writer is not None:
            os.close(writer); writer=None
        if command in ['reap','shutdown','replace']:
            child.wait(timeout=5)
        if command=='replace':
            os.execv(sys.executable,[sys.executable,str(Path(__file__).resolve()),'--node','replacement'])
        print(json.dumps(dict(event=command,pid=child.pid)),flush=True)
        if command=='shutdown': return 0
    if writer is not None: os.close(writer)
    child.wait(timeout=5)
    return 0


class Globals(ast.NodeTransformer):
    def visit_Nonlocal(self,node): return ast.copy_location(ast.Global(names=node.names),node)


def until(fn,description,seconds=5):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        value=fn()
        if value: return value
        time.sleep(.05)
    raise TimeoutError(description)


def scenario(source,kind,output):
    home=Path(tempfile.mkdtemp(prefix='t096-tree-',dir='/private/tmp')).resolve()
    fixture=home/'fixture'; reports=output/'reports'
    (fixture/'state').mkdir(parents=True); output.mkdir(parents=True); reports.mkdir()
    (fixture/'payload.txt').write_bytes(b'T096 owned tree\n')
    credential=fixture/'operator-1.json'
    credential.write_text(json.dumps(dict(kind='operator',state=str(fixture/'state'),epoch='local-only',token='synthetic-test-only')),encoding='utf-8'); credential.chmod(0o600)
    selector=selectors.DefaultSelector()
    parent=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--node','parent','--fixture',str(fixture)],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True,bufsize=1)
    item=dict(case=kind,status='INCOMPLETE',fixture=str(fixture),output=str(output),parent=parent.pid,observations=[],cleanup_complete=False)
    pids=[parent.pid]; timer=None; timer_errors=[]
    def receive():
        if not selector.select(5): raise TimeoutError('private parent receipt')
        line=parent.stdout.readline()
        if not line: raise RuntimeError('private parent exited before receipt')
        value=json.loads(line); item.setdefault('private_receipts',[]).append(value); return value
    def command(text):
        parent.stdin.write(text+'\n'); parent.stdin.flush(); return receive()
    def run(argv,**unused):
        assert argv[:3]==['/bin/ps','-ww','-p'] and int(argv[3]) in pids, 'Only owned PID probes allowed'
        item['observations'].append(dict(argv=argv))
        if len(item['observations'])>240: raise RuntimeError('process read budget exceeded')
        parent.poll()  # Reap our direct child; its own child remains unreaped in the zombie case.
        value=subprocess.run(argv,capture_output=True,text=True,env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C'},timeout=5)
        item['observations'][-1].update(exit=value.returncode,stdout=value.stdout,stderr=value.stderr)
        return value
    def identity(pid): return probe_process(pid,run=run)
    def state(pid):
        value=run(['/bin/ps','-ww','-p',str(pid),'-o','pid=,stat=,command='])
        if value.returncode==1 and not value.stdout.strip() and not value.stderr.strip(): return 'absent'
        if value.returncode: raise RuntimeError('state query failed')
        return value.stdout.strip().split(maxsplit=2)[1]
    try:
        (output/'parent-start.json').write_text(json.dumps(dict(pid=parent.pid,fixture=str(fixture))),encoding='utf-8')
        selector.register(parent.stdout,selectors.EVENT_READ)
        spawned=receive(); assert spawned['parent']==parent.pid
        child=spawned['child']; pids.append(child); item['child']=child
        (fixture/'state/daemon.pid').write_text(str(parent.pid)+'\n',encoding='utf-8')
        owners=[identity(pid) for pid in pids]; assert all(owners)
        item['registered']=owners
        (output/'ownership.json').write_text(json.dumps(dict(fixture=str(fixture),owned=owners)),encoding='utf-8')
        main=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='main')
        functions=[Globals().visit(n) for n in main.body if isinstance(n,ast.FunctionDef) and n.name in ['identify','alive','kill']]
        ns=dict(result=dict(status='INCOMPLETE',process_reads=0,owned=owners,backend_crash=dict(epoch=1,pids=pids),daemon_start_receipt=dict(epoch=1,pid=parent.pid)),
            run=run,probe_process=probe_process,os=os,signal=signal,time=time)
        exec(compile(ast.fix_missing_locations(ast.Module(body=functions,type_ignores=[])),'candidate-process','exec'),ns)
        injection_error=None
        try:
            if kind=='parent-death':
                ns['kill'](owners[0]); parent.wait(timeout=5)
                # Ensure the child's EOF-driven exit won the race. Never kill it
                # merely to make the parent-death case pass.
                until(lambda:state(child)=='absent','orphan exits after parent death')
                ns['kill'](owners[1])
            elif kind=='zombie':
                command('exit-child')
                zombie=until(lambda:(s if (s:=state(child)).startswith('Z') else None),'real unreaped child zombie')
                item['real_zombie_state']=zombie
                def reap():
                    try: command('reap')
                    except BaseException as error: timer_errors.append(str(error))
                timer=threading.Timer(.3,reap); timer.start()
                ns['kill'](owners[1]); timer.join(timeout=6)
                assert not timer.is_alive() and not timer_errors, 'Private parent must reap the zombie'
                ns['kill'](owners[0]); parent.wait(timeout=5)
            elif kind=='already-exited':
                command('exit-child'); command('reap')
                assert identity(child) is None
                ns['kill'](owners[1]); ns['kill'](owners[0]); parent.wait(timeout=5)
            elif kind=='live-replacement':
                replacement=command('replace'); assert replacement['event']=='replacement'
                assert identity(parent.pid)['started']==owners[0]['started']
                try: ns['kill'](owners[0])
                except RuntimeError: item['replacement_refused']=True
                else: raise AssertionError('Live command replacement must be refused')
                assert parent.poll() is None and not ns['result'].get('signal_receipts'), 'Replacement must survive without a signal'
                parent.stdin.write('shutdown\n'); parent.stdin.flush(); parent.wait(timeout=5)
        except BaseException as error:
            injection_error=error; item['injection_error']=str(error)
        if timer:
            timer.join(timeout=6)
            assert not timer.is_alive() and not timer_errors
        assert all(not receipt['signal_sent'] for receipt in ns['result'].get('signal_receipts',[]) if receipt['pid']==child), 'Naturally exited child must never be signalled'
        # Execute the candidate's complete finally, with real stopped endpoints,
        # private synthetic operator request, process reads and archive copying.
        # Electron is absent by construction; no unrelated app is touched.
        def write_json(path,value):
            with path.open('x',encoding='utf-8') as destination: destination.write(json.dumps(value,ensure_ascii=False)+'\n')
        ns.update(observer=None,observer_start_unconfirmed=False,observer_expected_crash=False,expected_layout=None,
            daemon_live=True,daemon_start_unconfirmed=False,owned=owners,fixture=fixture,output=output,HERE=reports,summary=reports/'tree.run.json',source=ROOT,
            args=argparse.Namespace(label='tree'),env={'A2A_OPERATOR_CREDENTIAL':str(credential)},
            wait=lambda fn,description,timeout=30:until(fn,description,min(timeout,5)),operator_request=operator_request,
            close_observer=close_observer,finish_cleanup=finish_cleanup,normal_quit=None,endpoint_state=endpoint_state,copy_view=copy_view,
            archive_fixture=archive_fixture,
            write_json=write_json,Path=Path,api=None,requests=[],commands=[],sys=sys,json=json,shlex=__import__('shlex'))
        final=next(n for n in main.body if isinstance(n,ast.Try)).finalbody
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(ast.fix_missing_locations(ast.Module(body=[Globals().visit(n) for n in final],type_ignores=[])),'candidate-finally','exec'),ns)
        item['runner_result']=ns['result']
        assert ns['result']['status']=='INCOMPLETE', 'Successful cleanup must not upgrade a failed scenario to PASS'
        assert ns['result']['cleanup_complete'], 'Exited tree and verified dead endpoint must archive even after a kill exception'
        if ns['result'].get('stopped_crash_endpoints'):
            assert credential.exists() and (fixture/'state/control.sock').exists(), 'Stopped crash source evidence must remain'
        assert (output/'fixture/payload.txt').read_bytes()==b'T096 owned tree\n'
        assert not (output/'fixture/operator-1.json').exists() and not (output/'fixture/state/control.sock').exists()
        assert all(identity(pid) is None for pid in pids), 'All recorded PIDs must be absent'
        if injection_error: raise AssertionError('Candidate kill failed: '+str(injection_error))
        item['status']='PASS'
    except BaseException as error:
        item['error']=str(error); item['traceback']=traceback.format_exc()
    finally:
        if timer: timer.join(timeout=6)
        # Independent fixture teardown is deliberately a private graceful command,
        # so a faulty candidate cannot strand its own test tree or get a free retry.
        try:
            if parent.poll() is None:
                parent.stdin.write('shutdown\n'); parent.stdin.flush(); parent.wait(timeout=6)
                item['private_shutdown_returncode']=parent.returncode
            for pid in pids: until(lambda pid=pid:identity(pid) is None,'test-owned PID absent '+str(pid),seconds=5)
            item['cleanup_complete']=True
        except BaseException as error:
            item['status']='INCOMPLETE'; item['handoff']=dict(reason=str(error),fixture=str(fixture),pids=pids,policy='No signal retry; inspect only this test-owned tree')
        if parent.poll() is not None:
            raw=parent.stderr.read(65537)
            (output/'parent.stderr.txt').write_text(raw,encoding='utf-8')
            if len(raw)>65536:
                item['status']='INCOMPLETE'; item['error']='parent stderr exceeded 64 KiB budget'
        selector.close()
        for resource in [parent.stdin,parent.stdout,parent.stderr]: resource.close()
    return item


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node',choices=['parent','child','replacement']); parser.add_argument('--fixture',type=Path); parser.add_argument('--fd',type=int)
    parser.add_argument('--candidate',default='worktree'); parser.add_argument('--output',type=Path); parser.add_argument('--summary',type=Path)
    args=parser.parse_args()
    if args.node: return node(args.node,args.fixture,args.fd)
    if not args.output or args.output.exists(): raise RuntimeError('new report path required')
    if args.summary and args.summary.exists(): raise RuntimeError('new summary path required')
    base=Path('/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096')
    if not os.path.ismount('/Volumes/WD-Elements') or not args.output.resolve().is_relative_to(base): raise RuntimeError('mounted external raw output required')
    checked=['workbench/tests/test_t096_process_tree.py','evidence/2026-10-16-batch16/T-096/run_restart.py','evidence/2026-10-16-batch16/T-096/restart_cleanup.py','evidence/2026-10-16-batch16/T-096/archive_failed_02.py']
    if subprocess.check_output(['git','diff','HEAD','--',*checked],cwd=ROOT): raise RuntimeError('frozen harness and helper source required')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    args.output.parent.mkdir(parents=True,exist_ok=False)
    source=(FOLDER/'run_restart.py').read_text(encoding='utf-8') if args.candidate=='worktree' else subprocess.check_output(['git','show',args.candidate+':evidence/2026-10-16-batch16/T-096/run_restart.py'],cwd=ROOT,text=True)
    report=dict(status='INCOMPLETE',argv=sys.argv,candidate=args.candidate,harness_revision=revision,scope='real owned Python tree and actual runner kill/finally; no model/CLI/Electron',cases=[])
    for kind in ['parent-death','zombie','already-exited','live-replacement']:
        item=scenario(source,kind,args.output.parent/'cases'/kind); report['cases'].append(item)
        if not item['cleanup_complete']: break
    if len(report['cases'])==4 and all(item['status']=='PASS' for item in report['cases']): report['status']='PASS'
    with args.output.open('x',encoding='utf-8') as destination: destination.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    summary=dict(status=report['status'],argv=sys.argv,candidate=args.candidate,harness_revision=revision,raw_report=str(args.output),scope=report['scope'],
        cases=[dict(case=c['case'],status=c['status'],error=c.get('error'),cleanup=c['cleanup_complete'],fixture=c['fixture'],pids=[c['parent'],c.get('child')],
            ps_reads=len(c['observations']),real_zombie_state=c.get('real_zombie_state'),runner_cleanup=c.get('runner_result',{}).get('cleanup_complete'),handoff=c.get('handoff')) for c in report['cases']])
    if args.summary:
        with args.summary.open('x',encoding='utf-8') as destination: destination.write(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary))
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__': sys.exit(main())
