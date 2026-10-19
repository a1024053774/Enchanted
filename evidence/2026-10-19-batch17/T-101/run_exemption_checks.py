#!/usr/bin/env python3
"""验证精确对象/offset 豁免、拒绝新命中，以及 23 个会话路径的保留。"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import uuid

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_local_checks as fixture


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def modules(mutant_path=None):
    slim = load(mutant_path or HERE / 'slim_history.py', 'exemption_slim')
    sys.modules['slim_history'] = slim
    checker = load(HERE / 'recheck_credential_exemptions.py', 'exemption_probe')
    return slim, checker


def expect_rejected(module, source, output, exemptions):
    try:
        module.scan(source, output, exemptions)
    except module.CredentialScanRejected:
        result = module.read(output)
        assert result['unexempted_hit_count'] > 0 and result['status'] == 'NO_GO'
        return
    raise AssertionError('unapproved location accepted')


def exact_identity(root, mutant_path=None):
    root.mkdir()
    slim, checker = modules(mutant_path)
    source = root / 'source'
    fixture.repo(source)
    path = source / 'workbench/tests/credential-case.txt'
    path.parent.mkdir(parents=True)
    sample = ('a2a-public-fixture-' + uuid.uuid4().hex).encode('ascii')
    path.write_bytes(b'Bearer ' + sample + b'\n')
    fixture.command(['git', '-c', 'core.hooksPath=/dev/null', 'add', '.'], source)
    fixture.command(['git', '-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'synthetic fixture input'], source)
    original = fixture.command(['git', 'rev-parse', 'HEAD:workbench/tests/credential-case.txt'], source).decode().strip()
    empty = root / 'empty.json'
    approved = root / 'approved.json'
    shifted = root / 'wrong-offset.json'
    slim.save(empty, {'schema': 1, 'approved_entry_count': 0, 'entries': []})
    slim.save(approved, {'schema': 1, 'approved_entry_count': 1, 'entries': [{'object': original, 'offset': 0}]})
    slim.save(shifted, {'schema': 1, 'approved_entry_count': 1, 'entries': [{'object': original, 'offset': 1}]})
    expect_rejected(slim, source, root / 'strict-red.json', empty)
    green = slim.scan(source, root / 'approved-green.json', approved)
    assert green['hit_count'] == green['exempted_hit_count'] == 1 and green['unexempted_hit_count'] == 0
    expect_rejected(slim, source, root / 'wrong-offset-red.json', shifted)
    checker.negative_probe(source, root / 'counterexample', green, approved)
    assert sample not in (root / 'approved-green.json').read_bytes(), 'raw value leaked into scan report'
    proof = slim.read(root / 'counterexample/proof.json')
    assert proof['unexempted_hit_count'] == 2 and proof['source_refs_unchanged'] is True


def retained_sessions(root, mutant_path=None):
    root.mkdir()
    slim, _ = modules(mutant_path)
    run = root / 'run'
    run.mkdir()
    source = run / 'repository'
    fixture.repo(source)
    paths = [f'evidence/batch/task/run/rollout-case-{index:02d}.jsonl' for index in range(23)]
    for name in paths:
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b'{"message":"fixture body retained in history"}\n')
    (source / 'evidence/batch/task/run/raw.bin').write_bytes(b'archive only this raw input\n')
    fixture.command(['git', '-c', 'core.hooksPath=/dev/null', 'add', '.'], source)
    fixture.command(['git', '-c', 'core.hooksPath=/dev/null', 'commit', '-m', '23 native session fixture paths'], source)
    snapshot = slim.stable_snapshot(source)
    slim.save(run / 'backup.json', {'status': 'PASS', 'objects': slim.object_count(source), 'snapshot': snapshot})
    slim.save(run / 'snapshot.json', snapshot)
    info = root / 'info'
    info.mkdir()
    (info / 'keep-paths.txt').write_text('# isolated input list\n', encoding='utf-8')
    versions = slim.history_versions(source)
    slim.save(info / 'sessions.json', {'required_count': 23, 'sessions': [{'path': path, 'versions': versions[path]} for path in paths]})
    slim.HERE = info
    slim.PUBLIC_SESSIONS_PATH = info / 'sessions.json'
    slim.ARCHIVES = root / 'simulated-external-archive'
    slim.plan(run)
    plan = slim.read(run / 'plan.json')
    assert set(paths).isdisjoint(plan['remove']) and set(paths) <= set(plan['keep']), 'protected sessions were selected for removal'
    assert set(plan['retained_native_sessions']) == set(paths)
    slim.rewrite(run)
    after = slim.history_versions(run / 'prepared')
    assert all(set(versions[path]) <= set(after[path]) for path in paths), 'native session body/version disappeared'
    assert 'evidence/batch/task/run/raw.bin' not in after
    assert len([p for p in after if Path(p).name.startswith('rollout-')]) == 23


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    assert not args.report.exists()
    for key in list(os.environ):
        if key.startswith('GIT_CONFIG_'):
            os.environ.pop(key)
    os.environ.update(GIT_AUTHOR_NAME='T101 fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
                      GIT_COMMITTER_NAME='T101 fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid',
                      PYTHONDONTWRITEBYTECODE='1')
    root = Path(tempfile.mkdtemp(prefix='a2a-t101-exemption-unit-', dir='/tmp')).resolve()
    original = (HERE / 'slim_history.py').read_text(encoding='utf-8')
    weak = root / 'weak-object-binding.py'
    old = "hit['exempted'] = (hit.get('object'), hit.get('offset')) in exemptions"
    assert old in original
    weak.write_text(original.replace(old, "hit['exempted'] = any(offset == hit.get('offset') for _, offset in exemptions)", 1), encoding='utf-8')
    dropped = root / 'dropped-session-retention.py'
    block = "        if path in public_sessions:\n            kept[path] = 'user-decision-B-public-native-session-body'\n            continue\n"
    assert block in original
    dropped.write_text(original.replace(block, '', 1), encoding='utf-8')
    cases = []
    status = 'PASS'
    try:
        for name, test, expected in [
            ('exact-object-and-offset', lambda p: exact_identity(p), None),
            ('offset-only-mutant', lambda p: exact_identity(p, weak), '新凭据反例未被拒绝'),
            ('23-session-bodies-retained', lambda p: retained_sessions(p), None),
            ('removed-session-retention-mutant', lambda p: retained_sessions(p, dropped), 'protected sessions were selected for removal')]:
            try:
                test(root / name)
            except (AssertionError, ValueError) as error:
                if expected is None:
                    raise
                assert expected in str(error), 'unrelated failure in known-bad probe: ' + str(error)
                cases.append({'case': name, 'status': 'PASS', 'known_bad_rejected': True, 'reason': str(error)})
            else:
                assert expected is None, 'known-bad implementation passed'
                cases.append({'case': name, 'status': 'PASS'})
    except (AssertionError, ValueError, OSError) as error:
        import traceback
        (root / 'failure.txt').write_text(traceback.format_exc(), encoding='utf-8')
        cases.append({'case': 'unexpected-failure', 'status': 'NO_GO', 'reason': str(error)})
        status = 'NO_GO'
    command = ['python3', '-B', str(HERE / 'run_exemption_checks.py'), '--report', str(args.report)]
    args.report.write_text(json.dumps({'status': status, 'artifact_root': str(root), 'cases': cases,
                                       'checks': [{'argv': command, 'exit': 0 if status == 'PASS' else 1}],
                                       'scope': '真实小型 Git/现有 filter-repo 2.47.0；不改真实候选、外置盘或用户配置'},
                                      ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(status + ' ' + str(args.report))
    raise SystemExit(0 if status == 'PASS' else 1)


if __name__ == '__main__':
    main()
