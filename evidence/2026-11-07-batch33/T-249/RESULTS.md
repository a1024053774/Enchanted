# T-249-1 第三次派发：本次核对与交付证据

状态：**INCOMPLETE**（无界面完成条件 PASS；Electron 端到端红绿、新包与独立 Computer Use 验收尚待沙箱外运行）。

- 任务：`a2a+T-249-1`；attempt：`6bab2eb9-0d63-4bb1-b325-f70fa6df2d2b`；session：`9becf52d-3f2e-4cb5-863a-74a8860e5bbc`；fence：2；spec_rev：3。
- 基线：`dc51588832c705aaee0463fb1b96b5586e4c91b7`。
- 按指定顺序运行 `git show ed080306faea900d7c5b26f732b2f05e0c68059a --format= | git apply` 后先提交为 `1cf52a800327153f03e910ab10b632311b761d02`。
- 本次修正后的代码版本：`937a1a038203c43156bd2aacaa1adbdfae534907`。最终证据提交号以 submit 请求为准。
- 环境：Node v26.5.0、Git 2.52.0；提交钩子记录 Codex CLI 0.167.0、gpt-6-astra、xhigh。
- 首次派发的报告原文保存到 [RESULTS-FIRST-ATTEMPT.md](RESULTS-FIRST-ATTEMPT.md)，原 `headless-redgreen/` 输出原样保留，均不作为本次通过证据。

## 实现与逐文件核对

`renderer.tsx` 在 `Workbench` 的主区右侧挂载 `PanelDock`，以 pane key 记录聚焦窗格；`main.ts` 经快照识别普通 shell 与受管 launch，普通 shell 的 cwd 由 `lsof` 读取，受管窗格取 worktree，无聚焦窗格取项目主目录。`preload.ts` 暴露内部 IPC；`gitHost.ts` 在主进程按 argv 执行 Git，不经过 shell。`PanelDock.tsx` 提供注册表、开关、拖宽、固定目录和主题能力；`GitGraphPanel.tsx` 提供提交表、详情、diff、确认框、写操作菜单和 Manygit；`gitGraphModel.ts` 与 `gitGraphCli.ts` 共用同一套读取、布局及写命令代码。`panels.css` 与 `terminalPalettes.ts` 沿用现有主题；终端色板抽取前后的值相同。

已核对 `package.mjs` 和 `start.mjs`，没有修改它们。只提供隔离 test variant 的沙箱外运行脚本。未修改门禁、验收程序、依赖清单或锁文件；未做 T-250、第三方 mod、更新检查或远程机器功能；未 push。

