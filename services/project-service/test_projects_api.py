import os
import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient

from main import app, creation_prerequisites
from projects import Project


class ProjectAccessTest(unittest.TestCase):
    def setUp(self):
        self.owner_a, self.owner_b = uuid4(), uuid4()
        self.token_a, self.token_b = "a" * 43, "b" * 43
        self.records = {}
        self.env = patch.dict(os.environ, {
            "APP_ENV": "development",
            "AUTH_SERVICE_URL": "http://localhost:8001",
            "DATABASE_URL": "postgresql://test",
            "FRONTEND_APP_URL": "http://localhost:3001",
        }, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

        def auth(url, *, headers, timeout, follow_redirects, trust_env):
            token = headers["Cookie"].split("=", 1)[1]
            owner = {self.token_a: self.owner_a, self.token_b: self.owner_b}.get(token)
            return httpx.Response(200, json={"user_id": str(owner)}) if owner else httpx.Response(401)

        def create(connection, owner, title, description):
            project = Project(uuid4(), owner, title, description)
            self.records[project.id] = project
            return project

        def listing(connection, owner):
            return [project for project in self.records.values() if project.owner_user_id == owner]

        def get(connection, project_id, owner):
            project = self.records.get(project_id)
            return project if project and project.owner_user_id == owner else None

        for target, replacement in (
            ("main.httpx.get", auth),
            ("main.psycopg.connect", MagicMock()),
            ("main.create_project", create),
            ("main.list_projects", listing),
            ("main.get_project", get),
        ):
            mock = patch(target, replacement)
            mock.start()
            self.addCleanup(mock.stop)

    def test_owner_access_and_signed_out_denial(self):
        # Override the unavailable integration only to exercise the route contract.
        app.dependency_overrides[creation_prerequisites] = lambda: None
        self.addCleanup(app.dependency_overrides.clear)
        origin = {"Origin": "http://localhost:3001"}
        self.client.cookies.set("acadence_session", self.token_a)
        created = self.client.post("/v1/projects", json={"title": "Project A", "description": "Details"}, headers=origin)
        self.assertEqual(created.status_code, 201)
        project = created.json()
        self.assertEqual(set(project), {"id", "title", "description"})
        self.assertEqual(self.client.get("/v1/projects").json(), [project])
        self.assertEqual(self.client.get(f"/v1/projects/{project['id']}").json(), project)

        self.client.cookies.set("acadence_session", self.token_b)
        self.assertEqual(self.client.get("/v1/projects").json(), [])
        self.assertEqual(self.client.get(f"/v1/projects/{project['id']}").status_code, 404)
        self.assertEqual(self.client.get(f"/v1/projects/{project['id']}", headers={"X-User-ID": str(self.owner_a)}).status_code, 404)
        self.client.cookies.clear()
        for method, path in (("get", "/v1/projects"), ("get", f"/v1/projects/{project['id']}"), ("post", "/v1/projects")):
            response = getattr(self.client, method)(path, **({"json": {"title": "Denied"}, "headers": origin} if method == "post" else {}))
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.headers["cache-control"], "no-store")

    def test_creation_is_closed_and_owner_cannot_be_supplied(self):
        self.client.cookies.set("acadence_session", self.token_a)
        origin = {"Origin": "http://localhost:3001"}
        self.assertEqual(self.client.post("/v1/projects", json={"title": "Blocked"}, headers=origin).status_code, 503)
        self.assertEqual(self.records, {})
        app.dependency_overrides[creation_prerequisites] = lambda: None
        self.addCleanup(app.dependency_overrides.clear)
        self.assertEqual(self.client.post("/v1/projects", json={"title": "x", "owner_user_id": str(self.owner_b)}, headers=origin).status_code, 422)
        self.assertEqual(self.client.post("/v1/projects", json={"title": "x"}, headers={"Origin": "https://evil.example"}).status_code, 403)
        self.assertEqual(self.records, {})

    def test_revoked_session_and_auth_failure_fail_closed(self):
        self.client.cookies.set("acadence_session", "c" * 43)
        self.assertEqual(self.client.get("/v1/projects").status_code, 401)
        with patch("main.httpx.get", side_effect=httpx.ConnectError("unavailable")):
            self.assertEqual(self.client.get("/v1/projects").status_code, 503)
        with patch("main.httpx.get", return_value=httpx.Response(200, json={"user_id": "invalid"})):
            self.assertEqual(self.client.get("/v1/projects").status_code, 503)
