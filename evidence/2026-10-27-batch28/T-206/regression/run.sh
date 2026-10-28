#!/bin/sh
# T-206 regression: e2e tests whose user-input checks touch managed pane input. Run from workbench/tests.
R=../../evidence/2026-10-27-batch28/T-206/regression
python3 test_t145_mouse_reports_e2e.py --summary $R/t145-1.json
python3 test_t159_split_e2e.py --summary $R/t159-1.json
python3 test_t133_t134_records_metrics_e2e.py --summary $R/t133-t134-1.json
python3 test_t166_busy_input_e2e.py --summary $R/t166-separate-1.json
python3 test_t166_queued_input.py --summary $R/t166-queued-1.json
# After updating expectations that assumed one record per key (see RESULTS.md):
python3 test_t145_mouse_reports_e2e.py --summary $R/t145-2.json
python3 test_t133_t134_records_metrics_e2e.py --summary $R/t133-t134-2.json
python3 test_t166_queued_input.py --summary $R/t166-queued-2.json
python3 test_t078_input_entry.py --source ../.. --output $R/t078-input-entry-1 --runtime-probe --input-failures
