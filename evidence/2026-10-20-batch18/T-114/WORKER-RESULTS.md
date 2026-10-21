# T-114 / a1 仓库内改动交付

状态：INCOMPLETE。两项仓库内改动及沙箱外脚本已准备；提交时 git add 被沙箱拒绝，真实打包、签名和 GUI 验证也尚未运行。分支 `exec/t114`，起点 `b71fc9b36beb64d9adf811ead64669b2d964fb33`；规格为 T-114 `ready_rev: 1`，本轮范围以主控 #70 的两项派发为准。当前尚无交付提交，构建脚本会记录主控提交后的实际 HEAD。

## 提交交接

`git add --sparse` 退出 128：Git 元数据位于本 worktree 可写范围之外的主仓库，创建 index.lock 被拒绝。现场见 `git-add-sandbox-denied.txt`。按派发要求不申请升级；由执行主控先运行：

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t114
bash evidence/2026-10-20-batch18/T-114/RUN-OUTSIDE-COMMIT-01.sh
```

脚本核对分支和起点、拒绝已有暂存项，只暂存本次明确列出的文件，执行 diff 检查并提交；尾注交给已有钩子，不手写。它不 push。

## 1. 软件改名

- `workbench/app/package.mjs`：最终产物为 `Enchanted.app`；打包 manifest 增加 `productName: Enchanted`，用于产品菜单名称。保留包内 `name: a2a`、Packager `name: a2a`、`executableName: a2a` 和 `org.a2a.workbench`，主程序与 helper 可执行名称均不改。
- 签名前通过 Packager 的 `afterCopyExtraResources` 钩子，把主包 `CFBundleName`、`CFBundleDisplayName` 设为 Enchanted。最终目录重命名沿用原有流程，签名后不修改包内容。
- 原因：[固定版本 Packager 20.0.4 的 mac.ts](https://github.com/electron/packager/blob/v20.0.4/src/mac.ts) 在 `extendInfo` 后重写名称，并按 `name` 改 helper 名；[platform.ts](https://github.com/electron/packager/blob/v20.0.4/src/platform.ts) 的资源钩子在签名前执行，空资源列表也执行钩子。因此使用 `extraResource: []`，避免改进程名、引入新依赖或重签路径。未来 Packager 可独立配置显示名时可删除该钩子。
- 界面文字四处：`main.ts` 的窗口标题、`index.html` 的页面标题均改为 Enchanted；`renderer.tsx` 侧栏改为“Enchanted / a2a 内核”；`desktop.mjs` 错误框改为“Enchanted 启动失败”。
- `desktop.mjs` 已与起点按字节核对，除错误标题外完全相同；后台路径、userData 与连接逻辑均未动。未改 `main.ts` 的数据目录逻辑。

运行前已检索受控文件中的 `executableName`、`Contents/MacOS/a2a`、`a2a Helper` 与 `pgrep` 相关引用；本次不改这些内部名称，无需迁移其调用方。另有旧入口绑定旧应用路径：`workbench/app/RUN-OUTSIDE-LOCAL-PACKAGE.sh` 仍固定 T-102 worktree，`workbench/tests/run_t102_packaged.mjs` 固定 `/Applications/a2a.app`；它们是旧验证入口，本次未修改，不可直接拿来验证新的安装路径。

执行主控在本 worktree 的沙箱外运行：

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t114
bash evidence/2026-10-20-batch18/T-114/RUN-OUTSIDE-BUILD-01.sh build-01
```

每次换新标签。脚本使用本 worktree 的 `npm ci --ignore-scripts` 与标准 `package:mac`，不安装应用、不启动 GUI、不调用模型。检查产物路径、主包四个 plist 字段、内部可执行名、helper 名称、打包 manifest、desktop 副本和 codesign。

成功后产物在 `/private/tmp/t114-build-proof-build-01/Enchanted.app`，构建槽 `/private/tmp/a2a-build-t114-build-01` 和本次 npm 安装缓存已删除；保留产物与命令日志，供主控后续安装和发布。摘要写入同目录 `outside-build-build-01.json`。失败保留目录和日志，摘要保持 INCOMPLETE。已有 `~/Library/Caches/a2a-workbench`、Electron 缓存及 worktree 的 node_modules 沿标准构建逻辑保留，后续清理归主控负责。

## 2. 中文首页与旧文档

- 根 README 改为 Enchanted 首页，说明 a2a 编排内核定位、产品页、Release `.zip` 下载、ad-hoc 签名与未公证、右键打开和 `xattr`、GPL-3.0 及 Synara MIT 声明。
- 限制明确为 macOS arm64、Claude Code 与 Codex、开发初版，不承诺可靠性、吞吐或成本收益；保留尚未完成的完整双主控协作、恢复与日常切换边界。
- 删除必须挂载外置盘才能构建的旧说法，改为内置盘构建；开发输出与启动示例按当前 `os.tmpdir()` 路径修正。
- `workbench/README.md` 按 T-111 Resolution 更新沙箱外与独立审查复验结果，并同步新 `.app` 的产物及安装路径。该结论引用 T-111 已有证据，不作为本次打包验收。

## 检查与待办

PASS：`git diff --check`；`node --check` 检查 package.mjs 与 desktop.mjs；`bash -n` 和嵌入 Python 语法检查；改动文本按 UTF-8 无 BOM、LF 回读，没有替换字符；desktop 数据路径代码保持原样。未安装依赖或启动任何产品/模型进程。

按 evidence-first-testing 区分观察与运行：`worker-baseline.json` 仅保存起点的旧名称源码观察，不能替代真实打包红态。真实产物、界面布局、签名及已知坏候选验证尚未运行，行为验收与独立审查仍为 INCOMPLETE。

`project_map.py status` 起止均退出 1：8 项缺文件问题，路径涉及稀疏 checkout 未检出的 findings 与旧 grilling 文件；stale living docs 为 0。原始结束输出在 `project-map-worker-end.txt`。主控需在完整 checkout 重跑，不能把本 worktree 的结果报为 0 问题。

遵照本轮范围，未改 AGENTS、地图、术语表、ticket、验收文件；未 push、未调用 gh，未执行凭据扫描、仓库改名公开、Pages、Release、安装或缓存清理；未调用其他模型或派生 agent。
