#!/bin/bash
# 主控 #24：后台包括逐次输入事件变异和自动重启变异，再跑真实界面。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t104
LABEL=${1:?传入新编号，例如 review-fix-01}
case "$LABEL" in *[!A-Za-z0-9_-]*|'') exit 2;; esac
bash evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-06-UI.sh "$LABEL"
python3 - "$LABEL" <<'PY'
import json
from pathlib import Path
import sys
folder=Path('evidence/2026-10-19-batch17/T-104');label=sys.argv[1]
backend=json.loads((folder/(label+'-backend')/'suite.json').read_text(encoding='utf-8'))
ui=json.loads((folder/(label+'-summary.json')).read_text(encoding='utf-8'))
assert backend['status']==ui['status']=='PASS'
cases={row['case']:row for row in backend['checks']}
assert len(cases)==10 and all(row['expected'] for row in cases.values())
for name in ['input-events-mutant','restart-mutant']:
 assert cases[name]['exit']==1 and cases[name]['counterexample_effect'], '变异未生效或未被拒绝：'+name
assert cases['metadata-known-bad']['exit']==1 and cases['candidate']['exit']==0
report=dict(status='PASS',task='T-104',attempt='a1',base_revision=ui['revision'],
            backend_summary=str(folder/(label+'-backend')/'suite.json'),ui_summary=str(folder/(label+'-summary.json')),
            mutations={name:cases[name] for name in ['input-events-mutant','restart-mutant']},
            independent_review='修复后独立复审尚未运行')
with (folder/(label+'-review-fixes.json')).open('x',encoding='utf-8') as file:
 json.dump(report,file,ensure_ascii=False,indent=2);file.write('\n')
print(json.dumps(report,ensure_ascii=False))
PY
