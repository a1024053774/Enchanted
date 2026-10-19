# Python 3.9 准备阶段修复

修复项：PASS。T-105 整体验收：INCOMPLETE。

执行主控已提交原候选 `ba23a605d2536c91668f6628a54ccf01ff9c25d7`。首次沙箱外重跑在 Python 3.9.6 的 `tarfile.extractall(filter=...)` 处退出，尚未进入 Electron。原失败目录 `/private/tmp/t105-outside-baufcev4` 保留，未改动。

只把固定 Git 基线的解压改为 `/usr/bin/tar -xf ... -C ...`，移除未使用的 tarfile 导入。没有改工作台实现、门禁、输入或布局合同。

本地使用系统 `/usr/bin/python3` 3.9.6 执行实际 wrapper 的源码复制、git archive 和解压代码，停在 npm 边界：

- 原脚本复现同一 TypeError；最终验证器也拒绝 ba23a605d 的原脚本，见 `python39-extract-known-bad-03.json`。
- 修复后 PASS：445 个文件路径与 `git ls-tree` 一致；main.ts、README.md、package-lock.json 与固定基线的 `git show` 字节一致，见 `python39-extract-green-02.json`。
- wrapper 的 Python 3.9 编译及 `bash -n` 通过；`/usr/bin/python3 workbench/tests/run_t105_panes.py --help` 通过。
- 验证器初版曾提前停在解压之前，造成“缺全部文件”的夹具错误；记录保留在 `python39-check-setup-failure-01.json`，不当作产品红态。

验证命令（末尾编号需选未使用的路径）：

```sh
/usr/bin/python3 evidence/2026-10-19-batch17/T-105/VERIFY-PYTHON39.py --script evidence/2026-10-19-batch17/T-105/RUN-OUTSIDE-01-ELECTRON.sh --source /Users/luckye/Documents/Code/a2a-wt-t105 --summary /private/tmp/t105-python39-recheck.json
```

本地只验证了 npm/Electron 之前的真实准备代码；不据此宣称完整 Electron 通过。主控在沙箱外运行：

```sh
bash evidence/2026-10-19-batch17/T-105/RUN-OUTSIDE-03-COMMIT-PY39.sh
bash evidence/2026-10-19-batch17/T-105/RUN-OUTSIDE-01-ELECTRON.sh 02
```

新摘要为 `electron-02.json`。提交脚本只接收 T-105 证据目录中的改动，核对父版本 ba23a605d，并让既有钩子自动追加本 worker 尾注。
