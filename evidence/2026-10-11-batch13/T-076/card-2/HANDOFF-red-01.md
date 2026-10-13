# T-076-2：阶段 1–3 沙箱外交接

准备状态：**PASS（静态检查）**；业务证据：**INCOMPLETE（尚未运行）**。授权为主控 #32、[决定01](controller-decision-01.md)。本阶段没有P-review或真实worker/reviewer入口，真实Codex预算仍 **0/8**。

## 执行命令与停止点

在主仓库运行；每个阶段需前一阶段的 `run.json` 为PASS，阶段目录已存在会拒绝重写。先执行第一条，核对报告后才执行下一条；遇INCOMPLETE保留现场并回传，不自动重试。

```sh
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh stage-1 red-01
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh stage-2 red-01
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh stage-3 red-01
```

输出根：`evidence/2026-10-11-batch13/T-076/card-2/outside-red-01/`。

1. **stage-1**：核对真实外置盘挂载、Node26.5/Git/Python版本、现有依赖能解析；校验产品/旧验收相对起点无diff。用`git archive`冻结`a7f4cc3033c16d5888de50d8352da516c941f8e9`，另存测试源码快照。源码和夹具在新`/tmp`目录；只有现有依赖引用，不移动或链接任何共享构建输出。本阶段不运行任何Codex命令，也不安装依赖。
2. **stage-2**：11个明确的新契约红态，见[assertion-hunks](assertion-hunks.md)。子测试保留退出1、`status=INCOMPLETE`及失败原文；外层只有在全部命中预写业务标识、无夹具/清理错误时才返回`status=PASS`，其含义仅是“预期红态取证完整”。`product_status`始终INCOMPLETE。
3. **stage-3**：8个既有保护对照全过后，三个单点产品变异体必须分别在指定业务断言失败。停止条件/输出含义同上。不声称完成新review/score/上限反例。

## 所用真实面与受控面

真实：`workbench/src/gates/cli.ts`、Unix socket、后台请求处理、Panes登记与空闲队列、Stop/signal与B relay、门禁、Git worktree/提交/引用、SQLite事件/状态。所有后台以`start_new_session=True`启动，记录并核对本进程PID；停止只用它自己的`daemon_stop`。

受控：`node-pty.spawn`、`Panes.processInfo`、本夹具生成的原生结构化记录。测试不启动zsh里的真实Codex；模拟终端只记录写入字节，在CR时生成预定turn事实。用于读版本的可执行文件是仅接受`--version`的夹具脚本，字符串`codex-cli 0.162.1`是**模拟输入，不是实际供应商CLI版本证明**。未复制auth，未安装真实session或Git hook，未连接Herdr或正式工作台。

没有改门禁结果、绕过caller检查、写入通过状态或注入一个review_passed布尔值。模拟进程号不会用于操作系统kill；模拟PTY的kill只调用本测试回调。后台PID则是真实自建进程，报告中明确区分。

## 结果分类与留存

- `ContractFailure`携带独立断言编号，只有与预写编号相符的失败可算预期红态；usage、JSON损坏、导入、socket、超时、版本/权限、意外协议错误均为harness_error，停止后交主控。
- 所有命令保留完整argv/cwd、stdout/stderr原始字节、退出码；signal的原始stdin单存。每个用例保存`case.json`、停止前数据库逐表读回、Git引用/worktree/status读回、B请求副本、后台输出；夹具原目录保留，打包归档。
- 一些红态会证明起点确实错误集成或回收；这仅发生于本次新建夹具仓库/模拟worker。原Git现场必须保留，不复位来“变绿”。
- 新增接口当前无法独立触达的部分写入`deferred-contracts.json`。缺review/缺分联合前置红态不等于已孤立证明score字段验证；缺首条反馈也不等于已证明第三次停止。
- 大于5 MB的夹具压缩包移到`/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-076/card-2/<标签-阶段>/`，仓库留pointer。原始大输出如仍>5 MB由`oversize_files`列明，未经压缩/外置归档不提交；不覆盖历史证据。
- 本阶段源测试有修改时，不接着跑同标签后续阶段；旧目录保留，选新label从stage-1重新冻结。若T-077已合入导致产品diff，stage-1直接停，先重读冲突位置。

请回传三阶段`run.json`及出现INCOMPLETE的用例/命令原始输出。收到实际红态后才能进入对应产品实现；P-review的具体argv/home/hook将另行交实例批准。
