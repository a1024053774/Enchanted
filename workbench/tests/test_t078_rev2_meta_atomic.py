"""Probe the actual metadata writer at the truncate/write interleaving."""
import argparse
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
from t078_raw_retention import HttpExchange


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--legacy-writer', action='store_true')
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    observed = []; original = Path.write_text
    with tempfile.TemporaryDirectory(prefix='t078-meta-atomic-', dir='/private/tmp') as td:
        root = Path(td); target = root / 'http-exchanges/0001.meta.json'
        def interleaved_write(path, data, *a, **kw):
            if path.name.startswith('0001.meta.'):
                with path.open('w', encoding='utf-8') as stream:
                    if target.exists():
                        try: json.loads(target.read_bytes()); observed.append('valid_original')
                        except ValueError: observed.append('invalid_json_visible')
                    else: observed.append('not_published_yet')
                    stream.write(data)
                return len(data)
            return original(path, data, *a, **kw)
        def legacy(self):
            (self.base / (self.label + '.meta.json')).write_text(json.dumps(self.meta), encoding='utf-8')
        with patch.object(Path, 'write_text', interleaved_write):
            if args.legacy_writer:
                with patch.object(HttpExchange, 'persist', legacy):
                    record = HttpExchange(root, 1, 'POST', '/v1/messages', 'application/json', b'{}', 'ideation')
                    record.finish(409, 'application/json', True)
            else:
                record = HttpExchange(root, 1, 'POST', '/v1/messages', 'application/json', b'{}', 'ideation')
                record.finish(409, 'application/json', True)
        status = 'INCOMPLETE' if 'invalid_json_visible' in observed else 'PASS'
        result = {'status': status, 'legacy_writer': args.legacy_writer, 'interleaving': 'after open/truncate before write',
                  'observed': observed, 'final_complete': json.loads(target.read_bytes())['complete'], 'processes': 0}
    (args.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result)); return 0 if status == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
