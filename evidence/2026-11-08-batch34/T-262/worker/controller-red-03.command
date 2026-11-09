# 仅供主控在其沙箱外工具执行；worker 未执行此命令。
# 工具 cwd：/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-262-1-a1
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --revision f80d5cdbf0e1b62de864300eff7bb4497f8c4c70 --summary /Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/red-outside-03.json
