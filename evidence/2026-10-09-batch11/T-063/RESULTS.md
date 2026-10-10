# T-063 执行结果

状态：INCOMPLETE（代码与检查已完成，待冻结候选独立审查）。ready_rev：1；worker：s11-t063。Ticket 保持 open，待主控关闭。

fork 基线：`4ac5ba00e7125279b08c241037d1404450455ff6`（a2a 分支）；候选：`e94a0efc395c26bedb6cbf65f8fdf7f5c2125a58`。a2a 起点：`4352d8e59931da82a825cace96256cf8e76f14ef`。原有 `.grok/`、主控持续追加日志与 T-062 现场都保留。身份与版本见 `binding.json`、`fixture-identity.json`、`versions01.log`；provider 禁用，模型调用为 0。

目标：查明已有 profile 重开停在 logo 的来源，走通隔离验收重开路径；修复两种窗口尺寸的空态重叠。非目标：正式实例、产品启动流程、服务端、Electron 主进程、其他组件、外观认可。验收来自 ticket ready_rev 1，未从实现输出生成答案。

Tracer bullet：真实隔离 dev 入口先红，再以同一入口验证布局与重开。Deep modules：没有新增生产包装、兼容路径或重试。Ubiquitous language：沿用“任务窗口”“agent 会话”“问题上报”。界面按 frontend-less-ai-tone 沿用 Synara 样式；只判断是否重叠，不宣布外观合格。

## 变更与上游清单

只改上游 `apps/web/src/components/ChatView.tsx` 的空态块（8 行增加、11 行删除），详见 `fork-diff.patch`。导入横幅退出绝对定位，横幅、logo、标题和输入区按正常流排布；内容不足时整个空态可滚动，宽裕时输入区仍在底部。没有改 `apps/web/src/a2a`、Sidebar、启动流程、服务端或 Electron 主进程。

## 问题 1：来源与重开

观察到的 11 秒 logo 阶段是 dev 模块加载阶段：`red02.json` 与 `reopen-node-normal01.json` 记录 HTML boot splash、仍在响应的 Vite 原始模块请求及尚未建立的产品后端 WebSocket，已看标记没有机会在此阶段门控 React。并非“健康接口 200 所以启动通过”。原 T-062 约 11 秒观察不足以证明永久卡住；本轮系统 Chrome 在数次较长加载中还出现进程提前关闭，具体内部退出原因没有查明，不能把它当成产品启动逻辑缺陷。

同一 `browser-red02` profile 保留全部产品 localStorage，仅在隔离 dev 页关闭 HTTP 缓存后，`green07-resume.json` 实际读回任务窗口、隔离项目、三条问题和空态标题，18.747 秒内完成 hydration。截图为 `green07-resume-reopened.png`。这是验收环境的可用重开路径，不是产品中的 fallback；生产源码未修改启动行为。`reopen-cache-off01.json` 只看到主界面壳，单独不算完整重开通过。

最终固定浏览器的正常 HTTP 缓存复验 `green11-pinned-resume` 也退出 0：同一 `browser-green09-pinned-cached` profile 完整重开耗时 38.913 秒，三条指定的 seed 输入都可见，实际显示 5 条（全部筛选），没有禁用 HTTP 缓存。两种尺寸、resize 返回、长中文标题和输入区均零重叠且可完整滚动到可见。对应 `green11-pinned-resume-*.png`、`*-command.json`。这证明隔离 dev + 已有 profile 在正确测试浏览器下可走通，未修改产品启动流程；系统 Chrome 内部退出原因仍未知，正式实例未测试。

测试工具另一条环境问题：项目固定 Playwright 1.62.1 的浏览器缺失，系统 Chrome 的 Vitest 运行在收集前断开。经已有 Playwright 的标准安装入口把对应 Chromium Headless Shell 151.0.7922.34（v1234）下载到外置盘本轮目录；相关原有浏览器用例随后通过。安装与路径见 `playwright-install01-command.json`、`browser-pinned.config.mts`。没有改依赖清单、锁文件或用户浏览器配置。

## 问题 2：独立红绿证据

`counterfactual-red01` 临时换回基线的 ChatView，执行真实界面 oracle 后在 finally 恢复候选原字节；保存两版源码和恢复记录。旧版在 1600×1050 的横幅/logo 相交面积为 1460 px²，1280×900 的横幅/标题相交面积为 14315.15625 px²，标题还挤进输入区。退出 1 的原因包含这些业务断言。

`green07-resume` 在候选上退出 0。两种尺寸、1280→1600 resize 返回、加长中文文案下，横幅/logo、横幅/标题、标题/输入区的相交面积都为 0。额外确认滚动后 logo 与完整标题、完整输入区均能看见，防止“藏掉文字所以不重叠”的伪通过。截图分别以 `green07-resume-1600x1050`、`1280x900`、`resized-back`、`long-copy-1280x900` 为前缀；`-hero.png` 展示标题和 logo，`-composer.png` 展示输入区。

