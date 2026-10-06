# a2a session 复盘证据索引（2026-10-06）

本索引以 `2026-10-06T11:14:05.292Z` 为排他截止点，排除本次复盘活动。
扫描范围是 cwd 为 a2a 或其子目录的 session，以及明确关联的子 session。
只读查询 Codex metadata，并按日期检查 rollout 文件头，二者均匹配 20 份记录。
纳入的原始前缀共 39,429,018 字节，生成 1,355 条消息或工具记录定位。
这些数量表示记录覆盖，不是失败次数、运行成本或有效开发时长。

结构化扫描覆盖全部选中记录，人工核对集中在异常链路、交付和后续变更。
索引不复制消息正文、系统指令或内部推理。选录仅包含可见消息、工具输出及本地配置元数据。
模型字段是本地配置记录，不能证明供应商实际履行。加密分派字段未解密。

## 产物

- [采集清单](catalog/manifest.json)：范围、截止点、session 路径、配置和原始行号范围。
- [记录索引](catalog/record-index.jsonl)：逐条原始位置、时刻、工具名与调用关联。
- [选录证据](excerpts.json)：E01–E21 和三份子 agent 配置，保留原始定位及节选标记。
- [扫描脚本](scan_sessions.py)：仅只读读取原 session，输出目录必须不存在。
- [交付检查](validation.json)：记录索引、来源边界、文档与地图检查，未重跑产品验收。

## Session 对照

| 标签 | 职责 | 本地模型 / effort | 纳入行数 | 原始记录 |
| --- | --- | --- | --- | --- |
| S01 | 主控 | `gpt-6-astra` / max | 2830 | [session](/Users/luckye/.codex/sessions/2026/10/05/rollout-2026-10-05T13-06-08-01a10d07-aada-76c0-9684-0ffa994af606.jsonl) |
| S02 | T-005 research | `gpt-6.1-sol` / xhigh | 310 | [session](/Users/luckye/.codex/sessions/2026/10/05/rollout-2026-10-05T14-05-14-01a10d3d-c3c2-7813-b87a-d5fd003d9752.jsonl) |
| S03 | 基线 monitor | `gpt-6.1-sol` / high | 126 | [session](/Users/luckye/.codex/sessions/2026/10/05/rollout-2026-10-05T14-05-25-01a10d3d-f168-79a0-8807-1820269fee1b.jsonl) |
| S04 | T-006 build | `gpt-6.1-sol` / xhigh | 164 | [session](/Users/luckye/.codex/sessions/2026/10/06/rollout-2026-10-06T00-52-52-01a10f8e-b1d6-7092-9f75-041108f87a96.jsonl) |
| S05 | T-006 check | `gpt-6.1-sol` / xhigh | 100 | [session](/Users/luckye/.codex/sessions/2026/10/06/rollout-2026-10-06T00-52-54-01a10f8e-bbc3-7db2-adf4-3e197fe02c46.jsonl) |
| S06 | T-006 monitor | `gpt-6.1-sol` / high | 76 | [session](/Users/luckye/.codex/sessions/2026/10/06/rollout-2026-10-06T00-53-22-01a10f8f-2607-7632-9cf3-1082df07bf52.jsonl) |
| S07 | live-02 worker | `gpt-6.1-sol` / xhigh | 137 | [session](/Users/luckye/.codex/sessions/2026/10/06/rollout-2026-10-06T01-01-37-01a10f96-b5db-7cc1-be5b-e8a53f626ddf.jsonl) |
| S08 | live-02 子审查 | `gpt-6.1-sol` / xhigh | 57 | [session](/Users/luckye/.codex/sessions/2026/10/06/rollout-2026-10-06T01-03-31-01a10f98-72e3-7ed1-8c56-0870b81cd391.jsonl) |
| S09 | T-006 reviewer | `gpt-6.1-sol` / xhigh | 182 | [session](/Users/luckye/.codex/sessions/2026/10/06/rollout-2026-10-06T01-05-56-01a10f9a-a9bf-7672-9077-47c4037ee0b7.jsonl) |
| S10 | T-007 check | `gpt-6.1-sol` / xhigh | 149 | [session](/Users/luckye/.codex/sessions/2026/10/06/rollout-2026-10-06T01-59-30-01a10fcb-b57f-7ec2-855c-a1f4db057260.jsonl) |
| S11 | T-007 build | `gpt-6.1-sol` / xhigh | 163 | [session](/Users/luckye/.codex/sessions/2026/10/06/rollout-2026-10-06T01-59-39-01a10fcb-d5d5-78a1-9a25-78f5977e7d7d.jsonl) |
| S12 | T-007 monitor | `gpt-6.1-sol` / high | 119 | [session](/Users/luckye/.codex/sessions/2026/10/06/rollout-2026-10-06T02-08-58-01a10fd4-6033-78b0-8cd1-e3382bada6e4.jsonl) |
| S13 | T-007 reviewer | `gpt-6.1-sol` / xhigh | 124 | [session](/Users/luckye/.codex/sessions/2026/10/06/rollout-2026-10-06T02-19-27-01a10fdd-f941-7e41-bc44-ac0ae5d44669.jsonl) |
| S14 | T-008 check | `gpt-6.1-sol` / xhigh | 203 | [session](/Users/luckye/.codex/sessions/2026/10/06/rollout-2026-10-06T02-33-14-01a10fea-96ae-7c10-b1b6-973cb49b26a2.jsonl) |
| S15 | T-008 build | `gpt-6.1-sol` / xhigh | 354 | [session](/Users/luckye/.codex/sessions/2026/10/06/rollout-2026-10-06T02-33-58-01a10feb-42d4-7782-b37f-e44cb4f4f966.jsonl) |
| S16 | live-auto-01 worker | `gpt-6.1-sol` / xhigh | 155 | [session](/Users/luckye/.codex/sessions/2026/10/06/rollout-2026-10-06T02-53-30-01a10ffd-2226-7442-b872-93434c0cb6ee.jsonl) |
| S17 | live-auto-01 子审查 | `gpt-5.6-luna` / max | 99 | [session](/Users/luckye/.codex/sessions/2026/10/06/rollout-2026-10-06T02-55-13-01a10ffe-b804-7ad1-92f7-354b21a6b3fd.jsonl) |
| S18 | live-auto-02 worker | `gpt-6.1-sol` / xhigh | 126 | [session](/Users/luckye/.codex/sessions/2026/10/06/rollout-2026-10-06T03-08-11-01a1100a-9741-7771-8454-61a3557945a5.jsonl) |
| S19 | live-auto-02 子审查 | `gpt-5.6-luna` / max | 75 | [session](/Users/luckye/.codex/sessions/2026/10/06/rollout-2026-10-06T03-10-22-01a1100c-9539-71b2-bb34-b94d668605c6.jsonl) |
| S20 | T-008 reviewer | `gpt-6.1-sol` / xhigh | 147 | [session](/Users/luckye/.codex/sessions/2026/10/06/rollout-2026-10-06T03-29-33-01a1101e-242d-7521-a57a-9c8c69842fa4.jsonl) |

