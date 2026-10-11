#!/usr/bin/env python3
"""Read-only field/argv audit of the failed preimage and current candidate.

This audits interface usage, not business acceptance. No daemon/PTY/provider.
"""
import argparse
import ast
import copy
import difflib
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[3]
E = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
failed = E / 'outside-relay-check-01/preimage'
test_path = 'workbench/tests/test_relay_conflict_e2e.py'
with tarfile.open(failed / 'sources.tar.gz') as archive:
    originals = {m.name: archive.extractfile(m).read() for m in archive if m.isfile()}
changed_product = [name for name, data in originals.items()
                   if name.startswith(('workbench/src/', 'workbench/hooks/')) and (ROOT / name).read_bytes() != data]
assert changed_product == ['workbench/src/relay.ts'], changed_product
for name in ['workbench/tests/test_task_cards_e2e.py', 'workbench/tests/relay_conflict_host.ts']:
    assert (ROOT / name).read_bytes() == originals[name], name
old_text = originals[test_path].decode('utf-8'); text = (ROOT / test_path).read_text(encoding='utf-8')
old, new = ast.parse(old_text), ast.parse(text)


class NormalizePaneCall(ast.NodeTransformer):
    def visit_Attribute(self, node):
        self.generic_visit(node)
        if isinstance(node.value, ast.Name) and node.value.id == 'self' and node.attr == 'pane_cli':
            node.attr = 'cli'
        return node


def assertions(tree):
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
    rows = {}
    for method in cls.body:
        if not isinstance(method, ast.FunctionDef) or method.name == 'pane_cli':
            continue
        rows[method.name] = [ast.dump(NormalizePaneCall().visit(copy.deepcopy(n)), include_attributes=False)
            for n in ast.walk(method) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and isinstance(n.func.value, ast.Name) and n.func.value.id == 'self' and n.func.attr.startswith('assert')]
    return rows


assert assertions(old) == assertions(new), 'Existing assertions changed'
commands = json.loads((failed / 'commands.json').read_text(encoding='utf-8'))
status = next(json.loads(c['stdout']) for c in commands if 'status' in c['argv'])
attempt = status['task']['current_attempt']; launch = attempt['runtime_identity']['launch']
assert 'launch' not in status
with tarfile.open(failed / 'fixtures.tar.gz') as archive:
    env_file = next(m for m in archive if m.isfile() and m.name.endswith('/' + launch + '.env.json'))
    env = json.loads(archive.extractfile(env_file).read())
    runtime_file = next(m for m in archive if m.isfile() and m.name.endswith('/' + launch + '.runtime.json'))
    runtime = json.loads(archive.extractfile(runtime_file).read())
assert env['A2A_LAUNCH'] == launch and env['A2A_ATTEMPT'] == attempt['attempt_id']
assert env['A2A_SESSION'] == attempt['session_id'] and int(env['A2A_FENCE']) == attempt['fence']
assert runtime['cwd'] == attempt['workspace']
oracle_source = status['task']['card']['completion_conditions'][0]['argv'][-1]
assert ast.literal_eval(ast.parse(oracle_source).body[1].test.comparators[0]) == 'worker+host\n'

# These exact source anchors locate the producers manually inspected for both
# versions. They are interface references, not generated behavioral oracles.
anchors = {
    'workbench/src/gates/cli.ts': [
        'const commands:', 'const noTask =', 'const allowed =',
        'await emit(request.command === "signal" && result.ok ? {} : result);'],
    'workbench/src/daemon.ts': [
        'if (input.command === "workbench_snapshot")', 'if (input.command === "pane_status")',
        'if (input.command === "pane_process_info")', 'if (input.command === "pane_release")'],
    'workbench/src/gates/core.ts': [
        'private async claim(', '...(conflict ? { conflict_source:', 'return { ok: true, task, attempt };',
        'if (args.command === "status")', 'if (args.command === "events")'],
    'workbench/src/panes.ts': ['A2A_SESSION: attempt.session_id', 'A2A_REQUEST_DIR: requestDirectory',
                              'status(thread: string)', 'runtime_identity: { launch:'],
    'workbench/src/relayFiles.ts': ['return { ok: true, queued: true, delivered: false'],
    'workbench/src/relay.ts': ['key TEXT PRIMARY KEY, launch TEXT NOT NULL', 'request_id TEXT, input TEXT NOT NULL',
                             'CREATE TABLE IF NOT EXISTS relay_results'],
    'workbench/tests/relay_conflict_host.ts': ['const runtime = { native, file, cwd:', 'launch + ".env.json"'],
}
references = {}
for version in ('preimage', 'candidate'):
    references[version] = {}
    for name, needles in anchors.items():
        source = originals[name].decode('utf-8') if version == 'preimage' else (ROOT / name).read_text(encoding='utf-8')
        lines = source.splitlines(); entries = []
        for needle in needles:
            matches = [(i + 1, line) for i, line in enumerate(lines) if needle in line]
            assert matches, (version, name, needle)
            entries.extend({'line': i, 'source': line.strip()} for i, line in matches)
        references[version][name] = entries
field_reads = [{'line': n.lineno, 'expression': ast.get_source_segment(text, n)} for n in ast.walk(new)
    if isinstance(n, ast.Subscript) and isinstance(n.ctx, ast.Load) and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str)]
pane_calls = [n for n in ast.walk(new) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and
              n.func.attr in ('cli', 'pane_cli') and n.args and isinstance(n.args[0], ast.Constant)]
for call in pane_calls:
    command = call.args[0].value
    assert (call.func.attr == 'pane_cli') == command.startswith('pane_'), command
    if command.startswith('pane_'):
        assert '--task' not in [a.value for a in call.args if isinstance(a, ast.Constant)]
report = {'status': 'PASS', 'scope': 'Static interface and archived-field checks only; end-to-end pending',
    'product_delta_since_failed_preimage': changed_product, 'existing_assertions_unchanged': True,
    'old_status_top_level': sorted(status), 'launch_from_persisted_status': launch,
    'archived_env_matches_status_tuple': True, 'oracle_literal_is_combined_content_with_newline': True,
    'field_reads': field_reads, 'references': references, 'real_codex_turns': 0}
(args.output / 'audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(args.output / 'fixture.patch').write_text(''.join(difflib.unified_diff(old_text.splitlines(True), text.splitlines(True),
    fromfile='failed-preimage/' + test_path, tofile='candidate/' + test_path)), encoding='utf-8')
print(json.dumps({k: report[k] for k in ('status', 'scope', 'existing_assertions_unchanged', 'real_codex_turns')}))
