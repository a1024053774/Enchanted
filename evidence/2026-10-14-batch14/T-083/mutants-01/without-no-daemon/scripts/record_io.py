"""Durable append-only JSONL for the two Herdr-period evidence entry points."""
from contextlib import contextmanager
import datetime as dt
import fcntl
import json
import os
import stat


def token(value):
    if not value or value in (".", "..") or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_." for c in value):
        raise ValueError("无效标识：" + value)
    return value


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


@contextmanager
def locked(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def read_records(path):
    if not path.exists():
        return []
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        raise ValueError("记录尾部不完整，保留现场：" + str(path))
    rows = []
    for number, line in enumerate(raw.splitlines(), 1):
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"清单条目不是对象：{path}:{number}")
        rows.append(row)
    return rows


def append_record(path, row):
    # Callers hold the stream's lock. A partial write stays visible and the next
    # invocation rejects it; never truncate a failed append to hide evidence.
    data = (json.dumps(row, ensure_ascii=False) + "\n").encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError("记录文件必须是普通文件：" + str(path))
        pending = memoryview(data)
        while pending:
            count = os.write(fd, pending)
            if count == 0:
                raise OSError("记录写入未取得进展")
            pending = pending[count:]
        os.fsync(fd)
    finally:
        os.close(fd)
    sync_directory(path.parent)
