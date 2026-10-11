"""Shared probe shutdown observation and standalone SQLite archival.

Only caller-owned PIDs are observed. No process is killed by this helper.
"""
from contextlib import closing
import shutil
import sqlite3
import subprocess
import time


def archive_and_cleanup(state, output, isolated, cleanup_pids, run, save, verdict):
    # A file snapshot is coherent only after this probe's writers have exited.
    stopped_for_archive = False
    try:
        deadline = time.monotonic() + 10
        while True:
            remaining = run(['/bin/ps', '-o', 'pid=,ppid=,pgid=,command=', '-p', ','.join(map(str, sorted(cleanup_pids)))], check=False) if cleanup_pids else None
            if remaining is not None and (remaining.returncode not in (0, 1) or getattr(remaining, 'stderr', '').strip()):
                raise RuntimeError('Process readback failed; exit is unconfirmed')
            if not (state / 'daemon.pid').exists() and not (remaining and remaining.stdout.strip()):
                stopped_for_archive = True
                break
            if time.monotonic() >= deadline:
                verdict.update(status='BLOCKED', cleanup_error='停止期限内仍有未确认退出的进程，保留隔离 home 等主控核对')
                break
            time.sleep(0.1)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        verdict.update(status='BLOCKED', cleanup_error=str(error))
    # Never open the original WAL database for writing. Normalize only the
    # copied archive to DELETE mode, so it does not need -wal/-shm sidecars.
    try:
        if state.exists():
            for name in ('daemon.stdout.log', 'daemon.stderr.log'):
                if (state / name).exists():
                    with (output / name).open('xb') as stream:
                        stream.write((state / name).read_bytes())
            if (state / 'state.sqlite3').exists():
                if not stopped_for_archive:
                    raise RuntimeError('Database archive requires confirmed daemon stop')
                destination = output / 'state.sqlite3'
                with destination.open('xb') as stream:
                    stream.write((state / 'state.sqlite3').read_bytes())
                wal = state / 'state.sqlite3-wal'
                if wal.exists():
                    with (output / 'state.sqlite3-wal').open('xb') as stream:
                        stream.write(wal.read_bytes())
                with closing(sqlite3.connect(destination)) as dest:
                    if dest.execute('PRAGMA journal_mode=DELETE').fetchone() != ('delete',):
                        raise RuntimeError('Archive journal mode did not become DELETE')
                    if dest.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
                        raise RuntimeError('Archive integrity check failed')
                verdict['database_archive'] = {'path': str(destination), 'journal_mode': 'delete', 'integrity': 'ok'}
    except (OSError, RuntimeError, sqlite3.Error) as error:
        verdict.update(status='BLOCKED', archive_error=str(error))
    finally:
        try:
            if stopped_for_archive:
                shutil.rmtree(isolated)
                verdict['isolated_home_removed'] = True
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
            verdict.update(status='BLOCKED', cleanup_error=str(error))
        finally:
            save('verdict.json', verdict)

