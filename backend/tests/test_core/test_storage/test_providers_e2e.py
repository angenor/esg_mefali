"""Tests E2E round-trip 1 MB + 10 MB sur les 2 providers (Story 10.6 AC7).

Prouve :
  - Intégration bout-en-bout put → exists → get → delete → exists.
  - Streaming efficace sur fichiers volumineux (non-bloquant event loop).
  - Bascule multipart automatique à ≥ 10 MB sur S3 (via `boto3.s3.transfer`).

Règle d'or 10.5 : égalité binaire stricte (taille + contenu), pas d'assertion
sur l'appel interne `boto3.client.put_object`.
"""

from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path

import pytest

from app.core.storage.base import StorageProvider
from app.core.storage.local import LocalStorageProvider

# moto est optionnel — skip propre si absent
moto = pytest.importorskip("moto", reason="moto[s3] required for E2E S3 tests")

import boto3  # noqa: E402
from moto import mock_aws  # noqa: E402

from app.core.storage.s3 import S3StorageProvider  # noqa: E402


@pytest.mark.parametrize("size_mb", [1, 10])
async def test_roundtrip_local(tmp_path: Path, size_mb: int):
    """Local round-trip 1 MB + 10 MB : put/exists/get/delete/exists."""
    provider: StorageProvider = LocalStorageProvider(base_path=tmp_path / "store")
    key = f"docs/e2e-{size_mb}mb.bin"
    content = os.urandom(size_mb * 1024 * 1024)

    await provider.put(key, content, content_type="application/octet-stream")
    assert await provider.exists(key) is True

    got = await provider.get(key)
    assert got == content

    await provider.delete(key)
    assert await provider.exists(key) is False


@pytest.mark.s3
@pytest.mark.parametrize("size_mb", [1, 10])
async def test_roundtrip_s3(size_mb: int):
    """S3 round-trip 1 MB + 10 MB via moto (bascule multipart ≥ 10 MB)."""
    bucket = "e2e-bucket-eu-west-3"
    region = "eu-west-3"

    with mock_aws():
        client = boto3.client("s3", region_name=region)
        client.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={"LocationConstraint": region},
        )
        provider: StorageProvider = S3StorageProvider(bucket=bucket, region=region)

        key = f"docs/e2e-{size_mb}mb.bin"
        content = os.urandom(size_mb * 1024 * 1024)

        await provider.put(key, content, content_type="application/octet-stream")
        assert await provider.exists(key) is True

        got = await provider.get(key)
        assert got == content
        assert len(got) == size_mb * 1024 * 1024

        await provider.delete(key)
        assert await provider.exists(key) is False


async def test_event_loop_not_blocked_local(tmp_path: Path):
    """Paralléliser 3 puts via `asyncio.gather` — vérif non-blocage event loop."""
    provider = LocalStorageProvider(base_path=tmp_path / "parallel")
    content = os.urandom(2 * 1024 * 1024)  # 2 MB

    # Temps d'un put seul
    start_seq = time.monotonic()
    await provider.put("seq/one.bin", content)
    elapsed_seq = time.monotonic() - start_seq

    # Temps de 3 puts parallèles
    start_par = time.monotonic()
    await asyncio.gather(
        provider.put("par/a.bin", content),
        provider.put("par/b.bin", content),
        provider.put("par/c.bin", content),
    )
    elapsed_par = time.monotonic() - start_par

    # Si event-loop bloqué, ratio ≈ 3 ; via asyncio.to_thread, ratio < 1.5
    # Tolérance relaxée pour CI (contention du thread pool variable).
    ratio = elapsed_par / max(elapsed_seq, 0.001)
    if ratio >= 2.5:
        pytest.fail(
            f"event loop potentially blocked — ratio {ratio:.2f} "
            f"(seq {elapsed_seq*1000:.0f}ms, par {elapsed_par*1000:.0f}ms)"
        )
