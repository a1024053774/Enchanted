// Find forward (gap) transitions in 2026-2028 whose skipped wall-clock window ends at or after local midnight,
// i.e. a wall time late on day D does not exist and normalizes into D+1.
const H = 3600e3, DAY = 86400e3;
const offsetMin = (tz, t) => {
  const f = new Intl.DateTimeFormat('en-US', { timeZone: tz, hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const p = Object.fromEntries(f.formatToParts(new Date(t)).map(x => [x.type, x.value]));
  return (Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour, +p.minute, +p.second) - Math.floor(t / 1000) * 1000) / 60e3;
};
const out = [];
for (const tz of Intl.supportedValuesOf('timeZone')) {
  let prev = offsetMin(tz, Date.UTC(2026, 0, 1));
  for (let t = Date.UTC(2026, 0, 1) + H; t < Date.UTC(2028, 0, 1); t += H) {
    const cur = offsetMin(tz, t);
    if (cur > prev) {
      // find exact transition minute
      let lo = t - H, hi = t;
      while (hi - lo > 60e3) { const mid = lo + Math.floor((hi - lo) / 120e3) * 60e3; if (offsetMin(tz, mid) === prev) lo = mid; else hi = mid; }
      const before = hi + prev * 60e3, after = hi + cur * 60e3;
      if (Math.floor(after / DAY) > Math.floor(before / DAY)) out.push(`${tz} ${new Date(before).toISOString().slice(0, 16)} -> ${new Date(after).toISOString().slice(0, 16)} (local wall)`);
    }
    prev = cur;
  }
}
console.log(out.join('\n') || 'none');
