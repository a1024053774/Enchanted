import json
import os
from pathlib import Path
import subprocess
import sys

out = Path(__file__).resolve().parent
label, *args = sys.argv[1:]
argv = [sys.executable, str(out / "run-check.py"), label, *args]
with (out / (label + "-launcher.log")).open("x", encoding="utf-8") as stream:
    process = subprocess.Popen(argv, stdout=stream, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True, env={**os.environ, "DEBUG": "pw:browser"})
with (out / (label + "-launcher.json")).open("x", encoding="utf-8") as stream:
    json.dump(dict(pid=process.pid, argv=argv), stream, ensure_ascii=False, indent=2)
print(process.pid)
