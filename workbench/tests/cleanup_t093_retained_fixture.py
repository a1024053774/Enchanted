"""Outside-only removal of one recognized, inactive T-093 fixture. No archive."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import stat
import sys

SOURCE=Path(__file__).resolve().parents[1]/'src/claudeLoginSession.py'
spec=importlib.util.spec_from_file_location('cleanup_runtime',SOURCE)
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)

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
    files=[value for value in items if not value['directory']]
    receipt={'status':'INCOMPLETE','root':str(root),'scope':'one recognized inactive fixture; only process/cleanup metadata read, no credential body; no archive',
             'files_before':len(files),'bytes_before':sum(value['bytes'] for value in files),
             'credential_file_present':any(value['relative']=='source-home/.claude/.credentials.json' for value in files)}
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
    if not args.protected:
        home=Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
        policy='(version 1)(allow default)(deny file-write* (subpath '+json.dumps(str(home))+'))(deny network*)(deny mach-lookup (global-name-regex #".*[Ss]ecurity.*"))(deny process-fork)'
        os.chdir('/private/tmp')
        os.execve('/usr/bin/sandbox-exec',['sandbox-exec','-p',policy,'/usr/bin/python3','-I','-S','-B',str(Path(__file__).resolve()),'--protected','--root',str(args.root),'--output',str(args.output)],{'PATH':'/usr/bin:/bin','LANG':'C'})
    try:receipt=remove(args.root)
    except Exception as error:
        reason=str(error) if isinstance(error,ValueError) and re.fullmatch(r'[a-z_]{1,120}',str(error)) else 'retained_fixture_inspection_failed'
        receipt={'status':'INCOMPLETE','root':str(args.root),'root_removed':False,'reason':reason,'error_type':type(error).__name__}
    runtime.save(args.output,receipt)
    print(json.dumps({'status':receipt['status'],'root_removed':receipt['root_removed']}))
    return 0 if receipt['status']=='PASS' else 2

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception:
        sys.stderr.write('retained_fixture_cleanup_refused\n')
        raise SystemExit(2)
