# 第三轮各已知坏实现的全部实际失败值

## round2

| TZ | 失败项 | 实际值 | 手工期望 |
| --- | --- | --- | --- |
| America/Nuuk | F12/sunday-late-query | 2026-03-29T11:00:00.000Z | 2026-03-28T12:00:00.000Z |
| America/Nuuk | F12/thursday-late-query | 2026-03-29T11:00:00.000Z | 2026-03-28T12:00:00.000Z |
| America/Nuuk | F12/already-ran-Saturday | 2026-03-29T11:00:00.000Z | None |
| America/Nuuk | F12/before-normalized-slot | 2026-03-23T01:30:00.000Z | 2026-03-22T01:30:00.000Z |
| America/Nuuk | F12/next-week-before-slot | 2026-03-30T00:30:00.000Z | 2026-03-29T01:30:00.000Z |
| America/Nuuk | F12/2027-sunday-late-query | 2027-03-28T11:00:00.000Z | 2027-03-27T12:00:00.000Z |
| America/Nuuk | F12/2027-before-normalized-slot | 2027-03-22T01:30:00.000Z | 2027-03-21T01:30:00.000Z |
| America/Scoresbysund | F12/sunday-late-query | 2026-03-29T11:00:00.000Z | 2026-03-28T12:00:00.000Z |
| America/Scoresbysund | F12/thursday-late-query | 2026-03-29T11:00:00.000Z | 2026-03-28T12:00:00.000Z |
| America/Scoresbysund | F12/already-ran-Saturday | 2026-03-29T11:00:00.000Z | None |
| America/Scoresbysund | F12/before-normalized-slot | 2026-03-23T01:30:00.000Z | 2026-03-22T01:30:00.000Z |
| America/Scoresbysund | F12/next-week-before-slot | 2026-03-30T00:30:00.000Z | 2026-03-29T01:30:00.000Z |
| America/Scoresbysund | F12/2027-sunday-late-query | 2027-03-28T11:00:00.000Z | 2027-03-27T12:00:00.000Z |
| America/Scoresbysund | F12/2027-before-normalized-slot | 2027-03-22T01:30:00.000Z | 2027-03-21T01:30:00.000Z |

## baseline

| TZ | 失败项 | 实际值 | 手工期望 |
| --- | --- | --- | --- |
| America/New_York | F1/spring-query-for-earlier-Monday | 2026-03-02T08:30:00.000Z | 2026-03-02T07:30:00.000Z |
| America/New_York | F4/gap-query-before-normalized-slot | 2026-03-01T08:30:00.000Z | 2026-03-01T07:30:00.000Z |
| America/New_York | F4/one-ms-before-normalized-slot | 2026-03-01T08:30:00.000Z | 2026-03-01T07:30:00.000Z |
| America/New_York | F11/already-ran-same-project | 2026-03-02T08:30:00.000Z | None |
| America/New_York | F11/other-project-does-not-block | 2026-03-02T08:30:00.000Z | 2026-03-02T07:30:00.000Z |
| America/New_York | F11/manual-run-does-not-block | 2026-03-02T08:30:00.000Z | 2026-03-02T07:30:00.000Z |
| America/Nuuk | F12/before-normalized-slot | 2026-03-22T02:30:00.000Z | 2026-03-22T01:30:00.000Z |
| America/Nuuk | F12/2027-before-normalized-slot | 2027-03-21T02:30:00.000Z | 2027-03-21T01:30:00.000Z |
| America/Scoresbysund | F12/before-normalized-slot | 2026-03-22T02:30:00.000Z | 2026-03-22T01:30:00.000Z |
| America/Scoresbysund | F12/2027-before-normalized-slot | 2027-03-21T02:30:00.000Z | 2027-03-21T01:30:00.000Z |

## hours-before-date

