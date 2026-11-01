# 第五轮命令与重跑

工作目录：`/Users/luckye/Documents/Code/a2a-worktrees/T-216`。每次重跑使用新输出名，保留既有结果。

完整矩阵先在 T124 遇到 ENOSPC 后停止；清理自有终止夹具的可重建安装副本后，另名续跑失败和未运行项。两份输出合并后有 27 项符合预期退出码，其中 4 项是应被拒绝的业务反例。

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5_verified_matrix.py > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-matrix.log 2>&1
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5_resume_verified.py > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-resume-matrix.log 2>&1
```

以上是实际外层命令。脚本禁止覆盖；重跑整个矩阵须复制脚本并统一改用新前缀。以下是各子进程的完整实际命令；单项重跑也先改输出名。退出 1 只有在业务失败位置另外核对后，才计作反例证据。

### round5-verified-restart-queue (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case restart-queue --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-restart-queue.json
```

### round5-verified-restart-unknown (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case restart-unknown --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-restart-unknown.json
```

### round5-verified-states-agy (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case states --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-states-agy.json
```

### round5-verified-states-opencode (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case states --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-states-opencode.json
```

### round5-verified-role (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case role-change --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-role.json
```

### round5-verified-restart (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case restart-draft --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-restart.json
```

### round5-verified-unknown (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case unknown --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-unknown.json
```

### round5-verified-race (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case race --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-race.json
```

### round5-verified-identity (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case identity --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-identity.json
```

### round5-verified-t216 (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t216.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t216.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t216.json
```

### round5-verified-r2-online (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-r2-online.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-r2-online.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-r2-online.json
```

### round5-verified-r2-offline (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-r2-offline.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-r2-offline.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case routing-offline --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-r2-offline.json
```

### round5-verified-r2-processor (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-r2-processor.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-r2-processor.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case processor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-r2-processor.json
```

### round5-verified-r2-duplicate (exit=1, expected=1)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-r2-duplicate.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-r2-duplicate.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --duplicate-submit --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-r2-duplicate.json
```

### round5-verified-t124-02 (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t124-02.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t124-02.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t124-02.json
```

### round5-verified-t132 (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t132.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t132.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t132_issues_panel_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t132.json
```

### round5-verified-t171 (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t171.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t171.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t171_superseded_issue_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t171.json
```

### round5-verified-t212 (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --mismatched-screen --output /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t212
```

### round5-verified-mutant-blocked (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case states --mutant allow-blocked --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-mutant-blocked.json
```

### round5-verified-mutant-force (exit=1, expected=1)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case states --mutant force-blocked --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-mutant-force.json
```

### round5-verified-mutant-working (exit=1, expected=1)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case states --mutant allow-working --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-mutant-working.json
```

### round5-verified-mutant-resend (exit=1, expected=1)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case unknown --mutant resend-unknown --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-mutant-resend.json
```

### round5-verified-codex-local (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli codex --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-codex-local.json
```

### round5-verified-agy (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli agy --vendor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-agy.json
```

### round5-verified-opencode (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli opencode --vendor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-opencode.json
```

### round5-verified-codex-vendor (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli codex --vendor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-codex-vendor.json
```

### round5-verified-t133-codex (exit=0, expected=0)

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t133-codex.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t133-codex.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t133_codex_terminal_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t133-codex.json
```

### round5-agy-vendor-01.json

```sh
python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli agy --vendor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-agy-vendor-01.json
```

### round5-codex-local-01.json

```sh
python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli codex --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-codex-local-01.json
```

### round5-codex-local-02.json

```sh
python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli codex --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-codex-local-02.json
```

### round5-codex-substitute-01.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli codex --case basic --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-codex-substitute-01.json
```

### round5-codex-vendor-01.json

```sh
python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli codex --vendor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-codex-vendor-01.json
```

### round5-final-agy.json

```sh
python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli agy --vendor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-agy.json
```

### round5-final-codex-local.json

```sh
python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli codex --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-codex-local.json
```

### round5-final-codex-vendor.json

```sh
python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli codex --vendor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-codex-vendor.json
```

### round5-final-identity.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case identity --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-identity.json
```

### round5-final-mutant-blocked.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case states --mutant allow-blocked --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-mutant-blocked.json
```

### round5-final-mutant-force.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case states --mutant force-blocked --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-mutant-force.json
```

### round5-final-mutant-resend.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case unknown --mutant resend-unknown --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-mutant-resend.json
```

### round5-final-mutant-working.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case states --mutant allow-working --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-mutant-working.json
```

### round5-final-opencode.json

```sh
python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli opencode --vendor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-opencode.json
```

