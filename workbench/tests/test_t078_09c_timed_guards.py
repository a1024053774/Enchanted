"""Check timed-coordinator validation and duplicate-entry refusal without a scene."""
import argparse
import copy
import json
from pathlib import Path
import runpy
import sys
import tempfile
from unittest.mock import patch

import t078_09c_timed_run as timed
import t078_09c_driver as c

BASE = timed.SOURCE/'evidence/2026-10-11-batch13/T-078'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    flow=BASE/'09c-fix-01/real-chain-outside-03/flow'
    dispatch=json.loads((flow/'ideation-p1/phases/C-I3/dispatch-01/result.json').read_bytes())
    review=flow/'ideation-p1/phases/C-I3/execute-02-review'
    template=json.loads((review/'template.json').read_bytes());original=(review/'screen.bin').read_bytes()
    start=json.loads((flow/'clock-origin.json').read_bytes())
    inp=json.loads((flow/'ideation-p1/input.json').read_bytes())
    role=template['binding'];stop={**start['stop']}
    plan={'source':str(timed.SOURCE),'node':role['argv'][0],'source_revision':role['source_revision'],
          'package':role['package'],'roles':{'ideation':inp},'target_identity':role['target'],
          'target_binding':{'thread_id':role['target']['thread_id']}}
    checks=[]
    cases=['recorded-positive','command-extra','wrong-thread','wrong-stop','wrong-request','wrong-seq','wrong-tool',
           'wrong-target','wrong-selected-line','truncated-capture']
    for label in cases:
        item=copy.deepcopy(template);body=original;capture=copy.deepcopy(item['screen_capture'])
        if label=='command-extra':item['binding']['command']+=' ; echo unexpected'
        if label=='wrong-thread':item['binding']['thread']='other-thread'
        if label=='wrong-stop':item['binding']['stop']['id']='other-stop'
        if label=='wrong-request':item['binding']['stop']['request_id']='other-request'
        if label=='wrong-seq':item['binding']['global_seq']+=1
        if label=='wrong-tool':item['binding']['tool_use_id']='other-tool'
        if label=='wrong-target':item['binding']['target']['thread_id']='other-target'
        if label=='wrong-selected-line':item['selected_line']='❯ 2. Yes'
        if label=='truncated-capture':body=body[:-1]
        error=None
        with patch.object(c,'original_send',return_value=(stop,{'request_id':stop['request_id']},None)):
            try:timed.verify_template(plan,'C-I3',dispatch,item,body,capture,start)
            except ValueError as caught:error=str(caught)
        assert (error is None)==(label=='recorded-positive'),(label,error)
        checks.append({'case':label,'status':'PASS','error':error,'key_calls':0})
    # Known-bad counterfactual: omitting the boundary validator accepts a changed
    # target. A sentinel demonstrates why success from a mocked gate is insufficient.
    bad=copy.deepcopy(template);bad['binding']['target']['thread_id']='other-target'
    key_spy=[]
    with patch.object(timed,'verify_template',return_value=None):
        timed.verify_template(plan,'C-I3',dispatch,bad,original,bad['screen_capture'],start);key_spy.append('would Enter')
    assert key_spy==['would Enter']
    checks.append({'case':'mutant-validator-removed','status':'PASS','known_bad_observed':'RED','unapproved_target_would_reach_Enter':True})
    with tempfile.TemporaryDirectory(prefix='t078-timed-duplicate-',dir='/private/tmp') as name:
        output=Path(name)/'existing';output.mkdir();raw=b'{"status":"INCOMPLETE","sentinel":"preserve"}\n';(output/'result.json').write_bytes(raw)
        argv=['timed','--signature-ref','test only']
        for key in ['plan','stage-a','ideation','executor','build','preapproval']:argv+=['--'+key,str(Path(name)/'missing')]
        argv+=['--output',str(output)];calls=[]
        def forbidden(*a,**k):calls.append('process/window');raise AssertionError('duplicate must not start')
        with patch.object(sys,'argv',argv),patch('subprocess.run',forbidden),patch('subprocess.Popen',forbidden),patch('electron_client.ElectronClient',forbidden):
            try:runpy.run_path(str(Path(timed.__file__)),run_name='__main__')
            except FileExistsError:pass
            else:raise AssertionError('duplicate output accepted')
        assert (output/'result.json').read_bytes()==raw and not calls
        checks.append({'case':'duplicate-entry','status':'PASS','bytes_unchanged':True,'process_window_key_calls':0})
    result={'status':'PASS','scope':__doc__,'checks':checks,'models':0,'live_phase_execution':'NOT_RUN',
            'known_bad_scope':'guard counterfactual only; no live transport is mocked into success'}
    timed.save(args.output/'result.json',result);print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
