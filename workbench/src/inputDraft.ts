// T-206: what the user types into a managed pane. Agents reach a pane only through a2a's own interfaces (dispatch, inbox,
// gate receipts), so keyboard input there is the user's. Keys are composed into a draft and nothing is recorded until
// Enter sends it: then the whole message is one record. Other keys (Esc, Ctrl-C, arrows in a menu) are not records of
// their own; the terminal's raw bytes stay in the pane's write events either way.
export type InputDraft = { chars: string[]; cursor: number; keys: string[]; uncertain: boolean };
export type InputEntry = { text: string; content?: Record<string, unknown> };

export const emptyDraft = (): InputDraft => ({ chars: [], cursor: 0, keys: [], uncertain: false });

// The keys the draft edits like a one-line editor. Any other key may change what the CLI holds in ways the draft
// cannot follow (history, completion), so the message is marked text_uncertain.
const SEQUENCES: Record<string, string> = { "[D": "←", "OD": "←", "[C": "→", "OC": "→", "[H": "Home", "OH": "Home",
  "[F": "End", "OF": "End", "[3~": "Delete", "[A": "↑", "OA": "↑", "[B": "↓", "OB": "↓" };
// Ctrl-C and Ctrl-D clear the line in the CLIs a2a runs; the draft starts over.
const CLEARS = new Set(["\x03", "\x04"]);

function edit(draft: InputDraft, key: string) {
  draft.keys.push(key);
  if (key === "←") draft.cursor = Math.max(0, draft.cursor - 1);
  else if (key === "→") draft.cursor = Math.min(draft.chars.length, draft.cursor + 1);
  else if (key === "Home") draft.cursor = 0;
  else if (key === "End") draft.cursor = draft.chars.length;
  else if (key === "Delete") draft.chars.splice(draft.cursor, 1);
  else draft.uncertain = true;
}

function insert(draft: InputDraft, text: string) {
  const chars = Array.from(text);
  draft.chars.splice(draft.cursor, 0, ...chars);
  draft.cursor += chars.length;
}

// Feeds one chunk xterm sent into the draft (changing it) and returns the messages it sent, in order.
export function feedInput(draft: InputDraft, data: string, pasted: boolean, binary: boolean): InputEntry[] {
  if (binary) { edit(draft, "二进制输入"); return []; }
  if (pasted) { insert(draft, data.slice(6, -6).replace(/\r\n?/g, "\n")); return []; }
  // Esc on its own interrupts the agent; it is not part of the message being typed.
  if (data === "\x1b") return [];
  const sent: InputEntry[] = [];
  const chars = Array.from(data);
  for (let index = 0; index < chars.length; index++) {
    const char = chars[index]!;
    if (char === "\r" || char === "\n") {
      const text = draft.chars.join("");
      if (text.trim()) sent.push({ text, ...(draft.keys.length ? { content: { action: "terminal-submit", keys: draft.keys,
        ...(draft.uncertain ? { text_uncertain: true } : {}) } } : {}) });
      Object.assign(draft, emptyDraft());
    } else if (char === "\x7f" || char === "\b") {
      if (draft.cursor > 0) draft.chars.splice(--draft.cursor, 1);
    } else if (CLEARS.has(char)) {
      Object.assign(draft, emptyDraft());
    } else if (char === "\x1b") {
      let sequence = "";
      if (chars[index + 1] === "[") {
        let end = index + 2;
        while (end < chars.length && !/[@-~]/.test(chars[end]!)) end++;
        sequence = chars.slice(index + 1, end + 1).join(""); index = end;
      } else if (chars[index + 1] === "O" && index + 2 < chars.length) {
        sequence = "O" + chars[index + 2]; index += 2;
      }
      edit(draft, sequence ? SEQUENCES[sequence] ?? "ESC " + sequence : "Esc");
    } else if (char === "\x01") edit(draft, "Home");
    else if (char === "\x05") edit(draft, "End");
    else if (char === "\t") edit(draft, "Tab");
    else if (char < " ") edit(draft, "Ctrl-" + String.fromCharCode(char.charCodeAt(0) + 64));
    else insert(draft, char);
  }
  return sent;
}
