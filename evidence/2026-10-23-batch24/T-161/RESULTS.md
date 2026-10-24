# T-161-1 / a1：只读查看与窗格角色

PLAN / INCOMPLETE。修前 RED / PASS；05 的真实 Electron green 已通过，输入错误变异因测试等待超时尚无有效反证，完整验证集待主控运行 `RUN-OUTSIDE-06.sh`。Stop 输入回归另有已知 T-165，保留失败状态。本文不代替独立验收或门禁结论。

主控 #73 已确认 T-157 合并，并在沙箱外把本分支变基至当前 main，接手 HEAD `374cbb384`。已重新阅读 T-157 的 renderer 焦点、输出读取、拒绝提示、恢复按钮和相关测试。产品仅修改 `renderer.tsx`；main/preload 与后台权限保持原实现。

修复内容：

- 输入焦点 effect 在 snapshot.input_enabled 为 true 时才执行，仍等待本次可见状态回放完成，每次显式焦点请求只服务一次。
- xterm 的焦点模式序列仍由原解析器消费，防止自动回传；只有可写窗格才经 observeFocus 记录。没有吞掉真实输入失败，原 failInput 继续停止发送并显示错误。
- 窗格复用 sidebar 已确认主控的 role_label，按 launch 对应传入。原始 shell 身份、权限与侧栏分类不变；头部显示“普通终端 · 执行主控”（或构思主控），自定义名称存在时也保留完整标签。未确认、交回角色的普通终端不获得主控标签。
- README 仅同步焦点与标签行为。Ubiquitous language 继续区分普通终端这一载体与确认角色；没有新增存储、API 或包装模块。

证据：完整修前运行见 `RED.md` 与 `red04-20261024T034907Z.json`，六条缺陷断言失败、九条对照通过，无运行或清理错误。既有失败现场与模拟交付元数据说明保留。

本次测试新增四个分离变异（焦点观察、自动焦点、角色标签、输入错误），并加入可写主控/worker 仍获得输入焦点的正向对照。绿态计划 17 条检查；变异必须只有对应业务断言失败、无运行错误且模型请求为 0。T-157 复跑 Stop 期间输入原样直达、旧回合拒绝后的显式恢复及失效 attempt；T-159 复跑真实分屏、普通终端标签、目录、输入归属与布局恢复。全部经真实 Electron/后台入口；T-157 使用真实 CLI 加本地脚本化 Messages，不调用供应商模型。

当前限制：输入错误变异尚待 06 确认；Stop 输入回归的已知 T-165 未解决，不报告全回归 PASS。最终独立审查、门禁验收、集成和原始夹具归档由执行主控安排。

本地检查 PASS：候选 `57b5c0b42a49dde905350d40e490f2dd50238700` 通过标准 `node app/build.mjs --slot t161-candidate` 构建（workbench 目录，独立 /private/tmp 构建槽）；完成后只清理该临时构建输出，见 `BUILD-01.json`。`python3 -B workbench/tests/test_t157_turn_identity.py --summary evidence/2026-10-23-batch24/T-161/T157-IDENTITY-01.json` 的四项隔离状态检查通过；这不是实际 CLI、PTY 或 GUI 证据。测试、受控 peer、05/06 内嵌 oracle 和 zsh 语法、UTF-8 回读及 `git diff --check` 通过。

05 结果（执行主控 #75 回传）：候选 `fdcf721f3cf3133be544576b5fbf2d67bbaf5b84`，原始结果 `/private/tmp/t161-outside-05.KIeFyq`，摘要与 green 截图保存在 `OUTSIDE-05/`。green 全部 17 项 PASS；观察、焦点、角色三个变异仅在各自的两项业务断言失败，无 error；T-157 recover/expired 及 T-159 split 均 PASS，供应商模型回合为 0。原始失败与原始路径保留，汇总不改写。

05 的输入错误变异只隐藏提示，原 until 因提示永不出现而超时，未走到 real_input_failure_still_visible。这是测试观察方式缺陷。本次不改判据，改为等待最多 4 秒内出现可见的“输入尚未确认”提示，返回布尔值；缺失时该断言 False，截图和零模型请求检查继续执行。CDP/运行异常仍抛出为 error，没有 catch 吞错，产品代码未改。

05 的 t157-stop-input 在“worker 及门禁反馈回到空闲”超时；执行主控 #75 已确认不含 T-161 的 main 上也 2/2 失败，另开 T-165 交 b24-t165 处理。这是主控提供的基线对照，本 worker 不补称自己复跑。06 保留该项及原始错误，只在完全匹配该超时且原 submit 已接受时标 known_baseline_failure=T-165；全套 status 仍为 INCOMPLETE，另列 T-161 范围结果。任何不同失败不按已知问题豁免。
