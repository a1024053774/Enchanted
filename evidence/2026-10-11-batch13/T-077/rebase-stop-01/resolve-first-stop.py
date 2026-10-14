#!/usr/bin/env python3
"""Resolve the recorded five-file stop, preserving the two gate contracts."""
from pathlib import Path
import json
import re

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t077')
HERE = ROOT / 'evidence/2026-10-11-batch13/T-077/rebase-stop-01'


def replace_once(source, before, after):
    assert source.count(before) == 1, (before[:100], source.count(before))
    return source.replace(before, after, 1)


def conflicts(source, choices):
    pattern = re.compile(r'^<<<<<<< HEAD\n(.*?)^=======\n(.*?)^>>>>>>> [^\n]+\n', re.M | re.S)
    blocks = list(pattern.finditer(source))
    assert len(blocks) == len(choices), (len(blocks), len(choices))
    for match, choose in reversed(list(zip(blocks, choices))):
        main, t077 = match.groups()
        replacement = choose(main, t077) if callable(choose) else (main if choose == 'main' else t077)
        source = source[:match.start()] + replacement + source[match.end():]
    return source


def unresolved(path):
    before = (HERE / 'unresolved' / path).read_text()
    assert (ROOT / path).read_text() == before, f'Working file changed: {path}'
    return before


outputs = {}
path = 'acceptance/test_run_e2e.py'
# T-076 first rejection keeps this owned worker alive for repair. The S3
# ended-worker cleanup assertions remain in their separate lifecycle cases.
outputs[path] = conflicts(unresolved(path), ['main'])
outputs[path] = replace_once(outputs[path],
    '        expected_refs[f"refs/a2a/attempts/{self.task}/a1"] = candidate\n        expected_refs[f"refs/a2a/verifications/{self.task}/a1/v1"] = candidate',
    '        expected_refs[f"refs/a2a/verifications/{self.task}/a1/v1"] = candidate')

path = 'workbench/src/contracts/a2aGates.ts'


def attempt_contract(main, t077):
    delivery, reviews = main.split('}\n\nexport interface A2ARepair {', 1)
    return delivery + t077 + '}\n\nexport interface A2ARepair {' + reviews


def verification_contract(main, t077):
    return main + '  };\n' + t077


outputs[path] = conflicts(unresolved(path), [attempt_contract, verification_contract])
path = 'workbench/src/gates/cli.ts'
outputs[path] = conflicts(unresolved(path), [lambda main, _: replace_once(main, '"score-file"', '"score-file", "overlap-reason"')])

path = 'workbench/src/panes.ts'


def pane_methods(main, t077):
    feedback = t077[:t077.index('  async dispatch(')]
    return feedback + main


outputs[path] = conflicts(unresolved(path), [pane_methods])
outputs[path] = replace_once(outputs[path],
    '    check([...this.panes.values()].every((pane) => pane.stopped && pane.archived), "single_worker_slice");',
    '    check([...this.panes.values()].filter((pane) => pane.record.role === "worker")\n      .every((pane) => pane.stopped && pane.archived), "single_worker_slice");')

path = 'workbench/src/gates/core.ts'
source = unresolved(path)
# The last three large hunks interleave shared integrate braces; replace that
# whole command span, rather than selecting individual sides of those hunks.
start = source.index('<<<<<<< HEAD\n      if (args.command === "verify")')
end = source.index('      requireGate(args.command === "reclaim", "invalid_command");', start)
source = source[:start] + '__COMBINED_VERIFY_INTEGRATE__\n' + source[end:]
source = conflicts(source, [
    lambda main, _: replace_once(main, 'chmodSync,', 'chmodSync, existsSync,'),
    lambda main, _: replace_once(main, 'pathAllowed,', 'pathAllowed, pathIntersection,'),
    lambda main, t077: main + t077,
    't077',
    lambda main, _: replace_once(main, '!task.candidate_commit', 'repairing || !task.candidate_commit'),
    lambda main, t077: main + '        await this.cleanupAttempt(task, attempt);\n',
])
source = replace_once(source, '      task.current_attempt = attempt;\n      task.fence',
    '      task.current_attempt = attempt;\n      task.repair = null;\n      task.review = null;\n      task.fence')
