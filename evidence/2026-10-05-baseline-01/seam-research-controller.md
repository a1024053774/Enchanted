# Controller research: upstream seam — baseline-2026-10-05-01

Status: INCOMPLETE

This is a controller-side read-only research record. The worker's first report was absent
and its follow-up was reclaimed after a bounded timeout; those facts remain in the monitor
report and are not replaced by this record.

## Source and versions

- Temporary read-only clone: `/tmp/herdr-upstream.pniXIr`
- Upstream HEAD: `c4653a4f10502601ac110b12b2c45a5f7134082b`
- Local Herdr client/server: `0.9.3` / `0.9.1`, protocol 22, endpoint compatible, server binary stale
- Local Codex: `codex-cli 0.160.0`
- Upstream toolchain: Rust `1.96.1`; the repository documents `just test` and `just check`
- Local environment: `just` is not installed; the `a2a` directory is not a Git worktree

## Verified entry points

The upstream source exposes the following real agent surfaces:

- CLI dispatch in `src/cli/agent.rs`: `agent start`, `list`, `get`, `read`, `prompt`, `wait`,
  `send-keys`, and `explain`.
- API schema in `src/api/schema.rs`: `AgentStart`, `AgentList`, `AgentRead`, `AgentPrompt`,
  and `AgentWait` methods.
- Lifecycle implementation in `src/api/wait.rs`: `wait_for_agent` and `prompt_agent` track
  lifecycle/status events and prompt-stall behavior; they do not represent a business task's
  acceptance result.
- The upstream skill explicitly says `idle` and `done` mean ready for input and that `--wait`
  observes lifecycle state rather than an individual business turn.
- The upstream README and skill document `just test`/`just check` and the use of agent/pane
  surfaces for real entry-point checks.

## What remains unresolved

- This `a2a` project contains no product source, Git history, or representative coding task;
  it is currently a governance and evidence repository.
- No independent acceptance command/oracle for the intended first task exists yet.
- No persistent Herdr fork/checkout location has been chosen for implementation.
- `just` and the upstream test prerequisites are not available in the current shell.
- A worker follow-up inspected upstream files but did not save its required report before being
  reclaimed; no worker result is treated as an acceptance oracle.

## Consequence

The verified Herdr CLI/API lifecycle surface is sufficient to design an adapter probe, but not
to close T-005 or create a product implementation ticket. The next research/design step must
choose a persistent target checkout, a representative task fixture, and an independent oracle;
until then the correct status remains `INCOMPLETE`.

## Commands and evidence

- `git clone --depth 1 https://github.com/herdrdev/herdr.git /tmp/herdr-upstream.pniXIr`
- `git -C /tmp/herdr-upstream.pniXIr rev-parse HEAD`
- `rg -n 'AgentPrompt|AgentWait|AgentRead|wait_for_agent|prompt_agent' /tmp/herdr-upstream.pniXIr/src`
- `herdr status`, `herdr agent list`, `herdr agent get`, `herdr agent read`
- Prior lifecycle and timeout observations: `monitor.md`
