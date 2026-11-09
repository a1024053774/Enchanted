# T-275 结果：发 0.1.7

状态：PASS

| 项 | 结果 | 证据 |
| --- | --- | --- |
| 构建 | PASS | 提交 `2f170d11a` 的干净 sparse checkout，`package.mjs --slot release017 --variant release`；版本 0.1.7，`codesign --verify --deep --strict` 通过，ad-hoc 签名，内带 hc 0.1.15 |
| 安装 | PASS | 退出应用、停后台、旧包备份到 `/private/tmp/enchanted-rollback-t264-20261109`，替换 /Applications 后重签核对通过、版本 0.1.7；启动后 Enchanted 进程 CPU 1–2%；生产 hc core 42545 未动；门禁 `tasks_list` 正常返回 |
| push | PASS | 推送前扫描 `origin/main..HEAD` 新增行 473,162 行：用户邮箱、三个受保护账号名、操作员凭据、各类密钥格式 0 命中，大于 1 MB 的文件 0 个；HTTPS 推送 `fbb842fe8..2f170d11a`，不是 force push |
| Release | PASS | v0.1.7 为 Latest，目标 `2f170d11a`；附件 `Enchanted-0.1.7-macos-arm64.zip`（149,961,464 字节）下载回来 `cmp` 相同；v0.1.6、v0.1.5 保留 |
| 产品页 | PASS | Pages 构建 `2f170d11a` 为 built，线上 200，含“0.1.7 更新”与第 7 站；线上第 7 站挂载、四步可切，第 4 步面板跟到 worker worktree 且只读，无控制台错误 |

没做：T-248 的 43 项页面检查脚本没重跑（它按 6 站写成，换成 7 站需要改检查本身）；本地预览时逐项点过新站（Git 图选提交与看 diff、暂存、Enter 提交后 Git 图出现新提交、审阅备注作为粘贴送进聚焦终端、点 worker 窗格面板跟随）。
