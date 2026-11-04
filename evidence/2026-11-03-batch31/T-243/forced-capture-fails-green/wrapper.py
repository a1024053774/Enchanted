import runpy, sys
sys.path.insert(0, '/Users/luckye/Documents/Code/a2a/workbench/tests')
import electron_client
def unconfirmed(self):
    raise RuntimeError('T-243 forced: Electron exit unconfirmed')
electron_client.ElectronClient.close = unconfirmed
if True:
    def capture_fails(self, scene):
        raise RuntimeError('T-243 forced: scene capture failed')
    electron_client.ElectronClient.capture_and_stop = capture_fails
sys.argv = ['/Users/luckye/Documents/Code/a2a/workbench/tests/test_electron_e2e.py', '--source', '/Users/luckye/Documents/Code/a2a', '--output', '/Users/luckye/Documents/Code/a2a/evidence/2026-11-03-batch31/T-243/forced-capture-fails-green/out', '--stage', 'window']
runpy.run_path(sys.argv[0], run_name='__main__')
