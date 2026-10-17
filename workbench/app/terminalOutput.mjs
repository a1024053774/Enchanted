// Public xterm APIs own parsing and mode changes. T-078 P1 records the known-bad
// focus output and the public-parser counterexamples for this boundary.
// Failure modes: enabling 1004, losing other modes, reordering a mixed mode
// against later output, losing a split sequence, or inventing its raw bytes.
export function createFocusSafeWriter(term, observe) {
  let previousTail = '';
  let activeSequence = null;
  let forwarded = null;
  let pending = Promise.resolve();
  const nativeWrite = text => new Promise(resolve => term.write(text, resolve));

  for (const final of ['h', 'l']) {
    term.parser.registerCsiHandler({prefix:'?',final}, params => {
      if (!params.includes(1004)) return false;
      // Public handlers receive numbers, which have already lost leading
      // zeros. The output writer retains the actual sequence for this callback.
      const match = /^(\x1b\[\?|\x9b\?)([0-9;:]*)([hl])$/.exec(activeSequence ?? '');
      if (!match || match[3] !== final) throw new Error('Focus sequence has no matching raw output frame');
      const remaining = match[2].split(';').filter(value => Number(value.split(':')[0]) !== 1004);
      observe('focus-mode-intercept', {raw_sequence:activeSequence,mode:final === 'h' ? 'set' : 'reset'});
      if (remaining.length) forwarded = nativeWrite(match[1]+remaining.join(';')+final);
      // Never let the built-in 1004 handler enable focus reports. Non-1004
      // parameters are parsed by xterm itself before any following output.
      return true;
    });
  }

  return function write(text) {
    pending = pending.then(async () => {
      const combined = previousTail+text;
      let cursor = previousTail.length;
      const frames = [];
      // This only finds write boundaries; it does not decide whether bytes
      // are a CSI inside the terminal parser. False matches remain unchanged.
      for (const match of combined.matchAll(/(?:\x1b\[|\x9b)\?[0-9;:]*[hl]/g)) {
        const end = match.index+match[0].length;
        if (end <= cursor) continue;
        frames.push({text:combined.slice(cursor,end),sequence:match[0]});
        cursor=end;
      }
      if (cursor < combined.length) frames.push({text:combined.slice(cursor),sequence:null});
      previousTail = /(?:\x1b(?:\[(?:\?[0-9;:]*)?)?|\x9b(?:\?[0-9;:]*)?)$/.exec(combined)?.[0] ?? '';
      for (const frame of frames) {
        activeSequence=frame.sequence; forwarded=null;
        await nativeWrite(frame.text);
        // Do not await a nested write inside a parser callback: that would
        // block xterm's own queue. The current frame ends at the mode command.
        if (forwarded) await forwarded;
        activeSequence=null;
      }
    });
    return pending;
  };
}

// The daemon owns device replies, including when no window is open. Consume
// these queries in the view so an xterm-generated reply cannot look like typing.
export function ownTerminalQueries(term, observe) {
  for (const id of [{final:'c'},{prefix:'>',final:'c'},{final:'n'},{prefix:'?',final:'n'},
    {intermediates:'$',final:'p'},{prefix:'?',intermediates:'$',final:'p'}]) {
    term.parser.registerCsiHandler(id, params => { observe('owned-query',{id,params}); return true; });
  }
  term.parser.registerCsiHandler({final:'t'}, params => {
    if (![14,16,18,20,21].includes(params[0])) return false;
    observe('owned-query',{id:{final:'t'},params}); return true;
  });
  for (const id of [4,10,11,12]) term.parser.registerOscHandler(id, data => {
    if (!data.split(';').includes('?')) return false;
    observe('owned-query',{id,data}); return true;
  });
  term.parser.registerDcsHandler({intermediates:'$',final:'q'}, (data,params) => {
    observe('owned-query',{id:{intermediates:'$',final:'q'},data,params}); return true;
  });
}
