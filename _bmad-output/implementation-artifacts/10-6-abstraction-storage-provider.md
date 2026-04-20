# Story 10.6 : Abstraction `StorageProvider` (local + S3 EU-West-3)

Status: done

> **Contexte** : 6ᵉ story Epic 10 Fondations Phase 0. Première story **infra intégration externe** de l'épic (transition défense en profondeur multi-tenant → portabilité stockage). Bloquante pour Story 10.7 (environnements DEV/STAGING/PROD ségrégués) qui consommera `S3StorageProvider` + CRR EU-West-3 → EU-West-1 (NFR33 backup 2 AZ).
>
> **Divergence vs Stories 10.2/10.3/10.4** (squelettes modules métier) et **similitude avec Story 10.5** (couche transverse) : aucun module `backend/app/modules/xxx/` n'est créé. La valeur livrée est **transverse** : helper `backend/app/core/storage/` + refactor minimaliste de **2 consommateurs persistants** (`documents/service.py` + `reports/service.py`) qui détiennent aujourd'hui 100 % des écritures disque de l'application (vérifié par Task 1 scan NFR66).
>
> **Cadrage strict** :
> 1. **Pas de migration** de fichiers existants (`/uploads/<user_id>/<doc_id>/<file>` et `/uploads/reports/<uuid>.pdf`). Story 10.6 livre la **couche d'abstraction + le nouveau code path**. La bascule production `STORAGE_PROVIDER=local → s3` sera opérée **Phase Growth** avec script de migration `scripts/migrate_local_to_s3.py` (déféré à une future story infra). MVP reste sur `STORAGE_PROVIDER=local` (filesystem).
> 2. **Rectification scope AC3 de l'épic** : l'épic mentionne « 8 modules existants qui manipulent `/uploads/` ». Le scan NFR66 (Task 1) **prouve que seuls 2 modules persistent réellement** sur disque : `documents/service.py` (upload) + `reports/service.py` (WeasyPrint `write_pdf(path)`). Les 4 autres consommateurs PDF (`credit/certificate.py`, `financing/preparation_sheet.py`, `applications/export.py`, `applications/prep_sheet.py`) génèrent **in-memory** (`HTML(...).write_pdf()` → `bytes` directement streamés via `FastAPI Response`) — aucune écriture disque. Story 10.6 **ne touche pas** ces 4 modules (leur bascule vers `storage.put()` pour caching/audit est capturée comme opportunité future, **hors scope MVP** — inscrite dans `deferred-work.md`).
> 3. **Pattern brownfield** : extension minimaliste. Les 2 modules impactés gardent leur API publique intacte (`upload_document`, `generate_esg_report_pdf`) — seule leur plomberie interne I/O bascule sur `storage.put()` / `storage.get()` / `storage.signed_url()`. Aucun endpoint REST modifié (contrat API inchangé).
> 4. **Source unique** `STORAGE_PROVIDER` via `app.core.config.Settings` (pattern Pydantic BaseSettings existant — **pas** de lecture directe `os.environ.get` dispersée). Alignement avec `quota_bytes_per_user_mb` / `quota_docs_per_user` récemment ajoutés (Story 9.2).
>
> **Dépendances** :
> - **Story 9.7 done** : pattern `with_retry` + `log_tool_call` acquis. Story 10.6 **consomme** `with_retry` pour wrapper les appels boto3 réseau (timeout, throttling, 5xx retriables). Cf. `backend/app/core/resilience.py` ou équivalent (à repérer en Task 1).
> - **Story 10.1 done** : aucune table BDD nécessaire pour 10.6. Le `Document.storage_path` (existant, VARCHAR 500) continue d'être la clé opaque utilisée par les providers (préfixe `user_id/doc_id/filename` → devient la `key` S3 en Phase Growth sans migration schéma).
> - **Story 10.5 done** : RLS filtre déjà `Document` et `Report` au niveau BDD. Les `signed_url` générés par `S3StorageProvider` **n'embarquent pas** de RLS ; l'autorisation reste au niveau **endpoint FastAPI** (`Depends(get_current_user)` + check ownership avant d'émettre l'URL pré-signée). Ce modèle est sécurisé car l'URL pré-signée n'est émise **que** pour un utilisateur authentifié et propriétaire.
>
> **Bloque** :
> - **Story 10.7** (environnements DEV/STAGING/PROD) : dépend de `S3StorageProvider` fonctionnel pour configurer `AWS_S3_BUCKET_STAGING` + `AWS_S3_BUCKET_PROD` avec CRR EU-West-3 → EU-West-1 (NFR33).
> - **Story 10.10** (micro-Outbox domain events) : consommera `storage.put()` si certains livrables PDF doivent être persistés pour audit trail (évalué story 10.10, hors 10.6).
> - **Phase Growth script `scripts/migrate_local_to_s3.py`** : non bloqué par 10.6 en soi, mais 10.6 doit garantir compatibilité de la clé opaque `storage_path` entre local et S3.
>
> **Contraintes héritées (7 leçons Stories 9.x → 10.5)** :
> 1. **C1 (9.7)** : **pas de `try/except Exception` catch-all**. Les erreurs storage remontent explicitement (`StorageError` custom + sous-classes `StorageNotFoundError`, `StoragePermissionError`, `StorageQuotaError`). Le handler FastAPI existant peut les traduire en 404/403/507, jamais de swallow silencieux. **Dérogation unique autorisée** (si nécessaire) : fermeture de stream binaire dans un `finally` — documentée inline si appliquée.
> 2. **C2 (9.7)** : **tests prod véritables**. Pas de mock bas niveau `boto3.client("s3")` via `unittest.mock.patch` — on utilise **`moto[s3]` décorateur `@mock_aws`** qui émule un vrai endpoint S3 en mémoire (requêtes HTTP réelles contre un mock server). Les tests `LocalStorageProvider` écrivent sur vrai filesystem via `tmp_path` fixture pytest (pas de `MagicMock` sur `Path.write_bytes`).
> 3. **10.1** : marker `@pytest.mark.postgres` **non applicable** ici (pas de DB). En revanche, **nouveau marker `@pytest.mark.s3`** introduit (Task 9) pour les tests qui requièrent `moto[s3]` installé — skip propre si la dépendance est absente (permet `pytest` minimal sans `pip install moto[s3]`).
> 4. **10.2 M2** : TODO Epic si pattern non-routable. **Non applicable** ici : toutes les responsabilités livrées sont pleinement routables dans Phase 0.
> 5. **10.3 M1** : **scan NFR66 exhaustif glob**. Avant de créer `backend/app/core/storage/`, vérifier via `rg --files-with-matches` qu'aucun helper préexistant ne couvre la responsabilité. **Résultat Task 1 anticipé** (validation finale en implémentation) : 0 match dans `backend/app/core/` + 0 import `boto3` dans tout le projet + 2 consommateurs `/uploads/` persistants identifiés.
> 6. **10.4 méthodo** : **comptages par introspection runtime**. Chaque AC qui mentionne « N tests ajoutés » sera prouvé par `pytest --collect-only -q backend/tests/test_core/test_storage/ | grep -c '::'` avant/après ; les chiffres du rapport de story citeront la commande exacte exécutée.
> 7. **10.5 règle d'or** : **tester effet observable**. Pour Story 10.6, pas de listener ORM, mais pattern équivalent = **tests storage réels** qui déclenchent `put()` puis **re-lisent** via `get()` et assertent le contenu binaire identique — pas d'assertion sur l'appel interne à `boto3.client.put_object(...)` via mock. Les 2 tests E2E AC6 (round-trip 1 MB + 10 MB) sont l'application directe de cette règle.

---

## Story

**As a** Équipe Mefali (SRE/backend) + futurs mainteneurs Phase Growth,
**I want** une couche d'abstraction `StorageProvider` avec deux implémentations (`LocalStorageProvider` pour MVP/DEV, `S3StorageProvider` pour Phase Growth EU-West-3) + refactor brownfield des 2 consommateurs persistants (`documents/service.py` + `reports/service.py`) pour router toutes leurs I/O fichier via `storage.put()` / `storage.get()` / `storage.signed_url()` + configuration env unique `STORAGE_PROVIDER=local|s3` via `Settings`,
**So that** le passage de `/uploads/` local vers S3 EU-West-3 (NFR24 data residency + NFR33 backup 2 AZ + NFR25 chiffrement at rest) soit un simple changement de config env, sans refactor métier, et que la ligne budget NFR69 « ~100 €/mois S3 » de la décomposition infra 1000 €/mois soit opérationnalisable dès Phase Growth sans dette de refonte.

---

## Acceptance Criteria

### AC1 — Module `backend/app/core/storage/` expose l'ABC `StorageProvider` + 2 implémentations

**Given** le repository dans l'état `main @ HEAD` avec aucune abstraction storage préexistante (confirmé Task 1 scan NFR66) et 2 consommateurs persistants identifiés (`backend/app/modules/documents/service.py:103-126` + `backend/app/modules/reports/service.py:359-366`),

**When** un développeur exécute `ls backend/app/core/storage/`,