source = replace_once(source, '        attempt,\n        ...(args.command === "dispatch")',
    '        attempt,\n        task,\n        ...(args.command === "dispatch")') if '        attempt,\n        ...(args.command === "dispatch")' in source else replace_once(source,
    '        attempt,\n        ...(args.command === "dispatch"\n', '        attempt,\n        task,\n        ...(args.command === "dispatch"\n')
source = replace_once(source, 'requested_service_tier: "fast"', 'requested_service_tier: "default"')

# Start with main's complete quality pipeline; insert only S3's workspace,
# real text-conflict handling and known-outcome cleanup at the same boundaries.
main_verify = (HERE / 'main-verify-block.txt').read_text()
body = main_verify.split('\n', 1)[1].rsplit('      }\n', 1)[0]
body = ''.join(line[4:] if line.startswith('    ') else line for line in body.splitlines(keepends=True))
verify = '  private async verifyCandidate(task: A2ATask, attempt: A2AAttempt): Promise<A2AGateResult> {\n    const taskId = task.task_id;\n' + body + '  }\n'
old_start = source.index('  private async verifyCandidate(')
old_end = source.index('  private async integration(', old_start)
old_verify = source[old_start:old_end]
baseline_start = old_verify.index('    if (attempt.rework?.state === "submitted")')
baseline_end = old_verify.index('    const verification_id', baseline_start)
verify = replace_once(verify, '    const verification_id = randomUUID(),\n      workspace = join(this.root, "verification", verification_id);\n',
    old_verify[baseline_start:baseline_end] + '''    const verification_id = randomUUID();
    const ordinal = Number(this.db.prepare(
      "SELECT count(*) AS n FROM verifications WHERE json_extract(data,'$.attempt.attempt_id')=?",
    ).get(attempt.attempt_id)!.n) + 1;
    const workspace = join(this.projectWorktrees(task), `${this.attemptName(attempt)}-verify-${ordinal}`);
''')
verify = replace_once(verify, '      verification_id,\n      attempt: { ...attempt },',
    '      verification_id,\n      ordinal,\n      attempt: structuredClone(attempt),')
verify = replace_once(verify, '    mkdirSync(join(this.root, "verification"), { recursive: true });',
    '    mkdirSync(this.projectWorktrees(task), { recursive: true });\n    mkdirSync(join(this.root, "verification"), { recursive: true });')
merge_start = old_verify.index('      if (merge.returncode !== 0) {')
merge_end = old_verify.index('      const tree =', merge_start)
new_merge_start = verify.index('      if (merge.returncode !== 0) {')
new_merge_end = verify.index('      const tree =', new_merge_start)
verify = verify[:new_merge_start] + old_verify[merge_start:merge_end] + verify[new_merge_end:]
for check in ['path_boundary', 'commit_trailers']:
    line = f'      await this.rejectDelivery(task, attempt, "{check}", {{ error: error.code, details: error.details }});' if check == 'path_boundary' else f'        await this.rejectDelivery(task, attempt, "{check}", {{ error: error.code, details: error.details }});'
    indent = line[:len(line)-len(line.lstrip())]
    verify = replace_once(verify, line, indent + 'await this.cleanupVerification(task, attempt, v);\n' + line)
verify = replace_once(verify,
    '        if (expected) await this.rejectDelivery(task, attempt, failure.error === "rule_check_failed" ? "rule_checks" : "red_state", failure);',
    '        if (expected) {\n          await this.cleanupVerification(task, attempt, v);\n          await this.rejectDelivery(task, attempt, failure.error === "rule_check_failed" ? "rule_checks" : "red_state", failure);\n        }')
verify = replace_once(verify, '    this.save(task, "verification_result", { verification: v, task });\n    if (v.state',
    '    this.save(task, "verification_result", { verification: v, task });\n    await this.cleanupVerification(task, attempt, v);\n    if (v.state')
source = source[:old_start] + verify + source[old_end:]

