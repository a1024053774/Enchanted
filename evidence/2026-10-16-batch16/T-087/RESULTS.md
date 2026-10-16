# T-087-1 交付证据（2026-10-16）

**INCOMPLETE：待主控确认 findings 索引的最小修改范围、在可写 Git 元数据的环境提交，并安排非作图会话做来源语义抽查。**

绑定：T-087 / attempt a1 / worker s16-t087（wF:p4H）/ session `e80ff7ba-11a8-449b-a70e-930f2c6db624` / launch `launch-81bf2744649b42f2bc780ace08c32634`；ticket ready_rev 1，起点与读取来源最近提交均为 `fc362ab44054bc82afe8a2f56eef17972ece7bc5`。任务卡指定 codex-cli 0.162.1、gpt-6.1-sol、xhigh、service_tier default；这里不把请求配置写成供应商实际 tier 的证明。本次只读分析仓库，不启动服务，不调用模型 API，不改全局配置。

产物：

- [中文图文报告](../../../findings/ticket-gates-graph-2026-10-16.zh-CN.md)：34 个门禁检查/agent 会话/人工决定点、63 条连接，三个视图共用 ID；12 条隐式边单列后果及 T-081/T-082 覆盖和未覆盖。来源为 ticket 字段、收件箱类型、任务卡、真实门禁顺序/拒收码/恢复路径与持久化边界。
- [生成与引用检查脚本](../../../findings/generate_t087_graph.py)：Python 标准库；只读来源和 Git 版本信息，输出文本，不执行图中的流程。

本地检查：

| 检查 | 结果 | 证据与边界 |
| --- | --- | --- |
| 同一来源连续生成两次 | PASS | `generation-repeat.diff` 为空（0 字节）；直接比较文本，没有计算哈希。 |
| 每个点/连接的来源存在性、图表 ID 一致性 | PASS | `references-final.json`：34 个点、63 条连接、207 条来源行、477 处引用；检查文件/行号/摘录，不判断语义支持。 |
| 检查器拒绝损坏文档 | PASS | `checker-negative-probes.json`：无效行号、点缺引用、边缺引用、图中删边四案，预期 exit 1，实际均 exit 1；损坏文档留在 JSON 所列 /tmp 目录。 |
| project_map.py status | INCOMPLETE | `project-map-before-commit.txt`、`project-map-final.txt`：0 problems / 1 stale，新增报告需同步 findings/README.md。 |
| 来源语义抽查 | INCOMPLETE | 依任务卡由另一不写图的会话完成；本作者没有宣布完成。 |
| 暂存 / 提交 | INCOMPLETE | `git-add-refused.txt`：共享 Git 元数据的 index.lock 写入被沙箱拒绝；没有暂存或提交。按任务卡要求不申请升级，交 `finish-from-controller.sh`。 |
| 产品/模型端到端运行、T-081/T-082 重跑、图形渲染 | 未运行 | 本任务是静态调研；图为 Mermaid 文本。引用两票的日期记录，不把旧证据移作本票的新通过结论。 |

仓库根目录复现主要检查：

```sh
python3 findings/generate_t087_graph.py > /tmp/t087-first.md
python3 findings/generate_t087_graph.py > /tmp/t087-second.md
diff -u /tmp/t087-first.md /tmp/t087-second.md
diff -u findings/ticket-gates-graph-2026-10-16.zh-CN.md /tmp/t087-first.md
python3 findings/generate_t087_graph.py --check findings/ticket-gates-graph-2026-10-16.zh-CN.md
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
git diff --check
```

已按角色卡上报非 blocking 问题 `20261016T083546Z-worker:s16-t087-issue-001`；正文 `issue-readme-stale.md`，发送结果 `issue-send.txt`。最小建议补丁 `readme-index-proposed.patch` 已用 `git apply --check` 核对可应用；尚未修改 findings/README.md。它只增加一条新报告索引，不改地图、术语或产品。

Git 元数据限制另按角色卡上报为非 blocking 问题 `20261016T083842Z-worker:s16-t087-issue-001`（`git-issue-send.txt`）。`finish-from-controller.sh` 是沙箱外 Git 操作的交接脚本，worker 未运行。它先要求 status 通过并复查生成物，再只暂存本次交付，不提交、不集成；主控核对后按脚本末尾所列命令另行提交。角色卡要求追加的两条 issue 是仅有的位于 findings/、scripts/、evidence/ 之外的新文件，没有修改任何角色卡或他人的 ticket。

开发失败现场保留：`generation-01.stderr.txt`、`generation-02.stderr.txt` 是收件箱提示语锚点重复导致的拒绝，第二次收窄仍重复；改用该分支的唯一条件锚点后生成成功。首次检查 draft-03 输出“来源索引格式不完整”，原因是检查器的来源 ID 字符类漏了下划线；该次命令与原文保留于本 session 工具记录，原文档 `/tmp/t087-draft-03.md` 未覆盖，之后才修正检查器。03/04 的空 stderr 与 draft-04 检查结果也保留。本地修正不是产品行为的红/绿验收。

技能：本次读取本机 `project-map`、`document-writing` 的 SKILL.md 及后者 polishing/encoding 参考；未假定其目录具备可用版本号。来源语义独立抽查交给主控安排，作者不以自己的检查背书。
