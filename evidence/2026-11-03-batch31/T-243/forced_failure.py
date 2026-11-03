"""T-243 forced failure: run a copy of a non-Fixture test that raises right after its daemon is up, then list the
processes left under its fixture. The copy lives in this run's output directory; the test itself is not changed.
Usage: forced_failure.py TEST_NAME OUTPUT_DIR (e.g. test_t193_multi_project_e2e.py)"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
TESTS = ROOT / 'workbench/tests'
name, out = sys.argv[1], Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=False)
source = (TESTS / name).read_text(encoding='utf-8')
anchor_root = 'ROOT = Path(__file__).resolve().parents[2]'
anchor_run = '        running = True\n'
assert source.count(anchor_root) == 1 and source.count(anchor_run) == 1, '注入点必须唯一'
copy = out / ('forced_' + name)
copy.write_text(source.replace(anchor_root, f'ROOT = Path({str(ROOT)!r})')
                .replace(anchor_run, anchor_run + "        raise RuntimeError('T-243 forced failure after daemon start')\n"), encoding='utf-8')
summary = out / 'summary.json'
env = dict(os.environ, PYTHONPATH=str(TESTS), ENCHANTED_HC_CACHE_DIR=str(ROOT.parent / 'hc-cache'))
run = subprocess.run([sys.executable, str(copy), '--summary', str(summary)], cwd=ROOT, env=env, capture_output=True, text=True, timeout=600)
time.sleep(2)
report = json.loads(summary.read_text(encoding='utf-8')) if summary.exists() else {}
fixture = report.get('fixture')
listing = subprocess.run(['/bin/ps', '-axE', '-ww', '-o', 'pid=,command='], capture_output=True, text=True, check=True).stdout
left = [line.strip()[:300] for line in listing.splitlines() if fixture and fixture in line]
result = dict(test=name, exit=run.returncode, status=report.get('status'), error=report.get('error'), residue=report.get('residue'),
              core_cleanup=report.get('core_cleanup'), fixture=fixture, left_after=left, tail=(run.stdout + run.stderr)[-2000:])
(out / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(json.dumps({k: result[k] for k in ('test', 'exit', 'status', 'error', 'core_cleanup', 'left_after')}, ensure_ascii=False))
