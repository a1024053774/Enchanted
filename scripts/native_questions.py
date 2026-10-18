"""只读已绑定 Codex 原生会话的提问事实，不解释自然语言答复。"""
import json
import os
from contextlib import contextmanager
from pathlib import Path
import sqlite3
import stat


class NativeUnreadable(ValueError):
    def __init__(self, reason, **details):
        self.reason, self.details = reason, details
        super().__init__(reason)


def index_rows(store, session=None):
    path = Path(store)
    if not path.is_absolute():
        raise NativeUnreadable("native_index_path_not_absolute")
    try:
        # URI read-only mode cannot create a missing database.
        connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=1)
        try:
            connection.execute("PRAGMA query_only = ON")
            query = "SELECT id,rollout_path,cwd,source FROM threads"
            rows = connection.execute(query + " WHERE id=?", (session,)).fetchall() if session is not None else connection.execute(query).fetchall()
        finally:
            connection.close()
    except sqlite3.Error as exc:
        raise NativeUnreadable("native_index_unreadable", error=str(exc)) from exc
    return [dict(zip(("id", "path", "cwd", "source"), row)) for row in rows]


def isolated_session(store, workspace):
    """仅供本脚本新建、只含一个 worker 的隔离 HOME 建立初次绑定。"""
    rows = index_rows(store)
    if (len(rows) != 1 or rows[0]["source"] != "cli" or not isinstance(rows[0]["id"], str) or not rows[0]["id"]
            or not isinstance(rows[0]["cwd"], str)
            or not isinstance(rows[0]["path"], str)
            or Path(rows[0]["cwd"]).resolve() != Path(workspace).resolve()
            or not Path(rows[0]["path"]).resolve().is_relative_to(Path(store).parent.resolve())):
        raise NativeUnreadable("isolated_native_session_not_unique")
    return rows[0]


def questions(value, asynchronous):
    if not isinstance(value, dict) or not isinstance(value.get("questions"), list) or not value["questions"]:
        raise NativeUnreadable("native_question_arguments_incomplete")
    ids = []
    for question in value["questions"]:
        if not isinstance(question, dict):
            raise NativeUnreadable("native_question_arguments_incomplete")
        text = question.get("title" if asynchronous else "question")
        if not isinstance(text, str) or not text:
            raise NativeUnreadable("native_question_arguments_incomplete")
        options = question.get("options")
        if options is not None and (not isinstance(options, list) or any(
                not isinstance(option, str) if asynchronous else
                not isinstance(option, dict) or not isinstance(option.get("label"), str) or not isinstance(option.get("description"), str)
                for option in options)):
            raise NativeUnreadable("native_question_options_incomplete")
        if not asynchronous:
            identity = question.get("id")
            if not isinstance(identity, str) or not identity or identity in ids or not isinstance(question.get("header"), str):
                raise NativeUnreadable("native_question_ids_incomplete")
            ids.append(identity)
    return ids


