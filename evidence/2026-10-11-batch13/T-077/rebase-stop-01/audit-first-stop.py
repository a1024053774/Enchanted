#!/usr/bin/env python3
"""Source/syntax preflight only; this is not business acceptance evidence."""
from pathlib import Path
import ast
import json
import re
import subprocess

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t077')
HERE = ROOT / 'evidence/2026-10-11-batch13/T-077/rebase-stop-01'
PATHS = ['acceptance/test_run_e2e.py', 'workbench/src/contracts/a2aGates.ts',
         'workbench/src/gates/cli.ts', 'workbench/src/gates/core.ts', 'workbench/src/panes.ts']


def methods(source):
    headers = list(re.finditer(r'^  (?:private )?(?:async )?(\w+)\(', source, re.M))
    result = {}
    for index, match in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(source)
        body = source[match.start():end]
        close = body.rfind('\n  }\n')
        result[match[1]] = body[:close + len('\n  }\n')].strip() if close >= 0 else body.strip()
    return result


commands = []
for name in PATHS:
    source = (ROOT / name).read_text()
    assert not re.search(r'^(<<<<<<<|=======|>>>>>>>)', source, re.M), name
    assert (ROOT / name).read_bytes() == (HERE / 'resolved-final' / name).read_bytes(), name
    if name.endswith('.ts'):
        argv = ['node', '--check', name]
        subprocess.run(argv, cwd=ROOT, check=True)
        commands.append(argv)
    else:
        ast.parse(source, filename=name)
commands.append(['Python ast.parse', PATHS[0]])

core = (ROOT / 'workbench/src/gates/core.ts').read_text()
current = methods(core)
main_methods = ['projectQuality', 'qualityCommand', 'checkQuality', 'checkQualityEvidence',
    'qualityIssue', 'rejectDelivery', 'reviewAttempt', 'requireReviewed', 'reviewLifecycleFailed',
    'requestReview', 'failReviewProtocol', 'reclaimReview', 'scoreData', 'finalScore',
    'runtimeIdentity', 'checkThread', 'bindObservedIdentity']
s3_methods = ['attemptName', 'projectWorktrees', 'checkClaimPaths', 'retainCommit',
    'cleanupAttempt', 'cleanupVerification', 'conflictPrompt', 'writeConflict',
    'integrationWorktree', 'checkIntegrationHead', 'changedPaths', 'checkIntegratedContent',
    'advanceWorkBranch', 'candidateBase']
for side, names in [('main', main_methods), ('t077', s3_methods)]:
    original = methods((HERE / side / 'workbench/src/gates/core.ts').read_text())
    for name in names:
        assert current[name] == original[name], (side, name)
pane_methods = ['createReview', 'sessionFacts', 'qualityFeedback', 'dispatch',
                'drain', 'release', 'signal', 'caller', 'terminate', 'shutdown']
old_panes = methods((HERE / 'main/workbench/src/panes.ts').read_text())
new_panes = methods((ROOT / 'workbench/src/panes.ts').read_text())
for name in pane_methods:
    assert new_panes[name] == old_panes[name], ('panes/main', name)
assert new_panes['createPane'] == old_panes['createPane'].replace(
    'native: null, turn: null, active: null,', 'native: null, turn: null, nativeEnded: false, active: null,')
assert core.count('if (args.command === "verify") return await this.verifyCandidate(task, attempt);') == 1
assert core.count('private async verifyCandidate(') == 1
assert 'requested_service_tier: "fast"' not in core
assert 'requested_service_tier: "default"' in core
verify = current['verifyCandidate']
assert 'await this.checkQuality(task, attempt, v);' in verify
assert 'this.checkQualityEvidence(task, attempt, v);' in verify
assert 'await this.requestReview(task, attempt);' in verify
assert 'misses >= 4' in current['revalidateForIntegration']
import_argv = ['node', '-e', 'Promise.all([import("./workbench/src/gates/core.ts"), import("./workbench/src/panes.ts"), import("./workbench/src/contracts/a2aGates.ts")]).then(() => console.log("module imports PASS"))']
subprocess.run(import_argv, cwd=ROOT, check=True)
commands.append(import_argv)
status_argv = ['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', '.']
status = subprocess.run(status_argv, cwd=ROOT, check=True, text=True, capture_output=True)
(HERE / 'project-map-status.txt').write_text(status.stdout + status.stderr)
commands.append(status_argv)
large_files = [str(p.relative_to(ROOT)) for p in HERE.parent.rglob('*') if p.is_file() and p.stat().st_size > 5 * 1024 * 1024]
assert not large_files, large_files
unmerged = subprocess.check_output(['git', 'diff', '--name-only', '--diff-filter=U', '-z'], cwd=ROOT).decode()
assert sorted(filter(None, unmerged.split('\0'))) == sorted(PATHS)
result = {'status': 'PASS', 'scope': 'source_preservation_and_syntax_only',
    'business_acceptance': 'INCOMPLETE: deferred until all rebase commits replay and rebase-final-01 runs',
    'no_git_mutations': True, 'no_real_model_turns': True,
    'unchanged_main_core_methods': main_methods, 'unchanged_s3_core_methods': s3_methods,
    'unchanged_main_pane_methods': pane_methods,
    'main_createPane_only_adds_s3_nativeEnded_initialization': True,
    'commands': commands, 'files_over_5mb': large_files}
(HERE / 'preflight.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
