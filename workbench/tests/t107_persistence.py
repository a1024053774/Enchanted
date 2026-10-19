"""Independent exact values for every fixture SQLite table and trace file."""
import base64
import json
from pathlib import Path
import sqlite3
import sys


def persistence(state):
    state = Path(state)
    databases = {}
    for path in sorted(state.rglob('*.sqlite3')):
        with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True) as db:
            db.execute('PRAGMA query_only=ON')
            schema = db.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name').fetchall()
            tables = {}
            for kind, name, _, _ in schema:
                if kind == 'table':
                    rows = db.execute('SELECT * FROM "' + name.replace('"', '""') + '"').fetchall()
                    encoded = [[{'blob_base64': base64.b64encode(value).decode('ascii')} if isinstance(value, bytes) else value for value in row] for row in rows]
                    tables[name] = sorted(encoded, key=lambda row: json.dumps(row, ensure_ascii=False))
            databases[str(path.relative_to(state))] = dict(schema=schema, tables=tables)
    traces = {str(path.relative_to(state)): base64.b64encode(path.read_bytes()).decode('ascii')
              for path in sorted((state / 'traces').rglob('*')) if path.is_file()}
    return dict(databases=databases, traces=traces)


if __name__ == '__main__':
    print(json.dumps(persistence(sys.argv[1]), ensure_ascii=False))