def parse_records(rows, session):
    pending, resolved, active, calls, user_events = {}, [], None, set(), []
    for number, row in enumerate(rows, 1):
        payload = row.get("payload")
        if not isinstance(payload, dict):
            if row.get("type") in ("session_meta", "response_item", "event_msg"):
                raise NativeUnreadable("native_record_incomplete", line=number)
            continue
        kind = payload.get("type")
        if row.get("type") in ("event_msg", "response_item") and not isinstance(kind, str):
            raise NativeUnreadable("native_record_incomplete", line=number)
        if row.get("type") == "event_msg" and isinstance(kind, str) and kind.startswith("request_user_input"):
            raise NativeUnreadable("native_question_event_format_unverified", line=number)
        if row.get("type") == "session_meta" and payload.get("id") != session:
            raise NativeUnreadable("native_session_changed", line=number)
        if row.get("type") == "response_item" and kind == "function_call":
            call = payload.get("call_id")
            if not isinstance(call, str) or not call or call in calls or not isinstance(payload.get("name"), str) or not payload["name"]:
                raise NativeUnreadable("native_call_identity_incomplete", line=number)
            calls.add(call)
        if row.get("type") == "response_item" and kind == "function_call_output":
            if not isinstance(payload.get("call_id"), str):
                raise NativeUnreadable("native_response_identity_incomplete", line=number)
            if payload["call_id"] not in calls:
                raise NativeUnreadable("native_response_without_call", line=number)
        if row.get("type") == "response_item" and kind == "function_call_output" and any(item["call_id"] == payload.get("call_id") for item in resolved):
            raise NativeUnreadable("native_duplicate_question_response", line=number)
        if row.get("type") == "event_msg" and kind == "task_started":
            turn = payload.get("turn_id")
            if not isinstance(turn, str) or not turn:
                raise NativeUnreadable("native_turn_identity_missing", line=number)
            active = turn
        elif row.get("type") == "response_item" and kind == "function_call" and payload.get("name") in ("request_user_input", "request_user_input_async"):
            call = payload.get("call_id")
            attribution = payload.get("internal_chat_message_metadata_passthrough")
            turn = attribution.get("turn_id") if isinstance(attribution, dict) else None
            if not isinstance(call, str) or not call or call in pending or any(item["call_id"] == call for item in resolved) or not active or turn != active:
                raise NativeUnreadable("native_question_identity_incomplete", line=number)
            asynchronous = payload["name"] == "request_user_input_async"
            try:
                arguments = json.loads(payload["arguments"])
            except (KeyError, TypeError, ValueError) as exc:
                raise NativeUnreadable("native_question_arguments_incomplete", line=number) from exc
            ids = questions(arguments, asynchronous)
            pending[call] = dict(call_id=call, turn_id=turn, asynchronous=asynchronous, ids=ids,
                                 question_count=len(arguments["questions"]), delivered=not asynchronous,
                                 accepted=not asynchronous, request_line=number)
        elif row.get("type") == "event_msg" and kind == "item_completed":
            item = payload.get("item", {})
            if not isinstance(item, dict):
                raise NativeUnreadable("native_item_incomplete", line=number)
            if item.get("type") == "AgentMessage" and item.get("delivery") == "async" and item.get("questions"):
                call = item.get("id")
                if (not isinstance(call, str) or call not in pending or payload.get("thread_id") != session
                        or payload.get("turn_id") != pending[call]["turn_id"] or not pending[call]["asynchronous"]):
                    raise NativeUnreadable("native_question_delivery_unmatched", line=number)
                questions(item, True)
                if len(item["questions"]) != pending[call]["question_count"] or pending[call]["delivered"]:
                    raise NativeUnreadable("native_question_delivery_incomplete", line=number)
                pending[call]["delivered"] = True
            elif item.get("type") == "UserMessage" and pending:
                # The captured format has no call id for async answers or skips.
                # Plain user text cannot close a question by inference.
                user_events.append(number)
        elif row.get("type") == "response_item" and kind == "function_call_output" and payload.get("call_id") in pending:
            call = payload["call_id"]
            try:
                value = json.loads(payload["output"])
            except (KeyError, TypeError, ValueError) as exc:
                raise NativeUnreadable("native_question_response_incomplete", line=number) from exc
            question = pending[call]
            attribution = payload.get("internal_chat_message_metadata_passthrough")
            if attribution is not None and (not isinstance(attribution, dict) or attribution.get("turn_id") != question["turn_id"]):
                raise NativeUnreadable("native_response_identity_mismatch", line=number)
            if question["asynchronous"] and isinstance(value, dict) and set(value) == {"accepted"} and value["accepted"] is True:
                if question["accepted"]:
                    raise NativeUnreadable("native_duplicate_question_receipt", line=number)
                question["accepted"] = True  # Receipt only. It is not an answer.
            else:
                answers = value.get("answers") if isinstance(value, dict) else None
                if (not isinstance(answers, dict) or any(not isinstance(key, str) or not key for key in answers)
                        or not question["asynchronous"] and any(key not in question["ids"] for key in answers)
                        or any(not isinstance(answer, dict) or not isinstance(answer.get("answers"), list)
                               or any(not isinstance(text, str) for text in answer["answers"]) for answer in answers.values())):
                    raise NativeUnreadable("native_question_response_incomplete", line=number)
                if question["asynchronous"] and answers and len(answers) != question["question_count"]:
                    raise NativeUnreadable("native_async_answers_incomplete", line=number)
                if not question["accepted"] or not question["delivered"]:
                    raise NativeUnreadable("native_question_publication_incomplete", line=number)
                resolved.append(dict(call_id=call, turn_id=question["turn_id"], response_line=number,
                                     response="answers" if answers else "empty_answer_map"))
                del pending[call]
    if active is None:
        raise NativeUnreadable("native_turn_identity_missing")
    if any(not item["accepted"] or not item["delivered"] for item in pending.values()):
        raise NativeUnreadable("native_question_publication_incomplete")
    if any(item["turn_id"] != active for item in pending.values()):
        raise NativeUnreadable("native_unresolved_question_from_previous_turn")
    if pending and user_events and max(user_events) > min(item["request_line"] for item in pending.values()):
        raise NativeUnreadable("native_user_response_uncorrelated")
    return dict(state="pending" if pending else "clear", turn_id=active,
                pending=list(pending.values()), resolved=resolved)


