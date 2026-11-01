// List forward (gap) transitions in any IANA zone between two UTC instants.
const [from, to] = process.argv.slice(2).map(s => Date.parse(s));
const H = 3600e3;
const fmt = new Map();
const offsetMin = (tz, t) => {
  let f = fmt.get(tz);
  if (!f) { f = new Intl.DateTimeFormat('en-US', { timeZone: tz, hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }); fmt.set(tz, f); }
  const p = Object.fromEntries(f.formatToParts(new Date(t)).map(x => [x.type, x.value]));
  return (Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour, +p.minute) - Math.floor(t / 60e3) * 60e3) / 60e3;
};
const out = [];
for (const tz of Intl.supportedValuesOf('timeZone')) {
  let prev = offsetMin(tz, from);
  for (let t = from + H; t <= to; t += H) { const cur = offsetMin(tz, t); if (cur > prev) out.push(`${tz} forward ${prev}->${cur} near ${new Date(t).toISOString()}`); prev = cur; }
}
console.log(out.join('\n') || 'none');
