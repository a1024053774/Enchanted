# T-157 独立审查 01（agy）

- 候选：1ca1f3e08；起点 37c42f17a
- argv：`agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-157-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-157-r1/prompt.txt)"`
- # pane wG:p1Y started 2026-10-24T04:22:01Z candidate 1ca1f3e080923b4215acb29b4e7965f862416848
- 结论：PASS。一条 P3：panes.ts:1032-1034 转录逐行 JSON.parse，中间行受损会抛错由外层 catch 记录；建议的“单行解析保护”会吞掉坏行，执行主控不采纳（不加吞异常路径），保持现状。

## 窗格原文

```text

      ▄▀▀▄
     ▀▀▀▀▀▀
    ▀▀▀▀▀▀▀▀
   ▄▀▀    ▀▀▄
  ▄▀▀      ▀▀▄

  Antigravity CLI 1.4.7
  <agy 账号邮箱，已删> (Google AI Pro)
  Gemini 3.8 Flash (High)
  ~/Documents/Code/a2a-review/T-157-r1

────────────────────────
> 你是 a2a
  项目的只读独立审查员（re
  viewer），审查
  T-157：真实使用测试发现
  （F01，blocker）受管
  worker 的 Stop
  交付批次进行中用户在窗格
  输入后，同一
  attempt 的 submit
  被门禁拒为
  worker_not_active，界面
  显示“未知/忙”且无说明、
  无恢复入口。
  用户 2026-10-24
  定原则（构思主控转述，见
  user-decision.md）：“我
  在
  agent
  工作过程中输入内容这个他
  自己
  cli
  会处理的吧,他会在此次工
  具执行完成后加入这句话再
  做思考,这个不用我们处理
  吧”。据此：(a)
  输入原样直达
  CLI，不拦不延后，只记人
  工介入；(b)
  工作中的输入不应让进行中
  的
  Stop 批次交付失效——人工
  Enter
  不清空/替换仍有效的 turn
  身份，同 attempt submit
  按原 turn
  核对通过，门禁核对不放松
  ；(c)
  输入确已开启新 turn
  时门禁仍明确拒绝、不改写
  成成功、不自动重试，界面
  写明最后事实与原因，此时
  才给最小恢复入口；(d)
  不做“暂停后点重新交付”的
  常规路径。
  执行主控沙箱外运行（0
  个真实模型回合，真实
  daemon/PTY/Claude
  CLI/Electron，脚本化
  Messages）：outside-01
  修前红态；03/04
  暴露夹具问题（整块粘贴被
  CLI
  当粘贴确认）与一个产品缺
  陷（排队输入的新
  turn
  未登记，最终停在“未知”）
  ；outside-05
  共 13 项：正例 4 项与
  T-159/T-160/T-133 回归
  PASS，两个修前基线与 4
  个坏实现只在预期断言失败
  。
  请特别核对：门禁
  turn/attempt/版本核对确
  未放松；“凭原生
  queued human 转录建立新
  turn”是否可靠、会不会把
  无关输入误配为
  Stop；新 turn
  已开始时仍拒绝；恢复入口
  绑定原
  attempt、不自动重试、不
  复用旧请求；界面文案清楚
  ；改动是否在任务卡边界内
  （panes.ts、gates/**、re
  nderer.tsx、sidebar.ts、
  测试、README）。

  材料在
  /Users/luckye/Documents/
  Code/a2a-review/T-157-r1
  /
  下：candidate/ 为候选
  1ca1f3e08
  只读副本（ticket 在
  candidate/.project-map/t
  ickets/，任务卡、RESULTS
  与运行证据在
  candidate/evidence/2026-
  10-23-batch24/T-157/）；
  full.diff
  为相对起点
  37c42f17aa5e0dc0b27272ba
  2363d713cf14f2b6
  的 workbench/
  全部改动；user-decision.
  md
  为本批用户授权的转述（构
  思主控
  assign）。

  请核对：
  1.
  根因是否找对，改动是否在
  最小根因层；有无吞异常、
  fallback、重试、兼容分支
  或平行
  API。
  2. ticket
  的每条验收是否有真实入口
  的证据；期望值是否来自
  ticket/规格/用户原话而不
  是抄产品输出。
  3.
  红态是否在修前版本上落在
  缺陷断言上；变异是否代表
  真实坏实现并被拒绝。
  4.
  是否越出任务卡的修改边界
  ；界面文案是否清楚、不含
  营销腔。
  5.
  其他正确性、回归风险。

  这是交互会话。只用你自带
  的读文件/搜索工具，不要
  运行任何
  shell
  命令，不要写任何文件。可
  以打开截图。输出中文报告
  ：每条发现写文件与行号、
  严重度（P0–P3）、失败场
  景。审查完把完整报告作为
  你最后一条回复直接输出，
  最后一行只写
  `T-157 REVIEW
  PASS`、`T-157 REVIEW
  INCOMPLETE` 或 `T-157
  REVIEW NO_GO` 之一。

○ Thought for 3m 18s
● Explored 25 fil...
(ctrl+o to expand)

▸ Thought for 53s
   a2a 项目 T-157
  独立审查报告

  审查对象：T-
  157（候选提交
  1ca1f3e08 /
  被测完整产品版本
  d9e948bba197e8484225a8
  1eb85a91a0aef6a8c0）
  基线版本：37c42f17aa5e
  0dc0b27272ba2363d713cf
  14f2b6
  审查范围：full.diff
  改动、任务卡
  card.md、用户裁定
  user-decision.md、隔离
  状态测试及外部真实
  Electron / daemon /
  PTY / Claude CLI
  证据（OUTSIDE-01 至
  OUTSIDE-05，共 13
  场运行证据与截图）
  审查角色：只读独立审查
  员（Read-only
  Independent Reviewer）
  ──────
  ## 一、审查结论摘要

  候选方案完全遵循用户
  2026-10-24 裁定的“由
  CLI
  原生排队处理输入”原则
  ：

  1.
  根因定位准确且在最小根
  因层：修前人工 Enter
  错误抢跑置空
  claudePromptId 并替换
  active
  身份，导致进行中的
  Stop 批次交付在
  assertActive
  检查时被拒为
  worker_not_active。修
  复去除了 Enter
  抢跑逻辑，输入原样直达
  CLI
  并记录人工介入，未放松
  任何门禁校验，未引入重
  试、fallback、平行 API
  或异常吞没。
  2.
  排队回合与原生转录建立
  新 turn
  机制可靠：对排队中的
  UserPromptSubmit
  校验终端 Enter
  事实与原生转录路径，并
  在转录出现符合要求的
  queued human
  记录时才正式切换新
  turn。工具结果、子线程
  、错会话/目录/时间的记
  录均不能建立新
  turn，不存在误配风险。
  3. 新 turn
  拒绝与恢复入口契合规范
  ：新 turn
  已开始时，迟到的旧
  Stop/submit 明确拒绝为
  relay_requires_current
  _stop；界面显示“旧回合
  交付被拒”及结构化最后
  事实与原因；恢复入口严
  格绑定原
  attempt/session/fence/
  spec_rev/commit，使用
  稳定新
  request_id（recover-
  ${seq}），具备双击保护
  ，原 attempt
  失效时自动禁用且点击不
  发字节。
  4.
  红态与反证严密：修前版
  本在缺陷断言上精准失败
  ；4 个外部变异与 3
  个隔离变异均精准在预期
  断言上失败且无非预期
  error；T-159、T-
  160、T-133 回归全部
  PASS。
  5.
  任务卡边界与文案：改动
  完全在授权文件内，无越
  界修改；文案克制客观，
  不含营销腔。
  ──────
  ##
  二、逐项核对与发现（Fi
  ndings）

  ### 1.
  根因与实现架构（最小根
  因层 / 门禁完整性）

  • 核对结果：合格。
  •
  文件与行号：panes.ts:1
  205-1212、panes.ts:158
  5-1601、panes.ts:1024-
  1054、panes.ts:1804-18
  13
  • 分析：
      •
      修前在用户键入回车
      后，工作台在
      panes.ts:1168
      执行了 pane.
      claudePromptId =
      null 并覆写了
      pane.active。本次
      修复对 Claude Code
      移除了过早覆写行为
      ，让输入字节原样直
      达 PTY。
      • 在 Stop
      批次执行期间，如果
      收到带原 prompt_id
      的排队
      UserPromptSubmit，
      要求此前有未消费的
      真实终端 Enter
      写入（排除了括号粘
      贴包），记录
      claude_prompt_queu
      ed，不打断进行中的
      Stop
      交付；在原生转录完
      整写入且经严格校验
      （非
      sidechain、根工作
      目录、未使用的新
      promptId、时间戳有
      效、正文与排队输入
      一致等 12
      项约束）后，才在
      scan() 中正式更新
      claudePromptId。
      •
      caller.assertActiv
      e() 仍严格检查
      pane.
      claudePromptId ===
      turn，门禁要求完全
      未放松。新 turn
      一旦建立，旧
      caller 立即失效。


  ### 2.
  界面展示、恢复入口与防
  重策略

  • 核对结果：合格。
  •
  文件与行号：renderer.t
  sx:61-73、renderer.tsx
  :94-120、renderer.tsx:
  136-156
  • 分析：
      • isTurnRejection
      严格限制必须为
      delivery.state ===
      'rejected' 且
      delivery.
      native_turn_change
      d ===
      true，并在特定原因
      白名单内，正例（交
      付成功通过）绝不展
      示错误或恢复入口。
      •
      侧栏与窗格头部同步
      显示“旧回合交付被
      拒”，面板中陈述事
      实（任务尚无候选、
      原提交前 12 位、原
      attempt 前 8
      位、可折叠原交付记
      录）。
      •
      canRequestDelivery
      Check
      约束极严：必须为
      worker、原 attempt
      与合同版本匹配、无
      候选提交、无运行中
      草稿/active/interr
      upted、pane 处于
      idle。
      • 点击“请原 worker
      核对交付”后，前端
      发送带括号粘贴保护
      的终端文本给
      worker，指示
      worker
      核对原范围与
      worktree
      HEAD，指定 --
      request-id
      recover-${sequence
      } 显式交付；前端有
      recoveryInFlight.
      current 与
      recoveryWritten.
      current
      强防重机制，不调用
      operator
      submit，不重放旧
      request_id，不自动
      重试。


  ### 3.
  验收标准与测试证据链核
  对

  • 核对结果：合格。
  • 证据文件：
      • OUTSIDE-
      01：修前真实
      Electron
      红态复现通过（RED-
      01.json、RED-01.
      png）。
      • OUTSIDE-05/stop-
      input-positive.
      json 与 stop-
      input-positive-04.
      json：两场独立
      state 与随机
      sentinel 的正例 11
      项断言全部
      PASS，原 submit
      正常通过，输入原样
      进入下一
      turn，最终回到空闲
      。
      • OUTSIDE-
      05/stale-recover.
      json：新 turn
      建立后迟到旧 Stop
      被明确拒绝为
      relay_requires_cur
      rent_stop，恢复操
      作单次成功完成显式
      交付，12
      项断言全部 PASS。
      • OUTSIDE-
      05/stale-expired.
      json：attempt
      撤销后恢复按钮禁用
      且点击无字节发送，
      9 项断言全部
      PASS。
      • OUTSIDE-05/stop-
      input-baseline.
      json 与 stale-
      baseline.
      json：在修前版本上
      按预期失败于缺陷断
      言，red_reproduced
      =true，errors:
      []。
      • OUTSIDE-05 中 4
      个变异（mutant-
      old-stop、mutant-
      no-reason、mutant-
      no-recovery、stop-
      input-bad-
      caller）：均精准在
      预期断言上失败，er
      rors: []。
      • 回归测试（split-
      regression.
      json、review-
      regression.
      json、controller-
      regression.
      json）：全部
      PASS。
      •
      外部测试均运行在真
      实 Electron /
      daemon / PTY /
      Claude CLI
      环境，使用本地脚本
      化 Messages
      接口，真实供应商模
      型回合累计 0 /
      12，无凭据泄露与环
      境污染。


  ### 4. 边界与规范检查

  • 核对结果：合格。
  • 文件范围：改动集中在
  panes.ts、renderer.
  tsx、sidebar.
  ts、README.md
  及新增测试
  test_t157_*.{py,
  ts}，禁止修改的 .
  project-
  map/**、AGENTS.md、CON
  TEXT.md 等均未受污染。
  •
  文案检查：文案使用“原
  生 CLI
  已开始新回合，旧回合的
  交付请求被门禁拒绝”、“
  最后确定：旧请求未获接
  受；任务尚无候选”、“请
  原 worker
  核对交付”等，完全面向
  工程事实，无
  AI/营销词汇。
  ──────
  ## 三、微小观察项（P3
  建议，不阻断验收）

  • 发现项 1（P3 -
  代码防御）：
      •
      文件与行号：panes.
      ts:1032-1034
      •
      说明：在读取转录时
      执行了 lines.
      filter(Boolean).
      map(line => JSON.
      parse(line))。虽然
      通过 lines.pop()
      丢弃了最后可能未写
      完的一行，但在极端
      磁盘并发写入且非原
      子换行的情况下，若
      某中间行受损，JSON
      .parse 可能会抛出
      SyntaxError
      并由外层 catch
      记录。
      • 影响：当前
      Claude CLI
      追加写入均为原子行
      ，且在外层有异常捕
      获；测试中未发生异
      常。后续版本若需进
      一步提升极端容错能
      力，可在此处加上单
      行解析保护。

  ──────
  ──────
  ## 四、最终审查结论

  T-157
  的根因分析透彻，改动收
  敛于最小根因层，忠实落
  实了用户关于“CLI
  自身排队处理输入、不打
  断当前 Stop、新 turn
  开始后明确拒绝并给最小
  显式恢复入口”的裁定。
  门禁核对未作任何妥协，
  测试证据链（红态、正例
  、反例、恢复、失效、变
  异、回归）在真实
  Electron/CLI
  环境下完整闭环。

  T-157 REVIEW PASS

───────────────────────────
>
───────────────────────────
? for shortcuts```
