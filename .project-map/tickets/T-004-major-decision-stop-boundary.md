---
id: T-004
title: Major-decision stop boundary
type: decide
status: closed
blocked_by: []
claimed_by: /root
supersedes:
---

## Question

Which concrete conditions require the autonomous controller to stop and ask the user, and
which routine operations may it perform through Herdr without another approval?

## Resolution

The controller stops for scope or goal changes, acceptance or permission changes,
irreversible external effects, unverified or conflicting external state, a design trade-off
that changes the destination, or a budget/risk breach. Routine dispatch, status checking,
policy-bounded retry, and reclaim remain autonomous. The user accepted this boundary in
grilling round 6. Closed 2026-10-05.
