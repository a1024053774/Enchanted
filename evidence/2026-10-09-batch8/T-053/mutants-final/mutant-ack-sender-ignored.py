#!/usr/bin/env python3
"""Append-only Herdr-period inbox. Python 3 standard library only."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sys
import uuid


JUDGMENT_PERIOD = dt.timedelta(minutes=15)
SNOOZE_PERIOD = dt.timedelta(hours=1)
COPY_REMINDER_PERIOD = dt.timedelta(days=7)
KINDS = {"assign", "revise", "cancel", "stop", "report", "needs-decision",
         "issue", "disposition", "answer", "ack"}
ACTIONS = {"close", "dismiss", "forward", "snooze", "reopen", "needs-user", "delivered"}
ENVELOPE = {"id", "from", "to", "kind", "reply_to", "refs", "created_at", "schema"}


class InboxError(ValueError):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise InboxError(message)


def timestamp(value):
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise InboxError("无效 UTC 时间：" + str(value)) from exc
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise InboxError("时间必须显式使用 UTC：" + str(value))
    return parsed


def token(value):
    if not value or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_:." for c in value) or value in (".", ".."):
        raise InboxError("无效标识：" + str(value))
    return value


def frontmatter(path):
    """Read the project's flat scalar/inline-list front matter; body stays opaque."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise InboxError("缺少 front matter")
    fields = {}
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            return fields, "".join(lines[i + 1:]).removeprefix("\n")
        if not line.strip():
            continue
        key, separator, raw = line.partition(":")
        key, raw = key.strip(), raw.strip()
        if not separator or not key or key in fields:
            raise InboxError("损坏或重复的 front matter 字段")
        if raw.startswith('"') or raw.startswith("["):
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                # Existing hand-written entries use [ticket:T-053, ticket:T-054].
                if raw.startswith("[") and raw.endswith("]") and '"' not in raw and "[" not in raw[1:]:
                    value = [part.strip() for part in raw[1:-1].split(",") if part.strip()]
                else:
                    raise InboxError("损坏的字符串或列表：" + key) from exc
        elif raw in ("true", "false"):
            value = raw == "true"
        else:
            value = raw
        fields[key] = value
    raise InboxError("front matter 未结束")


def entries(root):
    result, errors = {}, []
    for path in sorted((root / ".project-map/inbox").glob("*.md")):
        try:
            item, body = frontmatter(path)
            missing = ENVELOPE - item.keys()
            if missing:
                raise InboxError("缺少字段：" + ", ".join(sorted(missing)))
            for key in ("id", "from", "to", "kind"):
                if not isinstance(item[key], str):
                    raise InboxError("字段必须为字符串：" + key)
                token(item[key])
            if item["id"] != path.stem or item["kind"] not in KINDS or str(item["schema"]) != "1":
                raise InboxError("id/文件名、kind 或 schema 不合规")
            if not isinstance(item["reply_to"], str) or not isinstance(item["refs"], list) or not all(isinstance(ref, str) for ref in item["refs"]):
                raise InboxError("reply_to/refs 类型不合规")
            if item["kind"] == "issue" and (not isinstance(item.get("title"), str) or not item["title"].strip() or not isinstance(item.get("blocking", False), bool)):
                raise InboxError("issue 需要标题与布尔 blocking")
            if item["kind"] == "disposition" and item.get("action") not in ACTIONS:
                raise InboxError("disposition 缺少有效 action")
            item["_time"], item["_body"], item["_path"] = timestamp(item["created_at"]), body, path
            result[item["id"]] = item
        except (InboxError, OSError, UnicodeError) as exc:
            errors.append(f"{path.name}: {exc}")
    while True:
        dangling = [ident for ident, item in result.items() if item["reply_to"] and item["reply_to"] not in result]
        if not dangling:
            break
        for ident in dangling:
            item = result.pop(ident)
            errors.append(f"{item['_path'].name}: reply_to 不存在：{item['reply_to']}")
    return result, errors


def local_file(root, value):
    path = Path(value)
    if ".." in path.parts:
        raise InboxError("拒绝路径穿越：" + value)
    resolved = (root / path).resolve()
    if root not in resolved.parents or not resolved.is_file():
        raise InboxError("引用文件不存在或越出项目：" + value)
    return resolved


