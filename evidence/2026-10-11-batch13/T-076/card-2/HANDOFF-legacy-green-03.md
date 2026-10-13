# T-076-2 legacy-green-03交接

状态：**INCOMPLETE**。主控 #60 授权的F09夹具修复已完成，文件探针通过；动态门禁结果待执行。真实回合 **0/8**。

02的错误来自`/tmp`与`/private/tmp`拼写：reviewer home已登记，shell正确，但Panes传入realpath，旧夹具配置未规范为同一拼写。现在只在`prepare_review_control()`创建配置时固定真实root；严格home/shell条件不变，夹具另追加拒绝诊断。Panes、门禁、业务断言和旧证据均不改。

修复及W07前置核对见[fixture-path-repair-01/README](fixture-path-repair-01/README.md)。离线probe覆盖旧配置复现、新配置接受、陌生home/错误shell拒绝、session/turn字节及B文件；同时静态读回三条hook argv和身份调用链。probe首轮索引错误已单独保留，不能当作产品红态。

主控从主checkout执行：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh legacy-green legacy-green-03
```

单阶段顺序和边界沿[02交接](HANDOFF-legacy-green-02.md)：重新冻结 → F10/W07预写来源反事实 → 候选和完整回归。第一处非预期失败停止，不重试；不覆盖01/02，不启动真实Codex/P-review。

静态收据`legacy-ready-checks-03.json`的再生成命令（换新output保留历史）：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/check-legacy-preparation.py --output evidence/2026-10-11-batch13/T-076/card-2/legacy-ready-checks-03.json
```

本次fixture改动不会放宽产品home/shell校验；离线probe不能替代真实入口。完整T-076仍INCOMPLETE，交回READY后等待主控运行。
