# T-114 / a1 / #71 helper 启动修复

状态：INCOMPLETE。代码与新脚本已就绪；本 session 不运行沙箱外 GUI、不申请升级。新提交仍需主控运行提交脚本；新的真实构建、启动与反例结果尚未取得。

## 已知失败与根因

主控 #71 报告：提交 `488ffe3e98ad2ac11d53ad6709ee2cd780477ba2` 的 BUILD-01 退出 0，plist 与 codesign 检查通过，但安装产物启动报：

```text
FATAL electron_main_delegate_mac.mm:66 Unable to find helper app
```

原始构建摘要 `outside-build-build-01.json` 同时记录了 `CFBundleName: Enchanted` 与 `a2a Helper*.app`。这是已知坏候选；其 PASS 仅覆盖旧脚本检查，不能作为启动通过证据。主控在安装副本临时改回 CFBundleName 并重签后能启动、数据表行数未变，只是恢复使用，不作为修复交付。

此前改 plist 的做法让 Electron 按 CFBundleName 找到的 helper 名称与磁盘内容不一致。此次删除整个钩子和空资源配置，由 Packager 一次性生成一致的名称，不再在签名前后单独修改 plist。

## 修改边界

- `package.mjs` 的 Packager `name` 与 `executableName` 都为 Enchanted，打包路径统一为 `Enchanted.app`；主程序变为 `Contents/MacOS/Enchanted`，helper 变为 `Enchanted Helper*.app`。
- `org.a2a.workbench` 不变；未修改 desktop.mjs、main.ts、数据目录或 userData 逻辑。
- `run_t102_packaged.mjs` 改用 `/Applications/Enchanted.app` 和 `Contents/MacOS/Enchanted`。任务标识和原验收行为不变。
- `RUN-OUTSIDE-LOCAL-PACKAGE.sh` 改查 Enchanted.app，并从脚本位置定位当前 workbench，删除固定 T-102 worktree 路径。
- workbench README 同步主程序和 helper 的新名称。旧 WORKER-RESULTS 和 BUILD-01 作为失败过程记录保留；本次以本报告与 BUILD-02 为准。

全仓检索命令和结果保存在 `name-reference-search-02.txt`：完整 Git index 按 `MacOS/a2a|a2a Helper|a2a\.app` 搜索，包括稀疏目录未检出的受控文件；修改后的 workbench、scripts、acceptance、根 README、docs 再以 rg 搜索，旧名称无命中。其余匹配位于历史 ticket、收件箱及日期证据，保留原样，不改写历史。内部主程序和 helper 名称变更的实际调用方是上述打包器、旧验证脚本和安装验收入口，均已更新；bundle id、包内 manifest 的内部包标识 `a2a` 及 IPC 名不属于可执行路径。

## 主控运行顺序

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t114
bash evidence/2026-10-20-batch18/T-114/RUN-OUTSIDE-COMMIT-02.sh
bash evidence/2026-10-20-batch18/T-114/RUN-OUTSIDE-COUNTEREXAMPLE-02.sh
bash evidence/2026-10-20-batch18/T-114/RUN-OUTSIDE-BUILD-02.sh build-02
```

每步成功后再进行下一步。提交脚本要求分支仍为 exec/t114、HEAD 为 488ffe3e98ad2ac11d53ad6709ee2cd780477ba2、没有既存暂存项；显式 `git add --sparse`，尾注仍由钩子生成，不 push。历史构建摘要保持未暂存，不替主控提交其运行证据。

反例脚本对原始 `/private/tmp/t114-build-proof-build-01/Enchanted.app` 运行同一个真实启动探针，要求拒绝且 stderr 明确出现 `Unable to find helper app`，并确认隔离进程与数据已清理。它不操作 `/Applications` 中临时修复过的应用；原始产物若已不在或已被修改，不算反例通过。

BUILD-02 仍在本 worktree 执行 `npm ci --ignore-scripts` 和标准 `package:mac`。除 plist、helper 文件与 codesign 外，它必须通过 `check-packaged-start.mjs`：

1. 直接启动本次产物，用新建的 `/private/tmp/t114-start-*` 下的 `--state`、`--user-data`，清除继承的 A2A、Electron 和 Node 注入环境；不启动任何 agent CLI 或模型。
2. 通过该产物实际 renderer 的 CDP 确认 Enchanted 页面就绪；从系统进程表确认主进程及它的 Enchanted renderer helper；经该产物的唯一门禁入口读取 daemon_status，核对 daemon 可执行路径、独立进程组及隔离 state。
3. 关闭真实窗口，要求主进程正常退出；经同一隔离 state 的 daemon_stop 停止后台，确认主进程、helper、daemon 以及 socket/PID 文件消失后才删隔离数据。清理不明时保留目录并失败，不按名称批量 kill。
4. 只有启动和退出清理均通过才记 PASS，移除构建槽与本次 npm 缓存；保留 `/private/tmp/t114-build-proof-build-02/Enchanted.app` 供后续安装。启动报告与进程表进入 `outside-build-build-02.json` 的 startup 字段，stdout/stderr 留在独立 proof 目录。

## 当前检查

PASS：package.mjs、run_t102_packaged.mjs、启动探针的 `node --check`；新旧相关 shell 的 `bash -n`；嵌入 Python 语法、UTF-8 回读及 `git diff --check`。这些是静态检查，不替代真实启动证据。

INCOMPLETE：新候选真实启动、已知坏候选拒绝、独立审查及提交。上次 Git 写元数据的沙箱拒绝仍适用，因此仅交主控运行脚本。project-map 仍有稀疏 checkout 的 8 项缺文件问题，stale 为 0，输出见 `project-map-worker-fix-02.txt`；完整 checkout 的状态检查仍由主控运行。
