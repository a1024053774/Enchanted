状态：INCOMPLETE（未跑真实回归）。T-141-1 / a1，worker b23-t141。

受保护的 test_t140_extra_dirs_e2e.py 在隔离 Codex home 的 config.toml 里只配置 provider，没有可信夹具根；旧启动器用 projects=untrusted 绕到 Open restricted。T-141 按用户要求移除此覆盖后，同一新 HOME 将走 unset 的 Trust and continue。沙箱外三类探针已证明 unset 会保存信任；按主控答复，候选不选择它并记录 codex_folder_trust_requested。

因此 T-140 的原始回归夹具需要由验收文件所有者决定如何明确配置已核对的夹具根信任。worker 不修改 oracle_paths，也不使用运行时 monkeypatch 或自动代按 Trust and continue 让回归表面变绿。RUN-OUTSIDE-01 保留 as-is T-140，预计这项可能在 Codex 启动处 INCOMPLETE；实际结果以沙箱外摘要为准。

同样，产品 reviewer 在新的一次性副本中若没有用户已配置的信任，也会按 unset 暂停；不会为通过审查自动写用户配置。新 T-141 e2e 自己的隔离 HOME 明确只信任已创建、已核对的整个夹具根，覆盖 worker 与 review-copy。
建议：主控确认生成的测试 HOME 可加入已核对夹具根的 trusted 项后，由 oracle 所有者更新夹具，再复跑 T-140。产品首次信任仍由用户自己处理。
