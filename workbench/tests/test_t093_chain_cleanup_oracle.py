"""Independent cleanup oracle regressions; synthetic receipts and mocked PID probes."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

source=Path(__file__).with_name('check_t093_chain_results.py')
spec=importlib.util.spec_from_file_location('result_oracle',source);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
output=Path(sys.argv[1]);assert not output.exists();checks=[]
with tempfile.TemporaryDirectory(prefix='t093-oracle-unit-',dir='/private/tmp') as temporary:
 directory=Path(temporary);target=directory/'result.json';root=directory/'t093-chain-removed'
 # A canonical absent root; these are external test inputs, not product output.
 root=Path('/private/tmp')/('t093-chain-oracle-absent-'+directory.name)
 primary='external_primary_probe'
 roles=('F','D','U','S','M','G0','G1','G2')
 identities={role:440910+index for index,role in enumerate(roles)}
 control={'fixture_root':str(root),'checkpoint_sequence':3,'processes':{**{role:{'pgrp':identities[role]} for role in roles[:5]},'G':[{'pid':identities[role]} for role in roles[5:]],'C':[{'pid':440901},{'pid':440902}]},'writer_exit':{'all_exited':True,'daemon_closed':True,'groups':[{'role':name,'pgrp':identities[name],'exited':True} for name in roles],'children':[{'pid':440901,'exited':True}],'reporter_pid':440902},'source_home_cleanup':{'profile':'D test source cleanup','source_home':str(root/'source-home'),'removed':True,'credential_body_read':False,'checkpoint_sequence':2},'service_receipts':{'D_guards':{'source_content_read':{'denied':True,'bytes_read':0,'errno':1}}}}
 history=[{'sequence':1,'phase':'business_pending','primary_failure':None},{'sequence':2,'phase':'cleanup_pending','primary_failure':primary},{'sequence':3,'phase':'complete','primary_failure':primary,'fixture_removed':True}]
 for kind in ('control','writer_alive','primary_lost','source_unconfirmed','source_body_readable','source_before_checkpoint','history_missing','reporter_alive','false_group_exit','false_child_exit','wrong_group_identity','omitted_child'):
  value=copy.deepcopy(control);events=copy.deepcopy(history)
  if kind=='writer_alive':value['writer_exit']['all_exited']=False
  if kind=='primary_lost':events[1]['primary_failure']=None
  if kind=='source_unconfirmed':value['source_home_cleanup']['removed']=False
  if kind=='source_body_readable':value['service_receipts']['D_guards']['source_content_read']['denied']=False
  if kind=='source_before_checkpoint':value['source_home_cleanup']['checkpoint_sequence']=1
  if kind=='history_missing':events=[]
  if kind=='wrong_group_identity':value['writer_exit']['groups'][0]['pgrp']=441000
  if kind=='omitted_child':value['writer_exit']['children']=[]
  Path(str(target)+'.events.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in events))
  def probe(pid,signal):
   assert signal==0
   if kind=='reporter_alive' and pid==440902:return
   if kind=='false_child_exit' and pid==440901:return
   raise ProcessLookupError()
  def group_probe(group,signal):
   assert signal==0
   if kind=='false_group_exit' and group==identities['F']:return
   raise ProcessLookupError()
  with patch.object(mod.os,'kill',side_effect=probe),patch.object(mod.os,'killpg',side_effect=group_probe):errors=mod.cleanup_proof(value,target,primary)
  checks.append({'case':kind,'status':'PASS' if (errors==[])==(kind=='control') else 'FAIL','accepted':not errors,'failures':errors})
status='PASS' if all(v['status']=='PASS' for v in checks) else 'FAIL'
with output.open('x') as stream:json.dump({'status':status,'scope':'independent result oracle logical counterexamples; no actual process or OS boundary execution','checks':checks},stream,indent=2);stream.write('\n')
print(json.dumps({'status':status,'checks':len(checks)}));raise SystemExit(0 if status=='PASS' else 2)
