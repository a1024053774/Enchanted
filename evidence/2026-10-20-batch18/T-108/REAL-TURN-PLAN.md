# T-108 真实回合：已批准，尚未运行

2026-10-20 主控 #13 转述用户逐字：“跑真实回合,版本不重要,以后肯定要经常更新 cli 版本的”。据此取代提交 16b412964 中本文件的版本前置与手工命令。

本次批准 Claude **1 个根回合**：haiku 5.5、low，T-093 正常登录入口；失败不补发、不自动重跑。预计 2 条生成请求，CLI 自身重试逐条记账，不能把 1 根写成 1 次 API 请求。F/D 生命周期 600 秒。Codex 用已保存原件回放，新增真实回合 **0**。不改 panes.ts 的 xhigh 问题，由主控另票处理。

## 执行顺序

先提交修订候选（RUN-OUTSIDE-COMMIT-02.sh），再运行以下两份脚本。它们尚未执行；工作目录是本 worker 的 worktree，依赖与构建没有链接到主仓库。

```sh
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-VERSION-PROBE-01.sh /private/tmp/t108-version-probe-01.json
```

版本探针沿用 T-093 的隔离登录与 onboarding 探针，读取当前安装 CLI 版本，复制登录后核对 auth status；生成当前隔离 cwd 的 onboarding／信任状态，禁止业务按键，仅答终端协议。CLI 只连接本地假服务，真实模型／供应商请求为 0。版本取不到、启动状态不符合假设、HOME/网络边界失败或清理未确认时停止并上报，不默许新界面。保留旧探针的全部安全检查，未修改其清单差异判定。

只有探针 PASS 后才运行：

```sh
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-REAL-01.sh /private/tmp/t108-version-probe-01.json /private/tmp/t108-real-01.summary.json
```

真实脚本再次读取当前版本，并要求与探针记录一致；版本变化时重新做探针，不偷偷使用旧结论。经 `claudeLoginSession.py → 受保护 daemon → controller_start → 交互 PTY` 启动，不使用普通 daemon_start 替代保护入口。精确版本号写入 manifest、启动记录与最终 T-093 facts，不再只允许 2.1.302；身份、来源、私有 session、auth_original_reads=1、HOME 禁写、网络与凭据清理检查保留。

脚本只提交一次根输入；角色说明要求一次 AskUserQuestion，问题为“选择部署区域？”，选项“东区／西区”，multiSelect=false。Electron 显示问题和等待用户状态后，DOM 选择“西区”写回原 PTY。核对 PostToolUse 的答案、同 prompt_id 的 Stop、idle、answer 用户输入的 reply_to／target.request／thread，以及重复拒绝。finally 走正常 daemon_stop、正常登录事实检查与进程退出核验，不截屏、不调用任何第二根输入。

## 证据边界

版本构造、重复消费、HOME/端口/清理辅助合同、版本拒绝与 T-096 恢复合同已本地通过。新脚本只有语法与局部逻辑检查，未执行真实登录版本探针或模型，不宣称实际 2.1.304 内部状态或真实回合已通过。

Codex 原件及来源见 native-hook-samples.json；回放为已安装 0.163.0 CLI 在本地假 API 下产生的实际 hooks，不称其为供应商真实模型证据。主控 #13 已批准本轮采用回放、真实新增 0。
