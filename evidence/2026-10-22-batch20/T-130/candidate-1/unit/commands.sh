#!/bin/zsh
# T-130 candidate 1 unit evidence: run from workbench/. The hook test on the candidate, on the parent revision's hook
# and on nine known-bad copies of hooks/hook.py that this script makes in a temporary directory.
E=../evidence/2026-10-22-batch20/T-130/candidate-1/unit
M=$(mktemp -d)
python3 tests/test_t130_hook_claude_facts.py $E/hook-green.json > $E/hook-green.log 2>&1; print "hook-green exit=$?" >> $E/exits.txt
git -C .. show 04354734b:workbench/hooks/hook.py > $M/parent.py
python3 - $M <<'PY'
import sys
src = open('hooks/hook.py').read()
mutants = {
  'synthetic-kept': ("if isinstance(model, str) and model and model != '<synthetic>':", "if isinstance(model, str) and model:"),
  'half-line-read': ("            if not line.endswith('\\n'):\n                break  # An incomplete append cannot provide current-turn facts.\n            record = json.loads(line)\n            if not isinstance(record, dict) or record.get('type') != 'assistant':",
                     "            record = json.loads(line)\n            if not isinstance(record, dict) or record.get('type') != 'assistant':"),
  'any-session-file': ("projects.glob('*/' + native + '.jsonl')", "projects.glob('*/*.jsonl')"),
  'duplicate-first': ("    if len(files) != 1 or projects not in files[0].resolve().parents:\n        raise ValueError('原生会话记录不唯一或路径越界')\n    latest = None",
                      "    if projects not in files[0].resolve().parents:\n        raise ValueError('原生会话记录不唯一或路径越界')\n    latest = None"),
  'session-unchecked': ("            if record.get('sessionId') != native:\n                raise ValueError('原生记录不是本会话')\n", ""),
  'effort-field-only': ("(latest.get('effort'), latest.get('perTurnEffort'))", "(latest.get('effort'),)"),
  'disagreement-first': ("    if len(efforts) > 1:\n        raise ValueError('原生记录的强度字段不一致')\n", ""),
  'missing-refused': ("    if not files:\n        return 'unknown', 'unknown'\n    if len(files) != 1 or projects",
                      "    if not files:\n        raise ValueError('missing')\n    if len(files) != 1 or projects"),
  'home-only': ("Path(env.get('CLAUDE_CONFIG_DIR') or Path(env['HOME']) / '.claude')", "(Path(env['HOME']) / '.claude')"),
}
for name, (old, new) in mutants.items():
    assert src.count(old) == 1, name
    open(f'{sys.argv[1]}/{name}.py', 'w').write(src.replace(old, new))
PY
for m in parent synthetic-kept half-line-read any-session-file duplicate-first session-unchecked effort-field-only disagreement-first missing-refused home-only; do
  python3 tests/test_t130_hook_claude_facts.py $E/hook-$m.json $M/$m.py > $E/hook-$m.log 2>&1; print "hook-$m exit=$?" >> $E/exits.txt
done