### round5-final-r2-duplicate.hc.json

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --duplicate-submit --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-r2-duplicate.json
```

### round5-final-r2-duplicate.json

```sh
python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --duplicate-submit --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-r2-duplicate.json
```

### round5-final-r2-offline.hc.json

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case routing-offline --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-r2-offline.json
```

### round5-final-r2-offline.json

```sh
python3 workbench/tests/test_t216_round2_e2e.py --case routing-offline --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-r2-offline.json
```

### round5-final-r2-online.hc.json

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-r2-online.json
```

### round5-final-r2-online.json

```sh
python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-r2-online.json
```

### round5-final-r2-processor.hc.json

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case processor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-r2-processor.json
```

### round5-final-r2-processor.json

```sh
python3 workbench/tests/test_t216_round2_e2e.py --case processor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-r2-processor.json
```

### round5-final-race.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case race --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-race.json
```

### round5-final-red-agy.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case basic --source /private/tmp/t216-r5-before-7gr4zxtp --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-red-agy.json
```

### round5-final-red-opencode.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case basic --source /private/tmp/t216-r5-before-7gr4zxtp --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-red-opencode.json
```

### round5-final-restart.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case restart-draft --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-restart.json
```

### round5-final-role.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case role-change --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-role.json
```

### round5-final-states-agy.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case states --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-states-agy.json
```

### round5-final-states-opencode.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case states --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-states-opencode.json
```

### round5-final-t124.hc.json

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-t124.json
```

### round5-final-t124.json

```sh
python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-t124.json
```

### round5-final-t132.hc.json

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t132_issues_panel_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-t132.json
```

### round5-final-t132.json

```sh
python3 workbench/tests/test_t132_issues_panel_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-t132.json
```

### round5-final-t133-codex.hc.json

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t133_codex_terminal_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-t133-codex.json
```

### round5-final-t133-codex.json

```sh
python3 workbench/tests/test_t133_codex_terminal_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-t133-codex.json
```

### round5-final-t171.hc.json

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t171_superseded_issue_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-t171.json
```

### round5-final-t171.json

```sh
python3 workbench/tests/test_t171_superseded_issue_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-t171.json
```

### round5-final-t216.hc.json

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-t216.json
```

### round5-final-t216.json

```sh
python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-t216.json
```

### round5-final-unknown.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case unknown --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-final-unknown.json
```

### round5-green-agy-01.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-green-agy-01.json
```

### round5-green-opencode-01.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-green-opencode-01.json
```

### round5-green-restart-draft-01.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case restart-draft --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-green-restart-draft-01.json
```

### round5-green-restart-queue-01.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case restart-queue --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-green-restart-queue-01.json
```

### round5-green-restart-unknown-01.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case restart-unknown --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-green-restart-unknown-01.json
```

### round5-green-role-change-01.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case role-change --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-green-role-change-01.json
```

### round5-identity-01.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case identity --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-identity-01.json
```

### round5-mutant-allow-blocked-01.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case states --mutant allow-blocked --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-mutant-allow-blocked-01.json
```

### round5-mutant-allow-blocked-02.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case states --mutant allow-blocked --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-mutant-allow-blocked-02.json
```

### round5-mutant-force-01.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case states --mutant force-blocked --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-mutant-force-01.json
```

### round5-mutant-force-02.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case states --mutant force-blocked --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-mutant-force-02.json
```

### round5-mutant-resend-01.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case unknown --mutant resend-unknown --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-mutant-resend-01.json
```

### round5-mutant-resend-02.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case unknown --mutant resend-unknown --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-mutant-resend-02.json
```

### round5-mutant-working-01.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case states --mutant allow-working --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-mutant-working-01.json
```

### round5-mutant-working-02.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case states --mutant allow-working --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-mutant-working-02.json
```

### round5-opencode-vendor-01.json

```sh
python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli opencode --vendor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-opencode-vendor-01.json
```

### round5-opencode-vendor-02.json

```sh
python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli opencode --vendor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-opencode-vendor-02.json
```

### round5-r2-duplicate-01.hc.json

```sh
python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --duplicate-submit --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-r2-duplicate-01.json
```

### round5-r2-duplicate-01.json

```sh
python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --duplicate-submit --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-r2-duplicate-01.json
```

### round5-r2-offline-01.hc.json

```sh
python3 workbench/tests/test_t216_round2_e2e.py --case routing-offline --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-r2-offline-01.json
```

### round5-r2-offline-01.json

```sh
python3 workbench/tests/test_t216_round2_e2e.py --case routing-offline --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-r2-offline-01.json
```

### round5-r2-online-01.hc.json

```sh
python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-r2-online-01.json
```

### round5-r2-online-01.json

