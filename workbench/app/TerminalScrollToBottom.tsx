// Adapted from Synara 49cae984f, apps/web/src/components/TerminalScrollToBottom.tsx.
// Copyright (c) 2026 T3 Tools Inc. and Emanuele Di Pietro. MIT; see ../LICENSE.synara.
import type { Terminal } from '@xterm/xterm';
import { useEffect, useState } from 'react';

export function TerminalScrollToBottom({ terminal }: { terminal: Terminal | null }) {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    if (!terminal) return;
    let frame: number | null = null;
    const schedule = () => {
      if (frame !== null) return;
      frame = requestAnimationFrame(() => {
        frame = null;
        const buffer = terminal.buffer.active;
        setVisible(buffer.viewportY < buffer.baseY);
      });
    };
    schedule();
    const parsed = terminal.onWriteParsed(schedule);
    const scrolled = terminal.onScroll(schedule);
    return () => { if (frame !== null) cancelAnimationFrame(frame); parsed.dispose(); scrolled.dispose(); };
  }, [terminal]);
  return visible ? <button className="scroll-bottom" onClick={() => terminal?.scrollToBottom()}>回到底部 ↓</button> : null;
}
