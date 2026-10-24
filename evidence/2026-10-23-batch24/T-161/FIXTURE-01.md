# 第一次夹具失败诊断

PLAN / INCOMPLETE。首次运行 `red-20261024T032952Z.json` 的 checks 为空，未启动 Electron，不构成 F02/F07 红态。原 summary、log 及 `/private/tmp/t161-cj9privf` 现场保留。

只读核对 PTY 与 SQLite 事件发现：三个受控 worker 均通过 SessionStart，收到派发正文；随后 UserPromptSubmit 因缺少 `transcript_path` 被拒绝（`question_origin_unverified`），受控 CLI 以 exitCode 7 退出。没有 `turn_end_signal`，也没有提交请求被转交。不是已完成 Stop 却无法提交。

夹具原本只等待 state=idle，误把 SessionStart 后、派发前的空闲瞬间当成回合完成。修正为：真实 PTY 出现 `fixture-turn-1-complete`，后台同时报告 running、idle 且没有 failed；进程退出立即报告输出尾部。原产品缺陷断言未放宽。

受控 peer 现在在隔离 CLI 配置目录创建会话同名 JSONL，记录真实收到的 user prompt，把该路径传入 hook。此文件不伪造模型回复，model/effort 仍为 unknown。提交 CLI 返回 queued=true 后才调用匹配的 Stop，Stop 带明确 stop_hook_active=false。

版本核对：现场导出的 `src/panes.ts`、`src/questions.ts`、`src/gates/cli.ts`、`app/main.ts`、`app/build.mjs` 与 `git show 3c56f743f:workbench/<文件>` 直接逐字节比较均一致。首次运行没有到达构建阶段；因此不能声称 Electron 构建已验证。后续 summary 记录 source、源码比较结果、构建 manifest，并核对 manifest.source 指向指定版本的隔离 app 源码。

本地诊断探针 PASS：在 `/private/tmp/t161-peer-probe-57mmo93q` 用捕获 hook 执行修改后的 peer，实际得到 SessionStart、UserPromptSubmit、Stop，UPS 与 Stop 的 prompt_id 一致，Stop 为 false，JSONL 只有 user 记录。再直接调用首次现场源码的 `validateHookEnvelope`：新 UPS/Stop 均接受；删去 transcript_path 的反例被拒绝为 `question_origin_unverified`。这只证明 envelope 修正，不证明真实后台 Stop 交付或 Electron 红态。

重跑入口：`RUN-OUTSIDE-02.sh`。产品文件未修改，红态仍待真实运行确认。
