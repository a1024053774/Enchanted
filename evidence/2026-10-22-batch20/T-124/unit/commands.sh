#!/bin/zsh
# Run from workbench/. HEAD copies are written by: git -C .. show HEAD:workbench/app/notificationCenter.ts > $H/notificationCenter.ts
E=../evidence/2026-10-22-batch20/T-124/unit
node tests/test_t124_quota_notice.mjs $E/quota-green.json
node tests/test_t124_quota_notice.mjs $E/quota-red-head.json $H/notificationCenter.ts
python3 tests/test_t093_process_snapshot.py $E/t093-green.json
python3 tests/test_t121_role_request_e2e.py --summary $E/t121-green.json
