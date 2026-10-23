"""只读统计本票原生 Claude 根提示；不启动模型，不读取其他项目。"""
from collections import Counter
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE = Path('/Users/luckye/.claude/projects')
PREFIXES = ('-private-tmp-t155-dogfood-lv2rm2nt-',
            '-private-tmp-t155-dogfood-ohzs-78v-')


def main():
    for name in ('t155-dogfood-lv2rm2nt', 't155-dogfood-ohzs_78v'):
        state = Path('/private/tmp') / name / 'state'
        if (state / 'daemon.pid').exists() or (state / 'control.sock').exists():
            raise RuntimeError('须先确认后台停止：' + str(state))
    sessions = []
    for directory in sorted(BASE.glob('*t155-dogfood*')):
        if not directory.name.startswith(PREFIXES):
            continue
        for source in sorted(directory.rglob('*.jsonl')):
            rows = [json.loads(line) for line in source.read_text(encoding='utf-8').splitlines()]
            prompts, excluded, models = [], Counter(), Counter()
            for row in rows:
                if row.get('type') == 'assistant':
                    models[row.get('message', {}).get('model', 'unknown')] += 1
                if row.get('type') != 'user':
                    continue
                content = row.get('message', {}).get('content')
                text = content if isinstance(content, str) else '\n'.join(
                    block.get('text', '') for block in (content or []) if block.get('type') == 'text')
                if row.get('isMeta'):
                    excluded['meta_skill_expansion'] += 1
                elif row.get('interruptedMessageId'):
                    excluded['interrupt_marker_not_new_prompt'] += 1
                elif not text.strip():
                    excluded['tool_result_without_root_text'] += 1
                else:
                    if row.get('isSidechain'):
                        raise RuntimeError('发现未计入场景的子会话，须人工核对：' + str(source))
                    prompts.append({'uuid': row['uuid'], 'timestamp': row['timestamp']})
            sessions.append({'source': str(source), 'session': source.stem,
                             'turns': len(prompts), 'prompts': prompts,
                             'excluded': dict(excluded), 'assistant_models': dict(models)})
    result = {'status': 'PASS', 'scope': '预算的根提示回合计数，不是供应商 API 请求数或 token/cost 计量',
              'method': '原生 JSONL 中非 sidechain、非 isMeta、非 interruptedMessageId，且有文本的 user 条目；含被 Esc 中断的原提示、门禁回执、问题答复和人工输入；工具结果及技能展开不另算根回合。',
              'command': 'python3 evidence/2026-10-23-batch24/T-155/count_native_turns.py',
              'total_turns': sum(s['turns'] for s in sessions), 'sessions': sessions}
    if not sessions or result['total_turns'] > 60:
        raise RuntimeError('会话缺失或预算超限，须保留现场上报：' + str(result['total_turns']))
    with (HERE / 'native-turns.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'sessions': len(sessions), 'total_turns': result['total_turns']}))


if __name__ == '__main__':
    main()
