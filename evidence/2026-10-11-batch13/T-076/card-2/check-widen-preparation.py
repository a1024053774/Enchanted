"""Static preparation evidence only: no daemon, socket, signals or model calls."""
import argparse
import ast
import json
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    card = Path(__file__).resolve().parent
    report = {'status': 'INCOMPLETE', 'product_status': 'INCOMPLETE', 'real_codex_turns': 0,
              'scope': 'syntax, imports, mutation target uniqueness and saved evidence readback only', 'checks': []}
    if args.output.exists():
        raise RuntimeError('Preserve earlier evidence; choose a new output file.')

    def command(argv, **metadata):
        result = subprocess.run(argv, cwd=root, text=True, capture_output=True, timeout=45)
        report['checks'].append({'argv': argv, 'cwd': str(root), 'exit': result.returncode,
                                 'stdout': result.stdout, 'stderr': result.stderr, **metadata})
        if result.returncode:
            raise RuntimeError('Static command failed: ' + repr(argv))
        return result.stdout

    try:
        report['head'] = command(['git', 'rev-parse', 'HEAD']).strip()
        report['node'] = command(['node', '--version']).strip()
        report['external_volume_mounted'] = Path('/Volumes/WD-Elements').is_mount()
        if not report['external_volume_mounted']:
            raise RuntimeError('External volume is not mounted.')
        changed = command(['git', 'diff', 'a7f4cc3033c16d5888de50d8352da516c941f8e9', '--',
                           'acceptance/test_coop_e2e.py', 'acceptance/test_recovery_e2e.py',
                           'acceptance/test_run_e2e.py', 'scripts'])
        if changed:
            raise RuntimeError('Frozen acceptance or scripts changed.')
        python_files = [*root.glob('workbench/tests/*quality*.py'), Path(__file__).resolve()]
        for path in python_files:
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        report['python_ast'] = [str(p.relative_to(root)) for p in python_files]
        files = command(['git', 'diff', '--name-only', '--', 'workbench/src', 'workbench/tests']).splitlines()
        files += ['workbench/src/gates/qualityProtocol.ts', 'workbench/tests/quality_chain_host.ts']
        for path in files:
            if path.endswith('.ts'):
                command(['node', '--check', path])
        command(['node', '--input-type=module', '-e',
                 'await Promise.all(["./workbench/src/gates/core.ts","./workbench/src/daemon.ts","./workbench/src/gates/qualityProtocol.ts"].map(p=>import(p))); console.log("imports only; no runtime constructed")'])
        command(['zsh', '-n', str(card / 'outside-sandbox.sh')])
        tree = ast.parse((root / 'workbench/tests/run_t076_quality_widen.py').read_text(encoding='utf-8'))
        catalog = next(n for n in ast.walk(tree) if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == 'mutations' for t in n.targets))
        mutations = ast.literal_eval(catalog.value)
        with tempfile.TemporaryDirectory(prefix='q76-static-') as temporary:
            for name, case, failure, relative, before, after in mutations:
                content = (root / 'workbench/src' / relative).read_text(encoding='utf-8')
                if content.count(before) != 1:
                    raise RuntimeError('Mutation target is not unique: ' + name)
                target = Path(temporary) / (name + '.ts')
                target.write_text(content.replace(before, after), encoding='utf-8')
                command(['node', '--check', str(target)], mutation=name, source=relative, expected_failure=failure)
        report['mutation_count'] = len(mutations)
        prior = card / 'outside-focused-tracer-01'
        previous = json.loads((prior / 'run.json').read_text(encoding='utf-8'))
        rows = [json.loads(line) for line in (prior / 'commands.jsonl').read_text(encoding='utf-8').splitlines()]
        validation = [row for row in rows if row['phase'] == 'finished' and any('validate_scores' in arg for arg in row['argv'])]
        if previous['status'] != 'PASS' or len(validation) != 1 or validation[0]['exit'] != 0:
            raise RuntimeError('Prior tracer or schema readback disagrees.')
        receipt = validation[0]
        if Path(receipt['stdout_file']).read_bytes() != b'schema-1 payload accepted\n' or Path(receipt['stderr_file']).read_bytes():
            raise RuntimeError('Prior score validation raw bytes disagree.')
        report['prior_score_validation'] = receipt
        command(['git', 'diff', '--check'])
        command(['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', '.'])
        report['oversize_files'] = command(['find', str(card), '-size', '+5M']).splitlines()
        if report['oversize_files']:
            raise RuntimeError('Unarchived oversized evidence remains.')
        for path in [root / 'workbench/README.md', card / 'RESULTS.md', card / 'assertion-hunks.md', card / 'HANDOFF-widen-01.md']:
            content = path.read_bytes()
            if content.startswith(b'\xef\xbb\xbf') or '\ufffd' in content.decode('utf-8'):
                raise RuntimeError('Document encoding readback failed: ' + str(path))
        report['status'] = 'PASS'
    except Exception as error:
        report['error'] = repr(error)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({key: report[key] for key in ('status', 'product_status', 'real_codex_turns')}))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
