# P1 材料 08：一次目录信任与一个真实 hook 回合

2026-10-14，依据主控 #97～99、[用户答复](20261014T011751Z-ideation-answer-001.md) 与材料中的 [主控决定](p1-materials-08/controller-decision-04-update-98.md)。**静态准备 PASS；实际信任、主回合请求、hooks 和完成仍 INCOMPLETE／待逐次审批。** 本轮未启动 Claude、API、PTY，未执行任何信任按键。

## 范围和代码绑定

按 #99，08 只做一回合：新隔离 repo → 启动只读屏 → 单独批准 Digit1 信任 → 单独批准一次 nonce 注入 → 实际 UserPromptSubmit／Stop、busy、完成与假 API 主请求 → cleanup。Esc、第二次送达、紧急停止放到材料 09，等实际 hook payload 后再批；它们仍是 T-078-2 的验收内容。

旧改动已按逻辑提交：`8166e391c677179d483d886ad7a1d4279e0bc564` 为产品骨架，`b0bd9dbefb6388d4957a4a330ee579c27649e0cd` 为证据与授权，`8df2932d8d25e23e5f75154b14e5af67ea115d8d` 为后续转交副本；该停点工作树干净。08 的代码提交为 `721755d6ebde12f61277146b560c9c63d4a58446`，启动记录绑定它及 [源码快照](p1-materials-08/sources.tar.gz)。最终材料另行提交，保持工作树干净供主控变基。若变基改变快照覆盖的源码，必须重新生成、静态核对并审批绑定，当前 runner 会拒绝源码不一致；不把旧静态 PASS 当作变基后的通过。

新实例 `/private/tmp/t078-2-p1-08-47b72bcd`；launch `8215dcaf-7d3a-423f-ab3c-59f30c1acecf`，session `dfe70018-720e-4065-b195-d941a1c5c67d`，thread `b0acb22d-82f2-4b14-977d-108a62037474`。repo 只预置 value.txt；Git 元数据由 launch 在该目录初始化。HOME／CLAUDE_CONFIG_DIR／state／tmp／shell／requests／hooks／控制端 HOME 全在本实例内，没有 CLI 内部状态预置，不碰用户 ~/.claude。

## 参数、环境与留证

完整准确 argv、shell argv、白名单 env、角色文本、hooks 和 --version／--help 预检见 [approval.json](p1-materials-08/approval.json)；控制端／API argv/env 与预算见 [control-plane.json](p1-materials-08/control-plane.json)。固定 Claude Code 2.1.296，Haiku 5.5／low，manual，Bash/Read，空 MCP，三个 hook timeout 仍为 3 秒。

