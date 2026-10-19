# T-093 清理 PermissionError 诊断与非特权观察器交接 09

**INCOMPLETE：已保留外部失败并完成局部红绿；新观察器和实际删除等待主控沙箱外执行。**
task T-093 / attempt a1，worker s16-t093；受管 session 67f986cc-92e4-4089-9c22-802a1143b645，native session 01a14ae2-a3df-7731-a7b0-1b679b3bce95，launch launch-45148b6732394eccab3b21224b238513。
候选绑定最后 FROZEN 完整 SHA；冻结不代替 submit、独立验收或集成。

实现冻结 d355efac68c74ca8af7fe9bd8fea5a98f1968e9c 的只读审查为 INCOMPLETE，原文
[CLEANUP-OBSERVER-REVIEW-01.md](CLEANUP-OBSERVER-REVIEW-01.md)。13 个纯内存探针未发现本次边界内的已证实违约，实际 OS 能力仍未知。
审查后清理实现保持不变；另补实际 main 的模拟失败收据检查，cleanup-cli-red-01 用旧实现缺失的 operation/path/errno 命中业务断言，green-01 通过。
它覆盖实际 JSON 写入路径，仍用模拟操作替代权限边界，不替代下列沙箱外检查。

## 已确认与未知

主控 #97：请求 08 的七个清理均 rc 2、PermissionError、root_removed=false；后续完整链 -06 未执行。
[cleanup-05-inspection.json](cleanup-05-inspection.json) 保留七份旧结果及本轮只读元数据检查。

worker UID 501 与所有夹具 owner 一致。七根均为 0700，遍历 495 项元数据没有 0000、异主、flags、socket／FIFO 等异常；
ls -ldeO 成功，未见 ACL 条目。没有读取认证正文，也没有改权限或删除任何保留夹具。

共同流程中的 /bin/ps 实际是 root-owned 4755；/usr/bin/pgrep 为 0755、无 setuid／setgid。
初始根没有旧 PID 元数据仍同样失败，因此受保护环境中启动 setuid ps 是主要嫌疑。
旧结果没有路径或 errno，尚不能把这点写成已捕获的原次异常；本次 --inspect-only 会在同一 X 下只读重现旧启动，直接记录其 path／errno／mode。

## 修正边界

默认清理路径只使用 /usr/bin/pgrep，不尝试执行 ps、不复制系统二进制，也不 chmod。
先核对观察器无 setuid／setgid；用 -a -f -U 当前 UID 查询匹配的 R/G，输出仅 PID，不读取／保存其他进程的原始参数。
0 代表非空匹配、1 代表无匹配，其他退出码、异常输出或查询失败均拒绝删除，stderr 作为错误摘要保留。

一个无模型 Python 子进程只睡眠并携带 R/G 参数标记，不运行 R 驱动、Git 或供应商 CLI。
两次查询必须都看到它；随后终止、回收并确认其组已消失，再查真实 R/G。看不到对照或回收未确认都拒绝删除。
对照的 20 秒硬期限在 exec 前设置；所有观察器／对照子进程继承 X，并脱离调用者进程组。
X 的 HOME 禁写、禁网络、禁 Security 和既有 fork 权限不变；产品 C/F/D/V、Git 驱动及所有业务断言均未变。

入口仍只接受 retained-cleanup-scope-05.json 的七个固定根；已有结构、UID、D 删除收据与旧 PID／组检查全部保留。
没有放宽权限的必要，本次 permission_changes 始终为 []。权限或特殊文件若实际阻止操作，会原样停下，不能靠跳过／chmod 冒充成功。

失败结果新增 operation、path、errno，以及可用的 PID／组／mode／uid／flags／文件类型。
进程查询错误的 path 是实际可执行文件，信号 0 错误以 PID 为目标；rmtree 回调保留完整失败路径和原始相对 os_filename。
os.walk 的遍历错误不再吞掉；根的缺失核对遇到权限错误也不能判已删除，且不覆盖先前删除错误。

## 先只检查一个根，不删除

```sh
python3 -I -S -B workbench/tests/cleanup_t093_retained_fixture.py \
  --root /private/tmp/t093-chain-_7290n4q \
  --output /private/tmp/t093-cleanup-inspect-06.json --inspect-only
```

期望 rc 0、status=PASS、action=inspect_only、deletion_attempted=false、root_removed=false、permission_changes=[]。
setup_quiescence 必须 complete=true，positive_control 的 R_seen/G_seen/exit_confirmed 全 true，matching_processes=[]；observer 应为非 setuid 的 /usr/bin/pgrep。
legacy_ps_diagnostic 单列旧启动结果；若它返回 PermissionError，path／errno 会给出准确来源。这是诊断，不影响新的观察器判定，也不是删除成功。

若主结果仍 INCOMPLETE，保留新 JSON，回传 operation／path／errno、returncode／stderr 或 control_cleanup；停止后续清理及完整链，不能重复覆盖结果。

## 检查通过后逐根删除

每条分别执行，均使用新输出，程序会重新核对停机状态。期望 rc 0、action=delete、deletion_attempted=true、root_removed=true；否则保留根和错误原件。

```sh
python3 -I -S -B workbench/tests/cleanup_t093_retained_fixture.py --root /private/tmp/t093-chain-_7290n4q --output /private/tmp/t093-cleanup-06-01.json
python3 -I -S -B workbench/tests/cleanup_t093_retained_fixture.py --root /private/tmp/t093-chain-l2qtw5kt --output /private/tmp/t093-cleanup-06-02.json
python3 -I -S -B workbench/tests/cleanup_t093_retained_fixture.py --root /private/tmp/t093-chain-4ix7bnvu --output /private/tmp/t093-cleanup-06-03.json
python3 -I -S -B workbench/tests/cleanup_t093_retained_fixture.py --root /private/tmp/t093-chain-jlyq2vja --output /private/tmp/t093-cleanup-06-04.json
python3 -I -S -B workbench/tests/cleanup_t093_retained_fixture.py --root /private/tmp/t093-chain-kyew9xey --output /private/tmp/t093-cleanup-06-05.json
python3 -I -S -B workbench/tests/cleanup_t093_retained_fixture.py --root /private/tmp/t093-chain-wx413hum --output /private/tmp/t093-cleanup-06-06.json
python3 -I -S -B workbench/tests/cleanup_t093_retained_fixture.py --root /private/tmp/t093-chain-_4gt5f2t --output /private/tmp/t093-cleanup-06-07.json
```

这些根含合成认证源，不原样归档；删除仍是整根删除，依赖链接只 unlink，不跟随。
全部清理成功后，按请求 08 的 chain-06 命令先运行 none；rc 0 与 PASS JSON 成立后，才继续五项变异和独立核对器。
外部 V 的旧通过仅用于未变的入口事实，不能替代本候选完整链。

局部证据：cleanup-errors-red-03 用旧冻结源码拒绝缺失的六项诊断；green-03 通过，包括 FIFO 不打开、rmtree 完整路径和原 ps 错误模拟。
cleanup-observer-red-01 拒绝旧观察器；cleanup-quiescence-green-05 覆盖匹配对照、R/G 活动、观察器失败及不可见对照的拒绝。
retained-cleanup-local-06 的六项合成场景含 inspect-only 不删除。进程均为模拟，真实 OS 执行／现有根删除仍未发生。
没有真实供应商 CLI、认证读取、真实上游或模型回合；整票 INCOMPLETE。
