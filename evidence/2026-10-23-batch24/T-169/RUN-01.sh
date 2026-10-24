#!/bin/zsh
# T-169 checks. Run from the repository root. Each run writes a new summary; existing files are kept.
set -u
O=evidence/2026-10-23-batch24/T-169/runs-$(date -u +%Y%m%dT%H%M%SZ); mkdir -p $O
T=workbench/tests/test_t166_busy_input_e2e.py
python3 -B $T --scenario absorbed --revision 73b7e7873 --summary $O/red.json        # expect red_reproduced=true
python3 -B $T --scenario absorbed --summary $O/green.json                           # expect PASS
python3 -B $T --summary $O/separate.json                                            # T-166 scenario, expect PASS
# Mutant (clear the queue at Stop) is a throwaway commit; recreate it from mutant-clear-queue-at-stop.diff, then:
#   python3 -B $T --revision <mutant-sha> --summary $O/mutant.json                  # expect queued_native_turn_bound_and_completed to fail
python3 -B workbench/tests/test_t157_stop_input_e2e.py --summary $O/t157-stop-input.json
python3 -B workbench/tests/test_t165_queued_stop_e2e.py --summary $O/t165.json
python3 -B workbench/tests/test_t166_queued_input.py --summary $O/t166-host.json
python3 -B workbench/tests/test_t157_turn_identity.py --summary $O/t157-identity.json
