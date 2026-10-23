STATUS: INCOMPLETE
TARGET: 7c58ba11c5dad6c2fef79e0b19ed8da0abd6145e 加冻结的 T-127 测试差异、reviewer-origin 复放及 RUN-OUTSIDE-06.sh
EVIDENCE:
- 所有原有 check(...) 断言的 AST 相同；240 秒审查超时保持不变。
- RUN06 恰好包含 T-127 绿态与指定四场。
- 独立复放了保存的实际 missing/trusted 启动输入：两者均被拒；仅恢复 trust 后，两者均通过。
- RUN06 分类要求指定的原生目录拒绝，或审查已 passed 后原有具名行为断言失败。旧超时仍为 INCOMPLETE。
- Python 解析与 zsh 语法检查通过。
FINDINGS:
- 在有界审查范围内没有发现可达的验收违规。
COUNTEREXAMPLE:
- 对两份实际 trust 输入另加无关 sandbox 缺陷，仅恢复 trust 后仍被拒；helper 返回 INCOMPLETE，没有把全部拒绝错误归因于 trust。
- 当前变异删除 native-folder guard 后是否被原行为断言抓住，尚未证明。
LIMITATIONS:
- 未执行原生 RUN06。现有目录来源证据只证明 envelope 逻辑，不证明 reviewer 提交、原生 cwd 拒绝或 guard 变异被抓住。
- 旧原生结果不能证明改过的变异通过验收。当前验收仍为 INCOMPLETE。
RULE:
- N/A；没有确认新的重复问题。