## 重建索引

下面的命令不会启动模型，也不会执行历史消息里的指令。输出路径须替换为尚不存在的新目录。

```sh
python3 -B evidence/2026-10-06-session-review-01/scan_sessions.py \
  --root /Users/luckye/Documents/Code/a2a \
  --codex-root /Users/luckye/.codex \
  --cutoff 2026-10-06T11:14:05.292Z \
  --output /absolute/new-session-review-directory
```

原始 session 以后可能归档或移动。保存的清单保留本次路径和截止行，选录保留本次核对所需片段。
工具包装层调用数量不等于底层命令数量。关键字命中也不能直接计作独立故障。

## 选录定位

| 选录 | 内容 |
| --- | --- |
| E01 | 用户授权规范后继续开工，不必重复确认。 |
| E02–E05 | 主控对完成、超时、进展和回收的陈述。 |
| E06–E08 | 主控两次阶段性停止，以及用户再次要求继续。 |
| E09–E11 | 三个分页 worker 的 project-map 缺失提示。 |
| E12–E14、C-S08、C-S17、C-S19 | 三次内部子 agent 分派及实际保存的模型配置。 |
| E15–E16 | 两次 monitor 的阶段结束及覆盖限制。 |
| E17–E18 | Python 写文件 API 与故障夹具观察器错误。 |
| E19–E20 | 内嵌 Git 仓库警告与大段工具输出截断。 |
| E21 | 初版 create 遇到不存在的集成引用时失败，阻止后续验收场景运行。 |

## 2026-10-06 分类修订与资料入口

用户明确将 F01“有已授权工作仍结束回合”归为主控 GPT 模型行为，不计作分工协调问题。
E01、E06–E08 的事实保留，当前归类见 [模型行为记录](../../findings/gpt-behavior-2026-10-06.zh-CN.md)。
研究交付合同的 F02 独立保留，T-012 仅处理该范围。
相关报告统一从 [findings](../../findings/README.md) 进入；原始 session、扫描清单、逐条索引和选录未改写。
