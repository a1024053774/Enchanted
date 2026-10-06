#!/usr/bin/env python3
"""Save real Cargo build output, elapsed time and sampled disk occupancy."""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument("--entry", type=Path, required=True)
parser.add_argument("--manifest", type=Path, required=True)
parser.add_argument("--slot", required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--parallel", type=int, choices=[1, 2], default=1)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
cache = Path("/Volumes/WD-Elements/dev-cache/a2a")
paths = [cache / "target" / args.slot, cache / "cargo-home", cache / "zig-cache", cache / "tmp" / args.slot]


def sample():
    sizes = {}
    for path in paths:
        result = subprocess.run(["du", "-sk", str(path)], capture_output=True, text=True)
        sizes[str(path)] = int(result.stdout.split()[0]) * 1024 if result.returncode == 0 else None
    internal = os.statvfs("/System/Volumes/Data")
    external = os.statvfs("/Volumes/WD-Elements")
    return {"elapsed_s": round(time.monotonic() - start, 3), "bytes": sizes,
            "internal_available_bytes": internal.f_bavail * internal.f_frsize,
            "external_available_bytes": external.f_bavail * external.f_frsize}


env = os.environ.copy()
env["MUSTER_BUILD_SLOT"] = args.slot
command = ["/usr/bin/time", "-lp", str(args.entry.resolve()), "build", "--locked", "--manifest-path", str(args.manifest.resolve()), "-j", "4"]
start = time.monotonic()
samples = [sample()]
metadata = {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "argv": command,
            "cwd": str(Path.cwd()), "parallel": args.parallel,
            "env": {"MUSTER_BUILD_SLOT": args.slot},
            "source": str(args.manifest.parent.resolve())}
(args.output / "command.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
processes = []
streams = []
launches = []
for index in range(args.parallel):
    out = (args.output / f"build-{index}.stdout").open("x", encoding="utf-8")
    err = (args.output / f"build-{index}.stderr").open("x", encoding="utf-8")
    streams.extend([out, err])
    launches.append(time.monotonic() - start)
    processes.append(subprocess.Popen(command, env=env, stdout=out, stderr=err))
finishes = {}
while len(finishes) != len(processes):
    for index, process in enumerate(processes):
        if index not in finishes and process.poll() is not None:
            finishes[index] = time.monotonic() - start
    if len(finishes) != len(processes):
        samples.append(sample())
        with (args.output / "samples.jsonl").open("a", encoding="utf-8") as log:
            log.write(json.dumps(samples[-1]) + "\n")
        time.sleep(5)
samples.append(sample())
for stream in streams:
    stream.close()
result = {**metadata, "exit": [p.returncode for p in processes], "launch_s": launches,
          "observed_finish_s": finishes, "before": samples[0], "after": samples[-1],
          "sampled_peak_bytes": {str(p): max((s["bytes"][str(p)] or 0) for s in samples) for p in paths},
          "sampling": "du -sk every 5 seconds plus scan time; peak is a sampled lower bound, not an exact peak"}
(args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
raise SystemExit(0 if all(p.returncode == 0 for p in processes) else 1)
