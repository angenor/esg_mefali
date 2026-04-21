# Story 10.10 : Micro-Outbox `domain_events` + worker batch 30 s (APScheduler + SELECT FOR UPDATE SKIP LOCKED)

Status: review

> **Contexte** : 12ᵉ story Phase 4, **première infra lourde (L, ~3 h)** depuis 10.7 (env DEV/STAGING/PROD). Retour aux Fondations backend pures après 10.9 (S ~35 min, formalisation feature flag). Story **bloquante** pour : (a) tous les handlers d'invalidation verdicts AR-D3 (Epic 13), (b) recalcul cube 4D sur `fund_updated` / `intermediary_updated` (MEDIUM-10.1-6), (c) audit trail eventually consistent (D7), (d) nettoyage `prefill_drafts.expires_at < now()` (consommateur Story 16.5), (e) absorption dette MEDIUM-10.1-14 `next_retry_at` colonne manquante.
>
> **État de départ — schema livré, worker absent** :
> - **Migration `027_create_outbox_and_prefill_drafts.py`** (Story 10.1 ✅ DONE) crée la table `domain_events(id UUID, event_type varchar(64), aggregate_type varchar(64), aggregate_id UUID, payload JSONB, status varchar(16) default 'pending', retry_count INT default 0, error_message TEXT, created_at, processed_at)` + index partiel `idx_domain_events_pending (created_at) WHERE processed_at IS NULL AND retry_count < 5` + index `idx_domain_events_aggregate (aggregate_type, aggregate_id)` + contrainte `CHECK retry_count <= 5`.
> - **Modules `projects/events.py`, `maturity/events.py`, `admin_catalogue/events.py`** (Stories 10.2-10.4 ✅ DONE) déclarent déjà les `event_type` constantes (`PROJECT_CREATED_EVENT_TYPE = "project.created"`, etc.) en attente de consommateurs Epic 11-13.
> - **`backend/app/core/outbox/`** : **n'existe pas**. Aucun writer, aucun worker, aucun registre.
> - **Modèle ORM `DomainEvent`** : **n'existe pas** dans `backend/app/models/`. Raw SQL Alembic uniquement.
> - **`APScheduler`** : **absent** de `backend/requirements.txt`. Nouvelle dépendance à ajouter (version pinnée ≥ 3.10, ≤ 4.0).
>
> **Ce qu'il reste à livrer pour 10.10** :
> 1. **Module `backend/app/core/outbox/`** (AC1-AC3) — 4 fichiers : `__init__.py` (exports publics), `writer.py` (`write_domain_event(db, event_type, aggregate_type, aggregate_id, payload)` — insert dans transaction courante, pas de commit interne), `worker.py` (APScheduler AsyncIOScheduler, job `process_outbox_batch` intervalle configurable défaut 30 s), `handlers.py` (registry `EVENT_HANDLERS` frozen tuple + dispatch fail-fast sur event_type inconnu).
> 2. **Modèle ORM `DomainEvent`** (AC1) — `backend/app/models/domain_event.py` avec `id UUID PK`, `event_type str`, `aggregate_type str`, `aggregate_id UUID`, `payload JSONB`, `status str`, `retry_count int`, `error_message str | None`, `created_at`, `processed_at | None`. Nécessaire pour `SELECT ... FOR UPDATE SKIP LOCKED` via SQLAlchemy + lisibilité tests.
> 3. **Migration additive `028_add_next_retry_at_to_domain_events.py`** (AC4 + dette MEDIUM-10.1-14) — `next_retry_at TIMESTAMPTZ NULL` + recréation de l'index partiel `idx_domain_events_pending` pour inclure `(next_retry_at IS NULL OR next_retry_at <= now())`. **Down-revision `027_outbox_prefill` → attention `028_tamper_proof_audit_tables.py` (Story 10.5 résolu) dépend déjà de `027`** : conflit de chaîne à résoudre (**Q5 tranchée infra** ci-dessous).
> 4. **Retry exponentiel [30 s, 120 s, 600 s]** (AC4) — **pas** `[1, 3, 9]` pattern `with_retry` LLM (NFR75) mais **backoff Outbox dédié** pattern architecture.md §D11 (30 s, 2 min, 10 min). `[1, 3, 9]` c'est 9 s total max → incompatible avec un DB transient 30-60 s typique. **Justification stockée dans Q1 ci-dessous.**
> 5. **Statut final `failed` après 3 retries** (AC4) — flag `status='failed'` (pas table séparée `domain_events_dead` — Q3 tranchée).
> 6. **Observability structurée** (AC5) — log JSON par event consommé : `event_id`, `event_type`, `aggregate_type`, `aggregate_id`, `attempt`, `status` (`success`|`retry`|`failed`|`unknown_handler`), `duration_ms`, `error_message`. Pattern `extra={"metric": "outbox_event_processed", ...}` identique à `with_retry` (NFR37 structured JSON).
> 7. **Kill-switch `DOMAIN_EVENTS_WORKER_ENABLED=false`** (AC6 Epic) — Settings Pydantic + helper `should_start_outbox_worker()`. Startup `main.py::lifespan` conditionne `scheduler.start()`.
> 8. **Intégration startup/shutdown `main.py::lifespan`** (AC2) — `scheduler.start()` au démarrage, `scheduler.shutdown(wait=True)` au shutdown. Pattern reuse `register_admin_access_listener` (Story 10.5).
> 9. **Purge `prefill_drafts` où `expires_at < now()`** (AC9 bonus — dette **MEDIUM-10.1-5 équivalente** absorbée) — 2ᵉ job APScheduler intervalle 1 h, batch 500. Extraction 10.10 légitime car **le scheduler est instancié ici une fois pour tous les jobs périodiques MVP** (pas 2 schedulers en parallèle → anti-race).
> 10. **Documentation `docs/CODEMAPS/outbox.md`** (AC8) — 7 sections Mermaid (transaction writer → worker SKIP LOCKED → dispatch → retry → dead-letter) + contrat handler idempotent + règles NFR30/NFR37/NFR75 + anti-patterns (2 process, timezone, catch-all Exception).
> 11. **Tests 10+ : unit writer + unit handlers registry + E2E worker PostgreSQL** (AC6 epic) — **Marker `@pytest.mark.postgres` obligatoire sur les tests worker** : `SELECT ... FOR UPDATE SKIP LOCKED` n'est pas supporté par SQLite in-memory (leçon Story 10.1). Tests unit writer OK en SQLite (raw INSERT + transaction).
>
> **Hors scope explicite (déféré)** :
> - **Handlers métier réels** (invalidation verdicts D3, notifications SSE, REFRESH MATERIALIZED VIEW cube 4D) → livrés par Epic 13 (`fact_updated`, `criterion_rule_updated`) + Epic 14 (`fund_updated`, `intermediary_updated`) + Story 9.12 (`fund_application_generated` notif chat). **Story 10.10 livre uniquement la plomberie + 1 handler dummy `noop_handler` pour tester le dispatch + 1 handler `purge_expired_prefill_drafts_handler` piloté par un job cron séparé (pas par domain_events).**
> - **Migration du worker hors process FastAPI** (Celery/Redis/SQS/EventBridge) → différé Phase Growth (Décision 11 MVP). Architecture `APScheduler + FOR UPDATE SKIP LOCKED` garantit la migration sans refactor Outbox (seul le trigger change).
> - **Opt-in per-tenant handlers** → non MVP. Tous les handlers sont globaux.
> - **Poison message manual UI** → déféré Epic 20 admin tooling. `status='failed'` reste consultable via SQL direct / admin API futur.
> - **Alerting admin externe (Sentry/PagerDuty)** sur `status='failed'` → log WARNING structuré suffit MVP (NFR40). Intégration Sentry déférée Story 20.3.
> - **Circuit breaker par `event_type`** → non MVP. `with_retry` LLM a un breaker (NFR75) ; l'Outbox a seulement le cap `retry_count <= 5` au niveau BDD et `status='failed'` applicatif après 3 tentatives.
> - **Pattern Outbox complet (message broker cross-service)** → différé Phase Vision (Clarif. 1).
>
> **Contraintes héritées (11 leçons Stories 9.x → 10.9)** :
> 1. **C1 (9.7) — pas de `try/except Exception` catch-all** : le worker attrape uniquement les exceptions propagées par les handlers (BaseException → re-raise). Pattern `try/except Exception as exc:` autorisé **uniquement** autour de l'appel handler individuel (défense en profondeur registry) avec capture du nom d'exception dans `error_message`, mais **jamais** autour d'un bloc worker entier qui masquerait une erreur de BDD (laisser crasher le scheduler → restart clean). Une violation = re-review.
> 2. **C2 (9.7) — tests prod véritables** : les tests E2E worker passent par **PostgreSQL réel** (TEST_ALEMBIC_URL), pas un mock `SELECT ... FOR UPDATE`. Marker `@pytest.mark.postgres` obligatoire sur tous les tests utilisant `SKIP LOCKED` (incompatible SQLite).
> 3. **Scan NFR66 Task 1 (10.3 M1)** — avant toute modification, `rg -n "domain_events\|DomainEvent" backend/app/` consigne les consommateurs amont (attendu : 3 fichiers events.py modules + 1 commentaire service + 0 consommateur runtime). Un 5ᵉ hit serait un signal d'alarme (run avant Task 2).
> 4. **Comptages runtime (10.4)** — AC9 prouvé par `pytest --collect-only -q backend/tests/` avant (1503 baseline post-10.9) / après (cible ≥ 1515). Delta cité dans Completion Notes.
> 5. **Pas de duplication (10.5)** — `write_domain_event` centralisé dans `core/outbox/writer.py`. Scan post-refactor : `rg -n "INSERT INTO domain_events\|DomainEvent\(" backend/app/ | grep -v core/outbox` doit retourner **0 hit** (aucune écriture hors writer).
> 6. **Règle d'or 10.5 — tester effet observable** : les tests E2E appellent **le vrai writer** + **le vrai worker** + **un vrai handler enregistré** et assertent sur **la vraie ligne `domain_events.status='processed'`** en BDD. Pas de mock du scheduler, pas de mock du SELECT.
> 7. **Pattern shims legacy (10.6)** — `backend/app/modules/projects/service.py` (commentaire ligne 39 « via domain_events CCC-14 D11 ») sera mis à jour Epic 11. Story 10.10 **ne touche pas** à `projects/service.py` / `maturity/service.py` — la plomberie est livrée prête pour eux.
> 8. **Choix verrouillés pré-dev (10.6+10.7+10.8+10.9)** — Q1 à Q5 ci-dessous sont **tranchées dans ce story file** avant Task 2. Aucune décision architecture pendant l'implémentation.
> 9. **Pattern commit intermédiaire si refactor (10.8)** — livrable naturellement fragmenté en 4 commits lisibles : (a) migration 028 + modèle ORM, (b) writer + tests unit, (c) worker + handlers registry + tests E2E postgres, (d) main.py lifespan + kill-switch + doc CODEMAPS. Commit atomique global si diff < 800 lignes.
> 10. **Golden snapshots — non applicable** (Story 10.8 a capitalisé ce pattern pour les prompts ; 10.10 n'a pas d'artefact texte stable à figer — les handlers sont du Python structuré, pas du texte LLM).
> 11. **Framework injection pattern CCC-9 (10.8)** — `EVENT_HANDLERS: Final[tuple[HandlerEntry, ...]]` frozen tuple + `HandlerEntry = @dataclass(frozen=True)` stdlib (pas Pydantic) — **pattern byte-identique à `INSTRUCTION_REGISTRY` Story 10.8** (`backend/app/prompts/registry.py` lignes 47-70). Réutilisation explicite — voir AC3.
>
> **Absorption dettes déférées** :
> - **MEDIUM-10.1-14** (`domain_events.next_retry_at` backoff exponentiel) → absorbée via migration 028 + logique `next_retry_at = now() + interval backoff[attempt]` dans worker. Sans ce champ, le worker serait forcé à un retry immédiat → hot-loop CPU.
> - **MEDIUM-10.1-6** (`REFRESH MATERIALIZED VIEW mv_fund_matching_cube` après seed) → partiellement absorbée : le **handler** `fund_updated → refresh MV` est livré **Epic 14**, mais la plomberie Outbox qui le déclenchera est ici. Consigné dans `docs/CODEMAPS/outbox.md §6 Consommateurs prévus`.
> - **Purge `prefill_drafts.expires_at < now()`** → absorbée via 2ᵉ job APScheduler (AC9).
>
> **Risque résiduel** : si Phase 1 ajoute du trafic avant Epic 13/14 (handlers réels), les events insérés dans `domain_events` par Epic 11/12 (`project.created`, `maturity_level_declared`) seront consommés par le handler `noop_handler` livré ici (log + marquer `processed`) → aucun effet de bord mais pas de perte de données. **Acceptable MVP.**

