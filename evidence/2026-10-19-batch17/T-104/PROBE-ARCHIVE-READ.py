"""执行 RUN-SUITE 的实际变异效果查询，仅读已停止并归档的 review-fix-01。"""
import ast
import json
from pathlib import Path
import sqlite3
import sys

folder=Path(__file__).resolve().parent
source=(folder/'RUN-SUITE.py').read_text(encoding='utf-8')
tree=ast.parse(source)
node=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and
          ast.get_source_segment(source,n).startswith("if expected and case in ('input-events-mutant', 'restart-mutant')"))
run=Path('/Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-104/review-fix-01-backend')
row=json.loads((folder/'review-fix-01-backend/input-events-mutant.json').read_text(encoding='utf-8'))
db=run/'input-events-mutant/state/state.sqlite3'
report=dict(status='INCOMPLETE',scope='原 RUN-SUITE 查询块与实际归档数据库',database=str(db),exists=db.is_file(),bytes=db.stat().st_size,
            wal_exists=Path(str(db)+'-wal').exists(),shm_exists=Path(str(db)+'-shm').exists(),
            header_versions=list(db.read_bytes()[18:20]))
context=dict(sqlite3=sqlite3,run=run,case='input-events-mutant',expected=True,checks=[{}],row=row,Path=Path)
try:
    exec(compile(ast.Module(body=[node],type_ignores=[]),'RUN-SUITE-effect-query','exec'),context)
    assert context['checks'][-1]['expected'] and context['checks'][-1]['counterexample_effect']
    report.update(status='PASS',effect=context['checks'][-1]['counterexample_effect'])
except (sqlite3.Error,AssertionError) as error:
    report.update(error=repr(error))
with Path(sys.argv[1]).open('x',encoding='utf-8') as output:
    json.dump(report,output,ensure_ascii=False,indent=2);output.write('\n')
print(json.dumps(report,ensure_ascii=False))
raise SystemExit(0 if report['status']=='PASS' else 1)
