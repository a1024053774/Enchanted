# 工具许可 Enter 的提交记账缺口

非 blocking。当前只读发现，实际新 CLI 未启动，不能称已实测。

`workbench/src/panes.ts:493` 起 userInput 对任意非 paste 的 CR/LF 直接替换 pane.active 并追加 source=user 的 turn_submit_intent。一次真实 PermissionRequest 的窗口 Enter 实际是批准工具，并不会产生新的 UserPromptSubmit，却也走此逻辑；因此预计新增假 intent、丢失原注册 active 的关联。这会影响提交额度和 Stop／原登记结算，虽然目前控制字节的 user_inputs 分类本身已是 action。

红态材料不修改产品；严格分记实际 UPS/API、审批键的真实 action/write receipt、多余 intent 和原登记结算 INCOMPLETE。它只证明首次 controller inbox 客户端拒绝，不宣称完整关联或转交通过。建议先真实运行捕获这条因果，再在已分配的 panes/caller 范围将工具许可控制动作保留原注册关系；不得将内部 intent 当实际原生新根，或为绿态删证据。若主控认为应先使用精确每会话 allow 参数隔离此问题，可在实际 launch 前裁定新配置；不自行改启动许可。
