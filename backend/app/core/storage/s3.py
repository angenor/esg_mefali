"""S3StorageProvider — AWS S3 EU-West-3 Paris (Phase Growth).

Story 10.6 — remplit le contrat `StorageProvider` via boto3 sync délégué
à `asyncio.to_thread`. Justification async : aiobotocore épingle une version
botocore incompatible avec langchain-openai ; l'overhead thread pool est
< 1ms/call vs gain de stabilité packaging. Seuil de re-évaluation :
> 100 calls/sec concurrents avec contention du thread pool → migrer vers
`aioboto3` (Phase Growth scale).

Conformité NFR :
  - NFR24 data residency : région par défaut ``eu-west-3`` (Paris).
  - NFR25 chiffrement at rest : SSE-S3 AES256 systématique sur tous les `put`.
  - NFR33 backup 2 AZ : via CRR EU-West-3 → EU-West-1 configuré Story 10.7.
"""

from __future__ import annotations

import asyncio
import logging
from io import BytesIO
from typing import BinaryIO

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from .base import (
    StorageError,
    StorageNotFoundError,
    StoragePermissionError,
    StorageProvider,
    StorageQuotaError,
)

logger = logging.getLogger(__name__)

# Seuil multipart — aligné boto3.s3.transfer default (8 MB chunks)
MULTIPART_THRESHOLD_BYTES = 10 * 1024 * 1024

# Retry : codes transitoires re-essayables (permanents = propagation directe)
_TRANSIENT_ERROR_CODES = frozenset(
    {
        "RequestTimeout",
        "RequestTimeoutException",
        "ServiceUnavailable",
        "SlowDown",
        "InternalError",
        "ThrottlingException",
    }
)

_MAX_ATTEMPTS = 3
_BACKOFF_SECONDS = (0.2, 0.4, 0.8)


def _is_transient_error(exc: Exception) -> bool:
    """Politique transient : timeout/throttle/5xx → retry ; permanent → no."""
    if isinstance(exc, ClientError):
        code = exc.response.get("Error", {}).get("Code", "")
        return code in _TRANSIENT_ERROR_CODES
    # BotoCoreError couvre les erreurs réseau/timeout côté client
    return isinstance(exc, BotoCoreError)


def _map_client_error(exc: ClientError, key: str) -> StorageError:
    """Traduit une ClientError boto3 en hiérarchie canonique StorageError.

    Aucune stack boto3 brute ne remonte aux appelants (isolation API contract).
    """
    code = exc.response.get("Error", {}).get("Code", "")
    if code in {"NoSuchKey", "404", "NotFound"}:
        return StorageNotFoundError(f"key not found: {key}")
    if code in {"AccessDenied", "403"}:
        return StoragePermissionError(f"IAM denied for key {key}")
    if code in {"QuotaExceeded", "SlowDown"}:
        return StorageQuotaError(f"S3 quota or throttling on key {key}: {code}")
    return StorageError(f"S3 failure on key {key}: {code}")


