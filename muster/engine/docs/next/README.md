# muster


<p align="center">
  <img src="assets/logo.png" alt="muster" width="100" />
</p>

<p align="center">
  <a href="https://muster.dev">muster.dev</a> · <a href="#install">install</a> · <a href="https://muster.dev/docs/quick-start/">quick start</a> · <a href="https://muster.dev/docs/">docs</a>
</p>

<p align="center">
  English · <a href="README.zh-CN.md">简体中文</a>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-666666?labelColor=333333" alt="Apache 2.0 license" /></a>
  <a href="https://github.com/musterdev/muster/releases"><img src="https://img.shields.io/github/downloads/musterdev/muster/total?labelColor=333333&color=666666" alt="total GitHub release downloads" /></a>
  <a href="https://github.com/musterdev/muster/stargazers"><img src="https://img.shields.io/github/stars/musterdev/muster?labelColor=333333&color=666666&logo=github" alt="GitHub stars" /></a>
  <a href="https://github.com/musterdev/muster/releases/latest"><img src="https://img.shields.io/github/v/release/musterdev/muster?label=release&labelColor=333333&color=666666" alt="latest stable release" /></a>
  <a href="https://formulae.brew.sh/formula/muster"><img src="https://img.shields.io/homebrew/v/muster?label=homebrew&labelColor=333333&color=666666" alt="Homebrew version" /></a>
  <a href="https://x.com/musterdev"><img src="https://img.shields.io/badge/follow-%40musterdev-000000?logo=x&logoColor=white" alt="follow @musterdev on X" /></a>
</p>

---

https://github.com/user-attachments/assets/043ec09f-4bdd-41d5-aee0-8fda6b83e267

**the runtime your coding agents live on.**

- **detach without stopping work** — muster keeps terminals running in a background server when you close the client or lose your SSH connection. after a server or machine restart, muster restores the saved layout and can resume supported agent sessions; the original processes do not survive. [session state →](https://muster.dev/docs/session-state/)
- **several machines, one window** — keep local work and saved ssh machines together, with a combined agent list and independent reconnects. [remote machines →](https://muster.dev/docs/connecting-machines/)
- **never hunt for the stuck one** — every pane is marked working, blocked, or idle. when an agent stops and needs an answer, muster says so.
- **agent-native** — agents drive muster through the cli and socket api: they can spawn panes, prompt each other, and wait until another agent is genuinely blocked. [agent skill →](https://muster.dev/docs/agent-skill/)
- **runs what you already run** — claude code, codex, cursor, opencode, grok and the rest. muster doesn't wrap or replace them; it owns their terminals. building an agent? [add muster support →](https://muster.dev/docs/add-muster-support/)
- **keyboard and mouse, both first-class** — tmux-style prefix keys *and* click, drag, split. pick per moment, not per tool.
- **plugins** — extend panes and workflows. [browse the marketplace →](https://muster.dev/plugins/)
- **one rust binary, no electron** — runs in whatever terminal you already use.

---

## install

```bash
curl -fsSL https://muster.dev/install.sh | sh
```

or `brew install muster` · `mise use -g muster` · windows: `powershell -ExecutionPolicy Bypass -c "irm https://muster.dev/install.ps1 | iex"` · [endpoint-protected Windows](https://muster.dev/docs/windows-beta/) · [binaries](https://github.com/musterdev/muster/releases)

then start it where the work lives:

```bash
muster
```

run your agents, split panes, walk away. `ctrl+b q` detaches, `muster` reattaches. [quick start →](https://muster.dev/docs/quick-start/)

## docs

everything lives at [muster.dev/docs](https://muster.dev/docs/): [quick start](https://muster.dev/docs/quick-start/) · [concepts](https://muster.dev/docs/concepts/) · [supported agents](https://muster.dev/docs/agents/) · [keyboard](https://muster.dev/docs/keyboard/) · [configuration](https://muster.dev/docs/configuration/) · [session state](https://muster.dev/docs/session-state/) · [connecting machines](https://muster.dev/docs/connecting-machines/) · [remote](https://muster.dev/docs/persistence-remote/) · [integrations](https://muster.dev/docs/integrations/) · [add muster support to your agent](https://muster.dev/docs/add-muster-support/) · [plugins](https://muster.dev/docs/plugins/) · [socket api](https://muster.dev/docs/socket-api/)

## thanks

every past sponsor and backer is listed in [SPONSORS.md](./SPONSORS.md) — thank you 🐑

enterprise / partnership: hey@muster.dev

## agent instructions

if you are an ai agent helping with this repository, read [`AGENTS.md`](./AGENTS.md) before making changes and read [`CONTRIBUTING.md`](./CONTRIBUTING.md) before opening issues or PRs.

## development

```bash
git clone https://github.com/musterdev/muster
cd muster
cargo build --release

just test        # unit tests
just check       # formatting, tests, and maintenance checks
```

## license

Muster is licensed under the [Apache License 2.0](LICENSE).
