# T-085 主控记录

## 开工 #14（2026-10-15 UTC，执行主控接续）

依据 ticket ready_rev 1（ready_by executor）。worktree /Users/luckye/Documents/Code/a2a-wt-t085（exec/t085，基于 main 6ba3bde4），npm ci（外置盘缓存），spawn-helper 755。worker 用 scripts/launch-worker 启动：Codex gpt-6.1-sol xhigh、service_tier default，launch-209c2887df444a53833d5013f7e8ee85，agent s15-t085（wF:p45）。任务卡 task-card-T-085-1.md 经 scripts/dispatch 派发。并发：Codex 会话 2 个（t078、t085），另有 Grok 会话 T-086（p3Z）。T-082 按既定顺序排在 T-078 之后，不开。

## 沙箱外运行与候选 #15–#23（2026-10-15 UTC）

#15：worker 首次运行前请求 `rm -rf evidence/.../T-085 && ...`，主控 Esc 拒绝（证据只追加），要求用新序号目录、沙箱外命令交主控跑。
主控跑 OUTSIDE-COMMANDS.sh 三轮（outside-run-01/02/03.log）：01 红 PASS、绿 5/5 失败于 /tmp 对 /private/tmp 路径断言、变异失败点不对（#20 退回）；02 绿目标用例停在 reviewing（重启后审查已建但测试未驱动受控 reviewer，#21 退回）；03 红 red-05 只目标失败、绿 green-03 5/5 ok、变异 mutant-03 只目标失败于配置来源不等。#22 让 worker 写 RESULTS。worker 报 T-085 READY。
主控提交候选 e059da18c（尾注取自启动记录 launch-209c2887df444a53833d5013f7e8ee85，Native-Session 取 Herdr 识别的 Codex 会话 01a13fb5-3147-77c0-8c89-da9deff70175）。证据 15 MB，无单文件 >5 MB。
#23：新开 fresh Codex reviewer s15-t085-rev1（wF:p47），argv：`herdr agent start s15-t085-rev1 --kind codex --pane wF:p47 -- --no-daemon -m gpt-6.1-sol -c model_reasoning_effort="xhigh" -c service_tier="default" -c check_for_update_on_startup=false --sandbox workspace-write --ask-for-approval on-request`（launch-worker 只记 worker 角色，reviewer 未写入 records/launches.jsonl）。只读，仅写 independent-review-01.md 与 REVIEW-OUTSIDE-COMMANDS.sh。Codex 会话 3 个（t078、t085、t085-rev1）。
