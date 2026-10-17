"""Rebase only the fixed current T-078 branch; stop and preserve every conflict."""
import argparse,json,os,subprocess,traceback
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);args=p.parse_args()
expected=json.loads(args.inputs.read_bytes());root=Path(expected['root']);log=args.inputs.parent
record={'status':'INCOMPLETE','scope':'Git rebase only; no conflict resolution, stash/reset/clean, hook disabling, fetch/push or services','inputs':expected}
def git(*argv):return subprocess.check_output(['git',*argv],cwd=root,text=True).strip()
def verify_main():
    subprocess.run(['git','merge-base','--is-ancestor',expected['target'],'main'],cwd=root,check=True)
    assert not git('log','--format=%H',expected['target']+'..main','--','workbench/','acceptance/','scripts/'),'Code changed after the fixed target'
    assert not git('diff',expected['target']+'..main','--','workbench/','acceptance/','scripts/'),'Code differs from the fixed target'
    return git('rev-parse','main')
def save():(log/'result.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
save()
try:
    assert root==Path('/Users/luckye/Documents/Code/a2a-wt-t078')
    assert expected['target']=='490de67d05a08ccf8a453a78694a106288579b47'
    assert git('branch','--show-current')==expected['branch']=='exec/t078'
    assert git('rev-parse','HEAD')==expected['before']
    record['main_before_rebase']=verify_main()
    assert expected['backup_ref']=='backup/t078-before-main-2-'+expected['before'][:12]
    assert git('merge-base',expected['before'],expected['target'])==expected['merge_base']
    assert not git('status','--porcelain=v1'),'Dirty worktree; no automatic preservation workaround'
    for name in ['rebase-merge','rebase-apply']:assert not Path(git('rev-parse','--git-path',name)).exists()
    assert not any(name.startswith('A2A_') or name=='CODEX_THREAD_ID' or name=='GIT_CONFIG_COUNT' for name in os.environ)
    assert subprocess.run(['git','show-ref','--verify','--quiet','refs/heads/'+expected['backup_ref']],cwd=root).returncode==1,'Backup exists; inspect previous execution'
    subprocess.run(['git','branch',expected['backup_ref'],expected['before']],cwd=root,check=True)
    (log/'before-commits.txt').write_text(git('log','--reverse','--format=%H %s',expected['merge_base']+'..'+expected['before'])+'\n',encoding='utf-8')
    record['main_at_rebase_command']=verify_main()
    with (log/'rebase.stdout.txt').open('xb') as stdout,(log/'rebase.stderr.txt').open('xb') as stderr:
        result=subprocess.run(['git','-c','core.editor=true','-c','sequence.editor=true','rebase',expected['target']],cwd=root,stdout=stdout,stderr=stderr)
    conflicts=git('diff','--name-only','--diff-filter=U').splitlines()
    record.update(exit_code=result.returncode,HEAD=git('rev-parse','HEAD'),conflicts=conflicts,worktree_status=git('status','--porcelain=v1'))
    (log/'conflicts.txt').write_text('\n'.join(conflicts)+'\n',encoding='utf-8')
    (log/'worktree-status.txt').write_text(record['worktree_status']+'\n',encoding='utf-8')
    if result.returncode==0:
        assert not conflicts and not record['worktree_status']
        subprocess.run(['git','merge-base','--is-ancestor',expected['target'],'HEAD'],cwd=root,check=True)
        record['status']='PASS'
        (log/'after-commits.txt').write_text(git('log','--reverse','--format=%H %s',expected['target']+'..HEAD')+'\n',encoding='utf-8')
    else:
        rebase_head=subprocess.run(['git','rev-parse','REBASE_HEAD'],cwd=root,capture_output=True,text=True)
        record['REBASE_HEAD']=rebase_head.stdout.strip() if rebase_head.returncode==0 else None
except Exception as error:record.update(status='BLOCKED',error=repr(error),traceback=traceback.format_exc())
finally:save()
print(json.dumps({'status':record['status'],'HEAD':record.get('HEAD'),'REBASE_HEAD':record.get('REBASE_HEAD'),'conflicts':record.get('conflicts'),'log':str(log),'backup_ref':expected['backup_ref'],'error':record.get('error')},ensure_ascii=False))
raise SystemExit(0 if record['status']=='PASS' else 1)
