import unittest

from fastapi import APIRouter, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from main import app


router = APIRouter()


class TestPayload(BaseModel):
    count: int


@router.post("/test-validation")
def validate_payload(payload: TestPayload) -> dict[str, int]:
    return {"count": payload.count}


@router.get("/test-http-error")
def http_error() -> None:
    raise HTTPException(
        status_code=401,
        detail="sensitive exception detail",
        headers={"WWW-Authenticate": "Bearer", "X-Request-ID": "wrong"},
    )


@router.get("/test-unexpected-error")
def unexpected_error() -> None:
    raise RuntimeError("sensitive exception detail")


app.include_router(router)


class ProjectServiceErrorTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, raise_server_exceptions=False)
        self.addCleanup(self.client.close)

    def assert_valid_request_id(self, response):
        request_id = response.headers["X-Request-ID"]
        self.assertRegex(request_id, r"\A[A-Za-z0-9_-]{1,64}\Z")
        return request_id

    def assert_error(self, response, status):
        self.assertEqual(response.status_code, status)
        request_id = self.assert_valid_request_id(response)
        body = response.json()
        self.assertEqual(set(body), {"code", "message", "request_id", "details"})
        self.assertEqual(body["request_id"], request_id)
        self.assertIsInstance(body["code"], str)
        self.assertIsInstance(body["message"], str)
        self.assertIsInstance(body["details"], dict)
        return body

    def test_generated_and_accepted_request_ids(self):
        first = self.client.get("/healthz")
        second = self.client.get("/readyz")
        self.assertNotEqual(
            self.assert_valid_request_id(first), self.assert_valid_request_id(second)
        )
        for request_id in ("a", "ABC_123-xyz", "x" * 64):
            with self.subTest(request_id=request_id):
                response = self.client.get("/healthz", headers={"X-Request-ID": request_id})
                self.assertEqual(response.headers["X-Request-ID"], request_id)

    def test_invalid_request_ids_are_replaced(self):
        for request_id in ("", "x" * 65, "bad value", "bad.id", "bad/value"):
            with self.subTest(request_id=request_id):
                response = self.client.get("/missing", headers={"X-Request-ID": request_id})
                self.assert_error(response, 404)
                self.assertNotEqual(response.headers["X-Request-ID"], request_id)

        response = self.client.get(
            "/healthz",
            headers=[("X-Request-ID", "first"), ("X-Request-ID", "second")],
        )
        self.assertNotIn(self.assert_valid_request_id(response), ("first", "second"))

        response = self.client.get("/healthz", headers=[(b"X-Request-ID", b"\xe9")])
        self.assert_valid_request_id(response)
        self.assertNotEqual(response.headers["X-Request-ID"], "\xe9")

    def test_router_errors_and_protocol_headers(self):
        response = self.client.get("/missing", headers={"X-Request-ID": "req_404"})
        self.assert_error(response, 404)
        self.assertEqual(response.headers["X-Request-ID"], "req_404")

        response = self.client.post("/healthz", headers={"X-Request-ID": "req_405"})
        self.assert_error(response, 405)
        self.assertIn("GET", response.headers["Allow"])
        self.assertEqual(response.headers["X-Request-ID"], "req_405")

        response = self.client.get("/test-http-error", headers={"X-Request-ID": "req_401"})
        self.assert_error(response, 401)
        self.assertEqual(response.headers["WWW-Authenticate"], "Bearer")
        self.assertEqual(response.headers["X-Request-ID"], "req_401")
        self.assertNotIn("sensitive", response.text)

    def test_validation_error_does_not_expose_input(self):
        response = self.client.post(
            "/test-validation",
            json={"count": "sensitive-invalid-input"},
            headers={"X-Request-ID": "req_validation"},
        )
        self.assert_error(response, 422)
        self.assertEqual(response.headers["X-Request-ID"], "req_validation")
        self.assertNotIn("sensitive-invalid-input", response.text)

        response = self.client.post(
            "/test-validation",
            content=b'{"count": "sensitive-malformed"',
            headers={"Content-Type": "application/json"},
        )
        self.assert_error(response, 422)
        self.assertNotIn("sensitive-malformed", response.text)

    def test_unexpected_error_is_sanitized(self):
        for request_id in ("req_500", "invalid value", None):
            with self.subTest(request_id=request_id):
                headers = {"X-Request-ID": request_id} if request_id is not None else {}
                response = self.client.get("/test-unexpected-error", headers=headers)
                self.assert_error(response, 500)
                if request_id == "req_500":
                    self.assertEqual(response.headers["X-Request-ID"], request_id)
                else:
                    self.assertNotEqual(response.headers["X-Request-ID"], request_id)
                self.assertNotIn("sensitive", response.text)
                self.assertNotIn("RuntimeError", response.text)
                self.assertNotIn("Traceback", response.text)
