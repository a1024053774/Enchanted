# 第六轮重跑命令

工作目录： `/Users/luckye/Documents/Code/a2a-worktrees/T-216`

已有证据不覆盖，重跑须更换 summary/log 及矩阵前缀。

源码版本：基线为 `9c0e26212`；历史、补全及未知堵队原红态为 `round5-candidate.patch`；纯意图红态为 `round6-candidate-review1.patch`；迟到钩子红态为当前候选。原红态命令必须配合当时源码；当前 attach-only、skip-unknown-wait 变异可独立复现相应错误。

## 完整矩阵

```sh
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6_verified_matrix.py > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-matrix.log 2>&1
```

```sh
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6_resume_matrix.py > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-resume-matrix.log 2>&1
```

补跑驱动只执行未运行项，保留供应商 Codex 的原失败。

## round6-base-completion-claude-01

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case completion --revision 9c0e26212 --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-base-completion-claude-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-base-completion-claude-01.log 2>&1
```

## round6-base-completion-codex-01

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli codex --case completion --revision 9c0e26212 --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-base-completion-codex-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-base-completion-codex-01.log 2>&1
```

## round6-base-history-claude-01

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case history --revision 9c0e26212 --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-base-history-claude-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-base-history-claude-01.log 2>&1
```

## round6-base-history-codex-01

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli codex --case history --revision 9c0e26212 --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-base-history-codex-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-base-history-codex-01.log 2>&1
```

## round6-final-identity

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case identity --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-identity.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-identity.log 2>&1
```

## round6-final-r2-duplicate

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --duplicate-submit --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-r2-duplicate.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-r2-duplicate.log 2>&1
```

## round6-final-r2-offline

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_round2_e2e.py --case routing-offline --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-r2-offline.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-r2-offline.log 2>&1
```

## round6-final-r2-online

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-r2-online.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-r2-online.log 2>&1
```

## round6-final-r2-processor

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_round2_e2e.py --case processor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-r2-processor.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-r2-processor.log 2>&1
```

## round6-final-race

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case race --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-race.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-race.log 2>&1
```

## round6-final-restart-queue

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case restart-queue --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-restart-queue.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-restart-queue.log 2>&1
```

## round6-final-restart-unknown

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case restart-unknown --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-restart-unknown.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-restart-unknown.log 2>&1
```

## round6-final-restart

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case restart-draft --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-restart.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-restart.log 2>&1
```

## round6-final-role

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case role-change --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-role.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-role.log 2>&1
```

## round6-final-states-agy

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case states --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-states-agy.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-states-agy.log 2>&1
```

## round6-final-states-opencode

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case states --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-states-opencode.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-states-opencode.log 2>&1
```

## round6-final-t124

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-t124.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-t124.log 2>&1
```

## round6-final-t132

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t132_issues_panel_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-t132.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-t132.log 2>&1
```

## round6-final-t171

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t171_superseded_issue_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-t171.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-t171.log 2>&1
```

## round6-final-t216

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-t216.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-t216.log 2>&1
```

## round6-final-unknown

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case unknown --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-unknown.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-final-unknown.log 2>&1
```

## round6-green-history-claude-01

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case history --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-green-history-claude-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-green-history-claude-01.log 2>&1
```

## round6-green-provenance-claude-01

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case provenance --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-green-provenance-claude-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-green-provenance-claude-01.log 2>&1
```

## round6-green-provenance-codex-01

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli codex --case provenance --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-green-provenance-codex-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-green-provenance-codex-01.log 2>&1
```

## round6-green-recover-01

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case recover-unknown --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-green-recover-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-green-recover-01.log 2>&1
```

## round6-green-recover-done-01

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case recover-unknown --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-green-recover-done-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-green-recover-done-01.log 2>&1
```

## round6-green-restart-01

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case recover-restart --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-green-restart-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-green-restart-01.log 2>&1
```

## round6-green-unsent-01

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case never-sent --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-green-unsent-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-green-unsent-01.log 2>&1
```

## round6-mutant-attach-claude-01

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case history --mutant attach-only --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-mutant-attach-claude-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-mutant-attach-claude-01.log 2>&1
```

## round6-mutant-attach-codex-01

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli codex --case history --mutant attach-only --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-mutant-attach-codex-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-mutant-attach-codex-01.log 2>&1
```

