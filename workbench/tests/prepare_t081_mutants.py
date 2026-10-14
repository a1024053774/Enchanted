"""T-081：在一次性副本内取消一项门禁约束，保存完整补丁。"""
import difflib
from pathlib import Path
import shutil


MUTATIONS = {
    'oracle': [('      await this.checkOraclePaths(task, attempt, v);',
                '      // T-081 mutant: omit the protected-oracle check.')],
    'completion': [(
        '        const result = await this.execute(taskId, command.argv, workspace);\n        v.result = result;',
        '        const observed = await this.execute(taskId, command.argv, workspace);\n'
        '        const result = { ...observed, returncode: 0, exit: 0 };\n        v.result = result;')],
    'paths': [('      await this.checkPaths(task, attempt, v);',
               '      // T-081 mutant: omit the path boundary check.')],
    'trailer_shape': [(
        '        else if (Object.keys(trailers).length !== required.length ||\n'
        '          required.some((key) => trailers[key]?.length !== 1 || !trailers[key]![0])) error = "invalid_trailers";',
        '        else if (false) error = "invalid_trailers";')],
    'trailer_task': [(
        '        if (trailers.task?.some((value) => value !== task.task_id)) error = "trailer_task_mismatch";',
        '        if (false) error = "trailer_task_mismatch";')],
    'trailer_attempt': [(
        '        else if (trailers.attempt![0] !== attempt.attempt_id || trailers.session![0] !== attempt.session_id || trailers.role![0] !== "worker")',
        '        else if (trailers.session![0] !== attempt.session_id || trailers.role![0] !== "worker")')],
    'latest_head': [(
        '          requireGate(v.M, "not_verified");\n          const actual = await this.integration(task);',
        '          requireGate(v.M, "not_verified");\n'
        '          v.M = await this.git(taskId, attempt.workspace, ["rev-parse", "HEAD"]);\n'
        '          const actual = await this.integration(task);')],
    # Both sites implement the same constraint: only current_attempt may submit.
    # Selecting an archived attempt after removing only the first guard must
    # also avoid the current() lookup, otherwise the mutant still enforces it.
    'historical_attempt': [(
        '      if (args.attempt && !historicalAttempt)\n',
        '      if (args.attempt && !historicalAttempt && args.command !== "submit")\n'), (
        '      const attempt = historicalAttempt ?? this.current(task, args.attempt);',
        '      const attempt = args.command === "submit" && args.attempt\n'
        '        ? JSON.parse(String(this.db.prepare("SELECT data FROM attempts WHERE id=?").get(args.attempt)!.data)) as A2AAttempt\n'
        '        : historicalAttempt ?? this.current(task, args.attempt);')],
}

CASE_MUTANT = {
    'oracle_test': 'oracle', 'oracle_entry': 'oracle',
    'self_report_unchanged': 'completion', 'self_report_wrong': 'completion',
    'stale_attempt': 'historical_attempt', 'after_review': 'latest_head',
    'deny_path': 'paths', 'trailer_partial': 'trailer_shape',
    'trailer_duplicate': 'trailer_shape', 'trailer_task': 'trailer_task',
    'trailer_attempt': 'trailer_attempt',
}


def prepare(source, destination, name, patch_path):
    source, destination = Path(source), Path(destination)
    if destination.exists():
        raise RuntimeError('变异目录已存在，不覆盖：' + str(destination))
    relative = Path('workbench/src/gates/core.ts')
    original = (source / relative).read_text(encoding='utf-8')
    changed = original
    for before, after in MUTATIONS[name]:
        if changed.count(before) != 1:
            raise RuntimeError('变异定位须唯一：' + name + '\n' + before)
        changed = changed.replace(before, after, 1)
    shutil.copytree(source, destination, symlinks=True)
    (destination / relative).write_text(changed, encoding='utf-8')
    patch = ''.join(difflib.unified_diff(original.splitlines(True), changed.splitlines(True),
                                      fromfile='candidate/' + str(relative), tofile=name + '/' + str(relative)))
    with Path(patch_path).open('x', encoding='utf-8') as stream:
        stream.write(patch)
    return {'name': name, 'source': str(destination), 'changed_paths': [str(relative)],
            'patch': str(patch_path), 'sites': len(MUTATIONS[name])}
