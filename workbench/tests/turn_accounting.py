"""Read main turns from a confirmed, standalone SQLite evidence archive."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3


def read_main_turns(database, launch):
    database = Path(database).resolve(strict=True)
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as db:
        rows = [json.loads(row[0]) for row in db.execute(
            "SELECT data FROM orchestration_events WHERE type='native_record' AND launch=? ORDER BY seq", (launch,))]
    native_ids = {row['record']['payload']['id'] for row in rows
                  if row['record']['type'] == 'session_meta' and row['record']['payload'].get('source') == 'cli'}
    if not native_ids:
        return {'main_turns': None, 'native_session': None, 'turn_ids': [], 'reason': 'No root CLI session record'}
    if len(native_ids) != 1:
        raise ValueError('The archive contains multiple root CLI session identities')
    native = next(iter(native_ids))
    turns = {row['record']['payload']['turn_id'] for row in rows if row['file'].endswith(native + '.jsonl')
             and row['record']['type'] == 'event_msg' and row['record']['payload'].get('type') == 'task_started'}
    return {'main_turns': len(turns), 'native_session': native, 'turn_ids': sorted(turns), 'database': str(database)}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--launch', required=True)
    args = parser.parse_args()
    print(json.dumps(read_main_turns(args.database, args.launch), ensure_ascii=False))
