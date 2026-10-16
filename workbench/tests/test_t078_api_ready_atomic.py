"""Observe actual API main's readiness publication without opening a socket."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
import t078_09b_fake_api as api


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--expect',choices=['red','green'],required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(exist_ok=False);rows=[]
    for existing in [False,True]:
        with tempfile.TemporaryDirectory(prefix='t078-ready-',dir='/private/tmp') as folder:
            root=Path(folder);ready=root/'api-ready.json';old=b'{"original":"preserve"}\n'
            if existing:ready.write_bytes(old)
            observed=[];original_open=Path.open
            class Writer:
                def __init__(self,stream):self.stream=stream
                def __enter__(self):return self
                def __exit__(self,*a):self.stream.close()
                def __getattr__(self,k):return getattr(self.stream,k)
                def write(self,value):
                    if not existing and ready.exists():
                        with original_open(ready,'rb') as stream:observed.append(stream.read())
                    return self.stream.write(value)
            def opened(path,*a,**kw):
                stream=original_open(path,*a,**kw)
                mode=a[0] if a else kw.get('mode','r')
                return Writer(stream) if 'w' in mode or 'x' in mode else stream
            class Server:
                server_port=34567
                def __init__(self,*a):pass
                def serve_forever(self):pass
                def server_close(self):pass
            duplicate=False
            try:
                with patch.object(sys,'argv',['api','--root',str(root),'--role','ideation','--protocol']),patch.object(api,'ThreadingHTTPServer',Server),patch.object(api.signal,'signal'),patch.object(Path,'open',opened):
                    api.main()
            except FileExistsError:duplicate=True
            passed=(duplicate and ready.read_bytes()==old) if existing else (not observed and json.loads(ready.read_bytes())['port']==34567)
            rows.append({'name':'existing-ready' if existing else 'partial-ready','desired_contract_passed':passed,
                         'partial_observations':len(observed),'duplicate_rejected':duplicate,'sockets':0})
    ok=all(row['desired_contract_passed'] if args.expect=='green' else not row['desired_contract_passed'] for row in rows)
    result={'status':'PASS' if ok else 'INCOMPLETE','expected':args.expect,'checks':rows,'scope':__doc__,'process_starts':0}
    (args.output/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result));return 0 if ok else 1


if __name__=='__main__':raise SystemExit(main())
