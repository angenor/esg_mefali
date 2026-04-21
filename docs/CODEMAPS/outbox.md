# Micro-Outbox `domain_events` — pattern événementiel transactionnel

> Source : Story 10.10 (2026-04-21) — architecture.md §D11 « micro-Outbox MVP ».
> Consommateurs prévus : Epic 11-14 (handlers métier réels).

## §1 Vue d'ensemble

Le **pattern Outbox** garantit l'atomicité entre une mutation métier (ex.
« créer un projet ») et la **publication d'un événement** (ex.
`project.created`). En MVP, aucun message broker n'est déployé (Clarif. 1
« pas de Redis »). La cohérence est obtenue via une **table transactionnelle
`domain_events`** consommée par un **worker APScheduler + SELECT FOR UPDATE
SKIP LOCKED** (PostgreSQL natif).

```mermaid
flowchart LR
    S[Service métier] -->|1. write_domain_event<br/>(dans transaction)| T[(domain_events<br/>status=pending)]
    W[AsyncIOScheduler<br/>process_outbox_batch 30s] -->|2. SELECT FOR UPDATE<br/>SKIP LOCKED| T
    W -->|3. dispatch_event| H{EVENT_HANDLERS<br/>frozen tuple}
    H -->|4a. processed| T
    H -->|4b. retry<br/>next_retry_at=now+30s| T
    H -->|4c. failed<br/>after 3 retries| T
    H -->|4d. unknown_handler<br/>fail-fast| T
```

**5 briques** :

1. **writer** (`app.core.outbox.writer`) — `write_domain_event(db, ...)` : insert
   dans la transaction courante du caller, **pas de commit interne** (CCC-14).
2. **table** `domain_events` — schéma livré migration `027_outbox_prefill`, colonne
   `next_retry_at` ajoutée par migration `029_outbox_next_retry_at`.
3. **worker** (`app.core.outbox.worker.process_outbox_batch`) — intervalle 30 s
   configurable, `max_instances=1`, `coalesce=True`, `timezone=UTC`.
4. **handlers** (`app.core.outbox.handlers`) — `EVENT_HANDLERS:
   Final[tuple[HandlerEntry, ...]]` (pattern CCC-9 Story 10.8), dispatch O(n).
5. **scheduler lifecycle** — `start_outbox_scheduler(engine)` dans
   `main.py::lifespan` startup, `stop_outbox_scheduler(...)` au shutdown.

---

## §2 Contrat writer — `write_domain_event`

```python
await write_domain_event(
    db,                                   # AsyncSession en transaction ouverte
    event_type="project.created",        # regex ^[a-z_]+\.[a-z_]+$
    aggregate_type="project",
    aggregate_id=project.id,
    payload={"company_id": str(company.id), "name": project.name},
)
```

**Règle d'or** : le writer **n'appelle jamais `db.commit()`**. La décision de
commit appartient au caller (transaction métier). Cela garantit **CCC-14
atomicité** : si le caller `raise` après l'appel, la transaction rollback
propage à la ligne insérée.

**Validations fail-fast** :

- `event_type` → regex `^[a-z_]+\.[a-z_]+$`. Un format `BadFormat` raise
  `ValueError` immédiatement.
- `payload` → dry-run `json.dumps(payload)`. Une `datetime` naïve ou un `set`
  raise `ValueError("payload not JSON-serializable: …")` avec un hint
  (« convert datetimes to ISO strings, sets to lists »).

