"""Tests de la factory `get_storage_provider` + helpers (Story 10.6).

Couvre le chemin factory (lru_cache, switch local/s3, erreurs).
"""

from __future__ import annotations

import uuid

import pytest

from app.core import storage as storage_module
from app.core.config import settings
from app.core.storage import (
    StorageError,
    get_storage_provider,
    storage_key_for_document,
    storage_key_for_report,
)
from app.core.storage.local import LocalStorageProvider


def test_storage_key_for_document_shape():
    uid = uuid.uuid4()
    did = uuid.uuid4()
    key = storage_key_for_document(uid, did, "rapport.pdf")
    assert key == f"documents/{uid}/{did}/rapport.pdf"


def test_storage_key_for_report_shape():
    rid = uuid.uuid4()
    key = storage_key_for_report(rid, "esg.pdf")
    assert key == f"reports/{rid}/esg.pdf"


def test_factory_returns_local_by_default():
    provider = get_storage_provider()
    assert isinstance(provider, LocalStorageProvider)


def test_factory_is_cached():
    p1 = get_storage_provider()
    p2 = get_storage_provider()
    assert p1 is p2


def test_factory_s3_requires_bucket(monkeypatch):
    storage_module._reset_storage_provider_cache()
    monkeypatch.setattr(settings, "storage_provider", "s3")
    monkeypatch.setattr(settings, "aws_s3_bucket", "")
    try:
        with pytest.raises(StorageError, match="AWS_S3_BUCKET"):
            get_storage_provider()
    finally:
        storage_module._reset_storage_provider_cache()


def test_factory_s3_builds_provider(monkeypatch):
    pytest.importorskip("moto")
    from moto import mock_aws

    storage_module._reset_storage_provider_cache()
    monkeypatch.setattr(settings, "storage_provider", "s3")
    monkeypatch.setattr(settings, "aws_s3_bucket", "my-bucket")
    monkeypatch.setattr(settings, "aws_region", "eu-west-3")

    from app.core.storage.s3 import S3StorageProvider

    with mock_aws():
        provider = get_storage_provider()
        assert isinstance(provider, S3StorageProvider)
        assert provider.bucket == "my-bucket"
        assert provider.region == "eu-west-3"

    storage_module._reset_storage_provider_cache()


def test_resolve_local_path_absolute(tmp_path):
    from app.core.storage import _resolve_local_path

    abs_path = _resolve_local_path(str(tmp_path))
    assert abs_path == tmp_path.resolve()


def test_resolve_local_path_relative():
    from app.core.storage import _resolve_local_path

    rel = _resolve_local_path("uploads")
    # Résolu depuis backend/
    assert rel.is_absolute()
    assert rel.name == "uploads"
