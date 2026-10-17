"""Check ownership, text/command syntax and add-path existence; never mutate Git."""
import argparse
import ast
import json
from pathlib import Path
import shlex
import subprocess

SOURCE=Path(__file__).resolve().parents[4];BASE=SOURCE/'evidence/2026-10-11-batch13/T-078';HERE=Path(__file__).resolve().parent
CODE=['t078_09b_rehearsal_host.ts','t078_09b_rehearsal_peer.py','t078_raw_retention.py','t078_rev2_tools_cases.py',
      'test_t078_09c_coordinator_chain.py','test_t078_09c_real_chain.py','test_t078_rev2_rehearsal.py',
      'test_t078_a14_rehearsal.py','t078_owner_receipt_fixture.py','t078_process_tree.py','t078_topology_probe.py',
      'test_t078_topology_guards.py','test_t078_topology_probe_entry.py']
OWNED=['workbench/tests/'+name for name in CODE]+[str(path.relative_to(SOURCE)) for path in [
    BASE/'RESULTS.md',HERE,BASE/'09c-attempt-2-diag-01/current-topology-01',BASE/'09c-topology-probe-materials-01']]


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--materials',action='store_true');a=p.parse_args()
    assert not a.output.exists()
    def git(*args):return subprocess.check_output(['git',*args],cwd=SOURCE)
    assert not git('diff','--cached','--name-only'),'stage must be empty before ownership preflight'
    names=[]
    for row in git('status','--porcelain=v1','-z','--untracked-files=all').split(b'\0'):
        if not row:continue
        state=row[:2].decode();name=row[3:].decode();assert state in [' M','??'],(state,name)
        assert any(name==root or name.startswith(root+'/') for root in OWNED),('Unowned; no mutation',name)
        path=SOURCE/name;assert path.is_file() and not path.is_symlink() and path.stat().st_size<=5*1024*1024,name
        names.append(name)
    for name in CODE:
        path=SOURCE/'workbench/tests'/name;assert path.is_file()
        if path.suffix=='.py':ast.parse(path.read_text(encoding='utf-8'))
    for path in HERE.glob('*.py'):ast.parse(path.read_text(encoding='utf-8'))
    assert not git('diff','--','workbench/src','workbench/app','acceptance','scripts')
    subprocess.run(['git','diff','--check','--',*[str(SOURCE/'workbench/tests'/name) for name in CODE],str(BASE/'RESULTS.md')],cwd=SOURCE,check=True)
    commands=[]
    if a.materials:
        folder=BASE/'09c-topology-probe-materials-01';value=json.loads((folder/'SOURCE.json').read_bytes())
        assert not git('diff',value['source_revision'],'--','workbench','acceptance','scripts')
        assert json.loads((folder/'setup-approval.json').read_bytes())['approved_by'] is None
        for path in folder.glob('*COMMAND*.txt'):
            r=subprocess.run(['/bin/sh','-n',str(path)],capture_output=True);assert r.returncode==0,(path,r.stderr)
            for line in path.read_text(encoding='utf-8').splitlines():
                if line.startswith('python3 -B '):
                    argv=shlex.split(line);assert Path(argv[2]).is_file(),argv
                    commands.append({'file':str(path),'entry':argv[2],'execution':'NOT_RUN'})
        expected_add_paths=[folder,HERE]
    else:expected_add_paths=[SOURCE/'workbench/tests'/name for name in CODE]+[BASE/'RESULTS.md',HERE,BASE/'09c-attempt-2-diag-01/current-topology-01']
    for path in expected_add_paths:assert path.exists(),('git-add path missing',str(path))
    add_names=[str(path.relative_to(SOURCE)) for path in expected_add_paths]
    for name in names:
        assert any(name==root or name.startswith(root+'/') for root in add_names),('allowed but omitted from git-add list',name)
    own_output=str(a.output.resolve().relative_to(SOURCE))
    assert any(own_output==root or own_output.startswith(root+'/') for root in add_names),'preflight output omitted from add list'
    for path in [HERE/'README.md',HERE/'PARITY.md',BASE/'RESULTS.md']:
        text=path.read_text(encoding='utf-8');assert '\ufffd' not in text and not text.startswith('\ufeff')
    result={'status':'PASS','HEAD':git('rev-parse','HEAD').decode().strip(),'owned_paths':names,
        'git_add_paths':list(map(str,expected_add_paths)),'add_paths_exist':True,'simulated_final_status':[],
        'output_is_owned':str(a.output.resolve()).startswith(str(HERE)+'/'),'commands':commands,'actual_git_mutations':0,
        'runtime_scenes':'NOT_RUN','process_classification':'UNKNOWN'}
    assert result['output_is_owned']
    with a.output.open('x',encoding='utf-8') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'PASS','owned_paths_before_output':len(names),'commands':len(commands),'add_paths_exist':True,'simulated_final_status':[]}))


if __name__=='__main__':main()
