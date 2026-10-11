# T-078-1 第一检查点：P1 与输入／凭据红态

2026-10-11。**INCOMPLETE**：探针和红态测试已准备，沙箱外部分尚未运行。执行主控决定 01 已原样留档。本轮未修改产品代码，未运行 Claude、Claude 夹具或真实 Codex。

执行命令（由执行主控在沙箱外运行）：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh
```

输出到本 worktree 的 `T-078/outside-red-01/`。目录存在即拒绝，复跑必须传入新的标签；不要覆盖失败证据。此检查点要求产品仍处于起点 `14b57d22a84bcaebfa91c5051b9909b53a570fac`，不先变基。

## 运行内容与独立预期

1. **P1 库探针**：独立 Electron 窗口加载已安装 xterm 6.0.0。先证明裸 onData 包含设备应答；再用公开 parser 扩展接管协议查询，检查键盘、中文粘贴、合成 composition、大段粘贴、输出与输入交错、focus 应答。只用公开接口，没有访问私有字段、修改依赖或安装依赖。已核对本地 public/Terminal.ts，parser 不需要开启 proposed API。任何一项失败就停止。
2. **产品入口红态**：生产 Electron → IPC → 后台 → node-pty；仅把付费 CLI 换成确定性的 Python 字节接收器。它为现有启动器的固定版本检查返回一个夹具版本字符串，并生成一条合成 session_meta 供末尾归档；这不是真实 Codex 验收，也不生成 Claude 事件。无凭据、无 API、无模型调用。
3. **固定三项断言**：中文粘贴与提交到达真实 PTY；库里有该句用户输入及同 attempt 的人工介入；匿名调用即使写 `--from ideation` 也不能追加收件箱条目。预期起点分别出现：没有输入字节、没有用户输入及介入、伪造角色的条目已经入库。

每个断言保存预期、实际值、命令、退出码和独立 SQL 读回。P1 是库事实，不能替代产品来源认证；合成组合事件不能证明真实 macOS 输入法。产品红态仅覆盖这三项，其余启动、队列、收件箱与停止行为仍需各自红态后再实现。

## 停止、隔离与保留

- 三个预期行为红态才使本检查点的 `checkpoint_status` 为 PASS；任务总状态仍为 INCOMPLETE。初始化、构建、权限、探针或清理错误不计红态。
- P1 失败、实际结果不等于上述预期、或未知结果均停止，保留现场交主控。脚本不安装依赖、不重试业务请求、不修改断言。
- 项目、配置、接收器数据和 Electron 用户目录均在本卡 `/tmp` 夹具或证据目录；没有读取用户认证信息。产品 daemon detached，Electron 独立进程组；只关闭自己创建的窗口与后台。
- 标准产品构建输出进入外置盘的新构建槽；缺盘直接失败。夹具源与完整现场分别归档；单文件超过 5 MB 会报告并阻止直接交付。
- `sources.tar.gz` 保存本次所用产品和测试源，`entry-red/fixture.tar.gz` 保存无凭据夹具；截图、原始收字节、逐命令输出、SQLite 查询另存。凭据引入后需重新检查归档范围，不能沿用“夹具无凭据”的假设。

沙箱内只做 Python AST、JavaScript 语法、文档编码／路径和 diff 检查。静态检查记录见 `preparation-check-01.json`，不当作行为验收。

## 决定 02 后的下一次运行

`outside-red-01` 的 P1 未通过，产品红态未运行。调查发现，错误文本中的空串是“该阶段没有 onData”的拼接结果，原始日志没有空 onData；推断原因是探针只发送 char 而缺 keyDown。依据主控决定 02，补完整按键的对照、单独的空组合输入场景与产品空事件观察合同，原三条断言保持不变。详情及 observed/inferred 区分见 [RESULTS](RESULTS.md)。

下一标签为 `outside-red-02`，当前脚本默认值也已改为该标签。四项预期产品红态才算本检查点完成；旧失败现场不动。运行：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh outside-red-02
```

## 决定 03 后的下一次运行

`outside-red-02` 的 P1 为 11/12 项通过，焦点来源检查失败，产品红态未运行。按决定 03 改为公开 parser 接管 DECSET/DECRST 1004；混合模式的其余参数保序交给 xterm，拦截逐条记录原始序列。其余 11 项保留。已知限制是 CLI 不接收窗口焦点变化，详见 RESULTS 新增节。

当前新标签／默认标签为 `outside-red-03`。运行：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh outside-red-03
```

## 首次候选绿态

`outside-red-03` 已取得 P1 通过及四项产品合同红态。首个输入候选现在沿同一条生产路径实现，下一标签为 `outside-green-01`，脚本默认执行 green 阶段。只重跑 P1 与原四项断言；不启动 Claude、Claude 夹具或真实模型。详细边界见 RESULTS 的首个输入候选一节。

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh outside-green-01
```

## 第二阶段：库客户端与回归

首个输入候选已通过。收件箱领域测试取得 5 项预定红态，再达到 11/11 绿态；没有 CLI／PTY／socket 或模型。库客户端及回归适配器已写入，实际后台运行仍待主控。

