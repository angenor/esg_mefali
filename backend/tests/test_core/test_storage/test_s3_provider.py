"""Tests S3StorageProvider contre moto[s3] mock réaliste (Story 10.6 AC6).

moto ≥ 5.0 expose `@mock_aws` qui émule un endpoint S3 complet en mémoire
(requêtes HTTP interceptées). Skip propre si moto absent.

Règle d'or 10.5 : on teste l'effet observable (round-trip put/get/head)
pas le mécanisme interne (pas de `patch("boto3.client")`).
"""

from __future__ import annotations

import pytest

# Skip le module entier si moto n'est pas installé — permet `pytest` minimal
# sans `pip install moto[s3]` et sans ImportError qui casserait la collection.
pytest.importorskip("moto", reason="moto[s3] required for S3 provider tests")

import boto3
from moto import mock_aws

from app.core.storage.base import (
    StorageError,
    StorageNotFoundError,
)
from app.core.storage.s3 import S3StorageProvider

pytestmark = [pytest.mark.s3]


BUCKET = "test-bucket-eu-west-3"
REGION = "eu-west-3"


@pytest.fixture
def s3_provider():
    """Crée un bucket EU-West-3 en mémoire et instancie le provider."""
    with mock_aws():
        client = boto3.client("s3", region_name=REGION)
        client.create_bucket(
            Bucket=BUCKET,
            CreateBucketConfiguration={"LocationConstraint": REGION},
        )
        provider = S3StorageProvider(bucket=BUCKET, region=REGION)
        yield provider


async def test_put_get_roundtrip_small(s3_provider: S3StorageProvider):
    uri = await s3_provider.put("docs/a.txt", b"hello-s3")
    assert uri == f"s3://{BUCKET}/docs/a.txt"
    got = await s3_provider.get("docs/a.txt")
    assert got == b"hello-s3"


async def test_put_content_type_applied(s3_provider: S3StorageProvider):
    await s3_provider.put("docs/file.pdf", b"%PDF-1.4", content_type="application/pdf")
    client = boto3.client("s3", region_name=REGION)
    head = client.head_object(Bucket=BUCKET, Key="docs/file.pdf")
    assert head["ContentType"] == "application/pdf"


async def test_put_sse_applied(s3_provider: S3StorageProvider):
    """NFR25 — SSE-S3 AES256 systématique sur tous les put."""
    await s3_provider.put("docs/encrypted.bin", b"secret-data")
    client = boto3.client("s3", region_name=REGION)
    head = client.head_object(Bucket=BUCKET, Key="docs/encrypted.bin")
    assert head.get("ServerSideEncryption") == "AES256"


async def test_get_missing_raises_not_found(s3_provider: S3StorageProvider):
    with pytest.raises(StorageNotFoundError):
        await s3_provider.get("nonexistent/key")


async def test_delete_idempotent(s3_provider: S3StorageProvider):
    # S3 delete d'une clé absente = no-op (aucune exception)
    await s3_provider.delete("nonexistent/key")


async def test_signed_url_generates_presigned(s3_provider: S3StorageProvider):
    await s3_provider.put("docs/signed.txt", b"data")
    url = await s3_provider.signed_url("docs/signed.txt", ttl_seconds=900)
    assert url.startswith("https://")
    assert BUCKET in url
    assert "X-Amz-Signature" in url or "AWSAccessKeyId" in url


async def test_signed_url_ttl_boundary(s3_provider: S3StorageProvider):
    with pytest.raises(ValueError):
        await s3_provider.signed_url("key", ttl_seconds=0)
    with pytest.raises(ValueError):
        await s3_provider.signed_url("key", ttl_seconds=3601)
    # 1 et 3600 sont acceptés
    url_min = await s3_provider.signed_url("key", ttl_seconds=1)
    url_max = await s3_provider.signed_url("key", ttl_seconds=3600)
    assert url_min.startswith("https://")
    assert url_max.startswith("https://")


async def test_list_prefix(s3_provider: S3StorageProvider):
    await s3_provider.put("prefix/a.txt", b"1")
    await s3_provider.put("prefix/b.txt", b"2")
    await s3_provider.put("other/c.txt", b"3")

    keys = await s3_provider.list("prefix/")
    assert len(keys) == 2
    assert all(k.startswith("prefix/") for k in keys)
    assert keys == sorted(keys)


async def test_exists_true_false(s3_provider: S3StorageProvider):
    await s3_provider.put("exists/yes.txt", b"x")
    assert await s3_provider.exists("exists/yes.txt") is True
    assert await s3_provider.exists("exists/no.txt") is False


async def test_repr_masks_credentials(s3_provider: S3StorageProvider):
    s = repr(s3_provider)
    assert BUCKET in s
    assert REGION in s
    # Aucune clé AWS ne doit apparaître
    assert "AKIA" not in s
    assert "secret" not in s.lower()


async def test_constructor_rejects_empty_bucket():
    with pytest.raises(StorageError):
        S3StorageProvider(bucket="", region=REGION)


# ─── SSE-S3 AES256 sur chemins multipart — post-review MEDIUM-10.6-3 ─────


async def test_put_sse_applied_on_multipart_binaryio(s3_provider: S3StorageProvider):
    """NFR25 — SSE-S3 AES256 doit s'appliquer aussi sur `upload_fileobj`."""
    from io import BytesIO

    buffer = BytesIO(b"X" * (2 * 1024 * 1024))  # 2 MB via BinaryIO → multipart
    await s3_provider.put("multipart/sse.bin", buffer, content_type="application/pdf")
    client = boto3.client("s3", region_name=REGION)
    head = client.head_object(Bucket=BUCKET, Key="multipart/sse.bin")
    assert head.get("ServerSideEncryption") == "AES256"
    assert head["ContentType"] == "application/pdf"


async def test_put_sse_applied_on_large_bytes(s3_provider: S3StorageProvider):
    """NFR25 — bytes ≥ 10 MB basculent en multipart : SSE doit suivre."""
    # Juste au-dessus du seuil MULTIPART_THRESHOLD_BYTES (10 MB)
    payload = b"Y" * (10 * 1024 * 1024 + 1)
    await s3_provider.put("multipart/large.bin", payload)
    client = boto3.client("s3", region_name=REGION)
    head = client.head_object(Bucket=BUCKET, Key="multipart/large.bin")
    assert head.get("ServerSideEncryption") == "AES256"
    assert head["ContentLength"] == len(payload)
