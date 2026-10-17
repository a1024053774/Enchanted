# A-12 protocol I1 rebuild（review-only）

A-11 I1 consumed one registered root and twelve Messages after the Bash input schema defect caused eleven client retries. The frozen ideation budget is four roots/six Messages, so A-11 cannot continue. A-12 must use a new Stage-A root, new APIs, new B1 session and new onboarding receipts.

The fixed API emits `{"command": shlex.join(protocol.commands.I_SEND_STOP.argv)}` for the Bash tool. Dispatch phase stops at one PermissionRequest; permission phase reads the exact pane bytes and command, then sends one Electron `terminal-key` Enter as a control action. The second Messages request must be the matching tool_result, followed by actual Stop/relay and inbox readback.

No real process or input is started by this packet. A-12 source revision, readiness binding, P1 launch/session, permission screen and actual IDs are filled only after a fresh Stage-A/B1 preparation.
