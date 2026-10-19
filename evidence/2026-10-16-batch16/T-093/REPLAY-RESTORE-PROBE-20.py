"""Replay reviewer03's supplied-boundary probe without changing any old fixture."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--revision');parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();here=Path(__file__).resolve().parent;repo=here.parents[2];output=args.output.resolve()
metadata=output.with_suffix('.command.json')
if output.exists() or metadata.exists():parser.error('select a new output')
run=Path(tempfile.mkdtemp(prefix='t093-restore-replay20-',dir='/private/tmp'));(run/'t').mkdir()
private=Path(tempfile.mkdtemp(prefix='a2a-claude-login-replay20-',dir='/private/tmp'))
source=repo/'workbench/src/panes.ts'
if args.revision:
 source=run/'panes-source.ts'
 source.write_bytes(subprocess.check_output(['git','-C',str(repo),'show',args.revision+':workbench/src/panes.ts']))
record=json.loads((here/'generated-normal-record-review03-20.json').read_text(encoding='utf-8'))
old_root=str(Path(record['worktree']).parent);old_private=str(Path(record['env']['HOME']).parent)
def moved(value):
 if isinstance(value,str):return value.replace(old_root,str(run/'generated')).replace(old_private,str(private))
 if isinstance(value,list):return [moved(item) for item in value]
 if isinstance(value,dict):return {key:moved(item) for key,item in value.items()}
 return value
input_path=run/'generated-normal-record.json';input_path.write_text(json.dumps(moved(record)),encoding='utf-8')
script=(here/'REVIEWER-RESTORE-PROBE-20.mjs').read_text(encoding='utf-8')
script=script.replace("const base = '/private/tmp/t093-r03-uj4pu1e0';",'const base = '+json.dumps(str(run))+';')
script=script.replace("new URL('file://' + base + '/candidate/workbench/src/panes.ts')",'new URL('+json.dumps((repo/'workbench/src/panes.ts').as_uri())+')')
probe=run/'restore-independent.mjs';probe.write_text(script,encoding='utf-8')
command=['node','--experimental-vm-modules',str(probe),str(source),str(output),str(input_path)]
process=subprocess.run(command,capture_output=True,text=True,timeout=30,start_new_session=True)
with metadata.open('x',encoding='utf-8') as file:json.dump({'source_revision':args.revision or 'current source','command':command,'exit':process.returncode,'fixture':str(run),'private_fixture':str(private),'modifications':'Only scratch/dependency URL and generated input path prefixes; original cases/oracle unchanged','real_CLI_auth_models':0},file,ensure_ascii=False,indent=2);file.write('\n')
print(process.stdout.strip());raise SystemExit(process.returncode)
