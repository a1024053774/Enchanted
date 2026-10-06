---
id: T-003
title: Roles and evidence
type: decide
status: closed
blocked_by: []
claimed_by: /root
supersedes:
---

## Question

How should the exploratory pilot divide authority and preserve evidence?

## Resolution

The controller uses `gpt-6-astra` with max reasoning; workers use `gpt-6.1-sol` with xhigh
reasoning and the Fast service tier; the monitor uses `gpt-6.1-sol` with high reasoning and
is read-only. The controller may dispatch and reclaim workers through Herdr inside the
approved scope. Workers implement; claim, submit, acceptance, and integration gates remain
outside model self-report. The run produces an append-only record and an independent
acceptance result. The first run is exploratory baseline evidence and cannot claim improved
reliability without an independent comparison. The exact major-decision stop examples are
tracked by T-004. Evidence: user confirmations in grilling rounds 4 and 5. Closed 2026-10-05.
