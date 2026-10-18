"""Outside-only removal of one recognized, inactive T-093 fixture. No archive."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import pwd
import re
import shlex
import shutil
import stat
import subprocess
import sys

SOURCE=Path(__file__).resolve().parents[1]/'src/claudeLoginSession.py'
spec=importlib.util.spec_from_file_location('cleanup_runtime',SOURCE)
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)

def require_cleanup_scope(root):
    manifest=SOURCE.parents[2]/'evidence/2026-10-16-batch16/T-093/retained-cleanup-scope-05.json'
    value=json.loads(manifest.read_text())
    if value.get('source_repo')!=str(SOURCE.parents[2].resolve()) or str(root) not in value.get('roots',[]):
        raise ValueError('fixture_not_in_reviewed_cleanup_scope')

class ActiveSetupProcesses(ValueError):
    def __init__(self,proof):
        super().__init__('active_setup_processes_prevent_fixture_deletion')
        self.proof=proof

def setup_quiescence(root):
    source=str(SOURCE.parents[2].resolve())
    entry=str(SOURCE.parents[1]/'tests/run_t093_login_chain.py')
    child=subprocess.Popen(['/bin/ps','-ww','-axo','pid=,pgid=,stat=,command='],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',start_new_session=True)
    try:out,_=child.communicate(timeout=5)
    except subprocess.TimeoutExpired as error:
        child.kill();child.communicate()
        raise ValueError('setup_process_inventory_timeout') from error
    if child.returncode:raise ValueError('setup_process_inventory_unavailable')
    own_seen=False;matches=[]
    # Raw process arguments stay in memory. Only scoped R/G PID/group/state
    # observations enter the receipt; no other arguments are printed/saved.
    for line in out.splitlines():
        fields=line.split(None,3)
        if len(fields)!=4 or not fields[0].isdigit() or not fields[1].isdigit():continue
        pid,group,state,command=int(fields[0]),int(fields[1]),fields[2],fields[3]
        if pid==os.getpid():own_seen=True
        if source not in command and Path(entry).name not in command:continue
        try:arguments=shlex.split(command)
        except ValueError:raise ValueError('task_process_arguments_unparseable') from None
        role='R' if any(Path(value).name==Path(entry).name for value in arguments) else 'G' if any(value in ('git','/usr/bin/git') for value in arguments) and any(arguments[i]=='-C' and arguments[i+1]==source for i in range(len(arguments)-1)) else None
        if role:matches.append({'role':role,'pid':pid,'pgrp':group,'state':state})
    if not own_seen:raise ValueError('setup_process_inventory_incomplete')
    proof={'root':str(Path(root).resolve()),'source':source,'scope':'all T093 R entries and this worktree G commands; no raw argv retained','complete':True,
           'inspector':{'pid':child.pid,'pgrp':child.pid,'profile':'X inherited','exit':child.returncode},'matching_processes':matches}
    if matches:raise ActiveSetupProcesses(proof)
    return proof

def inspect(root):
    root=Path(root)
    if root.parent!=Path('/private/tmp') or not root.name.startswith('t093-chain-') or root.resolve()!=root or root.is_symlink():
        raise ValueError('exact_canonical_T093_fixture_required')
    if not root.is_dir() or root.stat().st_uid!=os.getuid():raise ValueError('owned_fixture_directory_required')
    directories={'U','S','M','state','repo','synthetic-home','source-home','roles','roles/ideation'}
    directories.update('roles/ideation/'+name for name in ('home','claude','tmp','shell','requests','hooks','user-data'))
    files={'roles/ideation/role.md','source-home/private-sentinel'}
    optional={'source-home/.claude','source-home/.claude/.credentials.json','upstream-port','host-home','U/guards.json','U/ready.json','S/result.json','M/result.json'}
    audit_pattern=r'state/login-audits/[0-9a-f-]{36}'
    extra_directory=lambda name:bool(name=='state/login-audits' or re.fullmatch(audit_pattern+r'(?:/(?:forwarder|metadata|C-tmp))?',name))
    extra_file=lambda name:bool(re.fullmatch(audit_pattern+r'/(?:C-processes\.jsonl|forwarder/python-guards\.json|metadata/(?:guards|ready|removed)\.json)',name))
    code_directory=lambda name:name in ('code','code/workbench','code/workbench/src','code/workbench/tests','code/workbench/bin') or name.startswith('code/workbench/src/')
    code_file=lambda name:name.startswith(('code/workbench/src/','code/workbench/tests/')) or name in ('code/workbench/package.json','code/workbench/bin/inbox')
    seen=set();items=[]
    for base,dirs,names in os.walk(root,followlinks=False):
        for name in dirs+names:
            path=Path(base)/name;value=path.lstat();relative=str(path.relative_to(root))
            if value.st_uid!=os.getuid():raise ValueError('fixture_link_or_foreign_owner_refused')
            if stat.S_ISLNK(value.st_mode):
                if relative!='code/workbench/node_modules' or path.resolve()!=(SOURCE.parents[1]/'node_modules').resolve():raise ValueError('unexpected_fixture_link_refused')
                items.append({'relative':relative,'directory':False,'bytes':value.st_size,'symlink':True});continue
            if relative not in directories|files|optional and not extra_directory(relative) and not extra_file(relative) and not code_directory(relative) and not code_file(relative):raise ValueError('unrecognized_fixture_entries_refused')
            if relative in directories or relative=='source-home/.claude' or extra_directory(relative) or code_directory(relative) and stat.S_ISDIR(value.st_mode):
                if not stat.S_ISDIR(value.st_mode):raise ValueError('fixture_entry_type_mismatch')
            elif not stat.S_ISREG(value.st_mode):raise ValueError('fixture_entry_type_mismatch')
            seen.add(relative);items.append({'relative':relative,'directory':stat.S_ISDIR(value.st_mode),'bytes':value.st_size})
    if not (directories|files)<=seen:raise ValueError('fixture_initial_structure_incomplete')
    metadata_files=[value['relative'] for value in items if not value['directory'] and value['relative'].endswith(('.json','.jsonl')) and value['relative'].startswith(('U/','S/','M/','state/'))]
    if metadata_files:
        removed=[name for name in metadata_files if name.endswith('/metadata/removed.json')]
        if len(removed)!=1:raise ValueError('post_service_fixture_without_cleanup_receipt')
        receipt=json.loads((root/removed[0]).read_text())
        if receipt.get('isolated_home_removed') is not True or receipt.get('cleanup_failures')!=[]:raise ValueError('private_HOME_cleanup_not_confirmed')
        for name in metadata_files:
            for line in (root/name).read_text().splitlines():
                value=json.loads(line)
                for key,probe in (('pid',os.kill),('pgrp',os.killpg)):
                    identity=value.get(key)
                    if identity is None:continue
                    if not isinstance(identity,int) or identity<=1:raise ValueError('invalid_recorded_process_identity')
                    try:probe(identity,0)
                    except ProcessLookupError:pass
                    else:raise ValueError('recorded_process_or_group_still_exists')
    return items

def remove(root):
    items=inspect(root)
    proof=setup_quiescence(root)
    files=[value for value in items if not value['directory']]
    receipt={'status':'INCOMPLETE','root':str(root),'scope':'one recognized inactive fixture; only process/cleanup metadata read, no credential body; no archive',
             'files_before':len(files),'bytes_before':sum(value['bytes'] for value in files),
             'credential_file_present':any(value['relative']=='source-home/.claude/.credentials.json' for value in files),'setup_quiescence':proof}
    try:shutil.rmtree(root)
    except OSError as error:receipt.update(error_type=type(error).__name__,errno=error.errno)
    receipt['root_removed']=not os.path.lexists(root)
    if receipt['root_removed']:receipt['status']='PASS'
    return receipt

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--protected',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args();runtime.require_safe_python();runtime.validate_bootstrap()
    if args.output.parent!=Path('/private/tmp') or args.output.resolve()!=args.output or os.path.lexists(args.output):parser.error('new canonical output directly under /private/tmp required')
    require_cleanup_scope(args.root)
    if not args.protected:
        home=Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
        # The sole ps child inherits X; product F/U/D fork bans are unchanged.
        policy='(version 1)(allow default)(deny file-write* (subpath '+json.dumps(str(home))+'))(deny network*)(deny mach-lookup (global-name-regex #".*[Ss]ecurity.*"))'
        os.chdir('/private/tmp')
        os.execve('/usr/bin/sandbox-exec',['sandbox-exec','-p',policy,'/usr/bin/python3','-I','-S','-B',str(Path(__file__).resolve()),'--protected','--root',str(args.root),'--output',str(args.output)],{'PATH':'/usr/bin:/bin','LANG':'C'})
    try:receipt=remove(args.root)
    except Exception as error:
        reason=str(error) if isinstance(error,ValueError) and re.fullmatch(r'[a-z_]{1,120}',str(error)) else 'retained_fixture_inspection_failed'
        receipt={'status':'INCOMPLETE','root':str(args.root),'root_removed':False,'reason':reason,'error_type':type(error).__name__}
        if isinstance(error,ActiveSetupProcesses):receipt['setup_quiescence']=error.proof
    runtime.save(args.output,receipt)
    print(json.dumps({'status':receipt['status'],'root_removed':receipt['root_removed']}))
    return 0 if receipt['status']=='PASS' else 2

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception:
        sys.stderr.write('retained_fixture_cleanup_refused\n')
        raise SystemExit(2)
