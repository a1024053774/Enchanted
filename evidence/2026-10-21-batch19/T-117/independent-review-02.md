STATUS: PASS（仅限 T-117 本次资源迁移跟进）

TARGET: `aaba2b586574f6bd6e65049bab0509c5b2a2b418`；差异基线 `6ff57c8a47d2ff36ae8f629f234e02e13c44f64c`。

审查来源：新建只读 agent `01a15d44-87e7-7e52-befa-929972b84b19`（Turing），不继承主会话历史。以下保存其返回结论。

EVIDENCE:

- `renderer.tsx:9`、`build.mjs:33`、`package.mjs:51` 均改用 `workbench/app/brand/`。现有私有复制及 `git archive … workbench` 调用方可取得所需素材，无须扩大夹具范围。
- 外部 `build-03.json` 及日志记录候选通过 `npm ci --ignore-scripts` 和标准 `npm run package:mac -- --slot t117-03`。独立核对保存的 `source.tar`：仅含 `workbench`，内容与冻结候选归档完全一致。
- 独立逐字节复核重建包与 `/Applications/Enchanted.app`：81 个仓库运行时/UI/hook/bin 等文件及 `.icns` 全部相同，与 `runtime-equivalence-03.json` 一致；锁文件未变。
- 两张应用 PNG、Pages 副本及新旧包内 PNG 均与外部 `inputs/original-on-{light,dark}.png` 完全一致；README、Pages 引用及静态副本未变。
- `isolated-app-03/result.json` 已完成，结果 PASS。检查实际打包侧栏、light→dark→light 时传给原生 Dock API 的图标，以及解码后的 `.icns`；侧栏截图显示深色 UI 与白色标记。
- 会话开始及结束的地图检查均为 Problems 0、Stale living docs 0；HEAD 保持冻结候选。

FINDINGS:

- 无本次范围内的可报告缺陷。资源归属修正恢复了既有 workbench-only 构建契约，未发现交付 logo 或仓库运行时内容变化。

COUNTEREXAMPLE:

- 父版本仅含 `workbench` 的真实构建被拒绝：`isolated-build-red.json/.log` 记录退出码 1，无法解析 `../../docs/assets/brand/logo-on-dark.png`。红态夹具的直接构建文件与父版本一致；候选在相同目录边界内成功打包，未以补复制 `docs` 绕过缺陷。

LIMITATIONS:

- 本次只读审查未启动应用、重跑构建或完整历史夹具，也未重新核验线上发布；真实运行依据现有候选证据。
- 81 文件比较排除 `ui/build.json` 的临时路径及重新构建的第三方 `node_modules`，不声称整个应用包完全相同。
- Dock 证据到原生 API 调用及图标内容，未覆盖最终屏幕像素。本结论不将冻结票据中仍为 INCOMPLETE 的整票状态上调。
