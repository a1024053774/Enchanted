# Project map

## Destination

`intent.md` is accepted for the Herdr-based multi-agent coding project. The current
destination is the first usable Spec and seam research before any implementation ticket. The
existing `herdr-a2a-research-and-plan-2026-10-06.md` remains the dated initial research record
and is not rewritten by this effort. The design record is [specs/herdr-a2a.md](specs/herdr-a2a.md).

## Notes

- Core goal: collaboration must not depend on the model continuously remembering the operating manual.
- First experiment: Codex workers in the current Herdr workflow; multi-CLI support is a later capability-contract validation, not the first success claim.
- Control rule: the Astra Max controller may dispatch and reclaim workers through Herdr within approved scope; it must pause for major decisions or direction changes and never bypass claim, submit, acceptance, or integration gates.
- Required skills by stage: `project-map` (map/status), `reality-first-engineering` (before architecture or broad implementation), `evidence-first-testing` (behavior changes and failure evidence), `design-integrity-review` (structural-risk completion), `behavioral-acceptance-review` (acceptance/eval surfaces), and `document-writing` (project documents). Use `grilling` for decision sessions.

## Decisions so far

- [T-001 Goal and destination](tickets/T-001-goal-and-destination.md): accepted `intent.md`; the research draft remains initial input; reducing reliance on remembered collaboration procedure is the core goal
- [T-002 First experiment contract](tickets/T-002-first-experiment-contract.md): Codex/Herdr experiment targets stale or unverified result acceptance and must reject invalid state with evidence
- [T-003 Roles and evidence](tickets/T-003-roles-and-evidence.md): Astra Max controller, 6.1 xhigh Fast workers, high-reasoning read-only monitor, append-only run evidence, and exploratory claims only
- [T-004 Major-decision stop boundary](tickets/T-004-major-decision-stop-boundary.md): explicit escalation triggers; routine dispatch, status checking, policy-bounded retry, and reclaim remain autonomous

## Not yet specified

- First representative task and Herdr entry point for the Codex experiment
- The acceptance suite and independent test seam for the first run
- When and how a second CLI validates the capability contract
- Numeric budget and risk thresholds
- [T-005 First seam and baseline](tickets/T-005-first-seam-and-baseline.md) is the next research ticket before any implementation ticket

## Out of scope

- Implementation, release, and deployment | reason: they belong to later Design, Slice, Work, and release sessions after this accepted intent.
- Rewriting the dated research draft | reason: it is the project's initial research record.

## Living docs

| Doc | Covers | Verified |
| --- | --- | --- |
| [CONTEXT.md](../CONTEXT.md) | `intent.md` | |
| [AGENTS.md](../AGENTS.md) | `.project-map/MAP.md`, `CONTEXT.md` | |
