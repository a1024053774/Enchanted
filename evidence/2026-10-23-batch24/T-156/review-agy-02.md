# T-156-2 独立审查 01（agy）

- 审查员：agy，gemini-3.8-flash-high，Herdr 可见窗格 wG:p1N，只读副本，候选 79955cf83。

```
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-156b-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-156b-r1/prompt.txt)"
# pane wG:p1N started 2026-10-24T01:18:16Z candidate 79955cf8335dedb46c0f60642de09f5dfcf4d51a
```

- 结论 PASS，无 P0～P2 发现。

```text
      • 新增：test_t156_quality_host_credentials.py
      • 删除：workbench/tests/run_t082_boundary.py
      •
      删除：workbench/tests/test_t078_quality_host_
      bootstrap.py
      • 更新：HISTORICAL.md:45-56
  •
  审查方式：只读检查、静态代码分析与证据交叉核验，
  无 shell 执行、无文件写入。
  ──────
  ## 2. 检查项逐项对照（原 Bootstrap vs 新测试）
  对照原 test_t078_quality_host_bootstrap.py 第
  71～100 行（守卫 QualityCase.start_host →
  quality_chain_host.ts
  两代凭据隔离生命周期）与新测试
  test_t156_quality_host_credentials.py:103-117：
   … │ 原 bootstra… │ 新测试对应…  │ 等价性 / 增…
  ───┼──────────────┼──────────────┼───────────────
   1 │ 真实         │ 相同捕获逻辑 │ 完全等价：真
     │ QualityCase  │ ：assert     │ 实执行
     │ 两次 spawn   │ len(captured │ case.setUp()
     │ 捕获 (assert │ ) ==         │ (第1代) 与
     │ len(captured │ generation   │ case.start_ho
     │ ) ==         │ (L91)        │ st()
     │ generation)  │              │ (第2代)。
   2 │ 生成环境注入 │ generation-  │ 更强：拆为独
     │ 路径 (path   │ {1,2}-spawn- │ 立子项，失败
     │ ==           │ path         │ 时明确区分
     │ str(expected │ (L105)：断言 │ spawn
     │ _path))      │ env['A2A_OPE │ 路径错误与
     │              │ RATOR_CREDEN │ host
     │              │ TIAL'] ==    │ 内部错误。
     │              │ expected_pat │
     │              │ h            │
   3 │ Host         │ generation-  │ 更强：探针独
     │ 探针观测凭据 │ {1,2}-host-  │ 立读取环境变
     │ 路径         │ path         │ 量与路径，不
     │ (observed['p │ (L106)：断言 │ 因后续读取失
     │ ath'] ==     │ metadata['pa │ 败丢失路径元
     │ expected_pat │ th'] ==      │ 数据。
     │ h)           │ expected_pat │
     │              │ h            │
   4 │ 凭据文件物理 │ generation-  │ 更强：原测试
     │ 创建存在     │ {1,2}-       │ 隐式通过
     │              │ created      │ statSync
     │              │ (L107)：探针 │ 抛错体现，新
     │              │ 检查         │ 测试显式核对
     │              │ existsSync(p │ 文件在 socket
     │              │ ath) 为 True │ 启动前已落盘
     │              │              │ 。
   5 │ 凭据身份类型 │ generation-  │ 更强：脱敏直
     │ kind ==      │ {1,2}-kind   │ 接反序列化，
     │ "operator"   │ (L108)：断言 │ 避免 reader
     │              │ metadata['ki │ 因其他字段拒
     │              │ nd'] ==      │ 绝而掩盖 kind
     │              │ 'operator'   │ 缺陷。
   6 │ 凭据绑定状态 │ generation-  │ 完全等价：精
     │ state ==     │ {1,2}-state  │ 确匹配本
     │ str(case.sta │ (L109)：断言 │ fixture
     │ te.resolve() │ metadata['st │ 独立解析后的
     │ )            │ ate'] ==     │ 绝对 state
     │              │ case.state.r │ 目录。
     │              │ esolve()     │
   7 │ 凭据 POSIX   │ generation-  │ 完全等价：严
     │ 权限精确为   │ {1,2}-mode   │ 格提取
     │ 0600 (mode   │ (L110)：断言 │ statSync(path
     │ == 0o600)    │ metadata['mo │ ).mode &
     │              │ de'] ==      │ 0o777。
     │              │ 0o600        │
   8 │ 凭据可被真实 │ generation-  │ 完全等价：真
     │ readOperator │ {1,2}-       │ 实导入生产
     │ Credential   │ readable     │ reader
     │ 读取         │ (L111)：断言 │ 函数并在
     │              │ 探针调用真实 │ TypeScript
     │              │ reader       │ 运行时验证。
     │              │ 成功且       │
     │              │ result.retur │
     │              │ ncode == 0   │
   9 │ 外来启动环境 │ generation-  │ 完全等价：两
     │ 变量过滤     │ {1,2}-       │ 代各自独立检
     │ ('A2A_LAUNCH │ launch-filte │ 查外来注入的
     │ ' not in     │ red          │ sentinel
     │ env)         │ (L112)：断言 │ 环境变量被剔
     │              │ 'A2A_LAUNCH' │ 除。
     │              │ in env 为    │
     │              │ False        │
   1 │ 真实         │ cleanup-     │ 更强：原
   0 │ close_fixtur │ failures     │ bootstrap
     │ e            │ (L116)：断言 │ 忽略了
     │ 内部清理状态 │ case.close_f │ close_fixture
     │              │ ixture() ==  │ ()
     │              │ []           │ 的返回值；新
     │              │              │ 测试显式验证
     │              │              │ 清理错误列表
     │              │              │ 为空。
   1 │ 归档前凭据物 │ capabilities │ 完全等价：两
   1 │ 理文件已被移 │ -removed-    │ 代 fixture
     │ 除           │ before-      │ 目录在退出时
     │              │ archive      │ 确无任何残留
     │              │ (L117)：断言 │ 凭据文件。
     │              │ list(case.ro │
     │              │ ot.glob('ope │
     │              │ rator-       │
     │              │ *.credential │
     │              │ .json')) ==  │
     │              │ []           │
   1 │ 旧 runner    │ 退役并随旧   │ 符合授权与裁
   2 │ 失败诊断复制 │ runner       │ 定：COVERAGE.
     │ (failed-run- │ 删除，不设平 │ md、HISTORICA
     │ copies-host- │ 行包装       │ L.md
     │ stderr)      │              │ 明确指出该项
     │              │              │ 属旧 runner
     │              │              │ 自身辅助机制
     │              │              │ ，无生产业务
     │              │              │ 契约，按授权
     │              │              │ 退役。
  结论：原 bootstrap 第 71～100 行守护的 11
  项核心断言全部迁入新测试，并按第 1 代、第 2
  代与清理阶段细化为 18
  项明确命名的独立断言，断言粒度与诊断性显著强于原
  测试；旧 runner 的日志复制探针按既定决策退役。
  ──────
  ## 3. 红态与隔离反例（7 个变异）核验
  核对 run_credentials_suite.py 中的 7 个变异实现与
  OUTSIDE-02.json 真实执行结果：
   变异名… │ 注入目… │ 预期命… │ 实际执… │ 是否代…
  ─────────┼─────────┼─────────┼─────────┼─────────
   missing │ workben │ generat │ exit    │ 是。代
   -creati │ ch/test │ ion-1-  │ 1；命中 │ 表 host
   on      │ s/quali │ created │ generat │ 启动前
           │ ty_chai │         │ ion-1-  │ 未创建
           │ n_host. │         │ created │ 凭据文
           │ tscreat │         │ 等 10   │ 件的缺
           │ eOperat │         │ 项断言  │ 陷实现
           │ orCrede │         │         │ 。
           │ ntial(r │         │         │
           │ oot); → │         │         │
           │ ""      │         │         │
   wrong-  │ workben │ generat │ exit    │ 是。代
   kind    │ ch/src/ │ ion-1-  │ 1；命中 │ 表角色
           │ credent │ kind    │ generat │ 凭据签
           │ ials.ts │         │ ion-1-  │ 发权限
           │ kind:   │         │ kind、r │ 降级或
           │ "operat │         │ eadable │ 混淆。
           │ or" →   │         │ 、clean │
           │ kind:   │         │ up      │
           │ "worker │         │         │
           │ "       │         │         │
   wrong-  │ workben │ generat │ exit    │ 是。代
   state   │ ch/src/ │ ion-1-  │ 1；命中 │ 表跨
           │ credent │ state   │ generat │ fixture
           │ ials.ts │         │ ion-1-  │ /跨租户
           │ state:  │         │ state、 │ state
           │ realpat │         │ readabl │ 路径篡
           │ hSync(r │         │ e、clea │ 改或泄
           │ oot) →  │         │ nup     │ 露。
           │ 固定外  │         │         │
           │ 来路径  │         │         │
   wrong-  │ workben │ generat │ exit    │ 是。代
   mode    │ ch/src/ │ ion-1-  │ 1；仅命 │ 表权限
           │ credent │ mode    │ 中      │ 掩码不
           │ ials.ts │         │ generat │ 合规；
           │ mode:   │         │ ion-1-  │ 此时
           │ 0o600 → │         │ mode 与 │ reader
           │ mode:   │         │ generat │ 仍可读
           │ 0o400   │         │ ion-2-  │ （400
           │         │         │ mode    │ 可读）
           │         │         │         │ ，精准
           │         │         │         │ 检验了
           │         │         │         │ mode
           │         │         │         │ 独立检
           │         │         │         │ 查而非
           │         │         │         │ reader
           │         │         │         │ 粗暴报
           │         │         │         │ 错。
   missing │ workben │ capabil │ exit    │ 是。代
   -cleanu │ ch/test │ ities-  │ 1；精准 │ 表清理
   p       │ s/test_ │ removed │ 命中    │ 逻辑遗
           │ quality │ -before │ capabil │ 漏凭据
           │ _chain_ │ -archiv │ ities-  │ 物理删
           │ e2e.pyc │ e       │ removed │ 除的泄
           │ redenti │         │ -before │ 露缺陷
           │ al.unli │         │ -archiv │ 。
           │ nk() →  │         │ e       │
           │ pass    │         │         │
   wrong-  │ workben │ generat │ exit    │ 是。代
   generat │ ch/test │ ion-2-  │ 1；精准 │ 表两代
   ion-    │ s/test_ │ spawn-  │ 命中    │ 凭据路
   path    │ quality │ path    │ generat │ 径隔离
           │ _chain_ │         │ ion-2-  │ 混淆或
           │ e2e.py  │         │ spawn-  │ 代际计
           │ 第 2    │         │ path、g │ 数错乱
           │ 代路径  │         │ enerati │ 。
           │ 由 02   │         │ on-2-   │
           │ 篡改为  │         │ host-   │
           │ 03      │         │ path    │
   inherit │ workben │ generat │ exit    │ 是。代
   ed-     │ ch/test │ ion-1-  │ 1；精准 │ 表环境
   launch  │ s/test_ │ launch- │ 命中    │ 隔离漏
           │ task_ca │ filtere │ generat │ 过滤外
           │ rds_e2e │ d       │ ion-1-  │ 来身份
           │ .py环境 │         │ launch- │ 的越权
           │ 过滤放  │         │ filtere │ 风险。
           │ 行      │         │ d、gene │
           │ A2A_LAU │         │ ration- │
           │ NCH     │         │ 2-      │
           │         │         │ launch- │
           │         │         │ filtere │
           │         │         │ d       │
  结论：7
  个变异均在隔离副本中实施，变异目标精准对应核心安
  全与隔离机制，所有变异在未修代码上均导致测试退出
  码为 1
  且首要失败点精确落在预期断言上，无假红、无泛化崩
  溃。
  ──────
  ## 4. 关键审查要点核实
  ### 1. 根因与最小改动原则
  • 根因：原 test_t078_quality_host_bootstrap.py 与
  run_t082_boundary.py
  因存在唯一有效直接检查（凭据创建与两代隔离）而无
  法在 T-156-1
  直接删除；用户裁定“迁移后删”后，将该唯一直接守护
  范围迁入专用测试并删除旧文件是最小根因解法。
  • 改动层：全量 diff 仅涉及 1 个新增测试文件、2
  个旧文件删除和 1 个 Markdown 文档更新。
  • 无不良代码味道：无吞异常、无 fallback、无
  retry、无兼容层垫片（shim）、无平行 runner 或
  API。
  ### 2. 验收证据与期望值来源
  • 证据链完整：主控在沙箱外真实运行 RUN-OUTSIDE-
  02.py，完整捕获套件正常通过、7
  个变异拒绝、现行导入无异常、历史脚本扫描与
  project-map 状态，原始证据与临时运行现场已按 T-
  088 归档至 /Volumes/WD-Elements/a2a-
  evidence/2026-10-23-batch24/T-156/。
  • 期望值独立性：断言中的
  'operator'、0o600、operator-01.credential.
  json、A2A_LAUNCH
  过滤等期望值全部硬编码自规范与契约，不是从产品代
  码输出抓取生成。
  ### 3. 修改边界与文案规范
  • 修改边界：未修改任何 workbench/src/**
  产品代码，未修改其他现行测试文件中的任何已有断言
  ，未修改 .project-map/**。严格处于任务卡
  card-2.md 允许的边界内。
  • 文案：HISTORICAL.md:45-56 与测试代码 docstring
  叙述平实客观，准确记录去向、退役边界与裁定理由，
  无夸大或营销口吻。
  ### 4. 现行入口导入完整性与历史脚本裁定
  • 现行入口扫描：对 workbench、scripts、acceptance
  执行 git grep 查找 run_t082_boundary 与
  test_t078_quality_host_bootstrap，匹配结果为
  0（exit code 1）。
  •
  受影响测试实测：test_quality_chain_e2e、test_t082
  _review_boundary_e2e、test_t156_quality_host_cred
  entials 及 T-152 run_suite.py 均正常 import /
  加载，exit code 0。
  • 历史脚本处理：evidence/2026-10-16-batch16/T-
  090/run-host.py:215 仍含历史 from
  run_t082_boundary import
  materialize。经执行主控裁定（#42）：该文件属日期
  归档历史脚本，复跑须检出对应历史
  commit，不属现行测试入口；按规则不作修改并在
  HISTORICAL.md:56
  正式载明。该裁定符合项目既定规范。
  ──────
  ## 5. 发现清单与缺陷评级
  经过系统性复核，针对各文件行号评定如下：
   文件与行号 │  严重度   │ 现象与评估 │ 处置建议
  ────────────┼───────────┼────────────┼───────────
   run-host.p │ P3（已知  │ 历史证据脚 │ 按历史归
   y:215      │  记录）   │ 本保留对已 │ 档保留，
              │           │ 删除模块的 │ 不影响本
              │           │ 导入。该脚 │ 次交付合
              │           │ 本非现行测 │ 入。
              │           │ 试入口，且 │
              │           │ 执行主控   │
              │           │ #42        │
              │           │ 已作保留原 │
              │           │ 样裁定并在 │
              │           │ HISTORICAL │
              │           │ .md        │
              │           │ 明确说明。 │
  未发现任何 P0、P1、P2
  级别的缺陷、检查放松、断言丢失或回归风险。
  ──────
  ## 6. 审查结论
  候选分支 79955cf83 完整落实了用户 2026-10-24
  “迁移后删”的明确授权：原凭据核心守护检查逐项迁移
  至现行测试且断言更强，7
  个隔离反例真实有效且命中预期断言，产品代码零修改
  ，其他测试断言零放松，删除后现行入口导入完整无损
  ，证据记录完备。
  T-156b REVIEW PASS
──────────────────────────────────────────────────────
>
──────────────────────────────────────────────────────
? for shortcuts                Gemini 3.8 Flash · high
```
