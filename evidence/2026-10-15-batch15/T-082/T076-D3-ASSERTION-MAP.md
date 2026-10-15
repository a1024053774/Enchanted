# T-076 / T-082 D3 assertion map

The T-076 files in this worktree are restored to the parent revision. The temporary D3-only patch is `t076-assertion-changes.patch`; OUTSIDE-05 applies it only in a clean temporary candidate.

| Parent assertion | Why it fails on the T-082 candidate | D3 replacement | New assertion |
| --- | --- | --- | --- |
| `TRACER-READONLY-ARGV` in `test_quality_tracer_e2e.py` | It requires reviewer `--sandbox read-only`, while D3 requires `workspace-write` in the disposable candidate copy. | D3 changes reviewer sandbox and adds network/tmp exclusions. | `T082-REVIEW-ARGV` and `T082-COPY-CREATED` in `test_t082_review_boundary_e2e.py`. |
| `TRACER-READONLY-ARGV` mutation in `run_t076_quality_green.py` | The old mutant target encodes the retired read-only branch. | Mutant changes reviewer `sandboxMode` back to `read-only`. | `T082-LAUNCH-REFUSED` through the four launch-policy mutants in `run_t082_boundary.py`. |
| `TRACER-REVIEWER-DEFAULT-ARGV` baseline id in `run_t076_launch_policy.py` | Parent source lacks the D3 candidate-copy policy, so the old reviewer launch assertion fails for the retired boundary. | Baseline expectation is mapped to the candidate-copy launch assertion. | `T082-REVIEW-ARGV`; the T-076 audit remains unchanged. |

The old T-076 source-audit check is not edited. OUTSIDE-05 creates clean temporary Git candidates, runs the unchanged parent assertions first to capture only the listed D3 failures, then applies this patch and reruns the candidate. Any unrelated failure remains a failure.
