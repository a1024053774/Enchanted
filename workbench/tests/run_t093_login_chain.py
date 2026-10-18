"""Outside entry for the protected no-model product chain. Never escalate."""
import argparse
import base64
import importlib.util
import json
import os
from pathlib import Path
import pwd
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from urllib.parse import quote
import uuid


def load_module(path):
    spec=importlib.util.spec_from_file_location('login_runtime',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def snapshot(source, root, mutation):
    if mutation == 'none': return source
    target=root/'code'; work=target/'workbench'; work.mkdir(parents=True)
    shutil.copytree(source/'workbench/src',work/'src',ignore=shutil.ignore_patterns('__pycache__'))
    (work/'tests').mkdir(); (work/'bin').mkdir()
    for name in ('test_t093_login_chain.ts','t093_fake_claude.c','t093_fake_login_peer.py','t093_parallel_chain_peer.py','t093_forwarder_guard.ts','t093_home_read_boundary.ts','probe_t093_parent_sandbox.py','probe_t093_parallel_profiles.py'):
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


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source-revision',required=True)
    parser.add_argument('--mutation',choices=('none','home-references-empty','scanner-zero','counts-always-match','drop-first-record','empty-credential-cases'),default='none')
    args=parser.parse_args();source=Path(__file__).resolve().parents[2]
    load_module(source/'workbench/src/claudeLoginSession.py').validate_bootstrap()
    if len(args.source_revision)!=40 or any(c not in '0123456789abcdef' for c in args.source_revision):parser.error('full source revision required')
    output=args.output.resolve();home=Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
    if os.path.lexists(output) or not output.parent.is_dir() or Path('/private/tmp') not in output.parents or home in output.parents:parser.error('select a new output outside real HOME under /private/tmp')
    read_target=source/'AGENTS.md'
    assert home in read_target.parents and read_target.is_file() and not read_target.is_symlink(),'read_counterexample_requires_public_AGENTS_in_actual_HOME'
    root=Path(tempfile.mkdtemp(prefix='t093-chain-',dir='/private/tmp')).resolve()
    for name in ('state','repo','source-home/.claude','U','S','M','synthetic-home'):(root/name).mkdir(parents=True,mode=0o700)
    for name in ('home','claude','tmp','shell','requests','hooks','user-data'):(root/'roles/ideation'/name).mkdir(parents=True,mode=0o700)
    (root/'roles/ideation/role.md').write_text('确定性正常登录链路测试。\n')
    token='synthetic-login-only/"\\'+uuid.uuid4().hex
    refresh='synthetic-refresh-'+uuid.uuid4().hex
    (root/'source-home/.claude/.credentials.json').write_text(json.dumps({'claudeAiOauth':{'accessToken':token,'refreshToken':refresh,'expiresAt':(time.time()+600)*1000},'unrelated':'must-not-copy'}))
    os.chmod(root/'source-home/.claude/.credentials.json',0o600)
    (root/'source-home/private-sentinel').write_text('protected synthetic source HOME\n')
    # Git checks are also under an OS HOME-write/network guard. No auth value
    # is an argv/env/log value; grep consumes independent variants on stdin.
    g='(version 1)(allow default)(deny file-write* (subpath '+json.dumps(str(home))+'))(deny network*)(deny mach-lookup (global-name-regex #".*[Ss]ecurity.*"))'
    processes=[]
    def git(arguments,input_text=None):
        child=subprocess.Popen(['/usr/bin/sandbox-exec','-p',g,'/usr/bin/git','--no-optional-locks','-c','core.fsmonitor=false','-c','core.untrackedCache=false','-C',str(source),*arguments],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        processes.append({'pid':child.pid,'profile':'G','role':'read-only Git check'})
        out,err=child.communicate(input_text.encode() if input_text else None,timeout=15)
        return child.returncode,out.decode()
    code,head=git(['rev-parse','HEAD']);assert code==0 and head.strip()==args.source_revision,'frozen_source_revision_must_match'
    code,_=git(['diff','--quiet','HEAD','--','workbench/src','workbench/tests']);assert code==0,'frozen_runtime_sources_must_be_clean'
    variants=[]
    for value in (token,refresh):
        encoded=base64.b64encode(value.encode()).decode()
        variants += [value,json.dumps(value)[1:-1],quote(value,safe=''),encoded,encoded.rstrip('='),base64.urlsafe_b64encode(value.encode()).decode().rstrip('=')]
    code,_=git(['grep','--cached','--quiet','-F','-f','-','--'],'\n'.join(variants)+'\n')
    assert code==1,'synthetic_credentials_must_not_enter_git_index'
    code_source=snapshot(source,root,args.mutation)
    runtime=load_module(code_source/'workbench/src/claudeLoginSession.py')
    ports=set()
    while len(ports)<4:ports.add(49152+secrets.randbelow(16000))
    p,u,other,bind=sorted(ports)
    (root/'upstream-port').write_text(str(u));(root/'host-home').write_text(str(home))
    manifest={'schema':1,'root':str(root),'state':str(root/'state'),'task':'t093-chain','preset':'ideation','launch':str(uuid.uuid4()),'session':str(uuid.uuid4()),'thread':str(uuid.uuid4()),'executable':str(root/'fake-claude'),'version':'2.1.302','role_file':str(root/'roles/ideation/role.md'),'code_revision':args.source_revision,'source_snapshot':str(code_source),'authentication':'normal-login','credential_source':'file','upstream_url':f'http://127.0.0.1:{u}','turn_limit':3}
    session=runtime.prepare(manifest,root/'repo',p,'127.0.0.1',180,root/'source-home')
    private=Path(session['private_root'])
    fixture={'root':str(root),'source':str(code_source),'candidate':args.source_revision,'output':str(output),'mutation':args.mutation,'upstream_port':u,'other_port':other,'bind_probe_port':bind,'git_index_hits':0,'G_processes':processes,'G_profile':g,'read_boundary_target':str(read_target),
             'inbox_sentinel':'t093-independent-'+uuid.uuid4().hex,'prompt':'无模型链路哨兵 '+uuid.uuid4().hex+'；请读取本角色收件箱并在 Stop 转交。'}
    peer=code_source/'workbench/tests/t093_parallel_chain_peer.py'
    command=lambda role:['/usr/bin/python3','-I','-S','-B',str(peer),'--session',str(private/'session.json'),'--role',role]
    q=lambda value:json.dumps(str(value))
    common=session['profiles']['F']
    # U has two explicit test listeners and no outbound. It has its own record
    # directory. No CLI process can reach either listener directly.
    profiles={'U':runtime.policies(session)['F'].split('(allow network-bind')[0].replace(q(session['forwarder_directory']),q(root/'U'))+'(allow network-bind network-inbound (local tcp4 "localhost:'+str(u)+'"))(allow network-bind network-inbound (local tcp4 "localhost:'+str(other)+'"))',
              'S':session['profiles']['C']+'(deny file-write* (subpath '+q(root/'synthetic-home')+'))','M':session['profiles']['C']}
    fixture['test_profiles']=profiles
    runtime.save(private/'fixture.json',fixture)
    print(json.dumps({'stage':'prepared_services','root':str(root),'audit':session['audit_directory'],'candidate':args.source_revision}),flush=True)
    runtime.start_services(session,command('F'),command('D'))
    extra={}
    for role in ('U','S','M'):
        own=dict(session);own['profiles']={**session['profiles'],role:profiles[role]}
        extra[role]=runtime.detach(own,role,command(role))
    runtime.save(private/'test-services.json',extra)
    runtime.enter_cli(session,[runtime.NODE,str(code_source/'workbench/tests/test_t093_login_chain.ts')],{'A2A_OPERATOR_CREDENTIAL':str(root/'operator.json')})

if __name__=='__main__':
    try:main()
    except Exception:
        # No input data or child stderr is exposed, including on early setup.
        print(json.dumps({'status':'INCOMPLETE','failure':'protected_chain_setup_failed'}))
        try:
            target=Path(sys.argv[sys.argv.index('--output')+1]).resolve()
            if Path('/private/tmp') in target.parents and not target.exists():
                with target.open('x') as stream:json.dump({'status':'INCOMPLETE','phase':'R','primary_failure':'protected_chain_setup_failed','cleanup_failures':['setup_did_not_reach_C'],'fixture_removed':False,'real_model_turns':0,'real_cli_starts':0,'real_upstream_requests':0},stream);stream.write('\n')
        except (ValueError,IndexError,OSError):sys.stderr.write('setup_failure_report_unavailable\n')
        raise SystemExit(2)
