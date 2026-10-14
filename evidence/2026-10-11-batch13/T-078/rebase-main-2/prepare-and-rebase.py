"""Controller #163: preserve this handoff with worker identity, then rebase in a separate environment."""
import json,os,subprocess,sys,tempfile,traceback
from pathlib import Path

ROOT=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
BASE=Path(__file__).resolve().parent
HEAD='50ea0f5f1121f0651eeab7b5f89351d34b65feb8'
TARGET='490de67d05a08ccf8a453a78694a106288579b47'
MERGE_BASE='87e954a2f4059d471e3e240872b565217e29b0b5'
DISPOSITION='.project-map/inbox/20261014T191522Z-executor-disposition-001.md'

def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def verify_main():
    subprocess.run(['git','merge-base','--is-ancestor',TARGET,'main'],cwd=ROOT,check=True)
    assert not git('log','--format=%H',TARGET+'..main','--','workbench/','acceptance/','scripts/'),'Code changed after the fixed target'
    assert not git('diff',TARGET+'..main','--','workbench/','acceptance/','scripts/'),'Code differs from the fixed target'
    return git('rev-parse','main')
def main():
    assert BASE==ROOT/'evidence/2026-10-11-batch13/T-078/rebase-main-2'
    assert git('branch','--show-current')=='exec/t078' and git('rev-parse','HEAD')==HEAD
    observed_main=verify_main()
    assert git('merge-base',HEAD,TARGET)==MERGE_BASE
    assert os.environ.get('CODEX_THREAD_ID')=='01a13a72-892d-7e33-8237-a592c9652c35','Run under the original worker startup identity'
    assert os.environ.get('A2A_TASK')=='T-078-1' and os.environ.get('A2A_ROLE')=='worker'
    assert not any(name in os.environ for name in ['GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE']),'Unexpected Git routing environment'
    for name in ['rebase-merge','rebase-apply']:assert not Path(git('rev-parse','--git-path',name)).exists(),'Rebase already active'
    records=subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all'],cwd=ROOT).decode('utf-8').split('\0')
    allowed=[DISPOSITION,'.project-map/inbox/20261014T192750Z-worker:t078-rebase2-issue-001.md',
             '.project-map/inbox/20261014T193049Z-worker:t078-rebase2-report-001.md']
    for row in records:
        if not row:continue
        path=row[3:]
        assert path in allowed or path.startswith('evidence/2026-10-11-batch13/T-078/rebase-main-2/'),('Unowned dirty path; no stash/reset/clean',path)
    subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
    subprocess.run(['git','add','--',DISPOSITION,str(BASE.relative_to(ROOT))],cwd=ROOT,check=True)
    subprocess.run(['git','add','--','.project-map/inbox/20261014T192750Z-worker:t078-rebase2-issue-001.md'],cwd=ROOT,check=True)
    subprocess.run(['git','add','--','.project-map/inbox/20261014T193049Z-worker:t078-rebase2-report-001.md'],cwd=ROOT,check=True)
    subprocess.run(['git','diff','--cached','--stat'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m','docs(T-078): preserve second main rebase inputs and disposition'],cwd=ROOT,check=True)
    before=git('rev-parse','HEAD')
    assert not git('status','--porcelain=v1'),'Worktree not clean after handoff commit'
    log=Path(tempfile.mkdtemp(prefix='t078-rebase-main-2-',dir='/private/tmp'))
    expected={'before':before,'handoff_parent':HEAD,'target':TARGET,'merge_base':MERGE_BASE,'branch':'exec/t078',
              'backup_ref':'backup/t078-before-main-2-'+before[:12],'root':str(ROOT),'main_at_preparation':observed_main}
    (log/'inputs.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    path=str((BASE/'rebase.py').relative_to(ROOT))
    (log/'rebase.py').write_bytes(subprocess.check_output(['git','show',before+':'+path],cwd=ROOT))
    # The previous rebase used no per-session commit identity/hook overrides.
    # Leave repository/global config unchanged; retain the original trailers.
    dropped=[name for name in os.environ if name.startswith('A2A_') or name=='CODEX_THREAD_ID' or
             name in ['GIT_CONFIG_COUNT','GIT_CONFIG_PARAMETERS'] or name.startswith(('GIT_CONFIG_KEY_','GIT_CONFIG_VALUE_'))]
    child={name:value for name,value in os.environ.items() if name not in dropped}
    (log/'removed-session-env-names.json').write_text(json.dumps(sorted(dropped),indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','phase':'handoff-commit','revision':before,'log':str(log),'next':'bounded rebase; no launch'},ensure_ascii=False),flush=True)
    return subprocess.run([sys.executable,'-B',str(log/'rebase.py'),'--inputs',str(log/'inputs.json')],cwd=ROOT,env=child).returncode

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        print(json.dumps({'status':'BLOCKED','error':repr(error),'traceback':traceback.format_exc(),'scope':'Preserve any commit/rebase state; no automatic retry/abort'},ensure_ascii=False))
        raise SystemExit(1)
