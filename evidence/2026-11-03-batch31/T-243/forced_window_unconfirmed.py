"""T-243 forced window-unconfirmed run: test_electron_e2e.py --stage window with ElectronClient.close replaced by one that
raises (Electron exit unconfirmed, the real process still running). Lists the processes left under the test's fixture.
TESTS selects the test sources: the checkout's workbench/tests, or a revision's copy for the red run.
CAPTURE_FAILS=1 also makes capture_and_stop raise; SAMPLE_FAILS=1 makes its stack sample time out (review-3 finding 1).
Usage: [CAPTURE_FAILS=1 | SAMPLE_FAILS=1] forced_window_unconfirmed.py OUTPUT_DIR [TESTS_DIR]"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
out = Path(sys.argv[1]).resolve()
tests = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else ROOT / 'workbench/tests'
out.mkdir(parents=True, exist_ok=False)
wrapper = out / 'wrapper.py'
wrapper.write_text(f'''import runpy, sys
sys.path.insert(0, {str(tests)!r})
import electron_client
def unconfirmed(self):
    raise RuntimeError('T-243 forced: Electron exit unconfirmed')
electron_client.ElectronClient.close = unconfirmed
if {os.environ.get('CAPTURE_FAILS') == '1'}:
    def capture_fails(self, scene):
        raise RuntimeError('T-243 forced: scene capture failed')
    electron_client.ElectronClient.capture_and_stop = capture_fails
if {os.environ.get('SAMPLE_FAILS') == '1'}:
    real_run = electron_client.subprocess.run
    def run(argv, *rest, **options):
        if argv[0] == '/usr/bin/sample':
            raise electron_client.subprocess.TimeoutExpired(argv, 60)
        return real_run(argv, *rest, **options)
    electron_client.subprocess.run = run
sys.argv = [{str(tests / 'test_electron_e2e.py')!r}, '--source', {str(ROOT)!r}, '--output', {str(out / 'out')!r}, '--stage', 'window']
runpy.run_path(sys.argv[0], run_name='__main__')
''', encoding='utf-8')
before = set(Path('/tmp').iterdir())
env = dict(os.environ, ENCHANTED_HC_CACHE_DIR=str(ROOT.parent / 'hc-cache'))
run = subprocess.run([sys.executable, str(wrapper)], cwd=ROOT, env=env, capture_output=True, text=True, timeout=900)
time.sleep(2)
fixtures = sorted(str(p.resolve()) for p in set(Path('/tmp').iterdir()) - before if p.name.startswith('a2a4-'))
listing = subprocess.run(['/bin/ps', '-axE', '-ww', '-o', 'pid=,command='], capture_output=True, text=True, check=True).stdout
left = [line.strip()[:300] for line in listing.splitlines() if any(f in line for f in fixtures)]
verdict = out / 'out' / 'verdict.json'
result = dict(tests=str(tests), exit=run.returncode, fixtures=fixtures, left_after=left,
              verdict=json.loads(verdict.read_text(encoding='utf-8')) if verdict.exists() else None, tail=(run.stdout + run.stderr)[-2000:])
(out / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(json.dumps(dict(exit=run.returncode, left=len(left), kinds=sorted({l.split()[1].rsplit('/', 1)[-1] for l in left}),
                      status=(result['verdict'] or {}).get('status')), ensure_ascii=False))
