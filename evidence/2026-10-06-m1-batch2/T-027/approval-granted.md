# T-027 hook 许可：主控批准（2026-10-06）

依据：用户在主控会话中转达请求并要求授权；主控核对 muster-agent-state.sh（仅在 MUSTER_ENV=1 时运行，只连接 MUSTER_SOCKET_PATH，上报 pane.report_agent_session / pane.report_agent）与隔离 home 位置（/tmp/t027-*）。

批准范围：
1. 仅在下一次新建的隔离 CODEX_HOME（/tmp 下、名称含 t027）中，信任 Muster 自己的 4 个上报 hook。
2. 该隔离 home 的 hooks.json 只放这 4 个 Muster hook；不复制用户已有条目（vibe-island、superset、herdr 等），也不批准它们。
3. 不写、不改用户的 ~/.codex（hooks.json、config.toml、auth.json 原件）；不改 Herdr 的原有 hook；不修改或重启默认 Herdr server。
4. 隔离 home 中复制的 auth.json、config.toml 不得进入证据目录或 git；测试结束后删除整个隔离 home，并在证据中记录删除命令与结果。
5. "现有 Herdr hook 仍在"的检查放在独立的只读配置副本中完成，不在被信任的 home 里运行。

不在批准范围：其他 trust/权限对话、任何用户级配置写入。再遇到需停下说明。
