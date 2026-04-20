"""ABC StorageProvider + hiérarchie d'exceptions canoniques.

Story 10.6 — découple les consommateurs (documents, reports) des détails
d'implémentation storage. NFR24 data residency EU-West-3 + NFR25 chiffrement
at rest SSE-S3 + NFR33 backup 2 AZ via CRR EU-West-3 → EU-West-1.

Références architecture : §D8 (environnements), §D9 (backup PITR), ligne 341
(stockage local MVP → S3 Growth).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageError(Exception):
    """Erreur de la couche storage (parent). Capture toute anomalie transverse."""


class StorageNotFoundError(StorageError):
    """Clé absente au moment du get/delete/signed_url."""


class StoragePermissionError(StorageError):
    """Permission AWS IAM insuffisante ou filesystem EACCES."""


class StorageQuotaError(StorageError):
    """Espace disque insuffisant (local) ou quota bucket S3 dépassé."""


class StorageProvider(ABC):
    """Abstraction I/O fichier — local (MVP) ou S3 EU-West-3 (Growth).

    Contrat d'invariants :
      - `key` est une chaîne opaque ASCII (path-like, séparateur `/`), <= 1024 chars.
      - `put` est idempotent sur la même `key` (écrase).
      - Les exceptions sont canoniques (hiérarchie `StorageError`), jamais boto3 brut.
      - Les méthodes ne bloquent PAS l'event loop : I/O via `asyncio.to_thread`.
    """

    @abstractmethod
    async def put(
        self,
        key: str,
        content: bytes | BinaryIO,
        *,
        content_type: str | None = None,
    ) -> str:
        """Stocke `content` sous `key`. Retourne l'URI canonique
        (`file:///abs/path` local ou `s3://bucket/key`). Écrase si déjà présent."""

    @abstractmethod
    async def get(self, key: str) -> bytes:
        """Récupère le contenu binaire complet sous `key`.
        Lève `StorageNotFoundError` si absent."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Supprime `key`. Idempotent : `StorageNotFoundError` NON levée
        si déjà absent (aligne avec sémantique S3 DeleteObject)."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Retourne True si `key` existe, False sinon (jamais d'exception)."""

    @abstractmethod
    async def signed_url(self, key: str, *, ttl_seconds: int = 900) -> str:
        """Retourne une URL pré-signée (ou URI `file://` pour local).

        Défaut 15 min (900 s). TTL borné [1, 3600] côté implémentations S3.

        **Contrat de présence** (divergent — Story 10.6 post-review MEDIUM-10.6-4) :
          - ``LocalStorageProvider`` : lève ``StorageNotFoundError`` si la clé
            est absente (check `is_file` synchrone — pas d'URL signée pour un
            fichier inexistant).
          - ``S3StorageProvider`` : émet une URL pré-signée valide **sans
            pré-check** (économise 1 round-trip HEAD + réduit énumération
            temporelle) — le 404 n'apparaît qu'à la consommation de l'URL
            par le client.

        Les consommateurs qui requièrent une garantie de présence doivent
        appeler ``await storage.exists(key)`` avant ``signed_url(key)``."""

    @abstractmethod
    async def list(self, prefix: str = "", *, max_keys: int = 1000) -> list[str]:
        """Liste les `key` sous `prefix`, triées lexicographiquement,
        plafonnées à `max_keys` (pagination hors scope MVP)."""