MIT 来源声明保留在借鉴源码中，完整许可在 `gitGraphModel.ts`；本次对照了 [上游 lanes.js](https://github.com/rabeeh-ta/herdr-git-graph/blob/main/mods/git-graph/lanes.js)。

本次红态检查后修正：

1. 原候选只检查 Git 子命令名称，`symbolic-ref HEAD refs/heads/other` 可从只读入口改 HEAD；输出文件选项的缩写与 `cat-file --filters` 也未被拒绝。现在只接受面板所需的只读参数形式，并禁用外部 diff/textconv。受管目录的写动作继续在执行边界拒绝。
2. 详情文件列表改为 NUL 分隔，中文与含制表符的真实文件名可正确传给 diff。
3. 空仓库的“当前分支”显示空历史；未提交行始终放在已加载 HEAD 的列上。
4. 删除没有实测依据的 Git 写操作自动重试，以及尚未使用的 T-250 监视器忽略钩子。
5. 沙箱外脚本不再通配删除其他 T-249 运行目录。每次新建自己的临时根，保存体量摘要后清理；测试未证实进程已退出时保留现场。变异必须触发指定父提交或排序断言，启动失败不能冒充红态。
6. Electron 测试使用真实 linked worktree；Git 元数据直接按文件内容比较，不计算摘要；删除夹具前先写状态摘要。

## 与原 mod 的泳道差别

按本次派发的明确答复：提交只按提交排列，第一父提交继承本列、其他父提交复用等待列或首个空列、多列等待时合到最左列、末尾空列去掉。原 mod 将未提交行也送入 lanes.js；这里单独把未提交行放在 HEAD 所在列，用虚线连接 HEAD，提交列不随工作区是否有改动而变化。不再为这条差异发 issue。尚未加载到 HEAD（分页未覆盖）时没有可连的 HEAD 行，继续加载后补上连接。

## 本次实际运行

本次输出集中在 [attempt-fence2/](attempt-fence2/)，未覆盖旧失败或旧绿态。

| 检查 | 本次结果 | 证据 |
| --- | --- | --- |
| `/usr/bin/python3 acceptance/T-249/check_git_graph.py` | PASS，退出 0；提交顺序、父提交、引用、泳道、未提交行、分支创建删除及非法名称 | `acceptance-initial.txt`、`acceptance-final.txt` |
| `node --test workbench/tests/test_t249_git_host.mjs` | 接回候选 1/8 通过、7 项失败；修正后 8/8 通过 | `host-red.txt`、`host-green.txt`、`host-final.txt` |
| `python3 workbench/tests/test_t249_outside_safety.py` | 原脚本错误接受启动失败、删除隔离旧目录哨兵；修正后 2/2 通过 | `outside-safety-red.txt`、`outside-safety-green.txt`、`outside-safety-final.txt` |
| `python3 evidence/2026-11-07-batch33/T-249/attempt-fence2/recheck_headless.py` | 未变异退出 0；父提交顺序变异、提交排序变异均退出 1，且命中相应断言 | `headless-*/green.txt`、`parents.txt`、`order.txt` |
| `node workbench/app/build.mjs --slot t249-fence2-check` | PASS，renderer/main/preload 构建完成；有 chunk 超过 500 kB 的构建提示 | `build.txt` |
| 隔离 Electron 启动探针 | 未就绪即 SIGABRT，退出 -6，stdout/stderr 空；不作 GUI 红态 | `electron-probe.txt` |
| 源码 `git diff <base> --check -- workbench`、Shell/Python 语法检查 | PASS | 本次交付检查 |

全候选差异检查会提示 `build.txt` 和 `host-red.txt` 中工具原始输出的行尾空格；为保留失败与构建输出原文，没有清洗这些证据。源码与文档无新增行尾空格。

上述无界面命令运行时 `TMPDIR=/private/tmp/a2a-requests-FnYTjr`，夹具用完删除；重放可指定自己的临时根。构建仅临时在 `workbench/app/node_modules` 引用现有依赖，构建输出为全新独立 slot；没有安装依赖、修改共享依赖或在构建输出里放链接。输出 15 个文件、1,627,633 字节，记录后已清理；依赖链接也已移除。没有运行全仓测试或类型检查；本次范围的宿主与构建检查不替代集成测试。

## 审查边界与待办

按 `design-integrity-review` 做实现者结构自查，扫描基线为本卡 base；没有 acceptance_changes。错误框负责展示读取/写入失败，localStorage 失败只影响视图偏好，监视器失败另有任务要求的 15 秒轮询。结构扫描不是行为验收。

按 `behavioral-acceptance-review` 检查证据独立性：冻结验收及补充宿主检查以真实 Git 和文件内容为期望源，变异输出明确命中对应断言；脚本安全测试仅证明脚本分类和清理逻辑。它们不能证明真实窗口焦点、固定目录、菜单、拖宽、键盘、watch 时序或打包后的行为。本 worker 不代替主控派发的独立只读审查，也不代替 gpt-6.1-terra 的 Computer Use 验收。

项目地图收尾状态：Problems 0，stale living docs 1（`REVIEW.md` 覆盖到本次 RUN-OUTSIDE 脚本）。`workbench/README.md` 已同步。地图与 REVIEW.md 不在卡内，已排队上报主控核对 Verified；未自行改动。状态原文见 `attempt-fence2/project-map-status.txt`。

## 主控在沙箱外运行

在本次候选 worktree 中运行：

```sh
bash workbench/app/RUN-OUTSIDE-T249.sh t249-fence2-review-20261108
```

脚本先记录正在运行的正式 Enchanted 进程，再跑冻结验收、Electron 绿态、父提交与排序两个变异，最后执行：

```sh
npm run package:mac -- --variant test --slot t249-fence2-review-20261108
```

使用全新的私有临时根、独立测试 state/UI 数据目录。打出的包位于脚本打印的 `/private/tmp/t249-outside-<随机值>/a2a-build-<slot>/Enchanted Test.app`，核对 bundle id `org.a2a.workbench.test`。正式 Enchanted 前后的 PID/启动时间必须一致。脚本不启动、不替换 `/Applications/Enchanted.app`，不连接它的后台或 hc core；待验收包留给主控启动和独立 Computer Use 验收。结果写入本票 `outside-<时间戳>/`；截图在独立本机临时目录。运行完成后由主控处理上述剩余验收和治理文档状态。

## 额外目录与交付状态

派发的额外可写目录为 `[]`，没有修改额外目录。请求目录仅用于本 attempt 的请求和临时测试；请求文件不会提交。issue 的 `queued=true` 只表示已排队。本报告保存后将 Git 提交，并按本卡受管身份显式发送 submit；排队不是门禁验收或集成通过。

**Works**：冻结完成条件 PASS；本次宿主红绿、脚本反例及两种无界面变异均有可重放文本证据。

**No regression**：当前候选 renderer/main/preload 构建通过，宿主 8/8、脚本 2/2；全仓与真实 GUI 尚未运行。

**Risk / undo**：Electron/新包/独立验收和 REVIEW.md 覆盖版本待主控处理；未集成、未 push，主控可拒收本候选，现场与旧证据保留。
