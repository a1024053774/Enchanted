"""Run the T-156-2 credential contract and isolated counterexamples, without sockets."""
import argparse
import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
TEST = 'workbench/tests/test_t156_quality_host_credentials.py'
MUTANTS = {
    'missing-creation': ('workbench/tests/quality_chain_host.ts',
                         'createOperatorCredential(root);', '', 'generation-1-created'),
    'wrong-kind': ('workbench/src/credentials.ts',
                   'kind: "operator", state: realpathSync(root)',
                   'kind: "worker", state: realpathSync(root)', 'generation-1-kind'),
    'wrong-state': ('workbench/src/credentials.ts',
                    'state: realpathSync(root), epoch:',
                    'state: "/private/tmp/foreign-quality-state", epoch:', 'generation-1-state'),
    'wrong-mode': ('workbench/src/credentials.ts',
                   'mode: 0o600', 'mode: 0o400', 'generation-1-mode'),
    'missing-cleanup': ('workbench/tests/test_quality_chain_e2e.py',
                        '                credential.unlink()',
                        '                pass  # Mutant: retain owned credentials.',
                        'capabilities-removed-before-archive'),
    'wrong-generation-path': ('workbench/tests/test_quality_chain_e2e.py',
                              "('operator-%02d.credential.json' % self.host_generation)",
                              "('operator-%02d.credential.json' % (1 if self.host_generation == 1 else 3))",
                              'generation-2-spawn-path'),
    'inherited-launch': ('workbench/tests/test_task_cards_e2e.py',
                         "if not k.startswith(('GIT_', 'A2A_'))}",
                         "if not k.startswith(('GIT_', 'A2A_')) or k == 'A2A_LAUNCH'}",
                         'generation-1-launch-filtered'),
}


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for name, mutation in [('green', None), *MUTANTS.items()]:
        selected = source
        if mutation:
            selected = output / (name + '-source')
            for directory in ['src', 'tests']:
                shutil.copytree(source / 'workbench' / directory, selected / 'workbench' / directory,
                                ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copyfile(source / 'workbench/package.json', selected / 'workbench/package.json')
            (selected / 'workbench/node_modules').symlink_to(
                (source / 'workbench/node_modules').resolve(), target_is_directory=True)
            relative, before, after, failure = mutation
            target = selected / relative
            text = target.read_text(encoding='utf-8')
            if text.count(before) != 1:
                raise RuntimeError('Mutation target is not unique: ' + name)
            target.write_text(text.replace(before, after), encoding='utf-8')
        command = [sys.executable, '-B', str(selected / TEST), '--output', str(output / name)]
        result = subprocess.run(command, cwd=selected, capture_output=True, timeout=90)
        (output / (name + '.stdout.txt')).write_bytes(result.stdout)
        (output / (name + '.stderr.txt')).write_bytes(result.stderr)
        report_path = output / name / 'results.json'
        report = json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else None
        failures = [row['name'] for row in report['checks'] if row['status'] != 'PASS'] if report else []
        valid = (result.returncode == 1 and report is not None and report['status'] == 'INCOMPLETE'
                 and failure in failures) if mutation else (
                     result.returncode == 0 and report is not None and report['status'] == 'PASS')
        valid = valid and report['scratch_removed'] and all(
            len(host['observations']) >= 1 for host in report['hosts']) and len(report['hosts']) == 2
        row = {'name': name, 'status': 'PASS' if valid else 'INCOMPLETE', 'command': command,
               'exit_code': result.returncode, 'report': str(report_path), 'failures': failures,
               'expected_failure': mutation[3] if mutation else None,
               'mutation': {'path': mutation[0], 'before': mutation[1], 'after': mutation[2]} if mutation else None}
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    record = {'status': 'PASS' if all(row['status'] == 'PASS' for row in rows) else 'INCOMPLETE',
              'task': 'T-156-2', 'attempt': 'a1', 'source': str(source),
              'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip(),
              'source_diff': subprocess.check_output(['git', 'diff', '--stat'], cwd=source, text=True),
              'node_version': subprocess.check_output(['node', '--version'], text=True).strip(),
              'python_version': sys.version, 'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'real_model_turns': 0, 'daemon_starts': 0, 'runs': rows}
    save(output / 'SUMMARY.json', record)
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
