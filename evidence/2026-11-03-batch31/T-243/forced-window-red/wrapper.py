import runpy, sys
sys.path.insert(0, '/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/3d33f3fe-5dae-4429-ab08-a90fa7e7e794/scratchpad/head-tests/workbench/tests')
import electron_client
def unconfirmed(self):
    raise RuntimeError('T-243 forced: Electron exit unconfirmed')
electron_client.ElectronClient.close = unconfirmed
sys.argv = ['/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/3d33f3fe-5dae-4429-ab08-a90fa7e7e794/scratchpad/head-tests/workbench/tests/test_electron_e2e.py', '--source', '/Users/luckye/Documents/Code/a2a', '--output', '/Users/luckye/Documents/Code/a2a/evidence/2026-11-03-batch31/T-243/forced-window-red/out', '--stage', 'window']
runpy.run_path(sys.argv[0], run_name='__main__')
