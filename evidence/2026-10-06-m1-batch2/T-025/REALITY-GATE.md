# T-025 探针边界（2026-10-06）

REALITY GATE: INCOMPLETE

- GOAL / NON-GOALS：核实锁定 gpui-kit 0.7.1 在本机的构建、窗口、中文与复制能力；不实现工作台、不改引擎或技术方向。
- DECISION：为后续 T-028 提供平台证据；本 worker 不作路线取舍。
- OBSERVED：任务书锁定 gpui-kit 0.7.1；该 crate 固定 gpui-pre =0.3.8，公开 test-support；本机 macOS 27.0，只有 Command Line Tools；外置盘独立挂载。
- MEASURED：构建耗时、target 占用与启动结果将在各运行目录保存。
- INFERRED：公开窗口与无头测试 API 足以构造此探针，实际编译与运行尚待核实。
- UNKNOWN：系统拼音的组词/候选位置、跨段复制是否保真、玻璃观感是否达标。
- PROBE：Codex worker 通过 scripts/build 编译独立包，启动一个 Blurred 窗口并截图；无头测试从真实 Render 入口操作控件与两个输入框。缺失控件、模式未更新、换行丢失、输入串框、窗口未出现均失败。失败保留原运行目录，不覆盖。
- PROBE：用户按 MANUAL-CHECK.md 用系统拼音与文本编辑操作，预写期望文本；丢字、候选窗错位、选区乱序均失败并停止；实际结果与录屏放在本目录的独立 manual 子目录。
- 自动测试隔离失败方式：模式按钮没有更新视图；不透明度更新未呈现；多行被单行化；焦点切换串框；Markdown 区域没有布局。初始空 Render 应因缺失控件失败；这属于新行为合同红态，不是已有产品缺陷。
- DECISION CONSEQUENCE：自动检查通过只证明相应范围，不能代替真人 IME、跨应用剪贴板或观感验收。
- NEXT ACTION / OWNER：worker 完成自动检查与手测交接；真人测试前 ticket 保持 open，整体 INCOMPLETE。