@contextmanager
def bound_native_log(store, record):
    """打开已按会话 ID 和日志头核对的文件；调用者不能选择别的日志。"""
    session = record["native_session"]
    if not isinstance(session, str) or session == "unknown" or not session:
        raise NativeUnreadable("native_session_unbound")
    if not store:
        raise NativeUnreadable("native_index_unbound")
    matches = index_rows(store, session)
    if len(matches) != 1:
        raise NativeUnreadable("native_index_identity_missing")
    entry = matches[0]
    if (entry["source"] != "cli" or not isinstance(entry["cwd"], str) or not Path(entry["cwd"]).is_absolute()
            or Path(entry["cwd"]).resolve() != Path(record["cwd"]).resolve() or not isinstance(entry["path"], str)):
        raise NativeUnreadable("native_index_identity_mismatch")
    path = Path(entry["path"])
    if not path.is_absolute():
        raise NativeUnreadable("native_log_path_not_absolute")
    try:
        with path.open("rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > 64 * 1024 * 1024:
                raise NativeUnreadable("native_log_not_readable_regular_file")
            first = stream.readline(4 * 1024 * 1024 + 1)
            if not first.endswith(b"\n") or len(first) > before.st_size:
                raise NativeUnreadable("native_metadata_incomplete")
            header = json.loads(first.decode("utf-8"))
            if not isinstance(header, dict):
                raise NativeUnreadable("native_metadata_incomplete")
            metadata = header.get("payload", {})
            if (header.get("type") != "session_meta" or not isinstance(metadata, dict)
                    or metadata.get("id") != session or metadata.get("session_id", session) != session
                    or metadata.get("source") != "cli" or metadata.get("cli_version") != "0.163.0"
                    or not isinstance(metadata.get("cwd"), str) or not Path(metadata["cwd"]).is_absolute()
                    or Path(metadata["cwd"]).resolve() != Path(record["cwd"]).resolve()):
                raise NativeUnreadable("native_log_identity_mismatch")
            yield path, stream, before, header
            after = path.stat()
            if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino) or after.st_size < before.st_size:
                raise NativeUnreadable("native_log_changed_or_incomplete")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise NativeUnreadable("native_log_unreadable", error=str(exc)) from exc


def read_native(store, record):
    try:
        with bound_native_log(store, record) as (path, stream, before, header):
            start = stream.tell()
            remaining = stream.read(before.st_size - start)
            if start + len(remaining) != before.st_size or remaining and not remaining.endswith(b"\n"):
                raise NativeUnreadable("native_log_changed_or_incomplete")
        rows = [header, *[json.loads(line) for line in remaining.decode("utf-8").splitlines()]]
        if any(not isinstance(row, dict) for row in rows):
            raise NativeUnreadable("native_record_incomplete")
        result = parse_records(rows, record["native_session"])
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise NativeUnreadable("native_log_unreadable", error=str(exc)) from exc
    result.update(session_id=record["native_session"], index=str(store), path=str(path), bytes=before.st_size,
                  device=before.st_dev, inode=before.st_ino, lines=len(rows))
    return result
