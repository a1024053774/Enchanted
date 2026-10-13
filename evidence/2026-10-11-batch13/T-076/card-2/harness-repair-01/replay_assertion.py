"""Replay one fixture assertion using saved responses. Never start a daemon."""
import argparse
import ast
import json
from pathlib import Path
from types import SimpleNamespace


class ContractFailure(AssertionError):
    pass


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def methods(path):
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'QualityCase')
    nodes = [node for node in cls.body if isinstance(node, ast.FunctionDef)
             and node.name in ('check', 'red_run_reject_preserves_worker')]
    if len(nodes) != 2:
        raise RuntimeError('The two exact fixture methods are required.')
    namespace = {'ContractFailure': ContractFailure, 'json': json, 'save': save}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--recorded', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    run = json.loads((args.recorded / 'run-result.json').read_text(encoding='utf-8'))['reply']
    tables = json.loads((args.recorded / 'database-readback.json').read_text(encoding='utf-8'))['tables']
    attempt_id = run['run']['attempt_id']
    attempt = next(json.loads(row['data']) for row in tables['attempts'] if row['id'] == attempt_id)
    relay = next(json.loads(row['data']) for row in tables['relay_results'] if row['key'] == 'id:delivery-1')
    git = json.loads((args.recorded / 'git-readback.json').read_text(encoding='utf-8'))
    reference = next(line.split()[0] for line in git['refs'].splitlines() if line.endswith(' refs/heads/main'))
    observed = []
    for label, path in [('before', args.before), ('after', args.after)]:
        loaded = methods(path)
        evidence = args.output / label
        evidence.mkdir()
        instance = SimpleNamespace(assertions=[], evidence=evidence, base=attempt['base_commit'])
        instance.start_run = lambda: attempt
        instance.commit = lambda *a, **kw: run['run']['details']['C']
        instance.worker_submit = lambda *a, **kw: relay
        instance.finish_run = lambda: run
        instance.cli = lambda command: {'task': run['task']} if command == 'status' else None
        instance.oid = lambda: reference
        instance.rows = lambda table: tables[table]
        instance.check = lambda *a: loaded['check'](instance, *a)
        result = {'label': label, 'method_source': str(path), 'assertions': instance.assertions}
        try:
            loaded['red_run_reject_preserves_worker'](instance)
            result['outcome'] = 'returned'
        except Exception as error:
            result.update(outcome=type(error).__name__, message=str(error))
        result['readback_saved'] = (evidence / 'run-repair-readback.json').is_file()
        observed.append(result)
    valid = (observed[0]['outcome'] == 'TypeError' and observed[0]['assertions'] == []
             and observed[1]['outcome'] == 'ContractFailure' and observed[1]['message'] == 'RED-RUN-REPAIR'
             and len(observed[1]['assertions']) == 1 and not observed[1]['assertions'][0]['passed']
             and observed[1]['readback_saved'])
    save(args.output / 'run.json', {'status': 'PASS' if valid else 'INCOMPLETE',
         'scope': 'offline fixture classification only; not a new product run',
         'recorded': str(args.recorded), 'observed': observed, 'real_codex_turns': 0})
    print(json.dumps({'status': 'PASS' if valid else 'INCOMPLETE',
                      'outcomes': [row['outcome'] for row in observed], 'real_codex_turns': 0}))
    return 0 if valid else 1


if __name__ == '__main__':
    raise SystemExit(main())
