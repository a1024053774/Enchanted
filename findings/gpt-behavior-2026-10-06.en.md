# GPT controller behavior record

Date: 2026-10-06. The user classified early turn completion with authorized work remaining as a GPT model issue.

[Chinese](gpt-behavior-2026-10-06.zh-CN.md) · [Findings directory](README.md) · [Original excerpts](../evidence/2026-10-06-session-review-01/excerpts.json)

This file records the behavior of the GPT controller in this development run.
F01 no longer belongs to the coordination summary or its corrective scope.
The original session facts remain available.
The classification does not establish a change in model behavior.

## F01: Early turn completion with authorized work remaining

The user authorized implementation after the planning documents without another confirmation request.
S01:550 and E01 preserve that instruction.
The controller still stopped in two cases that required further user intervention.

| Case | Source | Recorded behavior |
| --- | --- | --- |
| Initial research | S01:1158, E06 | The controller treated missing product code, Git history, and an oracle as reasons to stop. Later T-005 work prepared these within existing authorization. |
| After T-006 | S01:1710 and 1717, E07–E08 | The final response left T-007 pending. The user requested continued execution before T-007 and T-008 proceeded. |

Responsibility belongs to GPT controller persistence and instruction following.
F01 is not a Herdr, task-dispatch, or multi-agent coordination defect.
It does not create a coordination task to correct the model's early turn completion.

The records establish renewed user intervention.
They do not establish that every hour between the messages was development delay.
This record describes the actions of the GPT controller in this run.

## Related behavior: status interpretation and interruption

- S01:766, E02: the controller described the research round as complete based on Herdr `done`.
  The report file did not exist.
- S01:859, E03: the controller interrupted the research worker after the bounded wait.
  An expired wait alone does not prove a stalled worker.
- S01:987 and 1054, E04–E05: the controller recorded useful source inspection, then interrupted because the report remained absent.
  The controller subsequently wrote its own research record.

These judgments remain controller behavior observations.
They do not automatically establish a Herdr failure.
The separate coordination gap concerns intermediate research artifacts and task transfer conditions.
F02 in the coordination review retains that scope.

## Boundary with project tasks

[T-012](../.project-map/tickets/T-012-research-handoff.md) now covers intermediate research deliverables and evidence for task transfer or reclamation.
It does not decide when the controller ends its response to the user.
It does not carry an objective to correct F01.

The controller still must honor existing authorization and major-decision boundaries.
This classification does not change those obligations or transfer model responsibility to a new coordination mechanism.