仅在假服务 profile 移除 IS_DEMO，新增 [文档化的 CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1](https://code.claude.com/docs/en/env-vars)，跳过标题侧模型请求；它也关闭终端标题和状态报告，本探针用 hooks 证明状态。保留公开 `ANTHROPIC_AUTH_TOKEN=a2a-fixture-key-not-a-secret`、theme=dark，不设 API_KEY 或 apiKeyHelper。`--settings` 仍仅 hooks；不用 --bare、-p、SDK 或内部信任字段。

新增 [文档化的 --debug-file](https://code.claude.com/docs/en/hooks#debug-hooks)，指向本实例 claude-debug.log。实际 cli.ts signal 入口在 JSON 解析及后台调用前保存原始 stdin；stdout／stderr 原字节、退出码、PID、时间与耗时分别保存在 hooks/<随机记录>/。finished.json 原子发布，runner 等真实 UserPromptSubmit／Stop 的 exit 0 留证，不只等后台 idle。若 CLI 在 3 秒杀掉 hook，结束文件可能不存在，必须结合原生 debug 报告缺失／超时，不能补造 exit 0。不记录环境或私有 capability，不改 payload、身份检查或 timeout，不增加重试。

API 仍只绑定 127.0.0.1，端口启动时分配并写 runtime manifest 后才启动 CLI；仅接受公开 Bearer，主 Messages 预算 1，真实模型预算 0。count_tokens 是固定夹具响应，不转发任何服务。不存在真实登录或 Codex 回合。

## 五个独立阶段

1. **launch**：仅执行预检并启动隔离 API／后台／CLI，保存原文，返回 INCOMPLETE。任何主题、认证、信任或其他 UI 提示都停下，由主控读回，不能把后续 nonce 当作回答。

   ```sh
   bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-launch-08
   ```

2. **screen**：主控在实际信任界面出现后另行执行只读 screen，保存 screen/screen.bin 与时间、目录、launch/session。它不推断界面含义或批准。

   ```sh
   bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-screen-08
   ```

3. **trust**：主控审核原文后，另存 [trust-approval-template.json](p1-materials-08/trust-approval-template.json) 为 trust-approval.json，填 approved_by=executor、approval_ref、实际 basis。其 launch/session、directory、screen_file、key 必须与本实例一致；模板不是批准。然后单独批准下列明确按键命令：

   ```sh
   bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-trust-08 Digit1
   ```

   只写 ASCII `1`，不补 Enter、不选择默认。后台核对 operator 凭据、实际 CLI、启动期状态、审核过的完整屏幕原字节及本 launch 尚未发送过信任键；先登记意图再写 PTY。记录实际来源 executor、时间、目录、按键与原文，不把委托操作记为用户亲手输入。原文变化、第二次按键、非 Digit1 或非 operator 都拒绝；没有自动重试。写键后仍返回 INCOMPLETE，主控须读回 trust/screen.bin 和持续的 state/traces/<launch>/pty.raw。若实际界面需要其他键，或尚未看到信任完成，停下报告；不能运行第二次 trust 或自动 Enter。

4. **continue**：主控确认实际进入提示符后，将 [readiness-template.json](p1-materials-08/readiness-template.json) 另存为 readiness.json，填写本次 confirmed_by=executor、readiness=confirmed、basis，再单独批准。旧实例的确认不能复用。

   ```sh
   bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-continue-08
   ```

   核对原 CLI PID／启动时间／命令，放行初始 unknown，按原登记的 bracketed paste＋单独回车注入一次 nonce。要求 busy／active 与真实 turn_start_signal；假 API 收到该主回合请求，才释放唯一脚本化 SSE；要求 ACK、Stop、idle 和真实 exit 0 hook 原件。任一缺失、协议／预算／身份错误都停，不放宽断言、不重试、不发新输入。成功仅证明固定 CLI 的这一个假服务回合。

5. **cleanup**：读回后单独审批。沿用已真实复验的退出核对，只有本 manifest 的 CLI 确认退出才 PASS、归档和删根；仍活着／身份未知即 BLOCKED，保留现场。只停止自己的服务，无额外 CLI kill。

   ```sh
   bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-cleanup-08
   ```

单个证据文件超过 5 MiB 即停并报告，等待主控安排外置归档；不自动把压缩当豁免。

## 静态证据和限制

[profile 红](profile-red-08/results.json)／[绿](profile-final-08/results.json) 验证无 demo、禁标题、debug／trace、Bearer 与 timeout；[hook 留证红](hook-trace-red-08/results.json)／[绿](hook-trace-final-08/results.json) 经真实 gate CLI 的坏 JSON 输入在 transport 前退出 2，证明原字节与退出码保留；没有 socket、vendor CLI 或模型。

[trust 红](trust-red-08/results.json) 只证明入口缺失，拒绝规则在起点不可达，不称为业务红态。[trust 绿](trust-final-08/results.json) 用域夹具核对一次写键、来源、重复／Enter／旧屏幕拒绝；[重放变异反例](trust-replay-mutant-final-08/counterexample.json) 去掉一次性规则后实际执行了第二次域夹具写入，未操作真实 UI。两次探针夹具修正和工具补丁拒绝原样留档，没有改业务预期。真正入口、实际菜单与凭据隔离由上述批准后阶段验证，仍未运行。

[静态检查](p1-preparation-check-08.json) 覆盖仅 value.txt、无内部状态、参数／环境、48 个源码原件、语法、尺寸与项目 status。旧 8/9/18 与独立审查只绑定 T-078-1，不替 08 背书；最终验收和新候选审查待完整链路后进行。

重放静态产物用新输出／新编号：

```sh
node workbench/tests/test_t078_profile08.ts /绝对路径/新的profile目录
python3 -B workbench/tests/test_t078_hook_trace.py --output /绝对路径/新的trace目录
node workbench/tests/test_t078_trust.ts /绝对路径/新的trust目录
python3 -B workbench/tests/regenerate_t078_p1.py --label p1-materials-<新编号> --extra-source evidence/2026-10-11-batch13/T-078/p1-check-materials-08.py
python3 -B evidence/2026-10-11-batch13/T-078/p1-check-materials-08.py --output /绝对路径/新的静态报告.json
```

本次仅交 launch 审批。真登录阶段不启动、不读凭据、不改其他设置；以后目录信任也仍按独立审批留证。T-078 整票保持 INCOMPLETE、open，待主控关闭。
