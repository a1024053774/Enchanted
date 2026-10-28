#!/bin/sh
# T-207 regression: e2e tests that press Esc or type into a busy managed pane. Run from workbench/tests.
R=../../evidence/2026-10-27-batch28/T-207/regression
python3 test_t206_input_on_send_e2e.py --summary $R/t206-1.json
python3 test_t166_busy_input_e2e.py --summary $R/t166-busy-1.json
