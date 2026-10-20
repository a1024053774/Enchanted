"""Append-only launch identity shared by the launcher, Git hook, and score entry."""
from record_io import token

FIELDS = ("launch_id", "created_at", "project", "task", "attempt", "session", "role",
          "cli", "cli_version", "model", "effort", "service_tier_requested", "cwd",
          "project_commit", "launcher_commit", "role_card", "role_card_version", "argv")


def validate_launches(rows):
    latest = {}
    for row in rows:
        if row.get("schema") != 1 or row.get("phase") not in ("prepared", "started", "failed", "native-session"):
            raise ValueError("启动记录版本或阶段损坏")
        for key in FIELDS:
            value = row.get(key)
            if key == "argv":
                if not isinstance(value, list) or not value or any(not isinstance(v, str) for v in value):
                    raise ValueError("启动 argv 损坏")
            elif not isinstance(value, str) or not value:
                raise ValueError("启动记录字段损坏：" + key)
        token(row["launch_id"])
        if row.get("parent_launch") is not None:
            token(row["parent_launch"])
        if not isinstance(row.get("native_session"), str) or not row["native_session"]:
            raise ValueError("启动记录原生会话损坏")
        previous = latest.get(row["launch_id"])
        if row["phase"] == "prepared":
            if previous is not None or row["native_session"] != "unknown":
                raise ValueError("启动记录重复或初始原生会话损坏")
        else:
            if previous is None or any(row[key] != previous[key] for key in FIELDS) or row.get("parent_launch") != previous.get("parent_launch"):
                raise ValueError("启动记录身份或配置被改变")
            expected = "started" if row["phase"] == "native-session" else "prepared"
            if previous["phase"] != expected:
                raise ValueError("启动记录阶段顺序损坏")
            if row["phase"] == "native-session" and row["native_session"] == "unknown":
                raise ValueError("原生会话绑定为空")
            if row["phase"] != "native-session" and row["native_session"] != "unknown":
                raise ValueError("启动前不能绑定原生会话")
        latest[row["launch_id"]] = row
    return latest


def find_launch(rows, launch_id):
    latest = validate_launches(rows)
    if launch_id not in latest:
        raise ValueError("找不到启动记录：" + launch_id)
    row = latest[launch_id]
    if row["phase"] not in ("started", "native-session"):
        raise ValueError("启动记录没有成功启动：" + launch_id)
    return row
