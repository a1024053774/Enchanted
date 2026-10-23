# T-148 独立审查 01（agy）

- 审查员：agy 1.4.6，模型 gemini-3.8-flash-high，Herdr 可见窗格 wG:pX，交互 auto 模式（只用读文件工具），只读副本，候选 2d6e8e359。
- 启动 argv：

```
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-148-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-148-r1/prompt.txt)"
# pane wG:pX started 2026-10-23T17:26:55Z
```

- 审查后核对：候选副本 git status 0 行改动。结论 PASS，三条 P3：审查员 argv 取自产品有“实现自证”风险，已由 test_t141_reviewer_contract.mjs 与 8 个变异独立覆盖；receiver 保留 bracketed paste；历史旧契约断言只清点上报未越权修改。

## 窗格中的报告原文

```text

○ Thought for 4m 5s (Examined the documentati...)
● Explored 20 files (full...) (ctrl+o to expand)
▸ Thought for 45s

   a2a T-148 独立审查报告

  审查对象：T-148（T-141
  合入后过时的测试夹具修复：审查员 argv 与模拟
  Codex 启动屏）
  候选代码版本：2d6e8e359dee7dba6cd9496537c5f7f
  e34a538c0（分支起点 cca4f8beb）
  审查模式：只读独立审查（未运行任何 shell
  命令，未修改或创建任何文件）
  ──────
  ### 一、改动范围与断言完整性核对

  1. 改动范围严格受限于夹具与注释：
      • 全量差异（full.diff 共 134 行）仅涉及 5
      个测试文件，产品代码（src/、roles/
      等）零改动。
      • 3 处纯注释修改：
          •
          legacy_quality_driver.py:78-82：说明
          T-141 后 reviewer
          候选副本受限打开后，提示派发需等待
          native Codex 就绪包。
          • run_t112_native.py:207-211：标明
          worker 需 restricted-open 事件为 T-
          127 历史观察条件，T-141 已信任 worker
          不再产生该事件。
          •
          t112_reviewer_record.mjs:55-59：明确
          受限打开后需等待 native readiness
          才释放输入。
      • 2 处夹具适配：
          •
          t145_mouse_receiver.c:48-56：模拟已信
          任 Codex 启动，保留 bracketed paste
          并发送 native idle 就绪包。
          •
          test_t146_reviewer_hooks.mjs:14-77：
          动态捕获产品启动 argv，替换旧硬编码
          argv；changeSettings 改由定位 --
          settings 计算下标。

  2. 断言、检查名、超时与变异列表完全未动：
      • test_t146_reviewer_hooks.mjs:57-76：
          • 原断言
          assert.equal(validate(launch).id, 're
          viewer') 与 assert.throws(...)
          完全一致。
          • 检查名
          approved_session_end_hook_accepted 与
          8
          项变异拒收检查名（_rejected）完全一致
          。
          • 全部 8
          种变异（missing_session_end、extra_ho
          ok、foreign_session_end_command、sess
          ion_end_timeout、shell_write_expansio
          n、edit_expansion、changed_cli_flag、
          git_configuration）及其内部期望（如
          timeout: 11、GIT_CONFIG_COUNT = '1'
          等）未作任何删改。
      •
      test_t145_mouse_reports_e2e.py：文件完全
      未修改，原断言、超时（30s /
      10s）、检查名及 --mutant record-reports /
      --mutant drop-reports 变异完全保留。

  ──────
  ### 二、产品代码生成审查员 argv
  的独立性与风险评估

  1. 测试架构与独立性分析：
      • 本测试的被测单元是安全门禁
      A2AGates.prototype.reviewLaunch，而非启动
      器 Panes.prototype.createPane。
      • core.ts 中的 reviewLaunch
      包含完全独立的硬编码规范校验：对固定标志
      序列、dontAsk、AskUserQuestion
      禁用、permissions 严格集合、sandbox
      网络与额外写入目录、7 项 hooks
      结构、signal 尾缀与 launch.id
      对应关系均有自包含校验。
      • 若产品生成的 argv
      本身有错：validate(launch) 将直接抛出
      review_launch_boundary 导致测试在第 57
      行立即失败，绝不会照样通过（这正是合并回
      归 05 报错的机理）。
      • 门禁变异测试的独立性：8
      项负向变异均直接在候选对象上修改属性和
      JSON 字符串，未经过 Panes.
      createPane。即使基础 argv
      由产品生成，测试验证门禁拦截恶意篡改（扩
      权、超时、伪造钩子等）的能力依然完整、独
      立。
  2. 风险评估与独立证据覆盖：
      • 风险场景（P3）：当基准 argv
      由产品生成时，若未来 Panes 与 Gates
      发生协同偏离（例如双方同时放开某项非预期
      权限），test_t146
      将不再充当静态字面量基准。
      • 独立证据覆盖：
          •
          test_t141_reviewer_contract.mjs：独立
          覆盖 Claude Code 与 Codex 两种 CLI 的
          reviewer 启动契约，并包含
          mcp_hook_matches_native_tools、mcp_ho
          ok_missing、foreign_mcp_configuration
          、trust_override_* 等全套独立变异。
          • test_t141_launch_contract.mjs 与
          test_t141_loosened_limits_e2e.py：提
          供端到端真实沙箱与启动参数的交叉覆盖
          。


  ──────
  ### 三、新 receiver 就绪包契约符合性与 T-145
  被测行为验证

  1. 真实 Codex 协议符合性：
      • 真实 Codex
      启动探针（trusted.json:26）实测表明：受信
      任的 Codex 正常启动完成时向 PTY 发送
      \u001b]7501;
      state=idle:app=codex\u001b\\。
      • 产品逻辑 panes.ts:927-943 正则匹配该
      OSC 7501 序列，并在满足未启动条件时标记
      pane.started = true 并触发 this.
      drain(pane) 派发首个输入。
      • 契约测试
      test_t141_startup_signal.mjs:25-34
      验证了拆包支持及仅限首次准入的协议特征。
      • t145_mouse_receiver.c:53-56 发送
      \x1b[?2004h\x1b]7501;
      state=idle:app=codex\x1b\\，完全契合真实
      Codex 行为。
  2. T-145 核心被测行为验证的真实性：
      • 旧 receiver 发送 › 1. Open restricted
      导致合并回归超时，是因为 T-141 后 worker
      默认已信任且仅在收到 native idle
      包后才释放派发。
      • 握手就绪仅是任务进入的前置条件；T-145
      的真实核心被测行为是在收到派发后，CDP
      注入鼠标移动、滚轮与焦点切换时，验证
      daemon 不产生 human_intervention 或
      user_inputs 记录。
      • MANIFEST.json 的独立运行证据证实：
          • t145-green：16 项 checks
          全部通过（PASS，exit 0）。
          • t145-red-reverted（反向补丁完全还原
          T-145 产品修复）：准确在断言
          mouse_focus_do_not_create_records
          处抓获失败（exit 1），且前置
          receiver_native_identity_bound
          等均正常通过。
          • t145-mutant-record：准确失败于
          mouse_focus_do_not_create_records（ex
          it 1）。
          • t145-mutant-drop：准确失败于
          超时：三次移动均到 PTY（exit 1）。
      • 证明 T-145
      的业务保护逻辑和错误捕获能力完全未受影响
      ，依然得到真实、严格的验证。

  ──────
  ### 四、审查发现项列表

  • 发现项 1：
      •
      位置：test_t146_reviewer_hooks.mjs:105-11
      6
      • 严重度：P3（低风险 / 架构观察）
      • 失败场景：若未来 Panes.createPane 与
      A2AGates.reviewLaunch
      发生非预期的协同属性漂移，因基准输入动态
      取自产品，该测试单体将无法作为第三方静态
      规范提出异议；且 c.argv[11] = '--unknown'
      依赖下标位置（当前为 --
      disallowedTools，篡改后仍能被拒绝）。该风
      险当前已有
      test_t141_reviewer_contract.mjs 及 8
      项变异充分覆盖。
  • 发现项 2：
      • 位置：t145_mouse_receiver.c:53-56
      • 严重度：P3（良好实践提示）
      • 失败场景：若模拟 receiver 仅输出 native
      idle 就绪包而遗漏 \x1b[?2004h（开启
      bracketed paste），daemon
      派发的首个任务输入将无法被以粘贴格式安全
      解析。当前实现正确保留了
      \x1b[?2004h，运行符合预期。
  • 发现项 3：
      • 位置：run_t112_native.py:207-211 等 3
      处注释与 ISSUE-stale-oracles.md
      • 严重度：P3（范围外历史遗留清点）
      • 失败场景：代码库中其他历史测试（如
      test_t112_execution.mjs
      要求网络关闭、controlled_quality_pty.ts
      仅模拟 restricted
      屏等）仍包含旧启动契约。T-148
      未越权直接修改这些历史断言，而是如实记录
      并上报 issue，处理方式符合职责边界要求。

  ──────
  T-148 REVIEW PASS
```
