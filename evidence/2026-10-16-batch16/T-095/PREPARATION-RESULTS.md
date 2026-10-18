# T-095-1 准备阶段交付

**INCOMPLETE。** 主控 #87 已确认方向与预算，允许先实现不依赖真实面板的部分。本次没有启动额外 Codex，也没有复制登录凭据。真实折叠/展开面板的识别尚未接入，不能把本阶段结果当作 T-095 完整验收。

## 已实现

- `scripts/agent-status --root <保存启动记录的 checkout> --launch <launch_id>`：只调用 Herdr `agent get/read`，输出单份 JSON。身份或读数不可核对时，输出 `unknown` / “未知”，退出码 2；已核对的普通活动输出 `working` / “工作中”，退出码 0。
- 复用启动记录校验，核对 worker、pane、terminal、revision、cwd 和原生身份；读取前后检查 live 状态代次，并重读启动记录。已有原生身份绑定必须相等；未绑定时明确标注身份来源，不回写记录。新启动占用同 pane 时拒绝旧 launch。
- 普通活动须同时有计时活动行、输入框、模型栏及快捷键栏，并由 visible / detection 两份当前读数共同支持。只有 Herdr working 值、正文引用、草稿或陌生尾部结构均不足以判 working。每次重新读取，没有缓存的等待状态。
- `dispatch`、工作台、门禁、项目地图、AGENTS.md 和全局配置均未修改。

`controlled-panel-probe.py` 已在文件头和运行时明确手动操作顺序：提交后切到自建 pane，按需 **Shift+→ 折叠**，回脚本终端输入 `COLLAPSED`；看到 `CAPTURED collapsed` 后，再到自建 pane 按 **Shift+← 展开**，回脚本输入 `EXPANDED`；看到 `CAPTURED expanded` 后，手动取消待答问题，再输入 `CANCELLED`。脚本不代按方向键、不自动回答，也不把折叠当作取消。

## 检查与证据

| 检查 | 本阶段结果 | 原件或复现命令 |
| --- | --- | --- |
| 命令入口合同 | PASS，31 项；Herdr 是显式替身，不是面板验收 | `PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_agent_status.py --report <新的报告路径>`；最终报告 `synthetic-contract-after-05.json` |
| 真实普通活动入口 | PASS，仅当前 worker 的普通活动，不新增模型回合 | `scripts/agent-status --root /Users/luckye/Documents/Code/a2a --launch launch-4b1abba18e87460da9cbacec04905c78`；`preparation-live-status-02.json`，得到 working / s16-t095 / wF:p68 |
| 忽略画面的坏实现 | 被拒绝，8 项失败；证明原始 working 透传不足 | `synthetic-mutant-ignore-screen-01.json`，冻结副本位置见 `preparation-mutants.json` |
| 永不报告 working 的坏实现 | 被拒绝，5 项普通活动检查失败 | `synthetic-mutant-never-working-01.json` |
| 空列表原生身份被当成未绑定的坏实现 | 被拒绝；当前实现输出 unknown | `synthetic-native-shape-mutant-02.json`；最终合同中的 `empty-initial-native-is-not-unbound` |
| 探针准备 | PASS，仅语法、默认零回合预览和单提示/无按键调用点检查；实际执行未运行 | `python3 evidence/2026-10-16-batch16/T-095/controlled-panel-probe.py`；`probe-plan-03.json` |
| 项目地图 | PASS，0 problems、0 stale living docs | `preparation-map-status.txt` |

所有初始结果都保留。`synthetic-native-shape-before-01.json` 的首次反事实检查与文件更新重叠，实际读到更新版本，**不能作为修改前证据**；冻结副本的 `synthetic-native-shape-mutant-02.json` 才是有效反事实。`synthetic-contract-after-03.json` 有两项执行器总期限超时，`after-04.json` 有一次假 Herdr 启动超时；它们不是面板红态。执行器总期限由 10 秒改为 20 秒，覆盖命令最多四次、每次 3 秒的读取预算及启动开销；状态期望值和产品读取期限未改。假 Herdr 固定使用测试执行器的 Python，避免再次经 PATH 选择平台启动器。超时没有进入假 Herdr 首条日志，后续两种解释器的单次小探针均很快；根因没有被完全确定，**不宣称消除了全部调度延迟**，见 `fake-interpreter-investigation.json`。

失败夹具及坏副本留在各 JSON 的 `fixture` / `mutant_directory` 所指 `/tmp` 目录，未删除、未覆盖。它们尚未归档到外置盘；本 worker 没有运行沙箱外归档命令。本阶段不提交完整交付、不报 `T-095 READY <sha>`；独立审查留给带真实面板证据的完整候选。

## 待真实原件

等主控确认有 Codex 名额后，在沙箱外运行：

```sh
python3 evidence/2026-10-16-batch16/T-095/controlled-panel-probe.py --approve-one-root-turn --phase red
```

仍为单次 1 个根回合、红绿合计最多 2 个、不自动答题。需要两种形态的原始 visible / ANSI / detection 及同期身份、状态；脚本将完整采集放在外置盘 `a2a-evidence/2026-10-16-batch16/T-095/<run_id>/`。worker 收到原件后实现 `waiting_controller_answer` / “等待主控回答”，再做真实绿态、退出反例及完整审查。合成的 unknown → idle 重读证明不能替代真实面板关闭/回答后的回落证据。
