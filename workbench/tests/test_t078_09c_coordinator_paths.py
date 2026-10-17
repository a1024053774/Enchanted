"""Check actual coordinator helper-call construction for a relocated packet."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

import t078_09c_timed_run as candidate


class Captured(Exception):pass


def probes(Timed,root):
    packet=root/'separate-output/packet';packet.mkdir(parents=True)
    p1=root/'ideation-p1';executor=root/'executor-p1';output=root/'commands';output.mkdir()
    plan={'package':str(packet),'continued_demand_file':str(root/'demand.json'),'clock_origin_file':str(root/'clock.json')}
    captured={}
    value=SimpleNamespace(p1=p1,root=root,plan=plan,observe=lambda stage:({},b''))
    def first(label,argv):captured['permission']=str(argv[2]);raise Captured()
    value.run=first
    try:Timed.early(value)
    except Captured:pass
    assert 'permission' in captured
    for stage in ['C-I1','C-I2','C-I3','C-I4','C-E1']:
        folder=(executor if stage=='C-E1' else p1)/'phases'/stage/'armed-01';folder.mkdir(parents=True)
        (folder/'result.json').write_text('{"status":"ARMED"}',encoding='utf-8')
    value=SimpleNamespace(p1=p1,executor=executor,root=root,plan=plan,output=output,policy={},
        check_policy=lambda:None,permission_argv=lambda *a:[],run=lambda *a:None)
    def loading(name,path):captured['demand']=str(path);raise Captured()
    with patch.object(importlib.util,'spec_from_file_location',loading):
        try:Timed.execute(value)
        except Captured:pass
    assert 'demand' in captured
    expected={'permission':str(candidate.TICKET/'prepare-a14.py'),'demand':str(candidate.TICKET/'prepare-rev2-owner.py')}
    return [{'helper':key,'expected':path,'actual':captured[key],'actual_exists':Path(captured[key]).is_file(),
        'status':'PASS' if captured[key]==path else 'INCOMPLETE'} for key,path in expected.items()]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--known-bad-revision');args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False);Timed=candidate.Timed
    if args.known_bad_revision:
        filename='workbench/tests/t078_09c_timed_run.py'
        source=subprocess.check_output(['git','show',args.known_bad_revision+':'+filename],cwd=candidate.SOURCE)
        (args.output/'known-bad-coordinator.py').write_bytes(source)
        namespace={'__file__':str(candidate.SOURCE/filename),'__name__':'old_relocated_coordinator'}
        exec(compile(source,str(candidate.SOURCE/filename),'exec'),namespace);Timed=namespace['Timed']
    with tempfile.TemporaryDirectory(prefix='t078-coordinator-path-',dir='/private/tmp') as temporary:
        checks=probes(Timed,Path(temporary))
    result={'status':'PASS' if all(v['status']=='PASS' for v in checks) else 'INCOMPLETE',
        'scope':__doc__,'checks':checks,'known_bad_revision':args.known_bad_revision,
        'boundary':'permission first helper argv and demand module load only; business transport replaced by explicit no-action spies',
        'scene_process_starts':0,'key_writes':0,'temporary_root_removed':True}
    candidate.save(args.output/'result.json',result);print(json.dumps(result,ensure_ascii=False))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