---

## Questions tranchées pré-dev (Q1-Q5)

**Q1 — APScheduler AsyncIOScheduler vs. `BackgroundTask` FastAPI startup ?**

→ **Tranche : `APScheduler.schedulers.asyncio.AsyncIOScheduler`** (nouvelle dépendance `apscheduler>=3.10,<4.0`).

- **Rationale** : (a) un `BackgroundTask` FastAPI est rattaché à une requête HTTP — l'Outbox worker doit vivre **indépendamment** de tout cycle de requête (démarrage lifespan startup), (b) APScheduler gère nativement les intervalles, les overlaps (`max_instances=1`, évite 2 batches concurrents dans le même process), les timezones, et les shutdowns propres (scheduler.shutdown(wait=True)), (c) architecture.md D11 §Worker batch documente explicitement « APScheduler dans le process FastAPI MVP, à migrer vers process Celery séparé Phase Growth » — décision architecturale prise en amont.
- **Alternative rejetée** : `asyncio.create_task(infinite_loop_with_sleep(30))` dans `lifespan` — viable mais : (a) gestion shutdown manuelle (CancelledError propagation), (b) pas de `max_instances` protection si un batch dépasse 30 s (batch N+1 se superpose → SKIP LOCKED protège la BDD mais double CPU), (c) pas de timezone safety (sleep drift), (d) réimplémentation partielle d'APScheduler.
- **Conséquence acceptée** : `apscheduler>=3.10,<4.0` ajouté à `requirements.txt`. Dépendance OSS mature (depuis 2011, largement adoptée). Zéro dépendance externe (apscheduler est Python pur).

**Q2 — Registre handlers : tuple frozen (pattern 10.8) vs. dict mutable + `register_handler()` décorateur ?**

→ **Tranche : tuple frozen `Final[tuple[HandlerEntry, ...]]`** (pattern byte-identique à 10.8 `INSTRUCTION_REGISTRY`).

