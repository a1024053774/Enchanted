# T-154-1 / a1：6 个过时测试整份标历史

状态：**PASS（本票注释、索引与离线解析范围）**。不代表历史套件在当前 main 通过，也不代替执行主控的独立审查与集成。worker `b23-t154`，分支 `exec/t154`，起点 `b058e3a7585ccc85df190e90c01b52756c9d076e`；没有修改产品、断言、地图、ticket 或 T-150～T-153 的文件。

## 目标与边界

按任务卡、T-154 与用户选 C 的裁定，只给指定 6 个文件增加一行历史注释，更新 `workbench/tests/HISTORICAL.md`。非目标：迁移或运行这些历史原生验收、补齐无人守护的检查、改变现行产品行为。验收条件是标记与证据来源齐全，原正文不变，解析与离线导入不受破坏。

**Ubiquitous language**：历史通过只属于被引用版本；“当前无人守护”沿用用户裁定，现行部分覆盖不算整份替代。**Tracer bullet**：本票不新增跨层实现。**Deep modules**：保留原导出与调用关系，没有增加产品包装或并行入口。

## 验收证据

| 条件 | 结果与证据 |
| --- | --- |
| 6 个文件头含历史范围与无人守护摘要，代码不变 | PASS；`local-check-03.json` 确认删去新增首行后，6 个文件逐字节等于起点；Python AST 不变，两个 `.mjs` 经 `node --check` 通过。6 个原文件均无 shebang，模块 docstring 与 import 保留。UTF-8 无 BOM、LF 不变。 |
| 历史版本可追溯，缺失不编造 | PASS；逐文件 revision、原证据链接和限制见 HISTORICAL.md。T-112 执行/原生为 `e161476d6`，T-122 为 `01e0effd7`，T-108 为 `5f19062f5`；质量 tracer 的完整 13 案通过可绑定 `bb6c0ba3`，较新的未提交快照 PASS 不绑定为干净 revision。`run_pane_lifecycle.py` 写“无通过证据”，保留 live-04 原始 INCOMPLETE；部分生命周期证据与离线修复不合称整份通过。 |
| HISTORICAL.md 列出 6 个缺口与 4 个迁移票 | PASS；6 个移入历史节，原 3 个历史 helper 保留；4 个进入“已迁移到现行契约（T-150～T-153）”。按本次派发，T-150、T-151 已合入；T-152、T-153 写“迁移中，以合入为准”，执行主控集成时核对。30 个索引链接的目标都存在于受控文件树。 |
| 依赖仍可解析、导入 | PASS；实际导入 15 个 Python 模块，包括 `Tracer` 的质量/坏 worker/受保护验收/副本生命周期调用者及 `test_t112_closed_fixture`；另对顶层执行参数解析的 `test_t112_counterfactuals.py` 和 `run_t082_boundary.py` 做 AST 解析。完整模块清单见 `local-check-03.json`，未执行它们的原生或受控业务流程。 |
| 地图健康 | 提交前收据见 `project-map-final-01.json`；未改地图与术语表。 |

复现本票本地检查（选新摘要路径，不覆盖已有证据）：

```sh
python3 -B evidence/2026-10-23-batch23/T-154/CHECK-LOCAL-01.py --summary /private/tmp/t154-local-fresh.json
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
git diff b058e3a7585ccc85df190e90c01b52756c9d076e -- workbench/tests
```

检查环境：Python 3.9.6、Node v26.5.0。所有检查在本 worktree 沙箱内完成，没有模型调用、后台服务、Electron、原生 CLI 或外部配置写入；不需要 RUN-OUTSIDE。

## 失败、反事实与限制

- `local-check-01.json`：INCOMPLETE，检查脚本根目录误取上一层，Git 未进入仓库；随后只修检查脚本的根目录定位。
- `local-check-02.json`：INCOMPLETE，`run_pane_lifecycle.py` 的新增注释少了“只针对”后的格式空格；修该注释后，`local-check-03.json` PASS。两份失败收据原样保留。
- 起点的 6 个文件均缺要求的历史标记，`parent_missing_markers` 已记录。这是文档标记的反事实，不称产品红态。本票不改行为或断言，没有新产品测试、产品修复或产品变异实验。
- 没有复跑已知契约过时的完整历史测试；`test_t112_closed_fixture.py`、`test_t112_counterfactuals.py` 仍会调用旧 Node producer，不能因 import/AST 通过而称它们的业务断言通过。所有现行部分覆盖与缺口按 T-149 调查记录保留。
- 本轮历史证据调查读取了 T-149、受控树中对应测试的 RESULTS、命令脚本和 JSON 收据；对 sparse checkout 外的证据用 `git show HEAD:<路径>` 读取。“最后可绑定通过版本”限于查到的可复核记录，不是对历史证据完备性的保证。
- 本候选只改注释和处置文档；没有引入异常处理、fallback、兼容路径或公共行为变更。未自称独立验收，独立只读审查与集成由执行主控完成。

交付按任务卡使用 `git add --sparse` 与普通 `git commit`，不手写 A2A 尾注，不 push；完整提交号见交付消息。
