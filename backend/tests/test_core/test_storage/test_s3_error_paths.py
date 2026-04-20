"""Tests des chemins d'erreur boto3 et du mapping `StorageError` (Story 10.6).

Couvre :
  - `BotoCoreError` → `StorageError` générique
  - `AccessDenied` → `StoragePermissionError`
  - Retry transient (SlowDown puis succès)
  - `NotImplementedError` sur pagination > 1000
  - Multipart path via `BinaryIO`
"""

from __future__ import annotations

from io import BytesIO
from unittest.mock import MagicMock

import pytest

pytest.importorskip("moto", reason="moto[s3] required")

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from moto import mock_aws

from app.core.storage.base import (
    StorageError,
    StoragePermissionError,
)
from app.core.storage.s3 import S3StorageProvider, _is_transient_error, _map_client_error

pytestmark = [pytest.mark.s3]

BUCKET = "err-bucket"
REGION = "eu-west-3"


@pytest.fixture
def s3_provider():
    with mock_aws():
        client = boto3.client("s3", region_name=REGION)
        client.create_bucket(
            Bucket=BUCKET,
            CreateBucketConfiguration={"LocationConstraint": REGION},
        )
        yield S3StorageProvider(bucket=BUCKET, region=REGION)


def test_is_transient_error_on_slowdown():
    exc = ClientError(
        error_response={"Error": {"Code": "SlowDown"}},
        operation_name="PutObject",
    )
    assert _is_transient_error(exc) is True


def test_is_transient_error_on_access_denied():
    exc = ClientError(
        error_response={"Error": {"Code": "AccessDenied"}},
        operation_name="GetObject",
    )
    assert _is_transient_error(exc) is False


def test_is_transient_error_on_botocore():
    class FakeBoto(BotoCoreError):
        fmt = "fake"

    assert _is_transient_error(FakeBoto()) is True


def test_map_client_error_access_denied():
    exc = ClientError(
        error_response={"Error": {"Code": "AccessDenied"}},
        operation_name="GetObject",
    )
    mapped = _map_client_error(exc, "some/key")
    assert isinstance(mapped, StoragePermissionError)


def test_map_client_error_generic():
    exc = ClientError(
        error_response={"Error": {"Code": "WeirdError"}},
        operation_name="GetObject",
    )
    mapped = _map_client_error(exc, "some/key")
    assert isinstance(mapped, StorageError)
    assert "WeirdError" in str(mapped)


async def test_put_multipart_via_binaryio(s3_provider: S3StorageProvider):
    """Bascule multipart systématique si content=BinaryIO."""
    buffer = BytesIO(b"X" * (2 * 1024 * 1024))
    uri = await s3_provider.put(
        "multipart/data.bin", buffer, content_type="application/octet-stream"
    )
    assert uri == f"s3://{BUCKET}/multipart/data.bin"
    got = await s3_provider.get("multipart/data.bin")
    assert len(got) == 2 * 1024 * 1024


async def test_put_rejects_unknown_content_type(s3_provider: S3StorageProvider):
    with pytest.raises(StorageError):
        await s3_provider.put("bad/x.bin", 42)  # type: ignore[arg-type]


async def test_list_max_keys_beyond_limit_not_implemented(s3_provider: S3StorageProvider):
    with pytest.raises(NotImplementedError):
        await s3_provider.list("prefix/", max_keys=5000)


async def test_retry_on_transient_then_success(monkeypatch, s3_provider: S3StorageProvider):
    """Le provider re-essaie sur SlowDown puis réussit au 2e essai."""
    # Patcher le client pour simuler 1 SlowDown puis succès
    original_put = s3_provider._client.put_object
    call_count = {"n": 0}

    def fake_put_object(**kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise ClientError(
                error_response={"Error": {"Code": "SlowDown", "Message": "slow"}},
                operation_name="PutObject",
            )
        return original_put(**kwargs)

    monkeypatch.setattr(s3_provider._client, "put_object", fake_put_object)

    uri = await s3_provider.put("retry/ok.txt", b"hello")
    assert uri.startswith("s3://")
    assert call_count["n"] == 2  # 1 échec transient + 1 succès


async def test_get_with_botocore_error(monkeypatch, s3_provider: S3StorageProvider):
    """BotoCoreError réseau → StorageError mappée."""
    class FakeBotoError(BotoCoreError):
        fmt = "connection reset"

    def fake_get(**kwargs):
        raise FakeBotoError()

    monkeypatch.setattr(s3_provider._client, "get_object", fake_get)

    with pytest.raises(StorageError):
        await s3_provider.get("any/key")


async def test_delete_transient_then_success(monkeypatch, s3_provider: S3StorageProvider):
    """Delete re-essaie sur transient."""
    original = s3_provider._client.delete_object
    call_count = {"n": 0}

    def fake_delete(**kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise ClientError(
                error_response={"Error": {"Code": "ServiceUnavailable"}},
                operation_name="DeleteObject",
            )
        return original(**kwargs)

    monkeypatch.setattr(s3_provider._client, "delete_object", fake_delete)

    await s3_provider.delete("ok/to-delete.txt")
    assert call_count["n"] == 2


async def test_exists_on_access_denied_raises(monkeypatch, s3_provider: S3StorageProvider):
    """exists() propage AccessDenied (pas False silencieux)."""
    def fake_head(**kwargs):
        raise ClientError(
            error_response={"Error": {"Code": "AccessDenied"}},
            operation_name="HeadObject",
        )

    monkeypatch.setattr(s3_provider._client, "head_object", fake_head)

    with pytest.raises(StoragePermissionError):
        await s3_provider.exists("some/key")
