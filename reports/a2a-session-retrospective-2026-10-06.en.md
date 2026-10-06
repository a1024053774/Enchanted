# Review of a2a development sessions

Date: 2026-10-06. Project revision: `7069dc271541fb801616d17e11815cffc287d83e`.
Exclusive record cutoff: `2026-10-06T11:14:05.292Z`.

[Chinese report](a2a-session-retrospective-2026-10-06.zh-CN.md) · [Framework report](herdr-a2a-2026-10-06.en.md) · [Evidence index](../evidence/2026-10-06-session-review-01/README.md) · [T-009](../.project-map/tickets/T-009-session-retrospective.md)

This English report follows STE structural rules. It does not claim a dictionary compliance check or ASD certification.

## Result

The record scan and review deliverable are **PASS**. Implementation of the process lessons remains **INCOMPLETE**.

The scan covered 20 a2a sessions and approximately 39.4 MB of original records.
It produced 1,355 pointers to messages and tool records.
Detailed review then examined anomalies, deliveries, and subsequent changes.
The review used actual messages, tool calls, artifacts, and Git history.
It did not start new model experiments.

The main weaknesses concern controller stopping criteria, fixture instructions, descendant agent records, and monitoring coverage.
These weaknesses can require repeated checks and manual coordination even when product tests pass.
The records do not measure the amount of that overhead.

Session history supplied facts that the monitor snapshots omitted.
It does not establish continuous independent monitoring or a complete audit of operating system writes.

## Scope and evidence

Selection used the a2a working directory, its subdirectories, and explicit child-session relationships.
The metadata query and rollout header checks both matched 20 sessions in 20 files.
The cutoff excludes this retrospective.

| Role | Count | Labels |
| --- | --- | --- |
| Controller | 1 | S01 |
| Initial research worker | 1 | S02 |
| Independent monitors | 3 | S03, S06, S12 |
| Implementation and acceptance authors | 6 | S04, S05, S10, S11, S14, S15 |
| Reviewers that the controller started | 3 | S09, S13, S20 |
| Workers for real pagination tasks | 3 | S07, S16, S18 |
| Review agents that those workers created | 3 | S08, S17, S19 |

The [index](../evidence/2026-10-06-session-review-01/README.md) links each label to its original file.
The [selected evidence](../evidence/2026-10-06-session-review-01/excerpts.json) supplies timestamps, line numbers, and excerpts E01–E21.
The structured index does not export internal reasoning, system instructions, or complete message bodies.

Some internal dispatch messages contain encrypted fields. This review did not decrypt them.
Child-session findings use visible call parameters, parent relationships, local configurations, and visible results.
Local model settings do not prove provider fulfillment.

Each finding separates observations, interpretation, completed actions, and remaining work.
An error phrase can occur in quoted text or source code.
Keyword matches therefore do not count as independent failures.

## F01: The controller stopped with work remaining

The user explicitly authorized work after the planning documents without another confirmation request, as E01 records.
The controller later stopped because the new project lacked product code, Git history, and an oracle, as E06 records.
The T-005 resolution subsequently identified missing product code as a normal starting condition.
The controller could prepare the fixture and independent oracle within the existing authorization.

The controller also ended its T-006 response with T-007 still pending, as E07 records.
The user then requested continued execution, as E08 records.
T-007 and T-008 followed.

The controller treated ordinary preparation or one ticket's completion as a reason to stop the larger assignment.
The messages establish repeated user intervention.
They do not establish that every hour between messages was development delay.

Current AGENTS rules distinguish worker scope from controller coordination.
A mechanical handoff check still needs to record remaining authorized work, the exact stop reason, and the next owner.
Follow-up: [T-012](../.project-map/tickets/T-012-controller-handoff.md).

## F02: Research lacked intermediate deliverables

Shortly after the research worker started, the controller described its research round as complete because Herdr reported `done`.
The report file did not exist. E02 preserves that statement.
The controller later interrupted the worker after a bounded wait, as E03 records.

During the second attempt, the controller acknowledged useful source inspection at 18:15:21 UTC.
At 18:18:55, it decided to interrupt because the report still did not exist.
The controller then repeated inspection and wrote its own report.
E04 and E05 preserve those observations.

