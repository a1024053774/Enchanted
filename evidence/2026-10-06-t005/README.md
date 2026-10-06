# T-005 evidence (2026-10-06)

New evidence follows the interrupted 2026-10-05 probe; earlier results stay unchanged.
Goal: establish the real Herdr dispatch boundary and a reproducible independent oracle.
No reliability/cost improvement is claimed.

The earlier work was interrupted by the controller after wait timeouts while the worker
was visibly reading files. Timeout was not proof of a hung worker.
The earlier worker argv did not explicitly set Fast. Its actual service tier is unverified.

Persistent source: `.upstream/herdr`, pinned upstream commit
`c4653a4f10502601ac110b12b2c45a5f7134082b`; local copy of prior clean clone.
Project governance starting commit: `9c812f3`. Product source is initially absent by design.

The fixture is cursor pagination through a JSON subprocess API. Literal expected values
in `acceptance/pagination_oracle.py` are derived from `fixtures/pagination/CONTRACT.md`.
It does not import candidate code. Reference and deliberately broken starter are checked
before product implementation. The fixture is an isolated test repository, not another
user project.

Claude Code `~/.claude/skills/grilling` and `~/.agents/skills/grilling` both resolve to
`/Users/luckye/Documents/SKILLS/grilling-skill/grilling`. They use the same shared files.

Fast setting checked with installed CLI and official configuration reference:
https://learn.chatgpt.com/docs/config-file/config-reference
Use explicit `-c 'service_tier="fast"'`. Requested configuration is distinct from
provider-confirmed request fulfillment.

Local runtime: Herdr client 0.9.3 / server 0.9.1, protocol 22 compatible; Codex CLI 0.160.0.
Do not restart the active server. Inherited pane context is stale (w6:pQ); live a2a pane is
wF:p1 with foreground Codex cwd matching this project. Always use live explicit handles.
