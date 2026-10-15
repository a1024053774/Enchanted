# A-08 命令模板（均需新 approval，当前不启动）

阶段 A：见 `09B-A08-STAGE-A-COMMAND.txt`，签署 `a08-stage-a-approval-01.json` 后运行。

B1 P1（阶段 A 通过后）：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/prepare-a07-b1-ideation-p1.py \
  --packet /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/09b-executable-materials-08 \
  --stage-a /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/09b-a08-stage-a-01 \
  --p1 /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/09b-a08-b1-ideation-p1-01
```

I1 材料（B1 P1 已真实生成后）：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/prepare-09b-i1-materials.py \
  --stage-a /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/09b-a08-stage-a-01 \
  --p1 /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/09b-a08-b1-ideation-p1-01 \
  --prompt-file /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/a08-i1-prompt.txt \
  --output /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/09b-a08-i1-materials-01
```
