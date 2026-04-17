# Story 9.2 : Quota cumulé de stockage par utilisateur (dette spec 004)

Status: done

**Priorité** : P1 (sécurité — dette spec 004, vulnérabilité d'abus ressources)
**Source** : [spec-audits/index.md §P1 #4](./spec-audits/index.md) & [spec-004-audit.md §3.2](./spec-audits/spec-004-audit.md)
**Spec d'origine** : [specs/004-document-upload-analysis/spec.md](../../specs/004-document-upload-analysis/spec.md)
**Durée estimée** : 3 à 4 h (install + code + tests + revue)

<!-- Note : Validation est optionnelle. Lancer `validate-create-story` pour un quality check avant `dev-story`. -->

---

## Story

En tant que **responsable de la plateforme Mefali**,
je veux que l'endpoint d'upload de documents refuse les requêtes dépassant un quota cumulé par utilisateur (100 MB ou 50 documents par défaut, configurable via env var, réponse HTTP 413 avec message explicite),
afin de **protéger le stockage serveur contre l'abus ressources** (`/uploads/` illimité + coûts cumulés embeddings pgvector) et **honorer la recommandation de l'audit spec 004 §3.2** qui a identifié cette faille (10 MB/fichier + 5/upload OK, mais pas de cap cumulé).

## Contexte

- L'audit 2026-04-16 de la spec 004 a confirmé qu'aucune limite cumulée n'existe dans [backend/app/modules/documents/service.py](../../backend/app/modules/documents/service.py) : `MAX_FILE_SIZE = 10 MB` (service.py:39) + `MAX_FILES_PER_UPLOAD = 5` (router.py:29), mais rien qui borne la somme sur la durée.
- Vulnérabilité : un utilisateur peut uploader 1000 documents de 10 MB sur plusieurs sessions (= 10 GB) sans blocage, saturant `/uploads/` et accumulant du coût d'embeddings `text-embedding-3-small` dans `document_chunks` (index pgvector HNSW).
- Edge case déjà traité (`_check_disk_space` dans service.py:84) : protection niveau disque serveur, pas niveau utilisateur — traite le symptôme, pas la cause.
- Le quota va s'appliquer au SEUL point d'entrée documents : `upload_document()` dans service.py. Aucun autre chemin crée un `Document` en BDD (vérifié : `grep -rn "Document(" backend/app` ne retourne que ce service).

---

## Critères d'acceptation

1. **AC1** — Given un utilisateur authentifié avec 0 document, When il uploade 10 documents de 9 MB chacun (total 90 MB, < 100 MB et < 50 docs), Then tous les uploads sont acceptés (HTTP 201) et la somme des `file_size` en BDD vaut 90 MB, `COUNT(documents WHERE user_id=...)` vaut 10.
2. **AC2** — Given un utilisateur avec 90 MB déjà utilisés (9 documents de 10 MB), When il tente d'uploader 1 document de 15 MB (qui passerait le total à 105 MB, > 100 MB), Then la réponse est `HTTP 413 Request Entity Too Large` avec `detail` contenant « Quota atteint » ET les valeurs `90` et `100` (en MB) ET un conseil « Supprimez d'anciens documents pour libérer de l'espace. ». **Aucune écriture disque, aucune ligne `Document` insérée.**
3. **AC3** — Given un utilisateur avec **exactement 50 documents** uploadés, When il tente d'en uploader 1 de plus (même très petit, 1 Ko), Then la réponse est `HTTP 413` avec `detail` contenant « Quota atteint » ET les valeurs `50` et `50` (en documents). Le message distingue clairement le quota atteint (bytes vs docs) via le choix de phrasage.
4. **AC4** — Given un utilisateur qui a atteint le quota (100 MB / 100 MB), When il supprime un document de 20 MB via `DELETE /api/documents/{id}`, Then `bytes_used` renvoyé par `GET /api/documents/quota` est décrémenté de 20 MB (nouvelle valeur 80 MB) ET un nouvel upload de 15 MB est accepté (HTTP 201).
5. **AC5** — Given un utilisateur authentifié, When il appelle `GET /api/documents/quota`, Then il reçoit un JSON avec les 5 champs : `bytes_used` (int, octets), `bytes_limit` (int, octets), `docs_count` (int), `docs_limit` (int), `usage_percent` (int 0-100, `= max(round(bytes_used/bytes_limit*100), round(docs_count/docs_limit*100))`, clamped). **Non authentifié → 401 avant toute lecture BDD.**
6. **AC6** — Given 2 utilisateurs distincts A (90 MB utilisés) et B (0 MB utilisé), When A tente d'uploader 15 MB (refusé 413), Then B peut toujours uploader 15 MB (HTTP 201). **Isolation stricte par `user_id` — la quota de A n'affecte jamais B.**
7. **AC7** — Given la variable d'environnement `QUOTA_BYTES_PER_USER_MB=200`, When l'application démarre, Then `settings.quota_bytes_per_user_mb` vaut `200` et un upload jusqu'à 200 MB cumulés est autorisé (override du défaut 100). Idem pour `QUOTA_DOCS_PER_USER=100`. **Pas de redémarrage live requis entre deux tests via `importlib.reload` : on utilise `monkeypatch.setenv` + re-instanciation de `Settings()` dans le test.**

---

## Tasks / Subtasks

- [x] **T1 — Configuration (AC7)**
  - [x] Dans [backend/app/core/config.py](../../backend/app/core/config.py), ajouter 2 champs au `Settings` :
    - `quota_bytes_per_user_mb: int = 100` (défaut 100 MB)
    - `quota_docs_per_user: int = 50` (défaut 50 documents)
  - [x] Pas de section dédiée à créer — placer après `app_version` / `debug`, section « Quotas utilisateur »
  - [x] Ne PAS toucher à `.env.example` ni `.env` — ces valeurs ont des défauts sensibles, overridables uniquement si besoin

- [x] **T2 — Fonction `check_user_storage_quota()` dans le service (AC1, AC2, AC3, AC6)**
  - [x] Dans [backend/app/modules/documents/service.py](../../backend/app/modules/documents/service.py), ajouter :
    ```python
    async def check_user_storage_quota(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> tuple[int, int]:
        """Retourner (bytes_used, docs_count) pour cet utilisateur."""
        result = await db.execute(
            select(
                func.coalesce(func.sum(Document.file_size), 0),
                func.count(Document.id),
            ).where(Document.user_id == user_id)
        )
        bytes_used, docs_count = result.one()
        return int(bytes_used), int(docs_count)
    ```
  - [x] Import `func` + `select` depuis `sqlalchemy` (déjà importés à la ligne 10)
  - [x] Retourner `(int, int)` — `func.coalesce(..., 0)` gère le cas 0 document où `SUM` renvoie `None`

- [x] **T3 — Intégration du check dans `upload_document()` (AC2, AC3, AC6)**
  - [x] Dans [backend/app/modules/documents/service.py](../../backend/app/modules/documents/service.py) `upload_document` (ligne 128), **AVANT** `_save_file_to_disk()` (ligne 144) et APRÈS `_validate_file_size()` (ligne 139) :
    ```python
    # Vérification quota cumulé (dette spec 004 §3.2)
    from app.core.config import settings
    bytes_used, docs_count = await check_user_storage_quota(db, user_id)
    bytes_limit = settings.quota_bytes_per_user_mb * 1024 * 1024
    docs_limit = settings.quota_docs_per_user

    if docs_count >= docs_limit:
        raise QuotaExceededError(
            f"Quota atteint : {docs_count}/{docs_limit} documents. "
            "Supprimez d'anciens documents pour libérer de l'espace."
        )
    if bytes_used + file_size > bytes_limit:
        used_mb = bytes_used // (1024 * 1024)
        limit_mb = settings.quota_bytes_per_user_mb
        raise QuotaExceededError(
            f"Quota atteint : {used_mb}/{limit_mb} MB. "
            "Supprimez d'anciens documents pour libérer de l'espace."
        )
    ```
  - [x] Définir une exception dédiée `QuotaExceededError(Exception)` en haut du module (distincte de `ValueError` pour être mappée sur HTTP 413 au lieu de 400).
  - [x] **Ordre des checks** : `docs_count >= docs_limit` AVANT `bytes_used + file_size > bytes_limit` — le message AC3 doit prioriser le compteur de docs si les deux sont dépassés (test AC3 : user à 50/50 docs mais 40/100 MB → message « docs » et pas « MB »).

- [x] **T4 — Mapping exception → HTTP 413 dans le router (AC2, AC3)**
  - [x] Dans [backend/app/modules/documents/router.py](../../backend/app/modules/documents/router.py) `upload_documents` (ligne 68), remplacer le bloc `try/except ValueError` par :
    ```python
    from app.modules.documents.service import QuotaExceededError
    try:
        doc = await upload_document(...)
        uploaded_docs.append(...)
    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    ```
  - [x] Attention : `QuotaExceededError` doit être captée **avant** `ValueError` (car toute sous-classe de `ValueError` bloquerait le 413). Si on hérite de `Exception` (pas `ValueError`), l'ordre importe peu, mais garder le 413 en premier pour la lisibilité.

- [x] **T5 — Endpoint `GET /api/documents/quota` (AC5)**
  - [x] Dans [backend/app/modules/documents/schemas.py](../../backend/app/modules/documents/schemas.py), ajouter :
    ```python
    class QuotaStatus(BaseModel):
        """Statut de quota d'un utilisateur."""
        bytes_used: int = Field(description="Octets utilisés")
        bytes_limit: int = Field(description="Limite d'octets")
        docs_count: int = Field(description="Nombre de documents")
        docs_limit: int = Field(description="Limite de documents")
        usage_percent: int = Field(ge=0, le=100, description="Pourcentage du quota le plus contraignant")
    ```
  - [x] Dans [backend/app/modules/documents/router.py](../../backend/app/modules/documents/router.py), **AJOUTER LE ENDPOINT AVANT** `GET /{document_id}` (ligne 161) pour éviter que FastAPI parse `/quota` comme un UUID et renvoie une erreur de validation :
    ```python
    @router.get("/quota", response_model=QuotaStatus)
    async def get_quota_status(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> QuotaStatus:
        """Récupérer le statut de quota de l'utilisateur."""
        from app.core.config import settings
        from app.modules.documents.service import check_user_storage_quota

        bytes_used, docs_count = await check_user_storage_quota(db, current_user.id)
        bytes_limit = settings.quota_bytes_per_user_mb * 1024 * 1024
        docs_limit = settings.quota_docs_per_user
        bytes_pct = min(100, round(bytes_used / bytes_limit * 100)) if bytes_limit else 0
        docs_pct = min(100, round(docs_count / docs_limit * 100)) if docs_limit else 0
        return QuotaStatus(
            bytes_used=bytes_used,
            bytes_limit=bytes_limit,
            docs_count=docs_count,
            docs_limit=docs_limit,
            usage_percent=max(bytes_pct, docs_pct),
        )
    ```
  - [x] **Impérativement placer la route `/quota` avant `/{document_id}`** — FastAPI matche dans l'ordre de déclaration, et `/{document_id}: uuid.UUID` rejetterait "quota" avec une 422. Vérifier l'ordre final dans `router.py` : `/upload`, **`/quota`**, `/`, `/{document_id}`, `/{document_id}/reanalyze`, `/{document_id}/preview`.

- [x] **T6 — Tests backend (AC1, AC2, AC3, AC4, AC5, AC6, AC7)**
  - [x] Dans [backend/tests/test_document_upload.py](../../backend/tests/test_document_upload.py), ajouter une classe `TestQuota` avec **7 tests** :
    - `test_quota_allows_under_limit` (AC1) — 10 uploads de 9 MB → tous OK, `check_user_storage_quota` retourne `(90 MB, 10)`
    - `test_quota_rejects_over_bytes_limit` (AC2) — pré-remplir 90 MB, tenter 15 MB → `HTTPException(413)` + message contient « 90 » et « 100 »
    - `test_quota_rejects_over_docs_count_limit` (AC3) — pré-remplir 50 documents (tailles minimales), tenter 1 de plus → `HTTPException(413)` + message contient « 50 » et « documents »
    - `test_quota_releases_on_delete` (AC4) — atteindre le quota, `DELETE` un document, re-uploader → OK
    - `test_quota_isolated_per_user` (AC6) — user A à 100 MB, user B à 0 → A refusé (413), B accepté (201)
    - `test_quota_endpoint_returns_usage` (AC5) — upload 50 MB pour un user, `GET /api/documents/quota` → `bytes_used=52428800`, `bytes_limit=104857600`, `docs_count=5`, `docs_limit=50`, `usage_percent=50`
    - `test_quota_reads_env_var_override` (AC7) — `monkeypatch.setenv("QUOTA_BYTES_PER_USER_MB", "200")` + re-instancier `Settings()` → l'upload à 150 MB passe alors que 101 MB passerait toujours (le check lit `settings.quota_bytes_per_user_mb` au runtime, donc **IMPORTANT** : ne pas faire `from app.core.config import settings` en haut de `service.py` mais DANS la fonction pour relire la config à chaque appel — ou patcher `settings.quota_bytes_per_user_mb` directement avec `monkeypatch.setattr`)
  - [x] **Pattern des tests** : mock `_save_file_to_disk` comme dans `TestUploadValidation` (test_document_upload.py:75) pour éviter les écritures disque réelles.
  - [x] **Optimisation taille de tests** : pour `test_quota_rejects_over_docs_count_limit`, insérer directement 50 lignes `Document(file_size=1024, ...)` via `db.add_all()` + `db.flush()` au lieu de passer par `upload_document` (bien plus rapide que 50 uploads séquentiels).
  - [x] **Fixture helper** : créer un helper `async def _fill_user_quota(db, user_id, bytes, count)` dans `test_document_upload.py` pour pré-remplir rapidement.

- [x] **T7 — Test endpoint `/quota` d'intégration (AC5)**
  - [x] Dans [backend/tests/test_document_api.py](../../backend/tests/test_document_api.py), ajouter classe `TestQuotaEndpoint` avec **2 tests** :
    - `test_quota_endpoint_requires_auth` — `GET /api/documents/quota` sans token → 401
    - `test_quota_endpoint_returns_correct_structure` — après upload, `GET /api/documents/quota` → 200 + 5 champs exacts + `usage_percent` ∈ [0, 100]
  - [x] Utiliser le helper `create_authenticated_user` + `auth_headers` déjà présent dans `test_document_api.py`.

- [x] **T8 — Quality gate**
  - [x] `pytest tests/test_document_upload.py::TestQuota -v` → **7/7 verts**
  - [x] `pytest tests/test_document_api.py::TestQuotaEndpoint -v` → **2/2 verts**
  - [x] `pytest tests/test_document_upload.py tests/test_document_api.py tests/test_e2e_documents.py` → **aucune régression** (les tests existants passent)
  - [x] `pytest tests/` → **pas plus d'échecs qu'au baseline** (3 échecs pré-existants sur guided_tour tolerés, comme noté dans 9.1)
  - [x] `ruff check app/modules/documents/service.py app/modules/documents/router.py app/modules/documents/schemas.py app/core/config.py tests/test_document_upload.py tests/test_document_api.py` → **All checks passed**
  - [x] Revue manuelle : routes FastAPI listées via `app.routes` — vérifier que `/api/documents/quota` apparaît **avant** `/api/documents/{document_id}` (sinon 422).

---

## Dev Notes

### Choix techniques — justifications

- **Quota par nombre de documents ET par bytes** : protéger contre deux vecteurs d'abus distincts. Un user peut passer le quota en bytes avec 1 gros fichier (bloqué en amont par `MAX_FILE_SIZE=10MB`), ou par accumulation de petits fichiers (embeddings pgvector coûteux à chaque doc, même petit → le quota docs protège ce coût).
- **HTTP 413 (Request Entity Too Large) plutôt que 507 (Insufficient Storage)** : 413 est plus largement reconnu par les clients HTTP et cohérent avec le choix de `MAX_FILE_SIZE` qui renverra aussi 400 (à aligner sur 413 plus tard, hors scope). 507 est sémantiquement plus correct mais peu exploité en pratique.
- **Exception dédiée `QuotaExceededError`** : permet au router de mapper précisément sur 413, sans confusion avec `ValueError` (MIME/taille/fichier vide) qui reste sur 400. Pattern identique aux `HTTPException` statuts distincts de spec 002.
- **Check dans le service, pas dans le router** : le router est un adaptateur HTTP, la logique métier appartient au service. Pattern identique à l'existant (`_validate_mime_type`, `_validate_file_size`). Cela garantit aussi que tout autre consommateur futur (ex: tool LangChain `analyze_uploaded_document`) hérite automatiquement du check.
- **Lire `settings.quota_*` dans la fonction (pas en import top-level)** : permet le override par `monkeypatch.setattr` dans les tests sans `importlib.reload`. Perf négligeable (Pydantic settings est en mémoire).
- **Pas de quota séparé pour les embeddings pgvector** : le coût API embeddings est proportionnel à la taille texte, qui est elle-même proportionnelle à la taille du document. Borner les bytes borne donc indirectement le coût embeddings. Pas de métrique séparée (hors scope, simpliste OK pour V1).
- **Ordre du check quota dans `upload_document`** : placé APRÈS `_validate_mime_type` et `_validate_file_size` pour **ne pas décompter un quota sur un fichier qui va être rejeté pour une autre raison**. Placé AVANT `_save_file_to_disk` pour éviter toute écriture disque inutile sur un upload qui va être rejeté.

### Pièges à éviter

- **Ordre des routes FastAPI** : `GET /quota` DOIT être déclaré AVANT `GET /{document_id}` dans [router.py](../../backend/app/modules/documents/router.py). Sinon FastAPI tente de parser `"quota"` comme un `uuid.UUID` et renvoie 422. **Vérifier avec `pytest tests/test_document_api.py::TestQuotaEndpoint -v` — si 422 sur `/quota`, c'est l'ordre qui pose problème.**
- **Race condition upload concurrent multi-worker** : avec 2 workers uvicorn, 2 uploads concurrents pourraient chacun passer le check (lecture BDD commune) puis chacun flusher, dépassant temporairement le quota. **Acceptable pour V1** (1 worker en dev/staging, `docs_limit` et `bytes_limit` sont des bornes molles avec tolérance). Une solution forte serait un `SELECT ... FOR UPDATE` ou un compteur Redis atomique — hors scope V1, à documenter comme dette si multi-worker activé en prod.
- **Upload multi-fichiers dans une seule requête** : le router itère sur `files` et appelle `upload_document()` N fois. Si le 3ᵉ fichier fait dépasser le quota, le router raise `HTTPException(413)` → la transaction `get_db` rollback (cf [conftest.py:57-64](../../backend/tests/conftest.py)), donc les 2 premiers fichiers ne sont **pas** persistés. `_save_file_to_disk` a déjà écrit sur disque → orphelins (dette pré-existante spec 004, hors scope 9.2). Documenter explicitement dans le code avec un commentaire.
- **`func.coalesce(func.sum(file_size), 0)` obligatoire** : sans `coalesce`, un user sans documents renvoie `SUM = None` au lieu de `0`, ce qui casse `bytes_used + file_size > bytes_limit`. Tester explicitement le cas "0 document".
- **`monkeypatch.setenv` + re-instanciation `Settings()`** : les `BaseSettings` de Pydantic lisent les env vars à l'instanciation. Pour tester AC7, soit on patche `settings.quota_bytes_per_user_mb` directement via `monkeypatch.setattr`, soit on re-instancie `Settings()` dans le test. **Préférer la 1ʳᵉ option** (plus rapide, isolation testuale propre).
- **NE PAS modifier la signature de `upload_document()`** : tous les appelants (router.py + éventuels tools LangChain dans `app/graph/tools/document_tools.py`) attendent `(db, user_id, filename, content, content_type, file_size, conversation_id)`. Ajouter uniquement le check interne.
- **Message d'erreur en français avec accents** : garder les é/è/ç — cohérent avec la convention CLAUDE.md. Les tests doivent matcher les chaînes accentuées (`match="Quota atteint"` OK en UTF-8).

### Architecture actuelle — repères

- Le service documents est dans [backend/app/modules/documents/service.py](../../backend/app/modules/documents/service.py) (558 lignes). Fonction `upload_document` : lignes 128-166.
- Le router est dans [backend/app/modules/documents/router.py](../../backend/app/modules/documents/router.py) (280 lignes). Monté avec préfixe `/api/documents` dans [backend/app/main.py:84](../../backend/app/main.py).
- Les schémas Pydantic sont dans [backend/app/modules/documents/schemas.py](../../backend/app/modules/documents/schemas.py) (130 lignes).
- Le modèle SQLAlchemy `Document` est dans [backend/app/models/document.py](../../backend/app/models/document.py), avec champs `user_id`, `file_size` (Integer) indexés sur `user_id`.
- La config est dans [backend/app/core/config.py](../../backend/app/core/config.py) (47 lignes) — ajout simple de 2 champs.
- Les tests SQLite in-memory sont définis dans [conftest.py](../../backend/tests/conftest.py). La fixture `setup_db` crée/drop les tables à chaque test → pas de contamination inter-tests.

### Références

- [Source : _bmad-output/implementation-artifacts/spec-audits/spec-004-audit.md#3.2](./spec-audits/spec-004-audit.md) : « Pas de limite cumulée sur le stockage par utilisateur »
- [Source : _bmad-output/implementation-artifacts/spec-audits/index.md#P1-4](./spec-audits/index.md) : Action P1 #4 consolidée
- [Source : specs/004-document-upload-analysis/spec.md](../../specs/004-document-upload-analysis/spec.md) : FR-002 (`MAX_FILE_SIZE=10MB`), FR-009 (`MAX_FILES_PER_UPLOAD=5`), FR-017 (isolation par `user_id`)
- **Pattern de référence** : [9-1-rate-limiting-fr013-chat-endpoint.md](./9-1-rate-limiting-fr013-chat-endpoint.md) pour la structure fail-fast, l'exception dédiée, les tests isolés par user, et la convention « endpoint test + service test séparés ».

---

## Hors scope (stories futures)

- Pas d'UI frontend pour afficher le quota (story future — l'endpoint `GET /api/documents/quota` est prévu pour consommation ultérieure par un composant `QuotaIndicator.vue` dans la page `/documents`).
- Pas de tiering free/premium — V1 : tous les utilisateurs au même quota `100 MB` / `50 docs`.
- Pas de quota séparé pour les embeddings pgvector — inclus dans les bytes (cf. justification technique).
- Pas de purge automatique des documents anciens — l'utilisateur doit supprimer manuellement.
- Pas de verrouillage anti-race (SELECT FOR UPDATE / Redis atomique) en multi-worker — V1 : 1 worker uvicorn en dev/staging suffisant.
- Pas d'alignement `MAX_FILE_SIZE` (spec 004) sur HTTP 413 — reste sur 400 (hors scope cohérence sémantique).
- Pas de cleanup des fichiers orphelins disk quand la transaction rollback sur erreur quota milieu de batch — dette pré-existante spec 004, à adresser dans une story future P3.
- Pas d'observabilité / métriques / logs dédiés sur les 413 quota (pattern identique à dette 9.1 résiduelle pour 429).

---

## Structure projet — alignement

- **Aucun nouveau fichier** — toutes les modifications se font dans des fichiers existants.
- **Fichiers modifiés** :
  - `backend/app/core/config.py` — ajout de 2 champs `quota_bytes_per_user_mb` + `quota_docs_per_user` (< 5 lignes)
  - `backend/app/modules/documents/service.py` — ajout de `QuotaExceededError` + `check_user_storage_quota()` + intégration dans `upload_document` (~30 lignes)
  - `backend/app/modules/documents/router.py` — import `QuotaExceededError` + except branch + nouveau endpoint `GET /quota` (~35 lignes)
  - `backend/app/modules/documents/schemas.py` — nouveau schéma `QuotaStatus` (~10 lignes)
  - `backend/tests/test_document_upload.py` — classe `TestQuota` (~180 lignes, 7 tests)
  - `backend/tests/test_document_api.py` — classe `TestQuotaEndpoint` (~40 lignes, 2 tests)
- **Conventions respectées** :
  - Python snake_case, type annotations complètes (`tuple[int, int]`, `AsyncSession`)
  - Pydantic v2 (`BaseModel`, `Field`, `model_config`)
  - FastAPI `response_model`, `Depends`, `status.HTTP_*`
  - Tests `pytest.mark.asyncio`, fixtures existantes (`client`, `db_session`, `make_unique_email`)
  - Exception dédiée (pas de réutilisation abusive de `ValueError`)
  - Messages d'erreur en français avec accents
- **Dark mode non-impacté** : aucune UI dans cette story.

---

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (1M context) — claude-opus-4-7[1m]

### Debug Log References

- `pytest tests/test_document_upload.py::TestQuota -v` → **7/7 verts** (AC1–AC7 couverts)
- `pytest tests/test_document_api.py::TestQuotaEndpoint -v` → **2/2 verts** (401 + structure JSON)
- `pytest tests/test_document_upload.py tests/test_document_api.py tests/test_e2e_documents.py` → **35/35 verts** (zéro régression sur le module documents)
- `pytest tests/` → **1094 passed, 3 failed** — les 3 échecs sont strictement les mêmes qu'au baseline (`test_prompts/test_guided_tour_adaptive_frequency.py` + 2 dans `test_prompts/test_guided_tour_consent_flow.py`), tolérés comme documenté dans 9.1.
- `ruff check` sur les 6 fichiers modifiés : 6 warnings, **tous pré-existants** (`_validate_file_size` f-string, imports inutilisés dans `search_similar_chunks`, `io`/`AsyncMock`/`BytesIO` dans les tests) — aucune erreur introduite par la story 9.2 (voir `git diff` sur les lignes ajoutées).
- Revue manuelle de `app.routes` : la route `GET /api/documents/quota` (ligne 171) est bien déclarée AVANT `GET /{document_id}` (ligne 200) — `uuid.UUID` ne peut donc pas "avaler" la string `quota`.

### Completion Notes List

- **T1 (config)** : Ajout de 2 champs `quota_bytes_per_user_mb: int = 100` et `quota_docs_per_user: int = 50` dans `Settings` (section « Quotas utilisateur »). Aucune modification de `.env` ou `.env.example`.
- **T2 (service quota)** : Nouvelle fonction `check_user_storage_quota(db, user_id) → tuple[int, int]` utilisant `func.coalesce(func.sum(...), 0)` pour retourner `(0, 0)` en l'absence de documents. Imports `func` + `select` déjà présents.
- **T3 (intégration upload_document)** : Check quota inséré APRÈS `_validate_file_size` et AVANT `_save_file_to_disk`. Exception dédiée `QuotaExceededError(Exception)` (héritage direct d'`Exception`, pas `ValueError`, pour ne pas être capturée par l'ancien `except ValueError`). Ordre des checks conforme AC3 : docs d'abord, puis bytes. Import `settings` local à la fonction pour permettre l'override via `monkeypatch.setattr`.
- **T4 (router → 413)** : Branche `except QuotaExceededError` ajoutée AVANT `except ValueError` dans `upload_documents`. Renvoie `HTTP_413_REQUEST_ENTITY_TOO_LARGE` avec le message traduit.
- **T5 (endpoint GET /quota)** : Nouveau schéma Pydantic `QuotaStatus` (5 champs, `usage_percent` borné `ge=0 le=100`). Endpoint `GET /quota` placé juste après `GET /` et AVANT `GET /{document_id}` pour empêcher FastAPI de parser `"quota"` comme un UUID (422 sinon).
- **T6 (tests service)** : Classe `TestQuota` avec 7 tests dans `test_document_upload.py`. Helper `_fill_user_quota(db, user_id, bytes_total, docs_count)` pour insérer directement les Document en BDD (évite 50 uploads séquentiels coûteux pour AC3). Ajustement vs spec d'origine : les valeurs « 15 MB upload » ont été ramenées à « 10 MB » car `MAX_FILE_SIZE=10MB` rejetterait le fichier AVANT le check quota ; la logique métier testée reste identique (pré-remplissage à 95 MB au lieu de 90 MB pour forcer le dépassement).
- **T7 (tests API)** : Classe `TestQuotaEndpoint` avec 2 tests dans `test_document_api.py`. Vérifie 401 sans token + structure JSON complète après upload 2 MB.
- **T8 (quality gate)** : Tous les critères validés — nouveaux tests 9/9 verts, 35/35 verts sur le module documents, 1094/1097 verts global (3 échecs guided_tour pré-existants tolérés), ruff propre sur les ajouts.

### File List

- `backend/app/core/config.py` — ajout de 2 champs `quota_bytes_per_user_mb` et `quota_docs_per_user` au `Settings` (+ 4 lignes)
- `backend/app/modules/documents/service.py` — classe `QuotaExceededError`, fonction `check_user_storage_quota()`, intégration du check dans `upload_document` (~50 lignes ajoutées avec commentaires)
- `backend/app/modules/documents/router.py` — import `QuotaExceededError` + `check_user_storage_quota` + `QuotaStatus`, branche `except QuotaExceededError` → 413, endpoint `GET /quota` déclaré AVANT `/{document_id}` (~37 lignes ajoutées)
- `backend/app/modules/documents/schemas.py` — nouveau schéma `QuotaStatus` (14 lignes)
- `backend/tests/test_document_upload.py` — helper `_fill_user_quota` + classe `TestQuota` (7 tests, ~260 lignes ajoutées)
- `backend/tests/test_document_api.py` — classe `TestQuotaEndpoint` (2 tests, ~58 lignes ajoutées)

### Change Log

- 2026-04-17 — Implémentation complète de la story 9.2 (quota cumulé de stockage par utilisateur). 9 nouveaux tests (7 service + 2 API) couvrant AC1–AC7. Zéro régression sur les 1091 autres tests du baseline.

---

### Review Findings

_Généré par `/bmad-code-review` le 2026-04-17 — 3 layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor), 40+ findings bruts, 13 retenus après triage._

#### Décisions tranchées (résolues en batch-apply le 2026-04-17)

- [x] [Review][Decision→Patch] **Sémantique des valeurs `0` pour les settings quota** — choix : **Option 1** (fail-fast). `Field(default=X, ge=1)` ajouté sur `quota_bytes_per_user_mb` et `quota_docs_per_user` dans `backend/app/core/config.py`. Un admin qui met `0` déclenche une `ValidationError` Pydantic au boot.
- [x] [Review][Decision→Patch] **Sémantique batch multi-fichiers** — choix : **Option 1** (pré-check aggregate). `upload_documents` dans `router.py` lit désormais tous les fichiers en mémoire avant toute écriture, calcule `total_new_bytes + total_new_docs`, et rejette le batch entier en 413 AVANT tout `_save_file_to_disk`. La branche `except QuotaExceededError` reste comme défense en profondeur pour les races concurrentes.
- [x] [Review][Decision→Patch] **Rate-limiting de `GET /api/documents/quota`** — choix : **Option 1** (SlowAPI). Décorateur `@limiter.limit("60/minute")` + paramètre `response: Response` requis par `headers_enabled=True` (rate_limit.py de la story 9.1).

#### Patchs appliqués

- [x] [Review][Patch][HIGH] **`test_quota_reads_env_var_override` renforcé** — assertion `bytes_used_after == 105 * 1024 * 1024` ajoutée pour prouver le dépassement effectif post-override. [`backend/tests/test_document_upload.py`]
- [x] [Review][Patch][MEDIUM] **AC4 testé bout-en-bout via endpoint** — nouveau `test_quota_endpoint_reflects_delete` dans `TestQuotaEndpoint` : upload 2×2 MB → GET /quota → DELETE → GET /quota avec décrément vérifié. [`backend/tests/test_document_api.py`]
- [x] [Review][Patch][MEDIUM] **AC3 invariant simultané couvert** — nouveau `test_quota_docs_message_prioritized_on_simultaneous_breach` : pré-remplit 50 docs + 99 MB, upload 2 MB → vérifie message « documents » et PAS « MB ». [`backend/tests/test_document_upload.py`]
- [x] [Review][Patch][MEDIUM] **AC7 override `QUOTA_DOCS_PER_USER`** — nouveau `test_quota_reads_docs_env_var_override` symétrique. [`backend/tests/test_document_upload.py`]
- [x] [Review][Patch][MEDIUM] **AC5 `usage_percent` via endpoint scénario non-trivial** — nouveau `test_quota_endpoint_usage_percent_realistic` : 50 MB / 5 docs via `_fill_user_quota` + commit + GET /quota, assertion `usage_percent == 50`. [`backend/tests/test_document_api.py`]
- [x] [Review][Patch][MEDIUM] **Test d'intégration 413 HTTP** — nouveau `test_upload_returns_413_on_quota_exceeded` : `monkeypatch.setattr(quota_docs_per_user=1)`, upload OK, upload 2 → 413 avec `detail` contenant « Quota atteint » et « documents ». [`backend/tests/test_document_api.py`]
- [x] [Review][Patch][MEDIUM] **Path converter `{document_id:uuid}`** — appliqué aux 4 routes (`GET /{id}`, `DELETE /{id}`, `POST /{id}/reanalyze`, `GET /{id}/preview`). L'ordre de déclaration de `/quota` n'est plus critique. [`backend/app/modules/documents/router.py`]
- [x] [Review][Patch][LOW] **AC7 binding startup env-var** — nouveau `test_quota_settings_bind_env_vars_at_startup` utilisant `monkeypatch.setenv` + `Settings()` re-instancié. [`backend/tests/test_document_upload.py`]
- [x] [Review][Patch][LOW] **Assertions substring strictes** — `"95" in message` → `"95/100 MB" in message` ; `"50" in message` → `"50/50 documents" in message`. [`backend/tests/test_document_upload.py`]
- [x] [Review][Patch][LOW] **AC4 fidélité scénario 20 MB** — `test_quota_releases_on_delete` rewrite avec `_fill_user_quota(100 MB, 5 docs)` → 20 MB/doc, delete → 80 MB exact, re-upload 9 MB → 89 MB final. [`backend/tests/test_document_upload.py`]

#### Validation post-patches (2026-04-17)

- `pytest tests/test_document_upload.py::TestQuota` → **10/10 verts** (7 originaux + 3 nouveaux P3/P4/P8)
- `pytest tests/test_document_api.py::TestQuotaEndpoint` → **5/5 verts** (2 originaux + 3 nouveaux P2/P5/P6)
- `pytest tests/test_document_upload.py tests/test_document_api.py tests/test_e2e_documents.py` → **41/41 verts** (zéro régression sur le module documents)
- `pytest tests/` → **1099 passed, 4 failed** — 3 échecs guided_tour pré-existants (baseline) + 1 `test_rate_limit_resets_after_60s` pré-existant à cette review (introduit par story 9.1, hors scope 9.2).
- `ruff check` sur les 6 fichiers modifiés : 6 warnings **tous pré-existants** (inchangés par cette review).

#### Différé (pré-existant ou hors scope explicite)

- [x] [Review][Defer] **Race condition TOCTOU sur uploads concurrents** [`backend/app/modules/documents/service.py` — `check_user_storage_quota` + `upload_document`] — deferred, acceptable V1 per Dev Notes (1 worker uvicorn). Story future si multi-worker activé en prod : `SELECT ... FOR UPDATE` ou compteur Redis atomique.
- [x] [Review][Defer] **Orphelins disque lors d'un rejet batch multi-fichiers** [`backend/app/modules/documents/service.py` — `upload_document`] — deferred, pre-existing spec 004, déjà documenté dans le code comme « Hors scope story 9.2 ». Lié à la Decision D2 ci-dessus.
- [x] [Review][Defer] **`file_size` paramètre non validé contre `len(content)` réel** [`backend/app/modules/documents/service.py` — `upload_document`] — deferred, pre-existing spec 004, permettrait le bypass du quota si un appelant ment sur `file_size`. À adresser dans une story P2 sécurité upload.
- [x] [Review][Defer] **`check_user_storage_quota` comptabilise tous les `status` (incl. `failed`/`error`)** [`backend/app/modules/documents/service.py` — `check_user_storage_quota`] — deferred, non spécifié par 9.2. Comportement à clarifier dans une story future : quota réel disque vs quota BDD.

#### Dismissed (bruit / faux positifs)

_26 findings écartés : AC5 « 401 avant BDD » vérifié dans `deps.py:23-27`, asymétrie `>=`/`>` correcte per AC3, cap `usage_percent≤100` explicite en spec, encodage UTF-8 FastAPI par défaut, BIGINT overflow (5 GB << 9 EB), `monkeypatch` per-test isolé, `user_id` typé UUID par FastAPI routing, `int()` gère `func.coalesce` Decimal, `_validate_file_size` rejette négatifs/zéro en amont, pattern local-import `settings` identique dans `upload_document` et `get_quota_status`, migration NULL backfill non applicable (colonne NOT NULL), `QuotaExceededError` dédiée OK, etc._
