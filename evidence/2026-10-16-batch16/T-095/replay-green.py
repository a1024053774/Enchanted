#!/usr/bin/env python3
"""用真实绿态原件回放 agent-status；不启动 Herdr、Codex 或真实模型。"""
import argparse
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
HERDR = '''import json,os,pathlib,sys
p=pathlib.Path(os.environ['T095_GREEN_CAPTURE'])
data=json.loads((p/'capture.json').read_text(encoding='utf-8'))
a=sys.argv[1:]
with (p/'calls.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(a)+'\\n')
if a==['agent','get',data['pane']]:
    counter=p/'get-count'
    n=int(counter.read_text()) if counter.exists() else 0
    counter.write_text(str(n+1))
    sys.stdout.write(data['before' if n==0 else 'after'])
elif a in (['agent','read',data['pane'],'--source',s,'--format','text'] for s in ('visible','detection')):
    sys.stdout.write(data[a[4]])
else:
    print('Unexpected replay command.',file=sys.stderr)
    sys.exit(64)
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, default=HERE / "real-green-inputs.json", help="已保存的真实采集输入；不改变产品读取器")
    parser.add_argument("--panels-only", action="store_true", help="只回归两种面板；不据此宣称关闭回落或真实绿态通过")
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError("报告已存在；不覆盖失败证据")
    inputs = json.loads(args.inputs.read_text(encoding="utf-8"))
    native = Path(inputs["native_archive"]["archive"]).read_bytes()
    directory = Path(tempfile.mkdtemp(prefix="t095-green-readback-", dir="/tmp"))
    results = []
    for label, capture in inputs["captures"].items():
        if args.panels_only and label not in ("collapsed", "expanded"):
            continue
        case = directory / label
        (case / "records").mkdir(parents=True)
        (case / "bin").mkdir()
        cutoff = capture["native_bytes"]
        if len(native) < cutoff or not native[:cutoff].endswith(b"\n"):
            raise ValueError("原生归档未覆盖原投影的完整字节截止点")
        log = case / "opaque-native-input"
        log.write_bytes(native[:cutoff])
        store = case / "native-index.sqlite"
        rows = [dict(row, native_store=str(store)) for row in inputs["launches"]]
        with (case / "records/launches.jsonl").open("x", encoding="utf-8") as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        with sqlite3.connect(store) as connection:
            connection.execute("CREATE TABLE threads (id TEXT PRIMARY KEY, rollout_path TEXT, cwd TEXT, source TEXT)")
            connection.execute("INSERT INTO threads VALUES (?,?,?,?)",
                               (inputs["native_session"], str(log), rows[-1]["cwd"], "cli"))
        data = {key: capture[key] for key in ("before", "after", "visible", "detection")}
        data["pane"] = inputs["pane"]
        (case / "capture.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        executable = case / "bin/herdr"
        executable.write_text("#!" + sys.executable + "\n" + HERDR, encoding="utf-8")
        executable.chmod(0o700)
        argv = [sys.executable, str(REPO / "scripts/agent-status"), "--root", str(case), "--launch", inputs["launch"]]
        env = dict(os.environ, HERDR_ENV="1", T095_GREEN_CAPTURE=str(case),
                   PATH=str(case / "bin") + os.pathsep + os.environ.get("PATH", ""), PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run(argv, capture_output=True, text=True, env=env, timeout=20, check=False)
        (case / "argv.json").write_text(json.dumps(argv), encoding="utf-8")
        (case / "stdout.json").write_text(result.stdout, encoding="utf-8")
        (case / "stderr.txt").write_text(result.stderr, encoding="utf-8")
        (case / "exit.txt").write_text(str(result.returncode) + "\n", encoding="utf-8")
        observed = json.loads(result.stdout)
        expected = "waiting_controller_answer" if label in ("collapsed", "expanded") else "working"
        matches_recorded = all(observed[key] == capture["observed_projection"][key]
                               for key in ("state", "reason", "raw_state", "conflicts"))
        identity_correct = (observed["worker"] == inputs["worker"] and observed["launch"] == inputs["launch"]
                            and observed["identity"]["native_session"] == inputs["native_session"])
        calls = [json.loads(line) for line in (case / "calls.jsonl").read_text(encoding="utf-8").splitlines()]
        read_only = len(calls) == 4 and all(call[:2] in (["agent", "get"], ["agent", "read"]) for call in calls)
        results.append(dict(label=label, expected=expected, actual=observed["state"], reason=observed["reason"],
                            raw_state=observed["raw_state"], returncode=result.returncode,
                            conflicts=observed["conflicts"], identity_correct=identity_correct,
                            matches_recorded=matches_recorded, read_only=read_only,
                            meets_contract=observed["state"] == expected and identity_correct,
                            command=argv, raw_output=str(case / "stdout.json"), native_bytes=cutoff))
    replay_ok = all(row["identity_correct"] and row["read_only"] and row["returncode"] in (0, 2) for row in results)
    accepted = all(row["meets_contract"] for row in results)
    files = [path for path in directory.rglob("*") if path.is_file()]
    report = dict(status="PASS" if replay_ok and accepted else "INCOMPLETE", replay_status="PASS" if replay_ok else "NO_GO",
                  regression_status="PASS" if accepted else "NO_GO", source_revision=inputs["source_revision"],
                  scope="归档两种面板读回；不新增真实运行" if args.panels_only else "归档面板与回落合同读回；不新增真实运行",
                  matches_original_projection=all(row["matches_recorded"] for row in results),
                  candidate_revision=subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip(),
                  source_archive=inputs["source_archive"], command=[sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
                  real_model_turns=0, cases=results, fixture=str(directory), files=len(files), bytes=sum(path.stat().st_size for path in files),
                  adaptations=["Recreate only the archived launch native_store path in a temporary SQLite index.",
                               "Replay captured Herdr replies through an explicit fake executable; do not contact the closed live pane.",
                               "Keep launch, worker, pane, native UUID, cwd and exact native prefix bytes unchanged."],
                  limitation="Captured get/read surfaces precede live projections; this replay does not reconstruct their unrecorded internal reads.")
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(dict(status=report["status"], replay_status=report["replay_status"], regression_status=report["regression_status"],
                          states=[row["actual"] for row in results], report=str(args.report)), ensure_ascii=False))
    return 0 if replay_ok and accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
