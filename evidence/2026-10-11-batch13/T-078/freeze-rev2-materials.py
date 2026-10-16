"""Write merged A16/09C packets and unsigned commands; never launch a scene."""
import ast
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile

SOURCE = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream: stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def git(*args): return subprocess.check_output(['git', *args], cwd=SOURCE, text=True).strip()


def main():
    revision = git('rev-parse', 'HEAD')
    merge = json.loads((BASE / 'merge-main-4/source-binding.json').read_bytes())
    subprocess.run(['git', 'merge-base', '--is-ancestor', merge['merge_revision'], revision], cwd=SOURCE, check=True)
    assert not git('diff', 'HEAD') and not git('ls-files', '--others', '--exclude-standard', '--', 'workbench', 'scripts')
    metadata = {'revision': revision, 'business_revision': merge['merge_revision'], 'main_target': merge['main_target'],
                'scope': 'T090 merged; full source/fixtures frozen; later ticket evidence only; actual regressions remain unrun'}
    (BASE / 'review-followup-source.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    readbacks = [BASE / 'review-followup-regressions-02/result.json', BASE / 'merge-main-4-t078-regressions-01/result.json']
    index = {'status': 'PASS', 'scope': 'static files and source byte freeze only', 'source_revision': revision,
             'merge_revision': merge['merge_revision'], 'launch_status': 'NO_GO', 'scenes': [], 'process_starts': 0}
    for scene, instance, label, folder, output in [
        ('09B', 'a16', '09b-executable-materials-16', '09b-a16-materials-01', '09b-a16-stage-a-01'),
        ('09C', 'c1', '09c-executable-materials-01', '09c-materials-01', '09c-stage-a-01')]:
        packet = BASE / folder; executable = BASE / label
        assert packet.is_dir() and not executable.exists()
        command = [sys.executable, '-B', str(BASE / 'prepare-09b-executable.py'), '--scene', scene,
                   '--label', label, '--protocol', '--prompt-file', str(packet / 'i1-prompt.txt')]
        generated = subprocess.run(command, cwd=SOURCE, capture_output=True, text=True, timeout=300)
        save(packet / 'prepare.json', {'argv': command, 'exit_code': generated.returncode, 'stdout': generated.stdout, 'stderr': generated.stderr})
        assert generated.returncode == 0, 'static prepare failed; preserve outputs; no retry'
        static = json.loads((executable / 'static-check.json').read_bytes())
        assert static['scene'] == scene and static['revision'] == revision and Path(static['root']).is_dir()
        static['regression_readbacks'] = list(map(str, readbacks))
        (executable / 'static-check.json').write_text(json.dumps(static, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        if scene == '09C':
            protocol = json.loads((packet / 'protocol.json').read_bytes())
            protocol.update(kind='FROZEN_STAGE_PLAN_RUNTIME_UNBOUND', source_revision=revision)
            (packet / 'protocol.json').write_text(json.dumps(protocol, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        # Every named frozen member must exist and match this committed source.
        with tarfile.open(executable / 'sources.tar.gz') as archive:
            assert set(archive.getnames()) == set(static['source_paths'])
            for relative in static['source_paths']:
                assert archive.extractfile(relative).read() == subprocess.check_output(['git', 'show', revision + ':' + relative], cwd=SOURCE)
        approval = {'approved_by': None, 'approval_ref': None, 'stage': 'A', 'scene': scene,
            'source_revision': revision, 'launch_status': 'NO_GO', 'protocol': True, 'materials': label,
            'allow_role_cli_spawn': False, 'final_protocol_api': True, 'protocol_tag': 'rev2-raw-c-profile-v1',
            'fixture_profile': 'rev2-registered-raw-v1', 'real_vendor_model_turns': 0,
            'actions': ['real card preflight before root/spawn', 'start two detached fake APIs and daemon',
                        'real managed target dispatch/claim; original PID/argv/lstart receipts',
                        'stop at READY_FOR_APPROVAL; no role CLI'],
            'regression_readbacks': list(map(str, readbacks))}
        save(packet / 'stage-a-approval.json', approval)
        stage_a = BASE / output
        stage_command = ['python3', '-B', str(BASE / 'run-09b.py'), '--materials', str(executable), '--stage', 'A',
                         '--protocol', '--approval', str(packet / 'stage-a-approval.json'), '--output', str(stage_a)]
        (packet / 'STAGE-A-COMMAND.txt').write_text(shlex.join(stage_command) + '\n', encoding='utf-8')
        role_commands = []
        for role in ('ideation', 'executor'):
            p1 = BASE / (('09b-' if scene == '09B' else '09c-') + instance + '-b1-' + role + '-p1-01')
            argv = ['python3', '-B', str(BASE / 'prepare-a14.py'), '--mode', 'role', '--instance', instance,
                    '--prompt-file', str(packet / 'i1-prompt.txt'), '--role', role, '--stage-a', str(stage_a),
                    '--packet', str(executable), '--output', str(p1)]
            if scene == '09B' and role == 'executor':
                argv += ['--result', str(BASE / '09b-a16-b1-ideation-p1-01/phases/I1/execute-02/result.json')]
            role_commands.append(shlex.join(argv))
        (packet / 'ROLE-MATERIAL-COMMANDS.txt').write_text('# Stage A之后只写文件；角色启动/逐屏签字另批。\n' + '\n\n'.join(role_commands) + '\n', encoding='utf-8')
        p1_base = '09b-' if scene == '09B' else '09c-'
        owner_command = ['python3', '-B', str(BASE / 'prepare-rev2-owner.py'), '--mode', 'owner', '--stage-a', str(stage_a),
            '--packet', str(executable), '--ideation', str(BASE / (p1_base + instance + '-b1-ideation-p1-01')),
            '--executor', str(BASE / (p1_base + instance + '-b1-executor-p1-01')), '--output', str(packet / 'owner.json')]
        (packet / 'BIND-OWNER-COMMAND.txt').write_text('# 两个实际B1/逐屏完成、bind-launch后，只读核对并写owner；不启动/停止。\n' + shlex.join(owner_command) + '\n', encoding='utf-8')
        if scene == '09C':
            demand = ['python3', '-B', str(BASE / 'prepare-rev2-owner.py'), '--mode', 'demand', '--result',
                      str(BASE / '09c-c1-b1-ideation-p1-01/phases/C-I1/execute-02/settlement.json'),
                      '--approval', str(BASE / '09c-c1-b1-ideation-p1-01/phases/C-I1/approval.json'),
                      '--output', 'ACTUAL_READINESS_ROOT/continued-demand.json']
            # The concrete root is intentionally unavailable until Stage A.
            # This is a field-binding instruction, not an executable command.
            save(packet / 'CONTINUED-DEMAND-BINDING.json', {'kind': 'DEFERRED_RUNTIME_COMMAND', 'argv': demand,
                'replace_only': {'ACTUAL_READINESS_ROOT': 'this scene Stage A readiness.root'}, 'business_actions': 0})
        save(packet / 'SOURCE.json', {**metadata, 'scene': scene, 'material_package': str(executable),
            'static_root': static['root'], 'source_paths': static['source_paths'], 'runtime_binding': 'NOT_CREATED',
            'regression_status': 'INCOMPLETE; do not launch before both current readbacks PASS', 'launch_status': 'NO_GO'})
        # Runtime values are produced by Stage A/B1, never copied from A15.
        save(packet / 'RUNTIME-FIELDS.json', {'kind': 'UNBOUND_RUNTIME_FIELD_CONTRACT', 'root': 'Stage A readiness.root',
             'claim': 'Stage A actual target_binding, never null at a live entry', 'role_launch': 'actual B1 input/manifest',
             'owner': 'prepare-rev2-owner after both actual B1 manifests', 'permission': 'actual dispatch/PermissionRequest/full screen',
             'signatures': 'executor per stage; none supplied by worker'})
        index['scenes'].append({'scene': scene, 'materials': str(packet), 'executable': str(executable),
                               'source_files': len(static['source_paths']), 'StageA': stage_command})
    save(BASE / 'merge-main-4/frozen-materials.json', index)
    print(json.dumps(index, ensure_ascii=False))


if __name__ == '__main__': main()
