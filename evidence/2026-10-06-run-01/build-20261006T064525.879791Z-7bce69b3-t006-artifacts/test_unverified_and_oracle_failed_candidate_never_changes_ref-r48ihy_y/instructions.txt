# Cursor pagination fixture v1

This is an isolated coding task for the Herdr A2A experiment.

Run `python3 pager.py`. Read one JSON request from stdin and write one JSON response to stdout.
Requests contain `items` (records with distinct string `id` and integer `ts`), `limit`,
and optional `after` (null or [integer timestamp, string id]).
Sort records by (ts, id) ascending. Return at most limit records strictly after that pair.
Preserve all record fields. Return `{"items": [...], "next_cursor": ...}`.
The next cursor is the last returned pair only if additional eligible records remain;
otherwise it is null. Input order must not matter. Do not mutate input records.

Limits must be integers in [1, 100]; booleans are invalid. Invalid limit returns only
`{"error": "invalid_limit"}`. An after value with a wrong shape/type returns only
`{"error": "invalid_cursor"}`. Check limit before cursor. A cursor need not exist in the input.
Empty results have items=[] and next_cursor=null.

The initial program is deliberately incomplete. Implement this contract without modifying
this document or acceptance tools. A successful model turn is not delivery acceptance.
