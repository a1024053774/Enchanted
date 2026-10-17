"""Prepare only the recorded single-role probe's empty raw trees and redaction inventory; no stop."""
import argparse
import json
import os
from pathlib import Path
import sys
import traceback

SOURCE=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE/'workbench/tests'))
from t078_raw_retention import read_json,save,check_identities,NativeRuntime,require


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    result={'status':'BLOCKED','signals_sent':[],'key_writes':0,'directories_created':[]}
    try:
        owner=read_json(HERE/'probe-closeout/owner.json');root=Path(owner['root'])
        require(str(root)=='/private/tmp/t078-2-a14-rehearsal-i4jb8gm3','fixed probe root')
        helpers=check_identities(owner,NativeRuntime(owner))
        # No records are invented. A never-used API has no HTTP directory yet.
        for role in ['ideation','executor']:
            for name in ['http-exchanges','hooks']:
                path=root/'roles'/role/name
                if not path.exists():path.mkdir();result['directories_created'].append(str(path))
                require(path.is_dir() and not path.is_symlink(),'regular raw tree')
        credential=read_json(root/'operator.json');values=[credential['token'],credential['epoch']]
        target=root/'retention-secrets.json'
        if target.exists():require(not target.is_symlink() and read_json(target)==values,'existing inventory changed')
        else:
            with target.open('x',encoding='utf-8') as stream:os.chmod(target,0o600);json.dump(values,stream)
        result.update(status='PASS',allowed_helpers=helpers,secret_values_recorded=False,
            scope='validated original seven PIDs/receipts; no scene control; inventory stays in root only')
    except Exception as error:result.update(error=repr(error),traceback=traceback.format_exc())
    save(a.output/'result.json',result);print(json.dumps({'status':result['status'],'signals_sent':[]}));return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
