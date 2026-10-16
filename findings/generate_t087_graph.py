#!/usr/bin/env python3
"""Generate the T-087 dated Markdown record from repository sources; write stdout only."""

import argparse
import ast
import json
from pathlib import Path
import re
import subprocess
import sys


G = "workbench/src/gates/core.ts"
N = ".project-map/specs/native-cli-orchestration-2026-10-10.md"
C = ".project-map/specs/controller-split-user-input-2026-10-09.md"
I = "scripts/inbox"
T = ".project-map/templates/task-card.md"
K = "workbench/src/gates/taskCards.ts"
P = "workbench/src/panes.ts"
O = "workbench/src/store.ts"
E = ".project-map/roles/executor.md"
A = ".project-map/roles/ideation.md"
B81 = ".project-map/tickets/T-081-bad-worker-suite.md"
B82 = ".project-map/tickets/T-082-reviewer-oracle-sufficiency-mutation.md"
DOC = "findings/ticket-gates-graph-2026-10-16.zh-CN.md"

# These are authored source selections, not workflow rules or an executable policy.
# Resolve anchors on each run so line movement changes the generated citations.
ANCHORS = {
    "intent": ("intent.md", "让协作不依赖模型持续记住操作手册。"),
    "switch": ("intent.md", '在此之前，日常派发仍经 Herdr'),
    "ideation": (A, "你是上层主控"),
    "authorize": (A, "用户明确接受后才改目标、规则、术语"),
    "markready": (A, "把用户已决定、验收条件写清、依赖已关闭"),
    "executor": (E, "执行就绪 ticket：认领"),
    "stoprule": (".project-map/tickets/T-004-major-decision-stop-boundary.md", "The controller stops for scope or goal changes"),
    "ready": (C, "可执行的 ticket 类型是 build、task、research"),
    "readyfilter": (I, 'if item.get("status") != "open":'),
    "readydeps": (I, 'if all(dep in tickets and tickets[dep].get("status") in ("closed", "superseded")'),
    "revision": (C, "旧 rev 上进行中的 worker 由它决定继续还是重来"),
    "authref": (C, "**授权引用**"),
    "inboxwrite": (I, "os.link(temporary, inbox / (candidate + \".md\"), follow_symlinks=False)"),
    "ack": (I, 'if args.kind == "ack":'),
    "report": (C, "构思主控转述时状态逐字，不上调"),
    "emergency": (C, '执行主控 2 分钟没回 `ack`，且用户仍要求'),
    "triage": (E, "你只能关闭，不能替用户回答"),
    "answer": (E, '收到 `answer`：'),
    "worker": (".project-map/roles/worker.md", "显式 submit，不靠"),
    "monitor": (".project-map/roles/monitor.md", "不 claim，不 submit，不集成，不宣布成功"),
    "reviewrole": (".project-map/roles/reviewer.md", "必查完成条件是否足以拒绝明显错误的实现"),
    "split": (N, "一张就绪 ticket 拆成一张或几张任务卡"),
    "card": (T, "完成条件依赖的仓库内测试、脚本、夹具和配置"),
    "cardbinding": (K, 'check(card.source.ready_rev === source.source.ready_rev'),
    "claim": (G, "private async claim(task:"),
    "claimsave": (G, 'this.save(task, args.command === "dispatch" ? "dispatch_intent" : "claim_intent"'),
    "dispatch": (G, 'this.save(task, "dispatched", { attempt });'),
    "create": (G, 'this.save(task, "created");'),
    "submit": (G, 'if (args.command === "submit") {'),
    "submitted": (G, 'this.save(task, "submitted", { attempt, commit, task });'),
    "verify": (G, "private async verifyCandidate("),
    "verifysave": (G, 'this.save(task, "verification_intent", v);'),
    "merge": (G, 'this.save(task, "merge_candidate", v);'),
    "path": (G, 'await this.checkPaths(task, attempt, v);'),
    "oracle": (G, 'await this.checkOraclePaths(task, attempt, v);'),
    "completion": (G, 'for (const [index, command] of v.commands.entries())'),
    "completionlog": (G, 'this.event(taskId, "completion_check"'),
    "quality": (G, 'await this.checkQuality(task, attempt, v);'),
    "red": (G, 'const baseResult = await this.qualityCommand(task, v, "red_state"'),
    "rules": (G, 'for (const rule of task.quality.rule_checks)'),
    "quality-known": (G, 'const expected = error instanceof Refusal && ["red_state_failed"'),
    "quality-unknown": (G, 'else this.qualityIssue(task, attempt, "质量检查结果未知，等待核对", failure);'),
    "quality-unknown-code": (G, 'throw expected ? error : new Refusal("verification_unknown", failure);'),
    "quality-evidence": (G, 'private checkQualityEvidence('),
    "quality-evidence-code": (G, '"quality_reverification_required");'),
    "command-unknown": (G, 'const refusal = error.killed ? "command_timeout" : "command_unavailable";'),
    "trailers": (G, 'try { await this.checkTrailers(task, attempt, v); }'),
    "no-trailers": (G, 'const missing = Object.keys(trailers).length === 0;'),
    "model-unknown": (G, 'else if (trailers.model![0] !== "unknown" && trailers.model![0] !== attempt.delivery.model)'),
    "requestreview": (G, 'await this.requestReview(task, attempt);'),
    "reviewrequest": (G, 'const review: A2AReview = {'),
    "reviewrequirements": (G, 'mutation_checks: { min: 2, max: 5, workspace: candidateWorkspace'),
    "reviewlaunch": (G, 'private reviewLaunch('),
    "reviewsubmit": (G, 'if (args.command === "review_submit") {'),
    "reviewresult": (G, 'this.save(task, "review_result", { task, review });'),
    "review-needs-fix": (G, 'if (review.state === "needs_fix") await this.rejectDelivery(task, attempt, "independent_review", review.result);'),
    "review-parse": ("workbench/src/daemon.ts", 'try { request = reviewRequest(stop.last_assistant_message); }'),
    "review-relay-failed": ("workbench/src/daemon.ts", 'await gates.failReviewProtocol(pane.record.task, pane.record.review_id, { receipt, stop }, caller);'),
    "review-protocol": (G, 'async failReviewProtocol('),
    "review-protocol-save": (G, 'this.save(task, "review_protocol_failed", { task, review, details });'),
    "review-evidence": ("workbench/src/gates/qualityProtocol.ts", 'export function reviewEvidence('),
    "review-format-code": (G, 'error instanceof QualityProtocolError ? (error.field.startsWith("score") ? "invalid_score" : "invalid_review_result")'),
    "reviewend": (G, 'async reclaimReview('),
    "reviewboundary": (G, 'private async checkReviewBoundary('),
    "reviewremoved": (G, 'this.event(task.task_id, "review_candidate_copy_removed"'),
    "reviewrequired": (G, 'private requireReviewed('),
    "score": (G, 'private scoreData('),
    "integrate": (G, 'if (args.command === "integrate") {'),
    "intent-save": (G, 'this.save(task, "integration_intent", intent);'),
    "cas": (G, 'await send(`update ${intent.integration_ref} ${intent.M} ${intent.G}\\nprepare\\n`, "prepare: ok");'),
    "integrated": (G, 'this.save(task, completed ? "integrated" : "integration_conflict"'),
    "score-save": (G, 'private finalScore('),
    "reclaim": (G, 'this.event(taskId, "reclaim_intent", { attempt, live }, attempt.attempt_id);'),
    "cleanup": (G, 'private async cleanupAttempt('),
    "cleanupsave": (G, 'this.save(task, "worktree_cleanup_intent"'),
    "save": (G, 'private save('),
    "lock": (G, 'private operationLock('),
    "current": (G, 'private current('),
    "verifybinding": (G, 'private checkVerification('),
    "reject": (G, 'private async rejectDelivery('),
    "rejectsave": (G, 'this.save(task, "delivery_rejected", { task, repair });'),
    "feedback": (P, 'async qualityFeedback('),
    "unknown": (G, 'throw new Refusal("verification_unknown", v);'),
    "reviewfailed": (G, 'private reviewLifecycleFailed('),
    "reviewrestart": (G, 'recoverReviews()'),
    "interrupt": (G, 'private interruptVerification('),
    "invalidate": (G, 'private invalidate('),
    "revise": (G, 'if (args.command === "revoke" || args.command === "revise")'),
    "abandon": (G, 'if (args.command === "abandon") {'),
    "revalidate": (G, 'private async revalidateForIntegration('),
    "reconcile": (G, 'this.save(task, "integrated_reconciled", intent);'),
    "conflict": (G, 'private async writeConflict('),
    "conflictunknown": (G, 'this.save(task, "conflict_rework_unknown"'),
    "issue-save": (G, 'private qualityIssue('),
    "requestfailure": (G, 'this.event(taskId, "rejected", { error: code, details, input: raw });'),
    "store": (O, 'CREATE TABLE IF NOT EXISTS launch_records'),
    "launch": ("scripts/launch-worker", 'logfile = root / "records/launches.jsonl"'),
    "dispatchlog": ("scripts/dispatch", 'logfile = directory / "dispatch.jsonl"'),
    "dispatchunknown": ("scripts/dispatch", '派发结果未能记录；可能已送达，不得重试'),
    "b81": (B81, '## Resolution'),
    "b81cases": (B81, '坏行为（每项一案'),
    "b81limits": (B81, '第 7 项按用户决定'),
    "b82": (B82, '## Resolution'),
    "b82judgment": (B82, 'reviewer 判断是否正确如实记录，不作为门禁通过条件'),
    "assign087": (".project-map/inbox/20261016T082147Z-ideation-assign-001.md", 'kind: "assign"'),
    "audit087": (".project-map/tickets/T-087-explicit-graph-view.md", '抽查由不写图的会话完成'),
    "superseded": (".project-map/tickets/T-030-synara-fork-base.md", 'status: superseded'),
    "supersededwhy": (".project-map/tickets/T-030-synara-fork-base.md", '2026-10-10 由 [T-069]'),
    "outscope": (".project-map/tickets/T-028-app-tracer-bullet.md", 'status: out-of-scope'),
    "outscopewhy": (".project-map/tickets/T-028-app-tracer-bullet.md", '**2026-10-07：out-of-scope。**'),
    "runverify": (G, 'const verified = await this.request({ command: "verify", task: args.task, attempt: run.attempt_id! });'),
}


