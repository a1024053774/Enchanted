---
session_id: grilling-herdr-a2a-intent-20261005
status: confirmed
topic: herdr-a2a
destination_artifact: intent.md
created_at: 2026-10-05T00:00:00-04:00
updated_at: 2026-10-05T00:00:00-04:00
last_round: 6
---

## Destination

The destination is an accepted `intent.md` at the Plan / intent stage. The existing
research-and-plan document remains the project's initial research input and is not rewritten
as part of this grilling.

> User request: “先看本地的初步调研文档，然后围绕我的核心诉求，grilling me”
>
> Destination decision: “接受一份 intent，现有讨论稿不用改造了，当项目的初始”
>
> Goal confirmation: “是” — referring to “让协作不依赖模型持续记住操作手册”；the user
> added: “你前面说的那句才是关键部分”。

## Out of scope

- Implementation, repository creation, tests, release, deployment, and production changes | reason: grilling decides and hands off; it does not build.
- Treating the existing discussion draft as an accepted requirements artifact | reason: the draft says the project is still in requirements discussion and architecture design.
- Rewriting the existing discussion draft | reason: the user explicitly wants it retained as the project's initial input.

## Confirmed constraints

- C1 | state: confirmed | source: local research document | The project must not assume that terminal `idle`/`done` equals business-task success.
- C2 | state: confirmed | source: local research document | The document's current proposal is not an implementation authorization.
- C3 | state: confirmed | source: round 1, user | The canonical destination is a new `intent.md`; the existing discussion draft remains initial project material and is not rewritten.
- C4 | state: confirmed | source: round 1, user | The core goal is to make collaboration not depend on the model continuously remembering the operating manual; this is the key priority.
- C5 | state: confirmed | source: round 3, user accepting recommendation | If a model forgets the skill or skips a step, the system must reject invalid state, leave diagnostic evidence, and pause recoverably rather than guess success.
- C6 | state: confirmed | source: round 3, user | The first experiment uses Codex in a Herdr-based second-development workflow; other CLIs are not required for this first execution.
- C7 | state: confirmed | source: round 3, user | Modifying the Herdr core remains allowed if scale or a reproduced capability gap requires it; the boundary is evidence-driven and not fixed in this intent.
- C8 | state: confirmed | source: round 4, user | The controller is this primary agent on `gpt-6-astra` with max reasoning; workers use `gpt-6.1-sol` with xhigh reasoning and the requested Fast service tier.
- C9 | state: confirmed | source: round 5, user | The project uses the `project-map` workflow as its governance map; relevant local skills must be consulted and their boundaries recorded in project documents.
- C10 | state: confirmed | source: round 5, user | Within the approved scope, the controller may assign and reclaim worker tasks through Herdr without asking for each routine operation; it must stop for major decisions or direction changes and must not cross the agreed gates.
- C11 | state: confirmed | source: round 6, user | The controller stops for scope or goal changes, acceptance or permission changes, irreversible external effects, unverified or conflicting external state, destination-changing design trade-offs, or budget/risk breaches; routine dispatch, status checking, policy-bounded retry, and reclaim remain autonomous.

## Decisions so far

- D1 | state: confirmed | type: decide | origin: user | source: round 1 | Produce an accepted `intent.md` as the canonical Plan / intent artifact. | detail: intent.md
- D2 | state: confirmed | type: decide | origin: user | source: round 1 | Treat reduced dependence on remembered collaboration procedure as the core goal. | detail: intent.md#用户目标
- D3 | state: confirmed | type: decide | origin: recommended | source: round 2 | The core goal is the first priority; multi-CLI support is a boundary serving that goal, not the first success criterion. | basis: C4 | assumes: the first experiment may use one CLI while preserving a capability contract for later adapters.
- D4 | state: confirmed | type: decide | origin: user | source: round 2 | Define a capability contract before selecting a broader CLI set; use Codex as the first experimental CLI. | detail: intent.md#首轮范围
- D5 | state: confirmed | type: decide | origin: recommended | source: round 2 | The first affected users are the user's current Herdr-based multi-agent coding workflow. | basis: C4 | assumes: the intent will name at least one representative coordination failure from that workflow.
- D6 | state: confirmed | type: decide | origin: recommended | source: round 3 | The minimum safe behavior is rejection plus diagnostic, recoverable pause when claim/submit/integration state is invalid. | basis: C4 | assumes: safe refusal is preferable to automatic completion when the external state is unknown.
- D7 | state: confirmed | type: decide | origin: user | source: round 3 | Use Codex as the first test CLI while developing against Herdr; do not require a second CLI in this first experiment. | detail: intent.md#首轮范围
- D8 | state: confirmed | type: decide | origin: user | source: round 3 | Decide whether to patch Herdr core only after scale or a reproduced public-interface gap demonstrates the need. | detail: intent.md#首轮范围
- D9 | state: confirmed | type: compare | origin: recommended | source: round 4 | The first Codex experiment targets stale or unverified results being accepted. | basis: C4 | assumes: the first acceptance boundary is result validity, while other coordination failures remain secondary observations.
- D10 | state: confirmed | type: compare | origin: recommended | source: round 4 | The monitoring agent is read-only: it records events and flags anomalies but cannot claim, submit, integrate, or mark success. | basis: C5 | assumes: observation must not contaminate the behavior being measured.
- D11 | state: confirmed | type: decide | origin: recommended | source: round 4 | Experience collection produces an append-only run record plus an independent acceptance result, including versions, task/attempt/message/integration events, interventions, and failures. | basis: C4 | assumes: narrative summaries alone are insufficient evidence.
- D12 | state: confirmed | type: decide | origin: recommended | source: round 4 | The controller assigns and explains work, workers implement, and claim/submit/acceptance gates remain outside model self-report. | basis: C5 | assumes: the controller cannot bypass the same gates it is meant to evaluate.
- D13 | state: confirmed | type: decide | origin: recommended | source: round 5 | Use `gpt-6.1-sol` with high reasoning for the read-only monitoring agent. | basis: D10 | assumes: structured trace analysis does not require the controller's max configuration.
- D14 | state: confirmed | type: compare | origin: recommended | source: round 5 | The first run is an exploratory baseline and failure-evidence exercise; it cannot claim improved reliability without an independent comparison. | basis: D11 | assumes: experience collection and efficacy proof are separate stages.
- D15 | state: confirmed | type: decide | origin: user | source: round 5 | The controller autonomously dispatches and reclaims workers through Herdr inside the approved scope, pauses for major decisions or direction changes, and never bypasses gates. | detail: intent.md#角色、模型与权限
- D16 | state: confirmed | type: decide | origin: recommended | source: round 6 | Apply the concrete major-decision stop boundary in C11. | basis: C10 | assumes: the boundary is explicit enough for routine controller decisions and user escalation.