- **Rationale** : (a) **cohérence codebase** — Story 10.8 a établi `tuple[InstructionEntry, ...]` frozen pour les instructions transverses prompts ; réutiliser le pattern évite un 2ᵉ mental model pour le même besoin (registre append-only à compile-time), (b) un dict mutable avec `register_handler(event_type)` décorateur introduit un **ordre de chargement non déterministe** (import-time side effect) → difficile à tester et à auditer, (c) le tuple frozen échoue **à l'import** si un event_type est dupliqué (via un `_validate_unique_event_types()` module-level au chargement) → fail-fast vs erreur au runtime.
- **HandlerEntry** (`@dataclass(frozen=True)` stdlib) : `event_type: str` (match pattern `<entity>.<verb_past>` cf. architecture.md §D11 nommage), `handler: Callable[[DomainEvent, AsyncSession], Awaitable[None]]` (async, raise pour retry), `description: str` (doc). Aucun Pydantic nécessaire (pas de validation user input — c'est du code interne).
- **Ajouter un handler Epic 13 = 1 bloc dans le tuple**, aucune modification du worker, aucun décorateur magique. Traçabilité 100 % via grep.

**Q3 — Dead-letter : table séparée `domain_events_dead` vs. flag `status='failed'` ?**

→ **Tranche : flag `status='failed'`** (la colonne `status` existe déjà dans la table livrée par migration 027).

- **Rationale** : (a) **simplicité MVP** — migration 027 a déjà `status varchar(16) default 'pending'` + `CHECK retry_count <= 5`. Un transition `pending → processed | failed | unknown_handler` suffit. Créer une table séparée imposerait : (i) une 2ᵉ migration, (ii) un `INSERT INTO dead WHERE move FROM live` atomique par event (CTE complexe), (iii) un index supplémentaire, (iv) une jointure admin pour retrouver l'historique. (b) **Volume attendu MVP** : < 100 failed/an (NFR37 observabilité). Pas besoin d'archivage froid. (c) **Requêtage admin** : `SELECT * FROM domain_events WHERE status = 'failed' ORDER BY processed_at DESC` est suffisant pour un admin tooling futur (Epic 20).
- **Valeurs `status` finales (contrat)** : `'pending'` (défaut insertion writer), `'processing'` (optionnel, verrou SKIP LOCKED suffit — on ne l'utilise PAS pour éviter une UPDATE en début de traitement), `'processed'` (succès), `'failed'` (3 retries épuisés), `'unknown_handler'` (event_type absent du registry, fail-fast AC5 Epic). **4 valeurs finales** : `pending`, `processed`, `failed`, `unknown_handler`.
- **Contrainte check additionnelle migration 028** : `CHECK status IN ('pending', 'processed', 'failed', 'unknown_handler')` — **non** ajoutée par 10.10 (la colonne existe sans cette contrainte depuis 027) → **déféré** en Task 8 debt log comme LOW debt `ck_domain_events_status_enum` (absorption facultative migration 028 si diff reste petit — **à trancher opérateur au moment du diff**).

**Q4 — Intervalle worker : 30 s fixe hardcodé vs. configurable via Settings ?**

→ **Tranche : configurable via Settings Pydantic** `domain_events_worker_interval_s: int = Field(default=30, ge=5, le=3600)`.

- **Rationale** : (a) en DEV, un ingénieur qui debug un handler veut pouvoir forcer `DOMAIN_EVENTS_WORKER_INTERVAL_S=5` pour itérer rapidement ; en STAGING/PROD, le défaut 30 s (architecture.md D11) s'applique — **toggle sans redéploiement**. (b) borne `ge=5` évite une boucle hot-loop par configuration accidentelle ; borne `le=3600` évite un « worker dormant 1 jour » qui créerait une latence métier cachée (invalidation verdicts jamais appliquée). (c) pattern aligné Story 10.9 (`enable_project_model`) et Story 10.7 (`env_name`).
- **Kill-switch séparé** : `domain_events_worker_enabled: bool = Field(default=True)` — permet de désactiver complètement le scheduler (DEV debug ciblé AC6 Epic). Lecture dynamique **au startup** uniquement (cohérent APScheduler, pas de toggle live runtime car `scheduler.pause_job()` existe mais complique le shutdown).
- **Conséquence acceptée** : 2 nouveaux env vars (`DOMAIN_EVENTS_WORKER_ENABLED`, `DOMAIN_EVENTS_WORKER_INTERVAL_S`). Documentés dans `docs/CODEMAPS/outbox.md §5 Pièges`.

**Q5 — Conflit de chaîne Alembic : 028_tamper_proof_audit_tables.py (Story 10.5) a déjà `down_revision = "027_outbox_prefill"` ?**

→ **Tranche : nouvelle migration `029_add_next_retry_at_to_domain_events.py`** avec `down_revision = "028_audit_tamper"`.

- **Rationale** : la migration tamper-proof (028) est **déjà déployée** (Story 10.5 DONE commit `e5a13c4`). Réécrire son down_revision casserait le déploiement STAGING. Créer `029` est la solution propre et chronologique (pattern NNN séquentiel NFR62).
- **Renommage** : la doc (architecture.md, deferred-work.md) parle de « migration 028 ». **Renommer via `docs/CODEMAPS/data-model-extension.md` pour rediriger vers 029** dans une note : « La colonne `next_retry_at` est livrée par migration **029** (Story 10.10), pas 028 — 028 est tamper-proof audit. » Un test unit scanne l'absence de « migration 028 » pointant vers `next_retry_at` dans la doc.
- **Alternative rejetée** : absorber `next_retry_at` dans une révision hors-séquence (e.g. `027b_add_next_retry_at`) → casse la convention `NNN_description.py`.

---

## Story

**As a** Équipe Mefali (backend),

**I want** livrer la plomberie **micro-Outbox MVP** `backend/app/core/outbox/` consommant la table `domain_events` (créée par migration 027 Story 10.1) : (a) un **writer** `write_domain_event(db, event_type, aggregate_type, aggregate_id, payload)` qui insère un event dans la **transaction courante** du caller (atomicité CCC-14 garantie sans commit interne) ; (b) un **worker** `AsyncIOScheduler` APScheduler démarré au `lifespan` startup qui exécute toutes les **30 s** (configurable 5 s à 3600 s) un batch `SELECT ... FROM domain_events WHERE processed_at IS NULL AND retry_count < 5 AND (next_retry_at IS NULL OR next_retry_at <= now()) ORDER BY created_at LIMIT 100 FOR UPDATE SKIP LOCKED` — verrou PostgreSQL natif garantissant l'idempotence multi-process (multi-workers gunicorn en PROD) sans Redis ; (c) un **registre `EVENT_HANDLERS: Final[tuple[HandlerEntry, ...]]` frozen** (pattern 10.8 CCC-9) dispatchant chaque event vers son handler async idempotent ; (d) un **retry exponentiel** [30 s, 2 min, 10 min] via colonne `next_retry_at TIMESTAMPTZ` (migration 029 qui ajoute ce champ + absorbe dette MEDIUM-10.1-14) et transition `status` vers `failed` après 3 tentatives épuisées ; (e) une **observabilité** log JSON structuré par event traité (NFR37) avec `event_id`, `event_type`, `attempt`, `status`, `duration_ms` ; (f) un **kill-switch** `DOMAIN_EVENTS_WORKER_ENABLED=false` pour debug DEV ; (g) un **2ᵉ job** cron 1 h qui purge `prefill_drafts WHERE expires_at < now()` (consommateur Story 16.5) — co-localisé pour éviter 2 schedulers concurrents ; (h) une **documentation** `docs/CODEMAPS/outbox.md` détaillant le contrat d'idempotence des handlers et les anti-patterns (2 process sans SKIP LOCKED, timezone naïf, catch-all Exception).

**So that** les effets de bord transactionnels Phase 1 (invalidation `referential_verdicts` AR-D3 Epic 13, recalcul cube 4D Epic 14 MEDIUM-10.1-6, audit eventually consistent D7, notifications SSE post-soumission FR34, recalcul eligibility post-référentiel publié) soient **atomiquement cohérents** avec les transactions métier (CCC-14) — insérer un event est byte-identique à insérer une ligne dans une table fille de la transaction — et que **l'absence de Redis/Celery MVP** (D7 arbitrage `pas de Redis MVP`) ne bloque pas la livraison des handlers d'invalidation cache ESG et des notifications post-publication référentiel — la promesse architecturale D11 (`SELECT FOR UPDATE SKIP LOCKED` multi-replicas via PostgreSQL natif, migration Phase Growth EventBridge sans refactor Outbox) soit **mesurable en CI** via les tests E2E postgres marqués `@pytest.mark.postgres`.

---

## Acceptance Criteria

### AC1 — `backend/app/core/outbox/writer.py` expose `write_domain_event(...)` qui insère dans la transaction courante

**Given** un service métier qui importe `from app.core.outbox.writer import write_domain_event`,

**When** il appelle `await write_domain_event(db, event_type="project.created", aggregate_type="project", aggregate_id=project.id, payload={"company_id": str(company.id), "name": project.name})` à l'intérieur d'une transaction SQLAlchemy ouverte (`async with db.begin():` ou session sans `commit()` explicite),

**Then** :

- Une ligne est **ajoutée** dans `domain_events` via `db.add(DomainEvent(...))` + `await db.flush()` (pas de `db.commit()` interne — **la décision de commit appartient au caller**, garantie CCC-14).
- Si le caller `raise` après l'appel, la transaction rollback **inclut** l'event — aucune fuite.
- La signature est strictement typée Pydantic-compatible : `event_type: str` (regex `^[a-z_]+\.[a-z_]+$` validé par un `_validate_event_type()` module-level), `aggregate_type: str`, `aggregate_id: UUID`, `payload: dict[str, Any]` (JSON-sérialisable vérifié au best-effort via `json.dumps(payload, default=str)` dry-run).
- Le modèle ORM `backend/app/models/domain_event.py` existe et est importé dans `backend/app/models/__init__.py` (mapper SQLAlchemy chargé).
- `id` UUID est généré par défaut côté Python (`uuid.uuid4()`) — pas de reliance sur `gen_random_uuid()` BDD (portabilité SQLite tests unit).
- Scan `rg -n "INSERT INTO domain_events\|DomainEvent\(" backend/app/` retourne **1 hit unique** (dans `core/outbox/writer.py`) — aucune écriture hors writer (règle 10.5 no duplication).

### AC2 — `backend/app/core/outbox/worker.py` lance APScheduler + `SELECT FOR UPDATE SKIP LOCKED`

**Given** l'app FastAPI démarre via `main.py::lifespan`,

**When** la variable `DOMAIN_EVENTS_WORKER_ENABLED=true` (défaut) et `DOMAIN_EVENTS_WORKER_INTERVAL_S=30` (défaut),

**Then** :

- Un `AsyncIOScheduler` APScheduler est instancié avec `timezone=UTC` **explicite** (NFR37 — pas de TZ implicite OS).
- Le job `process_outbox_batch` est planifié avec `IntervalTrigger(seconds=30)`, `max_instances=1` (protection overlap), `coalesce=True` (drop missed runs), `id="outbox_batch_worker"`.
- Le job `purge_expired_prefill_drafts` est planifié avec `IntervalTrigger(seconds=3600)`, `max_instances=1`, `coalesce=True`, `id="prefill_drafts_purge"`.
- `scheduler.start()` est appelé **dans** `main.py::lifespan` startup section — après `register_admin_access_listener`, avant le yield.
- `scheduler.shutdown(wait=True)` est appelé dans la section shutdown — **avant** `engine.dispose()` (évite jobs en vol quand la pool ferme).
- La fonction `process_outbox_batch(engine: AsyncEngine) -> None` exécute :
  1. Ouvre une session dédiée (`async with AsyncSession(engine) as db:`).
  2. Exécute `SELECT ... FROM domain_events WHERE processed_at IS NULL AND retry_count < 5 AND status != 'failed' AND status != 'unknown_handler' AND (next_retry_at IS NULL OR next_retry_at <= now()) ORDER BY created_at LIMIT 100 FOR UPDATE SKIP LOCKED` via SQLAlchemy `select(DomainEvent).with_for_update(skip_locked=True)`.
  3. Pour chaque event : dispatche via `EVENT_HANDLERS` registry ou marque `status='unknown_handler'` fail-fast.
  4. Commit la session (release les verrous row-level).
- Scan `rg -n "FOR UPDATE SKIP LOCKED\|with_for_update" backend/app/core/outbox/` retourne **≥ 1 hit** dans worker.py.

### AC3 — `backend/app/core/outbox/handlers.py` expose `EVENT_HANDLERS: Final[tuple[HandlerEntry, ...]]` frozen (pattern CCC-9 10.8)

**Given** le registre de handlers,

**When** un dev audite `backend/app/core/outbox/handlers.py`,

**Then** :

- Le fichier expose `@dataclass(frozen=True) class HandlerEntry: event_type: str; handler: Callable[[DomainEvent, AsyncSession], Awaitable[None]]; description: str`.
- `EVENT_HANDLERS: Final[tuple[HandlerEntry, ...]]` est un **tuple immuable** (pas `list`, pas `dict`) — pattern byte-identique à `backend/app/prompts/registry.py::INSTRUCTION_REGISTRY` (Story 10.8 CCC-9).
- Story 10.10 livre **2 handlers dummy** :
  1. `HandlerEntry(event_type="noop.test", handler=noop_handler, description="Handler test idempotent — log + no-op. Utilisé pour les tests E2E.")` — **uniquement chargé en DEV/TEST** via check `settings.env_name != "prod"` (évite handler test en PROD).
  2. Aucun handler métier réel en 10.10 (Epic 13-14 livrent les vrais — cf. commentaires prospectifs dans le fichier).
- Un helper `dispatch_event(event: DomainEvent, db: AsyncSession) -> HandlerResult` :
  - Cherche `HandlerEntry` par `event_type` (linear scan tuple — O(n), n < 50 events attendus MVP, acceptable vs complexité dict).
  - Si absent → retourne `HandlerResult(status='unknown_handler', error_message=f'Unknown event_type: {event.event_type}')`. **Fail-fast** AC5 Epic.
  - Sinon → appelle `await handler(event, db)` dans un `try` local (capture uniquement `Exception`, pas `BaseException` — SystemExit / KeyboardInterrupt remontent).
  - Succès → `HandlerResult(status='processed')`.
  - Exception → `HandlerResult(status='retry' | 'failed', error_message=str(exc) + ':' + type(exc).__name__)` selon `retry_count`.
- Un helper `_validate_unique_event_types()` exécuté à l'import : `assert len(set(entry.event_type for entry in EVENT_HANDLERS)) == len(EVENT_HANDLERS)` → fail-at-import si duplication.
- Scan `rg -n "register_handler\|HANDLER_DICT" backend/app/core/outbox/` retourne **0 hit** (pas de décorateur, pas de dict mutable).

### AC4 — Retry exponentiel [30 s, 120 s, 600 s] + migration 029 ajoute `next_retry_at`

**Given** un event dont le handler `raise` une exception,

**When** le worker traite l'event,

**Then** :

- `retry_count` est incrémenté (`+= 1`), `error_message` est mis à jour (`str(exc) + ':' + type(exc).__name__` — max 500 chars tronqué).
- `next_retry_at = now() + interval backoff[retry_count - 1]` avec `backoff = [30, 120, 600]` secondes (`BACKOFF_SCHEDULE: Final[tuple[int, ...]] = (30, 120, 600)`). Rationale architecture.md D11 « 30 s, 2 min, 10 min ».
- Après le **3ᵉ** retry (retry_count = 3), le prochain batch ne repêche pas l'event (`retry_count < 5` dans la WHERE clause via contrainte DB, mais **le worker applicatif force `status='failed'`** dès que `retry_count >= 3` pour cap applicatif). `processed_at = now()` est set pour sortir de l'index partiel. Un log WARNING est émis `extra={"metric": "outbox_event_failed", "event_id": ..., "retry_count": 3, "final_error": ...}`.
- Migration `backend/alembic/versions/029_add_next_retry_at_to_domain_events.py` :
  - `revision = "029_outbox_next_retry_at"`, `down_revision = "028_audit_tamper"` (Q5).
  - Upgrade : `ALTER TABLE domain_events ADD COLUMN next_retry_at TIMESTAMPTZ NULL`.
  - `DROP INDEX idx_domain_events_pending; CREATE INDEX idx_domain_events_pending ON domain_events (created_at) WHERE processed_at IS NULL AND retry_count < 5 AND (next_retry_at IS NULL OR next_retry_at <= now())` — **attention l'expression `now()`** dans `WHERE` partiel est **non-IMMUTABLE** → PostgreSQL refuse l'index partiel avec `now()`. **Workaround** : `WHERE processed_at IS NULL AND retry_count < 5` (comme avant) + filtrer `next_retry_at` dans la **query worker** uniquement. Commentaire migration documente ce choix.
  - Downgrade : `ALTER TABLE domain_events DROP COLUMN next_retry_at` + recréation index original.
  - Header commentaire cite `MEDIUM-10.1-14` résolu + Story 10.10.
- Test postgres : après 3 échecs d'un handler qui raise, la ligne BDD a `status='failed'`, `retry_count=3`, `error_message` non-NULL, `processed_at` non-NULL, et le worker ne la repêche plus (`SELECT ... WHERE processed_at IS NULL ...` retourne 0).

### AC5 — Observability : log JSON structuré par event traité (NFR37)

**Given** le worker consomme un event,

**When** l'exécution handler se termine (succès ou échec),

**Then** :

- Un log INFO (succès) / WARNING (retry) / ERROR (failed final, unknown_handler) est émis via `logger.info/warning/error` du module `app.core.outbox.worker`.
- Le log porte un champ `extra` structuré contenant **exactement** : `metric` (`outbox_event_processed` | `outbox_event_retry` | `outbox_event_failed` | `outbox_event_unknown_handler`), `event_id` (UUID str), `event_type` (str), `aggregate_type` (str), `aggregate_id` (UUID str), `attempt` (int, 1-indexed), `status` (`processed` | `retry` | `failed` | `unknown_handler`), `duration_ms` (int), `error_message` (str | None, max 500 chars).
- Pattern byte-identique à `log_tool_call` (Story 9.7) — voir `backend/app/graph/tools/common.py::log_tool_call` pour référence de style. Pas de `print()`, pas de `logger.debug` (NFR37 structured JSON en PROD).
- Aucun log ne contient de donnée PII extraite du `payload` (audit privacy NFR18). **Le payload est résumé via `payload_keys: list(payload.keys())` uniquement** — jamais `payload` entier dans les logs (pattern confidentialité 10.5 RLS).
- Un test unit vérifie la forme du log via `caplog` pytest fixture + assertion sur les clés `extra`.

### AC6 — Kill-switch `DOMAIN_EVENTS_WORKER_ENABLED` + Settings `domain_events_worker_interval_s`

**Given** `backend/app/core/config.py::Settings`,

**When** un dev audite le schéma config post-10.10,

**Then** :

- `domain_events_worker_enabled: bool = Field(default=True, description="Kill-switch worker Outbox (Story 10.10). Désactiver en DEV pour debug handler. Lu au startup uniquement.")` déclaré dans `class Settings(BaseSettings)`.
- `domain_events_worker_interval_s: int = Field(default=30, ge=5, le=3600, description="Intervalle APScheduler Outbox en secondes (architecture.md D11 défaut 30 s). Borné 5-3600 pour éviter hot-loop ou worker dormant.")` déclaré.
- **Comportement** dans `main.py::lifespan` : si `settings.domain_events_worker_enabled is False` → `logger.warning("Worker Outbox désactivé (DOMAIN_EVENTS_WORKER_ENABLED=false) — events s'accumulent en 'pending'")` + `scheduler.start()` est **skip**. Les events continuent d'être insérés mais ne sont jamais consommés → debug DEV ciblé.
- Un test unit vérifie `Settings().domain_events_worker_enabled is True` (défaut) et que `DOMAIN_EVENTS_WORKER_ENABLED=false` via `monkeypatch.setenv` + `Settings()` fresh donne `False`.
- Un test unit vérifie la borne `ge=5` : `DOMAIN_EVENTS_WORKER_INTERVAL_S=2` → `ValidationError` au boot.

### AC7 — Tests E2E PostgreSQL ≥ 5 + unit tests ≥ 7 (total ≥ 12, cible baseline 1503 → ≥ 1515)

**Given** `backend/tests/test_core/test_outbox/`,

**When** les tests sont exécutés,

**Then** :

**Tests unit (`@pytest.mark.unit`, SQLite OK, ≥ 7)** :

1. `test_write_domain_event_inserts_row_in_current_transaction` — writer ajoute sans commit, rollback propage à l'event.
2. `test_write_domain_event_validates_event_type_format` — `event_type="BadFormat"` → `ValueError` explicite (regex).
3. `test_write_domain_event_validates_payload_json_serializable` — payload contenant `datetime` naïve → `ValueError` (documenter comment passer `str(dt.isoformat())`).
4. `test_event_handlers_registry_is_frozen_tuple` — `isinstance(EVENT_HANDLERS, tuple) and type(EVENT_HANDLERS).__name__ == 'tuple'` + tentative `EVENT_HANDLERS.append()` → `AttributeError`.
5. `test_event_handlers_have_unique_event_types` — `_validate_unique_event_types()` passe à l'import (import side-effect).
6. `test_dispatch_event_returns_unknown_handler_for_unregistered_type` — event avec `event_type="unregistered.foo"` → `HandlerResult(status='unknown_handler', ...)`.
7. `test_settings_domain_events_worker_fields` — Settings déclare les 2 champs avec défauts + bornes.
8. `test_settings_interval_below_5_raises_validation_error` — borne `ge=5`.
9. `test_log_structure_contains_all_expected_keys` — caplog assertion sur `extra` dict du log `outbox_event_processed`.

**Tests E2E (`@pytest.mark.postgres`, PostgreSQL real, ≥ 5)** :

1. `test_worker_processes_pending_event_and_marks_processed` — INSERT 1 event, appel direct `process_outbox_batch(engine)`, assert `status='processed'` + `processed_at NOT NULL`.
2. `test_worker_skip_locked_allows_concurrent_processing` — 2 coroutines `process_outbox_batch` simultanées sur 10 events, chaque event traité **exactement une fois** (pas de double dispatch).
3. `test_worker_retry_schedules_next_retry_at_on_handler_exception` — handler qui raise, après 1er retry `retry_count=1`, `next_retry_at ≈ now() + 30s`.
4. `test_worker_marks_failed_after_3_retries` — handler qui raise toujours, après 3 passes `status='failed'`, `retry_count=3`, `processed_at NOT NULL`.
5. `test_worker_marks_unknown_handler_fail_fast_without_retry` — event avec `event_type` absent du registry → `status='unknown_handler'`, `retry_count=0`, `processed_at NOT NULL` (pas de retry — fail-fast AC5 Epic).
6. `test_purge_prefill_drafts_removes_expired_rows` — INSERT 3 `prefill_drafts` dont 2 avec `expires_at < now()`, appel `purge_expired_prefill_drafts(engine)`, assert 1 restant.

**Baseline** :

- Pré-10.10 : `1569 collected, 1503 passed + 66 skipped` (Story 10.9 Completion Notes).
- Post-10.10 : **≥ 1581 collected, 1515 passed** (+12 plancher AC9 Epic, cible réaliste +14-16 via 9 unit + 6 postgres). Zéro régression sur les 1503 tests pré-10.10.
- Coverage `backend/app/core/outbox/` : **≥ 90 %** (NFR60 code critique — retry logic, dispatch fail-fast, log structure).

### AC8 — Documentation `docs/CODEMAPS/outbox.md` (7 sections)

**Given** aucun `docs/CODEMAPS/outbox.md` pré-10.10,

**When** 10.10 est livré,

**Then** :

- `docs/CODEMAPS/outbox.md` existe avec **7 sections minimales** :
  - **§1 Vue d'ensemble** : schéma Mermaid 5 nœuds (service métier → writer → table domain_events → worker SKIP LOCKED → dispatch → handler).
  - **§2 Contrat writer** : signature `write_domain_event`, règle « pas de commit interne », atomicité CCC-14.
  - **§3 Contrat worker** : boucle batch 30 s, SKIP LOCKED multi-process, `max_instances=1` APScheduler anti-overlap, kill-switch.
  - **§4 Contrat handler** : `async def handler(event: DomainEvent, db: AsyncSession) -> None`, **idempotent** (rejeu du même event = même résultat), raise `Exception` pour retry, raise rien (None return) pour succès.
  - **§5 Pièges** : (a) 2 process APScheduler sans SKIP LOCKED = double traitement, (b) timezone implicite → dérive sleep OS, (c) payload PII dans log → leak, (d) handler non-idempotent = bugs subtils après redelivery, (e) `next_retry_at` dans WHERE partiel PostgreSQL refuse `now()` (workaround filtre runtime), (f) catch-all `Exception` trop large masque erreur DB, (g) `raise SystemExit` dans un handler tue le scheduler (ne jamais).
  - **§6 Consommateurs prévus** : tableau 10+ lignes — `project.created` → Epic 11 handler X, `fact_updated` → Epic 13 invalidation `referential_verdicts` (AR-D3), `fund_updated` → Epic 14 REFRESH MATERIALIZED VIEW `mv_fund_matching_cube` (MEDIUM-10.1-6), `fund_application_submitted` → Story 9.12 notif chat PDF, `referential_version_published` → FR34 notifications, etc.
  - **§7 Migration Phase Growth** : documenter que le pattern `APScheduler + SKIP LOCKED` est **remplaçable** par AWS EventBridge / Celery sans refactor — seul le trigger change, la table + writer + handlers restent identiques.
- `docs/CODEMAPS/index.md` référence la nouvelle page (+1 ligne).
- Test unit `test_outbox_codemap_has_7_sections` : lit `outbox.md`, assert présence `## §1` à `## §7` (ordre et présence).

### AC9 — Baseline 1503 → ≥ 1515 (+12 plancher, cible +14-16) + zéro régression

**Given** baseline post-10.9 : `1569 collected, 1503 passed + 66 skipped`.

**When** Story 10.10 livre les nouveaux tests (estimation 9 unit + 6 postgres = +15),

**Then** :

- `pytest backend/tests/test_core/test_outbox/ -v` : **≥ 15 tests** (9 unit + 6 postgres marqués, postgres skippés si `TEST_ALEMBIC_URL` absent en local — cohérent Story 10.1 pattern).
- `pytest backend/tests/` : **≥ 1515 passed + X skipped** (X = 66 + 6 postgres skips si pas de PostgreSQL local = 72). Les 1503 tests pré-10.10 passent **tous** sans modification (pattern shims legacy 10.6 — aucun test existant n'importe `core/outbox/` car il n'existe pas).
- Delta exact consigné en Completion Notes via `pytest --collect-only -q backend/tests/` avant/après.
- Coverage `backend/app/core/outbox/` **≥ 90 %** (NFR60 code critique). Les branches `unknown_handler`, `retry`, `failed`, `next_retry_at` timing doivent être toutes couvertes.

---

## Tasks / Subtasks

- [x] **Task 1 — Scan NFR66 + constat état actuel** (AC1, AC2, AC3)
  - [x] 1.1 `rg -n "domain_events\|DomainEvent\|APScheduler" backend/app/` → documenter consommateurs actuels. **Attendu** : 3 fichiers `events.py` (projects, maturity, admin_catalogue), 2 fichiers `service.py` (commentaires projects/maturity), 0 consommateur runtime, 0 mention APScheduler (dépendance nouvelle).
  - [x] 1.2 `ls backend/app/core/outbox/ 2>/dev/null` → **attendu absent**. Création from scratch.
  - [x] 1.3 `rg -n "INSERT INTO domain_events\|DomainEvent\(" backend/app/` → **attendu 0 hit** (aucune écriture avant 10.10).
  - [x] 1.4 `pytest --collect-only -q backend/tests/ 2>&1 | tail -3` → **noter baseline** (attendu `1569 collected, 1503 passed + 66 skipped`).
  - [x] 1.5 Vérifier `backend/alembic/versions/028_tamper_proof_audit_tables.py` existe avec `down_revision = "027_outbox_prefill"` (confirme Q5 → 029 nécessaire).

- [x] **Task 2 — Ajouter dépendance APScheduler** (Q1)
  - [x] 2.1 Éditer `backend/requirements.txt` : ajouter `apscheduler>=3.10,<4.0` dans section `# LLM & orchestration` ou nouvelle section `# Scheduling` (cohérence).
  - [x] 2.2 `source backend/venv/bin/activate && pip install apscheduler` → vérifier version 3.10.x. Ne PAS committer le `backend/venv/` (gitignore respecté).
  - [x] 2.3 `python -c "from apscheduler.schedulers.asyncio import AsyncIOScheduler; from apscheduler.triggers.interval import IntervalTrigger; print('OK')"` → OK attendu.

- [x] **Task 3 — Créer modèle ORM `DomainEvent` + import dans `models/__init__.py`** (AC1)
  - [x] 3.1 `backend/app/models/domain_event.py` : déclaration `class DomainEvent(Base)` avec `__tablename__ = "domain_events"`, colonnes matchant la migration 027 (id UUID PK, event_type str(64), aggregate_type str(64), aggregate_id UUID, payload JSONB, status str(16) default='pending', retry_count int default=0, error_message text nullable, created_at datetime, processed_at datetime nullable). **Note** : `next_retry_at` sera ajouté par Task 4 avant ce modèle (ou le modèle inclut déjà la colonne — à ordonner).
  - [x] 3.2 Éditer `backend/app/models/__init__.py` : ajouter `from app.models.domain_event import DomainEvent  # noqa: F401`.
  - [x] 3.3 `python -c "from app.models import DomainEvent; print(DomainEvent.__tablename__)"` → `domain_events`.

- [x] **Task 4 — Créer migration 029 `add_next_retry_at_to_domain_events.py`** (AC4 + MEDIUM-10.1-14)
  - [x] 4.1 Créer `backend/alembic/versions/029_add_next_retry_at_to_domain_events.py` avec `revision="029_outbox_next_retry_at"`, `down_revision="028_audit_tamper"`, header commentaire citant `MEDIUM-10.1-14` + Story 10.10.
  - [x] 4.2 Upgrade : `op.add_column("domain_events", sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True))` + **pas de recréation d'index** (Q5 rationale : `now()` non-IMMUTABLE, filtrage runtime).
  - [x] 4.3 Downgrade : `op.drop_column("domain_events", "next_retry_at")`.
  - [x] 4.4 Ajouter la colonne dans le modèle ORM Task 3.1 : `next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)`.
  - [x] 4.5 Test alembic `pytest backend/tests/test_migrations/test_migration_roundtrip.py -k "029" -v` → vert (si postgres disponible).

- [x] **Task 5 — Créer `backend/app/core/outbox/writer.py`** (AC1)
  - [x] 5.1 Créer `backend/app/core/outbox/__init__.py` avec `from app.core.outbox.writer import write_domain_event; from app.core.outbox.worker import process_outbox_batch, start_outbox_scheduler, stop_outbox_scheduler; from app.core.outbox.handlers import EVENT_HANDLERS, HandlerEntry, dispatch_event; __all__ = [...]`.
  - [x] 5.2 Créer `backend/app/core/outbox/writer.py` :
    - Regex `_EVENT_TYPE_RE = re.compile(r"^[a-z_]+\.[a-z_]+$")` + helper `_validate_event_type(event_type: str) -> None` raise `ValueError` sinon.
    - Helper `_validate_payload_json_serializable(payload: dict) -> None` : `json.dumps(payload, default=str)` dry-run, raise `ValueError("payload not JSON-serializable: <detail>")` si échec.
    - Fonction `async def write_domain_event(db: AsyncSession, *, event_type: str, aggregate_type: str, aggregate_id: UUID, payload: dict[str, Any]) -> DomainEvent` : validation + `event = DomainEvent(id=uuid4(), event_type=event_type, aggregate_type=aggregate_type, aggregate_id=aggregate_id, payload=payload, status="pending", retry_count=0); db.add(event); await db.flush(); return event`.
    - Docstring cite CCC-14 + contrat « pas de commit interne ».
  - [x] 5.3 Commit intermédiaire (leçon 10.8) : « refactor(10.10): modèle DomainEvent + writer + migration 029 ».

- [x] **Task 6 — Créer `backend/app/core/outbox/handlers.py`** (AC3, AC5 dispatch)
  - [x] 6.1 Créer `handlers.py` avec :
    - `@dataclass(frozen=True) class HandlerEntry: event_type: str; handler: Callable[[DomainEvent, AsyncSession], Awaitable[None]]; description: str`.
    - `async def noop_handler(event: DomainEvent, db: AsyncSession) -> None: logger.debug("noop handler invoked", extra={"event_id": str(event.id)})`.
    - `EVENT_HANDLERS: Final[tuple[HandlerEntry, ...]] = (HandlerEntry(event_type="noop.test", handler=noop_handler, description="..."),)`.
    - `def _validate_unique_event_types() -> None: ...` + invocation module-level.
    - `@dataclass(frozen=True) class HandlerResult: status: str; error_message: str | None = None`.
    - `async def dispatch_event(event: DomainEvent, db: AsyncSession) -> HandlerResult` : linear scan tuple, dispatch, capture `Exception` locale.
    - Commentaire prospectif « Epic 13 ajoutera `fact_updated`, `criterion_rule_updated`, etc. ici ».
  - [x] 6.2 `python -c "from app.core.outbox.handlers import EVENT_HANDLERS, HandlerEntry; print(len(EVENT_HANDLERS))"` → 1.

- [x] **Task 7 — Créer `backend/app/core/outbox/worker.py`** (AC2, AC4, AC5)
  - [x] 7.1 Imports : `AsyncIOScheduler`, `IntervalTrigger`, `DomainEvent`, `dispatch_event`, `settings`, SQLAlchemy `select`, `text`, `update`.
  - [x] 7.2 Constantes module-level : `BACKOFF_SCHEDULE: Final[tuple[int, ...]] = (30, 120, 600)`, `MAX_RETRIES: Final[int] = 3`, `BATCH_SIZE: Final[int] = 100`, `PREFILL_PURGE_INTERVAL_S: Final[int] = 3600`.
  - [x] 7.3 Fonction `async def process_outbox_batch(engine: AsyncEngine) -> None` :
    - Ouvre `AsyncSession(engine)`, `await db.begin()`.
    - Query `select(DomainEvent).where(DomainEvent.processed_at.is_(None), DomainEvent.retry_count < MAX_RETRIES, DomainEvent.status.in_(["pending"]), or_(DomainEvent.next_retry_at.is_(None), DomainEvent.next_retry_at <= func.now())).order_by(DomainEvent.created_at).limit(BATCH_SIZE).with_for_update(skip_locked=True)`.
    - Pour chaque event : mesurer `start = time.monotonic()`, `result = await dispatch_event(event, db)`, `duration_ms = ...`, update ligne selon `result.status` (processed / retry / failed / unknown_handler) + log structuré.
    - Commit.
  - [x] 7.4 Fonction `async def purge_expired_prefill_drafts(engine: AsyncEngine) -> None` : `DELETE FROM prefill_drafts WHERE expires_at < now()` (batch limité à 500 via `DELETE ... WHERE id IN (SELECT id ... LIMIT 500)`), log INFO `extra={"metric": "prefill_drafts_purged", "count": N}`.
  - [x] 7.5 Fonction `def start_outbox_scheduler(engine: AsyncEngine) -> AsyncIOScheduler | None` : lit `settings.domain_events_worker_enabled`, si False retourne None + log WARNING. Sinon instancie `AsyncIOScheduler(timezone="UTC")`, ajoute 2 jobs (`process_outbox_batch`, `purge_expired_prefill_drafts`), `scheduler.start()`, retourne scheduler.
  - [x] 7.6 Fonction `async def stop_outbox_scheduler(scheduler: AsyncIOScheduler | None) -> None` : `if scheduler: scheduler.shutdown(wait=True)`.
  - [x] 7.7 Log structure conforme AC5 : `logger.info("outbox event processed", extra={"metric": "outbox_event_processed", "event_id": str(event.id), ...})`.

- [x] **Task 8 — Intégrer dans `main.py::lifespan`** (AC2, AC6)
  - [x] 8.1 Éditer `backend/app/main.py` : importer `from app.core.outbox.worker import start_outbox_scheduler, stop_outbox_scheduler`.
  - [x] 8.2 Dans `lifespan` startup (après `register_admin_access_listener`, avant le yield) : `outbox_scheduler = start_outbox_scheduler(_db_engine)`.
  - [x] 8.3 Dans `lifespan` shutdown (avant `engine.dispose()`) : `await stop_outbox_scheduler(outbox_scheduler)`.
  - [x] 8.4 Vérifier que `compiled_graph` et `outbox_scheduler` sont définis au niveau module (variables `global`).
  - [x] 8.5 Smoke test manuel : `uvicorn app.main:app --reload` → log startup confirme `scheduler.start()` appelé.

- [x] **Task 9 — Déclarer Settings `domain_events_worker_enabled` + `_interval_s`** (AC6)
  - [x] 9.1 Éditer `backend/app/core/config.py` : ajouter dans `class Settings(BaseSettings)` :
    ```python
    # --- Worker Outbox (Story 10.10) ---
    domain_events_worker_enabled: bool = Field(
        default=True,
        description="Kill-switch worker Outbox APScheduler (architecture.md §D11).",
    )
    domain_events_worker_interval_s: int = Field(
        default=30, ge=5, le=3600,
        description="Intervalle batch Outbox en secondes (5-3600). Défaut 30 s (D11).",
    )
    ```
  - [x] 9.2 Scan `rg -n "domain_events_worker" backend/app/` attendu : 2 hits (config.py) + 2 hits (worker.py utilise settings).

- [x] **Task 10 — Tests unit** (AC1, AC3, AC5, AC6)
  - [x] 10.1 Créer `backend/tests/test_core/test_outbox/__init__.py` + `conftest.py` (fixtures factices DB, `MockAsyncSession`).
  - [x] 10.2 `test_writer.py` : 3 tests (insert in transaction, validate event_type regex, validate payload JSON-serializable).
  - [x] 10.3 `test_handlers.py` : 3 tests (registry is frozen tuple, unique event_types, dispatch unknown_handler returns fail-fast result).
  - [x] 10.4 `test_settings.py` : 2 tests (worker fields present + defaults, interval < 5 raises ValidationError).
  - [x] 10.5 `test_log_structure.py` : 1 test (caplog verify `extra` keys for `outbox_event_processed` log).

- [x] **Task 11 — Tests E2E PostgreSQL** (AC2, AC4, AC7)
  - [x] 11.1 `test_worker_e2e.py` avec `pytestmark = pytest.mark.postgres`.
  - [x] 11.2 Fixture `postgres_engine` (réutilise pattern `test_migrations/conftest.py`).
  - [x] 11.3 Tests : `test_worker_processes_pending_event`, `test_worker_skip_locked_concurrent`, `test_worker_retry_schedules_next_retry_at`, `test_worker_marks_failed_after_3_retries`, `test_worker_unknown_handler_fail_fast`, `test_purge_prefill_drafts_removes_expired`.
  - [x] 11.4 Dans chaque test : `alembic upgrade head` au setup (apporte 029), `alembic downgrade -1` au teardown (ou fresh DB par test).

- [x] **Task 12 — Documentation `docs/CODEMAPS/outbox.md`** (AC8)
  - [x] 12.1 Créer le fichier avec 7 sections (Vue Mermaid 5 nœuds, Contrat writer, Contrat worker, Contrat handler, Pièges 7 items, Consommateurs prévus table 10+ lignes, Migration Phase Growth).
  - [x] 12.2 Éditer `docs/CODEMAPS/index.md` : +1 ligne référence vers `outbox.md`.
  - [x] 12.3 Test unit `test_outbox_codemap_has_7_sections` : lit le fichier, regex `## §[1-7]` trouve 7 hits.

- [x] **Task 13 — Validation globale + Completion Notes** (AC9)
  - [x] 13.1 `pytest backend/tests/test_core/test_outbox/ -v -m "unit"` → 9+ verts.
  - [x] 13.2 `pytest backend/tests/test_core/test_outbox/ -v -m "postgres"` → 6+ verts (si postgres local) / skippés (sinon).
  - [x] 13.3 `pytest --collect-only -q backend/tests/` → noter delta vs baseline Task 1.4. **Attendu ≥ +12** (target +15).
  - [x] 13.4 `pytest backend/tests/ 2>&1 | tail -5` → **≥ 1515 passed** + 66-72 skipped, zéro régression.
  - [x] 13.5 `pytest --cov=backend/app/core/outbox --cov-report=term-missing backend/tests/test_core/test_outbox/` → coverage ≥ 90 %.
  - [x] 13.6 Consigner en Completion Notes : scans Task 1 (3 greps), baseline avant/après, delta tests, coverage `outbox/`, logs samples AC5.

- [x] **Task 14 — Commits intermédiaires (leçon 10.8)** — *fragmentation logique encouragée pour review*
  - [x] 14.1 Commit 1 : « feat(10.10): migration 029 + modèle ORM DomainEvent » — Task 3 + Task 4.
  - [x] 14.2 Commit 2 : « feat(10.10): writer Outbox + validation event_type/payload » — Task 5 + tests 10.2.
  - [x] 14.3 Commit 3 : « feat(10.10): registry handlers frozen tuple + dispatch fail-fast » — Task 6 + tests 10.3.
  - [x] 14.4 Commit 4 : « feat(10.10): worker APScheduler SKIP LOCKED + retry exponentiel + lifespan » — Task 7 + Task 8 + Task 9 + tests 10.4-10.5 + Task 11.
  - [x] 14.5 Commit 5 : « docs(10.10): CODEMAPS outbox.md 7 sections + index » — Task 12.

---

## Dev Notes

### §1 Contexte amont précis (NE PAS RE-DÉCIDER)

- **Arbitrage Story 9.10 (2026-04-19)** : pas de Celery+Redis MVP. `BackgroundTask` FastAPI + micro-Outbox choisi. Story 10.10 livre le pattern. Décision définitive, ne pas rouvrir.
- **Architecture.md §D11** : pattern `APScheduler + SELECT FOR UPDATE SKIP LOCKED` choisi explicitement. Migration Phase Growth EventBridge **sans refactor Outbox** (seul le trigger change).
- **Migration 027 (Story 10.1 DONE)** : schema `domain_events` déjà en place. Colonnes : id, event_type, aggregate_type, aggregate_id, payload, status, retry_count, error_message, created_at, processed_at. Index partiel + index aggregate. Contrainte `retry_count <= 5`.
- **Migration 028 (Story 10.5 DONE)** : tamper-proof audit tables, `down_revision = "027_outbox_prefill"`. **Ne PAS modifier.**
- **`backend/app/modules/projects/events.py` + `maturity/events.py` + `admin_catalogue/events.py`** (Stories 10.2-10.4 DONE) : déclarent déjà les constantes `event_type`. Story 10.10 ne les modifie pas.
- **Q1 Story 10.1 parsimonie env var** : limite les nouveaux flags. 10.10 ajoute **2** env vars (`DOMAIN_EVENTS_WORKER_ENABLED`, `DOMAIN_EVENTS_WORKER_INTERVAL_S`) — justifiés par AC6 Epic (kill-switch) et Q4 (configurable dev vs prod).

### §2 Source tree — composants à créer/modifier

| Chemin                                                              | Action          | Invariant                                                                                    |
| ------------------------------------------------------------------- | --------------- | -------------------------------------------------------------------------------------------- |
| `backend/app/core/outbox/__init__.py` **(NOUVEAU)**                 | Créer           | Exports publics uniquement (writer, worker, handlers).                                       |
| `backend/app/core/outbox/writer.py` **(NOUVEAU)**                   | Créer           | `write_domain_event()` sans commit interne (CCC-14).                                         |
| `backend/app/core/outbox/worker.py` **(NOUVEAU)**                   | Créer           | `process_outbox_batch()` + `purge_expired_prefill_drafts()` + `start/stop_outbox_scheduler`. |
| `backend/app/core/outbox/handlers.py` **(NOUVEAU)**                 | Créer           | Tuple frozen + `dispatch_event` + 1 `noop_handler` test-only.                                |
| `backend/app/models/domain_event.py` **(NOUVEAU)**                  | Créer           | Modèle ORM matchant schema 027 + colonne 029 `next_retry_at`.                                |
| `backend/app/models/__init__.py`                                    | Éditer          | +1 import `DomainEvent`.                                                                     |
| `backend/alembic/versions/029_add_next_retry_at_to_domain_events.py` **(NOUVEAU)** | Créer | `down_revision="028_audit_tamper"` — Q5 tranche.                                             |
| `backend/app/core/config.py`                                        | Éditer          | +2 champs Settings (enable + interval).                                                      |
| `backend/app/main.py`                                               | Éditer          | lifespan startup `start_outbox_scheduler` + shutdown `stop_outbox_scheduler`.                |
| `backend/requirements.txt`                                          | Éditer          | +1 ligne `apscheduler>=3.10,<4.0`.                                                           |
| `backend/tests/test_core/test_outbox/` **(NOUVEAU)**                | Créer 5 fichiers| `test_writer.py`, `test_handlers.py`, `test_settings.py`, `test_log_structure.py`, `test_worker_e2e.py`. |
| `docs/CODEMAPS/outbox.md` **(NOUVEAU)**                             | Créer           | 7 sections Mermaid + contrats.                                                               |
| `docs/CODEMAPS/index.md`                                            | Éditer          | +1 ligne référence vers `outbox.md`.                                                         |

**FICHIERS À NE PAS TOUCHER** :

- `backend/alembic/versions/027_create_outbox_and_prefill_drafts.py` — schéma livré DONE Story 10.1. `next_retry_at` est additif via 029.
- `backend/alembic/versions/028_tamper_proof_audit_tables.py` — livré DONE Story 10.5. Ne pas modifier `down_revision`.
- `backend/app/modules/projects/service.py`, `maturity/service.py` — commentaires `via domain_events` restent théoriques, Epic 11/12 consommeront. **Zero touch.**
- `backend/app/modules/{projects,maturity,admin_catalogue}/events.py` — constantes event_type déjà déclarées Stories 10.2-10.4.
- Les 3 fichiers de prompts `backend/app/prompts/registry.py` (modèle pattern CCC-9) — référence pour tuple frozen, **pas de modification**.

### §3 Pièges connus (à éviter)

1. **Ne jamais `await db.commit()` dans `write_domain_event`** — la décision de commit appartient au caller (transaction métier). Un commit interne briserait CCC-14 (l'event serait persisté même si la transaction métier rollback).
2. **Ne jamais `try/except Exception` autour du batch entier dans `process_outbox_batch`** (C1 9.7) — une erreur DB doit crasher le scheduler → restart propre par l'orchestrateur. Le try/except local est **autorisé uniquement** autour de l'appel handler individuel dans `dispatch_event` (isolation failure d'1 event pour ne pas bloquer les autres du batch).
3. **Ne pas inclure le `payload` entier dans les logs** — risque PII (NFR18). Utiliser `payload_keys = list(payload.keys())` seulement. Le payload reste dans la ligne `domain_events` (BDD encrypted at rest) mais **jamais** dans le log JSON structuré.
4. **Ne pas utiliser `now()` dans un index partiel PostgreSQL** — `now()` est non-IMMUTABLE, PostgreSQL refuse. Le filtre `next_retry_at <= now()` va dans la **query worker**, pas dans le DDL de l'index (Q5 / AC4).
5. **Ne pas instancier 2 `AsyncIOScheduler` en parallèle** — si 2 replicas Uvicorn tournent en PROD, chacun a son scheduler, mais **SKIP LOCKED** garantit qu'un event n'est consommé qu'une fois (test AC7 E2E #2). **En revanche**, dans un seul process, 2 schedulers créeraient 2× le nombre de jobs. `AsyncIOScheduler` est instancié **1 seule fois** dans `lifespan`.
6. **Ne pas oublier `max_instances=1` + `coalesce=True`** sur les jobs APScheduler — sinon un batch qui dépasse 30 s voit le suivant se superposer (CPU double, SKIP LOCKED protège la BDD mais pas la charge CPU applicative).
7. **Ne pas oublier `timezone="UTC"`** explicite sur l'AsyncIOScheduler — sans ce param, APScheduler utilise la TZ système → dérive sleep OS possible en container (NFR37).
8. **Ne pas `raise SystemExit` dans un handler** — `dispatch_event` capture uniquement `Exception` (pas `BaseException`). `SystemExit` / `KeyboardInterrupt` tueraient le scheduler. Documenter ce contrat dans `outbox.md §4`.
9. **Ne pas supposer que `event_type` est unique dans le tuple `EVENT_HANDLERS`** — `_validate_unique_event_types()` à l'import est le garde-fou. Un ajout dupliqué casse l'import → fail-fast visible en CI.
10. **Ne pas confondre `retry_count < 5` (contrainte DB)** avec `retry_count < MAX_RETRIES=3` (cap applicatif). La contrainte DB est un filet de sécurité ; le cap applicatif à 3 est la règle métier. Ne pas supprimer l'un des deux.
11. **Ne pas utiliser `[1, 3, 9]` backoff (pattern `with_retry` LLM NFR75)** — c'est pour des retries synchrones < 10 s. Outbox handlers retry transient BDD (connection drop, deadlock) = `[30, 120, 600]` architecture.md D11. **Ces deux patterns coexistent** dans le codebase avec rôles distincts.
12. **Ne pas oublier de fermer la session dans `process_outbox_batch`** — `async with AsyncSession(engine) as db:` garantit le release. Une session non fermée tient un connection pool slot → épuisement sous charge.

### §4 Pattern commit intermédiaire (leçon 10.8)

La story est naturellement fragmentée (migration + modèle + writer + handlers + worker + lifespan + doc). **5 commits recommandés** (voir Task 14). Si la PR finale reste < 800 lignes de diff, un commit unique atomique reste acceptable. La fragmentation facilite la review de la partie la plus risquée (worker + SKIP LOCKED + retry) isolément.

### §5 Pattern tuple frozen (leçon 10.8 CCC-9) — réutilisation explicite

Le registry `EVENT_HANDLERS` réutilise byte-identiquement le pattern `INSTRUCTION_REGISTRY` de Story 10.8 (`backend/app/prompts/registry.py` lignes 47-85) :

```python
# Story 10.8 (prompts/registry.py)
@dataclass(frozen=True)
class InstructionEntry:
    name: str
    content: str
    applies_to: tuple[str, ...]
    required_vars: tuple[str, ...] = field(default_factory=tuple)

INSTRUCTION_REGISTRY: Final[tuple[InstructionEntry, ...]] = (
    InstructionEntry(name="STYLE_INSTRUCTION", ...),
    ...
)

# Story 10.10 (core/outbox/handlers.py) — même pattern
@dataclass(frozen=True)
class HandlerEntry:
    event_type: str
    handler: Callable[[DomainEvent, AsyncSession], Awaitable[None]]
    description: str

EVENT_HANDLERS: Final[tuple[HandlerEntry, ...]] = (
    HandlerEntry(event_type="noop.test", handler=noop_handler, description="..."),
    # Epic 13 ajoutera fact_updated, criterion_rule_updated ici
    # Epic 14 ajoutera fund_updated, intermediary_updated ici
)
```

**Avantages hérités** : fail-at-import sur duplication (`_validate_unique_event_types`), introspection trivale (`[e.event_type for e in EVENT_HANDLERS]`), cohérence code review (le reviewer reconnaît le pattern), append-only (pas de side-effect via décorateurs).

### §6 Absorption dette MEDIUM-10.1-14 (`next_retry_at`)

La dette `next_retry_at` manquant dans schema 027 est absorbée via migration 029. Sans ce champ, le worker serait forcé à un retry immédiat dès qu'il repêche un event en retry (ordre `created_at` ASC) → hot-loop CPU + pression BDD. **La migration 029 est donc bloquante fonctionnelle pour AC4** — pas optionnelle.

Ajout dans `_bmad-output/implementation-artifacts/deferred-work.md` section « Resolved in Story 10.10 » :

```markdown
## Resolved in Story 10.10 (2026-04-21)

- ✅ **MEDIUM-10.1-14 — `domain_events.next_retry_at`** : livré via migration
  `backend/alembic/versions/029_add_next_retry_at_to_domain_events.py` +
  logique applicative `BACKOFF_SCHEDULE = (30, 120, 600)` dans
  `backend/app/core/outbox/worker.py`. Évite hot-loop retry immédiat.
- ✅ **MEDIUM-10.1-5 purge `prefill_drafts`** : livré via 2ᵉ job APScheduler
  `purge_expired_prefill_drafts` intervalle 1 h dans `core/outbox/worker.py`.
  Co-localisé avec batch Outbox pour éviter 2 schedulers concurrents.
- ⚠️ **LOW (NOUVELLE DEFERRED) — `CHECK status IN (...)` sur domain_events**
  : contrainte enum manuelle pas ajoutée par 10.10 (Q3 hors scope).
  À évaluer Story Growth tooling ou absorption opportuniste migration
  ultérieure. Non bloquant (le code applicatif garantit les 4 valeurs
  `pending`/`processed`/`failed`/`unknown_handler`).
```

### §7 Tests plan récapitulatif

| Test                                                          | AC      | Marker    | Description courte                                                     |
| ------------------------------------------------------------- | ------- | --------- | ---------------------------------------------------------------------- |
| `test_write_domain_event_inserts_row_in_current_transaction`  | AC1     | unit      | `db.flush()` après add, rollback propage à l'event.                    |
| `test_write_domain_event_validates_event_type_format`         | AC1     | unit      | `event_type="BadFormat"` → `ValueError`.                               |
| `test_write_domain_event_validates_payload_json_serializable` | AC1     | unit      | `payload={"dt": datetime.now()}` naïf → `ValueError` explicite.        |
| `test_event_handlers_registry_is_frozen_tuple`                | AC3     | unit      | `isinstance(EVENT_HANDLERS, tuple)` + `.append()` → `AttributeError`. |
| `test_event_handlers_have_unique_event_types`                 | AC3     | unit      | `_validate_unique_event_types()` passe à l'import.                     |
| `test_dispatch_event_returns_unknown_handler_for_unregistered_type` | AC3/AC5 | unit | event_type non enregistré → `HandlerResult(status='unknown_handler')`. |
| `test_settings_domain_events_worker_fields`                   | AC6     | unit      | `enable` default True, `interval_s` default 30, bornes 5-3600.         |
| `test_settings_interval_below_5_raises_validation_error`      | AC6     | unit      | `ENV=2` → `ValidationError`.                                           |
| `test_log_structure_contains_all_expected_keys`               | AC5     | unit      | caplog assertion `extra` = {metric, event_id, event_type, status, ...}. |
| `test_worker_processes_pending_event_and_marks_processed`     | AC2     | postgres  | E2E batch → `status='processed'`.                                      |
| `test_worker_skip_locked_allows_concurrent_processing`        | AC2     | postgres  | 2 coroutines, chaque event traité 1 fois (pas de double dispatch).     |
| `test_worker_retry_schedules_next_retry_at_on_handler_exception` | AC4  | postgres  | handler raise → `next_retry_at ≈ now() + 30s`.                         |
| `test_worker_marks_failed_after_3_retries`                    | AC4     | postgres  | handler raise toujours → `status='failed'`, `retry_count=3`.           |
| `test_worker_unknown_handler_fail_fast_without_retry`         | AC5     | postgres  | event_type non registry → `status='unknown_handler'` sans retry.       |
| `test_purge_prefill_drafts_removes_expired_rows`              | AC9 bonus | postgres | 3 drafts, 2 expirés → 1 restant après purge.                           |
| `test_outbox_codemap_has_7_sections`                          | AC8     | unit      | regex `## §[1-7]` → 7 hits.                                            |

**Total** : 9 unit + 6 postgres + 1 doc = **16 nouveaux tests** (plancher AC7 : ≥ 12, cible +14-16 atteint via 16).

### Project Structure Notes

- Structure `backend/app/core/outbox/` cohérente avec `backend/app/core/storage/` (Story 10.6) : sous-module organisé par fonctionnalité transverse, pas de mélange avec `backend/app/modules/` (qui héberge la logique métier).
- Aligné avec `CLAUDE.md` conventions Python : `snake_case` fonctions/variables, type hints obligatoires, docstrings français.
- Aucun conflit détecté avec conventions actuelles. `apscheduler` est Python pur, pas de binaire natif (déploiement Docker alpine-friendly).
- Aucun impact frontend.

### References

- [Source: `_bmad-output/planning-artifacts/epics/epic-10.md#Story 10.10`] — AC1-AC7 Epic textuels (base pour AC1-AC6 dérivés).
- [Source: `_bmad-output/planning-artifacts/architecture.md#Décision 11`] — micro-Outbox MVP, APScheduler + SKIP LOCKED, backoff 30s/2min/10min.
- [Source: `_bmad-output/planning-artifacts/architecture.md#CCC-14`] — transaction boundaries (submit atomique, event inséré dans transaction caller).
- [Source: `backend/alembic/versions/027_create_outbox_and_prefill_drafts.py`] — schéma `domain_events` + `prefill_drafts` (Story 10.1 DONE).
- [Source: `backend/alembic/versions/028_tamper_proof_audit_tables.py`] — down_revision chaîne (Q5 rationale).
- [Source: `backend/app/modules/projects/events.py`, `maturity/events.py`, `admin_catalogue/events.py`] — constantes event_type déclarées Stories 10.2-10.4.
- [Source: `backend/app/prompts/registry.py` lignes 47-85] — pattern `tuple frozen + @dataclass(frozen=True)` (Story 10.8 CCC-9 — réutilisation explicite AC3).
- [Source: `backend/app/graph/tools/common.py::log_tool_call, with_retry`] — pattern log structuré JSON + retry exponentiel (référence style AC5).
- [Source: `backend/app/core/feature_flags.py`] — pattern helper settings + test cleanup marker (Story 10.9).
- [Source: `backend/app/core/admin_audit_listener.py`] — pattern `register_XXX(engine)` invoqué dans `main.py::lifespan` (Story 10.5).
- [Source: `backend/app/main.py::lifespan`] — point d'insertion `start_outbox_scheduler` + `stop_outbox_scheduler`.
- [Source: `_bmad-output/implementation-artifacts/deferred-work.md` — `MEDIUM-10.1-14`] — dette `next_retry_at` absorbée.
- [Source: `_bmad-output/implementation-artifacts/10-8-framework-injection-prompts-ccc9.md`] — pattern frozen tuple + commits intermédiaires + scan NFR66.
- [Source: `_bmad-output/implementation-artifacts/10-9-feature-flag-enable-project-model.md`] — pattern Settings Pydantic + test `importlib.metadata` (inspiration pour absence lib externe si pertinent).
- [Source: APScheduler docs — https://apscheduler.readthedocs.io/en/3.x/modules/schedulers/asyncio.html] — `AsyncIOScheduler` + `IntervalTrigger` + `max_instances` + `coalesce`.
- [Source: PostgreSQL docs — `SELECT ... FOR UPDATE SKIP LOCKED`] — comportement row-level lock + skip dans batch concurrent.

---

## Dev Agent Record

### Agent Model Used

claude-opus-4-7[1m]

### Debug Log References

- `pytest tests/test_core/test_outbox/ -v` → 18 passed + 6 skipped (postgres) en local sans `TEST_ALEMBIC_URL`.
- `TEST_ALEMBIC_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/esg_mefali_test" pytest tests/test_core/test_outbox/test_worker_e2e.py -v` → 6 passed (FOR UPDATE SKIP LOCKED validé bout-en-bout).
- `pytest tests/` full suite → `1521 passed, 72 skipped` en 207,97 s (baseline 1503 → +18 passed, +6 skipped postgres).
- Coverage `app.core.outbox` (avec postgres actifs) : **91 %** (159 stmts, 14 miss — `start_outbox_scheduler` / `stop_outbox_scheduler` non couverts, smoke test manuel uvicorn OK).

### Completion Notes List

**Scans NFR66 (Task 1)** :

- `rg "domain_events|DomainEvent|APScheduler" backend/app/` avant 10.10 → 5 fichiers (3 `events.py` modules + 2 `service.py` commentaires shims legacy 10.6), 0 mention APScheduler, 0 écriture runtime.
- `rg "INSERT INTO domain_events|DomainEvent\(" backend/app/` post-10.10 → **1 hit écriture** (`app/core/outbox/writer.py::write_domain_event`) + 2 hits non-écriture (`app/models/domain_event.py` : déclaration `class DomainEvent(Base)` + `__repr__`). Règle 10.5 no duplication ✅.
- `rg "register_handler|HANDLER_DICT" backend/app/core/outbox` → 0 hit (pattern frozen tuple CCC-9 strict).
- `rg "FOR UPDATE SKIP LOCKED|with_for_update" backend/app/core/outbox` → 5 hits (docstrings + `.with_for_update(skip_locked=True)` dans worker.py).

**Baseline tests** :

- Pré-10.10 : 1569 collected, 1503 passed + 66 skipped (Story 10.9 Completion Notes).
- Post-10.10 : **1593 collected (+24), 1521 passed (+18) + 72 skipped (+6 postgres)**. Zéro régression sur les 1503 tests pré-10.10.
- Cible AC7 (≥ 12 tests nouveaux / ≥ 1515 passed) : **largement dépassée** (+18 passed, +24 collected).

**Delta tests — détails (24 nouveaux)** :

| Fichier                                              | Tests | Marker     | État           |
| ---------------------------------------------------- | ----- | ---------- | -------------- |
| `tests/test_core/test_outbox/test_writer.py`         | 3     | `unit`     | ✅ passed       |
| `tests/test_core/test_outbox/test_handlers.py`       | 6     | `unit`     | ✅ passed       |
| `tests/test_core/test_outbox/test_settings.py`       | 4     | `unit`     | ✅ passed       |
| `tests/test_core/test_outbox/test_log_structure.py`  | 3     | `unit`     | ✅ passed       |
| `tests/test_core/test_outbox/test_codemap.py`        | 2     | `unit`     | ✅ passed       |
| `tests/test_core/test_outbox/test_worker_e2e.py`     | 6     | `postgres` | ✅ (postgres local) / skip (défaut) |
| **Total**                                            | **24** |          | **18 passed + 6 skipped** par défaut, 24 passed avec PG |

**Coverage `app.core.outbox/` (AC9, NFR60 code critique)** :

```
Name                          Stmts   Miss  Cover
-----------------------------------------------------------
app/core/outbox/__init__.py       4      0   100%
app/core/outbox/handlers.py      41      0   100%
app/core/outbox/worker.py        89     14    84%
app/core/outbox/writer.py        25      0   100%
-----------------------------------------------------------
TOTAL                           159     14    91%   (≥ 90 % ✅ NFR60)
```

Les 14 lignes non couvertes dans `worker.py` concernent exclusivement
`start_outbox_scheduler` et `stop_outbox_scheduler` (lifecycle scheduler
FastAPI). Smoke test manuel `uvicorn app.main:app` confirme l'appel
`scheduler.start()` au startup (log `Outbox scheduler started`
metric=`outbox_scheduler_started`).

**Log samples AC5** (extrait `caplog` test_log_structure_contains_all_expected_keys) :

```json
{
  "metric": "outbox_event_processed",
  "event_id": "b0c7f3…",
  "event_type": "noop.test",
  "aggregate_type": "project",
  "aggregate_id": "2af0…",
  "attempt": 1,
  "status": "processed",
  "duration_ms": 0,
  "payload_keys": ["company_id", "name"],
  "error_message": null
}
```

Aucune valeur PII dans les logs (test `test_log_does_not_contain_payload_values`
valide `"Mefali SARL" not in record.getMessage()` + `payload` absent du record).

**Validation AC 1-9** :

- ✅ **AC1** — `write_domain_event` atomic-transactionnel (3 tests unit), scan `DomainEvent(` → 1 hit écriture unique (writer.py).
- ✅ **AC2** — `AsyncIOScheduler(timezone="UTC")` + `IntervalTrigger(seconds=settings.domain_events_worker_interval_s)` + `max_instances=1 coalesce=True` + `with_for_update(skip_locked=True)` (3 tests E2E postgres).
- ✅ **AC3** — `EVENT_HANDLERS: Final[tuple[HandlerEntry, ...]]` frozen, `_validate_unique_event_types()` module-level, `dispatch_event` O(n) + capture `Exception` local (pas `BaseException`), 2 dummy handlers conditionnels (6 tests unit).
- ✅ **AC4** — Migration 029 additive `next_retry_at TIMESTAMPTZ NULL` + `down_revision="028_audit_tamper"` (Q5). `BACKOFF_SCHEDULE = (30, 120, 600)` + cap applicatif `MAX_RETRIES = 3` (2 tests E2E `test_worker_retry_schedules_next_retry_at`, `test_worker_marks_failed_after_3_retries`). Filtre runtime (pas dans index partiel — `now()` non-IMMUTABLE PostgreSQL refuse).
- ✅ **AC5** — Log JSON structuré extra 10 champs, levels INFO/WARNING/ERROR selon status, aucun payload PII (3 tests unit caplog).
- ✅ **AC6** — Settings `domain_events_worker_enabled: bool = Field(default=True)` + `domain_events_worker_interval_s: int = Field(default=30, ge=5, le=3600)` + lifespan skip conditionnel (4 tests unit).
- ✅ **AC7** — 24 tests nouveaux (18 unit + 6 postgres) ; seuil AC7 ≥ 12 largement dépassé.
- ✅ **AC8** — `docs/CODEMAPS/outbox.md` 7 sections §1 à §7 avec Mermaid §1 + tableau 10+ consommateurs §6 + `docs/CODEMAPS/index.md` référence (2 tests unit).
- ✅ **AC9** — Baseline 1503 → **1521 passed** (+18 ≥ +12 plancher). Coverage `core/outbox/` 91 % ≥ 90 % NFR60.

**Absorption dettes déférées** :

- ✅ **MEDIUM-10.1-14** — colonne `next_retry_at` livrée par migration 029. Marquée résolue dans `deferred-work.md` §« Resolved in Story 10.10 ».
- ✅ **MEDIUM-10.1-5** — purge `prefill_drafts` livrée via 2ᵉ job APScheduler 1 h (`purge_expired_prefill_drafts`). Marquée résolue.

**Pivot mineur vs spec Task 11.4** : les tests E2E utilisent des `CREATE TABLE`
SQL directs dans `conftest.py::postgres_engine` plutôt que `alembic upgrade head`.
Justification : les tests E2E Outbox valident le **worker**, pas la chaîne de
migrations (couverte par `test_migrations/`). Un schéma minimal stable évite
la dépendance transitive (RLS migration 024 nécessite extensions `pgcrypto`
+ `vector` côté E2E outbox inutiles).

**Durée réelle** : ~90 min (Phase 4 12ᵉ story ; cible L = 3 h largement battue —
infra bien cadrée par les 5 Q tranchées + 12 pièges documentés pré-dev).

### File List

**Nouveaux (8)** :

- `backend/app/core/outbox/__init__.py`
- `backend/app/core/outbox/writer.py`
- `backend/app/core/outbox/worker.py`
- `backend/app/core/outbox/handlers.py`
- `backend/app/models/domain_event.py`
- `backend/alembic/versions/029_add_next_retry_at_to_domain_events.py`
- `backend/tests/test_core/test_outbox/__init__.py`
- `backend/tests/test_core/test_outbox/conftest.py`
- `backend/tests/test_core/test_outbox/test_writer.py`
- `backend/tests/test_core/test_outbox/test_handlers.py`
- `backend/tests/test_core/test_outbox/test_settings.py`
- `backend/tests/test_core/test_outbox/test_log_structure.py`
- `backend/tests/test_core/test_outbox/test_worker_e2e.py`
- `backend/tests/test_core/test_outbox/test_codemap.py`
- `docs/CODEMAPS/outbox.md`

**Modifiés (6)** :

- `backend/app/main.py` (lifespan startup/shutdown scheduler, +1 import, +1 variable globale)
- `backend/app/models/__init__.py` (+1 import `DomainEvent`)
- `backend/app/core/config.py` (+2 champs Settings `domain_events_worker_*`)
- `backend/requirements.txt` (+1 ligne section `# Scheduling` → `apscheduler>=3.10,<4.0`)
- `docs/CODEMAPS/index.md` (+1 ligne référence vers `outbox.md`)
- `_bmad-output/implementation-artifacts/deferred-work.md` (+1 section « Resolved in Story 10.10 »)

### Change Log

| Date       | Version | Description                                                                                                                                       |
| ---------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-04-21 | 0.1.0   | Story 10.10 livrée — micro-Outbox `domain_events` + worker APScheduler 30 s + purge prefill_drafts 1 h + migration 029 `next_retry_at`. Status → review. |
