// Codex stores rollouts in local-date directories. Archives also look one day before launch.
export function* codexScanDays(since: number, now = Date.now(), startDayOffset = 0): Generator<Date> {
  const start = new Date(since), tomorrow = new Date(now);
  start.setHours(0, 0, 0, 0);
  start.setDate(start.getDate() + startDayOffset);
  tomorrow.setHours(0, 0, 0, 0);
  tomorrow.setDate(tomorrow.getDate() + 1);
  // Compare local calendar boundaries, whose elapsed separation can be 23 or 25 hours.
  for (const day = start; day.getTime() <= tomorrow.getTime(); day.setDate(day.getDate() + 1)) {
    yield new Date(day);
  }
}
