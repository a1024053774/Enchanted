#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json,subprocess,sys
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='9c29ec7d';check_only='--check-only' in sys.argv[1:]
allow=json.loads((base/'09b-newline-allowlist.json').read_bytes());future={str(base/'09b-newline-ownership-preflight-01.json')}
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD').startswith(before) and not git('diff','--cached','--name-only')
rows=[];bad=[]
for item in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
 if item:
  path=item[3:];owner=next((p for p in allow if path==p or path.startswith(p+'/')),None);rows.append({'path':path,'status':'PASS' if owner else 'INCOMPLETE','allowlist_entry':owner});bad += [] if owner else [path]
assert not bad,('Unowned work; no mutation',bad)
first=[p for p in allow if p not in future];missing=[p for p in first if not Path(p).exists()];assert not missing,('Allowlist path missing before git add',missing)
red=json.loads((base/'09b-newline-red-02/results.json').read_bytes());green=json.loads((base/'09b-newline-green-01/results.json').read_bytes());assert red['status']=='PASS' and green['status']=='PASS'
assert any(c['name']=='trimmed-final-newline-blocked-before-fix' and c['status']=='PASS' for c in red['checks'])
assert all(c['status']=='PASS' for c in green['checks']) and any(c['name']=='middle-text-mutation-blocked' for c in green['checks'])
assert (base/'09b-a08-newline-analysis.md').is_file() and (base/'09b-a08-i1-materials-01/execute-01/result.json').is_file()
template=json.loads((base/'stage-b-a08-ideation-approval-template.json').read_bytes());assert len(template['screen_approvals'])==6 and template['tool_approval']['one_time'] is True
subprocess.run(['git','diff','--check'],check=True);ownership=base/'09b-newline-ownership-preflight-01.json'
if check_only:
 ex=json.loads(ownership.read_bytes());assert ex['status']=='PASS' and ex['unowned']==[];print(json.dumps({'status':'PASS','mode':'check-only','head':git('rev-parse','HEAD'),'cached_paths':0,'checked_paths':len(rows),'unowned':bad}));raise SystemExit(0)
ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':bad,'entries':rows},ensure_ascii=False,indent=2)+'\n')
with (base/'RESULTS.md').open('a',encoding='utf-8') as fh:fh.write('\n## A-08 registration newline normalization\n\n实测 A-08 UserPromptSubmit trace 的 prompt 没有末尾换行，而旧 dispatch registration 保留 prompt 文件尾换行，导致 exact block。产品登记现在只去除末尾 CR/LF，内部正文仍逐字比较；真实 signal 红/绿与中间正文变异反例均保留。A-08 active 的合法收回仅是认证窗口用户 Esc/声明路径；本轮不操作现场，等待 A-09 裁定。\n')
subprocess.run(['git','add','--',*first,str(ownership)],check=True);subprocess.run(['git','commit','-m','fix(T-078): canonicalize registered prompt line endings'],check=True);assert not git('status','--porcelain');print(json.dumps({'status':'PASS','launch':'NO_GO'}))
PY