## round6-mutant-early-01

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case recover-unknown --mutant skip-unknown-wait --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-mutant-early-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-mutant-early-01.log 2>&1
```

## round6-red-completion-claude-01

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case completion --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-red-completion-claude-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-red-completion-claude-01.log 2>&1
```

## round6-red-completion-codex-01

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli codex --case completion --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-red-completion-codex-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-red-completion-codex-01.log 2>&1
```

## round6-red-history-claude-01

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case history --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-red-history-claude-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-red-history-claude-01.log 2>&1
```

## round6-red-history-codex-01

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli codex --case history --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-red-history-codex-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-red-history-codex-01.log 2>&1
```

## round6-red-late-hook-01

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case delayed-hook --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-red-late-hook-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-red-late-hook-01.log 2>&1
```

## round6-red-recover-01

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case recover-unknown --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-red-recover-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-red-recover-01.log 2>&1
```

## round6-red-unsent-01

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case never-sent --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-red-unsent-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-red-unsent-01.log 2>&1
```

## round6-verified-agy

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli agy --vendor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-agy.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-agy.log 2>&1
```

## round6-verified-codex-local

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli codex --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-codex-local.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-codex-local.log 2>&1
```

## round6-verified-codex-vendor

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli codex --vendor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-codex-vendor.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-codex-vendor.log 2>&1
```

## round6-verified-completion-claude

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case completion --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-completion-claude.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-completion-claude.log 2>&1
```

## round6-verified-completion-codex

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli codex --case completion --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-completion-codex.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-completion-codex.log 2>&1
```

## round6-verified-history-claude

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case history --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-history-claude.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-history-claude.log 2>&1
```

## round6-verified-history-codex

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli codex --case history --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-history-codex.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-history-codex.log 2>&1
```

## round6-verified-identity

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case identity --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-identity.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-identity.log 2>&1
```

## round6-verified-mutant-attach-claude

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case history --mutant attach-only --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-mutant-attach-claude.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-mutant-attach-claude.log 2>&1
```

## round6-verified-mutant-attach-codex

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli codex --case history --mutant attach-only --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-mutant-attach-codex.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-mutant-attach-codex.log 2>&1
```

## round6-verified-mutant-blocked

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case states --mutant allow-blocked --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-mutant-blocked.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-mutant-blocked.log 2>&1
```

## round6-verified-mutant-early

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case recover-unknown --mutant skip-unknown-wait --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-mutant-early.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-mutant-early.log 2>&1
```

## round6-verified-mutant-force

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case states --mutant force-blocked --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-mutant-force.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-mutant-force.log 2>&1
```

## round6-verified-mutant-resend

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case unknown --mutant resend-unknown --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-mutant-resend.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-mutant-resend.log 2>&1
```

## round6-verified-mutant-working

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case states --mutant allow-working --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-mutant-working.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-mutant-working.log 2>&1
```

## round6-verified-opencode

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli opencode --vendor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-opencode.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-opencode.log 2>&1
```

## round6-verified-provenance-claude

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case provenance --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-provenance-claude.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-provenance-claude.log 2>&1
```

## round6-verified-provenance-codex

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli codex --case provenance --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-provenance-codex.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-provenance-codex.log 2>&1
```

## round6-verified-r2-duplicate

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --duplicate-submit --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-r2-duplicate.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-r2-duplicate.log 2>&1
```

## round6-verified-r2-offline

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_round2_e2e.py --case routing-offline --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-r2-offline.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-r2-offline.log 2>&1
```

## round6-verified-r2-online

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-r2-online.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-r2-online.log 2>&1
```

## round6-verified-r2-processor

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_round2_e2e.py --case processor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-r2-processor.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-r2-processor.log 2>&1
```

## round6-verified-race

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case race --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-race.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-race.log 2>&1
```

## round6-verified-recover-restart

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case recover-restart --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-recover-restart.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-recover-restart.log 2>&1
```

