# T-076 boundary migration record

## Scope

T-082 changes the reviewer contract from a read-only审查 worktree to a writable, disposable candidate copy. The D3-only assertion patch is now applied to the T-082 candidate worktree; the patch is preserved in `t076-assertion-changes.patch` as a separately reviewable change.

## Temporary assertion edits and reason

1. `test_quality_tracer_e2e.py` changed the reviewer argv expectation from `read-only` to `workspace-write`, added the network/tmp exclusion flags, and checked that `-C` and the recorded worktree point to `candidate_workspace`. These assertions correspond directly to T-082 Acceptance 2 and the new candidate-copy boundary.
2. `run_t076_quality_green.py` changed only its reviewer launch mutant target and expected failure id so its counterfactual matches the T-082 boundary. It did not alter the source audit or acceptance oracle.
3. `run_t076_launch_policy.py` changed only the same reviewer launch mutant and its baseline failure id. It did not weaken the historical evidence or source checks.

The patch changes only those three D3 assertion/mutation descriptions. The T-076 audit mechanism code is unchanged. The new boundary assertions also live in `test_t082_review_boundary_e2e.py` and cover the candidate-copy request, launch policy, and cleanup.

## T-076 source audit

`run_t076_quality_green.py` does not compare a file hash list. It requires a clean working-tree diff for `workbench/src`, `workbench/hooks`, `workbench/tests`, and `workbench/README.md`, and separately requires the original acceptance files to have no diff from commit `a7f4cc3033c16d5888de50d8352da516c941f8e9`. Therefore the candidate must be frozen in a commit (or an equivalent clean candidate checkout) before that runner can accept the new assertion baseline. No audit logic or baseline hash list has been changed in T-082.

## Evidence slots

- Parent assertion counterfactual: the patch file records the old assertion text and expected D3 failure IDs.
- Candidate revision / new assertions: run `OUTSIDE-COMMANDS-06.sh`; it first runs the unchanged controlled fixtures, then records the candidate runner's source-audit gate and the D3 red/green inputs without changing the audit implementation.
