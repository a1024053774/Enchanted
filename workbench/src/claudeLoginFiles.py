"""Private helper. stdout is captured in memory by the host, never a terminal."""
import json
import os
from pathlib import Path
import stat
import signal
import subprocess
import sys
import time

SCOPES = (".claude", ".claude.json", ".claude.json.backup", "Library/Keychains")


def inventory(home):
    result = {}

    def visit(name, parent, relative):
        try:
            info = os.stat(name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            result[relative] = {"missing": True}
            return
        result[relative] = {"mode": info.st_mode, "bytes": info.st_size,
                            "mtime_ns": info.st_mtime_ns, "inode": info.st_ino}
        if stat.S_ISDIR(info.st_mode):
            try:
                directory = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            except FileNotFoundError:
                result[relative]["missing"] = True
                result[relative]["observation"] = "vanished_before_enumeration"
                return
            try:
                for child in sorted(os.listdir(directory)):
                    visit(child, directory, relative + "/" + child)
            finally:
                os.close(directory)

    home_fd = os.open(home, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for scope in SCOPES:
            parent = os.dup(home_fd)
            try:
                parts = Path(scope).parts
                for index, part in enumerate(parts):
                    if index == len(parts) - 1:
                        visit(part, parent, scope)
                        break
                    try:
                        next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                    except FileNotFoundError:
                        result[scope] = {"missing": True}
                        break
                    os.close(parent)
                    parent = next_fd
            finally:
                os.close(parent)
    finally:
        os.close(home_fd)
    return result


def read_auth(home, source):
    if source == "file":
        directory = os.open(home, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            child = os.open(".claude", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            try:
                fd = os.open(".credentials.json", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=child)
                with os.fdopen(fd, "rb") as stream:
                    if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                        raise ValueError()
                    raw = stream.read(1024 * 1024)
            finally:
                os.close(child)
        finally:
            os.close(directory)
    elif source == "macos-keychain":
        keychain = Path(home) / "Library/Keychains/login.keychain-db"
        if any((Path(home) / relative).is_symlink() for relative in
               ("Library", "Library/Keychains", "Library/Keychains/login.keychain-db")):
            raise ValueError()
        profile = '(version 1)(allow default)(deny file-write*)(deny network*)(deny process-fork)'
        command = ["/usr/bin/sandbox-exec", "-p", profile, "/usr/bin/security",
                   "find-generic-password", "-s", "Claude Code-credentials", "-w", str(keychain)]
        completed = subprocess.run(command, capture_output=True, timeout=8, check=False)
        if completed.returncode != 0:
            raise ValueError()
        raw = completed.stdout
    else:
        raise ValueError()
    if len(raw) >= 1024 * 1024:
        raise ValueError()
    oauth = json.loads(raw)["claudeAiOauth"]
    if not isinstance(oauth["accessToken"], str) or len(oauth["accessToken"]) < 16:
        raise ValueError()
    if oauth.get("refreshToken") is not None and not isinstance(oauth["refreshToken"], str):
        raise ValueError()
    if not isinstance(oauth["expiresAt"], (int, float)) or oauth["expiresAt"] <= (time.time() + 120) * 1000:
        raise ValueError()
    return {"claudeAiOauth": oauth}


if __name__ == "__main__":
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.alarm(20)
    try:
        request = json.load(sys.stdin)
        result = inventory(request["home"]) if request["operation"] == "inventory" else read_auth(request["home"], request["source"])
        sys.stdout.write(json.dumps(result, ensure_ascii=True))
    except Exception:
        # No source contents, subprocess stderr, account names or tokens escape.
        sys.stderr.write("claude_login_private_file_operation_failed\n")
        sys.exit(2)
