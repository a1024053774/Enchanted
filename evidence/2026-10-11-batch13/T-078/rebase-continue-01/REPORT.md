# 变基停点 01：b3fb998c

2026-10-14，主控 #136。**冲突文件准备 PASS；变基整体 INCOMPLETE。** worker 只修改工作树文件，未 add、continue、skip、abort、stash、reset 或 clean。没有 CLI／API／Electron／模型启动，也没有额外代理。

固定 HEAD `87e954a2f4059d471e3e240872b565217e29b0b5`，REBASE_HEAD `b3fb998cf48574821c39440ece3f9ff897f26cf9`，当前是 1/27。备份 `backup/t078-before-09a3-main-c6b3a127ba23` 指向旧材料提交 `c6b3a127ba235221a528269d3cd107158e954917`。原日志 `/private/tmp/t078-rebase-09a3-a5TxSq` 的九个关键文件已逐字节复制到 logs/，六个未解决源码原件保存在 unresolved/，当前解决稿保存在 resolved/；不覆盖失败现场。

| 文件 | 冲突处理 |
| --- | --- |
| gates/core.ts | 同时保留 main 的 ScoreProvenance 和重放提交的 GateActor/SubmitCaller 分工定义；只解决该冲突，未加新行为。其余差异来自 Git 重放 b3fb998c。 |
| daemon.ts | 同时保留 scores_validate 与 controller_prepare；用实际凭据的 authority 处理窗口输入，保留 main 的审查结果／回收处理；reviewer 的事件来源保持其角色身份。 |
| panes.ts | 同时初始化 nativeEnded 与串行输入字段；保留 main 的会话结束、sendGateFeedback、sessionFacts、qualityFeedback 与 default 速度，以及 T-078 的用户输入、组合输入、队列占用和唤醒。 |
| store.ts | 同一 register 保存质量 context 和 inbox 身份：保留 main 的第四参数 context，收件箱身份为第五参数；Panes 的派发仍保留 T-078 第四参数 inbox，质量反馈用第五参数 context，并明确转接。没有第二套登记 API。 |
| relay.ts | reviewer 白名单仍仅 review_submit；worker 保留 submit/status/issue，加上 T-078 的 inbox 操作。身份、请求重放及结果处理不放宽。 |
| tests/daemon_acceptance_host.ts | 合并 fs 导入；先创建窗口操作端凭据，再沿用 main 的 controlled worker/reviewer runtime 和同一 serve 入口。 |

六文件无冲突标记、Node 语法检查及 git diff --check PASS。Git 索引仍为原六项 unmerged，交主控脚本 stage 后 continue。此处尚未重放后续真实 Claude、空框声明及 UPS 拦截提交，不能宣称当前是最终 T-078 产品，不能沿用变基前通过结论。

主控在与初始变基一致、不带会话钩子环境的控制端运行：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/rebase-continue-01/continue.sh
```

脚本先逐项核对固定 HEAD、REBASE_HEAD、exec/t078 变基状态、精确六项冲突清单、解决稿字节、无标记和语法，再仅 add 这六项并 continue 一次；execution/ 独占保存结果，遇下一次冲突就保留，不自动选边。已有 execution/ 拒绝覆盖。停点证据保持未跟踪，待重放结束后另行提交，不塞入旧提交的历史材料。

全部重放后还须重新取本候选证据、生成全新 09A-3 标签／根／身份／来源快照，并静态核对，才交 launch 审批。当前没有新 launch 审批，T-078 保持 open、INCOMPLETE。