当前 `outside-sandbox.sh` 默认标签是 `outside-inbox-01`，顺序为领域测试、库客户端、原 8/9/18；不启动真实 Claude、Claude 夹具或任何模型。库客户端测试中的逻辑 handoff 是预置数据，未送达结果必须保持未送达。任何非预期失败停下。

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh outside-inbox-01
```

源快照、完整命令、数据库和 Git 读回保留；凭据文件不归档。阶段总体仍是 INCOMPLETE，不能把局部通过上调为整票通过。静态准备记录为 `preparation-check-05.json`。

## 修复 submit 的身份回归

`outside-inbox-01` 的领域和库客户端通过，但 coop 的 7 项 submit 失败，后两组未运行。
根因是产品 daemon 把管理角色构造成了虚构的原生 SubmitCaller；修复将管理 actor 与
原生 thread/turn 分开，submit 的既有身份检查及业务断言原样保留。详见 RESULTS 和
`identity-regression-fix.diff`。这不是测试夹具错误，也不是预期红态。

当前默认标签是 `outside-inbox-02`，重跑同一组检查：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh outside-inbox-02
```

## 主控 #37 后：下一运行时检查点

INCOMPLETE。outside-inbox-02 读回一致：domain 11、client 8、回归 8/9/18 PASS。追加状态层红绿与输入顺序修复；有效方向夹具重放坏版本后仍拒绝，当前 11/11 PASS。outside-sandbox.sh 已切到 outside-runtime-red-01，先归档六个超限原件，再验证真实运行时和窗口放行红态。详见 RESULTS 最后三节；未运行 Claude 或其夹具，未提交／变基。

## 主控 #41 后：窗口放行待绿态

INCOMPLETE。outside-runtime-red-01 读回确认唯一窗口放行红态；入口已沿现有窗口凭据／发送队列接通。脚本切到 outside-runtime-green-01，12 项全部须通过。静态探针误用 esbuild 的失败保留，改用实际 Vite 接口检查；详见准备检查 08/09。未启动 Claude 或其夹具，不重复 8/9/18。

## 主控 #42 后：输入失败方式红态待运行

INCOMPLETE。窗口放行真实入口绿态 12/12 已读回确认。下一脚本 outside-input-red-01 只跑输入入口 11 项，预期三项红态：组合输入占用、request_id 重用、二进制鼠标字节。未改产品来绕过先红后绿，未启动 Claude 或其夹具。详细范围及未完成项见 RESULTS；未进入最终回归／变基／独立审查。

## 主控 #45 后：三项输入修复待绿态

INCOMPLETE。outside-input-red-01 三项预期红态已读回；组合输入占用、窗口请求号去重、二进制字节原样传输已修复。状态回归 11/11、静态检查通过。脚本切到 outside-input-green-01，同一 11 项全部须通过，未运行 Claude 或其夹具；最终交付检查仍未执行。

## 主控 #46 后：冻结边界待答复

输入入口 11/11 绿态已核对。BLOCKED：本卡还有两项非 Claude 缺口，而引用的 #44 实际属于 T-077；需明确先补齐还是 INCOMPLETE 切出。已通过文件版 inbox 在本 worktree 上报 blocking issue 20261011T184051Z-worker:s13-t078-issue-001，正文留在 scope-closeout-question.md。最终验证脚本逻辑已备，未执行最终 8/9/18、Git 写操作、变基或独立审查；原失败与绿态证据全部保留。

## 主控 #49 后：范围已明确，worker 入口待红态

INCOMPLETE。不收缩原卡；静态 Claude 启动记录两项红态转绿，未启动任何 Claude 进程或夹具。worker 真实凭据客户端红态脚本已准备，14 项中预期九项 worker 合同失败、其余五项通过；产品 worker 转交代码尚未修复。下一标签 outside-worker-inbox-red-01；之后提交、变基、最终一次验证、一次独立审查。

## 主控 #55 后：入口修复与权限业务反例待运行

INCOMPLETE。已明确旧结果只有入口不可达红态，不能充当四项拒绝规则的业务红态。worker inbox_* 已接通原 Stop 文件转交，实际 caller 增加当前 attempt 校验。脚本 outside-worker-inbox-green-01 先要求 14/14，再跑四个单规则后台变异体；必须观察真实越权读取／库写入，不能只凭错误码变化。前端构建复用，未运行模型；最终回归及独立审查尚未执行。

## 主控 #63 后：待冻结提交与变基

非 Claude 实现及阶段证据齐备，worker 14/14 与四项业务反例已读回 PASS。整体 INCOMPLETE：最终变基候选和独立审查尚未完成，真实 Claude 仍待决定。outside-sandbox.sh 切为 outside-freeze-rebase-01，只做独立 add/commit 和 rebase；冲突保留现场，由 worker 解决后主控 continue，不提前重复跑最终测试。

## 主控 #64 后：纠正代提交方案

outside-freeze-rebase-01 未执行，主控否决了在他人会话里恢复 worker 身份再提交的方案。已移除环境恢复逻辑和导出包；worker 直接执行独立 git add / git commit，现有 hook 生成尾注，staged/committed 检查留证。outside-sandbox.sh 现在只做 rebase 和结果检查，标签 outside-rebase-01。最终检查与独立审查仍未运行，整体 INCOMPLETE。
