# 参数检查夹具更正

`rebase-resolution-check-01/results.json` 原样保留。三个参数检查退出均为 0，输出目录和身份内容正确；检查器把预期的 `/tmp` 路径与 runner 规范化后的 `/private/tmp` 字符串直接比较，误判了 macOS 上的同一路径。

只把检查器的预期目录也用 `Path.resolve()` 规范化，产品 runner 和验收业务断言没有因此修改。更正后的检查另存新标签：

```sh
python3 evidence/2026-10-11-batch13/T-078/verify_rebase_resolution.py --output evidence/2026-10-11-batch13/T-078/rebase-resolution-check-02
```

这是检查器错误，不是产品红态；不用于声称产品修复经过先红后绿。
