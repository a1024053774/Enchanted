"""The schema-2 fact command reports changes and mismatches without model grants."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

output=Path(sys.argv[1]);assert not output.exists();checks=[]
with tempfile.TemporaryDirectory(prefix='t093-facts-unit-',dir='/private/tmp') as temporary:
 root=Path(temporary);(root/'forwarder/journal').mkdir(parents=True)
 for changed in (False,True):
  for missing in (False,True):
   facts={'schema':2,'ledger':'forwarder/journal/requests.jsonl','forwarder':{'received':2},'inventory':{'changed':['.claude/concurrent.jsonl'] if changed else [],'pass_condition':False},'counts':{}}
   (root/'facts.json').write_text(json.dumps(facts))
   records=[{'kind':'request','sequence':1,'method':'POST','path':'/v1/messages'}]
   if not missing:records.append({'kind':'request','sequence':2,'method':'POST','path':'/v1/messages'})
   (root/'forwarder/journal/requests.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
   run=subprocess.run(['/opt/homebrew/bin/node',str(Path(__file__).resolve().parents[1]/'src/claudeLoginCheck.ts'),str(root)],capture_output=True,text=True,timeout=10)
   assert run.returncode==0,'fact_command_must_not_grant_or_reject_model_permission'
   value=json.loads(run.stdout);assert value['inventory']==facts['inventory'];assert value['counts']['counts_match'] is (not missing)
   checks.append({'inventory_changed':changed,'missing_record':missing,'fact_exit':run.returncode,'counts_match':value['counts']['counts_match']})
 facts['phase']='before_cli_input';(root/'preflight.json').write_text(json.dumps(facts))
 run=subprocess.run(['/opt/homebrew/bin/node',str(Path(__file__).resolve().parents[1]/'src/claudeLoginCheck.ts'),'--preflight',str(root)],capture_output=True,text=True,timeout=10)
 assert run.returncode==0 and json.loads(run.stdout)['phase']=='before_cli_input'
 checks.append({'preflight_mode':True,'fact_exit':run.returncode})
with output.open('x') as stream:json.dump({'status':'PASS','scope':'read-only fact command on supplied synthetic metadata/ledger; no OS sandbox claim','checks':checks},stream,indent=2);stream.write('\n')
print(json.dumps({'status':'PASS','checks':len(checks)}))
