"""Observe the launch argv without starting Electron; retain the failing old path."""
import argparse
import json
from pathlib import Path
import runpy
import tempfile
from unittest.mock import patch

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
evidence = Path(__file__).resolve().parent
root = evidence.parents[3]
old_source = Path(json.loads((evidence / 'outside-checks-02/verdict.json').read_text())['source'])
expected = str(root / 'workbench/node_modules/electron/dist/Electron.app/Contents/MacOS/Electron')
assert Path(expected).is_file()
fixture = Path(tempfile.mkdtemp(prefix='a2a4path-', dir='/tmp'))
results = []


class Captured(Exception):
    pass


for label, path in [('known_bad', old_source / 'workbench/tests/electron_client.py'),
                    ('candidate', root / 'workbench/tests/electron_client.py')]:
    module = runpy.run_path(str(path))
    observed = {}

    def capture(argv, **kwargs):
        observed['argv'] = argv
        kwargs['stderr'].close()
        raise Captured()

    with patch.object(module['subprocess'], 'Popen', side_effect=capture):
        try:
            module['ElectronClient'](old_source, fixture / 'build', fixture / 'state', 'path-check',
                                     fixture / 'ui', fixture / label, {})
        except Captured:
            pass
        else:
            raise AssertionError('The launch boundary was not observed')
    results.append({'version': label, 'module': str(path), 'binary': observed['argv'][0],
                    'expected': expected, 'matches': observed['argv'][0] == expected})
assert results[0]['matches'] is False and results[1]['matches'] is True
with args.output.open('x', encoding='utf-8') as stream:
    json.dump({'status': 'PASS', 'electron_spawned': False, 'fixture': str(fixture),
               'results': results}, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print('PASS: old argv rejected; candidate argv is the canonical executable; Electron not started')
