import json
import subprocess
import sys
import unittest
from pathlib import Path


class OpenAPITest(unittest.TestCase):
    def test_production_schema(self):
        result = subprocess.check_output(
            [
                sys.executable,
                "-c",
                "import json; from main import app; print(json.dumps(app.openapi()))",
            ],
            cwd=Path(__file__).resolve().parent,
            text=True,
        )
        schema = json.loads(result)
        self.assertEqual(schema["info"]["title"], "Acadence Billing Service")
        for path in ("/healthz", "/readyz"):
            with self.subTest(path=path):
                self.assertIn("200", schema["paths"][path]["get"]["responses"])
