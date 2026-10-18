#!/usr/bin/env python3
"""由主控在沙箱外归档 T-095 离线检查原件；默认只打印计划，绝不删除源。"""
import argparse
import json
from pathlib import Path
import shutil


def inventory(root):
    if not root.is_dir() or root.is_symlink():
        raise ValueError("归档目录不存在或是链接")
    result = {}
    for path in root.rglob("*"):
        if path.is_symlink() or not path.is_file() and not path.is_dir():
            raise ValueError("归档中含链接或非常规文件")
        if path.is_file():
            result[str(path.relative_to(root))] = path.stat().st_size
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(Path(__file__).with_name("native-offline-evidence.archive.json").read_text(encoding="utf-8"))
    source, target = Path(manifest["original"]), Path(manifest["archive"])
    if not args.apply:
        print(json.dumps({key: manifest[key] for key in ("status", "original", "archive", "files", "bytes", "mode")}, ensure_ascii=False))
        return 0
    base = Path("/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-095")
    if (source.parent != Path("/tmp") or not source.name.startswith("t095-offline-native-evidence-")
            or target.parent != base or not target.name.startswith("offline-native-")):
        raise ValueError("归档路径超出本任务固定边界")
    if not Path("/Volumes/WD-Elements").is_mount():
        raise ValueError("外置盘未挂载，不回退到内置盘")
    expected = manifest["inventory"]
    if inventory(source) != expected or len(expected) != manifest["files"] or sum(expected.values()) != manifest["bytes"]:
        raise ValueError("源文件数或字节数已变化；保留现场，不复制")
    if target.exists():
        raise ValueError("目标已存在；不覆盖或续写，先核对先前归档")
    shutil.copytree(source, target)
    if inventory(target) != expected or inventory(source) != expected:
        raise ValueError("复制后文件数或字节数不一致；保留两端现场")
    receipt = dict(status="PASS", scope="offline evidence copy only; no model turn",
                   original=str(source), archive=str(target), files=manifest["files"], bytes=manifest["bytes"],
                   originals_deleted=False)
    with target.with_suffix(".receipt.json").open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(receipt, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
