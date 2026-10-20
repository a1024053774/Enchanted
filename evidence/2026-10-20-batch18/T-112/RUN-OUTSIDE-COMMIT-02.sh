#!/bin/zsh
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t112
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
export LC_ALL=C PYTHONDONTWRITEBYTECODE=1
export A2A_TASK=T-112
export A2A_ATTEMPT=a1
export A2A_SESSION=a1823572-94e7-4583-b6e7-0be9349bc52f
export A2A_ROLE=worker
export A2A_PROJECT=a2a
export A2A_LAUNCH=launch-4bae242ff4df4772b0a47a50c4eabdc9
export A2A_LAUNCHES=/Users/luckye/Documents/Code/a2a/records/launches.jsonl
export CODEX_THREAD_ID=01a15956-4232-7ee0-8601-276763e7e41a
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=core.hooksPath
export GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a/scripts/git-hooks
git diff --check
git add --sparse -- .project-map/roles/worker.md .project-map/roles/reviewer.md .project-map/roles/monitor.md .project-map/roles/ideation.md .project-map/roles/executor.md .project-map/inbox/20261020T124548Z-worker:t112-a1-issue-001.md .project-map/inbox/20261020T130602Z-worker:t112-a1-issue-001.md scripts/launch-worker workbench/README.md workbench/app/main.ts workbench/app/preload.ts workbench/app/renderer.tsx workbench/app/ExecutionSettings.tsx workbench/app/execution-settings.css workbench/src/claudeLaunch.ts workbench/src/executionSettings.ts workbench/src/store.ts workbench/src/panes.ts workbench/src/daemon.ts workbench/src/gates/core.ts workbench/src/gates/cli.ts workbench/src/contracts/a2aGates.ts workbench/src/contracts/modelOptions.ts workbench/tests/test_t093_launch_profile.ts workbench/tests/test_t112_archive.py workbench/tests/test_t091_pane_ipc.mjs workbench/tests/test_t112_execution.mjs workbench/tests/test_t112_counterfactuals.py workbench/tests/test_t112_herdr.py workbench/tests/run_t112_native.py workbench/tests/t112_settings_driver.mjs evidence/2026-10-20-batch18/T-112
git commit -m '修复 T-112 验证快照解包与 Claude 主控默认值'
git show -s --format=full HEAD
git status --short
