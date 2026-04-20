"""Fixtures partagées — tests storage Story 10.6."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.storage.local import LocalStorageProvider


@pytest.fixture
def local_provider(tmp_path: Path) -> LocalStorageProvider:
    """LocalStorageProvider isolé dans un tmpdir par test (pas d'effet global)."""
    return LocalStorageProvider(base_path=tmp_path / "storage")
