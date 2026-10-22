"""T-135 轨迹归档。真实后台、门禁、终端主控，真实 Claude Code worker（模型是本地脚本化接口），真实 Electron 设置页。

期望来自 ticket 与原生记录本身：归档解压后必须正好等于原生记录从头到索引末尾的那一段（只到完整行）；第二回合后
新增的一段接在第一段后面；末尾没写完的半行不进归档，写完后进；设置页显示的占用等于归档目录里文件的实际大小。

失败方式（先列再写）：
1. 回合结束后没有归档，或者归档与原生记录对不上。
2. 不是增量：已归档的部分又复制一遍，或者后一段没接上前一段。
3. 半写入的末行被复制进归档。
4. 归档写到数据目录以外（例如原生记录所在目录）。
5. 设置页的占用与归档目录实际大小不一致，或读取失败时显示成 0。
--revision 在该版本源码上跑（修前没有归档）；--mutant 跑已知坏实现。
"""
import argparse
import gzip
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture, prompt_text, working_directory  # noqa: E402
import re  # noqa: E402

TYPED = 'T-135：第二回合，说一句就好'
PARTIAL = b'{"type":"t135-partial","note":"half'
REST = b' written"}\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['partial-line-copied', 'not-incremental'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, checks=[])
    patches = {
        'partial-line-copied': [('src/trajectoryArchive.ts', 'const complete = chunk.lastIndexOf(10) + 1;', 'const complete = chunk.length;')],
        'not-incremental': [('src/trajectoryArchive.ts', 'const start = Number(last?.end ?? 0);', 'const start = 0 * Number(last?.end ?? 0);')],
    }.get(args.mutant, [])

    def plan(body):
        text = prompt_text(body)
        assert '显式交付' in text, '只有 worker 会话'
        cwd = working_directory(body)
        submit = re.search(r'显式交付：\n(.+)\n', text).group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        return 'worker', [
            ('Write', dict(file_path=f'{cwd}/hello.txt', content='hello\n')),
            ('Bash', dict(command='git add hello.txt', description='stage')),
            ('Bash', dict(command='git commit -q -m "T-135 fixture change"', description='commit')),
            ('Bash', dict(command=submit, description='submit')),
        ], '已交付。'

    fixture = Fixture('t135-', plan, revision=args.revision, patches=patches)
    report['fixture'] = str(fixture.dir)
    electron = None

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def rows():
        with sqlite3.connect(f'file:{fixture.state / "state.sqlite3"}?mode=ro', uri=True) as connection:
            connection.row_factory = sqlite3.Row
            try:
                return [dict(row) for row in connection.execute('SELECT * FROM trajectory_archive ORDER BY seq')]
            except sqlite3.OperationalError:
                return []

    def archived(row):
        return gzip.decompress(Path(row['file']).read_bytes())

    def turn_ends():
        return [e for e in fixture.request('orchestration_events')['events'] if e['type'] == 'turn_end_signal' and e['launch'] == worker]

    try:
        fixture.start(args.claude, {'README.md': 'demo\n', 'check.py': 'import pathlib, sys\nsys.exit(0 if pathlib.Path("hello.txt").is_file() else 1)\n'})
        fixture.card('T-1', 'hello.txt', 'check.py')
        dispatched = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write')
        assert dispatched.get('ok'), dispatched
        worker = dispatched['attempt']['runtime_identity']['launch']
        native = fixture.request('launch_show', fixture.operator, launch=worker)['launch'].get('native_session')

        # 1: after the first turn the archive holds the transcript up to its last complete line.
        fixture.wait('第一回合结束', lambda: len(turn_ends()) >= 1, 180)
        first = fixture.wait('第一段归档', lambda: rows(), 30)
        assert len({row['launch'] for row in first}) == 1 and first[0]['launch'] == worker, first
        source = Path(first[0]['source'])
        report['source'], report['first_rows'] = str(source), [{k: r[k] for k in ('start', 'end', 'stored_bytes')} for r in first]
        transcript = source.read_bytes()
        end1 = first[-1]['end']
        check('first_turn_archived', source.name == f'{native}.jsonl' and end1 > 0 and transcript[end1 - 1:end1] == b'\n' and
              archived(first[-1]) == transcript[:end1], dict(end=end1, transcript=len(transcript)))
        check('archive_inside_data_directory', all(Path(r['file']).resolve().is_relative_to((fixture.state / 'archive').resolve()) for r in first) and
              not Path(first[0]['file']).resolve().is_relative_to(source.parent.resolve()), [r['file'] for r in first])

        # 2: the user's second turn; its increment starts where the first ended.
        window = fixture.request('window_open', fixture.operator, launch=worker, task=dispatched['attempt']['task_id'])
        assert window['ok'], window
        for sequence, data in enumerate(['\x1b[200~' + TYPED + '\x1b[201~', '\r'], 1):
            assert fixture.request('window_input', window['identity'], sequence=sequence, request_id=str(uuid.uuid4()), data=data)['ok']
            time.sleep(.5)
        # The first turn may already have been followed by the gate's receipt turn, so wait for the user's own turn.
        second = fixture.wait('第二回合归档', lambda: (lambda r: r if TYPED.encode() in archived(r[-1]) else None)(rows()), 150)
        transcript = source.read_bytes()
        end2 = second[-1]['end']
        report['second_rows'] = [{k: r[k] for k in ('start', 'end', 'stored_bytes')} for r in second]
        check('second_turn_continues_first', TYPED.encode() in transcript[end1:end2] and
              all(b['start'] == a['end'] for a, b in zip(second, second[1:])) and second[0]['start'] == 0 and
              archived(second[-1]) == transcript[:end2], report['second_rows'])

        # 3: a half-written last line waits; once complete it is archived (the 30 s sweep).
        fixture.wait('worker 空闲', lambda: fixture.request('status', fixture.operator, task='T-1')['task']['state'] == 'submitted', 30)
        settled = len(source.read_bytes())
        with source.open('ab') as handle:
            handle.write(PARTIAL)
        time.sleep(35)
        after_partial = rows()
        check('half_line_not_archived', PARTIAL not in archived(after_partial[-1]) and after_partial[-1]['end'] <= settled,
              dict(end=after_partial[-1]['end'], settled=settled))
        with source.open('ab') as handle:
            handle.write(REST)
        completed = fixture.wait('补完的行进归档', lambda: (lambda r: r if PARTIAL + REST in archived(r[-1]) else None)(rows()), 45)
        transcript = source.read_bytes()
        check('completed_line_archived', archived(completed[-1]) == transcript[:completed[-1]['end']] and transcript.endswith(PARTIAL + REST),
              completed[-1]['end'])

        # 5: the settings page shows the archive's real size on disk.
        on_disk = sum(path.stat().st_size for path in (fixture.state / 'archive').rglob('*') if path.is_file())
        electron = Electron(fixture, 't135-' + fixture.dir.name[5:])
        electron.until('窗口就绪', "!!document.querySelector('[aria-label=\"设置\"]')")
        electron.evaluate("document.querySelector('[aria-label=\"设置\"]').click()")
        shown = electron.until('归档占用', "(e=>e&&{sessions:e.dataset.archiveSessions,bytes:e.dataset.archiveBytes,text:e.textContent})(document.querySelector('[data-archive-bytes]'))", 20)
        electron.evaluate("document.querySelector('[data-archive-bytes]').scrollIntoView()")
        electron.screenshot(fixture.out / '01-settings-archive.png')
        report['settings'], report['on_disk'] = shown, on_disk
        check('settings_shows_archive_size', shown['sessions'] == '1' and int(shown['bytes']) == on_disk, dict(shown=shown, on_disk=on_disk))
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['api_snapshot'] = fixture.api.snapshot()
        raise
    finally:
        try:
            if electron:
                electron.stop()
        finally:
            fixture.stop()
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
