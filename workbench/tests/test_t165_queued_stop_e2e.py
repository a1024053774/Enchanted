"""T-165：真实 Electron / daemon / PTY / Claude CLI 的确定 Stop 顺序探针。

失败方式（先列再写）：
1. 排队输入的新 Stop 先到，后登记转录时丢失完成事实，worker 留在 busy。
2. 时序未命中、原 submit 被拒或启动失败，却被算成预期红态。
3. 夹具直接修改 pane/数据库或伪造原生 turn，掩盖真实身份检查。
4. 覆盖旧摘要或把脚本化 Messages 冒称供应商模型回合。

期望来自 T-165：先到的 Stop 在原生转录核验后仍须完成同一轮。
复用 T-157 全部断言，不改其期望。只在临时源码副本的 Claude scan
入口加转录可见性屏障：queued UPS 后不读取转录，真实新 Stop 的 signal
请求返回后放开，再经真实 pane_status 入口采集。没有写 pane 或数据库。
这证明 Stop 早于转录登记，不声称控制了 CLI 的物理磁盘写入时点。
--revision 选择产品源码；--mutant drop-early-stop 在新增缓存点丢弃 Stop。
"""
import argparse
import json
from pathlib import Path
import sys
import time

import test_t157_stop_input_e2e as original
from scripted_claude import Fixture


SCAN_POINT = '      if (!pane.claudeQueuedPrompts?.length) return;'
SCAN_BARRIER = SCAN_POINT + "\n      if (!existsSync(join(this.root, 't165-transcript-visible'))) return;"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', required=True, type=Path)
    parser.add_argument('--mutant', choices=['drop-early-stop'])
    args, rest = parser.parse_known_args()
    assert not args.summary.exists(), '保留既有摘要'
    inner = args.summary.with_name(args.summary.stem + '-t157.json')
    ordering = {}

    class OrderedFixture(Fixture):
        def __init__(self, *values, **options):
            patches = list(options.pop('patches', ()))
            patches.append(('src/panes.ts', SCAN_POINT, SCAN_BARRIER))
            if args.mutant:
                patches.append(('src/panes.ts', 'pane.claudeEarlyStops.push({ raw, received_at, transfer });',
                                '/* T-165 mutant: discard the authenticated early Stop. */'))
            super().__init__(*values, patches=patches, **options)

        def wait(self, label, predicate, timeout=90):
            if label != 'worker 及门禁反馈回到空闲':
                return super().wait(label, predicate, timeout)

            def early_stop_returned():
                trace = self.request('orchestration_events', task='demo+T-157-probe')['events']
                queued = next((e for e in trace if e['type'] == 'claude_prompt_queued'), None)
                if not queued:
                    return False
                requests = [e for e in trace if e['type'] == 'request_received' and
                            e['data']['input'].get('command') == 'signal' and e['seq'] > queued['seq']]
                for request in requests:
                    value = json.loads(request['data']['input']['raw_stdin'])
                    if value.get('hook_event_name') != 'Stop' or value.get('prompt_id') == queued['data']['prompt_id']:
                        continue
                    if not any(e['type'] == 'request_result' and e['data'].get('id') == request['data']['id'] for e in trace):
                        continue
                    assert not any(e['type'] == 'turn_start_signal' and e['data'].get('prompt_id') == value['prompt_id']
                                   for e in trace), '时序屏障未成立：新 turn 已登记'
                    ordering.update(stop=value, request_seq=request['seq'], queued_seq=queued['seq'],
                                    before_release=trace)
                    return True
                return False

            super().wait('真实新 Stop 已返回，转录尚未登记', early_stop_returned, 30)
            (self.state / 't165-transcript-visible').write_text('visible\n', encoding='utf-8')
            # Baseline failure must reach the unchanged T-157 assertions, with
            # complete diagnostics, rather than exit only through a wait timeout.
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                value = predicate()
                if value:
                    return value
                assert not self.api.error, self.api.error
                time.sleep(.2)
            ordering['idle_timeout'] = True
            return False

    original.Fixture = OrderedFixture
    sys.argv = [sys.argv[0], '--summary', str(inner), *rest]
    original.main()
    report = json.loads(inner.read_text(encoding='utf-8'))
    trace = report['observed'].get('final_timeline', [])
    stop_id = ordering.get('stop', {}).get('prompt_id')
    starts = [e for e in trace if e['type'] == 'turn_start_signal' and
              e['data'].get('prompt_id') == stop_id and e['data'].get('origin') == 'native-transcript']
    ordered = bool(stop_id and starts and ordering['request_seq'] < starts[0]['seq'])
    report['checks'].append(dict(name='real_stop_before_native_turn_registration', passed=ordered))
    pane = report['observed'].get('final_pane', {})
    report['red_reproduced'] = bool(ordered and not report['errors'] and pane.get('state') == 'busy' and
        pane.get('active') and any(e['type'] == 'stop_not_matched' and e['data'].get('prompt_id') == stop_id for e in trace) and
        any(c['name'] == 'original_stop_submit_accepted' and c['passed'] for c in report['checks']))
    report['ordering'] = ordering
    report['mutant'] = args.mutant
    report['scope'] = 'real CLI/Electron with controlled transcript visibility; no vendor model calls'
    report['status'] = 'PASS' if not report['errors'] and all(c['passed'] for c in report['checks']) else 'INCOMPLETE'
    with args.summary.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(dict(status=report['status'], red_reproduced=report['red_reproduced'], summary=str(args.summary))))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
