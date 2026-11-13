"""Verify offline R2-style SigV4 presigned requests using synthetic credentials."""

from urllib.parse import parse_qs, urlsplit

import boto3
from botocore.config import Config


def main() -> None:
    endpoint = "https://p00-fixture.r2.cloudflarestorage.com"
    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id="p00-fixture-access",
        aws_secret_access_key="p00-fixture-secret",
        region_name="auto",
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    paths = {}
    for operation, method in (("put_object", "PUT"), ("get_object", "GET")):
        params = {"Bucket": "private-fixture", "Key": "synthetic/report.pdf"}
        if method == "PUT":
            params["ContentType"] = "application/pdf"
        url = urlsplit(client.generate_presigned_url(operation, Params=params, ExpiresIn=300, HttpMethod=method))
        query = parse_qs(url.query)
        assert url.scheme == "https" and url.hostname == "p00-fixture.r2.cloudflarestorage.com"
        assert url.path == "/private-fixture/synthetic/report.pdf"
        assert query["X-Amz-Expires"] == ["300"]
        assert query["X-Amz-Algorithm"] == ["AWS4-HMAC-SHA256"]
        assert "host" in query["X-Amz-SignedHeaders"][0].split(";")
        assert ("content-type" in query["X-Amz-SignedHeaders"][0].split(";")) == (method == "PUT")
        assert len(query["X-Amz-Signature"][0]) == 64
        paths[method] = query["X-Amz-Signature"][0]
    assert paths["PUT"] != paths["GET"]
    print("PASS: generated and inspected offline 5-minute PUT and GET signatures with dummy credentials.")


if __name__ == "__main__":
    main()
