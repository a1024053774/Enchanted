"""Replay the frozen UI oracle on the parent ChatView, then restore our candidate bytes."""
import json
from pathlib import Path
import subprocess

out=Path(__file__).resolve().parent
fork=Path('/Users/luckye/Documents/Code/synara')
source=fork/'apps/web/src/components/ChatView.tsx'
baseline=json.loads((out/'binding.json').read_text(encoding='utf-8'))['baseline_fork']
candidate=source.read_bytes()
old=subprocess.check_output(['git','show',baseline+':apps/web/src/components/ChatView.tsx'],cwd=fork)
(out/'candidate-ChatView.tsx').write_bytes(candidate)
(out/'baseline-ChatView.tsx').write_bytes(old)
try:
    source.write_bytes(old)
    command=['python3',str(out/'run-command.py'),'counterfactual-red01','./a2a/scripts/bun','run','node',str(out/'ui-probe.mjs'),str(out),'/Volumes/WD-Elements/dev-cache/synara/instances/t063-probe01','counterfactual-red01']
    result=subprocess.run(command,cwd=fork)
finally:
    source.write_bytes(candidate)
    (out/'counterfactual-restored.txt').write_text('已恢复运行前保存的候选 ChatView 字节。基线：'+baseline+'\n',encoding='utf-8')
raise SystemExit(result.returncode)
