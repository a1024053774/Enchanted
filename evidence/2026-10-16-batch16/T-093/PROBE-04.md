# T-093 probe-04 端口规则修正（2026-10-17）

状态：INCOMPLETE。带端口 profile 已通过本机编译器；真正 `--version` 启动和认证路由仍等主控在沙箱外验证。
task T-093 / attempt a1 / ready_rev 1 / session `67f986cc-92e4-4089-9c22-802a1143b645`。
起点 `f8c1fb7015274bcc729c4ef5bb6eebc307795ca5`；本轮未提供新 fence 值。

目标：修正 profile 编译错误，在读取凭据前独立验证带端口 profile 的 CLI 启动与限制。
非目标：允许外连、读取真实 HOME、改认证来源、忽略清单差异、产品实现或真实模型回合。

## 根因与证据

- **measured（probe-03）**：无 BASE_URL 的状态查询成功；带端口 profile 下 `--version` exit 65，stdout 空，stderr 为 sandbox_exec 前缀。
- **measured（本机编译器）**：`sandbox_compile_string` 接受无端口 profile；拒绝原数值主机规则，诊断为固定模板
  `host must be * or localhost in network address`。换成 tcp 但保留数值主机同样失败，问题不是 JSON 格式。
- **measured**：使用 `remote tcp4`、`localhost` 和明确端口时编译成功；1、45678、65535 三个端口均已验证。
- 编译检查环境：macOS 27.0、kernel 27.0.0、Python 3.9.6；本轮直接调用已安装的系统库，不安装依赖。
- 未调用 `sandbox_apply`，未启动真实 CLI，未读取凭据。编译输入只含固定的合成 /private/tmp 路径及 /usr/bin/true，
  所以保存的固定编译诊断不含真实配置、邮箱或凭据。原红态见 `profile-compile-red-04.json`。
- API 声明参考 [WebKit SandboxSPI.h](https://github.com/WebKit/WebKit/blob/main/Source/WTF/wtf/spi/darwin/SandboxSPI.h)；
  该头文件将编译与应用分开。本机实际编译结果是语法结论的依据，不能替代实际应用/运行时拦截证据。

新规则只有：

```text
(allow network-outbound (remote tcp4 "localhost:<本次绑定端口>"))
```

保留 `deny network*` 和所有文件、Mach、fork 限制；没有 `*` 主机、通配端口、DNS 或其他外连许可。
TCP4 限定 IPv4；实际地址仍是 `http://127.0.0.1:<端口>`，没有改成任意自定义地址。

## 凭据前独立验证

完整脚本现在先完成以下阶段，成功才进入 CLI 帮助、精确钥匙串查询和凭据复制：

1. 保留原无端口 profile 的读/写/fork/网络反例。
2. 在父进程持有两个实际监听的本地 TCP 端口，一个许可，一个禁止；没有 HTTP 上游、转发或凭据。
3. 在带端口 profile、空隔离 HOME 和本地 BASE_URL 下单独执行同一个 CLI 的 `--version`，要求退出 0 且版本精确匹配。
   保存 `precredential_bound_profile_probe` 的安全结构摘要，失败即停止，不读取凭据。
4. 在同一 profile 下再次核对：指定 loopback 端口可连接、另一个活跃 loopback 端口不可连接，
   真实 HOME 不可读、隔离只读夹具不可写、fork 被拒绝。写反例仍不尝试写真实 HOME。
   结果保存到 `precredential_bound_profile_guards`，失败即停止。
5. 实际假上游绑定后仍保留原来的 `bound_profile_probe`，对实际端口再次执行版本检查。

没有针对真实外部服务发送探测包。外连限制的规则保持明确受限，实际运行时证据由上述本地正/反例和主控实跑提供。

## 清单归属方案

见 [HOME-WRITE-ATTRIBUTION-PROPOSAL.md](HOME-WRITE-ATTRIBUTION-PROPOSAL.md)。这里只提交方案，不实施归属观察、申请 root 权限或修改验收条件。
probe-03 五项差异原样保留；主控对 `a94ba246` 的来源说明不改写成当时的独立监控。
probe-04 继续完整清单比较，有差异仍为 INCOMPLETE，不增加目录白名单或忽略项。

## 主控在沙箱外执行

```sh
python3 workbench/tests/probe_t093_normal_login.py --run --claude /Users/luckye/.local/share/claude/versions/2.1.302 --output evidence/2026-10-16-batch16/T-093/probe-04.json
```

脚本在进入认证前先独立取得版本与权限前检，任一失败立即停止。输出独占新建，不覆盖旧探针。
重点读回凭据前的两个字段；不要把全局 INCOMPLETE（例如并发清单差异）与某个已验证事实混为一谈。

编译器定向检查的重放命令：

```sh
python3 workbench/tests/test_t093_probe_safety.py ProbeSafety.test_bound_profile_compiles_without_applying_it
```

编译修正时的辅助套件与“重新引入数值主机”反例保留在 `probe-helper-checks-07.json`；
加入“版本前检失败就不读凭据”入口场景后，当前 8 项基线检查与 11 个单点反例保存在 `probe-helper-checks-08.json`。
其中包括跳过版本前检停止条件的反例。入口场景使用合成 HOME 与受控 capture，证明流程先后关系，不替代实际 CLI 运行。
未扩大真实模型运行、HOME、网络或全局配置授权；未改产品代码。
