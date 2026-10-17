# Security notes 的固定比较规则

依据主控 #112 与 [决定 04](p1-materials-08d/controller-decision-04-update-112.md)。只允许隔离假服务实例确认 08c 已读回的这条提示，不能确认其他安全、权限或认证内容。新用途 `onboarding-notice` 仅允许 Enter。实际调用者仍来自 operator 凭据；批准模板不是批准。

## 输入与分段

基准是 [08c 原字节](p1-materials-08c/screen-after-theme-01/screen.bin)，共 4,685 字节；[主题确认前快照](p1-materials-08c/screen-theme-03/screen.bin) 共 3,906 字节，是它的完整前缀。提示段为剩余 779 字节，而非整个累计输出中的某个关键词命中。

每个新实例也先完成逐屏批准的主题导航／确认。后台取最后登记的 `onboarding-theme / Enter / Dark mode` 意图中的原字节；当前累计输出必须包含这个逐字节相同的完整前缀。只比较该前缀之后的全部提示输出。没有主题确认、前缀变化或没有新增字节均拒绝，不猜提示起点、不查找 Security notes 关键词、不回退到整屏匹配。

## 去控制序列与文字相等

[实现](../../../workbench/src/claudeNotice.ts) 只解析终端协议，不解释文字含义：

1. UTF-8 严格解码，不用替换字符掩盖错误；保留 BOM 和 Unicode 字符，不做 Unicode 归一化。
2. ESC `[` 的 CSI 按参数字节 `0x30–0x3f`、中间字节 `0x20–0x2f`、最终字节 `0x40–0x7e` 完整剥离，包含本次流中的 `?`、`<`、`>` 私有参数。其他已观察到的 ESC 字符集／单字符控制也剥离。未完成转义、控制字符串和未支持的 C1 控制不能授权按键。
3. CR、LF 转为换行，CRLF 只计一次；其他 C0 与 DEL 控制剥离。只去掉首尾空白换行，不去行内空格、不合并空格、不折叠正文空行、不改大小写或标点。
4. 剩余文字须与 [固定基准文字](p1-materials-08d/security-notice-text.txt) 全串相等。任何改字、追加说明、其他提示或可打印空格变化都拒绝 `notice_text_mismatch`。

基准文字保留了流中实际发出的字符；光标定位指令本身不携带的空格或字符不会猜补。这里是**去控制后的输出文字**，不是用截图重新排版或修正英语。因此 `You'rresponsibleforClaud's` 等片段照原流保留，不能为了可读性补字后放宽比较。原始屏幕仍独立留证供主控读回。

该比较在串行写入通路中、实际进程身份与原快照相等检查之后、意图登记及 PTY 写入之前执行。除了固定文字相等，当前累计输出原字节必须与主控本次批准的 screen.bin 全部相等；控制颜色变化可以保持文字相等，但仍须批准那份新原文。

## 一次性与范围

同一 screen_id 或相同原字节只能操作一次；本固定 notice 在整个 launch 也只能确认一次，改颜色或换 ID 不能二次确认。原文、目录、时间、用途、按键和批准引用随意图记录，成功写入另记事件；来源记 executor，不计为用户亲手输入。不自动补键或继续下一阶段。

外层隔离假服务凭据／启动记录限制保持原样，真登录记录拒绝此入口。真登录阶段在用户 HOME 出现任何引导屏，保存原文、停下交主控、不按键。

## 红态、反例与边界

[红态](notice-red-08d/results.json) 是新用途在起点被 `invalid_screen_key` 拒绝，额外 Enter 没有写入。起点上的文字比较／次数等规则尚不可达，不冒称各项规则已有业务红态。

[最终域绿态](notice-green-final-08d/results.json) 12/12：基准和纯颜色变化可确认；改字、附加提示、可打印空格变化、不完整控制序列、方向键、重复屏／重绘、原快照变化、真登录记录以及没有主题确认均拒绝。[文字规则变异体](notice-text-mutant-08d/counterexample.json) 仅撤掉文字比较后，四个禁止输入各自真实写入额外 CR；对应检查失败，其余 8 项通过，是业务反例。

原 [主题复现](theme-confirmation-green-08d/results.json) 4/4 和 [屏幕门禁](screen-key-green-08d/results.json) 4/4 保持通过。全部为域夹具，PTY 与进程身份合成；没有运行 CLI／API／模型，不证明真实 Security notes 已确认。真实动作留给 08d 的逐屏审批。

重放须使用新输出目录：

```sh
node workbench/tests/test_t078_notice_key.ts /绝对路径/新输出 evidence/2026-10-11-batch13/T-078/p1-materials-08c
```

变异体的精确替换、命令和退出原件见 notice-text-mutant-08d/command.json；只在新建临时源码副本上运行，原候选不改，输出不能覆盖。
