STATUS: INCOMPLETE
SUMMARY: 本次恢复字节与三项机械检查有完整证据；新候选的限定独立窗口审查、包与 Terra 尚未完成。worker 自查不代替独立审查。
TARGET: 当前工作树，相对 62faa87b9424e48a4739920b53920d111a057486，恢复 C=d8f55c958d901d052e79eda1a04dbf0a8fbf5ed5。
EVIDENCE:
- checks-01：冻结 CLI 入口 exit 0；真实 Git/原始文件宿主测试 27/27；脚本安全 6/6。期望值来自原始文件、独立 Git 或预先规定的业务断言，包含随机内容、特殊路径和邻居哨兵。
- equivalence.json：14 个产品/测试与 214 份原证据等于 C 的字节及执行位；README 的唯一差异为保留 T-265；27 份主控窗口文本与 base 原始来源相同；冻结验收及后台保护路径保持。
FINDINGS:
- 无已复现的新产品缺陷；治理 Verified stale 已经 issue 上报。
COUNTEREXAMPLE:
- 历史 host-red-C.txt 拒绝有 HEAD/unborn 的缺失未跟踪内容；local-01 的 unsafe-options、unsafe-paths、force-text 以及旧版均为指定业务红态，按原字节保留。
- 历史主控窗口 old-C 与九个变异分别命中未跟踪内容、列宽拖动/复原、迟到返回、面板/详情/diff 可见性及 Git 父提交/排序；当前只读核对，不冒称本 worker 重跑。
LIMITATIONS:
- 当前后台 panes.ts 与 C 不同；旧窗口与旧包不代表新组合验收。真实窗口与异步选择属 L3，当前新证据为 CLI/真实 Git 边界，不能跨层推定 UI 通过。
- 能力范围为文件、桌面交互、只读边界与异步选择；模型判断、检索、调度及发布不在本卡变更内。worker 未启动模型或后台。
- 最终限定独立审查须由审查员提出 2–5 小变异，主控外部执行，审查员独立判定；随后 Terra 与标准包绑定仍待完成。
RULE:
- 每项反例必须命中规定业务断言；启动、CDP、清理或材料投递失败不能记成产品红态。
