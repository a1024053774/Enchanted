#!/usr/bin/env python3
import json, subprocess
from pathlib import Path
base=Path('/private/tmp/t249-terra-20261108-01')
out=Path(__file__).parent
before=json.loads((base/'oracle-before.json').read_text())
def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],text=True)
a=base/'repos/alpha'; u=base/'repos/unborn'; readonly=Path('/Users/luckye/Library/Application Support/a2a-orchestrator-test/worktrees/terra/readonly')
root=before['detail_choices']['root']; normal=before['detail_choices']['normal']; feature=before['detail_choices']['feature']
result={'before':before,'alpha_after_refs':git(a,'for-each-ref','--format=%(objectname) %(refname)'), 'alpha_after_status':git(a,'status','--porcelain=v2','--branch'), 'readonly_after_status':git(readonly,'status','--porcelain=v2','--branch'),'readonly_after_refs':git(readonly,'for-each-ref','--format=%(objectname) %(refname)'), 'commits':{}, 'working_diff':git(a,'diff','--','first.txt'), 'unborn_worktree_file':(u/'file[1].txt').read_text(), 'unborn_staged_file':git(u,'show',':file[1].txt')}
for label,commit in [('root',root),('normal',normal),('feature',feature)]:
    result['commits'][label]={'hash':commit,'parents':git(a,'show','-s','--format=%P',commit).strip().split(),'subject':git(a,'show','-s','--format=%s',commit).strip(),'files':git(a,'diff-tree','--root','--no-commit-id','--name-only','-r',commit).splitlines(),'star_diff':git(a,'--literal-pathspecs','show','--format=','--no-ext-diff',commit,'--','file*.txt')}
(out/'git-oracle.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
