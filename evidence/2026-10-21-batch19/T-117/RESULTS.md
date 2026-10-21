# T-117 新 Logo 与 0.1.1 发布

状态：INCOMPLETE。Logo 与发布已验证；收尾发现的隔离构建资源依赖正在修正。2026-10-21，当前 Codex 按用户“允许”的逐次授权直接执行，跳过 Herdr 派发；没有创建 worker 或伪造门禁身份。

## 交付

- 原始透明 PNG 原样保存在 `docs/assets/brand/`，独立审查逐字节核对过用户附件。深色标记用于浅底，白色标记用于深底。
- 应用侧栏使用白色标记；Dock 根据 macOS 原生外观选择对应原图。打包入口从浅底原图生成 `.icns`；工作台界面本身仍是深色。
- GitHub README 用 `picture` 选择深浅原图；Pages 页头、演示和 favicon 接入相同素材，手动主题覆盖与系统主题均已验证。
- 安装到 `/Applications/Enchanted.app`，默认数据目录启动时可见新 Logo。bundle id 与数据位置保持不变，原后台 PID 71203 未停止或替换，数据表行数检查见 `run-summary.json`。
- 发布 GitHub Release `v0.1.1`，保留 `v0.1.0`。安装包为 `~/Downloads/Enchanted-0.1.1-macos-arm64.zip`，147,868,092 字节；从 Release 回下载的字节数一致。

已发布包的源码构建版本为 `22d65191515fd00426b9a985cd31f06c842d8516`，Release 目标为 `2754c6bf8dfd90ed3c30f3f4532c2c2de6b94816`；两者之间仅修改验收脚本与证据记录，生产源码相同。收尾另行修正应用素材归属：应用使用 `workbench/app/brand/`，Pages 保留静态发布副本，不再要求隔离工作台副本含 `docs/`。

## 验证

真实 Chrome 与 Electron 检查均直接观察已加载的图片或原生接口，不调用模型。

| 场景 | 结果 | 外置盘目录／文件 |
| --- | --- | --- |
| 旧页面没有新 Logo | 预期拒绝 | `red-site/result.json` |
| 旧安装版侧栏没有新 Logo | 预期拒绝；这才是有效应用红态 | `red-app-04/result.json` |
| Pages 本地：1280／390 宽度 × 系统深浅色 × 系统／浅色／深色选择，原图内容核对 | 12 组 PASS | `green-site-originals/` |
| 已安装应用：侧栏原始白图、Dock light→dark→light、`.icns` 解码像素与缩放后的独立原图一致、版本和签名 | PASS；隔离应用及后台均已退出 | `installed-app-originals/` |
| 将原图输入对调 | 预期拒绝，图片内容不一致 | `wrong-original-sentinel/` |
| 用系统 GenericApplicationIcon.icns 作为图标反例 | 预期拒绝，解码内容不一致；未修改实际应用 | `wrong-icns/` |
| 原有产品页演示回归 | 327/327 PASS | `demo-regression.log` |
| 已部署 Pages，同样的 12 组场景与附件内容核对 | 12 组 PASS | `online-site/` |
| GitHub 实际渲染的 README，深浅图片完成加载且内容匹配附件 | 2 组 PASS | `github-readme-02/` |
| 发布前全 refs 凭据扫描 | 90,563 对象，520 个已有精确豁免，未豁免 0 | `credential-scan-01.json` |
| 扫描后新增对象 | 9 对象，未豁免 0 | `credential-delta-02.json` |

独立只读审查报告保存在 `independent-review-01.md`，当时结论为 INCOMPLETE，不上调。它未发现产品回归，独立核对了原图和实际 `.icns`；指出的两项 P2 均为验收脚本内容核对不足。本次已补成外部原图输入与 `.icns` 解码比较，并取得上述两个拒绝反例。没有做第二轮独立审查。

初期探针的未知调试参数、启动暂停时求值、CSP 阻止 `fetch(file:)`，以及 GitHub 切主题过程中调用 `decode()` 的竞态，都是验证工具问题。原件分别保留在早期应用运行、`green-app/`、`github-readme/` 中，不将其冒称为 Logo 缺陷红态。GitHub 探针现等待所选图片完成加载后再核对，不改产品代码、不放宽内容断言。

## 重放与保留

完整目录为 `/Volumes/WD-Elements/a2a-evidence/2026-10-21-batch19/T-117/`，原始输入副本在其 `inputs/`。命令见 `runs.archive.json`；新的输出目录和构建 label 必须未使用过，避免覆盖旧现场。原演示检查器从基线 Git 对象取出后，以如下命令执行：

```sh
node /private/tmp/t117-tools/check_demo.mjs --url http://127.0.0.1:8617/ --shots /Volumes/WD-Elements/a2a-evidence/2026-10-21-batch19/T-117/demo-regression
```

当时的静态服务命令为 `python3 -m http.server 8617 --bind 127.0.0.1 --directory docs`，使用独立进程组，收尾已停止。`check_demo.mjs` 与同目录 `scenarios.mjs` 可从 `8cc91b023` 的 `evidence/2026-10-20-batch18/T-113/` 恢复到新的临时目录，再选新的截图目录。

依赖只安装在内置盘临时源码副本。成功构建的源码副本、依赖、npm 临时缓存、重复 `.app` 已清理，只保留已安装应用与 Downloads 安装包。第一次构建失败现场和旧安装包先复制到外置盘，逐文件数量和字节数核对一致后才删除原目录；没有计算校验值。清理前后 `df -h /` 均显示约 29 GiB 可用，详见 `cleanup.json`。

限制：未做 Apple 公证；窄屏检查使用桌面 Chrome 模拟视口，未做手机真机测试；Dock 检查覆盖真实原生调用与图片内容，未单独采集最终 Dock 像素。此次不是对全产品功能的重新验收。GitHub 更新范围为仓库 README 品牌与 Release，未修改 GitHub 账户头像或其全站 favicon。

T-115 仍为 INCOMPLETE，本次不归因、不改产品提醒逻辑；T-116 已按用户裁定改为 `ready: no`，不继续版本检查或夹具修复。