class S3StorageProvider(StorageProvider):
    """Provider AWS S3 — Phase Growth EU-West-3 (NFR24 data residency).

    boto3 est **sync** : chaque appel est délégué à `asyncio.to_thread`.
    Retry transient (3 tentatives, backoff 200/400/800 ms) sur
    ``ClientError`` / ``BotoCoreError`` dont le code est dans
    ``_TRANSIENT_ERROR_CODES``. Les erreurs permanentes (``NoSuchKey``,
    ``AccessDenied``) ne sont pas retryées.
    """

    def __init__(self, bucket: str, region: str = "eu-west-3") -> None:
        if not bucket:
            raise StorageError("bucket is required for S3StorageProvider")
        self._bucket = bucket
        self._region = region
        # Client boto3 singleton au constructor — ré-utilisation NFR perf.
        # `request_checksum_calculation="when_required"` : les checksums
        # ne sont calculés que lorsque le service le requiert, évite les
        # faux positifs `FlexibleChecksumError` côté multipart avec moto
        # et réduit le CPU sur les gros uploads.
        self._client = boto3.client(
            "s3",
            region_name=region,
            config=Config(
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )

    def __repr__(self) -> str:
        # Masque les credentials (jamais d'accès à self._client._request_signer)
        return f"S3StorageProvider(bucket={self._bucket!r}, region={self._region!r})"

    @property
    def bucket(self) -> str:
        return self._bucket

    @property
    def region(self) -> str:
        return self._region

    # ─── Retry helper ─────────────────────────────────────────────

    async def _call_with_retry(self, op_name: str, fn, *args, **kwargs):
        """Wrap un appel boto3 sync + retry exponentiel limité."""
        attempt = 0
        last_exc: Exception | None = None
        while attempt < _MAX_ATTEMPTS:
            try:
                return await asyncio.to_thread(fn, *args, **kwargs)
            except (ClientError, BotoCoreError) as exc:
                last_exc = exc
                if not _is_transient_error(exc) or attempt == _MAX_ATTEMPTS - 1:
                    raise
                delay = _BACKOFF_SECONDS[min(attempt, len(_BACKOFF_SECONDS) - 1)]
                logger.warning(
                    "s3.%s transient error (attempt %d/%d): %s — retry in %ss",
                    op_name,
                    attempt + 1,
                    _MAX_ATTEMPTS,
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)
                attempt += 1
        # Inatteignable théoriquement (raise dans la boucle)
        assert last_exc is not None  # noqa: S101 defensive
        raise last_exc

    # ─── put ──────────────────────────────────────────────────────

    async def put(
        self,
        key: str,
        content: bytes | BinaryIO,
        *,
        content_type: str | None = None,
    ) -> str:
        ct = content_type or "application/octet-stream"
        extra_args = {"ServerSideEncryption": "AES256", "ContentType": ct}

        try:
            if isinstance(content, (bytes, bytearray)):
                if len(content) < MULTIPART_THRESHOLD_BYTES:
                    # Single-part — put_object direct
                    await self._call_with_retry(
                        "put_object",
                        self._client.put_object,
                        Bucket=self._bucket,
                        Key=key,
                        Body=bytes(content),
                        ContentType=ct,
                        ServerSideEncryption="AES256",
                    )
                else:
                    # >= 10 MB : multipart via TransferManager (boto3.s3.transfer)
                    buffer = BytesIO(bytes(content))
                    await self._call_with_retry(
                        "upload_fileobj",
                        self._client.upload_fileobj,
                        buffer,
                        self._bucket,
                        key,
                        ExtraArgs=extra_args,
                    )
            elif hasattr(content, "read"):
                # BinaryIO → multipart systématique (taille inconnue a priori)
                await self._call_with_retry(
                    "upload_fileobj",
                    self._client.upload_fileobj,
                    content,
                    self._bucket,
                    key,
                    ExtraArgs=extra_args,
                )
            else:
                raise StorageError(
                    f"content must be bytes or BinaryIO, got {type(content).__name__}"
                )
        except ClientError as exc:
            raise _map_client_error(exc, key) from exc
        except BotoCoreError as exc:
            raise StorageError(f"S3 network failure on put {key}: {exc}") from exc

        return f"s3://{self._bucket}/{key}"

    # ─── get ──────────────────────────────────────────────────────

    async def get(self, key: str) -> bytes:
        try:
            response = await self._call_with_retry(
                "get_object",
                self._client.get_object,
                Bucket=self._bucket,
                Key=key,
            )
        except ClientError as exc:
            raise _map_client_error(exc, key) from exc
        except BotoCoreError as exc:
            raise StorageError(f"S3 network failure on get {key}: {exc}") from exc

        body = response["Body"]
        # body.read() est sync → délégué
        return await asyncio.to_thread(body.read)

    # ─── delete ───────────────────────────────────────────────────

    async def delete(self, key: str) -> None:
        # S3 delete_object est idempotent : 204 même si absent
        try:
            await self._call_with_retry(
                "delete_object",
                self._client.delete_object,
                Bucket=self._bucket,
                Key=key,
            )
        except ClientError as exc:
            raise _map_client_error(exc, key) from exc
        except BotoCoreError as exc:
            raise StorageError(f"S3 network failure on delete {key}: {exc}") from exc

    # ─── exists ───────────────────────────────────────────────────

    async def exists(self, key: str) -> bool:
        try:
            await self._call_with_retry(
                "head_object",
                self._client.head_object,
                Bucket=self._bucket,
                Key=key,
            )
            return True
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in {"404", "NoSuchKey", "NotFound"}:
                return False
            # Autres erreurs (AccessDenied, ...) → propagation canonique
            raise _map_client_error(exc, key) from exc
        except BotoCoreError as exc:
            raise StorageError(f"S3 network failure on exists {key}: {exc}") from exc

    # ─── signed_url ───────────────────────────────────────────────

    async def signed_url(self, key: str, *, ttl_seconds: int = 900) -> str:
        if not (1 <= ttl_seconds <= 3600):
            raise ValueError("ttl_seconds must be in [1, 3600]")
        # generate_presigned_url est sync mais purement local (signature HMAC)
        # → pas de round-trip réseau, mais on délègue au thread pool pour
        # cohérence et éviter tout blocage sur crypto lente.
        try:
            return await asyncio.to_thread(
                self._client.generate_presigned_url,
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=ttl_seconds,
            )
        except ClientError as exc:
            raise _map_client_error(exc, key) from exc
        except BotoCoreError as exc:
            raise StorageError(
                f"S3 signed_url failure for {key}: {exc}"
            ) from exc

    # ─── list ─────────────────────────────────────────────────────

    async def list(self, prefix: str = "", *, max_keys: int = 1000) -> list[str]:
        if max_keys > 1000:
            raise NotImplementedError(
                "pagination beyond 1000 keys deferred to Phase Growth"
            )
        try:
            response = await self._call_with_retry(
                "list_objects_v2",
                self._client.list_objects_v2,
                Bucket=self._bucket,
                Prefix=prefix,
                MaxKeys=max_keys,
            )
        except ClientError as exc:
            raise _map_client_error(exc, prefix) from exc
        except BotoCoreError as exc:
            raise StorageError(
                f"S3 list failure for prefix {prefix}: {exc}"
            ) from exc

        contents = response.get("Contents", [])
        keys = sorted(obj["Key"] for obj in contents)
        return keys
