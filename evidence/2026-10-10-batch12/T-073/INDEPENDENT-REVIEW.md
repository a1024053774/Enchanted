STATUS: FAIL
TARGET: 76e71f86f895e64f3eb5b7abedcfc08c7a62c98f
EVIDENCE:
- PASS：模板的 13 个字段与冻结 spec 第 2 节一致；AGENTS.md 和三张角色卡的链接均指向该模板，规则改动仅为链接。
- PASS：green02 原始 Git 输出中的普通、--no-verify 提交各有 9 项尾注；独立解析后，所有值与启动记录、原生会话环境一致。启动记录绑定本候选 SHA，Herdr 返回的实际 argv 与记录一致。
- PASS：red02 的真实旧入口提交没有尾注；green02 普通终端提交成功且没有尾注；原 prepare-commit-msg 留下两次调用痕迹。
- PASS：local03 的真实 Git 验证了原钩子失败阻止提交、缺环境变量/身份不符/损坏记录拒收，以及 amend、rebase、merge。Herdr 为明确标注的替身，不能据此证明真实 Herdr 边界。
- PASS：score01 实际命令拒收缺备注的评分，成功记录读回与独立事实 JSON 一致；放弃记录仅有结果和理由。local03 覆盖升级、用户另存、重复拒收、并发追加与损坏保护。
- 结构检查：异常边界传播失败并保留现场；没有重试、成功兜底或双写路径。全部 Git 钩子转发共用一个实现，符合 hooksPath 会替换整套原钩子的实际边界。
FINDINGS:
- [P2] scripts/git-hooks/hook.py:42 — Git 的 trailer.ifexists=replace 只替换最后一个同名尾注。只读 stdin 探针输入两条旧 A2A-Task 后，仍保留第一条旧值；按候选命令补齐九项后产生 10 行，任务身份同时包含旧值与当前值。预先含重复尾注的提交消息或合并后的消息可达此路径，违反尾注数量和值一致的完成条件。最小改正：清除受管尾注中的重复旧项，再写入唯一一组当前值，保留其他正文与项目尾注。
- [P2] scripts/score:48 — rejections 只检查“非空对象”，没有核对各项门禁检查是否齐全。只读执行冻结 validate_facts，传入 rejections={"not_a_gate_check":0} 被接受，实际七项检查的打回次数全部缺失；完整评分参数随后可将该记录追加为“通过”。最小改正：按既定门禁检查项验证打回次数字段完整性，缺项或未知项拒收。
COUNTEREXAMPLE:
- mutant-missing-effort03：提交成功但只有 8 项尾注，业务断言失败；能拒绝缺 A2A-Effort 的已知坏实现。
- red-pane-run-parent01：旧 JSON 响应假设导致启动失败；它证明响应处理缺陷，不能单独作为尾注业务验收。
- 新只读反例：重复 A2A-Task 输入留下旧值；任意非空 rejections 对象通过校验。现有 suite 未覆盖这两类输入。
LIMITATIONS:
- 未执行会写夹具、记录或操作真实 Herdr 的重放；仅核对冻结源码、许可范围内原始输出及只读探针。
- project_map.py status 的原始结果不在 review-manifest 清单中，本次未复核“0 problems”。
- 能力范围：编排状态、身份范围、CLI 交互、Git/JSONL 文件及隔离写入适用；检索记忆、流式输出和部署运维为 N/A。本结论不外推到生产可靠性或实际供应商 Fast tier。
RULE:
- 无可确认的项目既往同类失败记录，不新增治理规则。两项缺陷均可由真实 Git 重复尾注用例、公开 score 入口缺检查项用例机械检出。
