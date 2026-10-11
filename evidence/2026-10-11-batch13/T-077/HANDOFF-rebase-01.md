# T-077 变基后同一候选复验（主控 #54）

状态：**INCOMPLETE**。执行主控已完成变基，当前候选为 `446f25c3de00925dfcc2f1c3f1375713676e166b`，父提交为 `457e02a867bfdc5d8b06a9d14214eb7a429c48c2`。本轮只编写证据目录中的复验脚本和说明，没有再修改产品、测试或业务断言。

执行命令：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh rebase-01
```

每一阶段前后核对 HEAD、父提交，以及 workbench、acceptance、分页夹具相对该候选的零差异；发现新增未跟踪的产品或测试文件同样拒绝。只允许本卡证据变化。各阶段使用新的 `outside-rebase-01-*` 目录或文件，不覆盖旧结果；任一阶段退出非零立即停止，后续阶段不能记为通过。

| 顺序 | 检查 | 预期 | 输出后缀 |
| --- | --- | --- | --- |
| 1 | S3 全部定点场景，含生命周期、路径交集、R8、工作区保护与冲突 7 项 | 25 项，0 failures/errors/skipped | `contracts` |
| 2～6 | 原回归套件 | coop 8、recovery 9、run 18、cas 1、cards 15，收证据完成 | 对应套件名 |
| 7 | 冲突窗格边界 | 4 项，全部通过 | `panes.json` |
| 8～9 | 原生末尾日志与派发状态旧探针 | 9 个场景和 1 个状态探针，failure 均为 null | `native-final`、`dispatch-state` |
| 10～11 | 直接受本次合流影响的稳定身份与停机检查 | 各 4 项通过；原测试不改 | `identity`、`shutdown` |

第 1 阶段已经包含冲突 7 项，不再单独重复运行。额外的身份和停机检查验证 main 侧的具体行为，不以静态标识计数代替它们。回归 runner 显式以父提交 `457e02a8` 作范围审计基线，仍核对 W01～W16 的起点坐标没有被上游改写，并只允许主控 #51 认可的两处 cwd 夹具修正；不把 main 的既有变化当成本卡改动。

阶段全部完成后，`summarize-rebase-01.py` 逐份读取最终回执，核对数量、失败、跳过、收证据错误和版本，保存 `outside-rebase-01-summary.json`。脚本还运行项目地图 status，保存 Panes 原始夹具。超过 5 MB 的新输出逐字节核对后归档到 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-077/`，仓库内留路径和重放命令。不删除异常结果，不重试业务命令。

本轮没有真实 Codex 入口，不复制 auth、不创建真实模型会话，真实预算仍 **0/4**。汇总 PASS 仅表示变基后的脚本检查通过；真实 worker 整理、同一隔离 home 内历史根 CLI 记录保留与新身份归属、一次独立审查均仍待后续。通过后另交准确 argv、隔离 home 和 hook 清单。

本次准备检查命令为：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/audit_s3_assertions.py --base 457e02a867bfdc5d8b06a9d14214eb7a429c48c2 --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/rebase-preparation-scope-02.json
bash -n /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh
```

首次审计写入 `rebase-preparation-scope-01.json`，重放使用新输出名。行为检查尚未在此候选执行，不能将语法与范围审计记作业务 PASS。
