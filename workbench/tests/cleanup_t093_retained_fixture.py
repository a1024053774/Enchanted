"""Outside-only removal of one recognized, inactive T-093 fixture. No archive."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import pwd
import re
import signal
import shutil
import stat
import subprocess
import sys

SOURCE=Path(__file__).resolve().parents[1]/'src/claudeLoginSession.py'
spec=importlib.util.spec_from_file_location('cleanup_runtime',SOURCE)
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)

def mark(context,operation,path=None,**values):
    context.update(operation=operation,path=str(path) if path is not None else None)
    for field in ('pid','pgrp','metadata','returncode','stderr'):context.pop(field,None)
    context.update(values)

def error_details(error,context):
    value={key:context[key] for key in ('operation','path','pid','pgrp','metadata','returncode','stderr','timeout_seconds','control_cleanup','observer_cleanup') if key in context}
    value.update(error_type=type(error).__name__,errno=getattr(error,'errno',None))
    if isinstance(error,OSError) and error.filename is not None:
        if context.get('operation','').startswith('rmtree_'):
            value['os_filename']=str(error.filename)
        else:value['path']=str(error.filename)
    return value

def legacy_ps_diagnostic():
    context={}
    try:
        path=Path('/bin/ps');mark(context,'legacy_observer_stat',path);info=path.stat()
        mark(context,'legacy_observer_exec',path,metadata={'mode':oct(stat.S_IMODE(info.st_mode)),'setuid':bool(info.st_mode&stat.S_ISUID),'uid':info.st_uid})
        child=subprocess.Popen([str(path),'-ww','-axo','pid=,pgid=,stat=,command='],stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        try:out,_=child.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill();child.communicate();raise
        return {'operation':context['operation'],'path':str(path),'metadata':context['metadata'],'pid':child.pid,'pgrp':child.pid,'exit':child.returncode,'stdout_bytes':len(out),'raw_output_saved':False}
    except Exception as error:return error_details(error,context)

def require_cleanup_scope(root):
    manifest=SOURCE.parents[2]/'evidence/2026-10-16-batch16/T-093/retained-cleanup-scope-05.json'
    value=json.loads(manifest.read_text())
    if value.get('source_repo')!=str(SOURCE.parents[2].resolve()) or str(root) not in value.get('roots',[]):
        raise ValueError('fixture_not_in_reviewed_cleanup_scope')

class ActiveSetupProcesses(ValueError):
    def __init__(self,proof):
        super().__init__('active_setup_processes_prevent_fixture_deletion')
        self.proof=proof

def setup_quiescence(root,context=None):
    context={} if context is None else context
    source=str(SOURCE.parents[2].resolve())
    entry=str(SOURCE.parents[1]/'tests/run_t093_login_chain.py')
    binary=Path('/usr/bin/pgrep')
    mark(context,'observer_stat',binary)
    info=binary.stat()
    context['metadata']={'mode':oct(stat.S_IMODE(info.st_mode)),'setuid':bool(info.st_mode&stat.S_ISUID),'setgid':bool(info.st_mode&stat.S_ISGID),'uid':info.st_uid}
    observer=dict(context['metadata'])
    if info.st_mode & (stat.S_ISUID|stat.S_ISGID):raise ValueError('privileged_process_observer_refused')
    literal=lambda value:''.join('\\'+char if char in '.^$[]()|*+?{}\\' else char for char in value)
    patterns={'R':r'(^|[[:space:]/])run_t093_login_chain[.]py([[:space:]]|$)',
              'G':r'(^|[[:space:]/])git([[:space:]]|$).*[-]C[[:space:]]+'+literal(source)+r'([[:space:]]|$)'}
    inspectors=[]
    def query(role):
        mark(context,'process_inventory_exec',binary)
        child=subprocess.Popen([str(binary),'-a','-f','-U',str(os.getuid()),patterns[role]],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',start_new_session=True)
        context.update(pid=child.pid,pgrp=child.pid)
        try:out,err=child.communicate(timeout=5)
        except subprocess.TimeoutExpired as error:
            try:child.kill();child.communicate(timeout=5)
            except Exception as cleanup:context['observer_cleanup']=error_details(cleanup,{'operation':'observer_cleanup','path':str(binary),'pid':child.pid})
            context['timeout_seconds']=5
            raise ValueError('setup_process_inventory_timeout') from error
        context.update(returncode=child.returncode,stderr=err[:1000])
        if child.returncode not in (0,1):raise ValueError('setup_process_inventory_unavailable')
        values=out.split()
        if any(not value.isdigit() or int(value)<=1 for value in values):raise ValueError('setup_process_inventory_incomplete')
        result={int(value) for value in values}
        if (child.returncode==0)!=bool(result):raise ValueError('setup_process_inventory_incomplete')
        inspectors.append({'role':role,'pid':child.pid,'pgrp':child.pid,'profile':'X inherited','exit':child.returncode,'matches':len(result)})
        return result
    # A harmless Python child carries both argument markers. Matching it is
    # required before an empty query may be accepted as stopped R/G evidence.
    mark(context,'observer_control_exec','/usr/bin/python3')
    def control_deadline():
        signal.signal(signal.SIGALRM,signal.SIG_DFL);signal.alarm(20)
    control=subprocess.Popen(['/usr/bin/python3','-I','-S','-B','-c','import time; time.sleep(20)',entry,'/usr/bin/git','-C',source],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True,preexec_fn=control_deadline)
    primary=None
    try:
        observed={role:query(role) for role in ('R','G')}
        if any(control.pid not in values for values in observed.values()):raise ValueError('setup_process_positive_control_not_seen')
    except BaseException as error:primary=error;raise
    finally:
        try:
            if control.poll() is None:control.kill()
            control.communicate(timeout=5)
            try:os.killpg(control.pid,0)
            except ProcessLookupError:pass
            else:raise ValueError('observer_control_exit_unconfirmed')
        except Exception as error:
            context['control_cleanup']=error_details(error,{'operation':'observer_control_cleanup','path':'/usr/bin/python3','pid':control.pid})
            if primary is None:
                mark(context,'observer_control_cleanup','/usr/bin/python3',pid=control.pid)
                raise
    remaining={role:query(role) for role in ('R','G')}
    matches=[]
    for role in ('R','G'):
        for pid in sorted((observed[role]-{control.pid})|remaining[role]):
            mark(context,'process_group_probe',pid=pid)
            try:group=os.getpgid(pid)
            except ProcessLookupError:group=None
            matches.append({'role':role,'pid':pid,'pgrp':group,'state':'observed_present'})
    proof={'root':str(Path(root).resolve()),'source':source,'scope':'current UID T093 R entries and worktree G commands; pgrep returns PID only','complete':True,
           'observer':{'path':str(binary),**observer},'inspectors':inspectors,'positive_control':{'pid':control.pid,'pgrp':control.pid,'profile':'X inherited','R_seen':True,'G_seen':True,'exit_confirmed':True},'matching_processes':matches,'permission_changes':[]}
    if matches:raise ActiveSetupProcesses(proof)
    return proof

def inspect(root,context=None):
    context={} if context is None else context
    root=Path(root)
    mark(context,'root_metadata',root)
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
    def walk_error(error):mark(context,'scandir',error.filename);raise error
    for base,dirs,names in os.walk(root,followlinks=False,onerror=walk_error):
        for name in dirs+names:
            path=Path(base)/name;mark(context,'lstat',path)
            value=path.lstat();relative=str(path.relative_to(root))
            context['metadata']={'mode':oct(stat.S_IMODE(value.st_mode)),'uid':value.st_uid,'flags':getattr(value,'st_flags',0),'kind':'directory' if stat.S_ISDIR(value.st_mode) else 'regular' if stat.S_ISREG(value.st_mode) else 'symlink' if stat.S_ISLNK(value.st_mode) else 'socket' if stat.S_ISSOCK(value.st_mode) else 'fifo' if stat.S_ISFIFO(value.st_mode) else 'other'}
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
        mark(context,'read_cleanup_receipt',root/removed[0]);receipt=json.loads((root/removed[0]).read_text())
        if receipt.get('isolated_home_removed') is not True or receipt.get('cleanup_failures')!=[]:raise ValueError('private_HOME_cleanup_not_confirmed')
        for name in metadata_files:
            mark(context,'read_process_metadata',root/name)
            for line in (root/name).read_text().splitlines():
                value=json.loads(line)
                for key,probe in (('pid',os.kill),('pgrp',os.killpg)):
                    identity=value.get(key)
                    if identity is None:continue
                    if not isinstance(identity,int) or identity<=1:raise ValueError('invalid_recorded_process_identity')
                    mark(context,'process_signal_zero',pid=identity,pgrp=identity if key=='pgrp' else None)
                    try:probe(identity,0)
                    except ProcessLookupError:pass
                    else:raise ValueError('recorded_process_or_group_still_exists')
    return items

def remove(root,inspect_only=False,context=None):
    context={} if context is None else context
    items=inspect(root,context)
    proof=setup_quiescence(root,context)
    files=[value for value in items if not value['directory']]
    receipt={'status':'INCOMPLETE','root':str(root),'scope':'one recognized inactive fixture; only process/cleanup metadata read, no credential body; no archive',
             'files_before':len(files),'bytes_before':sum(value['bytes'] for value in files),
             'credential_file_present':any(value['relative']=='source-home/.claude/.credentials.json' for value in files),'setup_quiescence':proof,'action':'inspect_only' if inspect_only else 'delete','deletion_attempted':not inspect_only,'permission_changes':[]}
    if inspect_only:
        receipt.update(status='PASS',root_removed=False)
        return receipt
    mark(context,'rmtree',root)
    def deletion_error(function,path,details):
        mark(context,'rmtree_'+function.__name__,path)
        raise details[1]
    try:shutil.rmtree(root,onerror=deletion_error)
    except OSError as error:receipt.update(error_details(error,context))
    try:Path(root).lstat();receipt['root_removed']=False
    except FileNotFoundError:receipt['root_removed']=True
    except OSError as error:
        details=error_details(error,{'operation':'root_absence_check','path':str(root)})
        if 'error_type' in receipt:receipt['absence_check_error']=details
        else:receipt.update(details)
        receipt['root_removed']=False
    if receipt['root_removed'] and 'error_type' not in receipt:receipt['status']='PASS'
    return receipt

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--protected',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--inspect-only',action='store_true')
    args=parser.parse_args();runtime.require_safe_python();runtime.validate_bootstrap()
    if args.output.parent!=Path('/private/tmp') or args.output.resolve()!=args.output or os.path.lexists(args.output):parser.error('new canonical output directly under /private/tmp required')
    require_cleanup_scope(args.root)
    if not args.protected:
        home=Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
        # All observer/control children inherit X; F/U/D fork bans are unchanged.
        policy='(version 1)(allow default)(deny file-write* (subpath '+json.dumps(str(home))+'))(deny network*)(deny mach-lookup (global-name-regex #".*[Ss]ecurity.*"))'
        os.chdir('/private/tmp')
        os.execve('/usr/bin/sandbox-exec',['sandbox-exec','-p',policy,'/usr/bin/python3','-I','-S','-B',str(Path(__file__).resolve()),'--protected','--root',str(args.root),'--output',str(args.output),*(['--inspect-only'] if args.inspect_only else [])],{'PATH':'/usr/bin:/bin','LANG':'C'})
    context={}
    legacy=legacy_ps_diagnostic() if args.inspect_only else None
    try:receipt=remove(args.root,args.inspect_only,context)
    except Exception as error:
        reason=str(error) if isinstance(error,ValueError) and re.fullmatch(r'[a-z_]{1,120}',str(error)) else 'retained_fixture_inspection_failed'
        receipt={'status':'INCOMPLETE','root':str(args.root),'root_removed':False,'reason':reason,'error_type':type(error).__name__}
        receipt.update(error_details(error,context),action='inspect_only' if args.inspect_only else 'delete',deletion_attempted=False,permission_changes=[])
        if isinstance(error,ActiveSetupProcesses):receipt['setup_quiescence']=error.proof
    if legacy is not None:receipt['legacy_ps_diagnostic']=legacy
    runtime.save(args.output,receipt)
    print(json.dumps({'status':receipt['status'],'root_removed':receipt['root_removed']}))
    return 0 if receipt['status']=='PASS' else 2

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception:
        sys.stderr.write('retained_fixture_cleanup_refused\n')
        raise SystemExit(2)
