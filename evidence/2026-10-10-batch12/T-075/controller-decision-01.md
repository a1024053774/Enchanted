# T-075-1 执行主控决定 01（2026-10-11）

## 1. 依赖：effect 改用 npm 官方源的同版本
- 你申请联网执行 `npm install` 的那次批准，我用 Esc 拒绝了。原因是我被授权代批的范围只到 Computer Use，不含沙箱提权。会话因此被中断，不是你的问题。
- 之后我在自己的会话里试装：本机 npm 配置禁止从远程地址拉包（报 `EALLOWREMOTE`），不能装 pkg.pr.new 的 `effect@8881a9b`。我不改用户的 npm 配置。
- fork 里实际装的是这个预览构建，它自报版本为 `4.0.0-beta.25`；npm 官方源上有同版本号的包。
- 我的决定：
  - `workbench/package.json` 的 effect 改为精确版本 `4.0.0-beta.25`，这一行由执行主控改；
  - 由我执行安装，缓存在 `/Volumes/WD-Elements/a2a-t075-npm-cache`，输出在 `T-075/npm-install-by-executor.txt`；
  - 安装结果：`npm ls --depth=0` 显示 `effect@4.0.0-beta.25`，并已生成 `package-lock.json`。
- 这是执行主控的一次介入，请写进 RESULTS。预览构建和官方源的包可能有差别，以三套测试在新位置的红态、绿态和反例为准。
- 之后如还要联网装别的包，停下告诉我，不要再申请提权。

## 2. 测试产物重定向（回应 issue 20261011T020832Z）
- 同意。在本卡证据目录写一个 runner：加载原测试模块，只重定向 `EVIDENCE` 和产物目录，然后调用原测试，不改任何断言。
- 完成条件 2 改为用这个 runner 跑三套测试，保存实际命令和输出，测试项数仍须是 8、9、18。
- 不要逐字运行那三条原始命令往旧的 evidence 目录写产物。
- 编排测试里把旧 fork HEAD 记成元数据：可以由 runner 覆盖成新位置的版本信息；覆盖了哪些项写进 RESULTS。

## 3. CONTEXT.md / MAP 的 stale
你不用管。收尾时由我核对 `acceptance/entry/a2a_gates.py` 的覆盖关系，并更新 Verified。
