# T-077-1 首批实现检查交接（2026-10-11）

状态：**INCOMPLETE**，没有最终交付提交或整卡 PASS。

已独立读回 `outside-red-01/run.json`：13 个案例均 `business_red=true`，0 errors、真实回合 0；对应起点为 `14b57d22a84bcaebfa91c5051b9909b53a570fac`。该原始目录未改。

当前实现：worker/verify 命名；先保留引用再清理；撤销、改版、终结 run 的清理；dirty/unknown 保留并上报；交集默认拒绝及显式理由接口；dirty integration 上报。保留已有 Git 引用事务/检出工作区保护，未增加新存储表。认领占用锁只覆盖交集检查与 preparing 意图登记；同一后台不同 task 不能各自检查通过后争写同一范围。相关白名单 hunk 见 [assertion-hunks.md](assertion-hunks.md)。

R8、文本冲突回写、会话结束开新 attempt 与 reviewer 衔接尚未实现。主控消息确认 T-076-1 的回归，但当前 `main` 与本起点之间的 `workbench/src` diff 仍为空；未读取或改写主 checkout 的未提交代码，后续按主控安排合流。

执行命令：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh check-01
```

按顺序做两件事：

1. `outside-green-01`：运行 red-01 中除 R8 之外的 12 个相同 focused cases，期望全绿。失败则脚本停止并原样保留输出，不继续掩盖失败。
2. `outside-red-02`：新增“每次完成条件后独立作者再推进 main”的 R8 场景。要求一次初始验收加三次自动重验，共 4 次独立写入；第 4 次 CAS 落空必须停并有 issue。起点当前只执行一次验收便拒绝，没有 issue，因此预期业务红态。夹具作者最多写 5 次，避免将来错误的无限重验耗尽资源。

第二步使用 `outside-red-01/sources.tar.gz` 中的**原始产品源码**。准备器逐文件与 `git show <起点>:<文件>` 比较，然后放入新 `/tmp/s3-base-*`；不 checkout/reset/rebase 本分支。只有 node_modules 的读取链接指向本 worktree 已装依赖，不移动依赖、不重装、不在构建输出目录放链接。测试运行前再次逐字节核对原始归档，`baseline-binding.json` 记录来源；原始产品代码与当前测试一并保存到此次 sources 归档。

本次实际源码仍为工作区候选，完整内容见每批 `sources.tar.gz` 与 `preflight.json` 中的 diff。候选不是起点提交本身，不能用起点号替代未提交变更的身份。

两步均只用 `/tmp` 夹具与显式后台路径，不启动真实 Codex，不安装 hook，真实预算仍 **0/4**。确认退出只针对自建后台/子进程；原始现场归档并保留 `/tmp` 路径。单项失败为产品/协议失败或无法判定时交回主控，不能自动修业务断言。当前仅完成 Python AST、Node 语法/模块加载、Shell 语法检查，未运行候选业务检查。

下一步：由主控执行上述命令；若生命周期绿态成立且 red-02 确认，再实现有上限的 R8 并准备下一批冲突场景。此时不启动最终独立审查，不把分阶段进展称为整卡完成。
