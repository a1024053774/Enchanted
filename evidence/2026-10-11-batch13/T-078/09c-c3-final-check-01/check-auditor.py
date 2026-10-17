"""Reject corrupted evidence in the same readback function; no scene writes."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('C3_audit',HERE/'readback.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    out=args.output.resolve();out.mkdir(exist_ok=False)
    owner=json.loads(audit.OWNER.read_bytes());base=audit.Reader(owner);checks=[]
    original=audit.inspect(base);require=lambda ok: audit.require(ok,'known_bad_must_be_rejected')
    try:
        for case,reason in [('extra_POST','actual_POST_budget'),('double_Esc','exactly_one_Esc'),
            ('ack_added','original_stop_no_ack'),('early_emergency','real_event_age_gt120_lt150'),
            ('truncated_screen','complete_permission_screen'),('clock_jump','recorded_clock_arithmetic'),('HTTP409','actual_HTTP_success')]:
            class Changed:
                def __init__(self):
                    self.rows=copy.deepcopy(base.rows);self.names=set(base.names)
                    if case=='extra_POST':self.names.add('roles/ideation/http-exchanges/9999.request.bin')
                    if case=='ack_added':self.rows['inbox_records'].append({'id':'known-bad-ack','data':json.dumps({'id':'known-bad-ack','kind':'ack','reply_to':original['stop']['id']})})
                    if case=='early_emergency':
                        for row in self.rows['events']:
                            if row['type']=='emergency_interrupt_requested':row['time']=original['stop']['created_at']
                def __getattr__(self,name):return getattr(base,name)
                def raw(self,name):
                    data=base.raw(name)
                    if case=='double_Esc' and name=='target/received.bin':return data+b'\x1b'
                    if case=='HTTP409' and name=='roles/ideation/http-exchanges/0001.meta.json':
                        value=json.loads(data);value['status']=409;return json.dumps(value).encode()
                    return data
                def source(self,name):
                    data=base.source(name)
                    if case=='truncated_screen' and Path(name)==audit.P1/'phases/C-I1/dispatch-01/result.json':
                        value=json.loads(data);value['permission_screen_capture']['complete']=False;return json.dumps(value).encode()
                    if case=='clock_jump' and Path(name)==audit.P1/'phases/C-I3/execute-02/result.json':
                        value=json.loads(data);value['enter_at']['monotonic_ms']+=2000;return json.dumps(value).encode()
                    return data
                def json_source(self,name):return json.loads(self.source(name))
            try:audit.inspect(Changed())
            except AssertionError as error:require(reason in str(error));checks.append({'case':case,'status':'PASS','known_bad':'REJECTED','reason':str(error)})
            else:raise AssertionError('known bad accepted:'+case)
        value={'status':'PASS','checks':checks,'scene_processes_started':0,'keys':0,'signals':0,
            'scope':'evidence transport mutations; not reviewer product mutants or independent acceptance'}
        audit.write(out/'result.json',value);print(json.dumps({'status':'PASS','checks':len(checks)}))
    finally:base.close()


if __name__=='__main__':main()
