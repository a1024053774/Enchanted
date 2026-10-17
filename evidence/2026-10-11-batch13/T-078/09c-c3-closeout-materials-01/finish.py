"""Require independent C3 tar readback/review before the unchanged owner finish."""
import json
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parents[4];BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SOURCE/'workbench/tests'))
import t078_raw_retention as raw


def main():
    here=Path(__file__).resolve().parent;owner=raw.read_json(here/'capture-owner.json')
    approval=raw.read_json(here/'cleanup-approval.json');paths=raw.read_json(here/'paths.json')
    check=raw.read_json(paths['tar_check']+'/result.json');review=raw.read_json(paths['readback']+'/review.json')
    independent=raw.read_json(paths['readback']+'/readback.json');capture=raw.read_json(paths['capture']+'/capture-result.json')
    for value in [check,review]:
        raw.require(value['status']=='PASS' and value['root']==owner['root'] and value['source_revision']==owner['source_revision'] and
            value['archive']==paths['archive'],'independent_C3_archive_check_required')
    raw.require(check['POST']=={'ideation':7,'executor':1} and check['roots']=={'ideation':4,'executor':1} and check['permissions']==3 and
        check['target_delta_hex']=='1b' and check['no_ack'] is True and 120000<check['independent_emergency_age_ms']<150000,'C3_contract_required')
    raw.require(review['approved_by']=='executor' and review['approval_ref'] and review['scene_status']=='PASS' and
        review['credential_scan']=='PASS' and review['counts']==independent['counts']==raw.readback(paths['archive']), 'signed_independent_review_required')
    result=raw.finish(owner,approval,capture,independent,Path(paths['finish']),raw.NativeRuntime(owner))
    print(json.dumps(result,ensure_ascii=False));return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
