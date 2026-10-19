# T-106 / a1：P2 提交前表单拒收

2026-10-19。**INCOMPLETE**：修复与局部红绿、P1 回归完成；提交和当前候选真实 Electron 检查交主控执行。没有调用模型、保存截图、修改门禁/daemon 或申请升级。

绑定 task `T-106`、attempt `a1`、session `46c7c0a5-076f-48e7-adc0-4aea62a637a9`、launch `launch-d83c474a34f148c19f8e35e9bd60ff71`。起点与红态候选为 `5036a8dc32de265dc27499028f0b938db3d1a15a`。范围取主控 #44 的 P2 修复要求；未提供 fence/spec_rev，不推断其值。保留两轮审查报告、主控运行摘要和原审查脚本，不替主控暂存或改写它们。

目标是 main 已确定发生在提交前的字段拒收保持可编辑、可取消；非目标是改变 P1 的未知结果处理、门禁规则、权限、创建路径或任务卡默认值。**Tracer bullet** 沿表单 → main 的提交前拒收 → 可修改/取消 → 正常门禁注册检查；**Deep modules** 保持 main 对提交阶段的事实所有权，renderer 使用结构化结果；**Ubiquitous language** 区分未提交与结果未知。

## 修复

- main 将合法表单字段集合中的错误类型、空白标题及超过 240 字符的标题返回为 `{ok:false, stage:"preflight", persisted:false, details:{field,reason}}`。不再用 IPC 异常表达这些已知未提交的业务输入错误，也不创建临时卡或调用任何门禁。
- renderer 沿已有结构化结果保持表单可编辑、可取消，并明确显示“表单未提交”和字段原因。没有在前端按异常字符串猜阶段，也没有重新启用不确定提交的按钮。
- sender/frame、未知草稿、已保存或未知状态、额外 repo/非法字段集合的信任边界仍按原拒绝保护。P1 的 card_show/status 核对、未知锁定、禁止重放没有改动。
- 没有增加标题 HTML pattern；纯空白仍可走真实 IPC，由 main 的结构化返回验证修复，不只依靠前端拦截。

## 红绿与回归

```sh
node --experimental-vm-modules workbench/tests/test_t106_creation.mjs evidence/2026-10-19-batch17/T-106/preflight-red-01.json
node --experimental-vm-modules workbench/tests/test_t106_creation.mjs evidence/2026-10-19-batch17/T-106/preflight-green-01.json
node --experimental-vm-modules workbench/tests/test_t106_postcommit.mjs evidence/2026-10-19-batch17/T-106/preflight-postcommit-regression-01.json
node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs evidence/2026-10-19-batch17/T-106/preflight-pane-regression-01.json
```

第一条在编辑产品代码前退出 1，因纯空白标题抛 `Invalid creation fields`，没有得到要求的结构化提交前拒收。相同信号在修复后退出 0。新增检查覆盖纯空格、制表/换行/不换行空格、超长标题、非文本标题、非文本分支；每次均核对 `persisted:false`、preflight 阶段、字段及非空原因、零新增门禁调用、零保存/任务写入，再核对取消和后续有效提交。原测试断言没有删除或放宽。

后两条 PASS。P1 七种实际 daemon/门禁/SQLite 故障场景全部保持原行为，`test_t106_postcommit.mjs` 源码未改；17/18 IPC 名称、原权限/窗口/恢复及已知坏版本检查保持。创建测试使用实际 main 与边界夹具，其零写入不是实际五表 SQL 证明；真实五表计数及同一表单改正后成功由下述 Electron 复验完成，不冒充已运行。

标准 UI 构建在内置盘临时源码与依赖副本中运行 `node app/build.mjs --slot preflight-final`，结果见 `preflight-build-01.json`；成功后清理临时副本、依赖与构建输出。Vite 的既有大 chunk 提示未扩大处理。新脚本的 shell、嵌入 Python 3.9 语法、实际生成复验代码的 AST/compile、UTF-8 与 diff 检查均已运行；外部实际 Python 3.9 和 Electron 尚未执行。

## 主控提交与真实入口检查

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t106
bash evidence/2026-10-19-batch17/T-106/RUN-OUTSIDE-06-COMMIT.sh
bash evidence/2026-10-19-batch17/T-106/RUN-OUTSIDE-05-PREFLIGHT.sh
```

提交脚本核对分支、固定起点、暂存范围和未暂存产品变化，以本 worker 非秘密身份让原 hook 添加尾注。已知共享 Git 元数据写入边界交主控在沙箱外执行，不申请升级。

**不要直接用原 REVIEW-OUTSIDE-02.sh 验新候选**：原脚本固定 archive `5036a8dc3`，仍会测试旧代码。05 封装保持原脚本字节不变，在新的临时脚本中仅将候选绑定为运行时完整 HEAD，并在原全部断言后追加同一表单的“空白标题 → 结构化拒收 → 五表无增长 → 可编辑、可取消 → 改正标题 → 同一任务号成功注册”旅程。原先的取消检查与后续 P1 五场真实 GUI 故障全部保留。封装拒绝未经提交的 workbench 改动，保证运行对象为冻结提交；依赖主控已提供且保留在本 checkout 的 REVIEW-OUTSIDE-02.sh，脚本结构改变时明确停止，不猜测适配。

05 **无需手动操作目录对话框**，沿用原审查的观察 driver 固定测试目录，不把它说成新的原生目录选择证明。实际 main/preload/renderer、daemon、门禁、SQLite 均执行；没有模型、截图、安装或用户数据操作。运行前会输出冻结 candidate 与生成的复验代码路径，结束输出独立 summary 路径。原脚本的清理、失败保留与无覆盖语义保持。可先运行 `bash .../RUN-OUTSIDE-05-PREFLIGHT.sh --check`，仅生成并编译复验代码，不运行 GUI；本 worker 已运行此模式，未拿静态检查称 GUI PASS。

原审查文件和旧运行结论没有改写。新候选还需主控运行真实入口并完成针对 P2 的定向复核；本 worker 不代替独立审查。`project_map.py status` 仍有 8 个既有稀疏 checkout 缺文件诊断，stale living docs 0；未改地图或其他 ticket。真实模型根回合 0。
