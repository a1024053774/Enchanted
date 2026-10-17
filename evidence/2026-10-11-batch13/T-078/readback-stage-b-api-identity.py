"""Read A-05 ideation fake API argv and lstart twice; no process mutation."""
import argparse, json, os, shlex, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from workbench.tests.p1_processes import identity_from_ps
BASE=Path(__file__).resolve().parent;ROOT=Path(json.loads((BASE/'09b-stage-a-05/readiness.json').read_bytes())['root']);ROLE=ROOT/'roles/ideation';READY=json.loads((ROLE/'api-ready.json').read_bytes());PID=int(READY['pid'])
def probe():
 p=subprocess.run(['/bin/ps','-ww','-p',str(PID),'-o','pid=,lstart=,command='],capture_output=True,text=True,env={**os.environ,'LC_ALL':'C','LANG':'C'});return identity_from_ps(PID,p.returncode,p.stdout,p.stderr)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 first=probe();second=probe();parts=shlex.split(first['command']) if first else []
 expected=['-B',str(BASE.parents[2]/'workbench/tests/t078_09b_fake_api.py'),'--root',str(ROLE),'--role','ideation','--port','0']
 result={'status':'PASS' if first and second==first and parts[1:]==expected else 'INCOMPLETE','pid':PID,'ready':READY,'first':first,'second':second,'argv_expected':expected,'argv_match':bool(first and parts[1:]==expected),'scope':'two read-only ps command/lstart probes; no signal/API/CLI/pane action'}
 out=args.output.resolve();out.mkdir(exist_ok=False);(out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result));return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
