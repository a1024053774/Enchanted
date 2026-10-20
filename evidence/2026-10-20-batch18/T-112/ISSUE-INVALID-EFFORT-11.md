T-112 / a1：Codex 0.162.1 接受未列出的 effort 字符串，启动失败验收与 CLI 实测不符。

观察：outside-native-06.json（候选 d86126abe06ba845df036bddbeb922543c0542cb）已通过 factory、ui-settings、override；invalid 分支没有放行首轮，只等待 launch_failed，最终超时。终端显示 unsupported-t112 且进程继续运行。

进一步用 PROBE-INVALID-EFFORT-11.py 经真实交互 Codex 0.162.1、全新隔离 HOME/CODEX_HOME 和无凭据 loopback Responses API 测量。invalid-effort-cli-200-01.json 保存完整 argv、原始终端、请求及 rollout：reasoning.effort 原样为 unsupported-t112；turn_context.effort 也是原值；收到固定文本后产生 task_complete，进程在收尾前仍活着。结束时的 -15 是探针主动 SIGTERM，不是 CLI 参数错误。模型调用为 0；未调用真实供应商，不能断言真实 API 对这个值的行为。

位置：workbench/tests/run_t112_native.py:197 的 invalid 分支假设 CLI 必须在启动时非零退出。票中“不支持取值由 CLI 报错并记启动失败”的条件目前无法用这个字符串证明。CLI 没有拒绝或换值；a2a 不能靠新增枚举代为判断，也不能把自己构造的 HTTP 400 冒称为真实 API 行为。

建议：按执行主控 #53 的第三种分支交主控判断如何处置这项验收。保留当前失败与已通过的原生场景；不修改产品、原 invalid 断言或整体通过判定。若要改为首轮供应商参数错误，需要先明确真实错误依据，以及回合错误与启动失败的记录语义。