```sh
python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-r2-online-01.json
```

### round5-r2-processor-01.hc.json

```sh
python3 workbench/tests/test_t216_round2_e2e.py --case processor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-r2-processor-01.json
```

### round5-r2-processor-01.json

```sh
python3 workbench/tests/test_t216_round2_e2e.py --case processor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-r2-processor-01.json
```

### round5-race-01.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case race --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-race-01.json
```

### round5-race-02.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case race --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-race-02.json
```

### round5-race-03.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case race --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-race-03.json
```

### round5-red-agy-01.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-red-agy-01.json
```

### round5-red-opencode-01.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-red-opencode-01.json
```

### round5-red-restart-draft-02.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case restart-draft --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-red-restart-draft-02.json
```

### round5-red-restart-queue-01.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case restart-queue --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-red-restart-queue-01.json
```

### round5-red-restart-unknown-01.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case restart-unknown --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-red-restart-unknown-01.json
```

### round5-red-role-change-01.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case role-change --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-red-role-change-01.json
```

### round5-states-agy-01.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case states --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-states-agy-01.json
```

### round5-states-agy-02.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case states --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-states-agy-02.json
```

### round5-states-opencode-01.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case states --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-states-opencode-01.json
```

### round5-t124-01.hc.json

```sh
python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t124-01.json
```

### round5-t124-01.json

```sh
python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t124-01.json
```

### round5-t124-02.hc.json

```sh
python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t124-02.json
```

### round5-t124-02.json

```sh
python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t124-02.json
```

### round5-t124-03.hc.json

```sh
python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t124-03.json
```

### round5-t124-03.json

```sh
python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t124-03.json
```

### round5-t124-main-01.hc.json

```sh
python3 workbench/tests/test_t124_controller_e2e.py --revision main --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t124-main-01.json
```

### round5-t124-main-01.json

```sh
python3 workbench/tests/test_t124_controller_e2e.py --revision main --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t124-main-01.json
```

### round5-t124-main-02.hc.json

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5_main_control.py /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t124-main-02.json
```

### round5-t124-main-02.json

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216/workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t124-main-02.json
```

### round5-t124-main-03.hc.json

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5_main_control.py /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t124-main-03.json
```

### round5-t124-main-03.json

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216/workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t124-main-03.json
```

### round5-t124-packaged-01.hc.json

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5_main_control.py /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t124-packaged-01.json --candidate
```

### round5-t124-packaged-01.json

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216/workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t124-packaged-01.json
```

### round5-t132-01.hc.json

```sh
python3 workbench/tests/test_t132_issues_panel_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t132-01.json
```

### round5-t132-01.json

```sh
python3 workbench/tests/test_t132_issues_panel_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t132-01.json
```

### round5-t133-codex-01.hc.json

```sh
python3 workbench/tests/test_t133_codex_terminal_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t133-codex-01.json
```

### round5-t133-codex-01.json

```sh
python3 workbench/tests/test_t133_codex_terminal_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t133-codex-01.json
```

### round5-t133-codex-02.hc.json

```sh
python3 workbench/tests/test_t133_codex_terminal_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t133-codex-02.json
```

### round5-t133-codex-02.json

```sh
python3 workbench/tests/test_t133_codex_terminal_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t133-codex-02.json
```

### round5-t133-mutant-business.hc.json

```sh
python3 workbench/tests/test_t133_codex_terminal_controller_e2e.py --mutant reply-as-message --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t133-mutant-business.json
```

### round5-t133-mutant-business.json

```sh
python3 workbench/tests/test_t133_codex_terminal_controller_e2e.py --mutant reply-as-message --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t133-mutant-business.json
```

### round5-t171-01.hc.json

```sh
python3 workbench/tests/test_t171_superseded_issue_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t171-01.json
```

### round5-t171-01.json

```sh
python3 workbench/tests/test_t171_superseded_issue_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t171-01.json
```

### round5-t216-01.hc.json

```sh
python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t216-01.json
```

### round5-t216-01.json

```sh
python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t216-01.json
```

### round5-t216-02.hc.json

```sh
python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t216-02.json
```

### round5-t216-02.json

```sh
python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t216-02.json
```

### round5-t216-03.hc.json

```sh
python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t216-03.json
```

### round5-t216-03.json

```sh
python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-t216-03.json
```

### round5-unknown-01.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case unknown --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-unknown-01.json
```

### round5-unknown-02.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case unknown --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-unknown-02.json
```

### round5-unknown-03.json

```sh
python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case unknown --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-unknown-03.json
```

### round5-verified-r2-duplicate.hc.json

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --duplicate-submit --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-r2-duplicate.json
```

### round5-verified-r2-offline.hc.json

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case routing-offline --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-r2-offline.json
```

