import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

out = Path(__file__).resolve().parent
launch, label = sys.argv[1:]
data = json.loads((out / launch).read_text(encoding="utf-8"))
results = []
for process in data.get("processes", [data]):
    pid = process.get("pid")
    if not pid:
        continue
    observed = subprocess.run(["ps", "-p", str(pid), "-o", "command="], text=True, capture_output=True)
    expected = process["argv"][-1]
    result = dict(pid=pid, command=observed.stdout.strip(), expected=expected)
    if observed.returncode:
        result["already_exited"] = True
    else:
        assert expected in observed.stdout, result
        os.kill(pid, signal.SIGTERM)
        for _ in range(100):
            if subprocess.run(["ps", "-p", str(pid)], stdout=subprocess.DEVNULL).returncode:
                break
            time.sleep(.1)
        result["exited"] = subprocess.run(["ps", "-p", str(pid)], stdout=subprocess.DEVNULL).returncode != 0
    results.append(result)
with (out / (label + ".json")).open("x", encoding="utf-8") as stream:
    json.dump(dict(launch=launch, processes=results, retained_root=data["root"]), stream, ensure_ascii=False, indent=2)
print(json.dumps(results, ensure_ascii=False))