**Unicité** : scan CI `rg "INSERT INTO domain_events|DomainEvent\(" backend/app`
doit renvoyer **1 hit** (writer.py uniquement). Aucune écriture hors writer
(règle d'or 10.5 no duplication).

---

## §3 Contrat worker — `process_outbox_batch`

```python
# Job APScheduler auto-invoqué toutes les 30 s (settings.domain_events_worker_interval_s)
async def process_outbox_batch(engine: AsyncEngine) -> None:
    async with AsyncSession(engine, expire_on_commit=False) as db:
        stmt = (
            select(DomainEvent)
            .where(
                DomainEvent.processed_at.is_(None),
                DomainEvent.retry_count < MAX_RETRIES,   # 3 applicatif
                DomainEvent.status == "pending",
                or_(DomainEvent.next_retry_at.is_(None),
                    DomainEvent.next_retry_at <= func.now()),
            )
            .order_by(DomainEvent.created_at)
            .limit(BATCH_SIZE)                            # 100
            .with_for_update(skip_locked=True)            # ← pattern multi-process
        )
        events = (await db.execute(stmt)).scalars().all()
        for event in events:
            await _process_single_event(db, event)
        await db.commit()                                 # release verrous row-level
```

**Multi-process safe** : en PROD avec N replicas Uvicorn/gunicorn, chaque
réplica a son scheduler ; `FOR UPDATE SKIP LOCKED` garantit qu'un event
verrouillé par A est skippé par B (pas bloqué). Le verrou est libéré au commit
final.

**Retry exponentiel** — `BACKOFF_SCHEDULE = (30, 120, 600)` secondes. Sur
échec du handler :

1. `retry_count += 1`, `error_message = f"{ExceptionType}: {msg}"[:500]`.
2. Si `retry_count < MAX_RETRIES` (3) → `next_retry_at = now() +
   BACKOFF_SCHEDULE[retry_count - 1]`, `status` reste `pending`.
3. Si `retry_count >= MAX_RETRIES` → `status = 'failed'`, `processed_at = now()`,
   sort de l'index partiel. Consultable via `SELECT ... WHERE status='failed'`.

**Configuration** (Settings Pydantic, Story 10.10 AC6) :

| Env var                              | Défaut | Bornes   | Description                                 |
| ------------------------------------ | ------ | -------- | ------------------------------------------- |
| `DOMAIN_EVENTS_WORKER_ENABLED`       | `true` | bool     | Kill-switch (debug DEV). Lu au startup.     |
| `DOMAIN_EVENTS_WORKER_INTERVAL_S`    | `30`   | `[5, 3600]` | Intervalle batch APScheduler en secondes. |

---

## §4 Contrat handler

```python
async def mon_handler(event: DomainEvent, db: AsyncSession) -> None:
    # Code idempotent : rejouer le même event = même résultat.
    ...
```

**Règles** :

- **Idempotent** — le worker peut re-consommer un event après un retry. Le
  handler doit tolérer N exécutions sans effet cumulatif (ex. `ON CONFLICT DO
  NOTHING`, `UPDATE … WHERE status != 'done'`, etc.).
- **Raise `Exception`** → retry. Le worker capture localement dans
  `dispatch_event` (C1 9.7 : pas de catch-all autour du batch entier).
- **Return `None`** → succès (`status='processed'`).
- **Ne jamais `raise SystemExit` / `KeyboardInterrupt`** — ces `BaseException`
  propagent au scheduler et tuent le process.

**Enregistrement** : ajouter un bloc dans `EVENT_HANDLERS` (pattern byte-
identique à `INSTRUCTION_REGISTRY` Story 10.8) :

```python
EVENT_HANDLERS: Final[tuple[HandlerEntry, ...]] = (
    HandlerEntry(event_type="noop.test", handler=noop_handler, description="..."),
    # Epic 13 :
    HandlerEntry(event_type="fact.updated", handler=invalidate_referential_verdicts,
                 description="AR-D3 cache invalidation"),
    ...
)
```

Un `event_type` dupliqué provoque un **fail-at-import** via
`_validate_unique_event_types()`.

---

## §5 Pièges (anti-patterns documentés)

1. **`try/except Exception` autour du batch entier** (C1 9.7) : interdit. Une
   erreur BDD doit crasher le scheduler → restart propre par l'orchestrateur.
   Le try/except est **local** dans `dispatch_event` (isolation handler
   individuel).
2. **Payload PII dans les logs** (NFR18) : interdit. Seul `payload_keys =
   sorted(payload.keys())` est loggué. Les valeurs restent dans la ligne
   `domain_events` (BDD encrypted at rest).
3. **`now()` dans un index partiel PostgreSQL** : `now()` est non-IMMUTABLE,
   PostgreSQL refuse. Le filtre `next_retry_at <= now()` vit dans la query
   worker, **pas dans le DDL de l'index** (workaround documenté dans la
   migration 029).
