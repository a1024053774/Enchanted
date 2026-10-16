"""Exercise the cleanup boundary with real Unix sockets and lsof; no signals."""
import argparse
import importlib.util
import json
import os
import socket
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    out = parser.parse_args().output.resolve(); out.mkdir(exist_ok=False)
    cleanup = load('cleanup', BASE / 'cleanup-pending-timeout.py')
    archive = load('archive', BASE / 'cleanup-09b-stage-a-03.py')
    result = {'status': 'INCOMPLETE', 'checks': [], 'signals_sent': [],
              'scope': 'real AF_UNIX/lsof and archive readback; no retained fixture or A13 cleanup'}
    try:
        with tempfile.TemporaryDirectory(prefix='t078-socket-test-', dir='/private/tmp') as temporary:
            root = Path(temporary); (root / 'state').mkdir()
            (root / 'regular.txt').write_text('固定读回内容\n', encoding='utf-8')
            path = root / 'state/control.sock'
            with socket.socket(socket.AF_UNIX) as live:
                live.bind(str(path)); live.listen(1); observation = {}
                try:
                    cleanup.remove_residual_socket(root, observation)
                except AssertionError as error:
                    assert str(error) == 'socket_still_held_no_unlink'
                    assert path.exists() and observation['residual_socket']['held_by_process'] is True
                    result['checks'].append({'name': 'held_socket_refused', 'status': 'PASS', 'observed': observation})
                else:
                    raise AssertionError('live socket was removed')
            observation = {}; cleanup.remove_residual_socket(root, observation)
            assert not path.exists() and observation['residual_socket']['held_by_process'] is False
            assert observation['residual_socket']['removed'] is True
            inventory = archive.archive_and_verify(root, out / 'fixture.tar.gz')
            result['checks'].append({'name': 'stale_socket_logged_removed_and_archive_verified', 'status': 'PASS',
                                     'observed': observation, 'inventory': inventory})
            os.mkfifo(root / 'unexpected.fifo')
            try:
                archive.archive_and_verify(root, out / 'forbidden.tar.gz')
            except RuntimeError as error:
                assert 'unsupported filesystem member' in str(error)
                result['checks'].append({'name': 'other_special_type_refused', 'status': 'PASS', 'error': str(error)})
            else:
                raise AssertionError('FIFO was accepted')
        result['status'] = 'PASS'
    except Exception as error:
        result['error'] = repr(error)
    (out / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