These records do not prove that the worker stopped making progress.
They also do not prove that further waiting would produce a report.
The assignment specified a final report without a dependable intermediate artifact.
The controller therefore relied on terminal state and elapsed waiting.

Some early reclamation statements referred to Ctrl+C interruption. Pane closure happened later.
The two actions need different completion conditions.
Later workers supplied frozen artifacts, and the product separated submission from pane reclamation.
Research tasks still need intermediate evidence, blocker reports, and handoff conditions.
Follow-up: [T-012](../.project-map/tickets/T-012-controller-handoff.md).

## F03: Fixture workers applied governance checks to the wrong scope

All three real pagination workers read the parent project's rules.
They then ran project-map status in their isolated worktrees.
Each received a missing `.project-map/MAP.md` result.
E09, E10, and E11 preserve instances from S07, S16, and S18.
Later calls repeated the same check.

Those worktrees intentionally contained the pagination starter and CONTRACT.
They did not contain copies of the a2a project map.
The workers correctly avoided creating another project map.

The task prompt supplied the workspace, base, identity, and submission command.
It did not clearly connect the task repository, governance root, applicable rules, and acceptance entry point.
This ambiguity produced repeated irrelevant checks and could obscure an actual blocker.

The next contract needs explicit scope.
Copying all project instructions into every fixture would not settle applicability.
Follow-up: [T-013](../.project-map/tickets/T-013-fixture-governance-scope.md).

## F04: Agent records omitted internal descendants

Each real worker called internal `spawn_agent` once.
Those calls did not create new Herdr panes.
E12–E14 and configuration records C-S08, C-S17, and C-S19 establish these relationships.

| Parent | Child | Requested role | Local turn configuration |
| --- | --- | --- | --- |
| S07, live-02 | S08 | `explorer` | `gpt-6.1-sol`, xhigh |
| S16, live-auto-01 | S17 | `acceptance-auditor` | `gpt-5.6-luna`, max |
| S18, live-auto-02 | S19 | `acceptance-auditor` | `gpt-5.6-luna`, max |

The parent messages described local behavior reviews.
The dispatch arguments selected roles without explicit model overrides.
The luna settings appear in the child sessions' `turn_context` records.
They are not guesses from writing style or parent pane titles.
The evidence does not establish an intentional choice of a cheaper model by the worker.
The parent's Fast display also does not establish Fast service for a child session.

Run manifests mainly described agents that the controller created through Herdr.
They did not fully account for these descendants.
A pane inventory alone therefore could not answer which agents participated or how model constraints applied.
The records also lacked an explicit exception for review-role defaults.

All three child reviews produced completion results.
This review found no evidence that they caused invalid integration or persistent resource leakage.
The finding concerns incomplete configuration and resource records, not demonstrated model quality failure.
Follow-up: [T-010](../.project-map/tickets/T-010-descendant-session-accounting.md).

## F05: Monitoring ended without complete action tracking

S06 and S12 completed two samples each and explicitly limited their claims.
E15 and E16 preserve their final statements.
The T-006 prompt promised a second observation task, but that session received no second-stage assignment.
The saved material contains no second-stage report.
The located T-008 sessions contain implementation, acceptance, and review agents, but no independent monitor.

The T-007 monitor also identified stale glossary coverage, outdated manifest status, and inaccurate configuration wording.
Later changes updated the glossary and status.
The configuration wording remained unresolved until the preceding retrospective supplement.

The observers supplied useful checks, but their findings lacked complete owner, action, and recheck records.
Session history now permits retrospective inspection.
It cannot supply an independent observer that did not participate at the time.

The next check needs separate results for observation delivery, finding disposition, and monitoring coverage.
Product acceptance and complete monitoring are different claims.
Follow-up: [T-011](../.project-map/tickets/T-011-monitor-closure.md).

## F06: Evidence collection code failed repeatedly

The baseline monitor used `Path.write_text(..., newline=...)`, which the active Python rejected.
E17 preserves the resulting TypeError.
The first T-007 fault fixture failed to read the expected persisted intent.
It produced five fixture errors, which could not establish product failures.
E18 preserves that error.

