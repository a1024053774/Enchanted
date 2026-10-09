# 方向修复后的补验夹具修正

- delivery-final-21 的 extra 与 live-presets 同时操作同一服务，后者暂把 executor 的持久预设变为 ideation，前者恰在这一窗口发 CLI revise。产品保留条目、返回 role_session_missing，正确地没有伪称送达。两个探针存在依赖，不应并行；原失败全部保留，最终串行运行。
- serial-final-24 的 CLI send/ack 已通过；其最后一个负例沿用审查前的 executor→monitor report。spec 把 report 限为 executor→ideation，修复后在追加前拒绝，原脚本错误地索引 delivery。26 按独立 spec 使用 executor→ideation，并在实际原生归档目标后验证 session-ended 送达失败。不是放宽方向，也没有修改产品。