## Facts

- F1 | state: observed | source: `herdr-a2a-research-and-plan-2026-10-06.md`, local read on 2026-10-05 | It is a discussion draft and records the core direction as moving critical collaboration behavior from model memory into a persistent, validated, recoverable program layer.
- F2 | state: observed | source: workspace sweep on 2026-10-05 | No `AGENTS.md`, `CLAUDE.md`, `CONTEXT.md`, `.project-map/`, `.grilling/`, `intent.md`, `spec.md`, or `plan.md` existed before this session.
- F3 | state: observed | source: `herdr-a2a-research-and-plan-2026-10-06.md` | The draft recommends a small deterministic loop and explicitly defers repository creation until the plan is discussed.
- F4 | state: observed | source: `/Users/luckye/Documents/SKILLS/grilling-skill`, git HEAD `f1e01bb`, inspected 2026-10-05 | The current shared grilling skill includes canonical-artifact, user-quote, accepted-recommendation, and project-map handoff rules; the Claude job's `before` snapshot is older.

## Frontier

- None.

## Blocked

- None.

## Not yet specified

- The exact first representative task, Herdr entry point, and independent acceptance seam belong to the next Design / Spec session; they are named handoff risks, not unresolved intent decisions.
- The second CLI validation gate belongs after the Codex experiment; no second CLI is required for this intent.
- The formal budget number is not set; any budget or risk breach triggers C11 escalation.

## Risks and conflicts

- R8 | state: resolved | owner: user | affects: D16 | The user accepted the concrete stop boundary in C11.
- R9 | state: named-risk | owner: next Design / Spec session | affects: handoff | The first representative task, Herdr entry point, and independent acceptance seam remain unknown and must be resolved before implementation.

## Handoff

Confirmed. The accepted intent, project map, glossary, and AGENTS rules are the handoff. Start a separate project-map Design / Spec session, then slice the first tracer-bullet build tickets. The current user message authorizes execution after this decision session; this grilling session itself does not record worker implementation progress.

## Changelog

- Round 0: Workspace and discussion draft read. The pre-skill question was not counted as a round.
- Round 1: User accepted `intent.md` as the destination, kept the existing draft as initial material, confirmed the core goal, and raised the priority distinction between multi-CLI support and the core goal.
- Round 2: User accepted the recommendation that the core goal comes first, chose a capability contract with Codex as the first CLI experiment, and accepted the current Herdr multi-agent coding workflow as the first affected scenario.
- Round 3: User accepted the safe-rejection recommendation, clarified that the first experiment is Codex on a Herdr second-development path, and deferred the Herdr core/adapter boundary to evidence about scale or a reproduced gap. User proposed a controller plus worker plus monitoring-agent pilot for experience collection.
- Round 4: User accepted the first-failure, read-only monitor, append-only evidence, and controller/worker boundary recommendations. The user set Astra Max for the controller and 6.1 xhigh Fast for workers; the prior controller suggestion is superseded. Monitor model, claim level, and human approval boundary remain open.
- Round 5: User accepted the recommended monitoring model and exploratory evidence level. The user set the autonomy rule: the controller dispatches and reclaims workers through Herdr within scope, and stops for major decisions or direction changes. The local `project-map` skill family was inspected; Q16 remains to make the stop boundary concrete.
- Round 6: User accepted the recommended stop boundary, requested the current shared grilling skill be compared with the Claude snapshot, and authorized the project-map/intent/AGENTS documentation handoff before a separate execution session.
- Handoff: `intent.md`, `CONTEXT.md`, `AGENTS.md`, and `.project-map/` contain the confirmed baseline; T-004 is closed; the ledger is confirmed.
