# A-15 完整只读 harness 与续行命令

源码版本见 manifest.json：harness 与实际业务源码分别记录，后者仍为 dedd4f66bc424610183cbff2d7114e991483e1c6。原 58 文件中仅三条只读 caller 改动，其余 55 文件逐字节相同，新增 helper/恢复器/源校验器/测试入包，共 65 文件。每条命令先完整校验本包，再运行原入口；P1 显式使用本包的 source-materials。不要再用旧 reader 命令，或删除旧 source 检查。

**本包只准备，尚未读 A-15 新屏、恢复或 Enter。** commands/ 中每个文件可由主控单独 `sh <绝对路径>` 执行，不能整目录批量执行；set -e 在任何失败时停止。签字只由主控在完整读回后写入实际批准文件。

## E4（同一实际 dispatch / permission_event）

1. `commands/E4-01-READ-02.txt`：新 -02 完整只读屏幕；读到 EOF 且 total 不变才写 screen.bin。
2. `commands/E4-02-RECOVER-REFERENCE.txt`：确认旧 65,536 字节原件是完整新原件的严格前缀；追加 `phases/E4/screen-recovery-02/`，不改旧 dispatch、event、原屏、失败 -01 或未签 approval-01。生成实际未签 `phases/E4/permission-approval-02.json`。旧 dispatch id/seq/event 逐项保留，只有只读参考/完整性字段新增。
3. `commands/E4-03-READ-03-CMP.txt`：再次完整读新 -03，与恢复目录里的独立完整参考作全文件 cmp；不相同就停。
4. 主控检查完整命令、实际 stop id 与 ❯ 1. Yes，签生成的 approval-02。包内 E4-permission-approval-02-template.json 只供预审，不能拿模板代替已验证恢复后的实际文件。
5. `commands/E4-04-CHECK-ONLY.txt`：可选只读预检，停止在 build/窗口/键入之前。
6. `commands/E4-05-ENTER.txt`：一次 awaited Enter；`commands/E4-06-READBACK.txt`：之后只 collect。二者必须分开，Enter 后仍按原协议结算幂等 ack、实际 Stop/relay，不能重复送键。

## E5 与 E6

E5 phase approval 仍在 executor P1 的 phases/E5/approval.json，签字栏保持空；主控另签后，依次执行 E5-01-START → E5-02-READ-01-CMP（-02 仅作备用只读）→ E5-03-PREPARE-PERMISSION。新 phase_driver 自始保存完整原件与页范围，故 E5 不再沿用旧截断方式。主控读屏核对、签实际 permission-approval-01 后，E5-04 可只读预检、E5-05 才一次 Enter、E5-06 collect。

E6 phase approval 也仍为空；最后 E6-01-START → E6-02-READBACK，无工具、无 Enter。所有自动根继续来自真实 feedback/wake，dispatch.seq 按实际记录，不固定阶段号，不重派发业务。

当前剩余实际 POST：E4 tool_result 1 + E5 2 + E6 1 = 4；全场预算仍 ideation 4 roots/6 POST、executor 6/11，模型 0。E4 完成后 E5 的待批 HTTP 仍有 180 秒限制，超时/409/超预算即停，不重试。

## 复验与限制

本地真实 reader 参数入口的红绿/反例已保存，身份使用 spy；独立 /bin/ps 在沙箱被拒。主控可先运行 `../09b-a15-reader-fix-01/OUTSIDE-RECHECK-COMMAND.txt` 的完整命令，用自己前台 Python 的真实身份重跑隔离测试。该脚本不访问 A-15 root，不启动 CLI/API/daemon/窗口，fixture 用完删除。外侧复验本轮未运行。

历史原屏审计、完整测试范围、准备期失败与独立审查请求均在 ../09b-a15-reader-fix-01/。E1/E2/E3/I3 已有完整 gate total 与相同原屏；I1 只有 16,322 字节和同值 Electron offset，缺直接 total 证据，保持 INCOMPLETE 交主控判断。原结论没有改写。
