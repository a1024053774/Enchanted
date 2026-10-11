#!/usr/bin/env python3
"""Append native input; emit only the empty protocol object, never a decision."""
import datetime as dt
import json
import os
from pathlib import Path
import sys

raw=sys.stdin.read()
payload=json.loads(raw)
record={'received_at':dt.datetime.now(dt.timezone.utc).isoformat(),'raw_stdin':raw,'payload':payload}
with Path(sys.argv[1]).open('a',encoding='utf-8') as stream:
    stream.write(json.dumps(record,ensure_ascii=False)+'\n');stream.flush();os.fsync(stream.fileno())
print('{}')
