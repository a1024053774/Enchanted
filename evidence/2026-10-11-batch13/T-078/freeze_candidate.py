#!/usr/bin/env python3
"""Read-only Git checks and append-only freeze/rebase evidence. No Git writes."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
BASE=ROOT/'evidence/2026-10-11-batch13/T-078'
TICKET='.project-map/tickets/T-078-controllers-in-workbench.md'
phase,label=sys.argv[1:3]
if not label or label in ('.','..') or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in label):
    raise RuntimeError('A new single-directory label is required')
out=BASE/label
plan=json.loads((BASE/'freeze-plan.json').read_text(encoding='utf-8'))

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True)

def save(path,value):
    with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2)

def allowed(path):
    return (path.startswith(('workbench/','evidence/2026-10-11-batch13/T-078/')) or path==TICKET) and not Path(path).name.startswith('freeze-env-')

def commit_trailers():
    message=git('show','-s','--format=%B','HEAD')
    parsed=subprocess.check_output(['git','interpret-trailers','--parse'],cwd=ROOT,input=message,text=True).splitlines()
    for key,value in plan['expected_trailers'].items():
        if [line for line in parsed if line.startswith(key+':')]!=[key+': '+value]:
            raise RuntimeError('Missing or conflicting commit trailer: '+key)
    return parsed

if phase=='prepare':
    if out.exists():raise RuntimeError('Existing freeze/rebase output is preserved')
    if Path(git('rev-parse','--show-toplevel').strip()).resolve()!=ROOT:raise RuntimeError('Wrong Git worktree')
    if git('branch','--show-current').strip()!=plan['branch'] or git('rev-parse','HEAD').strip()!=plan['base_head']:
        raise RuntimeError('Candidate branch/head changed before freezing')
    if git('diff','--cached','--name-only').strip():raise RuntimeError('Existing staged changes must be inspected')
    if not os.path.ismount('/Volumes/WD-Elements'):raise RuntimeError('External evidence volume is not mounted')
    large=[str(p) for p in BASE.rglob('*') if p.is_file() and p.stat().st_size>5*1024*1024]
    if large:raise RuntimeError('Archive large evidence before freezing: '+str(large))
    expected={'A2A_PROJECT','A2A_TASK','A2A_ATTEMPT','A2A_SESSION','A2A_ROLE','A2A_LAUNCH','A2A_LAUNCHES',
              'CODEX_THREAD_ID','GIT_CONFIG_COUNT','GIT_CONFIG_KEY_0','GIT_CONFIG_VALUE_0'}
    env={key:os.environ.get(key) for key in expected}
    if set(env)!=expected or any(not isinstance(v,str) or not v or '\n' in v or '\r' in v for v in env.values()):
        raise RuntimeError('Current worker session is missing its Git environment')
    for key,field in [('A2A-Task','A2A_TASK'),('A2A-Attempt','A2A_ATTEMPT'),('A2A-Session','A2A_SESSION'),
                      ('A2A-Role','A2A_ROLE'),('A2A-Launch','A2A_LAUNCH'),('A2A-Native-Session','CODEX_THREAD_ID')]:
        if env[field]!=plan['expected_trailers'][key]:raise RuntimeError('Current session differs from worker: '+field)
    if env['A2A_LAUNCHES']!=plan['launch_record_source']:raise RuntimeError('Launch record source changed')
    if env['GIT_CONFIG_COUNT']!='1' or env['GIT_CONFIG_KEY_0']!='core.hooksPath':
        raise RuntimeError('Current session Git hook configuration changed')
    launches=[json.loads(line) for line in Path(env['A2A_LAUNCHES']).read_text(encoding='utf-8').splitlines()]
    current=[row for row in launches if row.get('launch_id')==env['A2A_LAUNCH']][-1]
    for key in ['project','task','attempt','session','role']:
        if current[key]!=env['A2A_'+key.upper()]:raise RuntimeError('Worker launch identity changed: '+key)
    if current['native_session'] not in ['unknown',env['CODEX_THREAD_ID']]:raise RuntimeError('Native session changed')
    for key,field in [('A2A-Tool','cli_version'),('A2A-Model','model'),('A2A-Effort','effort')]:
        if current[field]!=plan['expected_trailers'][key]:raise RuntimeError('Commit provenance changed: '+key)
    snapshot={'status':'PASS','task':'T-078-1','branch':plan['branch'],'head':plan['base_head'],
              'main':git('rev-parse','main').strip(),'status_before':git('status','--short'),
              'git_common_dir':git('rev-parse','--git-common-dir').strip(),
              'note':'Use the already-issued session Git hooks; no global or repository Git configuration is changed.'}
    save(BASE/('freeze-preflight-'+label+'.json'),snapshot)
    print(json.dumps({'status':'PASS','phase':'prepared','branch':plan['branch'],'main':snapshot['main']}))
elif phase=='staged':
    paths=git('diff','--cached','--name-only','-z').split('\0')[:-1]
    if not paths or not any(p.startswith('workbench/') for p in paths) or not all(allowed(p) for p in paths):
        raise RuntimeError('Staged files exceed this card or omit workbench')
    # Raw failure output and historical source snapshots must remain byte-for-byte intact.
    subprocess.run(['git','diff','--cached','--check','--','workbench',TICKET],cwd=ROOT,check=True)
    out.mkdir()
    result={'status':'PASS','phase':'staged','files':paths,'head':git('rev-parse','HEAD').strip(),
            'diff_check_scope':['workbench',TICKET],'raw_evidence_preserved':True}
    save(out/'staged-check.json',result)
    print(json.dumps({'status':'PASS','phase':'staged','files':len(paths)}))
elif phase=='committed':
    if git('rev-parse','HEAD^').strip()!=plan['base_head']:raise RuntimeError('Unexpected commit parent')
    paths=git('diff','HEAD^','HEAD','--name-only','-z').split('\0')[:-1]
    if not all(allowed(p) for p in paths):raise RuntimeError('Commit exceeds this card')
    parsed=commit_trailers()
    if git('status','--porcelain','--untracked-files=no').strip():raise RuntimeError('Tracked files changed after commit')
    save(out/'frozen-commit.json',{'status':'PASS','commit':git('rev-parse','HEAD').strip(),'trailers':parsed,
                                  'files':paths,'main_before_rebase':git('rev-parse','main').strip()})
    print(json.dumps({'status':'PASS','phase':'committed','commit':git('rev-parse','HEAD').strip()}))
elif phase=='rebased':
    code=int(sys.argv[3]);conflicts=git('diff','--name-only','--diff-filter=U').splitlines()
    if code==0:
        if conflicts or git('branch','--show-current').strip()!=plan['branch']:raise RuntimeError('Rebase did not restore the candidate branch')
        subprocess.run(['git','merge-base','--is-ancestor','main','HEAD'],cwd=ROOT,check=True)
        commit_trailers()
    result={'status':'PASS' if code==0 else 'INCOMPLETE','phase':'rebase','exit':code,
            'head':git('rev-parse','HEAD').strip(),'main':git('rev-parse','main').strip(),
            'conflicts':conflicts,'worktree_status':git('status','--short'),
            'final_checks_run':False,'independent_review_run':False}
    save(out/'rebase-result.json',result);print(json.dumps(result,ensure_ascii=False))
else:raise RuntimeError('Unknown freeze evidence phase')
