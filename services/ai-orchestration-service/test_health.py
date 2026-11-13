import unittest

from fastapi.testclient import TestClient

from main import app


class ProjectServiceHealthTest(unittest.TestCase):
    def test_health_returns_ok(self):
        with TestClient(app) as client:
            response = client.get("/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})