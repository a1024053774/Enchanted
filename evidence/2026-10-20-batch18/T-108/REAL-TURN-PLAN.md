# T-108 真实回合计划：待批准，尚未运行

申请 Claude **1 个根回合**；Codex **0 个新增真实回合**，选择已记录的原生 CLI hook 原件回放。整个计划尚未执行；本次只提交候选、证据与计划。真实验证未完成前，T-108 总状态保持 INCOMPLETE。

## 预算与预期

Claude 用 T-093 正常登录生产入口：`claudeLoginSession.py → 受保护 daemon → controller_start → 交互式 PTY 中的 Claude`。模型沿用入口的 claude-haiku-5-5、low，不改模型选择或版本检查，不开 Fast。

预算为 1 个用户根输入、预计 2 条生成请求（首次 AskUserQuestion 和回答后的继续生成），F/D 生命周期 600 秒。不在失败后补发第二个根输入，不自动重跑。CLI 自身的失败重试及辅助请求逐条进入 T-093 转发计数，不能把“1 根”说成“1 次 API 请求”，也不把该入口当作硬美元限额。用户正常登录额度的实际消耗以事实记录为准。

唯一根输入：“请按本会话角色说明，用 AskUserQuestion 询问部署区域；收到答复后只确认并结束。”角色说明已由准备脚本写定：问题“选择部署区域？”，选项“东区／西区”，multiSelect=false。只在 Electron 问题表单中选“西区”并发送，不把答复作为新的根输入。

验收要求：原生 PreToolUse → 当前 launch 的问题、选项与 waiting_user_answer → DOM 作答写入原 PTY → 一条 answer 用户输入引用该问题 → 原生 PostToolUse 确认“西区” → 同一 prompt_id 的 Stop → pane_idle。再次作答必须拒绝；缺事件、失败、超时或身份不符均 INCOMPLETE，不放宽为 idle 或已完成。

## 当前前置缺口

T-093 在 claudeLaunch.ts、claudeLogin.ts 和 claudeLoginSession.py 三处固定 **2.1.302**；当前机器只安装 **2.1.304**。执行前必须提供来源可核对的 2.1.302 独立二进制，例如 `/private/tmp/t108-vendor-2.1.302/claude`，由 `--version` 实测确认。未获得该二进制前停在无模型准备之前；不伪装版本，不把 2.1.304 加白，不改全局安装。若改用 2.1.304，须另做 T-093 版本边界探针与主控裁定，不属于这份 1 根计划的隐含授权。

`prepare_t108_real.py` 是新增的未执行准备工具，仅创建隔离夹具、核对版本、初始化夹具 Git、解析官方上游地址和选择端口，不读登录凭据，不启动交互 CLI、不提交模型输入。当前只检查了 Python 3.9 语法；正常登录部分的可运行性仍待批准后的验证，不能称为已跑通。

## 批准且版本前置满足后的命令

以下命令给主控审阅，现在不要运行。先提交候选，之后只在干净的 exec/t108 候选上执行；root 已存在就换新的编号，不覆盖旧现场。初始化夹具 Git 会清除继承的 GIT_DIR／GIT_WORK_TREE，并固定 LC_ALL=C。

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t108
export LC_ALL=C
unset GIT_DIR GIT_WORK_TREE
T108_REV=$(git rev-parse HEAD)
/usr/bin/python3 -B workbench/tests/prepare_t108_real.py \
  --root /private/tmp/t108-real-01 \
  --claude /private/tmp/t108-vendor-2.1.302/claude \
  --revision "$T108_REV"
```

通过 T-093 公开入口启动，进程独立成组，stdout/stderr 只写本次 /tmp 根；不调用普通 daemon_start 替代保护入口：

```sh
/usr/bin/python3 -B - <<'PY'
import json, os, subprocess
from pathlib import Path
root=Path('/private/tmp/t108-real-01')
net=json.loads((root/'network.json').read_text())
env={k:v for k,v in os.environ.items() if not k.startswith(('A2A_','GIT_','CLAUDE_','ANTHROPIC_','CODEX_')) and k not in ('NODE_OPTIONS','ELECTRON_RUN_AS_NODE')}
env.update(LC_ALL='C',PYTHONDONTWRITEBYTECODE='1')
argv=['/usr/bin/python3','-I','-S','-B','workbench/src/claudeLoginSession.py',
      '--manifest',str(root/'manifest.json'),'--repo',str(root/'repo'),
      '--forward-port',str(net['forward_port']),'--upstream-address',net['upstream_address'],'--lifetime-seconds','600']
with (root/'bootstrap.stdout').open('xb') as out,(root/'bootstrap.stderr').open('xb') as err:
 child=subprocess.Popen(argv,cwd='/Users/luckye/Documents/Code/a2a-wt-t108',env=env,stdout=out,stderr=err,start_new_session=True)
