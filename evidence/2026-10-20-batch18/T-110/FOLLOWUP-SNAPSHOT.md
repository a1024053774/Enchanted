# T-110 快照传输修复

INCOMPLETE。针对 `4455b51c8b55be979c8e7419fb500b517dd6f89e` 的真实入口第四轮，两个红态均被业务断言拒绝，green 在断连期间刷新时因快照缺字段抛 KeyError；该异常是测试夹具失败，不能当业务红态，也不能据此宣布整体绿态。

原因：`refresh()` 开始时清空 catalogError；驱动在该过渡期间读取不存在的 `.catalog-error` 得到 undefined。最终 JSON 序列化会丢弃属性，Python 的 `v['sidebar_error']` 因而抛错。现在只改驱动快照，让缺失的 sidebar_error、focused_agent、focused_launch、agent.project 和未挂载的 terminal_hidden 显式为 null；真实存在的错误文本原样保留，空文本仍为空文本。生产代码和业务场景的谓词、断言均未修改。

`test_t110_snapshot.mjs` 执行实际驱动内的 inspect 表达式并通过 JSON 往返，检查没有错误元素、过渡空文本、真实错误文本及未挂载／缺焦点／缺项目的状态。`snapshot-red-01.json` 在修前因序列化结果缺少 sidebar_error 失败；`snapshot-green-01.json` 同一检查 PASS。该本地检查证明快照传输契约，不冒称真实 Electron 全流程已通过。

第四轮原件仍在 `/private/tmp/t110-outside-04.json`；精简记录 `outside-04-summary.json`。原始夹具 `/private/tmp/t078-2-t110-59w7agw8` 未修改或删除。green 在首次断连时确已观察到 badge 0、通知为空和会话未知，随后在刷新过渡期间遇到上述夹具异常；刷新／重载／恢复完整流程仍需重跑。

```sh
zsh evidence/2026-10-20-batch18/T-110/RUN-OUTSIDE-COMMIT-03.sh
zsh evidence/2026-10-20-batch18/T-110/RUN-OUTSIDE-NO-MODEL.sh /private/tmp/t110-outside-05.json
```

提交脚本绑定 4455b51c8 起点及原 worker 身份，沿用自动尾注、LC_ALL=C、清除 Git 重定向变量和 `git add --sparse`。真实入口继续运行两个坏候选及修后正常／禁用场景；不调用模型、不保存截图。旧审查脚本的前缀问题已由主控接收，本次不改审查原件。
