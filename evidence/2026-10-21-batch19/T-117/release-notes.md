Enchanted 0.1.1 使用新的品牌 Logo。

- macOS 应用图标与侧栏接入新 Logo，Dock 图标随系统深浅色外观切换。
- GitHub 首页与产品页使用同一套深浅色素材，产品页 favicon 随主题切换。
- 工作台界面本身仍沿用现有深色主题。

安装包适用于 macOS arm64（Apple Silicon）。解压后将 `Enchanted.app` 放入“应用程序”。

本包使用 ad-hoc 签名，未经 Apple 公证。首次打开如被系统拦截，可在访达中右键选择“打开”；必要时运行：

```sh
xattr -dr com.apple.quarantine /Applications/Enchanted.app
```

使用前先安装并登录官方 Claude Code 或 Codex。bundle id 与后台数据目录保持不变。

这是开发中的初版，已知边界与未完成事项见仓库 README 和项目地图。
