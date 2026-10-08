"""Environment-enabled observation of the two unchanged Python transports."""
import json
import os
import sys
import time

if os.environ.get("A2A_TIMING_ENABLE") == "1":
    target = os.environ["A2A_TIMING_MARKS"]
    entry = os.environ["A2A_TIMING_PY_ENTRY"]
    launcher = os.environ["A2A_TIMING_PY_LAUNCHER"]

    def mark(event, **detail):
        record = dict(event=event, ns=time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW),
                      pid=os.getpid(), **detail)
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.write(fd, (json.dumps(record) + "\n").encode("utf-8"))
        finally:
            os.close(fd)

    mark("python_site_ready")

    def profile(frame, event, arg):
        filename = frame.f_code.co_filename
        if event == "call" and frame.f_code.co_name == "<module>":
            if filename == entry:
                mark("python_entry_start")
            elif filename == launcher:
                mark("launcher_python_start")
        elif event == "c_call" and getattr(arg, "__name__", None) == "execv" and filename == entry:
            mark("entry_exec")
        elif (event == "call" and frame.f_code.co_name == "execvpe" and frame.f_back
              and frame.f_back.f_code.co_filename == launcher):
            mark("launcher_exec")
        return profile

    sys.setprofile(profile)
