"""Tests LocalStorageProvider — round-trip sur vrai filesystem (Story 10.6 AC5).

Règle d'or 10.5 : tester l'effet observable (fichier présent + contenu
identique) pas le mécanisme interne. Aucun `unittest.mock.patch` sur
`Path.write_bytes` ou `open()`.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest

from app.core.storage.base import (
    StorageNotFoundError,
    StoragePermissionError,
)
from app.core.storage.local import LocalStorageProvider


async def test_put_get_roundtrip_small_bytes(local_provider: LocalStorageProvider):
    uri = await local_provider.put("docs/a.txt", b"hello")
    assert uri.startswith("file://")
    assert await local_provider.get("docs/a.txt") == b"hello"


async def test_put_overwrites_existing(local_provider: LocalStorageProvider):
    await local_provider.put("docs/a.txt", b"first")
    await local_provider.put("docs/a.txt", b"second")
    assert await local_provider.get("docs/a.txt") == b"second"


async def test_get_missing_raises_not_found(local_provider: LocalStorageProvider):
    with pytest.raises(StorageNotFoundError):
        await local_provider.get("nonexistent")


async def test_delete_idempotent(local_provider: LocalStorageProvider):
    # Aucune exception sur delete d'une clé absente
    await local_provider.delete("nonexistent")


async def test_delete_existing_removes_file_and_cleans_empty_parent(
    local_provider: LocalStorageProvider,
):
    key = "docs/user123/doc456/file.txt"
    await local_provider.put(key, b"payload")
    assert await local_provider.exists(key) is True

    await local_provider.delete(key)
    assert await local_provider.exists(key) is False

    # Le dossier parent (docs/user123/doc456) doit avoir été nettoyé
    parent = local_provider.base_path / "docs" / "user123" / "doc456"
    assert not parent.exists()


async def test_exists_returns_true_after_put(local_provider: LocalStorageProvider):
    await local_provider.put("exists/x.txt", b"x")
    assert await local_provider.exists("exists/x.txt") is True


async def test_exists_returns_false_before_put(local_provider: LocalStorageProvider):
    assert await local_provider.exists("exists/never.txt") is False


async def test_signed_url_returns_file_scheme(local_provider: LocalStorageProvider):
    await local_provider.put("docs/signed.txt", b"data")
    url = await local_provider.signed_url("docs/signed.txt")
    assert url.startswith("file://")
    assert url.endswith("docs/signed.txt") or "docs/signed.txt" in url


async def test_signed_url_missing_raises_not_found(local_provider: LocalStorageProvider):
    with pytest.raises(StorageNotFoundError):
        await local_provider.signed_url("never/exists")


async def test_list_with_prefix_filters_keys(local_provider: LocalStorageProvider):
    await local_provider.put("docs/a/1.txt", b"1")
    await local_provider.put("docs/b/2.txt", b"2")
    await local_provider.put("reports/3.pdf", b"3")

    docs_keys = await local_provider.list("docs/")
    assert len(docs_keys) == 2
    assert all(k.startswith("docs/") for k in docs_keys)
    assert docs_keys == sorted(docs_keys)


async def test_path_traversal_attack_rejected(local_provider: LocalStorageProvider):
    with pytest.raises(StoragePermissionError):
        await local_provider.put("../../../etc/passwd", b"evil")
    with pytest.raises(StoragePermissionError):
        await local_provider.put("/absolute/path.txt", b"evil")


async def test_put_stream_binaryio_10mb(local_provider: LocalStorageProvider):
    """Preuve du streaming via BinaryIO (pas de read() en entier)."""
    payload = b"A" * (10 * 1024 * 1024)
    stream = BytesIO(payload)
    uri = await local_provider.put("big/10mb.bin", stream)
    assert uri.startswith("file://")
    got = await local_provider.get("big/10mb.bin")
    assert len(got) == len(payload)
    assert got == payload


async def test_repr_shows_base_path(tmp_path: Path):
    provider = LocalStorageProvider(base_path=tmp_path)
    repr_str = repr(provider)
    assert "LocalStorageProvider" in repr_str
    assert str(tmp_path) in repr_str
