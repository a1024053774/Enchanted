#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json,subprocess,sys
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='3aeed23c';check_only='--check-only' in sys.argv[1:]
allow=json.loads((base/'09b-a09-queue-allowlist.json').read_bytes());future={str(base/'09b-a09-queue-ownership-preflight-01.json')}
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD').startswith(before) and not git('diff','--cached','--name-only')
rows=[];bad=[]
for item in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if item:
  path=item[3:];owner=next((p for p in allow if path==p or path.startswith(p+'/')),None);rows.append({'path':path,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner});bad += [] if owner else [path]
assert not bad,('Unowned work; no mutation',bad)
first=[p for p in allow if p not in future];missing=[p for p in first if not Path(p).exists()];assert not missing,('Allowlist path missing before git add',missing)
source=Path('workbench/src/store.ts').read_text(encoding='utf-8');assert 'canonicalText = text.replace(/[\\r\\n]+$/, "")' in source
red=json.loads((base/'09b-newline-red-02/results.json').read_bytes());green=json.loads((base/'09b-newline-green-01/results.json').read_bytes());spy=json.loads((base/'09b-newline-spy-a09-01/results.json').read_bytes());assert red['status']=='PASS' and green['status']=='PASS' and spy['status']=='PASS' and len(spy['checks'])==9
old=json.loads((base/'09b-a09-i1-materials-01/execute-01/result.json').read_bytes());assert old['status']=='INCOMPLETE' and old.get('error')
command=(base/'09b-a09-i1-materials-01/I1-COMMAND.txt').read_text(encoding='utf-8');assert '--resume-queued' in command and 'execute-02' in command
assert (base/'09b-a09-queue-recovery-analysis.md').is_file()
subprocess.run(['git','diff','--check'],check=True);ownership=base/'09b-a09-queue-ownership-preflight-01.json'
if check_only:
 ex=json.loads(ownership.read_bytes());assert ex['status']=='PASS' and ex['unowned']==[];print(json.dumps({'status':'PASS','mode':'check-only','head':git('rev-parse','HEAD'),'cached_paths':0,'checked_paths':len(rows),'unowned':bad}));raise SystemExit(0)
ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':bad,'entries':rows},ensure_ascii=False,indent=2)+'\n')
with (base/'RESULTS.md').open('a',encoding='utf-8') as fh:fh.write('\n## A-09 queued I1 recovery\n\n登记只移除末尾 CR/LF；真实 signal 红绿和 A-09 spy 通过。产品没有 queued cancel API；新增 --resume-queued 只读 pane_status/orchestration_events，核对真实 id/seq/原文后写登记并 release，不重新派发或伪造字段。A-09 execute-01 红态保留，execute-02 命令等待主控裁定。\n')
subprocess.run(['git','add','--',*first,str(ownership)],check=True);subprocess.run(['git','commit','-m','test(T-078): prepare queued A09 I1 recovery'],check=True);assert not git('status','--porcelain');print(json.dumps({'status':'PASS','launch':'NO_GO'}))
PY
