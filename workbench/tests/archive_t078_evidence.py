#!/usr/bin/env python3
"""Move this card's >5 MiB evidence to the approved mounted external volume.

No hashes, compression, overwrites, or automatic recovery. Delete the local
original only after a byte-for-byte readback and a new local summary succeed.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import uuid

ROOT=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
LOCAL=ROOT/'evidence/2026-10-11-batch13/T-078'
VOLUME=Path('/Volumes/WD-Elements')
ARCHIVE=VOLUME/'a2a-evidence/2026-10-11-batch13/T-078'
LIMIT=5*1024*1024

parser=argparse.ArgumentParser()
parser.add_argument('--labels',nargs='+',required=True)
parser.add_argument('--dry-run',action='store_true')
args=parser.parse_args()
selected=[]
for label in args.labels:
    if not label or label in ('.','..') or any(char not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for char in label):
        parser.error('Each label must be one directory name')
    directory=LOCAL/label
    if directory.resolve()!=directory or not directory.is_dir():
        raise RuntimeError('Evidence directory is missing or linked: '+str(directory))
    for source in sorted(directory.rglob('*')):
        if source.is_symlink():raise RuntimeError('Evidence links require inspection: '+str(source))
        if source.is_file() and source.stat().st_size>LIMIT:
            selected.append((source,ARCHIVE/source.relative_to(LOCAL)))
if args.dry_run:
    print(json.dumps({'dry_run':True,'files':[{'source':str(a),'destination':str(b),'bytes':a.stat().st_size} for a,b in selected]},ensure_ascii=False,indent=2))
    raise SystemExit(0)
if not os.path.ismount(VOLUME) or VOLUME.resolve()!=VOLUME:
    raise RuntimeError('External volume is not mounted; no fallback')
manifest={'status':'INCOMPLETE','labels':args.labels,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':[]}
manifest_path=LOCAL/('external-archive-'+uuid.uuid4().hex+'.json')
with manifest_path.open('x',encoding='utf-8') as out:json.dump(manifest,out,ensure_ascii=False,indent=2)
for source,destination in selected:
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.parent.resolve()!=destination.parent:raise RuntimeError('Archive directory is linked')
    size=source.stat().st_size
    summary={'source':str(source),'archive':str(destination),'bytes':size,
             'rule':'主控 #37：原始单文件超过 5 MiB 时统一外置盘归档，压缩不改变规则。',
             'source_snapshot':str(source.parent/'sources.tar.gz')}
    if source.suffix=='.json':
        record=json.loads(source.read_text(encoding='utf-8'))
        if isinstance(record,dict):
            for key in ['status','task','worker','ready_rev','tests_run','failures','errors','skipped','exit_code','test_phase_status','suite','argv','original_source','limitations']:
                if key in record:summary[key]=record[key]
            summary['replay_note']='使用源快照中的版本和 argv；--output 与 --label 必须改为新的证据目录，不能覆盖旧结果。'
    with source.open('rb') as src,destination.open('xb') as dst:
        shutil.copyfileobj(src,dst,1024*1024);dst.flush();os.fsync(dst.fileno())
    with source.open('rb') as src,destination.open('rb') as dst:
        while True:
            a,b=src.read(1024*1024),dst.read(1024*1024)
            if a!=b:raise RuntimeError('Archive readback differs; local original retained')
            if not a:break
    if source.stat().st_size!=size or destination.stat().st_size!=size:
        raise RuntimeError('Evidence changed while archiving; local original retained')
    summary['byte_readback']='PASS'
    sidecar=source.with_name(source.stem+'.summary.json')
    with sidecar.open('x',encoding='utf-8',newline='\n') as out:
        json.dump(summary,out,ensure_ascii=False,indent=2);out.write('\n')
    source.unlink()
    manifest['files'].append({**summary,'summary':str(sidecar),'local_original_removed':True})
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest['status']='PASS'
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','manifest':str(manifest_path),'archived':len(manifest['files'])},ensure_ascii=False))
