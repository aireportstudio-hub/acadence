import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


WORKER = Path(__file__).resolve().with_name("main.py")


class WorkerEntryPointTests(unittest.TestCase):
    def run_worker(self, *args: str) -> subprocess.CompletedProcess[str]:
        # Windows needs SystemRoot to start Python with an otherwise empty environment.
        env = {"SystemRoot": os.environ["SystemRoot"]} if "SystemRoot" in os.environ else {}
        with tempfile.TemporaryDirectory() as working_dir:
            return subprocess.run(
                [sys.executable, str(WORKER), *args],
                cwd=working_dir,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

    def test_smoke_check_succeeds_without_configuration(self) -> None:
        result = self.run_worker("--smoke-check")

        self.assertEqual(result.returncode, 0)
        self.assertIn("startup check", result.stdout)
        self.assertIn("no report job was run", result.stdout)

    def test_without_smoke_check_fails(self) -> None:
        result = self.run_worker()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not implemented", result.stderr)
        self.assertIn("no report job was run", result.stderr)


if __name__ == "__main__":
    unittest.main()
