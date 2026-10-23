---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: "20261023T204622Z-ideation-answer-001"
refs: ["evidence/2026-10-23-batch24/T-156/COVERAGE.md"]
created_at: "2026-10-23T22:39:44.580475Z"
schema: 1
title: "T-156：bootstrap 测试是唯一守护者，按裁定 C 不删，待决定"
id: "20261023T223944Z-executor-needs-decision-001"
---

按 20261023T204622Z 自建缺陷级票 T-156（ready_by executor）。实跑当前 main 8933ee0f4：旧 runner run_t082_boundary.py exit 1、INCOMPLETE（正常 tracer 七条过，第一个旧变异锚点已不存在）；test_t078_quality_host_bootstrap.py exit 0、PASS。覆盖对照：bootstrap（第 71～100 行）是 QualityCase.start_host → quality_chain_host.ts 两代隔离 operator 凭据创建、state/kind/0600 与清理的唯一直接守护者（T-152 用的是另一个 host），且它导入旧 runner 的 run_case，所以旧 runner 也不能单删。按用户裁定 C 的“唯一守护者退回决定”，两个文件都未删、HISTORICAL.md 未改；只合入调查证据（0f413d74c，未 push）。最小选项：A 保留两文件原样（可加一行历史头说明旧 runner 部分失效）；B 构思主控/用户明确退役 quality_chain_host 这部分历史覆盖后删除两文件；C 另行授权迁移（把凭据检查挪进现行测试后删旧 runner）。worker issue 20261023T223604Z-worker:b24-t156-issue-001。