| TZ | 失败项 | 实际值 | 手工期望 |
| --- | --- | --- | --- |
| America/New_York | F1/spring-query-for-earlier-Monday | 2026-03-02T08:30:00.000Z | 2026-03-02T07:30:00.000Z |
| America/New_York | F11/already-ran-same-project | 2026-03-02T08:30:00.000Z | None |
| America/New_York | F11/other-project-does-not-block | 2026-03-02T08:30:00.000Z | 2026-03-02T07:30:00.000Z |
| America/New_York | F11/manual-run-does-not-block | 2026-03-02T08:30:00.000Z | 2026-03-02T07:30:00.000Z |
| America/Nuuk | F12/before-normalized-slot | 2026-03-23T01:30:00.000Z | 2026-03-22T01:30:00.000Z |
| America/Nuuk | F12/next-week-before-slot | 2026-03-30T00:30:00.000Z | 2026-03-29T01:30:00.000Z |
| America/Nuuk | F12/2027-before-normalized-slot | 2027-03-22T01:30:00.000Z | 2027-03-21T01:30:00.000Z |
| America/Scoresbysund | F12/before-normalized-slot | 2026-03-23T01:30:00.000Z | 2026-03-22T01:30:00.000Z |
| America/Scoresbysund | F12/next-week-before-slot | 2026-03-30T00:30:00.000Z | 2026-03-29T01:30:00.000Z |
| America/Scoresbysund | F12/2027-before-normalized-slot | 2027-03-22T01:30:00.000Z | 2027-03-21T01:30:00.000Z |

## date-only-rollback

| TZ | 失败项 | 实际值 | 手工期望 |
| --- | --- | --- | --- |
| America/New_York | F4/gap-query-before-normalized-slot | 2026-03-01T08:30:00.000Z | 2026-03-01T07:30:00.000Z |
| America/New_York | F4/one-ms-before-normalized-slot | 2026-03-01T08:30:00.000Z | 2026-03-01T07:30:00.000Z |
| America/Nuuk | F12/before-normalized-slot | 2026-03-22T02:30:00.000Z | 2026-03-22T01:30:00.000Z |
| America/Nuuk | F12/2027-before-normalized-slot | 2027-03-21T02:30:00.000Z | 2027-03-21T01:30:00.000Z |
| America/Scoresbysund | F12/before-normalized-slot | 2026-03-22T02:30:00.000Z | 2026-03-22T01:30:00.000Z |
| America/Scoresbysund | F12/2027-before-normalized-slot | 2027-03-21T02:30:00.000Z | 2027-03-21T01:30:00.000Z |

## query-clock-round2

| TZ | 失败项 | 实际值 | 手工期望 |
| --- | --- | --- | --- |
| America/Nuuk | F12/sunday-late-query | 2026-03-29T11:00:00.000Z | 2026-03-28T12:00:00.000Z |
| America/Nuuk | F12/thursday-late-query | 2026-03-29T11:00:00.000Z | 2026-03-28T12:00:00.000Z |
| America/Nuuk | F12/already-ran-Saturday | 2026-03-29T11:00:00.000Z | None |
| America/Nuuk | F12/before-normalized-slot | 2026-03-23T01:30:00.000Z | 2026-03-22T01:30:00.000Z |
| America/Nuuk | F12/next-week-before-slot | 2026-03-30T00:30:00.000Z | 2026-03-29T01:30:00.000Z |
| America/Nuuk | F12/2027-sunday-late-query | 2027-03-28T11:00:00.000Z | 2027-03-27T12:00:00.000Z |
| America/Nuuk | F12/2027-before-normalized-slot | 2027-03-22T01:30:00.000Z | 2027-03-21T01:30:00.000Z |
| America/Scoresbysund | F12/sunday-late-query | 2026-03-29T11:00:00.000Z | 2026-03-28T12:00:00.000Z |
| America/Scoresbysund | F12/thursday-late-query | 2026-03-29T11:00:00.000Z | 2026-03-28T12:00:00.000Z |
| America/Scoresbysund | F12/already-ran-Saturday | 2026-03-29T11:00:00.000Z | None |
| America/Scoresbysund | F12/before-normalized-slot | 2026-03-23T01:30:00.000Z | 2026-03-22T01:30:00.000Z |
| America/Scoresbysund | F12/next-week-before-slot | 2026-03-30T00:30:00.000Z | 2026-03-29T01:30:00.000Z |
| America/Scoresbysund | F12/2027-sunday-late-query | 2027-03-28T11:00:00.000Z | 2027-03-27T12:00:00.000Z |
| America/Scoresbysund | F12/2027-before-normalized-slot | 2027-03-22T01:30:00.000Z | 2027-03-21T01:30:00.000Z |

