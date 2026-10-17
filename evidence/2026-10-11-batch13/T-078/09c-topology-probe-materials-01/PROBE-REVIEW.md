# 探针读回与允许项证据门

本包尚未运行。`setup-approval.json` 为空签字。先运行PROBE-COMMANDS第1步，再审生成的真实B1/首启材料；不要把整份命令文件当作一键批准。Stage A只为这个观察实验提供真实目标和服务，没有声称新的09C验收场次或四回归门已完成。

主控在三时点原件中逐项核对：

- 同一新root、实际B1 launch/session、固定Claude2.1.296可执行文件/启动参数、原七身份。`idle-01`保存空提示符完整原屏与0 POST，`turn-01/in-flight`对应现有API阶段屏障内同一未返回POST，`turn-01/permission-wait`对应实际PermissionRequest。审 `permission-screen-after-sampling.bin`、capture EOF、event原命令和same active/1 POST/零请求文件；没有任何许可Enter或工具执行。
- 每个角色CLI后代的comm、完整command、lstart、数值ps图、当前PPID链和观察时间。先查看所有PID，不只搜索caffeinate。`appearance_observations`/`absence_observations`是采样的时间边界，不能当作精确fork/exit时间；跨两个采样之间短暂出现但完全没被观察到的进程仍未知。
- `partial_identity_samples` 非空、`vanished_before_full_identity`、`graph_changed_during_detail`或lstart/原身份不一致时，原件保留但身份结论INCOMPLETE，不能补猜argv。当前PPID不是旧故障的历史fork记录。即使新探针抓到caffeinate，也不能倒填第2场故障时的具体PID集合。
- 新root的 `roles/ideation/claude-debug.log` 原件保留在root，若需辅助创建时段，只摘带UTC时间的 `Started caffeinate`、`tool_dispatch_start/end`、`Spawning shell` 原行。不要复制HOME/认证文件或整份未经脱敏的debug到Git。原ps来自自己的daemon树，未采全机其他会话argv/环境。

**本次未定义任何已允许的argv。**若证实某个进程为登记角色CLI合法派生的防休眠/工具子进程，再从实际无歧义的命令提议有限规则：绝对可执行路径与comm相符、固定可接受的参数排列、动态PID参数绑定原角色CLI PID、父进程必须是同一已登记CLI PID且lstart未变、同一场景/角色。参数有空白/歧义且ps不能还原真实argv时继续取证，不用字符串猜规则。让主控审原件和规则后，再实现并在真实九进程排练中验证。

仍须拒绝的反例：只同名但路径不同；父进程是其他角色/其他会话/daemon而非获准父CLI；父PID复用；`-w`等PID参数指向别人；多余参数、未见过的排列或可执行文件；原九节点缺失/关系改变；无法确定的短进程。不能放行整个daemon后代或所有CLI后代。若实际额外进程是daemon自己的ps等其他类别，先按创建链报告，另作最小处理裁定，不能套caffeinate规则。

三时点采样完成也只表示取证流程完成；合法性结论待读回。探针在许可屏保留现场，不能重跑turn（独占turn-intent防重复）。单角色探针只启动一个Claude、共七个持久进程；不能拿它假装九进程整场排练或为了清理凑启动第二角色。实际root/PID确定后按已有单角色owner-bound方式单独准备回收，先脱敏归档/逐字节读回，再正常daemon_stop和两API各一次SIGTERM，不能给未知子进程直接发信号。