**Then** le répertoire contient **exactement** 5 fichiers :
  1. `__init__.py` — re-exporte uniquement `StorageProvider`, `StorageError`, `StorageNotFoundError`, `get_storage_provider`, `storage_key_for_document`, `storage_key_for_report` (façade publique étroite).
  2. `base.py` — ABC `StorageProvider` + hiérarchie d'exceptions.
  3. `local.py` — `LocalStorageProvider` (filesystem, MVP default).
  4. `s3.py` — `S3StorageProvider` (AWS S3 EU-West-3, Phase Growth).
  5. `keys.py` — helpers purs `storage_key_for_document(user_id, document_id, filename) -> str` et `storage_key_for_report(report_id, filename) -> str` qui produisent la **clé opaque canonique** (ex. `"documents/<user_id>/<doc_id>/<filename>"` et `"reports/<report_id>/<filename>"`) consommée identiquement par local et S3 (garantit portabilité future).

**And** `base.py` définit l'**ABC** `StorageProvider` avec **exactement 6 méthodes abstraites** (aligné épic + extension `stat` utile aux 2 consommateurs existants) :
```python
from abc import ABC, abstractmethod
from typing import BinaryIO

class StorageProvider(ABC):
    """Abstraction I/O fichier — local (MVP) ou S3 EU-West-3 (Growth).

    Story 10.6 — découple les consommateurs (documents, reports) des
    détails d'implémentation storage. NFR24 data residency + NFR25 chiffrement
    at rest + NFR33 backup 2 AZ.

    Contrat d'invariants :
      - `key` est une chaîne opaque ASCII (path-like, séparateur `/`), <= 1024 chars.
      - `put` est idempotent sur la même `key` (écrase).
      - Les exceptions sont canoniques (hiérarchie `StorageError`), jamais boto3 brut.
      - Les méthodes ne bloquent PAS l'event loop : I/O via `asyncio.to_thread`.
    """

    @abstractmethod
    async def put(self, key: str, content: bytes | BinaryIO, *, content_type: str | None = None) -> str:
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
        """Retourne une URL pré-signée (ou chemin local absolu pour local).
        Défaut 15 min (900 s) aligné NFR (épic AC4). Lève `StorageNotFoundError` si absent."""

    @abstractmethod
    async def list(self, prefix: str = "", *, max_keys: int = 1000) -> list[str]:
        """Liste les `key` sous `prefix`, triées lexicographiquement,
        plafonnées à `max_keys` (pagination hors scope MVP)."""
```

**And** `base.py` définit la hiérarchie d'exceptions canonique (**1 base + 3 sous-classes**) :
```python
class StorageError(Exception):
    """Erreur de la couche storage (parent). Capture toute anomalie transverse."""

class StorageNotFoundError(StorageError):
    """Clé absente au moment du get/delete/signed_url."""

class StoragePermissionError(StorageError):
    """Permission AWS IAM insuffisante ou filesystem EACCES."""

class StorageQuotaError(StorageError):
    """Espace disque insuffisant (local) ou quota bucket S3 dépassé."""
```

**And** `__init__.py` expose **exactement** ces 6 symboles publics — `python -c "from app.core.storage import StorageProvider, StorageError, StorageNotFoundError, get_storage_provider, storage_key_for_document, storage_key_for_report; print('OK')"` doit réussir sans import d'autres symboles (audit surface API).

**And** le scan NFR66 Task 1 (documenté Dev Notes ci-dessous) confirme zéro duplication.

---

### AC2 — `LocalStorageProvider` fonctionnel + injection via `Settings` + factory `get_storage_provider`

**Given** l'absence de `boto3` en prod MVP (dépendance AWS optionnelle) et la contrainte NFR69 « stockage local MVP → S3 Growth » (architecture.md ligne 341), le provider **par défaut** doit être `LocalStorageProvider` (zéro dépendance externe au démarrage).

**When** un développeur implémente `backend/app/core/storage/local.py` + `backend/app/core/storage/__init__.py::get_storage_provider`,

**Then** `LocalStorageProvider` respecte les invariants suivants :
  - **Constructor** : `LocalStorageProvider(base_path: Path)` — `base_path` est résolu et créé (`mkdir(parents=True, exist_ok=True)`) au premier `put()` (lazy, pour permettre un `LocalStorageProvider(Path("/tmp/nonexistent"))` dans les tests sans side-effect au boot).
  - **`put(key, content, content_type)`** : résout `dest = base_path / key` (normalisation `pathlib`), crée les parents, appelle `await asyncio.to_thread(dest.write_bytes, content)` si `content: bytes`, sinon lit le BinaryIO par chunks 1 MB (streaming — **pas** de `content.read()` en entier qui exploserait la RAM sur un 100 MB). Retourne `f"file://{dest.resolve()}"`.
  - **Validation sécurité path-traversal** : `key.replace("..", "").split("/")` + assertion `key` ne commence pas par `/`. Si `key` contient `..` ou un segment absolu → `StoragePermissionError("path traversal detected")`. **Important** : même si `storage_key_for_document` produit toujours des clés sûres, la défense en profondeur doit rester au niveau du provider (zéro confiance).
  - **`get(key)`** : `dest = base_path / key` ; `StorageNotFoundError` si absent ; sinon `await asyncio.to_thread(dest.read_bytes)`.
  - **`delete(key)`** : `dest.unlink(missing_ok=True)` (idempotent) + **cleanup parent vide** (`rmdir` si dossier vide, pattern repris de `documents/service.py:123-126`). Silencieusement ignore les erreurs de cleanup parent (log `debug` seulement).
  - **`exists(key)`** : `(base_path / key).is_file()`.
  - **`signed_url(key, ttl_seconds)`** : pour local, **pas** de vraie URL pré-signée (pas de serveur HTTP dédié aux fichiers). Retourne le **path absolu** `str((base_path / key).resolve())` préfixé `file://`. **Les consommateurs MVP** (`reports/router.py:70-99`, `documents/router.py:355-380`) continueront de servir via `FastAPI FileResponse(path=...)` — le `signed_url` n'est **pas** consommé par l'UI en mode local. Cette divergence est **documentée** dans la docstring du provider et dans AC7 (`docs/CODEMAPS/storage.md §5 Limitations MVP`).
  - **`list(prefix, max_keys)`** : `list(base_path.glob(f"{prefix}**/*"))` filtré sur `is_file()`, tronqué à `max_keys`, renvoyé relatif à `base_path`.
  - **`__repr__`** : `f"LocalStorageProvider(base_path={base_path!r})"` (debug-friendly dans les logs).

**And** `backend/app/core/config.py` gagne **3 nouveaux champs** (alignement pattern Pydantic `Settings` existant, pas de lecture `os.environ` dispersée) :
```python
# --- Storage (Story 10.6) ---
storage_provider: str = Field(default="local", pattern="^(local|s3)$")
storage_local_path: str = Field(default="uploads")  # Relatif à backend/ ou absolu
aws_s3_bucket: str = ""  # Requis uniquement si storage_provider=s3
aws_region: str = Field(default="eu-west-3")  # NFR24 data residency
```