class Sources:
    def __init__(self, root):
        self.root = root
        self.files = {}
        self.entries = {}

    def read(self, path):
        if path not in self.files:
            resolved = (self.root / path).resolve()
            if not resolved.is_relative_to(self.root):
                raise ValueError("来源越出项目：" + path)
            self.files[path] = resolved.read_text(encoding="utf-8")
        return self.files[path]

    def add(self, key, path, needle):
        rows = [(i, line) for i, line in enumerate(self.read(path).splitlines(), 1) if needle in line]
        if len(rows) != 1:
            raise ValueError(f"来源锚点必须唯一：{path} / {needle!r}；实际 {len(rows)} 处")
        line, excerpt = rows[0]
        self.entries[key] = (path, line, excerpt.strip())

    def refs(self, keys):
        return "、".join(f"[{key}](#s-{key})" for key in keys.split())

    def span(self, start, end):
        path, line, _ = self.entries[start]
        end_path, end_line, _ = self.entries[end]
        if path != end_path or line >= end_line:
            raise ValueError("来源区间次序错误：" + start + "/" + end)
        return self.read(path).splitlines()[line - 1:end_line - 1], line


def table(headers, rows):
    def cell(value):
        return str(value).replace("|", "&#124;").replace("\n", "<br>")
    return "\n".join("| " + " | ".join(map(cell, row)) + " |" for row in [headers, ["---"] * len(headers), *rows])


def ticket_fields(s, path):
    lines = s.read(path).splitlines()
    if lines[0] != "---":
        raise ValueError("ticket 缺少 front matter：" + path)
    fields = {}
    for number, line in enumerate(lines[1:lines.index("---", 1)], 2):
        key, value = line.split(":", 1)
        if key in fields:
            raise ValueError("ticket 重复字段：" + key)
        fields[key] = value.strip()
        if key in {"id", "type", "status", "blocked_by", "claimed_by", "ready", "ready_by", "ready_rev"}:
            s.entries[fields.get("id", Path(path).stem) + ":" + key] = (path, number, line)
    return fields