T-008 also retained failures from Path serialization and a barrier that blocked controller reclamation.
The authors corrected the file writer, observer, diagnostic representation, and barrier.
The final T-007 parent run had four business failures, five passes, and no fixture errors.
T-008 used the valid repeated mutant result.
The earlier errors did not count as product counterexamples.

The [recovery results](../evidence/2026-10-06-recovery-01/RESULTS.md) and [automatic run results](../evidence/2026-10-06-run-01/RESULTS.md) preserve those distinctions.
However, collection compatibility and diagnostic validity still depended on discovery during execution.
Preflight checks should expose collection defects before expensive model experiments.
A deliberately broken collector must not produce a product PASS verdict.
Follow-up: [T-014](../.project-map/tickets/T-014-evidence-preflight.md).

## F07: Large output and incorrect packaging impeded review

Several source and tool reads produced truncated output.
One tool result reported approximately 115,063 original tokens and truncation, as E20 records.
That figure does not measure billed model tokens.

E19 records Git warnings about embedded repositories.
Some test directories entered a local commit as gitlinks.
Those entries did not preserve a portable copy of the full experiment.

Later work retained the original directories and archived Git objects, SQLite files, and source snapshots.
It also removed the incorrect gitlink entries.
The final records preserve the correction and earlier failures.

Future capture should save complete raw output before producing a bounded summary.
Artifact checks should inspect archive contents and unintended gitlinks before commit.
A committed filename alone does not establish reproducibility.
Follow-up: [T-014](../.project-map/tickets/T-014-evidence-preflight.md).

## Product defects that actual failures exposed

| Case | Evidence | Completed action |
| --- | --- | --- |
| An early `create` implementation mishandled an absent integration reference. | S05:97, E21. Seven tests stopped at creation without executing later assertions. | Later code handled the Git return code and ran the complete CLI scenarios. Seven blocked tests did not represent seven distinct defects. |
| The oracle omitted the upper limit check. | The independent reviewer and T-006 counterexample records. | New 100/101 cases rejected the bad candidate through real `verify`. The integrated artifact also passed twelve checks. |
| A normal helper shell caused an identity rejection. | Actual Herdr process observations from `live-auto-01`. | The program checked the Codex process leader. Positive, negative, and real-entry checks passed afterward. |

These cases demonstrate the value of the **Tracer bullet**.
Real entry points exposed behavior that code structure or substitutes alone did not establish.
Separate implementation and acceptance authors, frozen-candidate reviews, and retained counterexamples also supplied useful evidence.
Those practices should remain.

**Deep modules** should keep necessary coordination behind a small task contract without adding a wrapper for each incident.
**Ubiquitous language** must distinguish turn completion, submission, acceptance, integration, process interruption, and pane reclamation.

## Follow-up and completion criteria

Five task tickets now describe the repeated, checkable gaps.
They record future work, not completed product changes.

| Ticket | Required mechanism or check |
| --- | --- |
| [T-010](../.project-map/tickets/T-010-descendant-session-accounting.md) | Account for parent/child sessions, roles, requested settings, completion, and model exceptions. |
| [T-011](../.project-map/tickets/T-011-monitor-closure.md) | Check monitoring artifacts, finding disposition, and coverage separately. |
| [T-012](../.project-map/tickets/T-012-controller-handoff.md) | Check authorized next work, stopping reasons, and intermediate research artifacts. |
| [T-013](../.project-map/tickets/T-013-fixture-governance-scope.md) | Distinguish the task repository from its governance root and applicable checks. |
| [T-014](../.project-map/tickets/T-014-evidence-preflight.md) | Check collection compatibility, failure classification, raw-output preservation, and artifact packaging. |

The proposed order starts with T-010 and T-013, then monitoring and handoff checks.
T-014 should precede the next real model experiment.
Implementation still needs inspection of existing capabilities.
These proposals do not select a new architecture.

This review did not repeat product acceptance or claim improvements in cost, throughput, or reliability.
Review completion requires traceable instances, separate facts and inferences, explicit status, and preserved original sessions.
The five process mechanisms remain incomplete.
