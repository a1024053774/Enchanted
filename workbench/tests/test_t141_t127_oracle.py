"""Exercise the four revised T-127 predicates with independent good/bad inputs.

Failure modes: rejecting a trusted worker; accepting a trust override, rewritten
home or reviewer project hook. This tests the oracle, not native CLI behavior.
"""
import argparse
import ast
import json
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, default=Path(__file__).with_name('test_t127_codex_home_e2e.py'))
parser.add_argument('--summary', type=Path, required=True)
args = parser.parse_args()
assert not args.summary.exists(), 'Fresh summary path required'
tree = ast.parse(args.source.read_text(encoding='utf-8'))
checks = {node.args[0].value: node.args[1] for node in ast.walk(tree)
          if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'check'
          and isinstance(node.args[0], ast.Constant)}
report = dict(status='INCOMPLETE', source=str(args.source), scope='Oracle predicate counterexamples; no native CLI claim', checks=[])


def predicate(old, new, values, expected):
    expression = checks[new] if new in checks else checks[old]
    observed = bool(eval(compile(ast.Expression(expression), str(args.source), 'eval'), dict(values)))
    assert observed is expected, (new, values, expected, observed)
    report['checks'].append(dict(check=new, expected=expected))


try:
    for startup, expected in [(['turn_submitted'], True), ([], False),
                               (['codex_restricted_open_intent', 'codex_restricted_opened', 'turn_submitted'], False)]:
        predicate('restricted_answered_before_first_task', 'trusted_worker_starts_directly', dict(startup=startup), expected)
    for argv, expected in [(['codex', '-a', 'never'], True),
                            (['codex', '-c', 'projects={"/sentinel"={trust_level="untrusted"}}'], False),
                            (['codex', '-c', 'projects.sentinel.trust_level="trusted"'], False)]:
        predicate('worker_folder_untrusted_in_argv', 'worker_trust_not_overridden', dict(argv=argv), expected)
    before = '[projects."/independent-demo"]\ntrust_level = "trusted"\n'
    values = dict(changed=[], added='\n[tui]\nscreen_reader_detection_done=true\n', headers=['[tui]'],
                  config_before=before, config_after=before+'\n[tui]\nscreen_reader_detection_done=true\n')
    predicate('user_home_not_rewritten', 'user_home_not_rewritten', values, True)
    for change in [dict(changed=['hooks.json']), dict(added=None), dict(headers=['[projects.injected]']),
                   dict(added='\n[projects.injected]\ntrust_level="trusted"\n')]:
        predicate('user_home_not_rewritten', 'user_home_not_rewritten', dict(values, **change), False)
    for markers, expected in [(['home-hook-Stop-worker', 'home-hook-Stop-reviewer', 'project-hook-Stop-worker'], True),
                               (['project-hook-Stop-reviewer'], False), (['project-config-hook-reviewer'], False)]:
        predicate('project_codex_hooks_not_run', 'reviewer_project_codex_hooks_not_run', dict(markers=markers), expected)
    mutations = next(ast.literal_eval(node.value) for node in ast.walk(tree) if isinstance(node, ast.Assign)
                     and any(isinstance(target, ast.Name) and target.id == 'table' for target in node.targets))
    cases = next(ast.literal_eval(node.value.value) for node in ast.walk(tree) if isinstance(node, ast.AugAssign)
                 and isinstance(node.value, ast.Subscript) and isinstance(node.value.value, ast.Dict))
    report['mutation_targets'] = []
    with tempfile.TemporaryDirectory(prefix='t141-t127-mutations-') as temporary:
        for name, patches in list(mutations.items()) + list(cases.items()):
            texts = {}
            for path, old, new in patches:
                text = texts.get(path, (args.source.resolve().parent.parent / path).read_text(encoding='utf-8'))
                assert text.count(old) == 1, (name, path, 'Mutation target must be unique')
                texts[path] = text.replace(old, new)
            for path, text in texts.items():
                target = Path(temporary) / Path(path).name
                target.write_text(text, encoding='utf-8')
                subprocess.run(['node', '--check', str(target)], check=True, capture_output=True, text=True)
            report['mutation_targets'].append(name)
    report['status'] = 'PASS'
except Exception as error:
    report['error'] = f'{type(error).__name__}: {error}'
finally:
    args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
