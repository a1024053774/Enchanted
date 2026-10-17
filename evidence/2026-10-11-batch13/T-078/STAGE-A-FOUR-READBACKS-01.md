# Stage A 四份收据绑定（主控 #344）

本次仅改 Stage A 的测试工具/批准与冻结材料，不改业务代码、验收文件、原变异或 protocol；不运行 Stage A、角色 CLI、API、daemon、目标或模型。

两场都按相同顺序绑定以下实际文件，静态包与批准件的列表必须完全相同：

1. `review-followup-regressions-02/result.json`：保留原 `INCOMPLETE`。
2. `review-followup-mutant-cas-03/result.json`：CAS 分类器修复后的指定原用例补跑 PASS。
3. `review-followup-mutant-lock-04/result.json`：补齐原先未运行的 lock，PASS。
4. `merge-main-4-t078-regressions-01/result.json`：T-078 自身四段 PASS。

## 显式处理 02 的历史失败

`run-09b.py::validate_regression_readbacks` 不把 02 当成 PASS，也不忽略其状态。它要求状态为 INCOMPLETE、error 为 AssertionError，七个阶段恰为原五组、fence、CAS；前六段全部通过，最后只停在 CAS 分类，且尚无 verdict。它读取 02 对应 Git 版本的旧分类器，核对 traceback 中 `verify_mutant` 的行号确为旧 claim 匹配断言，并核对旧的两个 CAS 标签。五组子报告必须执行齐 8/9/18/1/15，无 error/skipped/未执行/收集错误；原 CAS 子测试必须是指定方法的 BUSINESS_RED。

cas-03、lock-04 各自必须只有指定补跑、顶层及 verdict PASS、子进程 exit1、原方法恰一项失败且零 error/skipped、business-red、实际 loaded_core 与子报告一致。T-078 自身 pending/startup-domain/startup-entry/worker 四段须全部 PASS。每份收据都核对测试提交是当前 HEAD 的祖先。

Stage A 输出会保存 `regression_validation`：02 原状态、只接受的历史失败原因、CAS 替代路径、lock 补齐路径、四个实际测试版本和源码核对范围。缺任一收据、其他失败、错方法或错批准列表均在建运行 root/任何运行进程之前拒绝。

## 源码与冻结

业务和测试自原 source `1b86f2c91c781cd4867227230185fc2a2c145aeb` 未变。回归源码核对继续覆盖全部 workbench/acceptance/scripts，以及原冻结闭包其余成员。唯一单列的差异为本次 `run-09b.py` 的 Stage A 收据预检；其他驱动、reader、API、角色启动、protocol 均不能变化。

该预检本身属于启动包的冻结源码，因此不放宽新包的完整性检查。旧 `09b-executable-materials-16` / `09c-executable-materials-01` 保留；用同一个标准 prepare 生成新 `09b-executable-materials-16-02` / `09c-executable-materials-02`，新包每成员与源码提交逐字核对，且相对旧包必须只有 `run-09b.py` 一项变化。两份当前未签批准件和相关命令改指新包；场景仍 A16/09C，预算、prompt、阶段顺序、原件保留与清理契约不变。

## 本地证据与边界

- [旧入口红态](stage-a-four-readbacks-red-01/result.json)：两个原 Stage A 预检都因 02 非 PASS 而拒绝；只在内存构造测试批准，无现场签字、root 或 spawn。
- [候选检查](stage-a-four-readbacks-green-01/result.json)：真实保存收据及 12 个反例共13项 PASS，文件反例只在一次性 `/private/tmp` 中，结束删除。
- [已知坏预检](stage-a-four-readbacks-bad-guard-01/result.json)：仅内存删去历史状态/error 检查，错误接受其他错误和伪称 PASS 的历史报告，被同一断言抓到；未改变原门禁变异。

新包生成及最终真实预检结果追加保存在 `stage-a-readback-rebind-01/` 与 `stage-a-four-readbacks-final-01/`。批准字段保持空；完整预检的正例只使用内存测试批准，不写任何实际批准或启动现场。
