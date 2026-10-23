#!/bin/zsh
# T-107 acceptance 4 (second half): a project added through the sidebar's "打开项目目录" (the macOS open panel) matches the
# daemon's registration. Run from the main checkout. The panel is operated by a Codex session through Computer Use (user,
# 2026-10-23: "让 Codex worker 用 Computer Use"), in the user's own ~/.codex, where the Computer Use plugin and its grants are;
# the test reads the result from the daemon and the window, never from Codex's account.
# green-01 ran the test before codex_finished_the_steps and the post-stop registration check were added; mutant-pick-ignored-01
# then failed only because Codex stopped on its own, so the test was changed to check the registration regardless and both
# runs were repeated (mutant-pick-ignored-02, green-02).
set -u
E=/Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-107-dialog
T=/Users/luckye/Documents/Code/a2a/workbench/tests/test_t107_open_directory_dialog.py
python3 $T --summary $E/green-01.json > $E/green-01.log 2>&1; echo "green-01 exit=$?" >> $E/exits.txt
python3 $T --mutant pick-ignored --summary $E/mutant-pick-ignored-01.json > $E/mutant-pick-ignored-01.log 2>&1; echo "mutant-pick-ignored-01 exit=$?" >> $E/exits.txt
python3 $T --mutant pick-ignored --summary $E/mutant-pick-ignored-02.json > $E/mutant-pick-ignored-02.log 2>&1; echo "mutant-pick-ignored-02 exit=$?" >> $E/exits.txt
python3 $T --summary $E/green-02.json > $E/green-02.log 2>&1; echo "green-02 exit=$?" >> $E/exits.txt
# After review-01 (P1: the cancel step could pass without the dialog ever opening): the test now sees the "+" button go
# busy while the dialog is up, waits for it to come back instead of sleeping, checks the main area switched to the project,
# never stops on Codex's own stop, and has a mutant for the cancel branch. Run one after another (one screen):
python3 $T --summary $E/green-03.json > $E/green-03.log 2>&1; echo "green-03 exit=$?" >> $E/exits.txt
python3 $T --mutant pick-ignored --summary $E/mutant-pick-ignored-03.json > $E/mutant-pick-ignored-03.log 2>&1; echo "mutant-pick-ignored-03 exit=$?" >> $E/exits.txt
python3 $T --mutant cancel-registers-default --summary $E/mutant-cancel-registers-default-01.json > $E/mutant-cancel-registers-default-01.log 2>&1; echo "mutant-cancel-registers-default-01 exit=$?" >> $E/exits.txt
