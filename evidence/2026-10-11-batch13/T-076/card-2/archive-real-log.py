"""Controller-only move of the single oversized, already compressed owned log."""
import argparse
import json
import os
from pathlib import Path
import shutil

CARD=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); args.output.mkdir(parents=True,exist_ok=False)
    source=CARD / 'outside-real-delivery-02/commands.jsonl.gz'
    target=Path('/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-076/card-2/outside-real-delivery-02/commands.jsonl.gz')
    report=dict(status='INCOMPLETE',source=str(source),archive=str(target),byte_readback=False,source_removed=False)
    try:
        if not Path('/Volumes/WD-Elements').is_mount(): raise RuntimeError('External disk is not mounted; no fallback.')
        if source.is_symlink() or not source.is_file() or target.exists(): raise RuntimeError('Unexpected source or preexisting archive; preserve and stop.')
        size=source.stat().st_size
        if size!=48122290: raise RuntimeError('Owned log size changed; stop before copying.')
        target.parent.mkdir(parents=True,exist_ok=True)
        with source.open('rb') as src,target.open('xb') as dst:
            shutil.copyfileobj(src,dst); dst.flush(); os.fsync(dst.fileno())
        with source.open('rb') as src,target.open('rb') as dst:
            while True:
                a,b=src.read(1024*1024),dst.read(1024*1024)
                if a!=b: raise RuntimeError('Archive byte readback differs; retain source.')
                if not a: break
        report['byte_readback']=True
        pointer=source.with_name(source.name+'.pointer.json')
        with pointer.open('x',encoding='utf-8') as stream:
            json.dump(dict(archive=str(target),bytes=size,compression='gzip',byte_readback=True,
                original_report='run.json (preserved INCOMPLETE/archive_required)',
                replay='gzip -dc '+str(target)),stream,indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        source.unlink(); report.update(status='PASS',bytes=size,source_removed=True,pointer=str(pointer))
        report['oversize_files']=[str(p) for p in CARD.rglob('*') if p.is_file() and p.stat().st_size>5*1024*1024]
        if report['oversize_files']: report.update(status='INCOMPLETE',error='Other oversized evidence remains.')
    except Exception as error: report['error']=repr(error)
    (args.output / 'run.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report)); return 0 if report['status']=='PASS' else 1


if __name__=='__main__': raise SystemExit(main())
