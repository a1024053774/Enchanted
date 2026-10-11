# T-077 cards 收证据修复（主控 #43）

状态：**INCOMPLETE**。已读回：red-04 的 W11 起点红态成立，green-04 同一信号通过；regression-02 的 coop 8、recovery 9、run 18、cas 1 均有完整 PASS 收据。cards 的 test-result.json 为 15 项通过、0 failures/errors/skipped，但收证据发生 `KeyError: 'state'`，缺少最终 run.json，仍为 INCOMPLETE。原失败输出不覆盖。

根因：`TaskCardsCLI.setUp` 明确定义 `self.state = self.root / 'state'`，其 ARTIFACTS 只保存 root/test/task/base；runner 错把它当成已经含 state 字段的 recovery 记录。现仅在选择 cards 生产者时，将已知 `root/state` 加入 runner 的新记录副本。原 ARTIFACTS、产品代码及所有业务断言不变，没有通用缺字段兜底。

只重跑 cards，使用新目录 `outside-regression-03-cards`：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh cards-03
```

期望 15 项通过、收证据完成并写出 run.json；尚未执行，不预填 PASS。不重复已有 8/9/18/CAS 结果，不启动真实 Codex，真实用量仍 0/4。之后继续冲突流程红/绿、真实场景、独立审查及合流交付。