4. **Handler non-idempotent** : un retry re-joue l'event. Tout handler qui
   « envoie un email » ou « incrémente un compteur » sans garde idempotent
   créera des doublons après redelivery.
5. **`max_instances` non fixé** : un batch qui dépasse 30 s verrait le suivant
   se superposer. `FOR UPDATE SKIP LOCKED` protège la BDD mais pas la charge
   CPU applicative. Toujours `max_instances=1` + `coalesce=True`.
6. **Timezone implicite** : `AsyncIOScheduler()` sans `timezone=` utilise la
   TZ système → dérive sleep OS en container. Toujours `timezone="UTC"` (NFR37).
7. **`raise SystemExit` dans un handler** : tue le scheduler. `dispatch_event`
   capture uniquement `Exception`, pas `BaseException`.
8. **2 schedulers dans le même process** : interdit. Un seul `AsyncIOScheduler`
   instancié dans `lifespan`, héberge **tous** les jobs périodiques (outbox +
   purge prefill_drafts).
9. **Cap applicatif vs contrainte DB** : `retry_count < MAX_RETRIES=3` côté
   applicatif **ET** `CHECK retry_count <= 5` côté DB. Défense en profondeur.
10. **Session pool leak** : toujours `async with AsyncSession(engine) as db:`
    (garantit release en `__aexit__`). Une session non fermée tient un slot
    du connection pool → épuisement sous charge.

---

## §6 Consommateurs prévus

| event_type                        | Handler (Epic) | Effet                                                   |
| --------------------------------- | -------------- | ------------------------------------------------------- |
| `noop.test`                       | Story 10.10    | Handler test-only (idempotent log + no-op).             |
| `project.created`                 | Epic 11        | Snapshot / materialized view company projection.        |
| `project.updated`                 | Epic 11        | Invalidation cache sommaire + re-score ESG auto.        |
| `maturity.declared`               | Epic 12        | Enregistrement plan de formalisation + notifications.   |
| `fact.updated`                    | Epic 13 AR-D3  | Invalidation `referential_verdicts` (cube compliance).  |
| `criterion_rule.updated`          | Epic 13        | Recalcul conformité × scoring sur tous projets impactés.|
| `fund.updated`                    | Epic 14        | `REFRESH MATERIALIZED VIEW mv_fund_matching_cube` (MEDIUM-10.1-6). |
| `intermediary.updated`            | Epic 14        | Recalcul matching + alerting candidatures actives.      |
| `fund_application.submitted`      | Story 9.12     | Notification chat SSE PDF généré.                       |
| `referential_version.published`   | FR34           | Notifications opt-in utilisateurs concernés.            |

---

## §7 Migration Phase Growth

Le pattern `APScheduler + SELECT FOR UPDATE SKIP LOCKED` est **remplaçable
sans refactor** par une infrastructure distribuée (Celery+Redis, AWS
EventBridge, SQS+Lambda). Seul le **trigger** change :

- **Aujourd'hui** : APScheduler `IntervalTrigger(seconds=30)` dans le process
  FastAPI.
- **Phase Growth** : une Lambda EventBridge (cron rate 30 s) qui invoque
  `process_outbox_batch` sur la RDS via IAM token, ou un worker Celery
  dédié qui consomme un canal Redis pub/sub signalé par un trigger
  PostgreSQL `NOTIFY`.

La table `domain_events`, le **writer**, les **handlers** et la query
`FOR UPDATE SKIP LOCKED` restent **identiques**. Aucune migration de
données requise. La promesse architecture.md §D11 est donc tenue.

**Tests E2E de régression** (marqueur `@pytest.mark.postgres`) :
``test_worker_skip_locked_allows_concurrent_processing`` valide le
comportement verrou row-level qui reste invariant quel que soit le trigger.
