"""Outside-only external facts startup check. No auth, CLI, service or model."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import uuid

SOURCE=Path(__file__).resolve().parents[1]/'src/claudeLoginSession.py'
spec=importlib.util.spec_from_file_location('facts_entry',SOURCE)
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)


def main():
    runtime.require_safe_python()
    runtime.validate_bootstrap()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    for path in (args.audit,args.output):
        if path.parent!=Path('/private/tmp') or path.resolve()!=path or os.path.lexists(path):
            parser.error('select new canonical paths directly under /private/tmp')
    args.audit.mkdir(mode=0o700)
    ledger=args.audit/'forwarder/journal/requests.jsonl';ledger.parent.mkdir(parents=True,mode=0o700)
    with ledger.open('x',encoding='utf-8') as stream:
        for sequence in (1,2):stream.write(json.dumps({'kind':'request','sequence':sequence,'method':'POST','path':'/v1/messages'})+'\n')
    runtime.save(args.audit/'facts.json',{'schema':2,'ledger':'forwarder/journal/requests.jsonl',
        'scope':'synthetic external facts V startup only; no auth or model permission',
        'fixture_nonce':str(uuid.uuid4()),'forwarder':{'received':2},'inventory':{'pass_condition':False,'changed':[]},'counts':{}})
    descriptor=os.open(args.output,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:os.dup2(descriptor,1)
    finally:os.close(descriptor)
    # Same PID enters the actual external facts entry. That entry applies V
    # once and execs Node; no unprotected supervisor or nested profile exists.
    sys.argv=[str(SOURCE),'--stage','facts','--audit',str(args.audit)]
    runtime.main()


if __name__=='__main__':
    try:main()
    except Exception:
        sys.stderr.write('external_facts_fixture_setup_failed\n')
        raise SystemExit(2)
