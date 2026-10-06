# Run manifest: baseline-2026-10-05-01

Status: INCOMPLETE — lifecycle surfaces are known, but the representative task and independent acceptance seam are not.

## Purpose

Collect the first read-only baseline for T-005 (`First seam and baseline`) without claiming
reliability improvement. The worker must identify the real Herdr/Codex entry point, a
representative task, and an independent acceptance seam.

## Initial environment

- Project root: `/Users/luckye/Documents/Code/a2a`
- Herdr client: `0.9.3` stable
- Herdr server: `0.9.1`, protocol 22, endpoint compatible
- Workspace: `wF` (`a2a`), controller pane: `wF:p1`
- Controller: `gpt-6-astra`, max reasoning
- Worker target: `gpt-6.1-sol`, xhigh reasoning, Fast service tier
- Monitor target: `gpt-6.1-sol`, high reasoning, read-only
- Intent: `intent.md`
- Spec: `.project-map/specs/herdr-a2a.md`
- Upstream source probe: `/tmp/herdr-upstream.pniXIr` at `c4653a4f10502601ac110b12b2c45a5f7134082b`

## Evidence contract

- Append events and observations; preserve failed or anomalous evidence.
- Do not treat terminal `idle`/`done` or model self-report as business acceptance.
- Do not claim PASS until an independent acceptance command/oracle and its result exist.
- If the worker finds an unknown external state, record `INCOMPLETE` and stop that branch.

## Reports

- `monitor.md`: read-only run timeline and anomalies; verdict `INCOMPLETE`.
- `seam-research-controller.md`: verified upstream CLI/API surfaces and remaining blockers.
- The worker's missing first report and follow-up timeout are preserved as anomalies; no
  worker self-report is an acceptance oracle.
