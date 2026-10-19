"""只读既有真实现场：在修改产品前保存 R1 与重启漏检的反例。"""
import json
from pathlib import Path
import sqlite3
import sys

base=Path('/Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-104')
report=dict(status='NO_GO',target='d54826223194b56ca057b8ab3213729c9e53a29a',checks=[])
with sqlite3.connect(f'file:{base / "ui-01/ui/fixture/state/state.sqlite3"}?mode=ro',uri=True) as db:
    rows=db.execute("SELECT e.seq,e.type,e.launch,e.data FROM orchestration_events e JOIN launch_records l ON l.id=e.launch "
                    "WHERE json_extract(l.data,'$.role')='shell' AND e.type='window_request_admitted' ORDER BY e.seq").fetchall()
    report['checks'].append(dict(case='R1',expected='shell 逐次输入事件数为 0',observed=len(rows),
                                 rejected=bool(rows),rows=[dict(seq=s,type=t,launch=l,data=json.loads(d)) for s,t,l,d in rows]))
with sqlite3.connect(f'file:{base / "review-outside-01/restart-mutant/state/state.sqlite3"}?mode=ro',uri=True) as db:
    boundary=db.execute("SELECT min(seq) FROM orchestration_events WHERE type='daemon_stopped'").fetchone()[0]
    rows=db.execute("SELECT seq,launch,data FROM orchestration_events WHERE type='shell_created' AND seq>? ORDER BY seq",(boundary,)).fetchall()
    report['checks'].append(dict(case='R2',expected='第一次 daemon_stopped 后新建 shell 数为 0',observed=len(rows),
                                 rejected=bool(rows),rows=[dict(seq=s,launch=l,data=json.loads(d)) for s,l,d in rows]))
assert all(row['rejected'] for row in report['checks']), '归档未重现预期缺陷，不得记为红态'
with Path(sys.argv[1]).open('x',encoding='utf-8') as output:
    json.dump(report,output,ensure_ascii=False,indent=2);output.write('\n')
print(json.dumps(report,ensure_ascii=False))
raise SystemExit(1)
