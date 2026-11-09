# T-249 v7 交付交接

PASS（worker 限定实现与证据收尾）；整票最终验收 INCOMPLETE。主控 #116 已报告真实窗口组 12/12 达到预期，用户经工作台人工续接后要求完成提交与显式 submit。本轮不再启动测试组，没有修改产品、开发测试或驱动。

已测输入绑定 `5ca17101d350e54582cb301d4f8c9166d63338b5`；当前收尾提交只归入证据、更新报告。主控原始结果来自 `controller/untracked-window-01`，27 份小型文本已归入本目录的 controller-window-01/；来源路径、原始字节核对和提交绑定边界见 controller-evidence-import.json。

- 本地 8 项符合预期：三条机械完成条件通过，旧 C 与只读边界/二进制变异均命中对应业务断言。
- 主控窗口 candidate 为 200 项通过，deferred-candidate 为 49 项通过；旧 C 和九个变异均命中指定业务断言。真实列宽为 128 → 192 → 128 px。
- 原始失败、窗口前自查和外部运行交接均保留。准确恢复 B 为 C 的唯一父提交 05002a377914d52372a4cd46a08fa40229d70e1f，详见 baseline-correction.md。
- 主控组 cleanup.json 确认自有夹具和复制依赖已清理；worker 本地夹具也已清理。额外可写目录 []，无额外目录改动。

RESULTS.md 是本次完整结论，两个 review 文件是限定范围的实现者自查。human-resumption.json 保存本次人工续接原话与介入前 34 项脏文件清单，final-evidence-check.json 保存收尾的来源、范围和编码检查。窗口实际 wrapper/子进程命令保留在原始 summary.json、各 run.json，未重复构建或重跑。

主控下一步：核对最终 submit 提交，安排限定独立审查、标准 Test 包、新 Terra Computer Use 与适用常规测试，再决定门禁集成及安装。project_map status 的 README/REVIEW 两项 Verified 由主控在治理范围处理；worker 不改冻结文档或地图，不把治理状态写成清零。

本次提交之后按当前 task/attempt/session/fence/spec 显式 submit 一次。queued 只表示请求入队，不代表已受理或验收通过；结束回合交 Stop hook 转交。
