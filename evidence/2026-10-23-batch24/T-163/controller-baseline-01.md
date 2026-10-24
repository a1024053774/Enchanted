# RUN-OUTSIDE-01 主控读回

来源：执行主控在本 worker 会话的消息 #47。运行目录 `/private/tmp/t163-outside-01.SmfeFT`。两个真实 Haiku 主控各 2 个根提示，实际合计 4/16；摘要原件入仓库，不修改其运行结论。

## oracle：红态成立

`t163-outside-01.SmfeFT-oracle-baseline.json` 为 NO_GO，无 `error` 或清理错误。真实模型为 `claude-haiku-5-5`，CLI `2.1.310`，Node `v26.5.0`。

- `summary-good` 与 `summary-good-other-layout` 被误拒。生成的脚本额外要求文末出现全部食材名称，超出输入中“文末给出全部种类和库存总计”的要求。
- `shopping-inverted` 被误收。生成脚本只核对零库存食材名称及分组，没有拒绝“无需购买”的反向语义。
- 其余坏输入被拒。正确补货单与数据变化后的正确补货单被接受。

原件：`/private/tmp/t163-ywbbysgx/out/native-transcript.json`、`check_pantry.py`、`check_shopping.py`、各 case/run.json；待主控归档，不用旧 T-155 运行替代本次红态。

## C5：漏项未复现，派发被夹具阻断

主控独立阅读 `/private/tmp/t163-jqxklbu2/out/native-transcript.json` 与两张草稿卡，判断为：

- “无显式自检，结果无遗漏”。A 卡有文末总计、首版故意漏总计、等真实打回再补、不得提前补；B 卡有先 issue 询问、收到答复前不得写文件。
- 两卡的完成条件仅为 `test -f`，属于弱验收；尚未保存、注册或派发，摘要里的 `unknown_task` 与此一致。
- 多行 `set -e` / 变量 / for 循环形式的 card_save/create 被 Claude 的 dontAsk 权限拒绝。主控原样报告并停下，没有绕过。

worker 核对：`test_t163_controller_e2e.py` 在隔离 HOME 生成的 settings 明确配置 `defaultMode=dontAsk` 与有限 Bash 前缀；`workbench/src/panes.ts` 的 `startShell` 只建立 zsh 终端环境，`workbench/terminal/bin/claude` 只追加 `--plugin-dir`，均不注入这套主控权限。因此这是夹具配置问题，不是本票发现的产品权限缺陷，不修改产品权限。

RUN-OUTSIDE-02 将同一隔离主控的 Bash 工具授权用于绿态与恢复旧说明的 oracle 变异。场景提示和业务样本不变；变异用于区分提示词变化与夹具授权变化，不能将修前 C5 阻断或无显式自检写成“漏项红态”。
