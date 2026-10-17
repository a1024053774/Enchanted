"""Read-only handoff gate: ownership, exact add list, syntax and future command paths."""
import argparse
import ast
import json
from pathlib import Path
import shlex
import subprocess
import sys

SOURCE=Path(__file__).resolve().parents[4];BASE=SOURCE/'evidence/2026-10-11-batch13/T-078';HERE=Path(__file__).resolve().parent
CODE='''t078_09b_rehearsal_peer.py t078_09c_driver.py t078_09c_timed_run.py t078_raw_retention.py t078_rev2_tools_cases.py
t078_topology_probe.py test_t078_09c_coordinator_paths.py test_t078_09c_real_chain.py test_t078_rev2_rehearsal.py
test_t078_topology_guards.py test_t078_c3_material_paths.py test_t078_caffeinate_kernel.py test_t078_caffeinate_profiles.py
test_t078_caffeinate_topology.py test_t078_probe_submission.py'''.split()
PATHS=[SOURCE/'workbench/tests'/n for n in CODE]+[BASE/n for n in ['RESULTS.md','prepare-09b-executable.py',
    'prepare-c2-runtime.py','run-09b.py','c3-revalidation.py','freeze-c3.py','09c-topology-idle-fix-01/turn-approval-01.json',
    '09c-attempt-3-materials-01','09c-caffeinate-fix-01','09c-topology-probe-run-01']]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();assert not args.output.exists()
    def git(*a):return subprocess.check_output(['git',*a],cwd=SOURCE)
    assert not git('diff','--cached','--name-only')
    roots=[str(p.relative_to(SOURCE)) for p in PATHS]
    def owned(name):return any(name==r or name.startswith(r+'/') for r in roots)
    for p in PATHS:assert p.exists(),('missing git-add path',str(p))
    rows=[]
    for row in git('status','--porcelain=v1','-z','--untracked-files=all').split(b'\0'):
        if not row:continue
        state=row[:2].decode();name=row[3:].decode();assert state in [' M','??'],(state,name)
        assert owned(name),('Unowned work; no mutation',name)
        path=SOURCE/name;assert path.is_file() and not path.is_symlink() and path.stat().st_size<=5*1024*1024,name
        assert path.name not in ['auth.json','credentials.json','operator.json'] and not path.name.startswith('state.sqlite3'),name
        rows.append(name)
    assert owned(str(args.output.resolve().relative_to(SOURCE)))
    assert not git('diff','--','workbench/src','workbench/app','acceptance','scripts')
    pyfiles=[p for p in PATHS if p.suffix=='.py']+list(HERE.glob('*.py'))
    for p in pyfiles:ast.parse(p.read_text(encoding='utf-8'))
    commands=[];future=[]
    for folder in [HERE,BASE/'09c-attempt-3-materials-01']:
        for p in folder.rglob('*.txt'):
            text=p.read_text(encoding='utf-8')
            if 'python3 -B' not in text:continue
            syntax=subprocess.run(['/bin/sh','-n',str(p)],capture_output=True);assert syntax.returncode==0,(p,syntax.stderr)
            if "<<'PY'" in text:ast.parse(text.split("<<'PY'\n",1)[1].split('\nPY\n',1)[0])
            for line in text.splitlines():
                if not line.startswith('python3 -B /'):continue
                argv=shlex.split(line);assert Path(argv[2]).is_file(),argv
                for key in ['--owner','--approval']:
                    if key in argv:assert Path(argv[argv.index(key)+1]).is_file(),(p,key)
                if '--output' in argv:
                    output=Path(argv[argv.index('--output')+1]);assert not output.exists(),('output already exists',p,str(output))
                    future.append(str(output))
                for key in ['--capture-result','--independent-readback']:
                    if key in argv:future.append(argv[argv.index(key)+1])
                commands.append({'file':str(p),'argv':argv,'execution':'NOT_RUN'})
    sys.path.insert(0,str(SOURCE/'workbench/tests'))
    from t078_raw_retention import validate_owner_receipts
    validate_owner_receipts(json.loads((HERE/'probe-closeout/owner.json').read_bytes()))
    for kind in ['probe','attempt2']:
        approved=json.loads((HERE/(kind+'-closeout/cleanup-approval.json')).read_bytes())
        assert approved['approved_by'] is None and approved['approval_ref'] is None
    for p in [HERE/'README.md',HERE/'CLOSEOUT.md',BASE/'09c-attempt-3-materials-01/PLAN.md',BASE/'RESULTS.md']:
        body=p.read_text(encoding='utf-8');assert '\ufffd' not in body and not body.startswith('\ufeff')
    subprocess.run(['git','diff','--check','--',*[str(p) for p in PATHS if p.is_file() and p.name!='turn-approval-01.json']],cwd=SOURCE,check=True)
    result={'status':'PASS','HEAD':git('rev-parse','HEAD').decode().strip(),'owned_paths':rows,'git_add_paths':list(map(str,PATHS)),
        'add_paths_exist':True,'simulated_final_status':[],'output_is_in_add_list':True,'commands':commands,'future_inputs_outputs':future,
        'actual_git_mutations':0,'scene_actions':0,'kernel_rehearsal_cleanup_C3_execution':'NOT_RUN'}
    with args.output.open('x',encoding='utf-8') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'PASS','owned_paths_before_output':len(rows),'commands':len(commands),'simulated_final_status':[],'scene_actions':0}))


if __name__=='__main__':main()
