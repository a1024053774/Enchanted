# 09A-3R2：预批模拟用户动作的失败方式

2026-10-14，主控 #150。目标是替换无法执行的人工窗口步骤，以 executor 逐项预批的 test-simulated-user 执行清空与声明。后台、输入记录语义、Stop、拦截与 API exact oracle 不改；不启动实际夹具，不依赖用户在场，不执行 slot 删除。Tracer bullet 是实际窗口按键 → 生产输入通路 → 控制字节写入收据 → PTY／窗口空框观察 → 生产声明按钮 → 原提交拦截／API oracle。

按键依据：2026-10-14 阅读 [官方 interactive mode](https://code.claude.com/docs/en/interactive-mode) General controls 的 Ctrl+C：无操作运行时第一下清空 prompt，第二下退出；文中提到恢复已清草稿需 v2.1.288+，本夹具固定 2.1.296。另见 [官方 cheatsheet](https://support.claude.com/en/articles/14553413-claude-code-cheatsheet) 的 Ctrl+C。该依据支持选择一次 Ctrl+C，不冒称已在新实例实测。Ctrl+U 是到行首删除，不能凭一键假设本例两行已清空。

计划门槛 PASS：按键有官方依据，执行与反证都可观测；实际新版行为仍 UNKNOWN，启动后以快照／原字节证伪。若其不清空，不尝试其他键或第二次 Ctrl+C，保留 INCOMPLETE。旧 09A-2 的真实窗口快照展示独立上下横线包围的 `❯` 编辑区及两行恢复文本；新包只接受这个可辨认编辑区，不把 transcript 中 nonce 消失当空框。

失败方式与停止条件：

1. actions 只有总批准、缺任一步批准／引用／依据，或 launch/session/scenario/source 不匹配：在任何窗口动作前拒绝。
2. Ctrl+C 仍在生成中、窗格错绑、active 未退休、窗口不可输入，或恢复编辑区没有第一 nonce：不发送清空／声明。
3. Ctrl+C 未经同窗口通路、被记为 message、缺准入／intent／written 或顺序不一致：不点击声明。命令只表示 attempted，不替代收据。
4. 一次 Ctrl+C 不清空、产生退出／菜单／未知框、快照只有 transcript、空白画面或占位提示：INCOMPLETE，不重复键、不采用备选键。
5. 截图／可访问文本未解析到清空后的 PTY offset、输入区仍有第二行／残字：不声明。保存窗口截图／快照和相同 highwater 的 PTY 原字节前缀。
6. 清空后有额外输入、输入代次改变或声明不引用当前 Esc：拒绝；生产旧声明不得放行。反例保留草稿，不得调用清空键。
7. 反例故意不真实的声明触发实际拼接，但 hook 不 block、不是 exit 0 或 API2 出现：INCOMPLETE，保留诊断／正文，不裁剪／重送。
8. 自动化证据被写成真实用户亲手操作：不接受。驱动日志和结果明确写 test-simulated-user、executor 批准及逐动作引用；生产 user_inputs 仍按真实窗口输入路径记录，靠同 request/sequence/window 关联自动化来源。

当前只做隔离契约检查：实际 runner／Electron driver 分支配合 synthetic client／收据，证明拒绝条件与动作顺序，不证明真实 Ctrl+C 或原生窗口效果。真实 CLI／PTY 证明留在新两套 launch 后，不冒称本地契约绿态是实际窗口验收。独立 reviewer 未运行，整票 INCOMPLETE。
