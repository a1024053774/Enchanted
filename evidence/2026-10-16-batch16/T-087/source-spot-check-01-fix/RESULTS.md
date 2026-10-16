# T-087 来源抽查 01 后修订（2026-10-16）

**INCOMPLETE：三项修订已完成本地检查，待主控提交后另开来源抽查；没有自行提交。** 抽查 01 的 NO_GO 保留，不能用本作者的检查上调。

本次起点 `db71960b8f4962dcbf6bc77a8db7dc50cfbb4ef3`，依据主控 #3 的修订要求与上层 [独立抽查 01](../source-spot-check-01.md)。仍为 T-087-1 / attempt a1 / s16-t087；任务卡范围不变，只改生成脚本、重新生成图文档并新增本目录文本证据。未改 workbench、地图、角色卡、术语或旧证据，未执行 Git 写命令。

| 问题 | 修订 |
| --- | --- |
| P2-01 | 新增 Q13 `checkQualityEvidence`，主串明确为 Q5 红态→Q6 规则→Q13 质量证据核对→Q7 尾注。E65/E66/E67 分别将 Q5/Q6/Q13 的非五个已知失败码出口连到 R2；保存 unknown、task paused 并上报，不调 rejectDelivery、不增加 delivery_rejected。拒收码表区分五个已知失败码与命令不可启动/超时、质量证据不符等未知路径。 |
| P2-02 | E68 表示当前运行审查的协议解析或门禁转交失败→R2，引用 daemon 的直接调用方和 failReviewProtocol。E46 限定为有效“需修复”业务结论。拒收码表补 invalid_review_result，说明格式错误与有效业务结论的不同暂停/计数路径；另保留 cancelled 审查只记 after_termination 的条件。 |
| P3-01 | Q7 与尾注拒收表写明 model 为字面量 unknown 时不要求等于交付模型；有尾注时其余齐全、唯一、非空要求仍在，全无尾注仍是人工介入分支。 |
| 隐式边 | 数量仍为 12；I08 区分业务判断与 E68 机械协议暂停，I10 明确人工选择发生在机械暂停之后。未把 T-081/T-082 的覆盖扩大到所有新增列出的未知路径。 |

定向失败信号来自主控明确要求，而非生成脚本的当前输出。修订前运行 `check_requested_corrections.py`：exit 1，九项 NO_GO，见 `requested-corrections-before.json`；修订后同一命令 exit 0、九项 PASS，见 `requested-corrections-after.json`。它只检查指定文档内容与连接，不能判断来源是否充分支持语义，不能替代新的独立抽查。

本地结果：

- PASS：两次生成均 exit 0、stderr 为空；`generation-repeat.diff` 0 字节，diff exit 0，生成结果与交付文档一致。命令和 /tmp 产物路径在 `generation-repeat.json`。
- PASS：引用存在性与图表 ID 一致性，35 个点、68 条连接、221 行来源索引、546 次引用，见 `references.json`。没有宣称完成来源语义抽查。
- PASS：`git diff --check`；交付文本按 UTF-8、无 BOM、LF 回读。
- INCOMPLETE：`project_map.py status` 为 0 problems / 1 stale（findings/README.md，修改被覆盖文档后索引未改），见 `project-map-status.txt`；本卡未扩大到已有索引的修改，留主控提交时处理。
- 未运行：产品/服务/模型、图形渲染、T-081/T-082 重验。没有改变产品行为。

仓库根目录复现：

```sh
python3 -B evidence/2026-10-16-batch16/T-087/source-spot-check-01-fix/check_requested_corrections.py
python3 -B findings/generate_t087_graph.py > /tmp/t087-audit01-first.md
python3 -B findings/generate_t087_graph.py > /tmp/t087-audit01-second.md
diff -u /tmp/t087-audit01-first.md /tmp/t087-audit01-second.md
diff -u findings/ticket-gates-graph-2026-10-16.zh-CN.md /tmp/t087-audit01-first.md
python3 -B findings/generate_t087_graph.py --check findings/ticket-gates-graph-2026-10-16.zh-CN.md
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
git diff --check
```

此前证据及抽查报告均未覆盖。本次使用 document-writing、project-map 和 evidence-first-testing；新的独立审查由主控另行安排。
