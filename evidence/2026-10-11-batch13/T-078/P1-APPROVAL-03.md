# T-078-2 P1 材料 03：角色卡参数最小修正

**INCOMPLETE，等待审批；本轮未启动 Claude、API、socket 或模型。** 材料 02 的 launch 失败原件和 cleanup PASS 保留。主控 #88 确认其假 API 曾绑定端口 61040，失败发生于 help 预检，交互 CLI 没有启动、模型回合为 0。

## 核对结论

已读回 2.1.296 的实际 `--help` 输出 `p1-materials-02/launch/command-output/00003.stdout.bin`：独立条目有 `--append-system-prompt <prompt>`；bare 说明另有 `--append-system-prompt[-file]`，但没有文件参数的独立条目。

[官方 CLI reference](https://code.claude.com/docs/en/cli-reference#system-prompt-flags) 仍列出文本和文件两种追加参数，并明确 help 不列全部参数；文档还描述 v2.1.283 起可以同时传两种形式。因此官方资料支持“文件形式仍保留、未完整列入帮助”，不能据缺项认定已删除或改名。本轮没有运行固定二进制的额外参数解析探针，也不把文档当作本次启动成功的证明。原预检把“帮助中没有完整字符串”判成不可用，结论过强。

## 唯一启动参数变化

```diff
- --append-system-prompt-file /本轮/role.md
+ --append-system-prompt "<role.md 的完整 UTF-8 文本，含末尾换行>"
```

构造器严格解码并读取角色卡一次，将同一文本用于 argv 和启动记录 role_text；保留 role_card 路径与版本。既有逐参数 shell 引用继续使用，引号、换行、中文、美元符号和反引号都不做 shell 展开。help 预检只把对应必需选项改为明确列出的文本形式，其余检查不变。

不换 Claude 2.1.296、模型、effort、permission-mode、tools、MCP、hooks、settings、认证或回合预算。新实例必须重新签发身份和路径，这些属于材料更新，不是额外 CLI 选项改动。`p1-materials-03/argv-change.json` 已对 02/03 正规化实例身份后逐项核对：只有上述 flag/value 改动，其他 argv、env、hooks 一致。

## 新材料与审批

新根 `/private/tmp/t078-2-p1-03-bvm3ke93`，launch `e9d4ca48-9139-4f1b-aabd-c371fdb11755`，native session `9f4a4b2a-b067-4945-bff5-60172fefd5b6`。完整 argv/env/hooks 和角色文本见 [approval.json](p1-materials-03/approval.json)；源码快照、差异及控制端参数都在同目录。旧 02 根已清理，不复用。

仍只用隔离 HOME/CLAUDE_CONFIG_DIR 与公开假 key。API 启动时绑定 loopback 端口 0，核对 PID/session 并保存实际 runtime-manifest 后才执行两个 CLI preflight 和一个交互启动。没有 --bare。三项真实 CLI 调用仍逐次纳入本次 P1 审批；当前尚未执行。

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-launch-03
```

launch 不输入文字，返回 INCOMPLETE／等待初始 readiness。主控观察实际隔离终端；只有确认可接新输入才在新根写 initial-ready.json（匹配 launch/session、confirmed_by=executor、readiness=confirmed、basis）。登录、onboarding、信任或权限等待必须停下，不把任务或 Enter 当作确认。

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-continue-03
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-cleanup-03
```

continue 使用同一 CLI，仅一次根输入和一次 Messages；保留 API 屏障、实际 UserPromptSubmit／Stop、busy→idle 和原始 nonce 回复检查。真实模型预算 0。期限及停止条件沿用 02：preflight 各 15 秒、观察各 30 秒、API 屏障 60 秒，异常即停、无重试。清理只停止本次身份核对通过的后台／PTY/API，归档并清理本次根；身份或退出未知则保留现场。不触碰正常登录或用户目录。

## 证据和复现

`p1-role-text-red-03` 捕获旧 argv 没有文本选项的构造合同失败；green-03 验证文本、换行和特殊字符准确进入单个 argv，CLI 未运行。新 help 必需选项已用实际 2.1.296 输出离线读回，全数存在。API 兼容性及隐藏文件参数的实际解析没有在此补称为通过。

```sh
node workbench/tests/test_t078_role_prompt.ts evidence/2026-10-11-batch13/T-078/p1-materials-02/launch/command-output/00003.stdout.bin <新输出目录>
python3 -B workbench/tests/regenerate_t078_p1.py --label p1-materials-04
```

重新生成必须新 label、新实例和重新审批；不能改写 03 或旧失败结果。P2～P4 不在本次范围，未合流、未重跑大套件。
