# T-158-1 / a1 阶段结果

**INCOMPLETE，待主控运行 RUN-OUTSIDE-01**。worker `b24-t158`，分支 `exec/t158`；产品基线 `c01742804961214ed025b6c9fb9924a1ea49ee2d`。

目标：按任务卡证明修订后正常重试成功，同时保留旧 attempt 活跃时的路径拒绝。不扩展到其他 ticket，不更改路径安全边界。

此前的决定阻塞见 [NEEDS-DECISION-01.md](NEEDS-DECISION-01.md)。主控 #36 已传回用户选择显式 reclaim 后释放；当前执行依据与文件范围见 [DECISION-01.md](DECISION-01.md)。

新增本票测试 `workbench/tests/test_t158_revise_retry_e2e.py`，含真实流程、帮助/角色说明检查、`--revision` 与三个 `--mutant`，尚未修改产品说明或门禁。真实流程将先跑修前基线；如果 reclaim 后已经成功，则只需补说明。

验收状态：

| 验收 | 状态与证据 |
| --- | --- |
| 真实 Electron：打回 → v2 → revise → 对旧 attempt reclaim → 正常 dispatch 一次成功 | INCOMPLETE；RUN-OUTSIDE-01 待主控运行 |
| 旧 attempt 活跃时继续拒绝 | INCOMPLETE；仅阅读实现，不以源码推断代替运行证据 |
| 角色说明与 a2a help 写明步骤 | 修前红态已取得；尚未修改说明 |
| 修后绿态、变异与既有 e2e 回归 | INCOMPLETE；待基线流程结果后推进 |

本地红态命令：`python3 workbench/tests/test_t158_revise_retry_e2e.py --check instructions --summary evidence/2026-10-23-batch24/T-158/instructions-red-01.json`。exit 1；真实帮助入口 exit 0，五项可发现性检查失败，errors 为空；与修前现象一致。输出见 [instructions-red-01.json](instructions-red-01.json)。这份文本证据不证明回收或重派行为。

本地 `zsh -n evidence/2026-10-23-batch24/T-158/RUN-OUTSIDE-01.sh` 与 Python AST 语法检查通过。一次 `python3 -m py_compile` 因系统 Python 想写沙箱外的 `/Users/luckye/Library/Caches/com.apple.python/...` 返回 PermissionError，未提权；语法检查改用不写缓存的 AST 解析，未把该环境错误算红态。

未改产品、全局配置或其他任务。临时夹具仅位于 `/private/tmp/t158-*`，不是项目额外目录；供应商模型回合数 0。

启动及阶段记录完成前运行 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`：均 exit 0，Problems 0、Stale living docs 0。末次输出见 [status-final-01.txt](status-final-01.txt)。

原阻塞问题条目为 `20261024T003159Z-worker:b24-t158-issue-001`；主控 #36 已传回上述裁定，worker 不自行关闭 blocking issue。

沙箱外请求：[RUN-OUTSIDE-01.sh](RUN-OUTSIDE-01.sh)。运行 `zsh evidence/2026-10-23-batch24/T-158/RUN-OUTSIDE-01.sh`；它先跑修前真实流程，再跑同修前版本的帮助文本红态，输出每次新建。请主控回传两份 JSON 路径；夹具按 T-088 由主控归档。未请求提权，未在此启动后台或 Electron。

说明修复后的相关既有回归为 `workbench/tests/test_t121_role_request_e2e.py`（终端命令、主控身份与插件挂载）。若需要改门禁，再增跑 S3 的路径交集、clean revise、dirty revoke 与 historical cleanup 场景；不会把历史候选的通过结论当作本票证据。
