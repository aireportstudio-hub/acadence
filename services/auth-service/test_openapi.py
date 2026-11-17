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
        self.assertEqual(schema["info"]["title"], "Acadence Auth Service")
        expected_paths = (
            "/healthz",
            "/readyz",
            "/v1/auth/google/start",
            "/v1/auth/google/callback",
            "/v1/auth/session",
            "/v1/auth/logout",
        )
        for path in expected_paths:
            with self.subTest(path=path):
                operation = (
                    schema["paths"][path]["post"]
                    if path == "/v1/auth/logout"
                    else schema["paths"][path]["get"]
                )
                self.assertIn("200" if path != "/v1/auth/logout" else "204", operation["responses"])
