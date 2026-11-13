import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


class AuthServiceHealthTest(unittest.TestCase):
    def test_startup_with_defaults_and_health_endpoints(self):
        with patch.dict(os.environ, {}, clear=True):
            with TestClient(app) as client:
                self.assertEqual(app.state.app_env, "development")
                self.assertEqual(app.state.log_level, "INFO")
                health = client.get("/healthz")
                ready = client.get("/readyz")

        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json(), {"status": "ok"})
        self.assertEqual(ready.status_code, 200)
        self.assertEqual(ready.json(), {"status": "ready"})

    def test_startup_with_valid_overrides(self):
        for app_env in ("development", "staging", "production"):
            for log_level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
                for configured_level in (log_level, log_level.lower()):
                    with self.subTest(app_env=app_env, log_level=configured_level):
                        with patch.dict(
                            os.environ,
                            {"APP_ENV": app_env, "LOG_LEVEL": configured_level},
                            clear=True,
                        ):
                            with TestClient(app):
                                self.assertEqual(app.state.app_env, app_env)
                                self.assertEqual(app.state.log_level, log_level)

    def test_startup_rejects_invalid_settings_without_echoing_values(self):
        for setting in ("APP_ENV", "LOG_LEVEL"):
            for value in ("", " ", "sensitive-invalid-value"):
                with self.subTest(setting=setting, value=value):
                    with patch.dict(os.environ, {setting: value}, clear=True):
                        with self.assertRaises(ValueError) as raised:
                            with TestClient(app):
                                self.fail("Startup should have failed")

                    self.assertIn(setting, str(raised.exception))
                    self.assertNotIn("sensitive-invalid-value", str(raised.exception))