重放见 `REPLAY.md` 与各 `*-command.json`。原始失败不覆盖，原 profile 不重置。

## 失败方式清单逐项处理

| 失败方式 | 处理及证据 | 限制 |
| --- | --- | --- |
| 已看标记或缓存损坏 | `green05.json` 在本轮 profile 的三个已看标记写入 `{invalid-json`，重开读回隔离项目、三条问题、标题；13.086 秒完成。现有存储读取报告解析错误后恢复，未改其实现。HTTP 缓存问题另用同一失败 profile 的 cache on/off 诊断与可见 UI 复验 | 不声称任意 profile 数据损坏都恢复；浏览器内部缓存损坏原因未知 |
| 服务端未就绪、前端无重试 | `delayed01` 核对身份后只停本轮 backend；页面显示 Failed to fetch，再启动同一 home 的真实 backend，19.285 秒内自动读回三条问题和标题，未 reload，未改重试逻辑 | 仅验证本地短暂未就绪，不主张无限断网可靠性 |
| 启动后窗口尺寸改变 | 同一 page 1600×1050→1280×900→1600×1050，每阶段零重叠并核对内容可滚动到完整可见 | 没有覆盖任意尺寸、移动端或真实桌面缩放 |
| 其他语言的文案变长 | 在真实 DOM 注入更长中文横幅和两行中文标题，1280×900 下零重叠、内容与输入区可见 | 产品没有 locale 开关；这是布局压力输入，不是真实翻译功能验收 |

## 检查

| 检查 | 结果 |
| --- | --- |
| 相关既有单元测试 | PASS，4 文件 / 32 项；`related-tests01.log`。命令中不存在的 useLocalStorage.test.ts 没有被算作通过；实际 hook 覆盖在下项 |
| 相关既有浏览器测试 | PASS，3 文件 / 5 项；`browser-tests04-pinned.log`。按名称只选相关用例，其余 208 项跳过，不宣称整份 ChatView 套件通过 |
| 全 workspace typecheck | PASS；`typecheck01-command.json`，保留已有建议输出 |
| 全 workspace lint | PASS，0 errors、877 warnings；`lint01-command.json`，未把警告改写为无警告 |
| 全 workspace fmt:check | PASS；`fmt-check01-command.json` |
| 完整 workspace test、正式桌面运行 | 未运行：brief 要求紧缩相关测试，正式实例禁止操作 |
| 只读独立审查 | 待审；只对冻结的 fork + a2a 证据提交审一次 |

## 保留的失败、限制与清理

`red01` 命令路径错误；`green01` 为被否决的中间布局；`green02` 在长文案截图写入遇到 ENOSPC；`green03`、`green05` 的长文案可见性检查遇到小数像素滚动误差，测试导航改为向上取整而没有降低断言；`green04-corrupt`、`green06` 为 Chrome 在 UI 设置期间提前关闭；`browser-tests01` 配置参数重复，02/03 是系统 Chrome 连接在测试收集前关闭。它们全部保留，不算产品通过。`green05` 总体退出 1，但它的损坏标记重开子用例实际通过，与整体结论分开。

ENOSPC 已经 `scripts/inbox send` 上报：`20261010T031612Z-worker:s11-t063-issue-001`，正文见 `issue-disk.md`。后续磁盘检查空间增长来自外部状态变化，本 worker 没有清理他人文件。清理时提前停止服务干扰了 `green08-pinned-cached`，见 `green08-intervention.md`；该轮不用作验收，通过新标签重跑。`green09/10` 的问题总数断言不成立：T-057 seed 实际有 5 条输入，其中等待筛选显示 3 条，全部筛选显示 5 条；重开恢复了全部筛选。测试已改为核对 seed 中三条指定的原始问题可见，并记录实际总数；没有放宽布局断言。09 的错误文字误称期限，实际 40.495 秒已出现项目与标题，总数断言才是失败。

本轮仅创建隔离 root `/Volumes/WD-Elements/dev-cache/synara/instances/t063-probe01`、工具缓存和证据。没有访问正式工作台数据、用户 Herdr、`~/.codex`、`~/.claude`，没有 push、桌面构建或 dist/依赖目录替换。原 profile 与 userdata 保留在隔离 root，未入 Git，也未归档私钥。停服务按记录核对 PID、lstart 和命令，只停自己的进程。结束前地图 status 要求 Problems 0、Stale 0。

`git diff --cached --check` 对原始 lint/typecheck/Vitest 输出中的尾空白与工具结尾空行返回 2（见 raw-diff-check.txt）；为保留失败与原始输出没有改写它们。生产 fork 的 diff --check 通过，fmt:check 通过。