def reference(root, value, items):
    prefix, separator, rest = value.partition(":")
    if separator and prefix in ("ticket", "issue", "worker", "attempt"):
        token(rest)
        if prefix == "ticket" and not any(path.stem == rest or path.name.startswith(rest + "-") for path in (root / ".project-map/tickets").glob("*.md")):
            raise InboxError("ticket 引用不存在：" + value)
        if prefix == "issue" and (rest not in items or items[rest]["kind"] != "issue"):
            raise InboxError("issue 引用不存在：" + value)
        return
    name = rest if separator and prefix == "file" else value
    file_name, fragment_separator, fragment = name.partition("#")
    if fragment_separator and (not fragment.startswith("L") or not fragment[1:].isdigit() or int(fragment[1:]) < 1):
        raise InboxError("无效文件行号：" + value)
    local_file(root, file_name)


def confirmed(items, ident, role):
    return any(item["kind"] == "ack" and item["reply_to"] == ident
               for item in items.values())


def write_entry(root, item, body, now, ident=None):
    """O_EXCL staging, fsync, then atomic no-overwrite hard-link publication.

    A killed writer may leave an unpublished .tmp in .inbox-staging; readers only
    consume inbox/*.md. Existing entries are never truncated or replaced.
    """
    inbox = root / ".project-map/inbox"
    staging = root / ".project-map/.inbox-staging"
    inbox.mkdir(parents=True, exist_ok=True)
    staging.mkdir(exist_ok=True)
    temporary = staging / (uuid.uuid4().hex + ".tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        sequence = 1
        while True:
            candidate = ident or f"{now.strftime('%Y%m%dT%H%M%SZ')}-{item['from']}-{item['kind']}-{sequence:03d}"
            item["id"] = token(candidate)
            data = ("---\n" + "".join(key + ": " + json.dumps(value, ensure_ascii=False) + "\n" for key, value in item.items()) + "---\n\n" + body).encode("utf-8")
            os.lseek(fd, 0, os.SEEK_SET)
            os.ftruncate(fd, 0)
            pending = memoryview(data)
            while pending:
                written = os.write(fd, pending[:65536])
                if written == 0:
                    raise InboxError("条目写入未取得进展")
                pending = pending[written:]
            os.fsync(fd)
            try:
                os.link(temporary, inbox / (candidate + ".md"), follow_symlinks=False)
                directory_fd = os.open(inbox, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
                return candidate
            except FileExistsError as exc:
                if ident:
                    raise InboxError("id 已存在，拒绝覆盖：" + ident) from exc
                sequence += 1
    finally:
        os.close(fd)
        temporary.unlink()


def send(root, args, now):
    items, errors = entries(root)
    if errors:
        raise InboxError("\n".join(errors))
    sender, recipient = token(args.sender), token(args.to)
    if args.ident is not None:
        token(args.ident)
        if (root / ".project-map/inbox" / (args.ident + ".md")).exists():
            raise InboxError("id 已存在，拒绝覆盖：" + args.ident)
    if args.reply_to and args.reply_to not in items:
        raise InboxError("reply_to 不存在：" + args.reply_to)
    for ref in args.ref:
        reference(root, ref, items)
    body = local_file(root, args.body_file).read_text(encoding="utf-8") if args.body_file is not None else args.body
    item = dict(**{"from": sender}, to=recipient, kind=args.kind, reply_to=args.reply_to or "",
                refs=args.ref, created_at=now.isoformat().replace("+00:00", "Z"), schema=1)
    if args.title is not None:
        item["title"] = args.title
    if args.kind == "issue":
        if not args.title or not args.title.strip() or recipient != "triage":
            raise InboxError("issue 需要 --title 且 --to triage")
        item["blocking"] = args.blocking
    elif args.blocking:
        raise InboxError("--blocking 只用于 issue")
    if args.kind == "ack":
        target = items.get(args.reply_to)
        if not target or target["to"] != sender or recipient != target["from"]:
            raise InboxError("ack 必须由原收件人发给原发送人")
        if confirmed(items, target["id"], sender):
            print("已确认 " + target["id"])
            return
    if args.kind == "disposition":
        target = items.get(args.reply_to)
        if not target or target["kind"] != "issue" or args.action not in ACTIONS:
            raise InboxError("disposition 需要 issue 的 --reply-to 与 --action")
        if sender not in ("executor", "ideation", "user", "system"):
            raise InboxError("该发送者不能处置问题")
        if args.action == "dismiss" and sender != "user":
            raise InboxError("dismiss 仅供用户")
        if args.action == "close":
            if target.get("blocking") and sender != "user":
                raise InboxError("blocking 问题不能由主控自行关闭")
            if not args.reason or not args.basis:
                raise InboxError("close 必须带 --reason 与 --basis")
        item["action"] = args.action
        if args.reason:
            item["reason"] = args.reason
        if args.basis:
            item["basis"] = args.basis
    elif args.action or args.reason or args.basis:
        raise InboxError("处置字段只用于 disposition")
    print(write_entry(root, item, body, now, args.ident))


def issue_state(issue, items, now):
    chain = [item for item in items.values() if item["kind"] in ("disposition", "answer") and
             (item["reply_to"] == issue["id"] or "issue:" + issue["id"] in item["refs"])]
    chain.sort(key=lambda item: (item["_time"], item["id"]))
    if not chain:
        return ("等你决定" if issue.get("blocking", False) or now - issue["_time"] >= JUDGMENT_PERIOD else "待判断"), None
    last = chain[-1]
    if last["kind"] == "answer":
        return "已答复", last
    action = last["action"]
    if action in ("close", "dismiss"):
        return "已关闭", last
    if action == "forward":
        return ("已转交" if now - last["_time"] < JUDGMENT_PERIOD else "等你决定"), last
    if action == "snooze":
        return ("稍后" if now - last["_time"] < SNOOZE_PERIOD else "等你决定"), last
    if action == "delivered":
        return "已送达", last
    return "等你决定", last


def copy_reminder(root, now):
    latest = None
    for path in sorted((root / "evidence").glob("*/sessions/manifest.jsonl")):
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                copied = timestamp(record["cutoff_at"])
            except (json.JSONDecodeError, KeyError, TypeError, InboxError) as exc:
                raise InboxError(f"{path}:{i}: 会话副本清单损坏：{exc}") from exc
            latest = copied if latest is None else max(latest, copied)
    if latest is not None and now - latest > COPY_REMINDER_PERIOD:
        print("提醒：上次会话副本已超过 7 天，请运行 scripts/session-copy。")


def list_entries(root, role, now):
    if role != "user":
        card = root / ".project-map/roles" / (role + ".md")
        if not card.is_file():
            raise InboxError("角色卡缺失：" + str(card))
        print(card.read_text(encoding="utf-8"), end="\n")
    else:
        print("等你决定")
    items, errors = entries(root)
    for item in sorted(items.values(), key=lambda entry: (entry["_time"], entry["id"])):
        status, last = issue_state(item, items, now) if item["kind"] == "issue" else (None, None)
        if role == "user":
            visible = status == "等你决定"
        else:
            visible = (item["to"] == role or (item["kind"] == "issue" and item["to"] == "triage")) and not confirmed(items, item["id"], role)
        if not visible:
            continue
        print(f"ENTRY {item['id']} {item['kind']} {item['from']} → {item['to']}" + (f" [{status}]" if status else ""))
        print("时间：" + item["created_at"])
        if item.get("title"):
            print("标题：" + item["title"])
        if item["refs"]:
            print("引用：" + ", ".join(item["refs"]))
        print(item["_body"])
        if last is not None:
            print("最近处置/答复：" + last["id"])
            for key in ("reason", "basis"):
                if last.get(key):
                    print(key + ": " + last[key])
            print(last["_body"])
    copy_reminder(root, now)
    return diagnostics(errors)


def diagnostics(errors):
    for error in errors:
        print("不合规：" + error, file=sys.stderr)
    return 1 if errors else 0


def ready(root):
    tickets, errors = {}, []
    for path in sorted((root / ".project-map/tickets").glob("*.md")):
        try:
            item, _ = frontmatter(path)
            if not item.get("id") or item["id"] in tickets:
                raise InboxError("id 缺失或重复")
            tickets[item["id"]] = item
        except (InboxError, OSError, UnicodeError) as exc:
            errors.append(f"{path.name}: {exc}")
    for ident, item in sorted(tickets.items()):
        missing = [field for field in ("ready", "ready_by", "ready_rev") if field not in item or item[field] == ""]
        if missing:
            errors.append(ident + " 缺少 " + ", ".join(missing))
            continue
        if item["ready"] == "no":
            continue
        if item["ready"] != "yes" or item["ready_by"] not in ("ideation", "executor") or not str(item["ready_rev"]).isdigit() or int(item["ready_rev"]) < 1:
            errors.append(ident + " 就绪字段无效")
            continue
        dependencies = item.get("blocked_by")
        if not isinstance(dependencies, list) or not all(isinstance(dep, str) for dep in dependencies):
            errors.append(ident + " blocked_by 必须为列表")
            continue
        if item.get("type") not in ("build", "task", "research") or item.get("status") != "open" or item.get("claimed_by"):
            continue
        if all(dep in tickets and tickets[dep].get("status") in ("closed", "superseded") for dep in dependencies):
            print(f"READY {ident} {item['type']} rev={item['ready_rev']} by={item['ready_by']} {item.get('title', '')}")
    return diagnostics(errors)


def main():
    parser = Parser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="项目根目录（夹具也使用此参数）")
    parser.add_argument("--now", help="显式 UTC 读取/写入时间；默认当前时间")
    sub = parser.add_subparsers(dest="command", required=True, parser_class=Parser)
    sending = sub.add_parser("send", help="追加条目")
    sending.add_argument("--from", dest="sender", required=True)
    sending.add_argument("--to", required=True)
    sending.add_argument("--kind", choices=sorted(KINDS), required=True)
    sending.add_argument("--reply-to")
    sending.add_argument("--ref", action="append", default=[])
    sending.add_argument("--title")
    sending.add_argument("--blocking", action="store_true")
    sending.add_argument("--id", dest="ident", help="显式条目 id；已存在时拒绝")
    sending.add_argument("--action", choices=sorted(ACTIONS))
    sending.add_argument("--reason")
    sending.add_argument("--basis")
    bodies = sending.add_mutually_exclusive_group(required=True)
    bodies.add_argument("--body")
    bodies.add_argument("--body-file")
    listing = sub.add_parser("list", help="角色卡及未确认条目；user 只呈现等你决定的问题")
    listing.add_argument("--role", choices=("ideation", "executor", "user"), required=True)
    acknowledging = sub.add_parser("ack", help="原收件人追加确认；重复确认无副作用")
    acknowledging.add_argument("--role", required=True)
    acknowledging.add_argument("--id", required=True)
    sub.add_parser("ready", help="列出可执行的已授权 ticket；不合规项报错")
    args = parser.parse_args()
    root = args.root.resolve()
    if not (root / ".project-map").is_dir():
        raise InboxError("项目根目录缺少 .project-map")
    now = timestamp(args.now) if args.now else dt.datetime.now(dt.timezone.utc)
    if args.command == "send":
        send(root, args, now)
        return 0
    if args.command == "list":
        return list_entries(root, args.role, now)
    if args.command == "ready":
        return ready(root)
    items, errors = entries(root)
    if errors:
        raise InboxError("\n".join(errors))
    target = items.get(args.id)
    if target is None:
        raise InboxError("待确认条目不存在：" + args.id)
    if target["to"] != args.role:
        raise InboxError("只有原收件人可以 ack")
    if confirmed(items, target["id"], args.role):
        print("已确认 " + target["id"])
        return 0
    print(write_entry(root, dict(**{"from": token(args.role)}, to=target["from"], kind="ack", reply_to=target["id"],
          refs=[], created_at=now.isoformat().replace("+00:00", "Z"), schema=1), "确认收到。", now))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (InboxError, OSError, UnicodeError) as error:
        print("错误：" + str(error), file=sys.stderr)
        sys.exit(1)
