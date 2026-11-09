# T-249 未跟踪文件内容缺口

FAIL（当前产品路径）；整票仍为 INCOMPLETE。独立 Terra 验收提交 `83cd1cc8f5873975f80b9438525044e299ea07dd` 报告该缺口后，主控在同一指定 Test 包中另建普通 shell，进入 `/private/tmp/t249-terra-20261108-03/repos/unborn`，点击“未提交的改动（3 个文件）”与 `? untracked.txt`。界面只显示“未跟踪文件，还没有 diff。”；实际文件内容为 `new file before first commit`。AX 与截图保存在本目录，主控自己的 shell 已关闭，未改夹具文件。

需求依据：票的“点文件看 diff”，以及本次验收卡“unborn 的暂存、未暂存、未跟踪内容分别核对”。该路径没有被非目标排除。源码 `GitGraphPanel.tsx` 的 `openDiff` 遇到 `?` 直接返回说明；现有开发窗口测试反而把此说明当成通过条件。这不是冻结的 `acceptance/**` 要求。修复须增加按独立文件/Git 内容核对的红绿场景，不能再把路径存在或说明文字当成内容验收。

Terra 其他结果保留在原提交及 controller/terra-v3-incomplete/。列宽两次 Computer Use 拖动返回 `noWindowsAvailable`，是工具未完成，不是产品缺陷；需要独立真实窗口输入测试补证。原候选 `18c108fcaed1c4ecf51831f2272578a3b09427be` 未集成，父 attempt 与 Terra attempt 均已经正常门禁回收。后续用新的受管 attempt 导入原候选并做限定修复，旧候选与失败证据不删除。

**Works**：主控真实窗口复现与独立验收一致；复现包为 `1243bc15f979976967cfd2d5cdd3a2acce6df635`，与父候选产品输入一致。

**No regression**：本次只观察已有功能，没有产品修改；Terra 的三项常规测试通过，不代替新修复的验证。

**Risk / undo**：新修复尚未实现；原包、提交、测试结果全部保留。正式应用与后台未重启。
