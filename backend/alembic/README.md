# Alembic migrations

## Convention de nommage

```
NNN_<verbe_action>_<objet>.py
```

- `NNN` : numéro séquentiel à 3 chiffres (`020`, `021`, …)
- `<verbe_action>` : verbe d'action (`create`, `add`, `alter`, `enable`, …)
- `<objet>` : objet métier cible (snake_case)

Exemples : `020_create_projects_schema.py`, `024_enable_rls_on_sensitive_tables.py`.

## En-tête docstring canonique

```python
"""<description courte>

Revision ID: NNN_verbose
Revises: <parent_revision_id>
Create Date: YYYY-MM-DD

Story N.M — <décision(s) supportée(s) ex. D1, D7>
FR covered: [FR..., FR...]
NFR covered: [NFR..., NFR...]
Phase: 0 (ou 1, 2, 3)
"""
```

## Revision ID verbose

Les anciennes migrations (001-017) utilisaient des hash hex courts. Depuis
la spec 018, la convention est un identifiant explicite :

- `018_interactive`, `019_manual_edits`
- `020_projects`, `021_maturity`, `022_esg_3layers`, `023_deliverables`,
  `024_rls_audit`, `025_source_tracking`, `026_catalogue_audit`,
  `027_outbox_prefill`

## Cross-dialecte JSONB

Pour supporter à la fois PostgreSQL (JSONB natif) et SQLite (tests
in-memory du conftest) :

```python
sa.dialects.postgresql.JSONB().with_variant(sa.JSON(), "sqlite")
```

## Features PostgreSQL-only

Les features suivantes ne sont exécutables qu'en PostgreSQL — encadrer
avec `if op.get_bind().dialect.name == "postgresql":` :

- RLS (`ENABLE ROW LEVEL SECURITY`, `CREATE POLICY`)
- Vues matérialisées (`CREATE MATERIALIZED VIEW`)
- Indexes GIN / BRIN
- Indexes partiels (`postgresql_where`)
- `gen_random_uuid()` (server_default), extension `pgcrypto`
- `pgvector` (extension `vector`)

## Tests migrations

- **Round-trip PostgreSQL** : `backend/tests/test_migrations/test_migration_roundtrip.py`
- **Structure schéma** : `backend/tests/test_migrations/test_schema_structure.py`
- **CRUD par table** : `backend/tests/test_migrations/test_data_integrity.py`
- **RLS skeleton** : `backend/tests/test_security/test_rls_skeleton.py`

Les tests sont marqués `@pytest.mark.postgres` et skippés si
`TEST_ALEMBIC_URL` n'est pas configuré.

## Rollback trimestriel (NFR32)

Procédure de rollback sur production documentée dans
[`docs/runbooks/README.md`](../../docs/runbooks/README.md).

Commandes standard :

```bash
# Validation en staging
alembic upgrade head && alembic downgrade -1 && alembic upgrade head

# Rollback ciblé vers une révision
alembic downgrade 019_manual_edits
```

**⚠️ Irréversible** : `downgrade()` drop effectivement des tables et des
données. Toujours prendre un `pg_dump` avant tout rollback en production.
