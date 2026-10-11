#!/usr/bin/env python3
"""Append the hook stdin verbatim; never make an approval decision."""
import datetime as dt
import json
import os
from pathlib import Path
import sys

raw = sys.stdin.read()
payload = json.loads(raw)
destination = Path(sys.argv[1])
record = {'received_at': dt.datetime.now(dt.timezone.utc).isoformat(),
          'raw_stdin': raw, 'payload': payload}
with destination.open('a', encoding='utf-8') as stream:
    stream.write(json.dumps(record, ensure_ascii=False) + '\n')
    stream.flush()
    os.fsync(stream.fileno())
