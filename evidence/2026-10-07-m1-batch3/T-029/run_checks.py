"""Run unchanged contract assertions with a Muster boundary and retained artifacts."""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[3]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--coop', type=Path, default=ROOT / 'coop.py')
    p.add_argument('--red', action='store_true')
    args = p.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    head_at_start = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    runtime = ROOT / '.runtime' / ('t029-' + out.parent.name + '-' + out.name)
    runtime.mkdir(parents=True, exist_ok=False)
    sources = runtime / 'acceptance'
    sources.mkdir()
    for name in ('test_coop_e2e.py', 'test_recovery_e2e.py', 'test_run_e2e.py'):
        text = (subprocess.check_output(['git', 'show', '50d93d341421928508e5a8f14cebc95601adfd04:acceptance/' + name], cwd=ROOT, text=True)
                if args.red else (ROOT / 'acceptance' / name).read_text(encoding='utf-8'))
        if name == 'test_coop_e2e.py':
            text = text.replace('ROOT = Path(__file__).resolve().parents[1]',
                                'ROOT = Path(' + repr(str(ROOT)) + ')', 1)
        if args.red and name == 'test_run_e2e.py':
            # Only the external executable/context is migrated for contract-red.
            # Every business assertion stays byte-for-byte unchanged.
            text = text.replace('HERDR', 'MUSTER').replace('Herdr', 'Muster').replace('herdr', 'muster')
            text = text.replace('"MUSTER_ENV": "1",', '"MUSTER_ENV": "1", "MUSTER_BIN": str(self.bin / "muster"),')
        (sources / name).write_text(text, encoding='utf-8')
        shutil.copyfile(sources / name, out / name)
    snapshot = runtime / 'coop-used.py'
    if args.red:
        snapshot.write_text(subprocess.check_output(['git', 'show', '50d93d341421928508e5a8f14cebc95601adfd04:coop.py'], cwd=ROOT, text=True), encoding='utf-8')
    else:
        shutil.copyfile(args.coop, snapshot)
    shutil.copyfile(snapshot, out / 'coop-used.py')
    inherited = [k for k in os.environ if k.startswith(('HERDR_', 'MUSTER_')) or k == 'CODEX_THREAD_ID']
    env = {k: v for k, v in os.environ.items() if k not in inherited}
    # Domain suites do not need the engine; run negatives own their fake boundary.
    env.update(COOP_SCRIPT=str(snapshot), PYTHONDONTWRITEBYTECODE='1')
    records = []
    for name, expected in [('test_coop_e2e.py', 8), ('test_recovery_e2e.py', 9), ('test_run_e2e.py', 18)]:
        artifact = runtime / (name + '-artifacts')
        artifact.mkdir()
        trace = out / (name + '.trace.json')
        argv = [sys.executable, '-B', str(sources / name), '--run-suite']
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        process = subprocess.run(argv, cwd=ROOT, env=dict(env, COOP_E2E_ARTIFACT_ROOT=str(artifact),
                                  COOP_E2E_TRACE=str(trace)), text=True, capture_output=True)
        (out / (name + '.stdout')).write_text(process.stdout, encoding='utf-8')
        (out / (name + '.stderr')).write_text(process.stderr, encoding='utf-8')
        details = json.loads(trace.read_text(encoding='utf-8'))
        record = dict(argv=argv, started=started, exit_code=process.returncode,
                      tests_run=details['tests_run'], failures=details['failures'], errors=details['errors'],
                      expected_tests=expected, artifacts=str(artifact), trace=str(trace),
                      layer='isolated-muster-codex-orchestration' if expected == 18 else 'real-cli-git-sqlite')
        records.append(record)
        print(json.dumps(record), flush=True)
    with tarfile.open(out / 'artifacts.tar.gz', 'w:gz') as archive:
        archive.add(runtime, arcname=runtime.name)
    result = dict(status='PASS' if all(r['exit_code'] == 0 and r['tests_run'] == r['expected_tests'] for r in records) else 'INCOMPLETE',
                  repository_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  selected_source=str(args.coop.resolve()), removed_environment=inherited, records=records)
    result['invocation_runtime'] = {k: os.environ.get(k) for k in ('MUSTER_ENV', 'MUSTER_PANE_ID', 'MUSTER_SOCKET_PATH', 'MUSTER_BIN')}
    result['repository_head_at_start'] = head_at_start
    (out / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