(root/'bootstrap-process.json').write_text(json.dumps({'pid':child.pid,'argv':argv})+'\n')
print('T-093 bootstrap PID',child.pid)
PY
```

待 daemon_status 确认当前 daemon 就绪，注册隔离任务，再以同一 manifest 启动 Claude。controller_start 会做版本、隔离身份、正常登录和转发器预检；任何拒绝都停止，不输入 Enter 或改默认项：

```sh
export A2A_OPERATOR_CREDENTIAL=/private/tmp/t108-real-01/operator.json
node workbench/src/gates/cli.ts --state /private/tmp/t108-real-01/state daemon_status
node workbench/src/gates/cli.ts --state /private/tmp/t108-real-01/state card_save \
  --task T108-real --card /private/tmp/t108-real-01/card.json --expected-version 0
node workbench/src/gates/cli.ts --state /private/tmp/t108-real-01/state create \
  --task T108-real --repo /private/tmp/t108-real-01/repo --branch refs/heads/main --card-version 1 --project T108-real
node workbench/src/gates/cli.ts --state /private/tmp/t108-real-01/state controller_start \
  --task T108-real --manifest /private/tmp/t108-real-01/manifest.json
node workbench/app/build.mjs --slot t108-real-01
```

Electron 只从内置盘运行。以下 DIST 取上一条 build 的 out 字段，LAUNCH 取 manifest.launch；它们是本次运行生成的值，不是另一场的固定结果。界面可输入且绑定该 launch 后，只提交上文一个根输入：

```sh
export ELECTRON_OVERRIDE_DIST_PATH=/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist
T108_LAUNCH=$(/usr/bin/python3 -B -c 'import json;print(json.load(open("/private/tmp/t108-real-01/manifest.json"))["launch"])')
node workbench/app/start.mjs --build /private/tmp/a2a-build-t108-real-01/dist \
  --state /private/tmp/t108-real-01/state --task T108-real --launch "$T108_LAUNCH" \
  --user-data /private/tmp/t108-real-01/ui
```

不用截图。以已保存 hook、question/answer 事件、原生 session、pane_idle 与转发原件核对；关闭 UI 后走 daemon_stop，并核对正常登录隔离 HOME 已删除、CLI／daemon／F／D 均退出。若未确认退出，保留现场并单独处置，不报告 PASS。

```sh
node workbench/src/gates/cli.ts --state /private/tmp/t108-real-01/state daemon_stop
/usr/bin/python3 -I -S -B workbench/src/claudeLoginSession.py --stage facts \
  --audit "/private/tmp/t108-real-01/state/login-audits/$T108_LAUNCH"
```

T-093 的 OS profile 禁写真实 HOME，hooks 只经每会话 --settings 传入；凭据只由原入口读取到私有 HOME，不进入证据或 Git。事实检查或清理尚未成功时保留 INCOMPLETE。最终文本摘要计划路径为 `/private/tmp/t108-real-01.summary.json`；它尚未生成。

## Codex：原件回放，新增真实模型预算 0

本轮选择回放 `native-hook-samples.json` 中已保存的 Codex 0.163.0 PreToolUse／PostToolUse 原文。来源为真实已安装的交互式 CLI，连接本地假 API；**不是供应商真实模型生成的证据**。回放已通过 signal／SQLite／PTY 边界替身，覆盖 waiting_controller_answer、原始问题与选项、写回按键、answer 关联、原生确认与重复拒绝；不宣称重新运行了原生 CLI 或 Electron。原始探针另证明当前 CLI 实际发送这些 hooks。

```sh
node workbench/tests/test_t108_hook_replay.mjs \
  --samples evidence/2026-10-20-batch18/T-108/native-hook-samples.json \
  --summary /private/tmp/t108-codex-hook-replay-approval-01.json
```

已有 `/private/tmp/t108-codex-hook-replay-green-01.json` 为 PASS；同一测试以 --ignore-question 的坏实现对照，在 red-02 中准确因 running != waiting_controller_answer 失败。red-01 是夹具少 queue 字段，不作为红态。

T-095 第五个真实模型根回合原件位于 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-095/answered-20261018T165159Z-ee1a8372`，其中 request_user_input_async 的 accepted 不证明同步阻塞，不能把它包装成当前同步提问的真实模型正例。当前生产 Codex dispatch 仍强制 xhigh，与 AGENTS.md 的 high 冲突，已单独上报；本票不改该规则或绕过门禁开新 worker。

如果票中的“已记录的真实原件”要求必须来自供应商真实模型，则上述当前 hook 原件的来源不满足该更强口径，Codex 部分应保留 INCOMPLETE；不自行放宽验收，也不自动追加根回合。后续需先解决 high 启动冲突，再单独提交 1 根 Codex 真实同步提问计划。本次申请仍只有 Claude 1 根。