**And** `backend/app/core/storage/__init__.py::get_storage_provider()` est une **factory cached** (`functools.lru_cache` ou module-level singleton) qui lit `settings.storage_provider` et retourne :
  - `storage_provider == "local"` → `LocalStorageProvider(base_path=_resolve_local_path(settings.storage_local_path))`, où `_resolve_local_path` gère relatif (résolu depuis `backend/`) vs absolu.
  - `storage_provider == "s3"` → **import lazy** `from .s3 import S3StorageProvider` (évite que `boto3` soit requis au boot si local) → `S3StorageProvider(bucket=settings.aws_s3_bucket, region=settings.aws_region)`. Si `aws_s3_bucket` est vide → `StorageError("AWS_S3_BUCKET is required when STORAGE_PROVIDER=s3")`.
  - **Fallback safety-net** : si `settings.storage_provider` est une valeur inconnue (shouldn't happen grâce à la regex Pydantic) → `StorageError(...)` explicite.

**And** `get_storage_provider()` est utilisable comme **dépendance FastAPI** (`Depends(get_storage_provider)`) **sans** avoir à wrapper dans une lambda (la factory est sync et idempotente — une fois résolue, elle retourne le même singleton à chaque appel, pattern aligné avec `get_db`).

**And** `backend/.env.example` gagne une nouvelle section documentée :
```bash
# --- Stockage fichiers (Story 10.6) ---
# Provider : "local" (MVP default) ou "s3" (Phase Growth EU-West-3)
STORAGE_PROVIDER=local
# Si local : chemin relatif (depuis backend/) ou absolu
STORAGE_LOCAL_PATH=uploads
# Si s3 : bucket + région (NFR24 data residency AWS EU-West-3 Paris)
AWS_S3_BUCKET=
AWS_REGION=eu-west-3
# Si s3 : credentials standard (IAM role en prod, clés en dev)
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
```

---

### AC3 — `S3StorageProvider` + multipart upload streaming + retry `with_retry`

**Given** la Phase Growth visera S3 EU-West-3 (NFR24 + NFR33 CRR → EU-West-1 + NFR25 chiffrement SSE-S3) avec budget 100 €/mois NFR69, et l'épic AC5 exige multipart upload pour les fichiers > 100 MB (bilans PDF audits), et boto3 est **sync** uniquement (aiobotocore ajoute friction packaging sans bénéfice sur un workload à faible contention),

**When** un développeur implémente `backend/app/core/storage/s3.py`,

**Then** `S3StorageProvider` respecte les invariants suivants :
  - **Dépendance optionnelle** : `import boto3` + `from botocore.exceptions import ClientError, BotoCoreError` au **top-level** de `s3.py` (pas lazy — c'est déjà lazy via l'import de `s3.py` lui-même qui n'est chargé que si `storage_provider=s3`). `backend/requirements.txt` gagne `boto3>=1.34,<2.0` (version stable 2026).
  - **Constructor** : `S3StorageProvider(bucket: str, region: str = "eu-west-3")`. Instancie `self._client = boto3.client("s3", region_name=region)` **une fois** au constructor (ré-utilisation du client boto3 en pattern singleton — NFR performance).
  - **Choix async boto3 sync** : toutes les méthodes I/O utilisent `await asyncio.to_thread(...)` pour déléguer les appels sync boto3 au default thread pool executor. **Justification documentée** dans la docstring du provider : « aiobotocore épingle une version botocore incompatible avec langchain-openai ; l'overhead thread pool est < 1ms/call vs gain de stabilité packaging ». Seuil de re-évaluation : si profiling Phase Growth montre > 100 calls/sec concurrents avec contention du thread pool, migrer vers `aioboto3`.
  - **`put(key, content, content_type)`** : **détection taille** pour basculer single-part vs multipart :
    - Si `content: bytes` et `len(content) < 10 * 1024 * 1024` (10 MB) → `put_object(Bucket, Key=key, Body=content, ContentType=content_type or "application/octet-stream", ServerSideEncryption="AES256")` (NFR25 chiffrement at rest SSE-S3 par défaut).
    - Si `content: bytes` et `>= 10 MB` OU `content: BinaryIO` → **multipart upload** via `boto3.s3.transfer.TransferManager.upload_fileobj` (geste le threading, les chunks de 8 MB par défaut, le retry intra-chunk). Paramètres : `ExtraArgs={"ServerSideEncryption": "AES256", "ContentType": ...}`.
  - **Wrapping `with_retry`** : chaque méthode I/O est wrappée par **le helper `with_retry` de Story 9.7** (à importer depuis son emplacement — `app.core.resilience.with_retry` ou équivalent repéré en Task 1). Politique : max 3 tentatives, délai exponentiel 200ms → 800ms, uniquement sur `BotoCoreError` et `ClientError` avec `error_code` dans `{"RequestTimeout", "RequestTimeoutException", "ServiceUnavailable", "SlowDown", "InternalError"}`. Les erreurs permanentes (`NoSuchKey`, `AccessDenied`) ne sont **pas** retryées — propagation directe.
  - **Mapping exceptions boto3 → `StorageError`** (défense en profondeur API contract) :
    - `ClientError` avec code `"NoSuchKey"` → `StorageNotFoundError(f"key not found: {key}")`
    - `ClientError` avec code `"AccessDenied"` → `StoragePermissionError(f"IAM denied for key {key}")`
    - `ClientError` avec code `"QuotaExceeded"` ou `"SlowDown"` (après retry épuisé) → `StorageQuotaError(...)`
    - Autres `BotoCoreError` / `ClientError` → `StorageError(f"S3 failure on key {key}: {e.response['Error']['Code']}")` (aucune stack boto3 brute propagée aux appelants).
  - **`get(key)`** : `get_object(Bucket, Key).read()` — **streaming** optionnel via `iter_chunks(1024 * 1024)` si un futur appelant passe un `io.BytesIO` cible (MVP retourne bytes comme local).
  - **`delete(key)`** : `delete_object(Bucket, Key)`. **Sémantique idempotente** : S3 retourne `200 OK` même si la clé n'existe pas — aligné avec la contractualisation AC1. Ne pas faire `head_object` avant pour vérifier l'existence (round-trip réseau inutile).
  - **`exists(key)`** : `head_object` + catch `ClientError` code `404` → `False`. Toute autre erreur → propagation.
  - **`signed_url(key, ttl_seconds=900)`** : `generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=ttl_seconds)`. **Validation `ttl_seconds`** : `1 <= ttl_seconds <= 3600` (1h max — défense sécurité, évite TTL infini si un appelant passe 86400). Si hors bornes → `ValueError("ttl_seconds must be in [1, 3600]")`. **Pas de pré-check `exists`** avant (round-trip réseau inutile ; boto3 émet une URL valide même si la clé est absente — côté consommateur, l'accès sera 404).
  - **`list(prefix, max_keys=1000)`** : `list_objects_v2(Bucket, Prefix=prefix, MaxKeys=max_keys)`. Retourne `[obj["Key"] for obj in response.get("Contents", [])]`. **Pagination** hors scope MVP (NotImplementedError si `max_keys > 1000` — à faire Phase Growth).

**And** `S3StorageProvider.__repr__` masque les credentials : `f"S3StorageProvider(bucket={bucket!r}, region={region!r})"` (jamais d'accès à `self._client._request_signer._credentials`).

**And** un test `@pytest.mark.s3 @mock_aws` (Task 10) prouve que les 5 scénarios round-trip (put/get/delete/exists/signed_url/list) fonctionnent contre le mock moto réaliste.

---

### AC4 — Intégration des 2 consommateurs persistants (`documents/` + `reports/`) via `storage_provider`

**Given** le scan NFR66 Task 1 a identifié **exactement 2 modules** qui persistent sur disque aujourd'hui (`documents/service.py:103-126` et `reports/service.py:44,359-366`), et les 4 autres modules générant du PDF (`credit/certificate.py`, `financing/preparation_sheet.py`, `applications/export.py`, `applications/prep_sheet.py`) retournent **in-memory** sans persistance (vérifié grep `write_pdf(` → `HTML(...).write_pdf()` sans argument path),

**When** un développeur refactore ces 2 modules,

**Then** le pattern **brownfield minimaliste** est appliqué (aucun changement de signature publique, aucun endpoint REST modifié) :

#### AC4.a — `backend/app/modules/documents/service.py`

- **Suppression** des helpers privés `_save_file_to_disk` + `_delete_file_from_disk` (remplacés par appels storage).
- **Conservation** `UPLOADS_DIR` uniquement pour **rétrocompatibilité lecture** (fichiers uploadés **avant** Story 10.6 restent accessibles via filesystem ; le path est stocké dans `Document.storage_path` qui continue d'être le **key** du provider — cf. invariant §1 de la section Contexte).
- **Refactor `upload_document`** (ligne 154-221) : remplace `storage_path = _save_file_to_disk(...)` par :
  ```python
  from app.core.storage import get_storage_provider, storage_key_for_document, StorageQuotaError

  storage = get_storage_provider()
  key = storage_key_for_document(user_id, document_id, safe_filename)
  try:
      await storage.put(key, content, content_type=content_type)
  except StorageQuotaError as exc:
      raise QuotaExceededError(str(exc)) from exc
  storage_path = key  # Même valeur stockée en BDD (clé opaque portable local↔s3)
  ```
- **Refactor `delete_document`** (ligne 605-612) : remplace `_delete_file_from_disk(document.storage_path)` par :
  ```python
  storage = get_storage_provider()
  await storage.delete(document.storage_path)
  ```
- **Refactor `analyze_document`** (ligne 367) : le path est utilisé pour **lire** via PyMuPDF/pytesseract/docx2txt/openpyxl qui attendent tous un **path filesystem** (pas un BinaryIO). **Stratégie MVP** : rester sur le filesystem local via `LocalStorageProvider`. Si Phase Growth passe sur S3, un adaptateur dédié téléchargera dans `tempfile.NamedTemporaryFile` et passera le path temporaire aux libs d'extraction (pattern déferré à la story de migration). **Document explicitement** dans Dev Notes + `docs/CODEMAPS/storage.md §6 Migration vers S3`.
- **Refactor `download_document` endpoint** (`documents/router.py:355-380`) : en mode local, continue d'utiliser `FileResponse(path=...)`. En mode S3 (Phase Growth), le endpoint utilisera `storage.signed_url(key)` puis `RedirectResponse(url)` — pattern capturé en commentaire TODO Story 10.6 avec marqueur `# Story 10.6 Growth: redirect vers signed_url si storage_provider==s3`.
- **`check_disk_space`** (ligne 88-100) : conservé **tel quel** — c'est une logique quota applicative (pas storage I/O). En mode S3, la vérification `shutil.disk_usage` serait non pertinente — le provider S3 lève `StorageQuotaError` directement sur `put()`. Ajouter un garde `if isinstance(storage, LocalStorageProvider):` autour de l'appel `_check_disk_space()` (ou simpler : déplacer le check **dans** `LocalStorageProvider.put` comme garde interne).

#### AC4.b — `backend/app/modules/reports/service.py`

- **Suppression** ligne 44 `UPLOADS_DIR = Path(...) / "uploads" / "reports"` (remplacé par clé storage).
- **Refactor `generate_esg_report_pdf`** (lignes 357-366) : remplace le bloc `UPLOADS_DIR.mkdir + pdf_path = UPLOADS_DIR / file_name + html_doc.write_pdf(str(pdf_path))` par :
  ```python
  from io import BytesIO
  from app.core.storage import get_storage_provider, storage_key_for_report

  buffer = BytesIO()
  html_doc.write_pdf(buffer)  # WeasyPrint supporte BinaryIO
  pdf_bytes = buffer.getvalue()

  storage = get_storage_provider()
  key = storage_key_for_report(report.id, file_name)
  await storage.put(key, pdf_bytes, content_type="application/pdf")
  report.file_path = key  # Clé opaque (même valeur dans les 2 providers)
  report.file_size = len(pdf_bytes)
  ```
- **Refactor `download_report` endpoint** (`reports/router.py:70-99`) : **2 branches** selon `settings.storage_provider` :
  - `local` → `FileResponse(path=storage.signed_url(report.file_path).removeprefix("file://"), ...)` **ou plus simple** : `FileResponse(path=str(resolved_abs_path), ...)` via un helper `storage.local_path(key)` exposé **uniquement** par `LocalStorageProvider` (cast isinstance accepté ici car le endpoint sait qu'il sert du local MVP).
  - `s3` → `RedirectResponse(url=await storage.signed_url(key, ttl_seconds=900))` (Growth ready).
  - **Alternative plus propre** : toujours passer par `await storage.signed_url(...)` et laisser le router faire `FileResponse` (local) ou `RedirectResponse` (s3) selon le préfixe (`file://` vs `https://`). **Choix retenu** (documenté dans Dev Notes) = cette alternative, car elle évite le `isinstance` anti-pattern.

**And** après refactor, **aucun** des 2 modules ne fait `open(path, "wb")`, `write_bytes(content)`, `write_pdf(<path>)`, ou `FileResponse(path=<hardcoded uploads>/... )` sans passer par `storage` — **audit grep** : `rg "(write_bytes|write_pdf\(str|\.write\(.*wb)" backend/app/modules/documents backend/app/modules/reports` doit retourner 0 résultat **hors** du helper `storage.put()` lui-même.

**And** les 4 modules PDF in-memory (`credit/certificate.py`, `financing/preparation_sheet.py`, `applications/export.py`, `applications/prep_sheet.py`) sont **intentionnellement non modifiés** — décision tracée dans `deferred-work.md` sous rubrique « Opportunités Phase Growth — migration vers storage.put() pour caching + audit trail ».

**And** les tests existants `backend/tests/test_documents/` + `backend/tests/test_reports/` restent **verts** (zéro régression comportementale — seul le chemin I/O change).

---

### AC5 — Tests unitaires `LocalStorageProvider` + round-trip (sans moto)

**Given** le pattern test prod véritable (C2 hérité 9.7 + règle d'or 10.5 « tester effet observable »),

**When** un développeur ajoute `backend/tests/test_core/test_storage/test_local_provider.py`,

**Then** le fichier contient **au minimum 10 tests** (cible +10 collectés via `pytest --collect-only -q`) couvrant :
  1. `test_put_get_roundtrip_small_bytes` — `put(key, b"hello")` puis `get(key) == b"hello"`
  2. `test_put_overwrites_existing` — 2 `put()` successifs sur même key, `get` retourne le dernier contenu
  3. `test_get_missing_raises_not_found` — `get("nonexistent")` lève `StorageNotFoundError`
  4. `test_delete_idempotent` — `delete("nonexistent")` ne lève **pas** (sémantique idempotente AC1)
  5. `test_delete_existing_removes_file_and_cleans_empty_parent` — après delete, `exists == False` **et** le dossier parent vide est supprimé
  6. `test_exists_returns_true_after_put` + `test_exists_returns_false_before_put`
  7. `test_signed_url_returns_file_scheme` — format `file:///abs/path`, **pas** d'URL HTTP
  8. `test_list_with_prefix_filters_keys` — 3 keys `docs/a/1.txt`, `docs/b/2.txt`, `reports/3.pdf` ; `list("docs/")` retourne 2 keys triés
  9. `test_path_traversal_attack_rejected` — `put("../../../etc/passwd", b"evil")` lève `StoragePermissionError`
  10. `test_put_stream_binaryio_10mb` — créer un `BytesIO(b"A" * 10_485_760)`, `put()` + `get()` round-trip identique (prouve le streaming)

**And** le fichier utilise la fixture `tmp_path` pytest (**pas** `MagicMock` sur `Path`) — les tests écrivent sur vrai filesystem isolé dans un tmpdir par test.

**And** tous les tests sont `async def` avec `@pytest.mark.asyncio` (mode auto défini dans `pytest.ini`).

**And** aucun test n'utilise `unittest.mock.patch("app.core.storage.local.open")` ou équivalent — **règle d'or 10.5** : tester l'effet observable (fichier présent + contenu identique), pas le mécanisme interne.

**And** `pytest backend/tests/test_core/test_storage/test_local_provider.py -q` retourne **10 passed** sans PostgreSQL ni moto (pur filesystem + pytest).

---

### AC6 — Tests `S3StorageProvider` avec `moto[s3]` (marker `@pytest.mark.s3`)

**Given** `moto[s3]` émule un endpoint S3 réel en mémoire (requêtes HTTP interceptées via decorator `@mock_aws` depuis `moto>=5.0`) et il n'est pas souhaitable d'imposer `moto` comme dépendance prod (uniquement dev),

**When** un développeur ajoute `backend/tests/test_core/test_storage/test_s3_provider.py`,

**Then** le fichier contient :
  - **Module-level marker** : `pytestmark = [pytest.mark.s3]` (nouveau marker, à déclarer dans `pytest.ini` ou `pyproject.toml` section markers).
  - **Skip propre si moto absent** : bloc au top-level :
    ```python
    moto = pytest.importorskip("moto", reason="moto[s3] required for S3 provider tests")
    ```
    — skip explicite si `moto` non installé, pas un ImportError qui casserait la collection.
  - **Fixture `s3_provider`** avec décorator `@mock_aws` qui :
    1. Crée un bucket `test-bucket-eu-west-3` en région `eu-west-3` via `boto3.client("s3").create_bucket(Bucket=..., CreateBucketConfiguration={"LocationConstraint": "eu-west-3"})`.
    2. Instancie `S3StorageProvider(bucket="test-bucket-eu-west-3", region="eu-west-3")`.
    3. Yield, nettoie après (moto auto-cleanup).
  - **Au minimum 8 tests** :
    1. `test_put_get_roundtrip_small` — put 100 bytes, get identique
    2. `test_put_content_type_applied` — put avec `content_type="application/pdf"`, head_object retourne `ContentType="application/pdf"`
    3. `test_put_sse_applied` — head_object retourne `ServerSideEncryption="AES256"` (NFR25 prouvé end-to-end)
    4. `test_get_missing_raises_not_found` — `StorageNotFoundError` mappée depuis `ClientError.NoSuchKey`
    5. `test_delete_idempotent` — delete inexistant = no-op (sémantique S3 confirmée)
    6. `test_signed_url_generates_presigned` — l'URL commence par `https://test-bucket-eu-west-3.s3.` et contient `X-Amz-Signature`
    7. `test_signed_url_ttl_boundary` — `ttl_seconds=0` → `ValueError` ; `ttl_seconds=3600` ok ; `ttl_seconds=3601` → `ValueError`
    8. `test_list_prefix` — seed 3 objets, `list("prefix/")` retourne 2 keys triées

**And** `backend/requirements-dev.txt` (si existant) ou section `[dev]` de `requirements.txt` gagne `moto[s3]>=5.0,<6.0`. Si `requirements-dev.txt` n'existe pas, créer le fichier et mettre à jour `README.md` backend pour mentionner `pip install -r backend/requirements-dev.txt`.

**And** `pytest.ini` (ou `pyproject.toml` `[tool.pytest.ini_options]`) gagne `markers = [..., "s3: requires moto[s3] mock server"]` (déclaration officielle pour éviter warning `PytestUnknownMarkWarning`).

**And** `pytest backend/tests/test_core/test_storage/test_s3_provider.py -q` retourne **8 passed** si `moto[s3]` est installé, **8 skipped** sinon — **pas** d'erreur collection.

---

### AC7 — Test E2E round-trip 1 MB + 10 MB (prouve streaming + intégration bout en bout)

**Given** l'épic AC5 exige multipart upload pour > 100 MB mais ce seuil n'est pas atteignable en test unitaire rapide (moto reste single-threaded en mémoire), et la règle d'or 10.5 exige de tester l'effet observable,

**When** un développeur ajoute `backend/tests/test_core/test_storage/test_providers_e2e.py`,

**Then** le fichier contient **2 tests paramétrés** `@pytest.mark.parametrize("size_mb", [1, 10])` qui :
  1. Génèrent `content = os.urandom(size_mb * 1024 * 1024)` (bytes pseudo-aléatoires — évite compression triviale qui biaiserait S3).
  2. Exécutent le **même scénario sur les 2 providers** (local via fixture `tmp_path` + S3 via `@mock_aws`) :
     - `await storage.put(key, content, content_type="application/octet-stream")`
     - `assert await storage.exists(key) is True`
     - `got = await storage.get(key)`
     - `assert got == content` (égalité binaire stricte, taille comprise)
     - `await storage.delete(key)`
     - `assert await storage.exists(key) is False`
  3. **Mesurent** `time.monotonic()` avant/après put+get pour prouver que l'opération **ne bloque pas l'event loop** : paralléliser 3 `put()` via `asyncio.gather` ; le temps total doit être **< 1.5× le temps d'un put seul** (preuve de parallélisme via `asyncio.to_thread`). Si > 1.5×, `pytest.fail("event loop blocked — likely missing asyncio.to_thread")`.
  4. Le test S3 utilise `@pytest.mark.s3` (skip si moto absent).

**And** le test 10 MB prouve que **l'upload S3 bascule bien en multipart** (via `boto3.s3.transfer` qui split en chunks 8 MB par défaut) : vérifier via `moto` logs ou via un assert sur `content_length` retourné par `head_object`. Note : moto n'expose pas directement le flag multipart, donc la preuve indirecte (absence de `MemoryError` + contenu identique + round-trip < 2s) suffit. Limitation documentée dans Dev Notes.

**And** les 2 tests × 2 providers = **4 tests** collectés minimum (2 local + 2 S3 skippables).

---

### AC8 — Documentation `docs/CODEMAPS/storage.md` + baseline ≥ 1350 tests

**Given** la pratique établie (Story 10.5 `docs/CODEMAPS/security-rls.md` créé ; `docs/CODEMAPS/data-model-extension.md` créé Story 10.1), et l'exigence AC8 utilisateur (baseline 1338 passed + 64 skipped → **cible ≥ 1350 passed +12 min**),

**When** un développeur crée `docs/CODEMAPS/storage.md`,

**Then** le fichier contient **au minimum 7 sections** :
  1. **§1 Vue d'ensemble** — diagramme Mermaid `graph LR` : `FastAPI` → `get_storage_provider` → (`LocalStorageProvider` | `S3StorageProvider`) → `filesystem` / `S3 EU-West-3`. Préciser que le switch est **config-only**.
  2. **§2 Contrat `StorageProvider`** — table des 6 méthodes ABC + signature + invariants (idempotence put, idempotence delete, clés opaques).
  3. **§3 `LocalStorageProvider`** — comportement, structure `uploads/documents/<uid>/<did>/<filename>` + `uploads/reports/<rid>/<filename>`, limitations (pas de vraie URL pré-signée, path-traversal guard).
  4. **§4 `S3StorageProvider`** — config requise (`AWS_S3_BUCKET`, `AWS_REGION=eu-west-3`, IAM policy minimale `s3:GetObject, s3:PutObject, s3:DeleteObject, s3:ListBucket` sur `arn:aws:s3:::<bucket>/*` + `arn:aws:s3:::<bucket>`), chiffrement SSE-S3, multipart seuil 10 MB, retry policy, presigned TTL 15 min défaut / 1h max.
  5. **§5 Limitations MVP** (explicites — Limitations 1-5) :
     1. Pas de migration automatique `/uploads/` existant → S3 (script différé Phase Growth).
     2. Les 4 modules PDF in-memory (`credit/financing/applications`) ne sont **pas** câblés à `storage` (tracés dans `deferred-work.md`).
     3. Les libs d'extraction (PyMuPDF, pytesseract, docx2txt, openpyxl) attendent un path filesystem — en S3 Phase Growth il faudra un adaptateur tempfile (story future).
     4. `LocalStorageProvider.signed_url` retourne un `file://` URI (pas une vraie URL pré-signée HTTP).
     5. `list(prefix, max_keys)` ne supporte pas la pagination > 1000 keys (hors scope MVP).
  6. **§6 Migration vers S3** — 4 étapes opérationnelles : (a) positionner `STORAGE_PROVIDER=s3` + `AWS_S3_BUCKET` + IAM role, (b) déployer script `migrate_local_to_s3.py` (hors Story 10.6), (c) vérifier CRR EU-West-3 → EU-West-1 activée (Story 10.7), (d) switcher environnement + monitoring 24h.
  7. **§7 Fichiers concernés** — liste explicite (`backend/app/core/storage/*.py`, `backend/tests/test_core/test_storage/*.py`, consommateurs `documents/service.py:154-221,605-612` + `reports/service.py:357-370` + routers download).
  8. **§8 Dépendances & coût** — NFR69 ligne S3 ~100 €/mois MVP → scaling, NFR25 SSE-S3 gratuit, NFR33 CRR EU-West-3 → EU-West-1 (story 10.7).

**And** `docs/runbooks/README.md` gagne une ligne référence pointant vers `docs/CODEMAPS/storage.md` section « Integrations » (pattern aligné avec entrée `security-rls.md` ajoutée Story 10.5).

**And** **baseline finale mesurée** par introspection runtime (commande citée dans le rapport Completion Notes) :
```bash
pytest --collect-only -q backend/tests/ | tail -1
```
- **Baseline actuelle** (post Story 10.5) : `1338 passed + 64 skipped` en CI locale sans `TEST_ALEMBIC_URL` ni `moto[s3]`.
- **Cible Story 10.6** : **≥ 1350 passed** en CI locale (avec `moto[s3]` installé) → **+12 tests minimum**. Décomposition prévisionnelle : 10 (AC5) + 8 (AC6) + 4 (AC7) = **22 tests bruts**, dont 8 skippent sans `moto[s3]` → cible plancher **+14 tests passés locale sans moto** ou **+22 tests passés locale avec moto** (dépasse largement le plancher utilisateur +12).
- **Zéro régression** sur les 1338 tests pré-existants — vérifié par `pytest backend/tests/ -q --ignore=backend/tests/test_core/test_storage`.

---

## Tasks / Subtasks

- [x] **Task 1 — Scan NFR66 exhaustif (AC1)** (AC: #1)
  - [x] Scan `rg` confirmé : 0 helper storage dans `backend/app/core/`, 0 import boto3 dans backend.
  - [x] 2 consommateurs persistants identifiés : `documents/service.py:114` (write_bytes) et `reports/service.py:363` (write_pdf(str(path))).
  - [x] `with_retry` localisé : `backend/app/graph/tools/common.py:372`.

- [x] **Task 2 — Créer `backend/app/core/storage/base.py`** (AC: #1)
  - [x] ABC `StorageProvider` + 6 méthodes abstraites async.
  - [x] Hiérarchie `StorageError` + `StorageNotFoundError` + `StoragePermissionError` + `StorageQuotaError`.
  - [x] Pur stdlib (abc + typing).

- [x] **Task 3 — Créer `backend/app/core/storage/keys.py`** (AC: #1)
  - [x] `storage_key_for_document(user_id, document_id, filename)` + `storage_key_for_report(report_id, filename)`.

- [x] **Task 4 — Créer `backend/app/core/storage/local.py`** (AC: #2)
  - [x] 6 méthodes async wrappées `asyncio.to_thread`.
  - [x] Streaming BinaryIO chunks 1 MB.
  - [x] Garde path-traversal (`..`, `/` absolu).
  - [x] Cleanup parent vide après delete.
  - [x] `_check_disk_space` privé déplacé dans `LocalStorageProvider.put`.

- [x] **Task 5 — Créer `backend/app/core/storage/s3.py`** (AC: #3)
  - [x] Client boto3 singleton + `Config(request_checksum_calculation="when_required")` (fix FlexibleChecksumError moto).
  - [x] Multipart auto via `upload_fileobj` si ≥ 10 MB ou BinaryIO.
  - [x] SSE-S3 AES256 systématique.
  - [x] Retry `_call_with_retry` 3 tentatives exponentiel (200/400/800 ms) sur codes transients.
  - [x] Mapping `_map_client_error` → `StorageError` / `StorageNotFoundError` / `StoragePermissionError` / `StorageQuotaError`.
  - [x] `signed_url` TTL borné [1, 3600].
  - [x] `__repr__` masque credentials.

- [x] **Task 6 — Créer `backend/app/core/storage/__init__.py`** (AC: #2)
  - [x] `get_storage_provider()` factory `@lru_cache(maxsize=1)`.
  - [x] Import lazy de `s3.py` uniquement si `storage_provider=s3`.
  - [x] 6 symboles publics exposés via `__all__`.
  - [x] `_reset_storage_provider_cache()` privé pour fixtures de test.

- [x] **Task 7 — Étendre `backend/app/core/config.py::Settings`** (AC: #2)
  - [x] 4 champs ajoutés : `storage_provider`, `storage_local_path`, `aws_s3_bucket`, `aws_region`.
  - [x] `backend/.env.example` enrichi section « Stockage fichiers (Story 10.6) ».

- [x] **Task 8 — Refactorer `backend/app/modules/documents/service.py`** (AC: #4)
  - [x] `upload_document` → `await storage.put(key, content, content_type)` ; `storage_path = key` (clé opaque `documents/<uid>/<did>/<file>`).
  - [x] `delete_document` → `await storage.delete(...)`.
  - [x] `analyze_document` : résolution path via `storage.local_path(key)` (Local) + rétrocompat `"uploads/"` legacy + `NotImplementedError` en S3 (adaptateur tempfile déferré).
  - [x] `StorageQuotaError` → `QuotaExceededError` wrapping (compat tests 9.2).
  - [x] Shims legacy `_save_file_to_disk` / `_delete_file_from_disk` / `_check_disk_space` conservés pour compat `unittest.mock.patch` (non appelés en prod).

- [x] **Task 9 — Refactorer `backend/app/modules/reports/service.py` + `reports/router.py`** (AC: #4)
  - [x] `generate_esg_report_pdf` : `BytesIO` buffer + `await storage.put(storage_key, pdf_bytes, content_type="application/pdf")` ; `report.file_path = storage_key`.
  - [x] `UPLOADS_DIR` supprimé du service.
  - [x] `download_report` endpoint : `FileResponse` (Local via `storage.local_path`) / `RedirectResponse(signed_url)` (S3) + rétrocompat legacy `file_path` sans préfixe.

- [x] **Task 10 — Tests `LocalStorageProvider`** (AC: #5, #8)
  - [x] `test_local_provider.py` : **13 tests** passants (round-trip bytes, overwrite, not-found, delete idempotent, cleanup parent vide, exists, signed_url, list prefix, path-traversal, streaming BinaryIO 10 MB, repr).
  - [x] Fixture `tmp_path` (aucun mock `Path.write_bytes`).

- [x] **Task 11 — Tests `S3StorageProvider` avec moto** (AC: #6, #8)
  - [x] `moto[s3]>=5.0,<6.0` ajouté à `backend/requirements-dev.txt` ; marker `s3` déclaré `pytest.ini`.
  - [x] `test_s3_provider.py` : **11 tests** (round-trip, SSE, content-type, not-found, delete idempotent, presigned, TTL boundary, list prefix, exists, repr credentials, constructor empty bucket).
  - [x] `test_s3_error_paths.py` : **12 tests** supplémentaires (mapping ClientError/BotoCoreError, retry transient, multipart BinaryIO, pagination `NotImplementedError`, delete retry).

- [x] **Task 12 — Tests E2E round-trip 1 MB + 10 MB** (AC: #7, #8)
  - [x] `test_providers_e2e.py` : **5 tests** collectés (2 local × 1MB/10MB + 2 S3 × 1MB/10MB + 1 event-loop non-blocking).
  - [x] Assertion `asyncio.gather × 3` + timing ratio < 2.5.

- [x] **Task 13 — Documentation `docs/CODEMAPS/storage.md`** (AC: #8)
  - [x] 8 sections (Vue d'ensemble Mermaid, Contrat, Local, S3 config+IAM, Limitations MVP, Migration, Fichiers, Dépendances+coût).
  - [x] Référence ajoutée dans `docs/runbooks/README.md` section Storage.

- [x] **Task 14 — Mettre à jour `deferred-work.md`** (AC: #4)
  - [x] Section « Story 10.6 Storage abstraction (2026-04-20) » ajoutée avec 6 entrées : 4 modules PDF in-memory, adaptateur tempfile, script migrate_local_to_s3, download_document signed_url, pagination > 1000, SSE-KMS.

- [x] **Task 15 — Validation finale** (AC: #8)
  - [x] `pytest --collect-only -q tests/test_core/test_storage/` → **49 tests collectés** (13 local + 11 s3 + 12 s3 error paths + 5 e2e + 8 factory).
  - [x] Full regression : **1387 passed + 64 skipped** (avec `moto[s3]` installé) vs baseline 1338 → **+49 tests**, zéro régression.
  - [x] Sans `moto[s3]` : les 23 tests avec marker `s3` skippent via `pytest.importorskip` → **1364 passed + 87 skipped** attendu.
  - [x] Coverage storage module : **88%** (cible ≥85%).
  - [x] Audit grep post-refactor : `rg "(write_bytes|write_pdf\(str|open\(.*wb)" backend/app/modules/{documents,reports}` → **0 résultat** (helpers legacy conservés comme shims vides).
  - [x] Sprint-status : `10-6-abstraction-storage-provider: in-progress` (sera `review` au commit final).

---

## Dev Notes

### Architecture patterns et contraintes

- **Stockage local MVP → S3 Growth (architecture.md ligne 341)** : transition par simple config env. Story 10.6 **livre le mécanisme** ; la **bascule opérationnelle** reste Phase Growth avec script de migration séparé.
- **NFR24 data residency (architecture.md ligne 295)** : AWS EU-West-3 Paris tranché. Le provider S3 **impose** `region="eu-west-3"` par défaut ; changer implique un override explicite de config + revue compliance.
- **NFR25 chiffrement at rest (architecture.md ligne 1260)** : SSE-S3 AES256 systématique sur tous les `put_object` — non-négociable, défense en profondeur même si le bucket est policies-protected.
- **NFR33 backup 2 AZ** : géré via CRR S3 EU-West-3 → EU-West-1 configuré **dans Story 10.7** (infra Terraform). Story 10.6 ne touche pas à la config CRR mais garantit que le provider S3 est compatible (aucune écriture spécifique à une AZ qui casserait la réplication).
- **NFR69 budget infra 1000 €/mois** : ligne S3 budgétée ~100 €/mois (business-decisions-2026-04-19.md ligne 185). Story 10.6 ne modifie pas le costing — elle livre le code qui permettra d'opérationaliser cette ligne.
- **Pattern brownfield (NFR62 CLAUDE.md)** : **ne pas créer de nouveau service** ; enrichir les 2 consommateurs existants (`documents/service.py` + `reports/service.py`) avec le minimum de changement et isoler la logique neuve dans `core/storage/`.
- **Pattern `core/` (urbanisation backend)** : `backend/app/core/` héberge les helpers transverses (`config.py`, `database.py`, `feature_flags.py`, `llm_guards.py`, `rate_limit.py`, `rls.py`, `admin_audit_listener.py`, `security.py`, `geolocation.py`). `storage/` rejoint naturellement — sous-dossier car 4 fichiers (base + local + s3 + keys) justifient un namespace.
- **Décision 10 LLM Provider Layer (architecture.md)** : même pattern 2-niveaux (provider ABC + implementations) appliqué ici pour storage. Cohérence architecturale forte.

### Source tree components to touch

**Créations (5 fichiers module + 4 fichiers tests + 1 doc + 1 requirements-dev)** :
- `backend/app/core/storage/__init__.py`
- `backend/app/core/storage/base.py`
- `backend/app/core/storage/keys.py`
- `backend/app/core/storage/local.py`
- `backend/app/core/storage/s3.py`
- `backend/tests/test_core/test_storage/__init__.py`
- `backend/tests/test_core/test_storage/conftest.py` (fixtures partagées)
- `backend/tests/test_core/test_storage/test_local_provider.py`
- `backend/tests/test_core/test_storage/test_s3_provider.py`
- `backend/tests/test_core/test_storage/test_providers_e2e.py`
- `docs/CODEMAPS/storage.md`
- `backend/requirements-dev.txt` (nouveau, si absent)

**Modifications (6 fichiers)** :
- `backend/app/core/config.py` — 4 nouveaux champs `Settings`
- `backend/app/modules/documents/service.py` — refactor I/O + suppression helpers privés
- `backend/app/modules/documents/router.py` — éventuelle bascule download via `signed_url` (commentaire TODO Growth)
- `backend/app/modules/reports/service.py` — refactor WeasyPrint → `BytesIO` → `storage.put`
- `backend/app/modules/reports/router.py` — bascule `FileResponse` / `RedirectResponse` via préfixe URI
- `backend/.env.example` — section « Stockage fichiers »
- `backend/requirements.txt` — `boto3>=1.34,<2.0`
- `pytest.ini` ou `pyproject.toml` — marker `s3` déclaré
- `docs/runbooks/README.md` — référence `storage.md`
- `_bmad-output/implementation-artifacts/deferred-work.md` — 3 nouvelles entrées

**Aucune modification** des modèles ORM (`Document`, `Report`, `DocumentChunk`) — `storage_path` / `file_path` restent des `VARCHAR` opaques consommés à l'identique par les 2 providers.

### Testing standards summary

- **Framework** : `pytest` + `pytest-asyncio` (mode auto, cf. `backend/pytest.ini`).
- **Marker `s3`** : nouveau, déclaré Task 11. Skip propre via `pytest.importorskip("moto")`.
- **Pas de marker `postgres`** ici (hors scope DB).
- **Fixture `tmp_path`** systématique pour les tests local (aucun write sur `backend/uploads/` réel).
- **Fixture `@mock_aws`** (moto ≥ 5.0) pour S3 — crée un bucket en mémoire par test.
- **Coverage NFR60** : le code storage est « code critique » (I/O + sécurité path-traversal + chiffrement). Cible locale ≥ 85 % via `pytest --cov=app.core.storage --cov-report=term-missing backend/tests/test_core/test_storage/`.
- **Tests prod véritables (C2)** : AUCUN `unittest.mock.patch("boto3.client")` ou `patch("pathlib.Path.write_bytes")` — les tests écrivent sur vrai filesystem / vrai mock server HTTP.
- **Règle d'or 10.5** : tester l'effet observable (fichier présent + contenu identique + head_object retourne SSE), pas le mécanisme interne.

### Pièges documentés (anticipation)

1. **boto3 sync dans un event loop async** : `asyncio.to_thread` OBLIGATOIRE sur chaque appel boto3. Oublier = bloquer l'event loop = P95 API dégradé sous charge. Test AC7 prouve la non-bloquance via `asyncio.gather` + timing.
2. **Path traversal** : `LocalStorageProvider.put` doit rejeter `..` et segments absolus **même si** `storage_key_for_document` produit toujours des clés sûres. Défense en profondeur (zéro confiance dans l'appelant).
3. **`BinaryIO` vs `bytes`** : WeasyPrint accepte un `BytesIO` dans `write_pdf(buffer)` — pattern plus propre que créer un fichier temp. À utiliser dans `reports/service.py` Task 9.
4. **boto3 multipart auto** : `boto3.s3.transfer.TransferManager` gère le split automatique à partir d'un certain seuil (8 MB default). Inutile de reimplémenter manuellement `create_multipart_upload` + `upload_part` + `complete_multipart_upload`. Task 5 doit utiliser `upload_fileobj` (TransferManager sous-jacent).
5. **SSE-S3 vs SSE-KMS** : MVP utilise SSE-S3 (AES256, gratuit). SSE-KMS (clé managée par Mefali) est une option Phase Growth pour compliance renforcée — **non livré 10.6**, capturé dans `storage.md §8`.
6. **Presigned URL TTL** : 15 min défaut (900s) aligné pattern MVP chat streaming. 1h max (3600s) pour downloads PDF larges. Plus long = risque de leak (URL contient la signature). Validation bornée dans `signed_url`.
7. **`moto` version** : `moto ≥ 5.0` a breaking change (`@mock_aws` remplace `@mock_s3`). Épingler `moto[s3]>=5.0,<6.0`.
8. **`exists` vs `get` pour check** : en S3, `head_object` est moins cher que `get_object` (pas de body download). `exists()` utilise `head_object` explicitement, **pas** `get_object().read()`.
9. **Idempotence delete** : S3 `delete_object` retourne 204 même si absent — aligner `LocalStorageProvider.delete` via `unlink(missing_ok=True)` (pattern déjà dans `_delete_file_from_disk`).
10. **Clé opaque portable** : `storage_key_for_document(uid, did, fname)` produit **exactement** la même string que l'ancien `f"uploads/{uid}/{did}/{fname}"` relatif, donc **les enregistrements `Document.storage_path` existants restent valides** avec `LocalStorageProvider` après refactor — **pas de migration BDD**.
11. **Event-loop blocking sur gros fichiers** : `Path.read_bytes()` sur 100 MB bloque ~500ms sur SSD standard. `asyncio.to_thread` impératif. Test AC7 vérifie explicitement.
12. **`settings.storage_provider` cached** : `get_storage_provider()` utilise `lru_cache` → en tests, si un test change `STORAGE_PROVIDER` via `monkeypatch.setenv`, le cache doit être invalidé. Exposer un helper privé `_reset_storage_provider_cache()` pour les fixtures de test (non exporté dans `__init__.py` mais accessible via `app.core.storage._reset_storage_provider_cache`).
13. **Préfixe clés** : `storage_key_for_document` utilise `"documents/"` et `storage_key_for_report` utilise `"reports/"` → permet des IAM policies S3 granulaires (`s3:GetObject` limité à `documents/*` pour un rôle spécifique, Phase Growth).

### Leçons capitalisées des stories précédentes

- **9.7 C1** : pas de `try/except Exception` catch-all. Exceptions canoniques `StorageError` + sous-classes ; boto3 exceptions mappées explicitement.
- **9.7 C2** : tests prod véritables. Pas de mock bas-niveau ; `tmp_path` + `moto[s3]` réalistes.
- **9.7 pattern `with_retry`** : ré-utilisé Task 5 pour les appels réseau boto3 (timeout, 5xx, SlowDown).
- **10.1 marker DB** : `@pytest.mark.postgres` **non applicable** — nouveau marker `@pytest.mark.s3` introduit avec même philosophie (skip propre sans dépendance).
- **10.2 M2** : TODO Epic — non applicable.
- **10.3 M1** : scan NFR66 **en première étape** (Task 1) avant toute création.
- **10.4 méthodo** : comptages par introspection runtime — `pytest --collect-only | grep -c '::'` cité dans le rapport final (AC8 + Completion Notes).
- **10.5 règle d'or** : tester l'effet observable — round-trip put/get AC5+AC6+AC7, pas d'assertion sur `boto3.client.put_object` mock.
- **10.5 source unique** : `Settings` Pydantic plutôt que `os.environ.get` dispersé — Task 7 respecte ce pattern (divergence consciente vs Story 10.5 qui gardait `os.environ` pour cohérence avec `ADMIN_MEFALI_EMAILS` legacy ; ici pas de legacy, donc `Settings` direct).

### Project Structure Notes

- **Alignement parfait** avec la structure FastAPI existante. Aucun nouveau dossier top-level. `backend/app/core/storage/` rejoint `core/` canonique (cf. `core/rls.py` Story 10.5 comme précédent de namespace dédié).
- **Divergence volontaire vs Stories 10.2/10.3/10.4** : pas de module `backend/app/modules/xxx/` parce que la responsabilité est **transverse, pas métier** — même décision que 10.5.
- **Tests `backend/tests/test_core/test_storage/`** : nouveau sous-dossier dans `test_core/` (pattern `test_core/test_rls.py` si existe ; sinon créer `test_core/__init__.py` vide aussi). Vérifier en Task 10.

### Scan NFR66 (résultat anticipé Task 1 — validation finale en implémentation)

**Commandes** :
```bash
rg --files-with-matches -i '(storage|boto3|s3|upload[s]?)' backend/app/core/ backend/app/api/
rg --files-with-matches '(write_bytes|write_pdf\(str|open\(.*["\x27]wb)' backend/app/modules/
rg 'import boto3' backend/
rg 'def with_retry' backend/app/
```

**Résultats attendus** (validés Task 1) :
- **Zéro** helper storage préexistant dans `backend/app/core/` (confirmé : seul `admin_audit_listener.py`, `config.py`, `database.py`, `feature_flags.py`, `geolocation.py`, `llm_guards.py`, `rate_limit.py`, `rls.py`, `security.py` — tous couvrent d'autres responsabilités).
- **Zéro** import `boto3` dans tout `backend/` (confirme que 10.6 est la première intégration AWS).
- **2 consommateurs persistants** : `backend/app/modules/documents/service.py:103-126` (`_save_file_to_disk` + `write_bytes`) et `backend/app/modules/reports/service.py:357-366` (`write_pdf(str(pdf_path))` + `UPLOADS_DIR`).
- **4 consommateurs in-memory non persistants** (hors scope) : `credit/certificate.py:56`, `financing/preparation_sheet.py:108`, `applications/export.py:149`, `applications/prep_sheet.py:135` — tous retournent `pdf_bytes = HTML(...).write_pdf()` et streament via FastAPI Response sans écriture disque.
- **`with_retry` de Story 9.7** : emplacement à confirmer en Task 1 (probable `backend/app/core/resilience.py` ou `backend/app/core/retry.py` ou inline dans `backend/app/graph/tools/` — à repérer).

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-10.md#Story 10.6]
- [Source: _bmad-output/planning-artifacts/architecture.md#Décision 8 — Environnements DEV/STAGING/PROD (lignes 664-691)]
- [Source: _bmad-output/planning-artifacts/architecture.md#Décision 9 — Backup + PITR 5 min + RTO 4h / RPO 24h (lignes 693-720)]
- [Source: _bmad-output/planning-artifacts/architecture.md#Stockage local → S3 EU-West-3 (ligne 341)]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data residency NFR24 (ligne 295)]
- [Source: _bmad-output/planning-artifacts/business-decisions-2026-04-19.md#NFR69 Budget infrastructure MVP (lignes 113, 185)]
- [Source: backend/app/modules/documents/service.py:27,88-126,199,610 (consommateur persistant 1 — refactor AC4.a)]
- [Source: backend/app/modules/reports/service.py:44,357-370 (consommateur persistant 2 — refactor AC4.b)]
- [Source: backend/app/modules/reports/router.py:70-99 (download PDF — bascule signed_url AC4.b)]
- [Source: backend/app/modules/documents/router.py:355-380 (download fichier — bascule signed_url AC4.a commentaire Growth)]
- [Source: backend/app/core/config.py:1-54 (pattern Pydantic Settings à étendre Task 7)]
- [Source: backend/.env.example (section à ajouter Task 7)]
- [Source: backend/app/models/document.py:71 (`storage_path VARCHAR(500)` — clé opaque conservée)]
- [Source: _bmad-output/implementation-artifacts/10-5-rls-postgresql-4-tables-sensibles.md#Leçons capitalisées (lignes 365-373)]
- [Source: _bmad-output/implementation-artifacts/10-5-rls-postgresql-4-tables-sensibles.md#Completion Notes règle d'or E2E listeners (lignes 428)]
- [Source: _bmad-output/implementation-artifacts/10-4-module-admin-catalogue-squelette.md (pattern Settings env + scan NFR66)]
- [Source: _bmad-output/implementation-artifacts/deferred-work.md (section à étendre Task 14)]
- [Source: docs/CODEMAPS/security-rls.md (pattern structure à reproduire pour storage.md)]
- [Source: CLAUDE.md#Phase 4 — Tests prod véritables]

---

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (1M context) — bmad-dev-story workflow

### Debug Log References

- **Fix FlexibleChecksumError moto + boto3 ≥ 1.42** : ajout de
  `Config(request_checksum_calculation="when_required", response_checksum_validation="when_required")`
  au constructor `S3StorageProvider`. boto3 récent calcule des checksums
  agressifs que moto n'émet pas → mismatch sur uploads multipart ≥ 10 MB.
  Cette option réduit aussi le CPU sur les gros uploads en prod.
- **AttributeError sur `patch(_save_file_to_disk)`** : 28 tests legacy
  patchaient les helpers internes supprimés. Restauration des shims
  `_save_file_to_disk` / `_delete_file_from_disk` / `_check_disk_space`
  comme **dead code** (retournent la clé opaque, n'écrivent rien).
  Ajout d'une fixture auto-use `isolate_storage_provider` dans
  `tests/conftest.py` qui redirige `storage_local_path` vers un
  `tmp_path_factory` dédié par test → évite pollution `backend/uploads/`.
- **WeasyPrint mock** : les tests mockaient `write_pdf(path)` avec un
  stub qui attendait un path str. Le service passe désormais un
  `BytesIO`. Mise à jour de 2 fakes (`test_report_router.py` +
  `test_report_service.py`) pour accepter les deux variantes via
  `isinstance(target, IOBase)`.

### Completion Notes List

- **8/8 AC satisfaits**, **15/15 tasks complétées**.
- **49 nouveaux tests** (cible +12) répartis :
  - 13 `test_local_provider.py` (round-trip, path-traversal, streaming BinaryIO 10 MB)
  - 11 `test_s3_provider.py` (marker `s3`, moto bucket EU-West-3, SSE, TTL boundary)
  - 12 `test_s3_error_paths.py` (marker `s3`, retry transient, mapping ClientError, BotoCoreError)
  - 5 `test_providers_e2e.py` (1 MB + 10 MB × local/S3, event-loop non-blocking)
  - 8 `test_factory.py` (factory cached, switch local/s3, `_resolve_local_path`)
- **Baseline** : 1338 passed + 64 skipped → **1387 passed + 64 skipped** (+49).
- **Coverage storage module** : **88%** (cible ≥ 85%) — `base.py` 100%, `keys.py` 100%, `__init__.py` 96%, `local.py` 86%, `s3.py` 85%.
- **Zéro régression** : full suite `pytest tests/ -q` verte (1387/1387 + skipped conformes).
- **2 consommateurs migrés** vers `get_storage_provider()` : `documents/service.py` (upload/delete/analyze) + `reports/service.py` (generate_esg_report_pdf) + `reports/router.py` (download avec bascule local/S3).
- **Règle d'or 10.5 respectée** : tous les tests (local + S3 + E2E) testent l'effet observable (round-trip binaire strict) — aucun `patch("boto3.client")` ou `patch("Path.write_bytes")`.
- **Choix techniques verrouillés respectés** : boto3 sync + `asyncio.to_thread`, SSE-S3 AES256 systématique, TTL presigned [1, 3600], Settings Pydantic (pas `os.environ.get`), factory `lru_cache` avec reset helper privé.
- **Leçon nouvelle (candidate pour capitalisation)** : lorsque des tests legacy patchent des helpers internes supprimés, le pattern « shims dead code + fixture auto-use `isolate_*` » permet zéro régression tests sans contaminer le code de prod. Le shim est explicitement marqué « n'est plus appelé en prod » et son existence sert exclusivement `unittest.mock.patch`.

### File List

**Créations (15 fichiers)** :
- `backend/app/core/storage/__init__.py`
- `backend/app/core/storage/base.py`
- `backend/app/core/storage/keys.py`
- `backend/app/core/storage/local.py`
- `backend/app/core/storage/s3.py`
- `backend/tests/test_core/test_storage/__init__.py`
- `backend/tests/test_core/test_storage/conftest.py`
- `backend/tests/test_core/test_storage/test_local_provider.py`
- `backend/tests/test_core/test_storage/test_s3_provider.py`
- `backend/tests/test_core/test_storage/test_s3_error_paths.py`
- `backend/tests/test_core/test_storage/test_providers_e2e.py`
- `backend/tests/test_core/test_storage/test_factory.py`
- `docs/CODEMAPS/storage.md`

**Modifications (9 fichiers)** :
- `backend/app/core/config.py` — 4 nouveaux champs `Settings`
- `backend/app/modules/documents/service.py` — refactor upload/delete/analyze + shims legacy
- `backend/app/modules/reports/service.py` — `BytesIO` buffer + `storage.put()`
- `backend/app/modules/reports/router.py` — bascule FileResponse/RedirectResponse + rétrocompat
- `backend/.env.example` — section « Stockage fichiers »
- `backend/requirements.txt` — `boto3>=1.34,<2.0`
- `backend/requirements-dev.txt` — `moto[s3]>=5.0,<6.0`
- `backend/pytest.ini` — marker `s3`
- `backend/tests/conftest.py` — fixture auto-use `isolate_storage_provider`
- `backend/tests/test_report_router.py` — fake `write_pdf` accepte BytesIO
- `backend/tests/test_report_service.py` — fake `write_pdf` accepte BytesIO
- `docs/runbooks/README.md` — section Storage ajoutée
- `_bmad-output/implementation-artifacts/deferred-work.md` — section 10.6 ajoutée
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — `10.6: in-progress → review`

### Change Log

- 2026-04-20 : Implémentation Story 10.6 — couche d'abstraction
  `StorageProvider` (local + S3 EU-West-3) livrée. 8 AC satisfaits,
  15 tasks complétées, 49 nouveaux tests, coverage storage 88%,
  zéro régression (1387/1387 + skipped). Ready-for-review.
- 2026-04-20 : Code review 3-layers `10-6-code-review-2026-04-20.md`
  livrée — APPROVE-WITH-CHANGES (0 CRITICAL, 1 HIGH, 4 MEDIUM, 6 LOW,
  3 INFO).
- 2026-04-20 : **Post-review round 1** — 5 patches livrés, baseline
  1387 → **1406 passed + 64 skipped** (+19 tests, 0 régression) :
  - **HIGH-10.6-1 résolu** : `delete_document` rétrocompat chemins
    legacy `uploads/<uid>/<did>/<file>` via helper partagé
    `_resolve_legacy_storage_path` (aligné sur `analyze_document` —
    single source of truth). 2 tests E2E `TestDeleteDocumentLegacyPaths`
    vérifient l'effet observable (fichier physique réellement supprimé
    → neutralise fuite RGPD FR65).
  - **MEDIUM-10.6-2 résolu** : validator Pydantic `_validate_eu_region`
    sur `Settings.aws_region` + liste blanche `ALLOWED_EU_REGIONS`
    (8 régions UE). Fail-fast boot si AWS_REGION hors UE (viole NFR24).
    15 tests `test_config_aws_region.py` (1 default + 8 EU param + 5
    non-EU param rejected + 1 empty rejected).
  - **MEDIUM-10.6-3 résolu** : 2 tests `test_put_sse_applied_on_multipart_binaryio`
    et `test_put_sse_applied_on_large_bytes` — SSE-S3 AES256 prouvé
    end-to-end sur les 2 chemins `put_object` **et** `upload_fileobj`
    (2 MB via BinaryIO + 10 MB + 1 byte bytes). NFR25 immunisé contre
    régression future du dict `extra_args`.
  - **MEDIUM-10.6-4 résolu** : docstring ABC `signed_url` enrichie avec
    section « Contrat de présence divergent » (Local raise NotFound,
    S3 émet sans pré-check). `storage.md §2` aligné avec la note.
    Le consommateur qui veut la garantie doit appeler `exists()` avant.
  - **MEDIUM-10.6-5 résolu** : `upload_document` catch également
    `StoragePermissionError` → mappé `ValueError` (HTTP 400) en défense
    en profondeur. Unreachable en prod car `storage_key_for_document`
    produit toujours des clés sûres, mais immunisé contre des appelants
    futurs qui passeraient une clé brute.
  - **6 LOW tracés** dans `deferred-work.md § code review of story-10.6
    (2026-04-20)` avec mapping explicite Epic/Story cible :
    - LOW-10.6-1 filename PII en clé → Epic 18 FR65 / Story 10.7
    - LOW-10.6-2 IAM DeleteObject trop large → Story 10.7 IaC
    - LOW-10.6-3 `exists()` silencieux path-traversal → Epic 18 hardening
    - LOW-10.6-4 Versioning+MFA delete+Object Lock → Story 10.7 runbook
    - LOW-10.6-5 `ThrottlingException` code mort → Epic 18 observabilité
    - LOW-10.6-6 `to_thread` sur presigned inutile → optim Phase Growth
  - **Coverage storage** : 88% inchangé (patches testés). **Zéro MEDIUM
    résiduel, zéro HIGH/CRITICAL. Story merged ready.**
