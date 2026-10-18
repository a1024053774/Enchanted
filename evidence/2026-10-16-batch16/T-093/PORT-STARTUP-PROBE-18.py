import argparse, ast, contextlib, copy, errno, importlib.util, io, json, re, secrets, subprocess, sys, types
from pathlib import Path

ROOT=Path('/Users/luckye/Documents/Code/a2a-wt-t093')
OUT=Path(__file__).parent
CANDIDATE='e5b8329e4f7d0c8104b7e666c346531357612372'
BASE='7bba61000d8ae5b643135b58111768a403a5d04c'
nonce=secrets.token_hex(7); port=22000+secrets.randbelow(19000)
rows=[]
def record(name, run):
    try:
        detail=run(); rows.append({'case':name,'status':'PASS','detail':detail})
    except Exception as error:
        rows.append({'case':name,'status':'FAIL','error':type(error).__name__,'detail':str(error)})
def load(path):
    spec=importlib.util.spec_from_file_location('independent_session',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
runtime=load(ROOT/'workbench/src/claudeLoginSession.py')
source=(ROOT/'workbench/src/claudeLoginSession.py').read_text()
tree=ast.parse(source)
session={'real_home':'/private/tmp/supplied-home-'+nonce,'private_root':'/private/tmp/supplied-private-'+nonce,
         'credential_home':'/private/tmp/supplied-auth-'+nonce,'forward_port':48137,'upstream_port':443,
         'upstream_address':'203.0.113.57','forwarder_directory':'/private/tmp/supplied-F-'+nonce,
         'metadata_directory':'/private/tmp/supplied-D-'+nonce,
         'manifest':{'state':'/private/tmp/supplied-state-'+nonce,'executable':'/usr/bin/true'}}
def policy_check(function):
    production=function(copy.deepcopy(session))
    test=function({**copy.deepcopy(session),'upstream_port':port})
    assert re.findall(r'\(allow network-outbound \(remote tcp4 "([^"\n]+)"\)\)',production['F'])==['*:443'],'production outbound must be exactly TCP *:443'
    assert re.findall(r'\(allow network-outbound \(remote tcp4 "([^"\n]+)"\)\)',test['F'])==['*:'+str(port)],'test outbound must depend on fresh supplied port'
    assert test['F'].replace('"*:'+str(port)+'"','"*:443"')==production['F'],'only F outbound port may differ'
    assert test['C']==production['C'] and test['D']==production['D'],'C and D permissions may not change'
    assert session['real_home'] in production['F'] and nonce in production['F'],'fresh sentinel paths must appear'
    for fragment in ['(deny network*)','(deny process-fork)','(deny file-write*)','[Ss]ecurity','(deny file-read*']:
        assert fragment in production['F'],'existing F boundary removed: '+fragment
    return {'fresh_port':port,'nonce':nonce,'production_remote':['*:443'],'test_remote':['*:'+str(port)]}
record('shared_profile_fresh_port_nonce',lambda:policy_check(runtime.policies))
def baseline_rejected():
    baseline=subprocess.check_output(['git','-C',str(ROOT),'show',BASE+':workbench/src/claudeLoginSession.py'],text=True)
    node=next(n for n in ast.parse(baseline).body if isinstance(n,ast.FunctionDef) and n.name=='policies')
    namespace=dict(runtime.__dict__);exec(compile(ast.Module(body=[node],type_ignores=[]),'base-policies','exec'),namespace)
    try:policy_check(namespace['policies'])
    except AssertionError as error:
        assert 'fresh supplied port' in str(error);return {'known_bad':BASE,'rejected_by_business_assertion':str(error)}
    raise AssertionError('base hardcoded 443 was accepted')
record('known_bad_hardcoded_port',baseline_rejected)
def invalid_ports():
    for bad in (0,65536,True,'443',None):
        try:runtime.policies({**session,'upstream_port':bad})
        except ValueError as error:assert str(error)=='invalid_upstream_port'
        else:raise AssertionError('bad port accepted: '+repr(bad))
    return {'rejected':[0,65536,True,'443',None]}
record('invalid_profile_ports',invalid_ports)
def production_parser():
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    captured=[]
    class Reached(Exception):pass
    def prepare(*args,**kwargs):captured.append(kwargs);raise Reached()
    namespace=dict(runtime.__dict__);namespace.update(validate_bootstrap=lambda:None,read=lambda p:{'state':'/private/tmp/unused'},prepare=prepare)
    exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-main','exec'),namespace)
    old=sys.argv
    try:
        common=['session.py','--manifest','/private/tmp/manifest-'+nonce,'--repo','/private/tmp/repo-'+nonce,'--forward-port','48137','--upstream-address','203.0.113.57']
        sys.argv=common
        try:namespace['main']()
        except Reached:pass
        assert len(captured)==1 and captured[0]['upstream_port']==443,'production must explicitly pass 443'
        sys.argv=common+['--upstream-port',str(port)]
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            try:namespace['main']()
            except SystemExit as error:assert error.code==2
            else:raise AssertionError('production CLI acquired port override')
        assert 'unrecognized arguments: --upstream-port' in stderr.getvalue()
        assert len(captured)==1,'override must be rejected before preparation'
    finally:sys.argv=old
    return {'actual_main_called':True,'captured_port':443,'override_rejected_before_prepare':True}
record('production_cli_fixed_port',production_parser)
def wrapper():
    wrapper=ROOT/'evidence/2026-10-16-batch16/T-093/T093-OS-16.sh'
    got=[]
    for supplied in (None,port):
        for mode in ('compile','primary','green','none','counts-always-match','verify-six','verify-rehearsal','verify-counts'):
            args=[str(wrapper),mode,'/supplied/repo-'+nonce,CANDIDATE,'/private/tmp/output-'+nonce]
            if mode.startswith('verify-'):args+=['/private/tmp/input-'+nonce]
            env={'PATH':'/usr/bin:/bin','LANG':'C'}
            if supplied is not None:env['T093_TEST_UPSTREAM_PORT']=str(supplied)
            command='exec() { printf "%s\\0" "$@"; }; script=$1; shift; . "$script" "$@"'
            proc=subprocess.run(['/bin/bash','-c',command,'independent-wrapper',*args],capture_output=True,env=env,timeout=5)
            argv=[x.decode() for x in proc.stdout.split(b'\0') if x]
            assert proc.returncode==0 and not proc.stderr
            flag='--test-upstream-port' if mode=='compile' else '--upstream-port'
            assert argv[argv.index(flag)+1]==str(18443 if supplied is None else supplied),'wrapper ignored configured test port'
            assert CANDIDATE in argv and args[4] in argv,'wrapper lost candidate/output binding'
            if mode.startswith('verify-'):assert args[-1] in argv
            got.append({'mode':mode,'port':18443 if supplied is None else supplied,'argv':argv})
    return got
record('actual_bash_wrapper_default_custom',wrapper)

peer_source=(ROOT/'workbench/tests/t093_parallel_chain_peer.py').read_text()
main=next(n for n in ast.parse(peer_source).body if isinstance(n,ast.FunctionDef) and n.name=='main')
index=next(i for i,n in enumerate(main.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='servers' for t in n.targets))
def u_case(fail_at,close_fail=(),mutate=False,receipt_fail=False):
    saved={};created=[];attempted=[];root=Path('/private/tmp/virtual-U-'+nonce)
    class Server:
        def __init__(self,address,handler):
            if fail_at is not None and len(created)==fail_at:raise OSError(errno.EACCES if fail_at==0 else errno.EADDRINUSE,'independent bind failure')
            self.closed=False;self.index=len(created);created.append(self)
        def server_close(self):
            attempted.append(self.index)
            if self.index in close_fail:raise OSError(errno.EIO,'independent close error')
            self.closed=True
    def save(path,value):
        if receipt_fail and path.name=='closed.json':raise OSError(errno.ENOSPC,'independent receipt publication error')
        saved[path.name]=copy.deepcopy(value)
    class StoppedPath(type(Path())):
        def exists(self):return True
    body=copy.deepcopy(main.body[index:])
    if mutate:
        class SkipClose(ast.NodeTransformer):
            def visit_Expr(self,node):
                if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and node.value.func.attr=='server_close':return ast.copy_location(ast.Pass(),node)
                return self.generic_visit(node)
        body=[SkipClose().visit(node) for node in body]
    fn=ast.FunctionDef(name='execute',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=body,decorator_list=[])
    namespace={'root':StoppedPath(root),'runtime':types.SimpleNamespace(save=save),'fixture':{'upstream_port':port,'other_port':port+1},'own':{'pid':58371,'pgrp':58370,'profile':'U'},'session':{'deadline':0},'received':[],'Handler':object,'LocalServer':Server}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'actual-U-listen-finally','exec'),namespace)
    observed=None;result=None
    try:result=namespace['execute']()
    except OSError as error:observed=error.errno
    if receipt_fail:return {'observed_exception':observed,'primary_receipt':saved.get('startup-failed.json'),'closed_receipt':saved.get('closed.json')}
    expected_errno=None if fail_at is None else errno.EACCES if fail_at==0 else errno.EADDRINUSE
    assert observed==expected_errno,'primary bind failure must survive endpoint-close errors'
    closed=saved.get('closed.json');assert closed is not None,'U must publish close receipt including zero listeners'
    assert attempted==list(range(len(created))),'each acquired endpoint must receive close even after another close fails'
    assert closed['listeners_bound']==len(created) and closed['closed_listeners']==sum(s.closed for s in created),'receipt must reconcile actual close count'
    assert closed['all_closed']==all(s.closed for s in created),'closure confirmation must match actual endpoints'
    assert closed['startup_completed']==(fail_at is None) and ('ready.json' in saved)==(fail_at is None)
    assert len(closed['close_errors'])==len(set(close_fail)&set(range(len(created))))
    if fail_at is not None:assert saved['startup-failed.json']['errno']==expected_errno
    else:assert result==(2 if close_fail else 0)
    return {'closed':closed,'close_attempts':attempted,'primary_errno':observed,'return':result}
