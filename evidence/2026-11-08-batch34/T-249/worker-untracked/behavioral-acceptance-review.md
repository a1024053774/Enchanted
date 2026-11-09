STATUS: PASS
SUMMARY: 本卡限定修复及新增检测能力的证据自查通过。worker 本地 8 项、主控真实 Electron 窗口 12 项均达到预先规定的结果；没有把预期失败当成候选通过。此为实现者自查，整票最终验收仍为 INCOMPLETE。
TARGET: scoped-repair.patch，相对 18c108fcaed1c4ecf51831f2272578a3b09427be；已测产品与开发测试绑定 5ca17101d350e54582cb301d4f8c9166d63338b5，冻结验收未改。
EVIDENCE:
- 需求来自任务卡“点击未跟踪普通文本显示内容 diff”，包括有 HEAD 与 unborn；旧占位说明不能作为成功预期。Tracer bullet 为真实文件 → 主进程 gitRead → 详情 diff → 独立文件/Git oracle。复用既有接口与展示符合 Deep modules；产品与证据沿用“未跟踪文件”“diff”的 Ubiquitous language。
- 实现前 host-red-C.txt 在有 HEAD 与 unborn 两项明确拒绝旧 C；local-01/host.txt 的 27 场景通过。随机内容来自原始文件，diff 全文由独立 Git 命令给出，不从产品模型生成答案。
- 字面特殊文件名、邻居哨兵、空文件和二进制由实际文件验证；linked worktree 的实际 git-dir/common-dir 由独立 rev-parse 定位，比较路径和文件原始字节，没有 checksum。
- 主控 controller-window-01/candidate/run.json 的 200 项检查通过，覆盖未跟踪普通文本、无首提交仓库、特殊文件名、非文本区分及适用旧窗口场景。主控在沙箱外执行；worker 没有启动 Electron、后台或模型 CLI。
- 列宽通过 CDP Input.dispatchMouseEvent 输入，表头与行几何实际为 128 → 192 → 128 px。没有调用 React handler 或写 DOM style 来伪造交互通过。旧 C 的列宽也通过，不因先前 CUA 的 noWindowsAvailable 改产品实现。
- deferred-candidate/run.json 的 49 项检查通过。测试副本挂起真实 Git 读取后的返回，通过可见控件关闭或改选后再释放；结果未重开已关闭 diff，也未覆盖新选择。该确定性插桩与正常 candidate 分开记录。
- local-01/acceptance.txt、host.txt、outside-safety.txt 对应三条机械完成条件，全部退出 0；这些回归结果不单独证明新的 UI 内容。
FINDINGS:
- 无已复现的新产品缺陷。首轮空文件测试预期有误，已按独立 Git 实测改正，原失败 host-green-01.txt 保留。导入器首次混淆 /usr/bin/python3 与实际 Xcode 解释器的核对失败也独立保留，不记为产品失败。
COUNTEREXAMPLE:
- 宿主旧 C 文本命中 untracked content missing；旧 C 空/二进制命中 Invalid diff base。unsafe-options、unsafe-paths 分别命中 Missing expected rejection；force-text 命中 non-text file manufactured text hunks。均为对应业务边界失败，不是启动失败。
- 窗口 old-C 和 no-untracked 均命中“未提交 未跟踪文本 diff 与原始文件及独立 Git 一致：untracked.txt”。原版占位和变异的错误空文件说明都被内容断言拒绝。
- no-resize 命中拖动几何断言，宽度仍为 128 px；no-reset 命中双击恢复断言，宽度仍为 192 px；stale-diff 命中关闭后旧内容重开断言。
- 原 no-panel、no-details、no-diff、parents、order 五项变异继续分别命中面板、详情、diff 可见性、独立 Git 父提交及排序断言。完整清单与实际 argv 保留在 controller-window-01/summary.json 和各 run.json。
LIMITATIONS:
- 12 项窗口结果全部达到预期，其中两个候选为 PASS，旧 C 与九个变异为指定业务 FAIL；不把这些 FAIL 改写成产品 PASS。各项清理 PASS，组 cleanup.json 确认自有夹具与复制依赖已经删除。
- 窗口原记录没有内嵌提交号。源码绑定由主控 #116、受管会话变更记录、724 个现存受控输入的原始字节核对共同支持；没有宣称运行时记录了源码指纹。详见 controller-evidence-import.json。
- 能力范围：真实文件读取和 Git 边界、桌面入口和异步选择均有证据；角色、编排门禁、模型判断与发布不在本轮变更内，不扩审。
- 最终独立审查、新 Test 包与 Terra Computer Use、治理 Verified、集成安装仍由主控负责。CDP 输入不能替代新的 Terra 观察；历史自查 INCOMPLETE 保留在 pre-window-self-check/。
RULE:
- 未跟踪 diff 必须核对原始内容与独立 Git hunk；每个反例必须命中指定业务断言。启动、CDP 或清理失败不算业务红态。
