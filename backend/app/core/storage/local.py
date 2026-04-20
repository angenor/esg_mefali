"""LocalStorageProvider — backend filesystem (MVP default).

Story 10.6 — remplit le contrat `StorageProvider` via un répertoire local
(typiquement ``backend/uploads/``). I/O déléguée à `asyncio.to_thread` pour
ne jamais bloquer l'event loop FastAPI.

Sécurité :
  - Défense en profondeur path-traversal : rejette `..` et segments absolus
    même si `storage_key_for_document` produit toujours des clés sûres.
  - `signed_url` retourne un URI `file://` (pas de vraie URL pré-signée
    HTTP — limitation MVP documentée storage.md §5).
"""

from __future__ import annotations

import asyncio
import logging
import shutil
from io import IOBase
from pathlib import Path
from typing import BinaryIO

from .base import (
    StorageError,
    StorageNotFoundError,
    StoragePermissionError,
    StorageProvider,
    StorageQuotaError,
)

logger = logging.getLogger(__name__)

# Seuil d'espace disque minimal (aligné `documents.service` legacy)
MIN_DISK_SPACE_BYTES = 50 * 1024 * 1024

# Taille chunk streaming BinaryIO (1 MB)
_STREAM_CHUNK = 1024 * 1024


def _validate_key(key: str) -> None:
    """Défense en profondeur path-traversal."""
    if not key:
        raise StoragePermissionError("key cannot be empty")
    if key.startswith("/"):
        raise StoragePermissionError(f"absolute path not allowed: {key}")
    # Rejette tout segment `..` (normalisation pathlib indépendante)
    for segment in key.replace("\\", "/").split("/"):
        if segment == "..":
            raise StoragePermissionError(f"path traversal detected: {key}")


class LocalStorageProvider(StorageProvider):
    """Provider filesystem local — MVP default (zéro dépendance externe)."""

    def __init__(self, base_path: Path) -> None:
        self._base_path = Path(base_path)
        self._initialized = False

    def __repr__(self) -> str:
        return f"LocalStorageProvider(base_path={self._base_path!r})"

    @property
    def base_path(self) -> Path:
        return self._base_path

    def _ensure_base(self) -> None:
        """Lazy create du base_path (permet un constructor sans side-effect)."""
        if not self._initialized:
            self._base_path.mkdir(parents=True, exist_ok=True)
            self._initialized = True

    def local_path(self, key: str) -> Path:
        """Chemin filesystem absolu pour la clé (utilisé par les endpoints
        FastAPI local pour `FileResponse`). Valide la clé contre path-traversal."""
        _validate_key(key)
        return (self._base_path / key).resolve()

    def _check_disk_space(self, required_bytes: int) -> None:
        """Garde quota local — lève ``StorageQuotaError`` si insuffisant."""
        target = self._base_path if self._base_path.exists() else self._base_path.parent
        try:
            usage = shutil.disk_usage(target)
        except OSError:
            logger.warning("Impossible de vérifier l'espace disque disponible")
            return
        # Vérifie MIN (évite saturation) + required_bytes
        if usage.free < max(MIN_DISK_SPACE_BYTES, required_bytes):
            raise StorageQuotaError(
                "Espace disque insuffisant. Libérez de l'espace avant "
                "d'uploader de nouveaux fichiers."
            )

    # ─── put ──────────────────────────────────────────────────────

    async def put(
        self,
        key: str,
        content: bytes | BinaryIO,
        *,
        content_type: str | None = None,
    ) -> str:
        _validate_key(key)
        self._ensure_base()

        dest = self._base_path / key

        if isinstance(content, (bytes, bytearray)):
            self._check_disk_space(len(content))
            await asyncio.to_thread(self._write_bytes, dest, bytes(content))
        elif hasattr(content, "read"):
            # Quota : best-effort (on n'anticipe pas la taille d'un BinaryIO)
            self._check_disk_space(MIN_DISK_SPACE_BYTES)
            await asyncio.to_thread(self._write_stream, dest, content)
        else:
            raise StorageError(
                f"content must be bytes or BinaryIO, got {type(content).__name__}"
            )

        return f"file://{dest.resolve()}"

    @staticmethod
    def _write_bytes(dest: Path, content: bytes) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)

    @staticmethod
    def _write_stream(dest: Path, stream: BinaryIO | IOBase) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as fh:
            while True:
                chunk = stream.read(_STREAM_CHUNK)
                if not chunk:
                    break
                fh.write(chunk)

    # ─── get ──────────────────────────────────────────────────────

    async def get(self, key: str) -> bytes:
        _validate_key(key)
        dest = self._base_path / key
        if not dest.is_file():
            raise StorageNotFoundError(f"key not found: {key}")
        return await asyncio.to_thread(dest.read_bytes)

    # ─── delete ───────────────────────────────────────────────────

    async def delete(self, key: str) -> None:
        _validate_key(key)
        dest = self._base_path / key
        await asyncio.to_thread(self._unlink_and_cleanup, dest)

    @staticmethod
    def _unlink_and_cleanup(dest: Path) -> None:
        try:
            dest.unlink(missing_ok=True)
        except OSError as exc:
            logger.debug("delete local storage: unlink %s failed: %s", dest, exc)
            return
        parent = dest.parent
        try:
            if parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
        except OSError as exc:  # noqa: BLE001 cleanup best-effort
            logger.debug("delete local storage: parent cleanup failed: %s", exc)

    # ─── exists ───────────────────────────────────────────────────

    async def exists(self, key: str) -> bool:
        try:
            _validate_key(key)
        except StoragePermissionError:
            return False
        dest = self._base_path / key
        return await asyncio.to_thread(dest.is_file)

    # ─── signed_url ───────────────────────────────────────────────

    async def signed_url(self, key: str, *, ttl_seconds: int = 900) -> str:
        _validate_key(key)
        dest = self._base_path / key
        if not await asyncio.to_thread(dest.is_file):
            raise StorageNotFoundError(f"key not found: {key}")
        # Local : pas de vraie URL pré-signée — URI `file://` consommé par
        # les endpoints FastAPI qui font `FileResponse(path=...)`.
        return f"file://{dest.resolve()}"

    # ─── list ─────────────────────────────────────────────────────

    async def list(self, prefix: str = "", *, max_keys: int = 1000) -> list[str]:
        return await asyncio.to_thread(self._list_sync, prefix, max_keys)

    def _list_sync(self, prefix: str, max_keys: int) -> list[str]:
        if not self._base_path.exists():
            return []
        root = self._base_path
        # Pattern glob : `<prefix>**/*` ; si prefix vide → tout
        pattern = f"{prefix}**/*" if prefix else "**/*"
        keys: list[str] = []
        for path in root.glob(pattern):
            if path.is_file():
                keys.append(str(path.relative_to(root)).replace("\\", "/"))
        keys.sort()
        return keys[:max_keys]
