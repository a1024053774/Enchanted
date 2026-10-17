"""Probe refusal entry and sampling bookkeeping; no CLI/API/socket/ps."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch
import t078_topology_probe as probe


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False);checks=[]
    with tempfile.TemporaryDirectory(prefix='t078-probe-entry-',dir='/private/tmp') as tmp:
        root=Path(tmp)
        for case in ['missing','unsigned','wrong-limit']:
            output=root/case;command=[sys.executable,'-B',str(Path(probe.__file__)),'--mode','setup','--output',str(output)]
            if case!='missing':
                approval=root/(case+'.json');value={'approved_by':None,'approval_ref':None,'allow_role_cli_spawn':False,'max_role_sessions':1,'real_model_turns':0}
                if case=='wrong-limit':value.update(approved_by='executor',approval_ref='UNIT ONLY',max_role_sessions=2)
                approval.write_text(json.dumps(value),encoding='utf-8');command+=['--approval',str(approval)]
            result=subprocess.run(command,capture_output=True,timeout=10)
            assert result.returncode!=0 and not output.exists(),case
            (args.output/(case+'.stderr.bin')).write_bytes(result.stderr)
            checks.append({'case':case,'exit':result.returncode,'root_or_output_created':False})
        output=root/'already-used';output.mkdir();(output/'result.json').write_bytes(b'{"original":true}\n')
        result=subprocess.run([sys.executable,'-B',probe.__file__,'--mode','turn','--probe',str(root/'missing-probe'),'--output',str(output)],capture_output=True,timeout=10)
        assert result.returncode!=0 and b'FileExistsError' in result.stderr
        assert list(output.iterdir())==[output/'result.json'] and (output/'result.json').read_bytes()==b'{"original":true}\n'
        checks.append({'case':'duplicate-turn-output','original_bytes_unchanged':True,'ps_or_key_calls':0})
    owner={'processes':{'ideation_cli':{'pid':20,'started':'fixture-start','command':'/fixture/peer'}}}
    def fixture(has_child,index):
        rows={'20':{'observed_at':str(index),'name':'peer','command':'/fixture/peer','lstart':'fixture-start','parent_chain':[20,10], 'creator_evidence':'unit'}}
        if has_child:rows['30']={'observed_at':str(index),'name':'child','command':'/fixture/child --owned','lstart':'fixture-child-start','parent_chain':[30,20,10],'creator_evidence':'unit'}
        return {'status':'PASS','processes':rows,'observed_at':str(index),'missing':[]}
    observed=iter([fixture(False,1),fixture(True,2),fixture(False,3)])
    with patch.object(probe,'snapshot',side_effect=lambda *args:next(observed)), \
         patch.object(probe.time,'monotonic',side_effect=[0,0,.2,.4,.6,.8]),patch.object(probe.time,'sleep'):
        folder=args.output/'sampling-transport-fixture';folder.mkdir();probe.sample_for(owner,folder,.5)
    history=json.loads((folder/'summary.json').read_bytes())['process_lifetimes_observed']['30']
    assert history['appearance_observations']==['2'] and history['absence_observations']==['3'] and history['role_cli_descendant'] is True
    checks.append({'case':'appearance-absence-chain','scope':'explicit snapshot transport fixture','status':'PASS'})
    result={'status':'PASS','checks':checks,'scene_starts':0,'role_CLIs':0,'models':0,'ps_calls':0,'key_writes':0}
    with (args.output/'result.json').open('x',encoding='utf-8') as stream:stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'PASS','checks':len(checks),'scene_starts':0}));return 0


if __name__=='__main__':raise SystemExit(main())
