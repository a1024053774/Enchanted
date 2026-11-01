# T-216 第七轮复跑命令（主控，2026-11-01）

从 ROUND6-COMMANDS.md 的 verified 复跑取出，只把 `round6-verified` 改为 `round7-verified`；工作目录是 `a2a-worktrees/T-216`。

## round7-verified-history-claude

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case history --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-history-claude.json
```

## round7-verified-history-codex

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli codex --case history --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-history-codex.json
```

## round7-verified-completion-claude

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case completion --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-completion-claude.json
```

## round7-verified-completion-codex

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli codex --case completion --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-completion-codex.json
```

## round7-verified-provenance-claude

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case provenance --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-provenance-claude.json
```

## round7-verified-provenance-codex

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli codex --case provenance --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-provenance-codex.json
```

## round7-verified-mutant-attach-claude

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case history --mutant attach-only --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-mutant-attach-claude.json
```

## round7-verified-mutant-attach-codex

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli codex --case history --mutant attach-only --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-mutant-attach-codex.json
```

## round7-verified-t216

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-t216.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-t216.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-t216.json
```

## round7-verified-t133-codex

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-t133-codex.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-t133-codex.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t133_codex_terminal_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-t133-codex.json
```

## round7-verified-t133-mutant

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-t133-mutant.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-t133-mutant.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t133_codex_terminal_controller_e2e.py --mutant reply-as-message --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-t133-mutant.json
```

## round7-verified-r2-online

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-r2-online.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-r2-online.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-r2-online.json
```

## round7-verified-r2-duplicate

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-r2-duplicate.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-r2-duplicate.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --duplicate-submit --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-r2-duplicate.json
```

## round7-verified-codex-local

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli codex --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-codex-local.json
```

## round7-verified-t212

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --mismatched-screen --output /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-t212
```

## round7-verified-recover

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case recover-unknown --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-recover.json
```

## round7-verified-recover-restart

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case recover-restart --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-recover-restart.json
```

## round7-verified-unknown

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case unknown --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-verified-unknown.json
```
