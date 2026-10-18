"""Outside entry for the protected no-model product chain. Never escalate."""
import argparse
import base64
import importlib.util
import json
import os
from pathlib import Path
import pwd
import re
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from urllib.parse import quote
import uuid


def load_module(path):
    spec=importlib.util.spec_from_file_location('login_runtime',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def run_git(source, profile, arguments, context, input_text=None, timeout=15):
    started=time.monotonic()
    child=subprocess.Popen(['/usr/bin/sandbox-exec','-p',profile,'/usr/bin/git','--no-optional-locks','-c','core.fsmonitor=false','-c','core.untrackedCache=false','-C',str(source),*arguments],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    context['processes'].append({'pid':child.pid,'profile':'G','role':'read-only Git check'})
    detail={'operation':context['setup_stage'],'pid':child.pid,'profile':'G','timeout_seconds':timeout}
    context['last_git']=detail
    try:
        out,err=child.communicate(input_text.encode() if input_text else None,timeout=timeout)
    except BaseException as error:
        if isinstance(error,subprocess.TimeoutExpired):
            detail.update(stdout=(error.output or b'').decode(errors='replace'),stderr=(error.stderr or b'').decode(errors='replace'))
        if context.get('output'):
            # Publish the original failure before terminating the owned writer.
            write_setup_failure(context,error,cleanup=False)
        # This Popen owns a new process group. Preserve the original failure;
        # termination/reaping problems are secondary cleanup observations.
        if child.poll() is None:
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            except OSError:context['cleanup_failures'].append('setup_Git_terminate_failed')
        try:
            out,err=child.communicate(timeout=5)
            detail.update(stdout=out.decode(errors='replace'),stderr=err.decode(errors='replace'),returncode=child.returncode)
            try:os.killpg(child.pid,0)
            except ProcessLookupError:detail['owned_group_exit_confirmed']=True
            except OSError:context['cleanup_failures'].append('setup_Git_exit_unconfirmed')
            else:context['cleanup_failures'].append('setup_Git_exit_unconfirmed')
        except (OSError,subprocess.TimeoutExpired):
            context['cleanup_failures'].append('setup_Git_reap_unconfirmed')
        raise
    else:
        detail.update(stdout=out.decode(errors='replace'),stderr=err.decode(errors='replace'),returncode=child.returncode)
        return child.returncode,detail['stdout']
    finally:detail['elapsed_seconds']=round(time.monotonic()-started,3)


def write_setup_failure(context, error, cleanup=True):
    error=context.setdefault('primary_error',error)
    variants=set()
    for value in context.get('secrets',[]):
        encoded=base64.b64encode(value.encode()).decode()
        variants.update((value,json.dumps(value)[1:-1],quote(value,safe=''),encoded,encoded.rstrip('='),base64.urlsafe_b64encode(value.encode()).decode(),base64.urlsafe_b64encode(value.encode()).decode().rstrip('=')))
    def text(value):
        value=str(value)
        for secret in sorted(variants,key=len,reverse=True):value=re.sub(re.escape(secret),'<CREDENTIAL>',value,flags=re.IGNORECASE)
        return value
    root=Path(context['fixture_root']) if context.get('fixture_root') else None
    secondary=list(context.get('cleanup_failures',[]))
    frames=[];trace=error.__traceback__
    while trace:
        frames.append({'file':Path(trace.tb_frame.f_code.co_filename).name,'function':trace.tb_frame.f_code.co_name,'line':trace.tb_lineno});trace=trace.tb_next
    original=text(error)
    summary={'type':type(error).__name__,'message':original[:4000],'message_truncated':len(original)>4000,'frames':frames[-8:]}
    if isinstance(error,OSError):summary['errno']=error.errno
    if isinstance(error,subprocess.TimeoutExpired):summary['timeout_seconds']=error.timeout
    git=dict(context.get('last_git',{}))
    for field in ('stdout','stderr'):
        if field in git:
            value=text(git[field]);git[field]=value[:4000];git[field+'_truncated']=len(value)>4000
    report={'status':'INCOMPLETE','phase':'R','setup_stage':context.get('setup_stage','unknown'),'candidate':context.get('candidate'),'mutation':context.get('mutation'),
            'primary_failure':'protected_chain_setup_failed','error_summary':summary,'last_git':git,
            'cleanup_failures':['setup_did_not_reach_C',*secondary],'fixture_root':str(root) if root else None,'fixture_removed':not root or not root.exists(),
            'source_credentials_removed':False,'cleanup_pending':True,'real_model_turns':0,'real_cli_starts':0,'real_upstream_requests':0,'real_auth_reads':0,
            'diagnostic_scan_scope':'generated setup credentials and raw/JSON/URL/base64 variants; no original auth read'}
    if context.get('private_root'):report['isolated_home']=context['private_root']
    if context.get('preparation_cleanup_error'):report['preparation_cleanup_error']=context['preparation_cleanup_error']
    target=Path(context['output']).resolve()
    if Path('/private/tmp') not in target.parents:raise ValueError('setup_report_must_be_outside_HOME')
    def publish():
        encoded=json.dumps(report,ensure_ascii=True)
        for secret in sorted(variants,key=len,reverse=True):encoded=re.sub(re.escape(secret),'<CREDENTIAL>',encoded,flags=re.IGNORECASE)
        if any(re.search(re.escape(secret),encoded,re.IGNORECASE) for secret in variants):raise ValueError('setup_diagnostic_credential_scan_failed')
        temporary=target.with_name(target.name+'.pending-'+uuid.uuid4().hex)
        fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            stream.write(encoded+'\n');stream.flush();os.fsync(stream.fileno())
        try:
            identity=context.get('report_identity')
            if identity:
                current=target.lstat()
                if (current.st_dev,current.st_ino)!=identity:raise ValueError('setup_report_owner_changed')
                os.replace(temporary,target)
            else:os.link(temporary,target)
        finally:
            if temporary.exists():temporary.unlink()
        current=target.lstat();context['report_identity']=(current.st_dev,current.st_ino)
    # No generated credential directory is touched before this durable report.
    publish()
    if cleanup:
        source_removed=True
        if root:
            try:shutil.rmtree(root/'source-home/.claude')
            except FileNotFoundError:pass
            except OSError as secondary_error:
                source_removed=False
                report['cleanup_failures'].append('source_credential_cleanup_failed')
                report['cleanup_error']={'type':type(secondary_error).__name__,'errno':secondary_error.errno,'path':secondary_error.filename}
        report.update(source_credentials_removed=source_removed,cleanup_pending=False)
        publish()
    return report


def snapshot(source, root, mutation):
    if mutation == 'none': return source
    target=root/'code'; work=target/'workbench'; work.mkdir(parents=True)
    shutil.copytree(source/'workbench/src',work/'src',ignore=shutil.ignore_patterns('__pycache__'))
    (work/'tests').mkdir(); (work/'bin').mkdir()
    for name in ('test_t093_login_chain.ts','t093_chain_evidence.ts','t093_fake_claude.c','t093_fake_login_peer.py','t093_parallel_chain_peer.py','t093_forwarder_guard.ts','test_t093_forwarder_host.ts','t093_home_read_boundary.ts','probe_t093_parent_sandbox.py','probe_t093_parallel_profiles.py'):
        shutil.copyfile(source/'workbench/tests'/name,work/'tests'/name)
    shutil.copyfile(source/'workbench/bin/inbox',work/'bin/inbox')
    shutil.copyfile(source/'workbench/package.json',work/'package.json')
    (work/'node_modules').symlink_to((source/'workbench/node_modules').resolve(),target_is_directory=True)
    path=work/'src/claudeLoginFacts.ts'
    before=path.read_text()
    if mutation=='home-references-empty':
        anchor='  if (typeof value === "string") return value.includes(home)'
        assert before.count(anchor)==1
        after=before.replace(anchor,'  return [];\n'+anchor)
    elif mutation=='scanner-zero':
        anchor='export function scanCredentialFiles(directory: string, secrets: readonly string[]) {'
        assert before.count(anchor)==1
        after=before.replace(anchor,anchor+'\n  return { hits: 0, files: 0 };')
    elif mutation=='counts-always-match':
        anchor='counts_match: received === requests.length && sequences'
        assert before.count(anchor)==1
        after=before.replace(anchor,'counts_match: true')
    elif mutation=='drop-first-record':
        path=work/'src/claudeForwarder.ts';before=path.read_text()
        anchor='  private record(value: Record<string, unknown>) {'
        assert before.count(anchor)==1
        after=before.replace(anchor,anchor+'\n    if (value.kind === "request" && value.sequence === 1) return;')
    else:
        path=work/'tests/test_t093_login_chain.ts';before=path.read_text()
        start=before.index('const injectionCases = [');end=before.index(']; // injection cases end',start)+1
        after=before[:start]+'const injectionCases = []'+before[end:]
    path.write_text(after)
    return target


def main(context):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source-revision',required=True)
    parser.add_argument('--mutation',choices=('none','home-references-empty','scanner-zero','counts-always-match','drop-first-record','empty-credential-cases'),default='none')
    parser.add_argument('--rehearsal',choices=('none','primary','green'),default='none')
    args=parser.parse_args();source=Path(__file__).resolve().parents[2]
    context.update(output=str(args.output),candidate=args.source_revision,mutation=args.mutation,setup_stage='bootstrap',processes=[],cleanup_failures=[])
    load_module(source/'workbench/src/claudeLoginSession.py').validate_bootstrap()
    context['setup_stage']='input_validation'
    if len(args.source_revision)!=40 or any(c not in '0123456789abcdef' for c in args.source_revision):parser.error('full source revision required')
    output=args.output.resolve();home=Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
    if os.path.lexists(output) or not output.parent.is_dir() or Path('/private/tmp') not in output.parents or home in output.parents:parser.error('select a new output outside real HOME under /private/tmp')
    read_target=source/'AGENTS.md'
    assert home in read_target.parents and read_target.is_file() and not read_target.is_symlink(),'read_counterexample_requires_public_AGENTS_in_actual_HOME'
    root=Path(tempfile.mkdtemp(prefix='t093-chain-',dir='/private/tmp')).resolve()
    context.update(fixture_root=str(root),setup_stage='fixture_creation')
    for name in ('state','repo','source-home/.claude','U','S','M','synthetic-home'):(root/name).mkdir(parents=True,mode=0o700)
    for name in ('home','claude','tmp','shell','requests','hooks','user-data'):(root/'roles/ideation'/name).mkdir(parents=True,mode=0o700)
    (root/'roles/ideation/role.md').write_text('确定性正常登录链路测试。\n')
    token='synthetic-login-only/"\\'+uuid.uuid4().hex
    refresh='synthetic-refresh-'+uuid.uuid4().hex
    context['secrets']=[token,refresh]
    (root/'source-home/.claude/.credentials.json').write_text(json.dumps({'claudeAiOauth':{'accessToken':token,'refreshToken':refresh,'expiresAt':(time.time()+600)*1000},'unrelated':'must-not-copy'}))
    os.chmod(root/'source-home/.claude/.credentials.json',0o600)
    (root/'source-home/private-sentinel').write_text('protected synthetic source HOME\n')
    # Git checks are also under an OS HOME-write/network guard. No auth value
    # is an argv/env/log value; grep consumes independent variants on stdin.
    g='(version 1)(allow default)(deny file-write* (subpath '+json.dumps(str(home))+'))(deny network*)(deny mach-lookup (global-name-regex #".*[Ss]ecurity.*"))'
    processes=context['processes']
    context['setup_stage']='git_revision'
    code,head=run_git(source,g,['rev-parse','HEAD'],context);assert code==0 and head.strip()==args.source_revision,'frozen_source_revision_must_match'
    context['setup_stage']='git_clean_sources'
    code,_=run_git(source,g,['diff','--quiet','HEAD','--','workbench/src','workbench/tests'],context);assert code==0,'frozen_runtime_sources_must_be_clean'
    variants=[]
    for value in (token,refresh):
        encoded=base64.b64encode(value.encode()).decode()
        variants += [value,json.dumps(value)[1:-1],quote(value,safe=''),encoded,encoded.rstrip('='),base64.urlsafe_b64encode(value.encode()).decode().rstrip('=')]
    context['setup_stage']='git_credential_scan'
    # The retained failure occurred after 15.24 s; the same full-index search
    # took 19.33 s locally. Keep the complete index and one bounded attempt.
    code,_=run_git(source,g,['grep','--cached','--quiet','-F','-f','-','--'],context,input_text='\n'.join(variants)+'\n',timeout=90)
    assert code==1,'synthetic_credentials_must_not_enter_git_index'
    context['setup_stage']='source_snapshot'
    code_source=snapshot(source,root,args.mutation)
    runtime=load_module(code_source/'workbench/src/claudeLoginSession.py')
    context['setup_stage']='choose_ports'
    ports=set()
    while len(ports)<3:ports.add(49152+secrets.randbelow(16000))
    p,other,bind=sorted(ports)
    # The current F contract permits outbound TCP 443 only. Never fall back
    # to another port or reuse a listener owned by another application.
    u=443
    (root/'upstream-port').write_text(str(u));(root/'host-home').write_text(str(home))
    manifest={'schema':1,'root':str(root),'state':str(root/'state'),'task':'t093-chain','preset':'ideation','launch':str(uuid.uuid4()),'session':str(uuid.uuid4()),'thread':str(uuid.uuid4()),'executable':str(root/'fake-claude'),'version':'2.1.302','role_file':str(root/'roles/ideation/role.md'),'code_revision':args.source_revision,'source_snapshot':str(code_source),'authentication':'normal-login','credential_source':'file','upstream_url':f'http://127.0.0.1:{u}','turn_limit':3}
    context['setup_stage']='prepare_session'
    def preparation_failure(error, private, pending, cleanup_error):
        context['private_root']=str(private)
        if cleanup_error:
            context['cleanup_failures'].append('private_preparation_cleanup_failed')
            context['preparation_cleanup_error']={'type':type(cleanup_error).__name__,'errno':cleanup_error.errno,'path':cleanup_error.filename}
        write_setup_failure(context,error,cleanup=False)
    session=runtime.prepare(manifest,root/'repo',p,'127.0.0.1',180,root/'source-home',on_failure=preparation_failure)
    baseline_profile=session['profiles']['D']
    source_barrier='(deny file-read* file-write* (subpath '+json.dumps(str(root/'source-home'))+'))'
    assert session['profiles']['D'].count(source_barrier)==1
    # Only the test D owner may unlink the generated source HOME. It still
    # cannot read its regular file bodies or write the actual account HOME.
    session['profiles']['D']=session['profiles']['D'].replace(source_barrier,'')+'(allow file-write-unlink (subpath '+json.dumps(str(root/'source-home'))+'))(deny file-read-data (require-all (subpath '+json.dumps(str(root/'source-home'))+')(require-not (vnode-type DIRECTORY))))'
    # prepare published this private file once; replace our own preparation
    # data before starting any consumer. No original auth is read again.
    (Path(session['private_root'])/'session.json').write_text(json.dumps(session)+'\n')
    context['private_root']=session['private_root']
    private=Path(session['private_root'])
    context['setup_stage']='build_fixture'
    fixture={'root':str(root),'source':str(code_source),'candidate':args.source_revision,'output':str(output),'mutation':args.mutation,'rehearsal':args.rehearsal,'upstream_port':u,'other_port':other,'bind_probe_port':bind,'git_index_hits':0,'G_processes':processes,'G_profile':g,'read_boundary_target':str(read_target),
             'inbox_sentinel':'t093-independent-'+uuid.uuid4().hex,'prompt':'无模型链路哨兵 '+uuid.uuid4().hex+'；请读取本角色收件箱并在 Stop 转交。'}
    # External oracle: the native-CLI spec dispatch adds the managed marker.
    # This fresh database's first dispatch is #1. Do not copy production output.
    fixture['expected_request_body']={'messages':[{'role':'user','content':'⟦主控 #1⟧\n'+fixture['prompt']}]}
    peer=code_source/'workbench/tests/t093_parallel_chain_peer.py'
    command=lambda role:['/usr/bin/python3','-I','-S','-B',str(peer),'--session',str(private/'session.json'),'--role',role]
    q=lambda value:json.dumps(str(value))
    common=session['profiles']['F']
    # U has two explicit test listeners and no outbound. It has its own record
    # directory. No CLI process can reach either listener directly.
    profiles={'D_baseline':baseline_profile,'U':runtime.policies(session)['F'].split('(allow network-bind')[0].replace(q(session['forwarder_directory']),q(root/'U'))+'(allow network-bind network-inbound (local tcp4 "localhost:'+str(u)+'"))(allow network-bind network-inbound (local tcp4 "localhost:'+str(other)+'"))',
              'S':session['profiles']['C']+'(deny file-write* (subpath '+q(root/'synthetic-home')+'))','M':session['profiles']['C']}
    fixture['test_profiles']=profiles
    runtime.save(private/'fixture.json',fixture)
    print(json.dumps({'stage':'prepared_services','root':str(root),'audit':session['audit_directory'],'candidate':args.source_revision}),flush=True)
    context['setup_stage']='start_F_D'
    runtime.start_services(session,command('F'),command('D'))
    extra={}
    for role in ('U','S','M'):
        context['setup_stage']='start_'+role
        own=dict(session);own['profiles']={**session['profiles'],role:profiles[role]}
        extra[role]=runtime.detach(own,role,command(role))
    runtime.save(private/'test-services.json',extra)
    context['setup_stage']='enter_C'
    runtime.enter_cli(session,[runtime.NODE,str(code_source/'workbench/tests/test_t093_login_chain.ts')],{'A2A_OPERATOR_CREDENTIAL':str(root/'operator.json')})

if __name__=='__main__':
    context={'setup_stage':'arguments'}
    try:main(context)
    except Exception as error:
        try:
            result=write_setup_failure(context,error)
            print(json.dumps({'status':result['status'],'failure':result['primary_failure'],'setup_stage':result['setup_stage'],'error_type':result['error_summary']['type']}))
        except (KeyError,ValueError,OSError):sys.stderr.write('setup_failure_report_unavailable\n')
        raise SystemExit(2)
