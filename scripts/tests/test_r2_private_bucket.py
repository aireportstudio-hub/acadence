"""Offline tests for the interactive private R2 verifier."""

import contextlib
from io import BytesIO, StringIO
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from botocore.exceptions import ClientError


SCRIPT = Path(__file__).resolve().parents[1] / "test_r2_private_bucket.py"
spec = importlib.util.spec_from_file_location("r2_private_bucket", SCRIPT)
r2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r2)


def client_error(operation, status, code):
    return ClientError(
        {"Error": {"Code": code, "Message": "secret message"},
         "ResponseMetadata": {"HTTPStatusCode": status}},
        operation,
    )


class PrivateBucketTests(unittest.TestCase):
    def test_main_and_all_cleanup_failures_are_reported_without_secrets(self):
        client = Mock()
        client.generate_presigned_url.return_value = "https://example.test/?secret-signature"
        client.delete_object.side_effect = client_error("DeleteObject", 400, "InvalidArgument")
        http_error = HTTPError(
            "https://example.test/?secret-signature", 403, "secret reason", {},
            BytesIO(b"<Error><Code>AccessDenied</Code><Message>secret body</Message></Error>"),
        )
        stderr = StringIO()
        with (
            patch.object(r2, "collect_details", return_value=("account", "https://example.test", "bucket", "secret-access", "secret-key")),
            patch.object(r2.boto3, "client", return_value=client),
            patch.object(r2, "urlopen", side_effect=http_error),
            contextlib.redirect_stderr(stderr),
            contextlib.redirect_stdout(StringIO()),
        ):
            self.assertEqual(r2.main(), 1)

        output = stderr.getvalue()
        self.assertIn("Signed synthetic upload", output)
        self.assertIn("HTTP 403", output)
        self.assertIn("AccessDenied", output)
        self.assertEqual(output.count("delete_object"), 3)
        self.assertEqual(output.count("HTTP 400"), 3)
        self.assertEqual(output.count("InvalidArgument"), 3)
        self.assertLess(output.index("Signed synthetic upload"), output.index("cleanup"))
        for secret in ("secret-access", "secret-key", "secret-signature", "secret body", "secret message"):
            self.assertNotIn(secret, output)
        self.assertEqual(client.delete_object.call_count, 3)
        for call in client.delete_object.call_args_list:
            self.assertEqual(set(call.kwargs), {"Bucket", "Key"})
            self.assertEqual(call.kwargs["Bucket"], "bucket")

    def test_head_failure_reports_status_and_code(self):
        client = Mock()
        client.head_object.side_effect = client_error("HeadObject", 403, "AccessDenied")
        with self.assertRaises(r2.R2TestFailure) as raised:
            r2.delete_and_verify(client, "bucket", "key")
        self.assertIn("head_object", str(raised.exception))
        self.assertIn("HTTP 403", str(raised.exception))
        self.assertIn("AccessDenied", str(raised.exception))
        self.assertEqual(client.delete_object.call_count, 2)
        client.head_object.assert_called_once_with(Bucket="bucket", Key="key")

    def test_missing_object_is_successful_cleanup(self):
        client = Mock()
        client.head_object.side_effect = client_error("HeadObject", 404, "404")
        r2.delete_and_verify(client, "bucket", "key")
        self.assertEqual(client.delete_object.call_count, 2)
        client.head_object.assert_called_once_with(Bucket="bucket", Key="key")

    def test_complete_run_and_cleanup_only_failure(self):
        client = Mock()
        client.generate_presigned_url.return_value = "https://example.test/?secret-signature"
        payload = b"Acadence private R2 connectivity check; synthetic data only.\n"
        responses = [(200, b""), (200, payload), (403, b""), (403, b""), (403, b""), (403, b"")]
        client.head_object.side_effect = client_error("HeadObject", 404, "404")
        with (
            patch.object(r2.boto3, "client", return_value=client),
            patch.object(r2, "request_url", side_effect=responses),
            patch.object(r2.time, "sleep"),
            contextlib.redirect_stdout(StringIO()),
        ):
            r2.run_test("https://example.test", "bucket", "access", "secret")
        self.assertEqual(client.delete_object.call_count, 6)
        self.assertEqual(client.head_object.call_count, 3)

        client.reset_mock(side_effect=True)
        client.delete_object.side_effect = client_error("DeleteObject", 400, "InvalidArgument")
        with (
            patch.object(r2.boto3, "client", return_value=client),
            patch.object(r2, "request_url", side_effect=responses),
            patch.object(r2.time, "sleep"),
            contextlib.redirect_stdout(StringIO()),
            self.assertRaises(r2.R2TestFailure) as raised,
        ):
            r2.run_test("https://example.test", "bucket", "access", "secret")
        self.assertIn("CLEANUP:", str(raised.exception))
        self.assertEqual(str(raised.exception).count("InvalidArgument"), 3)

    def test_unavailable_error_details_do_not_expose_response(self):
        self.assertEqual(
            r2.response_error_details(403, b'<Error xmlns="urn:s3"><Code>AccessDenied</Code></Error>'),
            "HTTP 403, R2 error code AccessDenied",
        )
        self.assertEqual(
            r2.response_error_details(500, b"<Error><Code>secret?signature</Code></Error>"),
            "HTTP 500, R2 error code unavailable",
        )
        self.assertEqual(
            r2.response_error_details(200, b"<Error><Code>NotAnError</Code></Error>"),
            "HTTP 200, R2 error code unavailable",
        )
        with patch.object(r2, "urlopen", side_effect=TimeoutError("secret URL")):
            with self.assertRaises(r2.R2TestFailure) as raised:
                r2.request_url("https://example.test/?secret", "GET", "Signed download")
        self.assertIn("Signed download", str(raised.exception))
        self.assertIn("HTTP unavailable, R2 error code unavailable", str(raised.exception))
        self.assertNotIn("secret", str(raised.exception))

    def test_presign_failure_is_reported_after_successful_cleanup(self):
        client = Mock()
        client.generate_presigned_url.side_effect = client_error("PutObject", 403, "AccessDenied")
        client.head_object.side_effect = client_error("HeadObject", 404, "404")
        stdout = StringIO()
        with (
            patch.object(r2.boto3, "client", return_value=client),
            contextlib.redirect_stdout(stdout),
            self.assertRaises(r2.R2TestFailure) as raised,
        ):
            r2.run_test("https://example.test", "bucket", "access", "secret")
        self.assertIn("generate_presigned_url", str(raised.exception))
        self.assertIn("HTTP 403, R2 error code AccessDenied", str(raised.exception))
        self.assertNotIn("CLEANUP:", str(raised.exception))
        self.assertIn("PASS: all synthetic test objects removed.", stdout.getvalue())
        self.assertEqual(client.delete_object.call_count, 6)

    def test_client_setup_failure_reports_no_cleanup_needed(self):
        stderr = StringIO()
        with (
            patch.object(r2.boto3, "client", side_effect=client_error("Setup", 403, "AccessDenied")),
            contextlib.redirect_stderr(stderr),
            self.assertRaises(r2.R2TestFailure),
        ):
            r2.run_test("https://example.test", "bucket", "access", "secret")
        self.assertIn("CLEANUP: not needed", stderr.getvalue())
        self.assertNotIn("secret", stderr.getvalue())

    def test_unsigned_authorization_400_is_denied_after_verified_signed_download(self):
        client = Mock()
        client.generate_presigned_url.return_value = "https://example.test/?secret-signature"
        client.head_object.side_effect = client_error("HeadObject", 404, "404")
        payload = b"Acadence private R2 connectivity check; synthetic data only.\n"
        denial = b"<Error><Code>InvalidArgument</Code><Message>Authorization</Message></Error>"
        responses = [(200, b""), (200, payload), (400, denial), (400, denial), (403, b""), (401, b"")]
        stdout = StringIO()
        with (
            patch.object(r2.boto3, "client", return_value=client),
            patch.object(r2, "request_url", side_effect=responses) as requests,
            patch.object(r2.time, "sleep"),
            contextlib.redirect_stdout(stdout),
        ):
            r2.run_test("https://example.test", "bucket", "access", "secret")
        self.assertEqual([call.args[2] for call in requests.call_args_list], [
            "Signed synthetic upload", "Signed download", "Anonymous read",
            "Anonymous write", "Expired signed read", "Expired signed upload",
        ])
        upload_key = client.generate_presigned_url.call_args_list[0].kwargs["Params"]["Key"]
        download_key = client.generate_presigned_url.call_args_list[1].kwargs["Params"]["Key"]
        self.assertEqual(upload_key, download_key)
        self.assertEqual(requests.call_args_list[2].args[0], f"https://example.test/bucket/{upload_key}")
        self.assertIn("PASS: all synthetic test objects removed.", stdout.getvalue())
        self.assertNotIn("secret-signature", stdout.getvalue())

    def test_other_400_responses_are_rejected_for_unsigned_and_expired_requests(self):
        valid = b"<Error><Code>InvalidArgument</Code><Message>Authorization</Message></Error>"
        invalid_bodies = [
            b"<Error><Code>InvalidArgument</Code><Message>Authorization </Message></Error>",
            b"<Error><Code>AccessDenied</Code><Message>Authorization</Message></Error>",
            b"<Error><Code>InvalidArgument</Code><Message>secret body</Message></Error>",
            b"<Error><Code>InvalidArgument</Code></Error>",
            b"<Error><Code>InvalidArgument</Code><Message>Authorization</Message><Message>secret body</Message></Error>",
            b"secret body",
        ]
        for body in invalid_bodies:
            for operation in ("Anonymous read", "Anonymous write"):
                with self.subTest(body=body, operation=operation):
                    with self.assertRaises(r2.R2TestFailure) as raised:
                        r2.require_denied(400, body, operation, unsigned=True)
                    self.assertIn("HTTP 400", str(raised.exception))
                    self.assertNotIn("secret body", str(raised.exception))
        for operation in ("Expired signed read", "Expired signed upload"):
            with self.subTest(operation=operation):
                with self.assertRaises(r2.R2TestFailure):
                    r2.require_denied(400, valid, operation)

    def test_signed_download_and_expiry_do_not_accept_unsigned_400_exception(self):
        denial = b"<Error><Code>InvalidArgument</Code><Message>Authorization</Message></Error>"
        payload = b"Acadence private R2 connectivity check; synthetic data only.\n"
        for responses, expected in (
            ([(200, b""), (400, denial)], "Signed download"),
            ([(200, b""), (200, b"wrong checksum")], "Signed download"),
            ([(200, b""), (200, payload), (403, b""), (403, b""), (400, denial)],
             "Expired signed read"),
            ([(200, b""), (200, payload), (403, b""), (403, b""), (403, b""), (400, denial)],
             "Expired signed upload"),
        ):
            with self.subTest(expected=expected, count=len(responses)):
                client = Mock()
                client.generate_presigned_url.return_value = "https://example.test/?secret-signature"
                client.head_object.side_effect = client_error("HeadObject", 404, "404")
                stdout = StringIO()
                with (
                    patch.object(r2.boto3, "client", return_value=client),
                    patch.object(r2, "request_url", side_effect=responses) as requests,
                    patch.object(r2.time, "sleep"),
                    contextlib.redirect_stdout(stdout),
                    self.assertRaises(r2.R2TestFailure) as raised,
                ):
                    r2.run_test("https://example.test", "bucket", "access", "secret")
                self.assertIn(expected, str(raised.exception))
                self.assertEqual(requests.call_count, len(responses))
                self.assertIn("PASS: all synthetic test objects removed.", stdout.getvalue())
                self.assertNotIn("secret-signature", stdout.getvalue())

    def test_unexpected_main_exception_is_not_masked_by_cleanup(self):
        client = Mock()
        client.generate_presigned_url.side_effect = ValueError("unexpected")
        client.delete_object.side_effect = client_error("DeleteObject", 400, "InvalidArgument")
        stderr = StringIO()
        with (
            patch.object(r2.boto3, "client", return_value=client),
            contextlib.redirect_stderr(stderr),
            self.assertRaisesRegex(ValueError, "unexpected"),
        ):
            r2.run_test("https://example.test", "bucket", "access", "secret")
        self.assertEqual(stderr.getvalue().count("InvalidArgument"), 3)


if __name__ == "__main__":
    unittest.main()
