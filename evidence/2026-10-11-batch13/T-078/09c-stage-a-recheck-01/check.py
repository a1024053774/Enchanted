"""只读核对主控 #350 的回收收据与既有 09C 冻结；不调用场景入口。"""
import copy
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile
import traceback

BASE = Path(__file__).resolve().parents[1]
SOURCE = BASE.parents[2]
sys.path.insert(0, str(SOURCE / 'workbench/tests'))
from t078_raw_retention import readback, verify_archive


def load(path):
    return json.loads(Path(path).read_bytes())


def git(*args):
    return subprocess.check_output(['git', *args], cwd=SOURCE)


def main():
    output = Path(__file__).with_name('result.json')
    assert not output.exists(), output
    result = {'status': 'INCOMPLETE', 'checked_HEAD': git('rev-parse', 'HEAD').decode().strip(),
              'scope': '只读 Git、归档、JSON 与 Stage A 输入校验；未调用 main/card/root/daemon/API/角色入口',
              'scene_process_starts': 0, 'signals_sent': [], 'SQLite_reads': 0,
              'live_signatures_written': False}
    try:
        closeout = BASE / '09b-a16-closeout-materials-01'
        owner = load(BASE / '09b-a16-materials-01/owner.json')
        dry = load(BASE / '09b-a16-cleanup-01-dry-run/result.json')
        finish = load(BASE / '09b-a16-cleanup-01/result.json')
        approval = load(closeout / 'cleanup-approval.json')
        signed = load(BASE / '09b-a16-raw-readback-01/readback.json')
        review = load(BASE / '09b-a16-raw-readback-01/a16-review-check.json')
        bundle = load(closeout / 'bundle.archive.json')
        pointers = load(closeout / 'raw-pointers.archive.json')
        archive = Path(bundle['archive'])
        assert bundle == load(archive.parent / 'bundle.archive.json')
        assert bundle['status'] == bundle['byte_readback'] == 'PASS'
        assert archive.stat().st_size == bundle['archive_bytes'] == finish['archive_bytes'] == 826185
        inventory = verify_archive(bundle['staging'], archive)
        assert inventory == bundle['inventory'] and len(inventory) == 929
        counts = readback(archive)
        assert signed['counts'] == counts
        assert counts['Messages_POST'] == {'ideation': 6, 'executor': 11}
        assert counts['roots'] == {'ideation': 4, 'executor': 6}
        assert {r: len(v) for r, v in counts['permission_requests'].items()} == {'ideation': 2, 'executor': 5}
        assert not counts['unfinished_http'] and not counts['unfinished_hooks']
        assert signed['approved_by'] == approval['approved_by'] == 'executor'
        assert signed['approval_ref'] and approval['approval_ref']
        assert review['status'] == 'PASS' and review['counts'] == {'POST': 17, 'roots': 10, 'permissions': 7}
        assert dry['status'] == 'PASS' and dry['dry_run'] and not dry['signals_sent'] and not dry['root_removed']
        assert finish['status'] == 'PASS' and finish['root_removed'] and not finish['dry_run']
        assert finish['post_stop_SQLite_reads'] == 0 and not Path(owner['root']).exists()
        assert finish['signals_sent'] == [{'pid': owner['processes'][r + '_api']['pid'], 'signal': 'SIGTERM'}
                                           for r in ['ideation', 'executor']]
        assert len(owner['processes']) == 9
        with tarfile.open(archive) as tar:
            snapshot = json.load(tar.extractfile('snapshot.json'))
            members = set(tar.getnames())
            for item in snapshot['records']:
                pointer = load(Path(pointers['pointers_directory']) / (item['logical'] + '.archive.json'))
                assert pointer['archive'] == str(archive) and pointer['member'] == 'files/' + item['logical']
                assert pointer['member'] in members and pointer['byte_readback'] == 'PASS'
        result['A16'] = {'status': 'PASS', 'archive': str(archive), 'archive_bytes': 826185,
                         'members': len(inventory), 'individual_raw_pointers': len(snapshot['records']),
                         'POST': counts['Messages_POST'], 'roots': counts['roots'],
                         'permissions': {r: len(v) for r, v in counts['permission_requests'].items()},
                         'archive_vs_staging_bytes': 'PASS', 'signed_executor_recount_matches_tar': True,
                         'cleanup': 'PASS', 'owned_processes': 9, 'root_removed': True,
                         'post_stop_SQLite_reads': 0, 'F1': 'A16 补证已保留；A15 原件缺失历史不改'}

        packet = BASE / '09c-materials-01'
        executable = BASE / '09c-executable-materials-02'
        live = load(packet / 'stage-a-approval.json')
        static = load(executable / 'static-check.json')
        metadata = load(packet / 'SOURCE.json')
        frozen_revision = static['revision']
        assert frozen_revision == metadata['revision'] == live['source_revision']
        assert frozen_revision == '7a6edbff87df85077b3a05d38f3cfd5654cde9c1'
        assert live['approved_by'] is None and live['approval_ref'] is None
        paths = load(executable / 'source-files.json')
        assert paths == static['source_paths'] == metadata['source_paths'] and len(paths) == 312
        with tarfile.open(executable / 'sources.tar.gz') as tar:
            assert set(tar.getnames()) == set(paths)
            for path in paths:
                frozen = tar.extractfile(path).read()
                assert frozen == (SOURCE / path).read_bytes() == git('show', frozen_revision + ':' + path), path
        spec = importlib.util.spec_from_file_location('stage_a_preflight', BASE / 'run-09b.py')
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        runner.validate_material_lineage(executable, static)
        try:
            runner.validate_stage_a_inputs(executable, live, protocol=True)
        except AssertionError:
            unsigned_rejected = True
        else:
            raise AssertionError('未签批准不应通过')
        # 此副本只在内存中用于静态输入校验，不写入批准件，不调用 runner.main。
        synthetic = copy.deepcopy(live)
        synthetic.update(approved_by='executor', approval_ref='只读校验内存夹具；不是运行批准')
        checked = runner.validate_stage_a_inputs(executable, synthetic, protocol=True)
        argv = shlex.split((packet / 'STAGE-A-COMMAND.txt').read_text(encoding='utf-8'))
        assert Path(argv[2]) == BASE / 'run-09b.py' and Path(argv[2]).is_file()
        assert argv[argv.index('--materials') + 1] == str(executable)
        assert argv[argv.index('--approval') + 1] == str(packet / 'stage-a-approval.json')
        assert argv[argv.index('--stage') + 1] == 'A' and '--protocol' in argv
        new_output = Path(argv[argv.index('--output') + 1])
        assert new_output == BASE / '09c-stage-a-01' and not new_output.exists()
        budget = load(packet / 'BUDGET.json')
        assert budget['ideation'] == {'roots': 4, 'POST': 7}
        assert budget['executor'] == {'roots': 1, 'POST': 1} and budget['models'] == 0
        result['09C'] = {'status': 'PASS', 'source_revision': frozen_revision, 'source_members_byte_equal': len(paths),
                         'material_package': str(executable), 'static_root': static['root'],
                         'refreeze_required': False, 'unsigned_approval_rejected': unsigned_rejected,
                         'approval_still_unsigned': True, 'launch_status': 'NO_GO',
                         'regression_validation': checked['regression_validation'],
                         'StageA_argv': argv, 'StageA_output_absent': True, 'budget': budget,
                         'actual_StageA': 'NOT_RUN'}
        result['status'] = 'PASS'
    except Exception as error:
        result.update(error=repr(error), traceback=traceback.format_exc())
    with output.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'output': str(output), 'scene_process_starts': 0,
                      **({'error': result['error']} if 'error' in result else {})}, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
