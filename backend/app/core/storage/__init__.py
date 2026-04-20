"""Couche d'abstraction storage — Story 10.6.

Façade publique étroite : seuls 6 symboles sont exportés — audit de surface
API via ``python -c "from app.core.storage import ..."`` (cf. AC1).

Providers disponibles :
  - ``LocalStorageProvider`` : MVP default, filesystem local.
  - ``S3StorageProvider`` : Phase Growth, AWS S3 EU-West-3 (import lazy).

Sélection via ``Settings.storage_provider`` ∈ {"local", "s3"}.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .base import (
    StorageError,
    StorageNotFoundError,
    StorageProvider,
)
from .keys import storage_key_for_document, storage_key_for_report

__all__ = [
    "StorageProvider",
    "StorageError",
    "StorageNotFoundError",
    "get_storage_provider",
    "storage_key_for_document",
    "storage_key_for_report",
]


def _resolve_local_path(raw: str) -> Path:
    """Résout le chemin local : relatif depuis ``backend/`` ou absolu."""
    path = Path(raw)
    if path.is_absolute():
        return path.resolve()
    # `backend/app/core/storage/__init__.py` → parents[3] == backend/
    backend_root = Path(__file__).resolve().parents[3]
    return (backend_root / path).resolve()


@lru_cache(maxsize=1)
def get_storage_provider() -> StorageProvider:
    """Factory cachée (singleton process-level).

    Retourne l'instance configurée via ``Settings.storage_provider`` :
      - ``"local"`` → ``LocalStorageProvider`` (zéro dépendance externe).
      - ``"s3"`` → ``S3StorageProvider`` (import lazy de boto3).

    Utilisable comme dépendance FastAPI : ``Depends(get_storage_provider)``.
    """
    from app.core.config import settings

    from .local import LocalStorageProvider

    provider = settings.storage_provider.lower()

    if provider == "local":
        return LocalStorageProvider(base_path=_resolve_local_path(settings.storage_local_path))

    if provider == "s3":
        if not settings.aws_s3_bucket:
            raise StorageError(
                "AWS_S3_BUCKET is required when STORAGE_PROVIDER=s3"
            )
        # Import lazy : évite que boto3 soit requis au boot si storage=local
        from .s3 import S3StorageProvider

        return S3StorageProvider(
            bucket=settings.aws_s3_bucket,
            region=settings.aws_region,
        )

    # Safety net — la regex Pydantic bloque normalement
    raise StorageError(f"unknown storage_provider: {provider!r}")


def _reset_storage_provider_cache() -> None:
    """Helper de test — invalide le singleton ``lru_cache``.

    **Ne pas** exporter dans ``__all__`` (API publique étroite). Consommé
    uniquement par les fixtures pytest qui font ``monkeypatch.setattr`` sur
    ``settings.storage_provider``.
    """
    get_storage_provider.cache_clear()
