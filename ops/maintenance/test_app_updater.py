"""Exercise update/rollback control flow without Docker or service changes."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class UpdaterTests(unittest.TestCase):
    def run_update(self, failure):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "bin").mkdir()
            (root / "ops/maintenance").mkdir(parents=True)
            (root / "ops/maintenance/app-canary.py").touch()
            fake = '''#!/usr/bin/env python3
import os, sys
from pathlib import Path
name = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['CALLS'], 'a') as f:
    f.write(name + ' ' + ' '.join(args) + '\\n')
if name == 'df': print('Available\\n999999999')
if name == 'git' and 'rev-parse' in args: print('test-revision')
if name == 'docker':
    if args[:2] == ['inspect', '-f']:
        print('sha256:old' if args[2] == '{{.Image}}' else 'healthy')
    if args[:2] == ['compose', 'build'] and os.environ['FAILURE'] == 'build': sys.exit(1)
    if args[0] == 'exec' and os.environ['FAILURE'] == 'canary': sys.exit(1)
'''
            for name in ("docker", "git", "df", "curl", "logger"):
                executable = root / "bin" / name
                executable.write_text(fake)
                executable.chmod(0o755)
            # Redirect only the test lock; production uses the shared deployment lock.
            script = Path(__file__).with_name("update-applications.sh").read_text()
            script = script.replace("/run/lock/nancy-deployment.lock", str(root / "deployment.lock"))
            result = subprocess.run(
                ["bash", "-c", script], capture_output=True, text=True,
                env={**os.environ, "PATH": str(root / "bin") + ":" + os.environ["PATH"],
                     "COMPOSE_DIR": str(root), "STATE_DIR": str(root / "state"),
                     "CALLS": str(root / "calls"), "FAILURE": failure},
            )
            return result.returncode, (root / "calls").read_text()

    def test_build_failure_does_not_deploy(self):
        status, calls = self.run_update("build")
        self.assertNotEqual(status, 0)
        self.assertNotIn("compose up", calls)
        self.assertNotIn("rollback.json up", calls)

    def test_functional_failure_rolls_back(self):
        status, calls = self.run_update("canary")
        self.assertNotEqual(status, 0)
        self.assertIn("rollback.json up", calls)

    def test_success_does_not_roll_back(self):
        status, calls = self.run_update("none")
        self.assertEqual(status, 0)
        self.assertNotIn("rollback.json up", calls)


if __name__ == "__main__":
    unittest.main()
