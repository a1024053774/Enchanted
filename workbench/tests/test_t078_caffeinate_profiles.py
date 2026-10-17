"""Original seven/nine receipt profiles and auxiliary cleanup ordering; no live processes."""
import copy
import json
from pathlib import Path
import tempfile
import argparse
import traceback
import t078_raw_retention as raw
import t078_09c_driver as c
from t078_rev2_tools_cases import fixture,Lifecycle

SOURCE=Path(__file__).resolve().parents[2];BASE=SOURCE/'evidence/2026-10-11-batch13/T-078'


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
    result={'status':'INCOMPLETE','scope':__doc__,'scene_starts':0};checks=[]
    try:
        owner=raw.read_json(BASE/'09c-caffeinate-fix-01/probe-closeout/owner.json')
        class Runtime:
            def identities(self):return copy.deepcopy(owner['processes'])
            def topology(self):return []
        raw.check_identities(owner,Runtime());checks.append('original seven-process probe receipts accepted')
        wrong={**owner,'scene':'09C'}
        try:raw.check_identities(wrong,Runtime())
        except (ValueError,KeyError):checks.append('seven probe cannot substitute for nine scene')
        else:raise AssertionError('seven probe accepted as 09C')
        with tempfile.TemporaryDirectory(prefix='t078-C-owner-kind-',dir='/private/tmp') as tmp:
            root=Path(tmp);path=root/'owner.json';raw.save(path,owner)
            runtime=c.NativePermission({'root':str(root),'scene':'09C','owner_file':str(path),'roles':{'ideation':{}}},'C-I3',None)
            try:runtime.actual()
            except ValueError as error:assert str(error)=='C_nine_process_scene_required'
            else:raise AssertionError('09C permission admitted probe profile')
            checks.append('actual NativePermission rejects probe profile before process/window calls')
        for failure in [False,True]:
            folder=a.output/('helper-hangs' if failure else 'helper-exits');folder.mkdir()
            root,owner,stage,capture,approval,independent=fixture(folder)
            class HelperLife(Lifecycle):
                def topology(self):return [{'pid':99,'started':'fixture-helper','command':'caffeinate -i -t 300','executable':'/usr/bin/caffeinate'}]
                def wait_helpers_absent(self,helpers,seconds):
                    self.calls.append('auxiliary-exit-confirmation')
                    if failure:raise ValueError('auxiliary_exit_unconfirmed')
            life=HelperLife(owner)
            finished=raw.finish(owner,approval,capture,independent,folder/'cleanup',life)
            if failure:assert finished['status']=='BLOCKED' and root.exists() and life.calls==['daemon_stop','auxiliary-exit-confirmation']
            else:assert finished['status']=='PASS' and not root.exists() and life.calls==['daemon_stop','auxiliary-exit-confirmation','SIGTERM:ideation_api','SIGTERM:executor_api']
            if root.exists():
                import shutil
                shutil.rmtree(root)  # This explicit metadata-only fixture has no processes.
            checks.append('auxiliary unconfirmed blocks API signals/delete' if failure else 'auxiliary exit confirmed before API cleanup/delete')
        result.update(status='PASS',checks=checks)
    except Exception as error:result.update(error=repr(error),traceback=traceback.format_exc())
    raw.save(a.output/'result.json',result);print(json.dumps({'status':result['status'],'checks':len(checks),'error':result.get('error')}));return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
