"""Check coordinator source packaging and the outside command without a scene."""
import argparse
import ast
import json
from pathlib import Path
import shlex
import sys

SOURCE=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(SOURCE/'workbench/tests'))
from test_t078_09c_coordinator_chain import CoordinatorScene, BASE, TESTS


parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
args.output.mkdir(parents=True,exist_ok=False)
for path in [TESTS/'test_t078_09c_coordinator_chain.py',TESTS/'test_t078_09c_coordinator_paths.py',
             TESTS/'test_t078_09c_real_chain.py',TESTS/'t078_09c_timed_run.py',Path(__file__)]:
    body=path.read_text(encoding='utf-8');assert '\ufffd' not in body;ast.parse(body,filename=str(path));compile(body,str(path),'exec')
names=CoordinatorScene.__new__(CoordinatorScene).freeze_sources(args.output/'sources.tar.gz')
required=['workbench/tests/test_t078_09c_coordinator_chain.py','workbench/tests/t078_09c_timed_run.py',
          'workbench/tests/test_t078_09c_real_chain.py','evidence/2026-10-11-batch13/T-078/prepare-a14.py',
          'evidence/2026-10-11-batch13/T-078/prepare-rev2-owner.py']
assert all(path in names for path in required)
argv=shlex.split((BASE/'09c-coordinator-rehearsal-01/RUN-OUTSIDE-COMMAND.txt').read_text(encoding='utf-8'))
assert len(argv)==7 and argv[0]=='python3' and argv[1]=='-B' and Path(argv[2]).is_file()
assert argv[3]=='--signature-ref' and 'REHEARSAL ONLY' in argv[4] and argv[5]=='--output'
output=Path(argv[6]);assert output.parent.is_dir() and not output.exists()
value={'status':'PASS','scope':__doc__,'source_members':len(names),'regular_unique_members_byte_readback':True,
       'required_members':required,'outside_command':argv,'outside_output_absent':True,'scene_process_starts':0,
       'key_writes':0,'models':0,'note':'working candidate file-only package check; actual rehearsal binds the committed HEAD'}
with (args.output/'result.json').open('x',encoding='utf-8') as stream:stream.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':'PASS','source_members':len(names),'outside_output_absent':True,'scene_process_starts':0}))
