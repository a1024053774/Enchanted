# 第二次夹具失败诊断

PLAN / INCOMPLETE。`red02-20261024T033623Z.json` 仍停在 setup，checks 为空，未启动 Electron，不构成产品红态；原始现场 `/private/tmp/t161-8jx4h4c6` 保留。

现场事件 46 是匹配的 Stop，47 的 native_turn_facts 为 model=unknown、effort=unknown，49 的 relay_rejected 为 delivery_facts_unknown，51 进入 pane_idle。提交请求已成功排队并由 Stop 转交，不能再称为未触发 Stop。

根因是夹具协议不完整：门禁 core.ts 的交付条件要求 sessionFacts 返回的 model、effort 均已知；Panes.claudeTurnFacts 从 transcript 的 assistant.message.model 及 Stop.effort.level 取得它们。上一版夹具只生成 user 记录，Stop 不带 effort，按契约必然被拒。这是测试替身缺少输入，不是 T-161 产品缺陷。

本次仅修测试替身：受控 peer 在提交前输出一条明确标识 `t161-controlled-pty-no-model` 的模拟 assistant 记录，Stop 报模拟 effort=low；记录、提交钩子、Stop、门禁与 reviewer 启动仍走原生产入口。此身份是确定性 PTY 驱动器的标记，不代表实际供应商模型、推理或服务档位。summary 显式记录 simulated_delivery_facts 和来源，模型调用仍为 0。首次诊断中“model/effort 保持 unknown”的夹具选择已被本次证据否定；此前报告保留。

本次增加拒绝诊断：worker 完成首轮后立刻记录 native_turn_facts、relay_processed、relay_rejected；若交付被拒，立即带原因失败，不继续等待 submitted 超时。原 F02/F07 断言未修改，产品代码未修改。

局部解析探针 PASS：修改后的 peer 在 `/private/tmp/t161-facts-probe-_69h08ib` 生成 UPS、模拟回复和 Stop；直接调用 `3c56f743f` 隔离源码的 `Panes.prototype.claudeTurnFacts`，新记录读得 model=t161-controlled-pty-no-model、effort=low，同一解析器读取 red02 原现场仍为 unknown/unknown。这只验证缺失字段已补齐，不替代真实门禁交付或 Electron 验证。

重跑入口：`RUN-OUTSIDE-03.sh`。真实门禁交付及 Electron 红态仍待该运行确认。
