"""Malformed hook input fails before transport; verify real CLI raw audit."""
import argparse,json,subprocess,tempfile,uuid
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();args.output.mkdir()
root=Path(tempfile.mkdtemp(prefix='t078-2-hook-trace-',dir='/tmp')).resolve()
(root/'state').mkdir();(root/'roles/ideation/hooks').mkdir(parents=True)
launch=str(uuid.uuid4());payload=b'{bad-hook-input\n'
argv=['node','/Users/luckye/Documents/Code/a2a-wt-t078/workbench/src/gates/cli.ts','--state',str(root/'state'),'signal','--launch',launch]
env={'PATH':'/opt/homebrew/bin:/usr/bin:/bin','A2A_STATE':str(root/'state'),'A2A_LAUNCH':launch,'A2A_PRESET':'ideation',
     'A2A_CAPABILITY':'PRIVATE_NEVER_LOG','A2A_HOOK_TRACE_DIR':str(root/'roles/ideation/hooks')}
p=subprocess.run(argv,input=payload,capture_output=True,env=env,timeout=10)
(args.output/'stdout.bin').write_bytes(p.stdout);(args.output/'stderr.bin').write_bytes(p.stderr)
record={'status':'INCOMPLETE','argv':argv,'root':str(root),'exit_code':p.returncode,'scope':'Native gate CLI argument/input parsing only; no vendor CLI or socket call','real_vendor_model_turns':0}
try:
    assert p.returncode==2
    dirs=list((root/'roles/ideation/hooks').iterdir());assert len(dirs)==1,'hook raw record missing'
    d=dirs[0];assert (d/'stdin.bin').read_bytes()==payload
    assert (d/'stdout.bin').read_bytes()==p.stdout and (d/'stderr.bin').read_bytes()==p.stderr
    done=json.loads((d/'finished.json').read_text());assert done['exit_code']==2
    assert done['launch']==launch and done['duration_ms']>=0
    assert all(b'PRIVATE_NEVER_LOG' not in f.read_bytes() for f in d.iterdir() if f.is_file())
    record['status']='PASS'
except Exception as error:record['error']=repr(error)
with (args.output/'results.json').open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2)
print(json.dumps(record));raise SystemExit(0 if record['status']=='PASS' else 1)
