"""Runner extraction failures: controlled links lost; traversal, link-parent writes,
absolute/escaping targets, cycles, dangling targets, duplicate and special members.
Uses real Git archive and private temporary trees; never starts a CLI or a model.
"""
import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
from t112_archive import extract_baseline


def sample(entries):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w') as tar:
        for name, kind, value in entries:
            member = tarfile.TarInfo(name)
            member.mode = 0o755 if kind == 'directory' else 0o644
            if kind == 'file':
                data = value.encode(); member.size = len(data)
                tar.addfile(member, io.BytesIO(data))
            else:
                member.type = {'directory': tarfile.DIRTYPE, 'symbolic': tarfile.SYMTYPE,
                               'hard': tarfile.LNKTYPE, 'device': tarfile.CHRTYPE}[kind]
                member.linkname = value
                tar.addfile(member)
    return buffer.getvalue()


def check(extract=extract_baseline):
    cases = []
    env = {key: value for key, value in os.environ.items() if key not in ('GIT_DIR', 'GIT_WORK_TREE')}
    env['LC_ALL'] = 'C'
    baseline = 'e3102389eda8952ea92cae4b373e14eaff898314'
    command = ['git', 'archive', baseline, 'workbench']
    archive = subprocess.check_output(command, env=env)
    with tempfile.TemporaryDirectory(prefix='t112-tar-check-', dir='/private/tmp') as raw:
        root = Path(raw)
        target = root / 'actual'
        extract(archive, target)
        assert (target / 'workbench/hooks/pre-commit').is_symlink(), 'Controlled Git hook link must survive extraction'
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            links = [member for member in tar if member.issym()]
        assert len(links) == 26, 'Frozen baseline has 26 hook links'
        for member in links:
            path = target / member.name
            assert os.readlink(path) == member.linkname
            assert path.resolve() == target / 'workbench/hooks/hook.py'
        cases.append('real_git_archive_preserves_26_internal_hook_links')
        valid = [('workbench/original', 'file', 'sentinel'),
                 ('workbench/hard', 'hard', 'workbench/original'),
                 ('workbench/alias', 'symbolic', 'original'),
                 ('workbench/nested/relative', 'symbolic', '../original')]
        extract(sample(valid), root / 'valid')
        assert (root / 'valid/workbench/original').stat().st_ino == (root / 'valid/workbench/hard').stat().st_ino
        assert os.readlink(root / 'valid/workbench/nested/relative') == '../original'
        cases.append('safe_relative_symbolic_and_hard_links_preserved')
        sentinel = root / 'untouched'; sentinel.write_text('untouched', encoding='utf-8')
        invalid = {
            'absolute_member': [(str(sentinel), 'file', 'changed')],
            'member_traversal': [('workbench/../untouched', 'file', 'changed')],
            'absolute_symbolic_target': [('workbench/link', 'symbolic', str(sentinel))],
            'symbolic_target_escape': [('workbench/link', 'symbolic', '../../untouched')],
            'hard_target_escape': [('workbench/link', 'hard', '../untouched')],
            'hard_target_absolute': [('workbench/link', 'hard', str(sentinel))],
            'symbolic_parent_write': [('workbench/link', 'symbolic', '.'), ('workbench/link/child', 'file', 'changed')],
            'hard_parent_write': [('workbench/original', 'file', 'sentinel'), ('workbench/link', 'hard', 'workbench/original'), ('workbench/link/child', 'file', 'changed')],
            'cycle': [('workbench/a', 'symbolic', 'b'), ('workbench/b', 'symbolic', 'a')],
            'dangling_target': [('workbench/link', 'symbolic', 'absent')],
            'duplicate_member': [('workbench/a', 'file', 'first'), ('workbench/a', 'file', 'second')],
            'device_member': [('workbench/device', 'device', '')],
        }
        for name, entries in invalid.items():
            destination = root / name
            try:
                extract(sample(entries), destination)
            except ValueError:
                pass
            else:
                raise AssertionError('Unsafe archive must be refused: ' + name)
            assert not destination.exists(), 'Validation must precede filesystem writes: ' + name
            assert sentinel.read_text() == 'untouched'
            cases.append(name + '_refused_before_writes')
    return cases


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', required=True, type=Path)
    args = parser.parse_args()
    assert not args.summary.exists()
    report = dict(status='INCOMPLETE', model_calls=0, command=['python3', '-B', __file__, '--summary', str(args.summary)])
    try:
        report['checks'] = check()
        # This known-bad behavior is exactly the previous runner's rejection.
        def reject_links(archive, destination):
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
                if any(member.issym() or member.islnk() for member in tar):
                    raise AssertionError('Controlled link rejected by old behavior')
            return extract_baseline(archive, destination)
        try:
            check(reject_links)
        except AssertionError as error:
            assert str(error) == 'Controlled link rejected by old behavior'
            report['known_bad_rejected'] = str(error)
        else:
            raise AssertionError('Known-bad extraction must fail')
        report['status'] = 'PASS'
    except Exception as error:
        report['error'] = str(error)
    args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
    raise SystemExit(0 if report['status'] == 'PASS' else 1)