### round5-verified-r2-online.hc.json

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-r2-online.json
```

### round5-verified-r2-processor.hc.json

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case processor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-r2-processor.json
```

### round5-verified-t124-02.hc.json

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t124-02.json
```

### round5-verified-t124.hc.json

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t124.json
```

### round5-verified-t124.json

```sh
python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t124.json
```

### round5-verified-t132.hc.json

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t132_issues_panel_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t132.json
```

### round5-verified-t133-codex.hc.json

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t133_codex_terminal_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t133-codex.json
```

### round5-verified-t171.hc.json

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t171_superseded_issue_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t171.json
```

### round5-verified-t216.hc.json

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-verified-t216.json
```

## 其他实际操作与交付检查

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5_hc_probe.py --output /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-hc-probe-NEW.json
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5_codex_allow_request.py
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5_clean_fixture_binaries.py
git diff --check
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5_delivery_check.py
```

后两份操作脚本绑定了当时的自有测试窗口或清理清单，禁止拿去操作别人的终端；不可重复批准同一申请或覆盖清理清单。首次 Codex 供应商确认的单次 `a2a request executor` 批准有 manual-approval.json；后续夹具将同一精确选择核对纳入代码，未批准命令前缀。

main 对照的实际提交为 `4a31cf3e09afabd095e99c6bd74eee87f2479090`，其 workbench/src 与 9c0e26212 无差异；副本预放同一固定 hc 构件以免缺缓存下载超过启动期限，原测试和断言不改。对应 .source.json 保存版本与副本位置。

探针启动等待不足、变异定位失败、operator 文件冲突、main 启动超时、ENOSPC 都保留，不作为业务红态或通过证据。原 T133 靶点旧文件保存在 round5-t133-before-target-fix.py；靶点修正后的 mutant-business 才是业务反例。

## TMPDIR=/private/tmp

```sh
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5_confined_matrix.py > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-matrix.log 2>&1
```

### round5-confined-restart-queue

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case restart-queue --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-restart-queue.json
```

### round5-confined-restart-unknown

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case restart-unknown --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-restart-unknown.json
```

### round5-confined-states-agy

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case states --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-states-agy.json
```

### round5-confined-states-opencode

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case states --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-states-opencode.json
```

### round5-confined-role

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case role-change --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-role.json
```

### round5-confined-restart

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case restart-draft --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-restart.json
```

### round5-confined-unknown

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case unknown --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-unknown.json
```

### round5-confined-race

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case race --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-race.json
```

### round5-confined-identity

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case identity --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-identity.json
```

### round5-confined-t216

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-t216.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-t216.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-t216.json
```

### round5-confined-r2-online

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-r2-online.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-r2-online.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-r2-online.json
```

### round5-confined-r2-offline

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-r2-offline.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-r2-offline.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case routing-offline --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-r2-offline.json
```

### round5-confined-r2-processor

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-r2-processor.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-r2-processor.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case processor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-r2-processor.json
```

### round5-confined-r2-duplicate

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-r2-duplicate.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-r2-duplicate.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --duplicate-submit --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-r2-duplicate.json
```

### round5-confined-t124

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-t124.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-t124.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-t124.json
```

### round5-confined-t132

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-t132.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-t132.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t132_issues_panel_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-t132.json
```

### round5-confined-t171

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-t171.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-t171.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t171_superseded_issue_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-t171.json
```

### round5-confined-t212

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --mismatched-screen --output /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-t212
```

### round5-confined-mutant-blocked

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case states --mutant allow-blocked --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-mutant-blocked.json
```

### round5-confined-mutant-force

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case states --mutant force-blocked --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-mutant-force.json
```

### round5-confined-mutant-working

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli agy --case states --mutant allow-working --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-mutant-working.json
```

### round5-confined-mutant-resend

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case unknown --mutant resend-unknown --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-mutant-resend.json
```

### round5-confined-codex-local

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli codex --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-codex-local.json
```

### round5-confined-agy

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli agy --vendor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-agy.json
```

### round5-confined-opencode

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli opencode --vendor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-opencode.json
```

### round5-confined-codex-vendor

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t216_real_cli_delivery_e2e.py --cli codex --vendor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-codex-vendor.json
```

### round5-confined-t133-codex

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-t133-codex.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-t133-codex.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t133_codex_terminal_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-t133-codex.json
```

### round5-confined-t133-mutant

```sh
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-t133-mutant.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-t133-mutant.json -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t133_codex_terminal_controller_e2e.py --mutant reply-as-message --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5-confined-t133-mutant.json
```

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5_confined_summary.py
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round5_confined_delivery_check.py
```