# S3's CAS loop remains the one integrate path. Main's review/evidence gates,
# score replay binding and atomic finalScore are applied on every iteration.
t077_core = (HERE / 't077' / path).read_text()
integrate_start = t077_core.index('      if (args.command === "integrate") {')
integrate_end = t077_core.index('      requireGate(args.command === "reclaim", "invalid_command");', integrate_start)
integrate = t077_core[integrate_start:integrate_end]
integrate = replace_once(integrate, '      if (args.command === "integrate") {\n',
    '      if (args.command === "integrate") {\n        const score = this.scoreData(args.score_file);\n')
integrate = replace_once(integrate, '        if (task.state === "accepted") {\n',
    '        if (task.state === "accepted") {\n          requireGate(JSON.stringify(score) === JSON.stringify(task.integration_intent?.score?.data), "score_replay_mismatch");\n')
integrate = replace_once(integrate, '          this.checkVerification(task, attempt, v);\n', '''          this.checkVerification(task, attempt, v);
          this.checkQualityEvidence(task, attempt, v);
          this.requireReviewed(task, attempt);
          requireGate(attempt.delivery, "score_provenance_required");
          if (intent) requireGate(intent.score && JSON.stringify(intent.score.data) === JSON.stringify(score), "score_replay_mismatch");
''')
integrate = replace_once(integrate, '              this.save(task, "integrated_reconciled", intent);', '''              this.db.exec("BEGIN IMMEDIATE");
              try {
                this.save(task, "integrated_reconciled", intent);
                this.finalScore(task, attempt, intent);
                this.db.exec("COMMIT");
              } finally { if (this.db.isTransaction) this.db.exec("ROLLBACK"); }''')
integrate = replace_once(integrate, '              state: "pending",\n              command_intent:',
    '              state: "pending",\n              score: { score_id: "score-" + randomUUID(), data: score },\n              command_intent:')
integrate = replace_once(integrate, '          this.save(task, completed ? "integrated" : "integration_conflict", { intent, readback });', '''          this.db.exec("BEGIN IMMEDIATE");
          try {
            this.save(task, completed ? "integrated" : "integration_conflict", { intent, readback });
            if (completed) this.finalScore(task, attempt, intent);
            this.db.exec("COMMIT");
          } finally { if (this.db.isTransaction) this.db.exec("ROLLBACK"); }''')
source = replace_once(source, '__COMBINED_VERIFY_INTEGRATE__\n',
    '      if (args.command === "verify") return await this.verifyCandidate(task, attempt);\n' + integrate)
source = replace_once(source,
    '    // This is an internal call, not a second public request acquiring our lock.\n    // T-076\'s quality chain has a single insertion point here and at verify.',
    '    // Re-run the public verify request\'s quality and review chain while the\n    // original task operation lock is still held.')
source = replace_once(source,
    '        if (repairing) requireGate(attempt.rework?.state === "delivered", "conflict_delivery_unconfirmed", attempt.rework);',
    '        if (repairing) requireGate(attempt.rework?.state === "delivered", "conflict_delivery_unconfirmed", attempt.rework);\n        const reworkSubmission = repairing || Boolean(task.repair && !task.repair.stopped &&\n          task.repair.candidate_commit === task.candidate_commit && attempt.rework?.state === "submitted");')
source = replace_once(source,
    '        let submissionBase = repairing ? attempt.rework!.base_commit : this.candidateBase(attempt, commit);',
    '        let submissionBase = reworkSubmission ? attempt.rework!.base_commit : this.candidateBase(attempt, commit);\n        if (reworkSubmission) requireGate(await this.ancestor(taskId, task.repo, submissionBase, commit),\n          "rework_baseline_changed", { base: submissionBase, commit });')
source = replace_once(source,
    '        if (repairing) {\n          attempt.rework!.state = "submitted";',
    '        if (reworkSubmission) {\n          attempt.rework!.state = "submitted";')
outputs[path] = source

for path, content in outputs.items():
    assert not re.search(r'^(<<<<<<<|=======|>>>>>>>)', content, re.M), path
for path, content in outputs.items():
    (ROOT / path).write_text(content)
    saved = HERE / 'resolved-final' / path
    saved.parent.mkdir(parents=True, exist_ok=True)
    saved.write_text(content)
print(json.dumps({'status': 'resolved_working_files_only', 'paths': list(outputs)}, indent=2))