## round6-verified-recover

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case recover-unknown --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-recover.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-recover.log 2>&1
```

## round6-verified-restart-queue

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case restart-queue --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-restart-queue.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-restart-queue.log 2>&1
```

## round6-verified-restart-unknown

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case restart-unknown --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-restart-unknown.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-restart-unknown.log 2>&1
```

## round6-verified-restart

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case restart-draft --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-restart.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-restart.log 2>&1
```

## round6-verified-role

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case role-change --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-role.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-role.log 2>&1
```

## round6-verified-states-agy

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case states --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-states-agy.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-states-agy.log 2>&1
```

## round6-verified-states-opencode

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case states --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-states-opencode.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-states-opencode.log 2>&1
```

## round6-verified-t124

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t124.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t124.log 2>&1
```

## round6-verified-t132

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t132_issues_panel_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t132.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t132.log 2>&1
```

## round6-verified-t133-codex

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t133_codex_terminal_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t133-codex.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t133-codex.log 2>&1
```

## round6-verified-t133-mutant

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t133_codex_terminal_controller_e2e.py --mutant reply-as-message --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t133-mutant.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t133-mutant.log 2>&1
```

## round6-verified-t171

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t171_superseded_issue_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t171.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t171.log 2>&1
```

## round6-verified-t216

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t216.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t216.log 2>&1
```

## round6-verified-unknown

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case unknown --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-unknown.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-unknown.log 2>&1
```

## round6-verified-unsent

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case never-sent --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-unsent.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-unsent.log 2>&1
```

## 各项实际命令

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case restart-queue --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-restart-queue.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case restart-unknown --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-restart-unknown.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case states --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-states-agy.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case states --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-states-opencode.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case role-change --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-role.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case restart-draft --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-restart.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case unknown --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-unknown.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case race --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-race.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case identity --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-identity.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t216.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t216.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t216.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-r2-online.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-r2-online.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-r2-online.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-r2-offline.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-r2-offline.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case routing-offline --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-r2-offline.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-r2-processor.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-r2-processor.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case processor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-r2-processor.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-r2-duplicate.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-r2-duplicate.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --duplicate-submit --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-r2-duplicate.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t124.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t124.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t124.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t132.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t132.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t132_issues_panel_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t132.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t171.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t171.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t171_superseded_issue_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t171.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --mismatched-screen --output /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t212
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case states --mutant allow-blocked --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-mutant-blocked.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case states --mutant force-blocked --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-mutant-force.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case states --mutant allow-working --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-mutant-working.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case unknown --mutant resend-unknown --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-mutant-resend.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli codex --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-codex-local.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli agy --vendor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-agy.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli opencode --vendor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-opencode.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli codex --vendor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-codex-vendor.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t133-codex.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t133-codex.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t133_codex_terminal_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t133-codex.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t133-mutant.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t133-mutant.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t133_codex_terminal_controller_e2e.py --mutant reply-as-message --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-t133-mutant.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case history --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-history-claude.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli codex --case history --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-history-codex.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case completion --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-completion-claude.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli codex --case completion --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-completion-codex.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case never-sent --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-unsent.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case provenance --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-provenance-claude.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli codex --case provenance --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-provenance-codex.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case recover-unknown --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-recover.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case recover-restart --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-recover-restart.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case history --mutant attach-only --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-mutant-attach-claude.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_prompt_provenance_e2e.py --cli codex --case history --mutant attach-only --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-mutant-attach-codex.json
```

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case recover-unknown --mutant skip-unknown-wait --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-mutant-early.json
```

## 探针、清理与核对

```sh
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6_caller_probe.py > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-caller-probe-01.log 2>&1
```

```sh
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6_caller_target_probe.py > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-caller-probe-02.log 2>&1
```

```sh
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6_caller_working_probe.py > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-caller-probe-03.log 2>&1
```

```sh
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6_cleanup_packaged_controls.py > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-packaged-control-cleanup.log 2>&1
```

```sh
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6_cleanup_binaries.py > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-cleanup-final.json 2>&1
```

```sh
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6_verified_summary.py > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-verified-summary-final.log 2>&1
```

```sh
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6_verified_delivery_check.py > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round6-delivery-checks-final.log 2>&1
```

```sh
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
git diff --check
```
