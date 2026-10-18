#!/usr/bin/env python3
"""离线核对绿态脚本接线；Herdr/Codex 和操作者确认都是显式替身。"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("controlled_probe", HERE / "controlled-panel-probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
root = Path(tempfile.mkdtemp(prefix="t095-green-wire-", dir="/tmp"))
inputs = json.loads((HERE / "real-panel-inputs.json").read_text(encoding="utf-8"))
(root / "inputs.json").write_text(json.dumps(inputs), encoding="utf-8")
(root / "phase").write_text("startup", encoding="utf-8")
(root / "auth.json").write_text("{}", encoding="utf-8")
(root / "bin").mkdir()
fake = '''import json, os, pathlib, sys
p=pathlib.Path(os.environ['T095_WIRE_ROOT']); a=sys.argv[1:]
with (p/'calls.jsonl').open('a') as f: f.write(json.dumps([pathlib.Path(sys.argv[0]).name,*a])+'\\n')
if pathlib.Path(sys.argv[0]).name=='codex':
    assert a==['--version']; print('codex-cli 0.163.0'); sys.exit(0)
phase=(p/'phase').read_text(); inputs=json.loads((p/'inputs.json').read_text())
def emit(value): print(json.dumps({'result':value}))
if a==['status']: print('explicit fake Herdr 0.9.4')
elif a[:2]==['pane','split']: emit({'pane':{'pane_id':'wire:p1'}})
elif a[:2]==['pane','read']: print('explicit fake shell prompt')
elif a[:2]==['agent','start']:
    native=a[a.index('--')+1:]
    agent=dict(name=a[2],agent='codex',pane_id='wire:p1',terminal_id='wire-terminal',revision=2,
               cwd=native[native.index('-C')+1],foreground_cwd=native[native.index('-C')+1],
               interactive_ready=True,state_change_seq=1,agent_status='idle')
    (p/'agent.json').write_text(json.dumps(agent)); emit({'agent':agent,'argv':['codex',*native]})
elif a[:2]==['agent','get']:
    agent=json.loads((p/'agent.json').read_text())
    if phase!='startup':
        agent.update(agent_status=inputs['captures'][phase]['before']['agent_status'],revision=250,
                     state_change_seq=2 if phase!='cancelled' else 3)
    emit({'agent':agent})
elif a[:2]==['agent','read']:
    if phase=='startup': print('explicit fake Codex idle')
    else:
        source=a[a.index('--source')+1]
        text=inputs['captures'][phase]['visible' if source=='visible' else 'detection']
        print(text,end='')
elif a[:2]==['pane','process-info']: emit({'process_info':{'pane_id':'wire:p1'}})
elif a[:2]==['agent','prompt']: emit({'submitted':True})
elif a[:2]==['pane','close']: emit({'closed':True})
else: raise AssertionError(a)
'''
for name in ("herdr", "codex"):
    path = root / "bin" / name
    path.write_text("#!" + sys.executable + "\n" + fake, encoding="utf-8")
    path.chmod(0o755)
tokens = iter(("SHELL_READY", "CODEX_IDLE", "COLLAPSED", "EXPANDED", "CANCELLED"))


def confirm(_message):
    token = next(tokens)
    if token in ("COLLAPSED", "EXPANDED", "CANCELLED"):
        (root / "phase").write_text(token.lower(), encoding="utf-8")
    return token


probe.ARCHIVE = root / "archive"
report = dict(status="INCOMPLETE", scope="offline fake-boundary wiring; zero model turns", fixture=str(root))
try:
    environment = dict(PATH=str(root / "bin") + os.pathsep + os.environ["PATH"], HERDR_ENV="1",
                       T095_WIRE_ROOT=str(root), PYTHONDONTWRITEBYTECODE="1")
    with patch.dict(os.environ, environment), patch.object(Path, "is_mount", return_value=True), \
            patch.object(os, "isatty", return_value=True), patch("builtins.input", side_effect=confirm), \
            patch.object(sys, "argv", [str(HERE / "controlled-panel-probe.py"), "--approve-one-root-turn",
                                       "--phase", "green", "--auth-json", str(root / "auth.json")]):
        code = probe.main()
    run = json.loads(next((root / "archive").glob("*/run.json")).read_text(encoding="utf-8"))
    projections = [item["output"]["state"] for item in run["projections"]]
    assert projections == ["unknown", "waiting_controller_answer", "working"], projections
    assert all(item["output"]["launch"] == run["probe_launch"] and item["output"]["worker"] == run["worker"] for item in run["projections"])
    assert code == 0 and run["pane_closed"] and run["isolated_home_deleted"] and run["empty_scratch_removed"]
    calls = [json.loads(line) for line in (root / "calls.jsonl").read_text().splitlines()]
    assert sum(call[1:3] == ["agent", "prompt"] for call in calls) == 1
    assert not any("send-keys" in call for call in calls)
    report.update(status="PASS", projections=projections, prompt_intents=1, real_model_turns=0, fixture=None)
finally:
    target = Path(sys.argv[1])
    with target.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    if report["status"] == "PASS":
        shutil.rmtree(root)
print(json.dumps(report, ensure_ascii=False))