for name,fail_at,close_fail in [('zero',0,()),('partial',1,()),('normal',None,()),('partial_close_error',1,(0,)),('first_close_error_continue',None,(0,)),('both_close_errors',None,(0,1))]:
    record('actual_U_'+name,lambda fail_at=fail_at,close_fail=close_fail:u_case(fail_at,close_fail))
def reject_skip():
    try:u_case(None,mutate=True)
    except AssertionError as error:return {'mutant':'skip actual endpoint close, keep receipt counters','rejected_by_business_assertion':str(error)}
    raise AssertionError('skip-close mutant accepted')
record('U_skip_close_mutant_rejected',reject_skip)
record('receipt_write_failure_observation',lambda:u_case(1,receipt_fail=True))
report={'candidate':CANDIDATE,'base':BASE,'nonce':nonce,'test_port':port,'scope':'L0/L1 only; no socket, sandbox, model, auth, or kernel PID probes','checks':rows,'status':'PASS' if all(r['status']=='PASS' for r in rows) else 'FAIL'}
with (OUT/'python-result-v2.json').open('x',encoding='utf-8') as output:output.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':report['status'],'checks':len(rows),'test_port':port,'artifact':str(OUT/'python-result-v2.json')}))
raise SystemExit(0 if report['status']=='PASS' else 2)
