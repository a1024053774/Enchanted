"""Archive only A15 counts, approved tools/results, error codes and I1 pending receipt."""
import argparse
import json
from pathlib import Path
import traceback
import importlib.util

BASE = Path(__file__).resolve().parent
ROOT = Path('/private/tmp/t078-2-09b-run-yp09xosq')


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def project(audit):
    assert audit['status'] == 'PASS' and audit['root'] == str(ROOT)
    roles = {}
    for role in ['ideation', 'executor']:
        value = audit['roles'][role]
        roles[role] = {'request_count': value['POST'], 'response_count': value['responses_200'],
                       'http_POST_files': len(value['requests']), 'roots': value['roots'],
                       'hook_counts': {kind: len([item for item in value['hooks'] if item['event'] == kind])
                                       for kind in ['UserPromptSubmit', 'Stop', 'PermissionRequest']},
                       'tools': [{'phase': item['phase'], **item['tools']} for item in audit['phases']
                                 if item['role'] == role and 'tools' in item]}
    return {'schema': 1, 'status': 'PASS', 'roles': roles,
            'error_codes': [{'phase': item['phase'], 'error_code': item['relay']['error_code']}
                            for item in audit['phases'] if 'error_code' in item.get('relay', {})],
            'original_I1_pending_receipt': audit['original_I1_pending_receipt'],
            'target_byte_count': audit['target_byte_count'], 'target_delta_hex': audit['target_delta_hex'],
            'raw_messages_retained': False, 'headers_metadata_system_auth_retained': False}


def collect(owner):
    evidence = load_module('a15_final_files', BASE / 'a15-final-evidence.py')
    return project(evidence.collect(owner))


def archive_projection(summary, out, archive):
    helper = load_module('verified_archive_members', BASE / 'redact-a14-scene.py')
    return helper.archive_projection(summary, out, archive)


def verify_archive(result):
    helper = load_module('verified_archive_members', BASE / 'redact-a14-scene.py')
    return helper.verify_archive(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--owner', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); owner = json.loads(args.owner.read_bytes())
    assert owner['root'] == str(ROOT)
    out = args.output.resolve(); out.mkdir(exist_ok=False)
    result = {'status': 'BLOCKED', 'root': str(ROOT), 'scope': __doc__}
    try:
        summary = collect(owner)
        archive = Path(owner['external_archive'])
        assert archive == Path('/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09b-a15-redacted-01/scene.tar.gz')
        assert Path('/Volumes/WD-Elements').is_mount() and archive.parent.parent.resolve() == archive.parent.parent
        archive.parent.mkdir(exist_ok=False)
        inventory = archive_projection(summary, out, archive)
        result.update(archive=str(archive), archive_bytes=archive.stat().st_size, inventory=inventory,
                      summary_file=str(out / 'projection/summary.json'), byte_readback='PASS')
        assert verify_archive(result) == summary
        result['status'] = 'PASS'
    except Exception as error:
        result.update(error_type=type(error).__name__, traceback=traceback.format_exc())
    (out / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result.get(key) for key in ['status', 'archive', 'byte_readback', 'error_type']}))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
