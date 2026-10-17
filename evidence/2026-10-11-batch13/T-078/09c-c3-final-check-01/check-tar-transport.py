"""Synthetic in-memory archive IO only; never captures the live C3 root."""
import argparse
import importlib.util
import io
import json
from pathlib import Path
import tarfile
from unittest.mock import patch

HERE=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    spec=importlib.util.spec_from_file_location('tar_reader',HERE/'readback.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    owner={'root':'/private/tmp/UNIT-ONLY-not-a-scene','source_revision':'0'*40,'target_binding':{},'processes':{},'roles':{},'process_graph':{}}
    boundary=Path('/UNIT-ONLY/task-boundary.json')
    fields={'snapshot.json':{'root':owner['root'],'source_revision':owner['source_revision'],'records':[{'source':str(boundary),'logical':'evidence/0/task-boundary.json'}]},
        'identity-receipts.json':owner,'live-rows.json':{},'files/evidence/0/task-boundary.json':{'unit_only':True}}
    native_open=tarfile.open;checks=[]
    for case in ['valid','wrong_root','duplicate_member']:
        stream=io.BytesIO()
        with native_open(fileobj=stream,mode='w:gz') as tar:
            for name,value in list(fields.items())+([('snapshot.json',fields['snapshot.json'])] if case=='duplicate_member' else []):
                raw=json.dumps(value).encode();entry=tarfile.TarInfo(name);entry.size=len(raw);tar.addfile(entry,io.BytesIO(raw))
        payload=stream.getvalue();handles=[]
        def opened(*_,**__):
            handle=native_open(fileobj=io.BytesIO(payload),mode='r:gz');handles.append(handle);return handle
        with patch.object(m.tarfile,'open',opened),patch.object(m.sqlite3,'connect',side_effect=AssertionError('archive must not open SQLite')):
            try:reader=m.Reader(dict(owner,root='/different') if case=='wrong_root' else owner,Path('/UNIT-ONLY/archive.tar.gz'),boundary)
            except AssertionError as error:
                assert str(error)==('archive_binding' if case=='wrong_root' else 'safe_unique_archive_members')
            else:
                assert case=='valid' and reader.task_boundary=={'unit_only':True};reader.close()
        assert handles and all(handle.closed for handle in handles),'archive handle leak'
        checks.append({'case':case,'status':'PASS','handles_closed':True})
    m.write(a.output,{'status':'PASS','checks':checks,'scope':'synthetic IO only; actual C3 archive capture/readback NOT RUN',
        'SQLite_reads':0,'scene_actions':0,'actual_archives_created':0})
    print(json.dumps({'status':'PASS','checks':len(checks),'scene_actions':0}))


if __name__=='__main__':main()
