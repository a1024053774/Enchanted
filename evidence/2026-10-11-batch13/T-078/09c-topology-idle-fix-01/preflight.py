"""Read-only ownership, evidence and command checks before a direct Git commit."""
import argparse
import ast
import json
from pathlib import Path
import shlex
import subprocess

SOURCE=Path(__file__).resolve().parents[4];BASE=SOURCE/'evidence/2026-10-11-batch13/T-078';HERE=Path(__file__).resolve().parent
PATHS=[SOURCE/'workbench/tests'/name for name in ['p1_simulated_actions.py','t078_topology_probe.py','test_t078_topology_idle.py']]+[
    BASE/'prepare-c2-runtime.py',BASE/'RESULTS.md',HERE,BASE/'09c-topology-probe-materials-01/setup-approval.json',
    BASE/'09b-a365-b1-ideation-01-dry-run',BASE/'09b-a365-b1-ideation-01',BASE/'09c-topology-probe-run-01']


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    assert not args.output.exists()
    def git(*a):return subprocess.check_output(['git',*a],cwd=SOURCE)
    assert not git('diff','--cached','--name-only')
    for path in PATHS:assert path.exists(),('git-add path missing',str(path))
    roots=[str(p.relative_to(SOURCE)) for p in PATHS];names=[]
    def owned(name):return any(name==root or name.startswith(root+'/') for root in roots)
    for row in git('status','--porcelain=v1','-z','--untracked-files=all').split(b'\0'):
        if not row:continue
        state=row[:2].decode();name=row[3:].decode();assert state in [' M','??'],(state,name)
        assert owned(name),('Unowned; no mutation',name)
        path=SOURCE/name;assert path.is_file() and not path.is_symlink() and path.stat().st_size<=5*1024*1024,name
        assert path.name not in ['auth.json','credentials.json','operator.json'] and not path.name.startswith('state.sqlite3'),name
        names.append(name)
    assert owned(str(args.output.resolve().relative_to(SOURCE)))
    assert not git('diff','--','workbench/src','workbench/app','acceptance','scripts')
    for path in [*PATHS[:4],HERE/'preflight.py']:
        ast.parse(path.read_text(encoding='utf-8'))
    source=json.loads((BASE/'09c-topology-probe-run-01/probe.json').read_bytes())
    approval=json.loads((HERE/'turn-approval-01.json').read_bytes())
    assert approval==json.loads((BASE/'09c-topology-probe-run-01/turn-approval-template.json').read_bytes())
    assert approval['root']==source['root'] and approval['source_revision']==source['source_revision']
    assert approval['approved_by'] is None and approval['approval_ref'] is None and approval['permission_Enter_allowed'] is False
    commands=[]
    for path in HERE.glob('*COMMAND.txt'):
        check=subprocess.run(['/bin/sh','-n',str(path)],capture_output=True);assert check.returncode==0,(path,check.stderr)
        for line in path.read_text(encoding='utf-8').splitlines():
            if line.startswith('python3 -B '):
                argv=shlex.split(line);assert Path(argv[2]).is_file()
                assert Path(argv[argv.index('--probe')+1])==BASE/'09c-topology-probe-run-01'
                if '--approval' in argv:assert Path(argv[argv.index('--approval')+1]).is_file()
                output=Path(argv[argv.index('--output')+1]);assert not output.exists(),output
                commands.append({'argv':argv,'entry_and_input_paths_exist':True,'output_is_new':True,'execution':'NOT_RUN'})
    assert len(commands)==2
    assert json.loads((HERE/'green-03/result.json').read_bytes())['status']=='PASS'
    for name in ['red-01','known-bad-red-01','marker-only-red-01']:
        assert json.loads((HERE/name/'result.json').read_bytes())['status']=='INCOMPLETE'
    for path in [HERE/'README.md',BASE/'RESULTS.md']:
        body=path.read_text(encoding='utf-8');assert '\ufffd' not in body and not body.startswith('\ufeff')
    subprocess.run(['git','diff','--check','--',*map(str,PATHS[:5])],cwd=SOURCE,check=True)
    result={'status':'PASS','HEAD':git('rev-parse','HEAD').decode().strip(),'git_add_paths':list(map(str,PATHS)),
        'owned_paths':names,'future_output_is_owned':True,'add_paths_exist':True,'simulated_final_status':[],
        'commands':commands,'actual_git_mutations':0,'scene_actions':0,'live_probe_execution':'INCOMPLETE'}
    with args.output.open('x',encoding='utf-8') as stream:stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'PASS','owned_paths_before_output':len(names),'commands':len(commands),
        'add_paths_exist':True,'simulated_final_status':[],'scene_actions':0}))


if __name__=='__main__':main()
