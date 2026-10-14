#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t083
test "$(git branch --show-current)" = exec/t083
test "$(git rev-parse HEAD)" = 10ada0328ad6f522de4612724b5802bc2e8a0efd
export A2A_PROJECT=a2a
export A2A_TASK=T-083
export A2A_ATTEMPT=a1
export A2A_SESSION=67ce5810-e135-4782-a6ff-80723dc4ab1b
export A2A_ROLE=worker
export A2A_LAUNCH=launch-1b1c894e009f4bd0b51f75ccc4401609
export A2A_LAUNCHES=/Users/luckye/Documents/Code/a2a/records/launches.jsonl
export CODEX_THREAD_ID=01a13bc6-4bf4-7d72-8361-985908f2393b
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=core.hooksPath
export GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a/scripts/git-hooks
git diff --check
git add -- acceptance/test_herdr_traceability_e2e.py evidence/2026-10-14-batch14/T-083/
git diff --cached --name-only | while IFS= read -r path; do
    case "$path" in
        acceptance/test_herdr_traceability_e2e.py|evidence/2026-10-14-batch14/T-083/*) ;;
        *) printf '超出 T-083 提交范围：%s\n' "$path" >&2; exit 1 ;;
    esac
done
git commit -m "test: align T-073 launch argv assertions (T-083)"
git log -1 --format=fuller --stat
