"""Freeze the approved read-only delta and write commands; never contact a scene."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import tarfile

BASE = Path(__file__).resolve().parent.parent
SOURCE = BASE.parents[2]
OUT = BASE / '09b-a15-reader-harness-01'
ORIGINAL = BASE / '09b-executable-materials-15'
IP = BASE / '09b-a15-b1-ideation-p1-01'
EP = BASE / '09b-a15-b1-executor-p1-01'
STAGE = BASE / '09b-a15-stage-a-01'
CHANGED = ['workbench/tests/run_t078_p1.py', 'workbench/tests/t078_09b_i1_permission.py', 'workbench/tests/t078_09b_phase_driver.py']
ADDED = ['workbench/tests/p1_output.py', 'workbench/tests/recover_t078_permission_screen.py',
         'workbench/tests/run_t078_frozen_harness.py', 'workbench/tests/test_t078_output_paging.py',
         'workbench/tests/test_t078_phase_capture.py', 'workbench/tests/test_t078_permission_recovery.py',
         'workbench/tests/test_t078_frozen_reader.py']


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--check-only', action='store_true'); args = parser.parse_args()
    assert not OUT.exists()
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip()
    assert not subprocess.check_output(['git', 'diff', 'HEAD', '--', 'workbench'], cwd=SOURCE)
    assert not subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '--', 'workbench'], cwd=SOURCE)
    with tarfile.open(ORIGINAL / 'sources.tar.gz') as old:
        original_names = old.getnames()
        differences = [name for name in original_names if (SOURCE / name).read_bytes() != old.extractfile(name).read()]
    assert sorted(differences) == sorted(CHANGED), differences
    names = original_names + ADDED; assert len(names) == len(set(names))
    for name in names:
        assert (SOURCE / name).is_file()
        assert (SOURCE / name).read_bytes() == subprocess.check_output(['git', 'show', revision + ':' + name], cwd=SOURCE)
    for p in [IP / 'input.json', EP / 'input.json', EP / 'launch-binding.json', EP / 'phases/E4/dispatch-01/result.json', EP / 'phases/E4/permission-approval-01.json']:
        assert p.is_file()
    assert not (EP / 'phases/E4/permission-approval-02.json').exists()
    assert not (EP / 'phases/E4/screen-recovery-02').exists()
    for label in ['a15-executor-E4-permission-screen-02', 'a15-executor-E4-permission-screen-03',
                  'a15-executor-E5-permission-screen-01', 'a15-executor-E5-permission-screen-02']:
        assert not (EP / label).exists()
    report = {'status': 'PASS', 'harness_revision': revision,
              'business_revision': json.loads((ORIGINAL / 'static-check.json').read_bytes())['revision'],
              'original_materials': str(ORIGINAL), 'changed_original_files': sorted(CHANGED),
              'added_files': ADDED, 'unchanged_original_files': len(original_names) - len(CHANGED),
              'source_files': len(names), 'scene_actions': 0}
    if args.check_only:
        print(json.dumps(report)); return
    OUT.mkdir(); (OUT / 'commands').mkdir()
    with tarfile.open(OUT / 'sources.tar.gz', 'x:gz') as archive:
        for name in names: archive.add(SOURCE / name, arcname=name)
    save(OUT / 'source-files.json', names); save(OUT / 'manifest.json', report)
    wrapper = SOURCE / 'workbench/tests/run_t078_frozen_harness.py'
    def command(entry, argv):
        return shlex.join(['python3', '-B', str(wrapper), '--freeze', str(OUT), '--entry', entry, '--', *map(str, argv)])
    def write(name, commands):
        with (OUT / 'commands' / name).open('x', encoding='utf-8') as stream:
            stream.write('set -e\n' + '\n'.join(commands) + '\n')
    binding = json.loads((EP / 'launch-binding.json').read_bytes()); manifest = Path(binding['process_manifest']); assert manifest.is_file()
    def screen(stage, suffix):
        return command('screen', ['--materials', EP, '--source-materials', OUT, '--reuse-stage-a', '--launch-label', binding['launch_label'],
                                 '--phase', 'screen', '--label', f'a15-executor-{stage}-permission-screen-{suffix}', '--screen-id', f'executor-{stage}-permission'])
    folder = EP / 'phases/E4'; recovery = folder / 'screen-recovery-02'
    write('E4-01-READ-02.txt', [screen('E4', '02')])
    write('E4-02-RECOVER-REFERENCE.txt', [command('recover', ['--p1', EP, '--original-result', folder / 'dispatch-01/result.json',
          '--screen-dir', EP / 'a15-executor-E4-permission-screen-02', '--output', recovery,
          '--approval-output', folder / 'permission-approval-02.json'])])
    write('E4-03-READ-03-CMP.txt', [screen('E4', '03'), shlex.join(['cmp', '--', str(EP / 'a15-executor-E4-permission-screen-03/screen.bin'), str(recovery / 'permission-screen.bin')])])
    def permission(stage, result, approval, output, check=False):
        argv = ['--materials', EP, '--p1', EP, '--stage', stage, '--stage-a', STAGE, '--dispatch-result', result,
                '--process-manifest', manifest, '--approval', approval, '--output', output]
        return command('permission', argv + (['--check-only'] if check else []))
    write('E4-04-CHECK-ONLY.txt', [permission('E4', recovery / 'result.json', folder / 'permission-approval-02.json', folder / 'permission-verify-03', True)])
    write('E4-05-ENTER.txt', [permission('E4', recovery / 'result.json', folder / 'permission-approval-02.json', folder / 'execute-02')])
    def phase(stage, action, label):
        p = EP / 'phases' / stage
        return command('phase', ['--mode', 'execute', '--protocol', '--stage', stage, '--materials', EP, '--stage-a', STAGE,
                                 '--approval', p / 'approval.json', '--protocol-phase', action, '--output', p / label])
    write('E4-06-READBACK.txt', [phase('E4', 'collect', 'readback-03')])
    write('E5-01-START.txt', [phase('E5', 'dispatch', 'dispatch-01')])
    folder = EP / 'phases/E5'
    for suffix in ['01', '02']:
        write('E5-02-READ-' + suffix + '-CMP.txt', [screen('E5', suffix), shlex.join(['cmp', '--', str(EP / f'a15-executor-E5-permission-screen-{suffix}/screen.bin'), str(folder / 'dispatch-01/permission-screen.bin')])])
    write('E5-03-PREPARE-PERMISSION.txt', [command('prepare-permission', ['--mode', 'permission', '--p1', EP,
          '--result', folder / 'dispatch-01/result.json', '--output', folder / 'permission-approval-01.json'])])
    write('E5-04-CHECK-ONLY.txt', [permission('E5', folder / 'dispatch-01/result.json', folder / 'permission-approval-01.json', folder / 'permission-verify-03', True)])
    write('E5-05-ENTER.txt', [permission('E5', folder / 'dispatch-01/result.json', folder / 'permission-approval-01.json', folder / 'execute-02')])
    write('E5-06-READBACK.txt', [phase('E5', 'collect', 'readback-03')])
    write('E6-01-START.txt', [phase('E6', 'dispatch', 'dispatch-01')]); write('E6-02-READBACK.txt', [phase('E6', 'collect', 'readback-03')])
    template = json.loads((EP / 'phases/E4/permission-approval-01.json').read_bytes())
    assert template['approved_by'] is None and template['approval_ref'] is None
    template['screen_file'] = str(recovery / 'permission-screen.bin')
    save(OUT / 'E4-permission-approval-02-template.json', template)
    print(json.dumps(report))


if __name__ == '__main__':
    main()
