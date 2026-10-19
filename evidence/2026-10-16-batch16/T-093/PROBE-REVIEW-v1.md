# T-093 前置探针 v1 独立审查

STATUS: FAIL
TARGET: T093-PROBE-v1；三个未提交文件 `probe_t093_normal_login.py`、`test_t093_probe_safety.py`、`PROBE.md`；HEAD `61786370428c3ec5f894ea60acccf2695d54c2dc`。

来源：干净上下文的只读 reviewer，gpt-6.1-sol / xhigh；按 behavioral-acceptance-review 执行。
未运行 Claude、`--run`、真实凭据读取或 Keychain 操作。下列为审查返回的原始结论（行号绑定 v1）。

EVIDENCE:

- 合成辅助套件 4 项通过，默认入口只显示范围。
- 独立合成反例复现凭据比较失真、清单越界、后代进程残留。
- 审查夹具与合成进程均已清理；未修改文件。project-map 为 0 problems、0 stale。

FINDINGS:

- [P1] `probe_t093_normal_login.py:215`：接收端每次请求重读可写副本。A 被改成 B 后，bearer B 仍报告匹配并满足路由通过条件。应在内存固定最初复制的 token。
- [P2] `probe_t093_normal_login.py:75`：只对最终路径 lstat；`HOME/Library` 为符号链接时仍会遍历范围外 Keychains。应核对祖先，不跟随链接。
- [P2] `probe_t093_normal_login.py:82`：进程组清理不能终止另建 session 的后代；登记列表为空不证明后代退出。TemporaryDirectory 的测试清理也不能证明探针自身完成清理。

COUNTEREXAMPLE:

- 接收端启动后将合成 A 改为 B，再发 bearer B：匹配 true，独立预期 false。
- 合成 HOME 的 Library 指向范围外目录：范围外文件进入清单。
- capture 子进程创建独立 session 后代并退出：后代仍存活；reviewer 随后终止该后代。

LIMITATIONS:

- macOS 沙箱、真实登录识别、Keychain 授权、真实 HOME 写保护均为 INCOMPLETE。
- 未证明真实 Claude 创建独立 session 后代；反例证明清理逻辑没有覆盖这类进程。
- 合成正常请求未保存 bearer 或正文，静态接收端没有上游转发代码。
- 尚未取得主控对清单范围的审阅结论。

## v2 修正与待验证边界

1. 假上游通过匿名管道接收最初复制的 token，并只在内存比较；不重读 CLI 可写副本。
   合成场景新增副本 A→B，要求 B 不匹配、A 继续匹配；含 token 的 URI 路径在落盘前脱敏。
2. 清单使用相对目录 fd 和 `O_NOFOLLOW` 逐级打开；Library 祖先链接只记录链接本身，不遍历目标。
   合成场景覆盖 Library→范围外 Keychains。
3. 保留进程组清理，但不再依赖它处理脱离进程组的后代：所有探针启动的程序均施加 OS 的 `deny process-fork`，
   CLI 的无凭据前检增加实际 fork 拒绝断言；security 另套只读、无网络、禁止 fork 的 profile，假上游也禁止 fork 和主动外连。
   这些 OS 规则尚未在沙箱外实跑。若它们阻断 CLI 的必要初始化，探针须停下交主控，不放宽限制。

只做了上述一次独立审查。v1 FAIL 保留，不把它写成 v2 已独立通过。
v2 的辅助反例结果另存新 JSON；真实边界及完整隔离 HOME 清理仍等主控 `--run` 结果。
