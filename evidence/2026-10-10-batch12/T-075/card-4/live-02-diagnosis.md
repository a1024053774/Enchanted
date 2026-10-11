# live-02 夹具诊断

状态：INCOMPLETE。原始失败保留在 `outside-live-02/`，本轮没有增加模型回合，累计 1/4。

`offline-trace/commands.jsonl` 第 13 行已经记录了出错命令：`pane_output --launch 064a82d5-08f2-4b54-a21a-1bd3470550c2 --offset -1`，退出 2、stdout 为空。stderr 为 `ERR_PARSE_ARGS_INVALID_OPTION_VALUE`，明确要求把以横线开头的参数值写成 `--offset=-XYZ`。夹具的 `call()` 没有先核对预期退出码 1，直接 `json.loads(result.stdout)`，因此用 JSONDecodeError 遮住了参数错误。

这发生在 ElectronClient 构造之前；该轮没有 window 目录。清理随后又追加了 ps、daemon_stop、ps，因此不能根据命令日志最后一条确定失败点。CLI 原文补回已经按字节相等，窗口补回尚未运行，不能记为通过。

最小修复：离线和真实生命周期两处负游标调用均使用 `--offset=-1`；解析业务拒收 JSON 前核对退出码。产品代码不变。所有本卡 UI 夹具命令的 stdout、stderr 在启动时就分别打开二进制文件，命令编号、argv、退出码、超时或启动异常关联到这些文件；JSON 解析异常带命令编号与路径，顶层错误保留堆栈。已有 Electron 原始输出继续单独保存。

隔离验证只检查夹具，可能的失败方式先列明：普通非零退出的空 stdout 或 stderr 丢失；非法 UTF-8 在落盘之前触发解码异常；超时前已输出的内容丢失；JSON 解析异常丢失命令位置；同一次命令的两条输出混淆。用本地短命令触发这些情况，不启动后台、Electron 或模型。参数修复先通过同一个 Node 参数解析器证明旧写法失败、新写法保留负值，完整后台与窗口验证交主控运行。

重新生成诊断与夹具检查：

```sh
python3 -B workbench/tests/test_command_evidence.py --output evidence/2026-10-10-batch12/T-075/card-4/command-evidence-01
```
