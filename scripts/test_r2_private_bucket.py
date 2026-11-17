"""Exercise private Cloudflare R2 access with a disposable synthetic object."""

from getpass import getpass
from hashlib import sha256
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen
from uuid import uuid4
from xml.etree import ElementTree

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError


class R2TestFailure(Exception):
    """A safe-to-display test failure that contains no credential material."""


def prompt_required(label: str, *, hidden: bool = False) -> str:
    prompt = f"{label}: "
    value = getpass(prompt) if hidden else input(prompt)
    value = value.strip()
    if not value:
        raise R2TestFailure(f"{label} is required.")
    return value


def collect_details() -> tuple[str, str, str, str, str]:
    account_id = prompt_required("Cloudflare R2 account ID")
    endpoint = prompt_required("R2 S3 API endpoint (https://<account-id>.r2.cloudflarestorage.com)")
    bucket = prompt_required("Existing private non-production bucket name")
    access_key = prompt_required("Scoped R2 S3 access key ID", hidden=True)
    secret_key = prompt_required("R2 S3 secret access key", hidden=True)

    parsed = urlsplit(endpoint)
    if (
        not re.fullmatch(r"[a-fA-F0-9]{32}", account_id)
        or parsed.scheme != "https"
        or parsed.hostname is None
        or parsed.hostname.casefold() != f"{account_id}.r2.cloudflarestorage.com".casefold()
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise R2TestFailure("Use the HTTPS R2 S3 endpoint matching the supplied 32-character account ID.")
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", bucket):
        raise R2TestFailure("The bucket name is not a valid R2 bucket name.")
    confirmation = input("Type the bucket name again to confirm it is private and non-production: ").strip()
    if confirmation != bucket:
        raise R2TestFailure("Bucket confirmation did not match; no R2 request was made.")
    ttl_confirmation = input(
        "A five-minute signed URL is used for test operations. Type yes to continue: "
    ).strip().casefold()
    if ttl_confirmation != "yes":
        raise R2TestFailure("Signed URL lifetime was not confirmed; no R2 request was made.")
    return account_id, endpoint.rstrip("/"), bucket, access_key, secret_key


def safe_error_code(code: object) -> str:
    if isinstance(code, str) and re.fullmatch(r"[A-Za-z0-9]{1,64}", code, flags=re.ASCII):
        return code
    return "unavailable"


def error_details(status: object, code: object) -> str:
    safe_status = str(status) if isinstance(status, int) and 100 <= status <= 599 else "unavailable"
    return f"HTTP {safe_status}, R2 error code {safe_error_code(code)}"


def response_error_fields(status: int, body: bytes) -> tuple[str | None, str | None]:
    if status < 400 or len(body) > 65536 or b"<!DOCTYPE" in body.upper():
        return None, None
    try:
        root = ElementTree.fromstring(body)
    except (ElementTree.ParseError, LookupError):
        return None, None
    if root.tag.split("}")[-1] != "Error":
        return None, None
    codes = [child for child in root if child.tag.split("}")[-1] == "Code"]
    messages = [child for child in root if child.tag.split("}")[-1] == "Message"]
    code = codes[0].text if len(codes) == 1 and len(codes[0]) == 0 else None
    message = messages[0].text if len(messages) == 1 and len(messages[0]) == 0 else None
    return code, message


def response_error_details(status: int, body: bytes) -> str:
    code, _ = response_error_fields(status, body)
    return error_details(status, code)


def request_url(
    url: str, method: str, description: str, body: bytes = b"", content_type: str | None = None
) -> tuple[int, bytes]:
    headers = {}
    if content_type is not None:
        headers["Content-Type"] = content_type
    request = Request(url, data=body if method == "PUT" else None, headers=headers, method=method)
    try:
        with urlopen(request, timeout=20) as response:
            return response.status, response.read()
    except HTTPError as exc:
        return exc.code, exc.read()
    except URLError as exc:
        reason = exc.reason
        reason_type = type(reason).__name__
        raise R2TestFailure(
            f"{description} could not reach R2 ({reason_type}; {error_details(None, None)})."
        ) from None
    except OSError as exc:
        raise R2TestFailure(
            f"{description} could not reach R2 ({type(exc).__name__}; {error_details(None, None)})."
        ) from None


def require_denied(status: int, body: bytes, operation: str, *, unsigned: bool = False) -> None:
    if status in (401, 403):
        return
    if unsigned and status == 400:
        code, message = response_error_fields(status, body)
        if code == "InvalidArgument" and message == "Authorization":
            return
    raise R2TestFailure(
        f"{operation} was expected to be denied ({response_error_details(status, body)})."
    )


def call_r2(operation, description: str):
    try:
        return operation()
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        raise R2TestFailure(f"{description} failed ({error_details(status, code)}).") from None
    except BotoCoreError:
        raise R2TestFailure(
            f"{description} failed due to a client or network error ({error_details(None, None)})."
        ) from None


def delete_and_verify(client, bucket: str, key: str) -> None:
    call_r2(lambda: client.delete_object(Bucket=bucket, Key=key), "cleanup delete_object")
    call_r2(lambda: client.delete_object(Bucket=bucket, Key=key), "cleanup idempotent delete_object")
    try:
        response = client.head_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if code in ("404", "NoSuchKey", "NotFound") or status == 404:
            return
        raise R2TestFailure(f"cleanup head_object failed ({error_details(status, code)}).") from None
    except BotoCoreError:
        raise R2TestFailure(
            f"cleanup head_object failed due to a client or network error ({error_details(None, None)})."
        ) from None
    raise R2TestFailure(
        "cleanup head_object found a synthetic object still present "
        f"({error_details(response.get('ResponseMetadata', {}).get('HTTPStatusCode'), None)})."
    )


def run_test(endpoint: str, bucket: str, access_key: str, secret_key: str) -> None:
    try:
        client = call_r2(
            lambda: boto3.client(
                "s3",
                endpoint_url=endpoint,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name="auto",
                config=Config(
                    signature_version="s3v4",
                    s3={"addressing_style": "path"},
                    connect_timeout=10,
                    read_timeout=20,
                    retries={"max_attempts": 2, "mode": "standard"},
                ),
            ),
            "R2 client setup",
        )
    except R2TestFailure:
        print("CLEANUP: not needed; no test objects were created.", file=sys.stderr)
        raise

    test_id = uuid4().hex
    prefix = f"acadence-r2-check/{test_id}"
    upload_key = f"{prefix}/signed-upload.bin"
    anonymous_write_key = f"{prefix}/anonymous-write.bin"
    expired_put_key = f"{prefix}/expired-put.bin"
    keys_to_clean = (upload_key, anonymous_write_key, expired_put_key)
    payload = b"Acadence private R2 connectivity check; synthetic data only.\n"
    content_type = "application/octet-stream"

    main_error = None
    cleanup_errors = []
    try:
        upload_url = call_r2(
            lambda: client.generate_presigned_url(
                "put_object",
                Params={"Bucket": bucket, "Key": upload_key, "ContentType": content_type},
                ExpiresIn=300,
                HttpMethod="PUT",
            ),
            "Signed upload generate_presigned_url",
        )
        status, body = request_url(upload_url, "PUT", "Signed synthetic upload", payload, content_type)
        if status not in (200, 201, 204):
            raise R2TestFailure(f"Signed synthetic upload failed ({response_error_details(status, body)}).")
        print("PASS: signed upload accepted.")

        download_url = call_r2(
            lambda: client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": upload_key},
                ExpiresIn=300,
                HttpMethod="GET",
            ),
            "Signed download generate_presigned_url",
        )
        status, downloaded = request_url(download_url, "GET", "Signed download")
        if status != 200 or sha256(downloaded).digest() != sha256(payload).digest():
            raise R2TestFailure(
                f"Signed download failed or its checksum did not match "
                f"({response_error_details(status, downloaded)})."
            )
        print("PASS: signed download and SHA-256 verification.")

        anonymous_url = f"{endpoint}/{quote(bucket, safe='')}/{quote(upload_key, safe='/')}"
        status, body = request_url(anonymous_url, "GET", "Anonymous read")
        require_denied(status, body, "Anonymous read", unsigned=True)
        print("PASS: anonymous read denied.")

        anonymous_write_url = f"{endpoint}/{quote(bucket, safe='')}/{quote(anonymous_write_key, safe='/')}"
        status, body = request_url(anonymous_write_url, "PUT", "Anonymous write", payload, content_type)
        require_denied(status, body, "Anonymous write", unsigned=True)
        print("PASS: anonymous write denied.")

        expired_get_url = call_r2(
            lambda: client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": upload_key},
                ExpiresIn=5,
                HttpMethod="GET",
            ),
            "Expired signed read generate_presigned_url",
        )
        expired_put_url = call_r2(
            lambda: client.generate_presigned_url(
                "put_object",
                Params={"Bucket": bucket, "Key": expired_put_key, "ContentType": content_type},
                ExpiresIn=5,
                HttpMethod="PUT",
            ),
            "Expired signed upload generate_presigned_url",
        )
        time.sleep(7)
        status, body = request_url(expired_get_url, "GET", "Expired signed read")
        require_denied(status, body, "Expired signed read")
        status, body = request_url(expired_put_url, "PUT", "Expired signed upload", payload, content_type)
        require_denied(status, body, "Expired signed upload")
        print("PASS: expired signed read and upload denied.")
    except R2TestFailure as exc:
        main_error = exc
    finally:
        for key in keys_to_clean:
            try:
                delete_and_verify(client, bucket, key)
            except R2TestFailure as exc:
                cleanup_errors.append(f"{key.rsplit('/', 1)[-1]}: {exc}")
        if cleanup_errors and sys.exc_info()[0] is not None:
            print(f"CLEANUP: could not be verified for {prefix}; {'; '.join(cleanup_errors)}", file=sys.stderr)
        elif not cleanup_errors:
            print("PASS: all synthetic test objects removed.")
    if cleanup_errors:
        cleanup_report = f"CLEANUP: could not be verified for {prefix}; {'; '.join(cleanup_errors)}"
        if main_error is not None:
            raise R2TestFailure(f"{main_error}\n{cleanup_report}") from None
        raise R2TestFailure(cleanup_report)
    if main_error is not None:
        raise main_error


def main() -> int:
    try:
        _, endpoint, bucket, access_key, secret_key = collect_details()
        print("Starting live R2 checks. Only synthetic data will be uploaded; no signed URLs or credentials are displayed.")
        run_test(endpoint, bucket, access_key, secret_key)
    except R2TestFailure as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled; no test was started if credential prompts were incomplete.", file=sys.stderr)
        return 1
    print("PASS: live private R2 checks completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
