import sys
# Heavy full-screen redraws, like an agent TUI spinner: each frame clears and repaints.
for i in range(1, 1601):
    sys.stdout.write('\x1b[H\x1b[2J' + ''.join(f'frame {i:05d} row {r:02d} ' + 'x' * 40 + '\r\n' for r in range(20)))
sys.stdout.write('FINAL-FRAME-MARK\r\n'); sys.stdout.flush()
