"""Real probe and runner callbacks, supplied ps/signal boundary. No actual ps.
Failures: empty rc1 rejected; noisy rc1 accepted; other errors swallowed; repeated
identity read races; exit between read/signal rejected; replaced PID signalled.
Only subprocess: Git reads the known-bad runner source.
"""
import ast
import importlib.util
import json
from pathlib import Path
import signal
import subprocess
import sys
from types import SimpleNamespace

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; FOLDER=ROOT/'evidence/2026-10-16-batch16/T-096'
spec=importlib.util.spec_from_file_location('t096_probe',FOLDER/'restart_cleanup.py')
support=importlib.util.module_from_spec(spec); spec.loader.exec_module(support)


def callbacks(source, responses, signal_error=None):
    main=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='main')
    functions=[n for n in main.body if isinstance(n,ast.FunctionDef) and n.name in ['identify','alive','kill']]
    calls=[]
    def run(argv,**kwargs):
        calls.append(argv); return responses.pop(0)
    def legacy(pid): raise subprocess.CalledProcessError(1,['/bin/ps'],output='',stderr='')
    def kill(pid,code):
        calls.append(('signal',pid,code))
        if signal_error: raise signal_error
    namespace=dict(result=dict(process_reads=0),run=run,process_identity=legacy,probe_process=support.probe_process,
        os=SimpleNamespace(kill=kill),signal=signal)
    exec(compile(ast.Module(body=functions,type_ignores=[]),'runner-probe','exec'),namespace)
    return namespace,calls


def response(rc,out='',err=''): return SimpleNamespace(returncode=rc,stdout=out,stderr=err)

report=dict(status='INCOMPLETE',scope='actual probe and runner AST with supplied process boundary; no actual PID observations',checks=[])
try:
    assert support.probe_process(201,run=lambda *a,**kw:response(1)) is None
    assert support.probe_process(201,run=lambda *a,**kw:response(1,' \n','\t')) is None
    for value in [response(1,'','denied'),response(1,'unexpected row',''),response(2),response(-9)]:
        try: support.probe_process(201,run=lambda *a,**kw:value)
        except subprocess.CalledProcessError as error: assert error.returncode==value.returncode
        else: raise AssertionError('Only rc1 with empty stdout and stderr is an exited process')
    for value in [response(0),response(0,'wrong row'),response(0,'202 Sun Oct 18 02:02:04 2026 /fixture/cli\n'),response(0,'201 Sun Oct 18 02:02:04 2026 /fixture/cli\n','warning')]:
        try: support.probe_process(201,run=lambda *a,**kw:value)
        except RuntimeError: pass
        else: raise AssertionError('Malformed successful readback must remain an error')
    good=response(0,'201 Sun Oct 18 02:02:04 2026 /fixture/cli --model x\n')
    owner=dict(pid=201,started='Sun Oct 18 02:02:04 2026',command='/fixture/cli --model x')
    assert support.probe_process(201,run=lambda *a,**kw:good)==owner
    old=subprocess.check_output(['git','show','958ede25f:evidence/2026-10-16-batch16/T-096/run_restart.py'],cwd=ROOT,text=True)
    bad,calls=callbacks(old,[good])
    try: bad['kill'](owner)
    except subprocess.CalledProcessError as error:
        report['known_bad']=dict(revision='958ede25f',rejected=error.returncode==1,error=str(error))
    assert report['known_bad']['rejected'], 'Known-bad second identity lookup must reject a process that just exited'
    current=(FOLDER/'run_restart.py').read_text(encoding='utf-8')
    fixed,calls=callbacks(current,[response(1)])
    fixed['kill'](owner)
    assert len(calls)==1 and fixed['result']['signal_receipts']==[dict(pid=201,signal_sent=False,already_exited=True)]
    fixed,calls=callbacks(current,[good],ProcessLookupError())
    fixed['kill'](owner)
    assert len(calls)==2 and fixed['result']['signal_receipts'][0]['already_exited']
    fixed,calls=callbacks(current,[good],PermissionError('denied'))
    try: fixed['kill'](owner)
    except PermissionError: pass
    else: raise AssertionError('Signal permission error must not be swallowed')
    fixed,calls=callbacks(current,[response(0,'201 Sun Oct 18 03:00:00 2026 /other\n')])
    try: fixed['kill'](owner)
    except RuntimeError: pass
    else: raise AssertionError('Changed owner must reject signal')
    assert len(calls)==1
    report['checks']=['rc1_empty_is_exited','other_rc_and_noise_remain_errors','invalid_identity_refused','valid_identity',
        'one_identity_read','already_exited_no_signal','exit_before_signal_recorded','permission_error_not_swallowed','changed_pid_no_signal']
    report['status']='PASS'
except BaseException as error: report['error']=str(error); report['traceback']=__import__('traceback').format_exc()
with Path(sys.argv[1]).open('x',encoding='utf-8') as output: output.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False)); sys.exit(0 if report['status']=='PASS' else 1)