def build(root):
    s = Sources(root)
    for key, (path, needle) in ANCHORS.items():
        s.add(key, path, needle)
    # The same check is called again by review_submit and integrate. Select the
    # one in verifyCandidate's quality block, not an arbitrary global occurrence.
    quality_lines, quality_first = s.span("quality", "trailers")
    evidence_calls = [(quality_first + index, line.strip()) for index, line in enumerate(quality_lines)
                      if line.strip() == "this.checkQualityEvidence(task, attempt, v);"]
    if len(evidence_calls) != 1:
        raise ValueError("verifyCandidate 质量串须有唯一 checkQualityEvidence 调用")
    s.entries["quality-evidence-call"] = (G, *evidence_calls[0])

    # Read literal kind names, never import or execute the inbox program.
    kinds = None
    for node in ast.parse(s.read(I)).body:
        if isinstance(node, ast.Assign) and any(isinstance(n, ast.Name) and n.id == "KINDS" for n in node.targets):
            kinds = ast.literal_eval(node.value)
    kind_rows = {}
    for line in s.read(C).splitlines():
        match = re.fullmatch(r"\| `([a-z-]+)` \| (.*?) \| (.*?) \|", line)
        if match:
            kind, direction, meaning = match.groups()
            kind_rows[kind] = (direction, meaning)
            s.add("kind:" + kind, C, line)
    if kinds != set(kind_rows):
        raise ValueError("收件箱 kind 与规格表不一致，须人工重新分析")

    points = []
    edges = []

    def point(ident, view, category, label, detail, refs):
        points.append((ident, view, category, label, detail, refs))

    def edge(ident, view, src, dst, label, persistence, refs, implicit=""):
        edges.append((ident, view, src, dst, label, persistence, refs, implicit))

    point("A1", "life", "agent 会话", "构思主控", "澄清、写决定/spec/ticket、标就绪和转述报告。", "ideation authorize")
    point("H1", "life", "人工决定点", "用户决定与授权", "T-004：目标/范围/验收/权限/不可逆外部效果/无法核对的外部状态/方向/预算风险。", "stoprule authref")
    point("L0", "life", "确定性步骤", "ticket 字段", "文件中的 status、blocked_by、claimed_by、ready、ready_by、ready_rev；不是门禁 task.state。", "ready")
    point("L1", "life", "确定性步骤", "就绪筛选", "scripts/inbox ready 只列 open、无人认领、可执行类型、就绪字段合法且依赖 closed/superseded 的 ticket。", "ready readyfilter readydeps")
    point("A2", "life", "agent 会话", "执行主控", "选择就绪工作、写任务卡、经门禁认领/派发/验收/集成/回收、汇总 Resolution。", "executor")
    point("L2", "life", "确定性步骤", "任务卡与注册", "正文由执行主控写；后台版本化任务卡并 create task；Herdr 期先用 Markdown 模板。", "card split create cardbinding")
    point("L3", "life", "确定性步骤", "Claim 认领", "原子预留路径、生成 attempt/session、fence 加一、绑定任务卡快照、建 worktree。", "claim claimsave")
    point("A3", "life", "agent 会话", "worker", "仅处理分配的 task/attempt；显式 Submit。", "worker dispatch")
    point("A4", "life", "agent 会话", "monitor", "只读观察、记录与 issue 上报；无成功判定权限。", "monitor")
    point("L4", "life", "确定性步骤", "问题上报与处置记录", "issue → triage；disposition/answer/ack 追加，不覆盖原条目。", "kind:issue kind:disposition answer inboxwrite")
    point("L5", "life", "确定性步骤", "ticket Resolution / 关闭", "执行主控汇总各任务卡结果；closed 是 ticket 字段，门禁 accepted 不会在此代码路径自动改 ticket。后半句是限定于已读路径的推断。", "executor T-087:status integrated")
    point("L6", "life", "确定性步骤", "当前不列为可执行", "未就绪、类型不适用、被认领、依赖未关闭或 status 非 open 均不会列入。closed 是完成记录；superseded/out-of-scope 是被取代/移出范围，不代表工作通过。", "readyfilter readydeps superseded outscope")
    point("Q0", "gate", "确定性步骤", "Submit 身份与版本", "task/attempt/session/fence/spec、运行时身份、HEAD、干净工作区、launch 交付事实。只到 submitted。", "submit submitted current")
    point("Q1", "gate", "确定性步骤", "Acceptance / verify 构造 M", "持操作锁；由当前工作分支 G 与固定候选 C 构造 M，冲突不进入路径检查。", "verify verifysave merge lock")
    point("Q2", "gate", "确定性步骤", "路径边界", "候选改动与合并改动均须在 allow 内且不命中 deny。", "path")
    point("Q3", "gate", "确定性步骤", "验收文件保护", "oracle_paths 相对认领起点与 G→M 改动有交集即 oracle_modified。", "oracle")
    point("Q4", "gate", "确定性步骤", "完成条件", "在 M 的验证工作区按卡执行 argv；逐条存意图、结果，非零打回。", "completion completionlog")
    point("Q5", "gate", "确定性步骤", "红态", "卡写了才查：起点加候选测试必须失败，候选必须通过；未写记 red_not_applicable。", "red quality")
    point("Q6", "gate", "确定性步骤", "规则式检查", "项目质量快照配置的规则在 M 执行；空列表记 rules_not_applicable。", "rules")
    point("Q13", "gate", "确定性步骤", "质量证据核对（checkQualityEvidence）", "红态与规则式检查返回后，核对质量快照、结果数量、测试清单和通过证据，再进入尾注。verify 中 quality_reverification_required 走未知结果暂停，不计作打回。", "quality-evidence-call quality-evidence quality-evidence-code quality-known quality-unknown-code")
    point("Q7", "gate", "确定性步骤", "提交尾注", "task/attempt/session/worker 与交付 launch/tool/effort 必须匹配；model 为字面量 unknown 时不要求与交付模型相等，否则须匹配。有 A2A 尾注时，所有必需字段仍须齐全、唯一且非空；全无尾注按人工介入处理。", "trailers no-trailers model-unknown")
    point("A5", "gate", "agent 会话", "reviewer 独立审查", "每次新建干净会话；T-082 一次性候选副本可写、断网，候选 Git 与共享仓库不可写。判断完成条件是否够格并做 2～5 个变异。", "reviewrole reviewlaunch reviewrequirements")
    point("Q8", "gate", "确定性步骤", "审查协议与绑定", "核对身份、版本、候选、非写入会话、结构化报告；有效可合并→verified，有效需修复→submitted/打回。当前运行审查的协议解析或转交门禁失败，经 failReviewProtocol 暂停并上报，不增加打回计数。协议格式不能证明判断正确。", "reviewsubmit reviewresult review-needs-fix review-parse review-relay-failed review-protocol b82judgment")
    point("Q9", "gate", "确定性步骤", "审查结束核对", "reviewer 已 idle；核对 refs、审查/worker worktree 与候选；清理副本和审查目录后写 review_reclaimed。verified 本身不够集成。", "reviewend reviewboundary reviewremoved reviewrequired")
    point("Q10", "gate", "确定性步骤", "验收打分参数", "执行主控提供主观评分及理由；门禁校验格式、launch 来源并填写客观事实。", "score score-save")
    point("Q11", "gate", "确定性步骤", "Integration / CAS", "核对当前 verification/review/结束记录和打分；持久意图后以 G→M CAS，读回后 accepted、记分。", "integrate intent-save cas integrated")
    point("Q12", "gate", "确定性步骤", "回收与清理", "核对身份、idle、停止/归档读回；保留 Git 引用后清理干净工作区，异常保留并上报。", "reclaim cleanup cleanupsave")
    point("R1", "recovery", "确定性步骤", "打回记录与计数", "已知检查失败或有效需修复业务结论调用 rejectDelivery，同一 attempt 计 delivery_rejected；少于三次允许回写，第三次 paused 并停止自动回写。质量未知结果与审查协议失败不计入。", "reject rejectsave feedback quality-known review-needs-fix review-protocol")
    point("R2", "recovery", "确定性步骤", "暂停或等待核对", "完成条件/质量串/质量证据的未知结果、运行中审查的协议失败、审查生命周期失败、超限或外部效果未知，不能等同成功。质量未知与协议失败是已有机械暂停路径，不是主控选择要不要打回。具体 state 见各路径。", "unknown quality-unknown-code review-protocol-save reviewfailed revalidate conflictunknown")
    point("R3", "recovery", "人工决定点", "执行主控处置", "三次打回/未知/异常后继续修复、放弃、升级或请求用户决定；不是统一自动恢复。", "triage stoprule abandon")
    point("R4", "recovery", "确定性步骤", "中断验收重跑", "锁释放后同一 verify 保留旧 interrupted/unknown 证据并新建 verification，不复活过期身份。", "interrupt verify verifybinding")
    point("R5", "recovery", "确定性步骤", "集成意图恢复", "同 intent：引用为 G 继续 CAS；为 M 核对内容补账；第三值或丢失需核对。", "integrate reconcile")
    point("R6", "recovery", "确定性步骤", "CAS 落空重新验收", "首次正常集成遇分支变化，持久 misses 后重跑质量串；候选及绑定不变且审查结束可沿用审查；第 4 次落空暂停上报。", "revalidate reviewrequired")
    point("R7", "recovery", "确定性步骤", "冲突返工", "保存冲突与候选/base refs；回原 worker；原会话结束时经回收/撤销后新 claim。新候选重跑与新审查。", "conflict conflictunknown submit")
    point("R8", "recovery", "确定性步骤", "撤销 / 修订 / 终结 attempt", "revoke/revise 使旧身份失效并回 ready；abandon 按打分结果 abandoned/upgraded；不等同 ticket 关闭。", "revise invalidate abandon")

    edge("E01", "life", "A1", "H1", "澄清并请求决定", "决定写 ticket/spec；用户原话另留引用", "authorize stoprule")
    edge("I01", "life", "H1", "L0", "隐式/靠主控判断：授权是否覆盖，标 ready", "ready/by/rev 落文件；判断不由筛选器验证", "markready authref", "I01")
    edge("E02", "life", "L0", "L1", "筛选字段与依赖", "只读文件；不认领、不改字段", "ready readyfilter readydeps")
    edge("E03", "life", "L1", "A2", "构思主控 assign（本批 refs）", "收件箱条目落盘；筛选器不发条目、不自动创建 task", "kind:assign assign087 inboxwrite")
    edge("I02", "life", "A2", "L2", "隐式/靠主控判断：拆卡与完成条件", "卡可持久；充分性与路径选择是人工判断", "split card executor", "I02")
    edge("E04", "life", "L2", "L3", "注册后 claim/dispatch", "card 版本/快照、task、attempt、fence 入库", "create claimsave")
    edge("E05", "life", "L3", "A3", "派发角色卡与任务卡", "后台 launch/dispatch 入库；Herdr launch/dispatch 分别落文件", "dispatch store launch dispatchlog")
    edge("E06", "life", "A3", "Q0", "显式 submit", "成功写 submitted；拒收追加 rejected", "worker submitted requestfailure")
    edge("E07", "life", "A3", "L4", "issue → triage", "Herdr 收件箱文件；后台 issue_records/events", "kind:issue inboxwrite issue-save")
    edge("E08", "life", "A4", "L4", "只读观察与 issue", "观察/报警记录；不写成功状态", "monitor kind:issue")
    edge("E09", "life", "A5", "L4", "范围外发现 issue", "同问题上报路径，不代替 review_submit", "reviewrole kind:issue")
    edge("I03", "life", "L4", "A2", "隐式/靠主控判断：分级与处置", "disposition 落盘；判断内容不由 kind 证明", "triage kind:disposition", "I03")
    edge("E10", "life", "A2", "A1", "needs-decision / report", "追加收件箱条目，报告状态逐字", "kind:needs-decision kind:report report")
    edge("E11", "life", "A1", "A2", "answer（逐字转述）", "条目引用 issue/worker；投递后 delivered 和 ack", "kind:answer answer")
    edge("E12", "life", "A2", "A3", "answer 原文投递", "dispatch 日志；已结束则 forward(session-ended)", "answer dispatchlog")
    edge("I04", "life", "A1", "A2", "revise 后隐式/靠主控判断：继续或重来", "ready_rev++ / revise 条目；执行选择另记证据", "kind:revise revision", "I04")
    edge("I05", "life", "A1", "A2", "cancel 后隐式/靠主控判断：如何结束执行", "cancel 落盘；条目本身不撤销门禁 attempt", "kind:cancel executor invalidate", "I05")
    edge("E13", "life", "A1", "A2", "stop；下一工具轮次执行并 ack", "stop/ack 追加；break-glass 需当时用户仍要求", "kind:stop kind:ack emergency")
    edge("E14", "life", "A2", "A1", "ack（确认收到/执行）", "追加文件；ack 不需要再 ack，不是验收证据", "kind:ack ack")
    edge("I06", "life", "Q12", "L5", "隐式/靠主控判断：各卡结果汇总关闭 ticket", "Resolution/status 另写文件；与门禁无跨介质原子提交", "executor integrated report", "I06")
    edge("E15", "life", "L5", "A2", "汇总完成报告", "有可执行就绪工作则继续；无则 report", "report executor")
    edge("E16", "life", "L0", "L6", "不满足 open/类型/认领/就绪/依赖条件", "只读排除；字段不合规报错，不自动修复", "readyfilter readydeps")
    edge("I12", "life", "H1", "L0", "隐式/靠主控判断：取代或移出范围", "决定另写 ticket 与地图；不自动等同取消活跃 attempt", "superseded supersededwhy outscope outscopewhy authorize", "I12")

    edge("I07", "gate", "Q0", "Q1", "隐式/靠主控判断：常规何时发起 verify", "submit 已入库；常规由主控调用，显式 run 可自动触发", "submitted executor runverify", "I07")
    # Extract the relative order of the actual verification calls, rather than
    # copying the narrative list in intent.md. Internal red/rule order is read too.
    order = [("Q2", "path"), ("Q3", "oracle"), ("Q4", "completion"),
             ("Q5", "quality"), ("Q13", "quality-evidence-call"), ("Q7", "trailers"), ("A5", "requestreview")]
    order.sort(key=lambda item: s.entries[item[1]][1])
    if not s.entries["red"][1] < s.entries["rules"][1]:
        raise ValueError("checkQuality 内红态/规则顺序变化，须重新分析")
    order.insert(next(i for i, item in enumerate(order) if item[0] == "Q5") + 1, ("Q6", "rules"))
    previous = "Q1"
    for number, (target, anchor) in enumerate(order, 20):
        edge("E" + str(number), "gate", previous, target, "通过后进入下一关", "检查意图/结果与 verification 关联入库；不适用项也记事件", anchor + " save", )
        previous = target
    edge("I08", "gate", "A5", "Q8", "隐式/靠主控判断：reviewer 判可合并或需修复", "格式、身份、C 绑定能核对；判断正确性无自动证明", "reviewrequirements reviewsubmit review-protocol b82judgment", "I08")
    edge("E30", "gate", "Q8", "Q9", "可合并；等 idle 后核对结束边界", "review_result 和 review_reclaimed 分开保存", "reviewresult reviewend")
    edge("I09", "gate", "Q9", "Q10", "隐式/靠主控判断：执行主控打分", "评分文件作参数；门禁校验并补客观字段", "score score-save executor", "I09")
    edge("E31", "gate", "Q10", "Q11", "integrate 核对并持久意图", "intent 绑定 attempt/session/fence/spec/G/C/M/score", "integrate intent-save verifybinding reviewrequired")
    edge("E32", "gate", "Q11", "Q12", "accepted 后回收", "分支读回+integrated+score；回收另写 reclaimed", "integrated reclaim cleanup")

    for number, (src, anchor) in enumerate([("Q2", "path"), ("Q3", "oracle"), ("Q4", "completion"), ("Q5", "red"), ("Q6", "rules"), ("Q7", "trailers")], 40):
        label = "已知红态失败（四码）" if src == "Q5" else "rule_check_failed" if src == "Q6" else "已知检查失败"
        edge("E" + str(number), "recovery", src, "R1", label, "delivery_rejected、失败检查、候选、count 持久化", anchor + " rejectsave" + (" quality-known" if src in ("Q5", "Q6") else ""))
    edge("E46", "recovery", "Q8", "R1", "有效的需修复业务结论", "review_result 后调用 independent_review 打回，增加 delivery_rejected 计数；协议失败不走此边", "reviewresult review-needs-fix rejectsave")
    edge("E47", "recovery", "R1", "A3", "count＜3：回写，修复后重交新 C", "派发记录与原 attempt 绑定；整串重跑", "reject feedback submitted")
    edge("E48", "recovery", "R1", "R2", "count≥3：paused，停止自动回写", "blocking issue 与计数入库", "reject feedback issue-save")
    edge("E49", "recovery", "Q1", "R4", "verifying 中断且锁已释放，再发 verify", "旧 verification=interrupted，缺失输出/退出码保持 unknown", "lock interrupt verify")
    edge("E50", "recovery", "R4", "Q1", "同一有效候选新 verification", "新 ID/独立验证工作区，不复用旧通过结论", "interrupt verifysave verifybinding")
    edge("E51", "recovery", "Q11", "R5", "pending intent 中断后重放 integrate", "先核对原 intent 与当前身份、引用", "integrate reconcile")
    edge("E52", "recovery", "R5", "Q11", "引用=G 继续；=M 核对补账", "仍用原 intent；M 分支不重复更新 Git", "integrate reconcile cas")
    edge("E53", "recovery", "R5", "R2", "第三值/引用丢失：needs_reconciliation", "保留 pending intent；不能 revoke/revise 绕过", "integrate revise")
    edge("E54", "recovery", "Q11", "R6", "无旧 pending 的新集成 CAS 落空", "integration_compare_failed 先保存 misses", "revalidate integrate")
    edge("E55", "recovery", "R6", "Q1", "misses＜4：重跑；同 C 可复用已结束审查", "旧验证与 refs 保留；不能仅沿用机械结果", "revalidate reviewrequired")
    edge("E56", "recovery", "R6", "R2", "misses≥4：integration_revalidation_limit", "paused 与 issue 落库", "revalidate")
    edge("E57", "recovery", "Q1", "R7", "merge_conflict", "冲突、候选/base 引用、返工 intent 保存", "merge conflict")
    edge("E58", "recovery", "R7", "A3", "送原 worker；已结束则新 claim 后再派发", "投递回执/替换 attempt 保存；新候选须新审查", "conflict submitted")
    edge("E59", "recovery", "R7", "R2", "外部停止/投递/创建结果未知", "conflict_rework_unknown；不盲重送/重建", "conflictunknown")
    edge("E60", "recovery", "Q4", "R2", "verification_unknown", "unknown 结果与 paused 保存，不计作已知失败", "unknown")
    edge("E61", "recovery", "Q9", "R2", "结束边界失败或重启无法接管 reviewer", "review_lifecycle_failed；结论失效并上报", "reviewfailed reviewrestart")
    edge("I10", "recovery", "R2", "R3", "隐式/靠主控判断：选处置方案", "issue 有记录；不存在通用自动解锁成功路径", "triage stoprule abandon quality-unknown review-protocol", "I10")
    edge("I11", "recovery", "R3", "R8", "隐式/靠主控判断：撤销、修订、放弃、升级", "经对应命令保存；设计/验收/权限变化须问用户", "revise abandon stoprule", "I11")
    edge("E62", "recovery", "R8", "L3", "仅 revoke/revise 回 ready 后可重新 claim", "旧 attempt 撤销，新 attempt/fence；abandon 不能直接 claim", "invalidate claim")
    edge("E63", "recovery", "A5", "R2", "审查创建失败或重启无法接管", "review_lifecycle_failed，当前执行暂停并上报", "reviewfailed reviewrestart")
    edge("E64", "recovery", "R8", "Q12", "终结后原 attempt 仍须经门禁回收", "命令绑定原 attempt；回收历史执行不接管新执行", "abandon reclaim cleanup")
    for ident, src in (("E65", "Q5"), ("E66", "Q6"), ("E67", "Q13")):
        edge(ident, "recovery", src, "R2", "五个已知失败码之外：verification_unknown", "verification_result 保留 unknown、task paused 并上报；不调用 rejectDelivery，不增加 delivery_rejected 计数", "quality-evidence-call quality-evidence-code quality-known quality-unknown quality-unknown-code command-unknown")
    edge("E68", "recovery", "Q8", "R2", "当前运行审查的协议解析或转交门禁失败", "failReviewProtocol 核对当前审查与 caller 后，review unknown、task paused，保存 review_protocol_failed 并上报；不调用 rejectDelivery，不增加 delivery_rejected 计数", "review-parse review-relay-failed review-protocol review-protocol-save review-evidence review-format-code")

    point_ids = {p[0] for p in points}
    if len(point_ids) != len(points) or len({e[0] for e in edges}) != len(edges):
        raise ValueError("图中重复 ID")
    for edge_row in edges:
        if edge_row[2] not in point_ids or edge_row[3] not in point_ids:
            raise ValueError("连接端点不存在：" + edge_row[0])
    focused = []
    for ident in ("T-078", "T-080", "T-081", "T-082", "T-087"):
        matches = sorted((root / ".project-map/tickets").glob(ident + "-*.md"))
        if len(matches) != 1:
            raise ValueError("ticket 路径必须唯一：" + ident)
        path = matches[0].relative_to(root).as_posix()
        fields = ticket_fields(s, path)
        dependencies = fields["blocked_by"].strip("[]").split(",")
        resolved = []
        for dependency in filter(None, (d.strip() for d in dependencies)):
            dep_paths = sorted((root / ".project-map/tickets").glob(dependency + "-*.md"))
            if len(dep_paths) != 1:
                raise ValueError("依赖 ticket 缺失/重复：" + dependency)
            dep = ticket_fields(s, dep_paths[0].relative_to(root).as_posix())
            resolved.append(dependency + "=" + dep["status"])
        focused.append([ident, fields["type"], fields["status"], fields["claimed_by"] or "空", fields.get("ready", "空") + "/" + fields.get("ready_by", "空") + "/" + fields.get("ready_rev", "空"), "; ".join(resolved) or "[]", s.refs(ident + ":type " + ident + ":status " + ident + ":claimed_by " + ident + ":ready " + ident + ":ready_by " + ident + ":ready_rev " + ident + ":blocked_by")])

    for row in points:
        for key in row[5].split():
            if key not in s.entries:
                raise ValueError("缺少来源：" + key)
    for row in edges:
        for key in row[6].split():
            if key not in s.entries:
                raise ValueError("缺少来源：" + key)

    # Refusal examples are selected by scope. Each code must exist literally in
    # that current source span; this is an existence check, not a semantic audit.
    refusal_groups = [
        ("操作锁", "lock", "current", ["operation_busy"], "等活跃执行者结束；只释放锁不算通过"),
        ("交付身份/候选", "submit", "integrate", ["stale_attempt", "stale_session", "stale_fence", "stale_spec", "stale_thread", "identity_conflict", "stale_turn", "candidate_conflict", "not_descendant", "workspace_head_mismatch", "dirty_worktree", "repair_requires_new_candidate", "delivery_facts_unknown"], "拒收，核对身份或交新候选；不把迟到提交迁移到新 attempt"),
        ("验证前置/合并/完成条件", "verify", "integrate", ["quality_rejection_limit", "repair_submission_required", "not_submitted", "needs_reconciliation", "merge_conflict", "oracle_failed", "verification_unknown"], "按打回、冲突、未知三条路径分别处理"),
        ("路径/验收文件", "claim", "integrate", ["oracle_not_found", "path_boundary_failed", "oracle_modified"], "认领起点须存在；交付越界/改验收文件打回"),
        ("红态/规则的五个已知失败码", "quality", "integrate", ["red_state_failed", "red_test_file_invalid", "red_test_not_changed", "red_test_symlink", "rule_check_failed"], "仅这五码在 verify 的质量块进入 rejectDelivery、增加 delivery_rejected；其余错误走 E65–E67"),
        ("提交尾注", "no-trailers", "integrate", ["trailer_task_mismatch", "invalid_trailers", "trailer_identity_mismatch", "trailer_launch_record_missing"], "打回；model=字面量 unknown 时不要求等于交付模型，其余必需字段仍须存在、唯一且非空；全无尾注是人工介入分支，不在此拒收列表"),
        ("审查绑定/结束", "reviewlaunch", "integrate", ["review_launch_boundary", "review_required", "stale_review", "review_end_check_required", "reviewer_not_idle", "review_shared_refs_changed", "review_worktree_changed", "review_worker_workspace_changed"], "边界失败使审查失效并上报；缺结束记录不能 integrate"),
        ("审查协议", "reviewsubmit", "submit", ["reviewer_required", "review_candidate_mismatch", "review_verification_mismatch", "review_writer_conflict", "review_native_session_reused", "review_requirements_mismatch"], "拒绝不匹配审查；格式合规仍不证明 reviewer 判断正确"),
        ("打分", "score", "integrate", ["score_required", "invalid_score", "score_provenance_required", "attempt_already_scored"], "补合法且绑定的打分，不绕过原 attempt"),
    ]
    refusal_rows = []
    for group, start, end, codes, consequence in refusal_groups:
        lines, first_line = s.span(start, end)
        links = []
        for code in codes:
            hits = [(first_line + i, line) for i, line in enumerate(lines) if '"' + code + '"' in line]
            if not hits:
                raise ValueError("来源中没有拒收码：" + group + "/" + code)
            number, excerpt = hits[0]
            key = "code:" + code
            s.entries[key] = (G, number, excerpt.strip())
            links.append("`" + code + "` " + s.refs(key))
        refusal_rows.append([group, "；".join(links), consequence])
    refusal_rows += [
        ["verify 质量块的未知结果", "`command_timeout` / `command_unavailable` " + s.refs("command-unknown") + "；`quality_reverification_required` " + s.refs("quality-evidence-call quality-evidence-code") + "；对外转换成 `verification_unknown` " + s.refs("quality-known quality-unknown-code"),
         "红态、规则命令无法启动/超时，或质量证据不符等非五码错误：unknown、paused、保存与上报，不调用 rejectDelivery，不增加 delivery_rejected。这里限定 verify；review_submit/integrate 的直接质量证据复核可原样返回拒收码。"],
        ["审查格式错误", "`invalid_review_result` " + s.refs("review-evidence review-format-code review-parse"),
         "QualityProtocolError 映射为格式拒收；真实 Stop 入口解析失败或转交门禁回执失败，再经 failReviewProtocol 将当前运行审查设 unknown、task paused，保存 review_protocol_failed 并上报，不增加 delivery_rejected。已 cancelled 的审查只记 review_after_termination。" + s.refs("review-relay-failed review-protocol review-protocol-save")],
    ]

    implicit_details = {
        "I01": ("ready 看似合法但授权/验收未真正确认，可能执行越权工作。", "不覆盖用户授权的含义判断。", "不覆盖授权；只判断候选与完成条件。"),
        "I02": ("拆卡漏目标，allow/oracle_paths 漏文件或完成条件过弱，坏交付仍可通过。", "覆盖已列入卡的越界/改验收文件、自报通过、正确交付误拒；不证明卡覆盖用户目标。", "直接审查完成条件充分性并做变异；2～5 个选择与判断仍属模型行为，不保证穷尽。"),
        "I03": ("严重问题被关闭、需用户决定的被当作日常问题处理，或未送达。", "不覆盖问题语义分级/送达。", "不覆盖 triage；可发现审查范围内问题，不保证跨角色处置。"),
        "I04": ("ready_rev 已变，旧 worker 继续做旧目标，或无谓重启丢失进度。", "覆盖旧 attempt 迟到交付的门禁拒收；不覆盖是否应该继续/重来。", "覆盖候选/审查绑定；不判断修订时执行策略。"),
        "I05": ("取消通知已确认，活跃 attempt 却仍可运行；误以为 cancel 等于 revoke。", "不覆盖 cancel 到门禁撤销的人工路由。", "不覆盖 cancel；审查生命周期核对不是取消决策。"),
        "I06": ("漏卡或漏证据仍把 ticket 关闭，或 accepted 后忘记关闭/报告。", "覆盖单个受管交付的错误拒收与固定候选；不覆盖 ticket 汇总关闭。", "覆盖每次审查与结束边界；不覆盖多卡汇总和 ticket 状态写回。"),
        "I07": ("候选停在 submitted，或错误地把提交/终端 idle 当已验收。", "覆盖仅自报成功不能通过完成条件；不保证主控及时触发 verify。", "审查请求发生在 verify 后；不覆盖触发时机。"),
        "I08": ("完成条件过弱或变异选错仍报可合并；结构化布尔值与报告标题不能证明判断正确。这里指有效业务结论的语义判断；协议解析/转交失败由 E68 机械暂停，不属这条隐式边，也不消耗打回计数。", "坏 worker 样本与正例检查门禁，不证明任意 reviewer 判断正确。", "直接增加充分性与变异要求；真实偏弱卡案例如实记录，明确不把判断正确作为门禁条件；不能因此将所有协议失败场景称为已覆盖。"),
        "I09": ("评分无根据或尺度漂移；合规 JSON 仍产生失真的评价数据。", "不覆盖主观分值/理由质量。", "不覆盖打分尺度。"),
        "I10": ("把未知结果当成功，重复外部副作用，或一直暂停无人处置。质量未知与审查协议失败已有 E65–E68 的机械暂停；这条隐式边只表示暂停之后如何处置。", "覆盖分支被改后的 CAS/拒收样本；不覆盖所有未知恢复的人工作法。", "覆盖 reviewer 结束边界与失效上报；不覆盖主控之后的决定，不将其扩大为全部质量未知或协议失败路径的验证。"),
        "I11": ("越权改验收/权限，或错误结束 attempt 后想沿用旧身份。", "覆盖旧身份拒收；不证明放弃/升级的业务判断或用户授权。", "不覆盖撤销/修订/升级的授权；可保护原候选审查边界。"),
        "I12": ("误把未做成或被放弃的工作写成完成；取代关系与活跃执行脱节。", "不覆盖 ticket 取代/范围决定。", "不覆盖 ticket 取代/范围决定。"),
    }
    if set(implicit_details) != {e[7] for e in edges if e[7]}:
        raise ValueError("隐式边清单与图不一致")

    # The revision concerns read source paths only. Committing this generated
    # document does not change its own source revision on regeneration.
    source_paths = sorted(s.files)
    revision = subprocess.run(["git", "log", "-1", "--format=%H", "--", *source_paths], cwd=root, check=True, text=True, capture_output=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=no", "--", *source_paths], cwd=root, check=True, text=True, capture_output=True).stdout
    if dirty:
        raise ValueError("来源有未提交修改，须先保留并确认来源版本：\n" + dirty)

    out = ["# ticket 生命周期与门禁检查串：显式图（2026-10-16）", "",
           f"T-087-1 / attempt a1；读取来源的最近提交：`{revision}`。本页是日期记录，由 `python3 findings/generate_t087_graph.py` 生成。", "",
           "结论：门禁把受管交付的身份、固定候选、检查结果和 Git 副作用绑定到持久记录；ticket 就绪的含义、任务卡是否充分、异常之后选哪条路、何时关闭 ticket，仍要主控或用户判断。图的虚线列出了这些人工决定。", "",
           "范围是当前 checkout 的文件与源码分析；未启动服务、模型或真实工作流。日常派发仍处 Herdr 期，后台源码表示已实现路径，不表示已切换日常派发（" + s.refs("switch intent") + "）。T-081/T-082 的通过只按 ticket 的日期 Resolution 引用，本次未重跑其验收。", "",
           "读图：矩形是确定性步骤，圆角是 agent 会话，菱形是人工决定点。实线只表示来源写明的检查/协议关系，不表示整段无人判断或已运行通过；虚线一律标“隐式/靠主控判断”。每个点以 ID 连接下方来源表，每条连接的 ID 连接条件、持久化与来源表。三个视图共享 ID，是同一流程的分区展示。", "",
           "这里沿用门禁检查、agent 会话、人工决定点、task/attempt 等 Ubiquitous language（" + s.refs("worker monitor reviewrole") + "）。Tracer bullet 的现有交付闭环由 Claim 到集成展开；Deep modules 所隐藏的锁、fence、快照与恢复在表中露出。没有增加术语或执行器。", "",
           "## ticket 的真实字段快照", "",
           "以下直接读取 front matter；ready=yes 可以与 closed 同时存在，因此“曾获授权”不等于“当前可执行”。依赖表读回被依赖票的 status，筛选条件以 " + s.refs("ready readyfilter readydeps") + " 为准。后台任务卡来源校验只检查 ready=yes 与 ready_rev，未重复脚本对 status、ready_by、类型和依赖的整套筛选；这一交接仍需主控按协议完成（" + s.refs("cardbinding readyfilter readydeps") + "）。", "",
           table(["ticket", "type", "status", "claimed_by", "ready/by/rev", "blocked_by 读回", "来源"], focused)]

    for view, title in [("life", "ticket、角色与交接"), ("gate", "受管交付的门禁检查串"), ("recovery", "拒收与恢复")]:
        selected = [e for e in edges if e[1] == view]
        ids = {e[2] for e in selected} | {e[3] for e in selected}
        out += ["", "## " + title, "", "```mermaid", "flowchart TD"]
        for ident, _, category, label, _, refs in points:
            if ident not in ids:
                continue
            text = ident + " " + label
            shape = ('(["', '"])') if category == "agent 会话" else ('{"', '"}') if category == "人工决定点" else ('["', '"]')
            out.append("  " + ident + shape[0] + text + shape[1])
        for ident, _, src, dst, label, _, _, implicit in selected:
            arrow = "-.->" if implicit else "-->"
            out.append(f'  {src} {arrow}|"{ident} {label}"| {dst}')
        out += ["```"]

    out += ["", "## 每个点的来源", "",
            table(["ID", "类别 / 名称", "含义与边界", "来源"], [[p[0], p[2] + " / " + p[3], p[4], s.refs(p[5])] for p in points]),
            "", "## 每条连接的条件与持久化", "",
            "所有常规门禁修改共用操作锁；save 以事务更新 task/attempt/verification 并追加事件。SQLite 的当前状态行可以更新；不能把“事件追加”写成“所有状态行不可变”（" + s.refs("lock save store") + "）。", "",
            table(["ID", "从 → 到", "条件 / 路由", "持久化或缺口", "来源"], [[e[0], e[2] + " → " + e[3], e[4], e[5], s.refs(e[6])] for e in edges]),
            "", "## 收件箱类型", "",
            "类型来自 scripts/inbox 的 KINDS 字面量，方向与含义来自交接规格表；两者不一致时脚本停止。ack 只确认条目，不能代替验收。", "",
            table(["kind", "方向", "含义", "图中连接", "来源"], [[kind, *kind_rows[kind], {"assign": "E03", "revise": "I04", "cancel": "I05", "stop": "E13", "report": "E10", "needs-decision": "E10", "issue": "E07/E08/E09", "disposition": "I03", "answer": "E11/E12", "ack": "E13/E14"}[kind], s.refs("kind:" + kind)] for kind in sorted(kinds)]),
            "", "## 拒收码与恢复路径的对照", "",
            "以下为图中路径所需的代表性拒收码，逐个检查其字符串位于对应源码区间，不是所有接口错误的穷举。reviewer 的“需修复”是业务结论，经 independent_review 打回，不冒充一个拒收码；已知失败、权限/运行阻塞、未知副作用分别保留。", "",
            table(["检查", "拒收码及源码行", "下一步"], refusal_rows),
            "",
            "集成的 `integration_compare_failed`、`integration_revalidation_limit`、`needs_reconciliation` 与回收的 `worker_working` 分别见 " + s.refs("revalidate cas integrate reclaim") + "；路径分别画在 E51–E56、E32。恢复时不能删锁文件、改 SQLite 或用锁已释放推断成功。", "",
            "## 持久化边界与未持久化的判断", "",
            table(["边界", "落地内容 / 不保证的部分", "来源"], [
                ["ticket → 就绪", "front matter/Resolution 落 Markdown；scripts/inbox ready 只读。所读路径未见 ticket 字段与后台 task 的跨介质事务（静态推断）。", s.refs("ready cardbinding executor")],
                ["收件箱 → 执行主控", "Herdr 条目 O_EXCL staging、fsync、link 原子发布；ack/disposition 另加条目。授权正文的含义仍靠人判断。", s.refs("inboxwrite authref")],
                ["认领 → agent 会话", "后台先保存 claim/dispatch intent、任务卡快照、attempt/session/fence，再建 worktree/会话。Herdr 的 launch 与 dispatch 分落 records/launches.jsonl 和 evidence/<batch>/dispatch.jsonl。", s.refs("claimsave launch dispatchlog store")],
                ["Submit → Acceptance", "C、交付 launch/tool/model/effort、attempt/session/fence/spec、任务卡快照均有绑定；verify 新建 G/C/M 与 verification_id。", s.refs("submitted verifysave verifybinding")],
                ["每项检查", "completion_intent/result、red/rule、path/oracle/trailer 事件落库；红态/规则之后、尾注之前另核对质量证据。执行中丢失的结果保持 unknown，不据此通过。", s.refs("completionlog red rules quality-evidence-call quality-evidence unknown save")],
                ["reviewer 请求 → 结束", "review 请求、启动记录、一次性副本、有效结构化结果、结束核对与清理事件分开；协议失败另记 review_protocol_failed。报告要求持久化，模型如何选变异与判断正确性无程序证明。", s.refs("reviewrequest reviewrequirements reviewresult review-protocol-save reviewend b82judgment")],
                ["打回 → worker", "失败检查/候选/计数先落库，后台回写有 dispatch 记录；第三次取消待回写队列并记 quality_feedback_stopped。", s.refs("rejectsave feedback store")],
                ["质量未知 / 审查协议失败 → 暂停", "verify 质量块五个已知失败码之外：verification_result=unknown、task paused 并上报；当前运行审查的协议解析/门禁转交失败：review unknown、task paused，保存 review_protocol_failed 并上报。两条路径均不调用 rejectDelivery、不增加 delivery_rejected。", s.refs("quality-known quality-unknown-code quality-unknown review-parse review-relay-failed review-protocol-save")],
                ["Integration → Git", "SQLite 先持久 pending intent；Git update-ref prepare/commit 做 CAS；读回引用/内容后记 accepted 和打分。SQLite 与 Git 不是同一事务，靠 intent 恢复。", s.refs("intent-save cas integrated reconcile")],
                ["回收 → 删除工作区", "身份和 idle 读回；Git 保留引用与 cleanup intent 先于 worktree remove；脏目录或未解决验收保留。", s.refs("reclaim cleanup cleanupsave")],
                ["人工判断 → 后续操作", "I01–I12 可能有文字记录，但没有能证明判断充分或原子完成路由的状态。日志存在不等于判断正确。派发结果未知时也不能凭重发补齐。", s.refs("authref triage dispatchunknown b82judgment")],
            ]),
            "", "## 隐式边清单与 T-081 / T-082 的覆盖", "",
            "“隐式”包括已规定职责、但下一步仍依赖语义判断的连接，不仅指完全没写规程的连接。后果和未覆盖项是本次静态分析的推断；覆盖仅引用两票的已记录范围，未把本次分析说成独立验收。T-081 记录 16 个坏行为、4 个正确交付及误拒绝 0，并明确能力检查的限制；T-082 记录 2 个真实 reviewer 回合及其适用边界（" + s.refs("b81 b81limits b82 b82judgment") + "）。", "",
            table(["ID / 从 → 到", "判断与潜在后果（推断）", "T-081 覆盖 / 未覆盖", "T-082 覆盖 / 未覆盖", "依据"], [[e[0] + " / " + e[2] + " → " + e[3], implicit_details[e[7]][0], implicit_details[e[7]][1], implicit_details[e[7]][2], s.refs(e[6] + " b81 b81cases b82 b82judgment")] for e in edges if e[7]]),
            "", "## 再生成、引用检查与证据边界", "",
            "在仓库根目录运行（输出 UTF-8、无 BOM、LF）：", "", "```sh",
            "python3 findings/generate_t087_graph.py > /tmp/t087-first.md",
            "python3 findings/generate_t087_graph.py > /tmp/t087-second.md",
            "diff -u /tmp/t087-first.md /tmp/t087-second.md",
            "python3 findings/generate_t087_graph.py --check findings/ticket-gates-graph-2026-10-16.zh-CN.md",
            "```", "",
            "脚本只读仓库来源与 Git 版本信息，向 stdout 输出文本；不写状态、不调门禁、不派发、不启动服务。来源集合最近提交号随来源提交变化，生成物本身提交不会改变它。锚点缺失/歧义、kind 不一致或红态/规则次序变化时停止，不能静默沿用旧引用。检查串调用的相对顺序从 verifyCandidate 中的锚点行序生成。", "",
            "这是面向这些文件的定向摘录，并非任意 TypeScript 控制流解析器。新增分支或其他文件中的新路由需要重新分析；源码变了，即使现有锚点仍在，也不能只凭引用存在就认定图语义完整。--check 检查点/连接 ID、引用声明、文件行号与摘录是否存在，不判断来源是否支持作者解读。", "",
            "状态：本页是 worker 的待审候选。两次生成、引用存在性和 project_map 状态另存 evidence/2026-10-16-batch16/T-087/；来源语义抽查须由不写图的会话完成（" + s.refs("audit087") + "），本作者不自称完成该抽查。", "",
            "## 来源索引", "",
            "每项链接显示仓库相对文件:行号；摘录为当前该行原文。图中来源 ID 都在这里展开。", "",
            table(["来源 ID", "文件:行", "该行摘录"], [[f'<a id="s-{key}"></a>{key}', f'[{path}:{line}](../{path}#L{line})', json.dumps(excerpt, ensure_ascii=False)] for key, (path, line, excerpt) in sorted(s.entries.items())]), ""]
    return "\n".join(out)


def check_document(root, path):
    """Check the artifact itself without regenerating its authored assertions."""
    text = path.read_text(encoding="utf-8")
    if "\ufffd" in text or text.startswith("\ufeff") or "\r" in text:
        raise ValueError("文档含替换字符、BOM 或非 LF 换行")
    declared = re.findall(r'<a id="s-([a-zA-Z0-9_:-]+)"></a>', text)
    used = re.findall(r'\[[^\]]+\]\(#s-([a-zA-Z0-9_:-]+)\)', text)
    if not declared or len(declared) != len(set(declared)) or not set(used) <= set(declared):
        raise ValueError("来源 ID 重复、缺失或未声明")
    source_rows = re.findall(r'^\| <a id="s-([^\"]+)"></a>[^|]+\| \[([^\]]+)\]\(\.\./([^#]+)#L(\d+)\) \| (.+) \|$', text, re.M)
    if len(source_rows) != len(declared):
        raise ValueError("来源索引格式不完整")
    for key, label, relative, number, excerpt in source_rows:
        resolved = (root / relative).resolve()
        if not resolved.is_relative_to(root) or not resolved.is_file():
            raise ValueError("来源文件不存在或越界：" + relative)
        lines = resolved.read_text(encoding="utf-8").splitlines()
        number = int(number)
        if not 1 <= number <= len(lines) or label != relative + ":" + str(number):
            raise ValueError("来源行号不存在或标签不符：" + key)
        if json.loads(excerpt.replace("&#124;", "|")) != lines[number - 1].strip():
            raise ValueError("来源摘录已变化：" + key)
    point_rows = re.findall(r'^\| ([ALHQR]\d+) \| (?:确定性步骤|agent 会话|人工决定点) / .*$', text, re.M)
    edge_rows = re.findall(r'^\| ((?:E|I)\d+) \| ([ALHQR]\d+) → ([ALHQR]\d+) \| .*$', text, re.M)
    if not point_rows or not edge_rows or len(point_rows) != len(set(point_rows)) or len(edge_rows) != len({e[0] for e in edge_rows}):
        raise ValueError("点或连接清单为空/重复")
    diagram_points = re.findall(r'^  ([ALHQR]\d+)(?:\(\[|\[|\{)', text, re.M)
    diagram_edges = re.findall(r'^  ([ALHQR]\d+) (?:-->|-\.->)\|"((?:E|I)\d+) [^\n]+"\| ([ALHQR]\d+)$', text, re.M)
    expected_edges = {(ident, src, dst) for ident, src, dst in edge_rows}
    if set(diagram_points) != set(point_rows) or {(ident, src, dst) for src, ident, dst in diagram_edges} != expected_edges or len(diagram_edges) != len(expected_edges):
        raise ValueError("图与点/连接清单不一致")
    if any(src not in point_rows or dst not in point_rows for _, src, dst in edge_rows):
        raise ValueError("图中连接端点未声明")
    for line in text.splitlines():
        if re.match(r'^\| (?:[ALHQR]\d+ |[EI]\d+ \|)', line) and not re.search(r'\]\(#s-', line):
            raise ValueError("点/连接缺少来源引用：" + line)
    return {"status": "PASS", "check": "引用存在性与图表 ID 一致性", "points": len(point_rows), "edges": len(edge_rows), "source_rows": len(source_rows), "source_uses": len(used), "semantic_audit": "未执行；由非作图会话完成"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", type=Path, help="检查已有文档的引用存在性；不重新生成")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.check:
            print(json.dumps(check_document(root, root / args.check), ensure_ascii=False, indent=2))
        else:
            sys.stdout.write(build(root))
    except (ValueError, OSError, SyntaxError, subprocess.CalledProcessError) as error:
        print("INCOMPLETE: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
