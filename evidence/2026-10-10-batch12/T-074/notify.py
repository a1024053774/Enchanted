#!/usr/bin/env python3
"""Record the native notify JSON argument without changing approval behavior."""
import datetime
import json
import os
import sys

record = {"received_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
          "payload": json.loads(sys.argv[2])}
with open(sys.argv[1], "a", encoding="utf-8") as stream:
    stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    stream.flush()
    os.fsync(stream.fileno())
