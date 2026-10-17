"""Refreeze the changed Stage A preflight and keep both approvals unsigned; no launch."""
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile

BASE = Path(__file__).resolve().parent
SOURCE = BASE.parents[2]


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip()
    assert not subprocess.check_output(['git', 'diff', 'HEAD'], cwd=SOURCE), 'Commit preflight source before refreezing'
    out = BASE / 'stage-a-readback-rebind-01'; out.mkdir(exist_ok=False)
    spec = importlib.util.spec_from_file_location('stage_a_preflight', BASE / 'run-09b.py')
    runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    readbacks = [str(BASE / name / 'result.json') for name in runner.REGRESSION_REPORTS]
    rows = []
    for scene, folder, old_label, label in [
        ('09B', '09b-a16-materials-01', '09b-executable-materials-16', '09b-executable-materials-16-02'),
        ('09C', '09c-materials-01', '09c-executable-materials-01', '09c-executable-materials-02')]:
        packet = BASE / folder; old = BASE / old_label; executable = BASE / label
        approval = json.loads((packet / 'stage-a-approval.json').read_bytes())
        assert approval['approved_by'] is None and approval['approval_ref'] is None
        assert old.is_dir() and not executable.exists()
        argv = [sys.executable, '-B', str(BASE / 'prepare-09b-executable.py'), '--scene', scene,
                '--label', label, '--protocol', '--prompt-file', str(packet / 'i1-prompt.txt')]
        result = subprocess.run(argv, cwd=SOURCE, capture_output=True, text=True, timeout=300)
        write(out / (scene + '-prepare.json'), {'argv': argv, 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
        assert result.returncode == 0, 'Static prepare failed; preserve outputs, no retry'
        static = json.loads((executable / 'static-check.json').read_bytes())
        assert static['scene'] == scene and static['revision'] == revision and static['protocol'] is True
        with tarfile.open(old / 'sources.tar.gz') as prior, tarfile.open(executable / 'sources.tar.gz') as current:
            assert set(prior.getnames()) == set(current.getnames()) == set(static['source_paths'])
            changed = []
            for path in static['source_paths']:
                value = current.extractfile(path).read()
                assert value == subprocess.check_output(['git', 'show', revision + ':' + path], cwd=SOURCE)
                if value != prior.extractfile(path).read(): changed.append(path)
            assert changed == [runner.PREFLIGHT_SOURCE], 'Only the Stage A readback preflight may differ'
        static['regression_readbacks'] = readbacks
        write(executable / 'static-check.json', static)
        approval.update(source_revision=revision, materials=label, regression_readbacks=readbacks)
        write(packet / 'stage-a-approval.json', approval)
        metadata = json.loads((packet / 'SOURCE.json').read_bytes())
        metadata.update(revision=revision, material_package=str(executable), static_root=static['root'],
                        source_paths=static['source_paths'], regression_status='PASS: explicit four-receipt composition; original 02 remains INCOMPLETE',
                        scope='Runtime source unchanged; Stage A readback preflight refrozen; no scene launched')
        write(packet / 'SOURCE.json', metadata)
        for name in ['STAGE-A-COMMAND.txt', 'ROLE-MATERIAL-COMMANDS.txt', 'BIND-OWNER-COMMAND.txt']:
            path = packet / name; command = path.read_text(encoding='utf-8')
            assert str(old) in command
            path.write_text(command.replace(str(old), str(executable)), encoding='utf-8')
        if scene == '09C':
            protocol = json.loads((packet / 'protocol.json').read_bytes())
            protocol['source_revision'] = revision
            write(packet / 'protocol.json', protocol)
        stage = shlex.split((packet / 'STAGE-A-COMMAND.txt').read_text(encoding='utf-8'))
        for option in ['--materials', '--approval']:
            assert Path(stage[stage.index(option) + 1]).exists()
        assert Path(stage[2]).is_file() and not Path(stage[stage.index('--output') + 1]).exists()
        assert approval['approved_by'] is None and approval['approval_ref'] is None
        rows.append({'scene': scene, 'source_revision': revision, 'new_packet': str(executable),
                     'previous_packet_retained': str(old), 'source_files': len(static['source_paths']),
                     'changed_frozen_members': changed, 'regression_audit': runner.validate_regression_readbacks(static, approval),
                     'StageA': stage, 'signatures': 'empty'})
    write(out / 'result.json', {'status': 'PASS', 'scope': 'File generation and byte verification only',
                              'scenes': rows, 'runtime_process_starts': 0, 'model_turns': 0})
    print(json.dumps({'status': 'PASS', 'source_revision': revision, 'output': str(out), 'runtime_process_starts': 0}))


if __name__ == '__main__': main()
