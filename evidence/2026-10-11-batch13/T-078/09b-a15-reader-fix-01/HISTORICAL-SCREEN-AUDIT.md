# 已完成许可原屏审计

只读取 Git 中已有材料，没有查询 A-15 现场，也不改旧结论。原 dispatch 捕获器没有保存 total 元数据；下表采用主控当时另存的 gate screen 样本，并逐字节核对它与 dispatch 原屏一致。

| 阶段 | 原屏字节 | 保存的 gate total | cmp 原屏 | 判断 |
| --- | ---: | ---: | --- | --- |
| E1 | 16026 | 16026 | 相同 | 完整样本，不受本次截断影响 |
| E2 | 32797 | 32797 | 相同 | 完整样本，不受本次截断影响 |
| E3 | 52533 | 52533 | 相同 | 完整样本，不受本次截断影响 |
| I3 | 44869 | 44869 | 相同 | 完整样本，不受本次截断影响 |
| I1 | 16322 | 未直接保存 | 当时 Electron offset=16322 | 未见触及 64 KiB 上限的证据；直接 total 证据 INCOMPLETE |
| E4（未批准） | 65536 | 76125 | 相同前缀 | 已证实截断，缺 10589 字节 |

E1/E2/E3/I3 的另存 gate 样本均为 start_offset=0、next_offset=total_bytes，且完整字节等于原参考。结合相同 launch 的追加式 trace，可证明这些原参考没有漏掉该时刻的尾部。

I1 原屏只有 16,322 字节，Enter 前 Electron 已解析 offset 也为 16,322；这不是 65,536 字节上限截断的形状。但 Electron cursor 并不是独立的 gate total，原 API 响应未留存，所以不补称取得了相同等级的完整性证明。主控据此判断对既有 I1 PASS 的影响；旧 execute/result/批准文件全部原样保留。

机器可读记录及各来源路径见 historical-screen-audit.json。本审计不能用当前累计长度倒推过去的 total。
