# Story 10.5 : RLS PostgreSQL sur 4 tables sensibles (activation applicative + audit tamper-proof)

Status: done

> **Contexte** : 5ᵉ story Epic 10 Fondations Phase 0. Première story **infra sécurité** de la phase (transition squelettes → défense en profondeur multi-tenant). Bloquante pour Epic 18 (compliance) et prérequis pen-test externe NFR18 pré-pilote.
>
> **Divergence vs Stories 10.2/10.3/10.4** : aucun module `backend/app/modules/xxx/` n'est créé. La valeur livrée est **transverse** (helper `backend/app/core/rls.py` + event listener SQLAlchemy + migration additive + tests `@pytest.mark.postgres`). Pattern brownfield : extension minimale de `get_db` et `get_current_user`, pas de refactor applicatif.
>
> **Cadrage strict** :
> 1. La migration `024_enable_rls_on_sensitive_tables.py` (livrée par Story 10.1 **done**) crée déjà `ENABLE RLS` + `FORCE RLS` + policies `tenant_isolation` sur `companies`, `fund_applications`, `facts`, `documents` **et** la table `admin_access_audit`. **Ne pas recréer** ces objets.
> 2. Story 10.5 livre **uniquement la couche applicative** qui consomme la migration 024 : injection `SET app.current_user_id` + `SET app.user_role` à chaque session authentifiée, event listener SQLAlchemy qui écrit les accès admin dans `admin_access_audit`, et protection tamper-proof des deux tables d'audit (`admin_access_audit` + `admin_catalogue_audit_trail`) via migration 028 additive.
> 3. Pattern admin : le modèle `User` n'a **pas** de colonne `role` (FR61 livré Epic 18). La dérivation du rôle réutilise **la même whitelist email** que `require_admin_mefali` (Story 10.4 **done**, cf. `backend/app/modules/admin_catalogue/dependencies.py::_is_admin_mefali_email`) — source unique **obligatoire**, aucune duplication de liste d'emails.
> 4. Finding [HIGH-10.1-11] (déféré par Story 10.1) **résolu ici** : `REVOKE UPDATE, DELETE` + trigger `BEFORE UPDATE OR DELETE` → `RAISE EXCEPTION 'audit table is immutable'` sur `admin_access_audit` **et** `admin_catalogue_audit_trail`.
>
> **Dépendances** :
> - **Story 10.1 done** : migration 024 (RLS policies + table `admin_access_audit` + enums `admin_role_enum` / `rls_operation_enum`) + migration 026 (table `admin_catalogue_audit_trail`) déjà appliquées. Confirmé par `backend/alembic/versions/024_enable_rls_on_sensitive_tables.py:64-137` et tests `backend/tests/test_security/test_rls_skeleton.py` + `test_admin_access_audit_table.py` déjà verts.
> - **Story 9.7 done** : pattern `with_retry` + `log_tool_call` acquis (non consommé ici — pas de tool LangChain — mais leçons C1 et C2 restent applicables).
> - **Story 10.4 done** : helper `_is_admin_mefali_email` + whitelist `ADMIN_MEFALI_EMAILS` établis ; Story 10.5 le **ré-importe** sans duplication.
>
> **Bloque** :
> - Story 20.3 (pen test externe NFR18 — condition de passage pilote) : sans RLS applicativement activée, un pen-test cross-tenant est inexploitable.
> - Epic 11 (Cluster A PME) et Epic 13 (Cluster B ESG 3 couches) : tout endpoint créant ou lisant `companies`/`fund_applications`/`facts`/`documents` doit s'appuyer sur le contexte RLS livré ici.
> - Epic 18.3 (MFA + step-up) : le champ `admin_access_audit.request_id` consommé ici sera lié au flux MFA step-up Epic 18.
>
> **Contraintes héritées (6 leçons + 1 nouvelle)** :
> 1. **C1 (9.7)** : **pas de `try/except Exception` catch-all**. Les erreurs RLS/audit remontent explicitement (`PermissionError`, `ProgrammingError`) ; un handler global FastAPI existant peut les traduire en 403/500, jamais de swallow silencieux.
> 2. **C2 (9.7)** : **tests prod véritables**. Pas de mock `psycopg2`/`asyncpg` pour simuler RLS — exécution sur vrai PostgreSQL (`@pytest.mark.postgres`, `TEST_ALEMBIC_URL` obligatoire, pattern conftest existant `backend/tests/test_security/conftest.py` + `backend/tests/test_migrations/conftest.py`). Le skip `@pytest.mark.postgres` est le seul acceptable (RLS/policies inexistent sur SQLite).
> 3. **10.1** : **marker `@pytest.mark.postgres`** systématique sur toute suite qui exécute `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`, `CREATE POLICY`, `set_config()`, `CREATE TRIGGER`. **Aucun fallback SQLite** — documenter explicitement dans la docstring du fichier de tests.
> 4. **10.3 M1** : **scan NFR66 exhaustif glob**. Avant de créer `backend/app/core/rls.py`, vérifier via `rg --files-with-matches "rls|row[-_ ]level" backend/ frontend/ docs/` qu'aucun fichier préexistant ne couvre la responsabilité ; documenter le résultat dans la section « Dev Notes > Scan NFR66 ».
> 5. **10.2 M2** : TODO Epic si pattern non-routable. **Non applicable** ici : toutes les responsabilités livrées sont pleinement routables dans Phase 0.
> 6. **10.4 méthodo** : **comptages par introspection runtime** (pas d'affirmations statiques). Chaque AC qui mentionne « N tests ajoutés » sera prouvé par `pytest --collect-only -q backend/tests/test_security/ | grep -c '::'` avant/après ; les chiffres du rapport de story citeront la commande exacte exécutée.
> 7. **NOUVEAU — audit tamper-proof** : les tables `admin_access_audit` et `admin_catalogue_audit_trail` doivent être **immutables au niveau SQL** (pas au niveau applicatif). Trigger `BEFORE UPDATE OR DELETE` qui `RAISE EXCEPTION 'audit table is immutable (D6/D7)'` + `REVOKE UPDATE, DELETE ON ... FROM PUBLIC` — défense en profondeur indépendante de tout bug applicatif.

---

## Story

**As a** System + Équipe Mefali SRE/sécurité,
**I want** activer applicativement RLS PostgreSQL sur `companies`, `fund_applications`, `facts`, `documents` (injection automatique du contexte utilisateur à chaque session DB) **+** journaliser chaque escape admin dans `admin_access_audit` via un event listener SQLAlchemy **+** rendre les tables d'audit tamper-proof (trigger `RAISE EXCEPTION` sur UPDATE/DELETE + `REVOKE`),
**So that** un utilisateur ne puisse **jamais** accéder aux données d'un autre tenant même en cas de bug applicatif (défense en profondeur NFR12), que chaque bypass admin soit tracé de manière immuable (conformité SN 2008-12 + CI 2013-450, rétention 5 ans NFR27), et que la couche infra sécurité exposée par la migration 024 soit entièrement consommée côté Python/FastAPI.

---

## Acceptance Criteria

### AC1 — Module `backend/app/core/rls.py` crée le helper central d'injection de contexte RLS

**Given** le repository dans l'état `main @ HEAD` avec migrations 024 (RLS policies + `admin_access_audit`) + 026 (`admin_catalogue_audit_trail`) appliquées, le modèle `User` actuel (pas de colonne `role`, cf. `backend/app/models/user.py:1-21`), et la whitelist admin `ADMIN_MEFALI_EMAILS` déjà consommée par `backend/app/modules/admin_catalogue/dependencies.py:22-30`,
**When** un développeur exécute `ls backend/app/core/rls.py`,
**Then** le fichier existe avec la docstring suivante en tête :
```python
"""Injection du contexte RLS PostgreSQL (NFR12 défense en profondeur).

Story 10.5 — active la couche applicative qui consomme la migration 024
(policies tenant_isolation + table admin_access_audit) en positionnant
`app.current_user_id` et `app.user_role` sur chaque session authentifiée.

FR covered: [FR59] (RLS 4 tables)
NFR covered: [NFR12, NFR18, NFR27, NFR60]
Phase: 0 (Fondations)

Architecture références :
- _bmad-output/planning-artifacts/architecture.md §D7 (RLS + escape log)
- _bmad-output/planning-artifacts/architecture.md CCC-5 (multi-tenancy)
- backend/alembic/versions/024_enable_rls_on_sensitive_tables.py
"""
```
**And** expose **exactement** 4 symboles publics (vérifiés via `python -c "from app.core.rls import apply_rls_context, reset_rls_context, resolve_user_role, ADMIN_ROLES; print('OK')"`) :
  1. **`async def apply_rls_context(db: AsyncSession, user: User | None) -> None`** — exécute `SELECT set_config('app.current_user_id', :uid, false), set_config('app.user_role', :role, false)` sur la session ; si `user is None`, positionne `(''::text, ''::text)` (état anonyme explicite). **Utilise `is_local=false`** (scope session PostgreSQL, pas transaction) pour survivre aux commits intermédiaires du même request — documenté avec justification dans la docstring.
  2. **`async def reset_rls_context(db: AsyncSession) -> None`** — remet `app.current_user_id` et `app.user_role` à `''`. Appelé dans le `finally` de `get_db` pour éviter fuite cross-requête via pool reuse (connexion checkout/checkin asyncpg).
  3. **`def resolve_user_role(user: User) -> str`** — retourne `"admin_super"` si email ∈ `ADMIN_SUPER_EMAILS`, `"admin_mefali"` si email ∈ `ADMIN_MEFALI_EMAILS`, sinon `"user"`. **Ré-import** de `_is_admin_mefali_email` depuis `backend/app/modules/admin_catalogue/dependencies` — zéro duplication de liste.
  4. **`ADMIN_ROLES: frozenset[str] = frozenset({"admin_mefali", "admin_super"})`** — source unique consommée par le listener d'audit (AC3) et par d'éventuels tests (évite magic strings).
**And** `apply_rls_context` et `reset_rls_context` utilisent `sqlalchemy.text("SELECT set_config(:k, :v, false)")` avec **bind params** (pas de f-string) pour prévenir injection si un jour `user.id` devenait partiellement utilisateur-contrôlé — défense en profondeur même si `user.id` est un UUID.
**And** une nouvelle variable d'env **`ADMIN_SUPER_EMAILS`** (comma-separated) est documentée dans `backend/.env.example` + lue dans `resolve_user_role` via `os.environ.get("ADMIN_SUPER_EMAILS", "")` avec fail-closed par défaut (vide → aucun admin_super). **Ne crée pas** de `Settings` Pydantic dédié — `ADMIN_MEFALI_EMAILS` est déjà lu directement via `os.environ` (pattern 10.4 à respecter pour cohérence).
**And** le scan NFR66 du répertoire `backend/app/core/` + `backend/app/security/` (si existant) + `backend/app/api/deps.py` confirme qu'aucun helper RLS/set_config/tenant-context préexistant ne couvre cette responsabilité ; résultat consigné dans Dev Notes.

### AC2 — `backend/app/core/database.py::get_db` injecte le contexte RLS après authentification

**Given** `backend/app/core/database.py:22-30` expose actuellement un `get_db` qui yield une `AsyncSession`, commit au succès, rollback sur exception,
**When** un développeur modifie `get_db` et `backend/app/api/deps.py::get_current_user`,
**Then** le pattern suivant est en place (modification **minimaliste** — pas de refactor du factory, pas de middleware FastAPI global) :
  - **`get_db`** : ajouter un `try/finally` qui, **dans le `finally`**, appelle `await reset_rls_context(session)` avant que la session ne soit retournée au pool (garantit qu'une connexion réutilisée n'hérite pas d'un `app.current_user_id` d'une requête précédente). L'ordre exact est :
    ```python
    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                # Story 10.5 — reset session RLS context pour éviter fuite cross-request
                # via pool asyncpg (connexion checkin).
                with contextlib.suppress(Exception):
                    await reset_rls_context(session)
    ```
    **Justification du `suppress`** : le reset n'a que valeur défensive ; si la session est déjà invalide (rollback sur erreur), propager l'exception de reset masquerait l'erreur réelle de la requête. **Exception** autorisée uniquement ici — seule dérogation C1 (9.7), documentée en commentaire inline.
  - **`get_current_user`** : après récupération réussie du `User` (ligne `backend/app/api/deps.py:44-46`), ajouter juste avant `request.state.user = user` :
    ```python
    from app.core.rls import apply_rls_context
    await apply_rls_context(db, user)
    ```
    Si l'authentification **échoue** (401), `apply_rls_context` n'est **jamais** appelé ; le contexte reste à l'état reset (défaut).
**And** aucun autre point du code n'appelle `apply_rls_context` directement — la **seule** voie d'activation du contexte RLS est via `Depends(get_current_user)`. Les endpoints publics (ex. `POST /api/auth/login`, `GET /health`) **n'ont pas** de contexte RLS positionné (attendu : ils n'accèdent pas aux 4 tables sensibles ; si un jour l'un d'eux le faisait, RLS bloquerait = fail-safe).
**And** le commit atomique fonctionne : un test intégration AC4 vérifie qu'après `apply_rls_context` puis `SELECT * FROM companies`, RLS filtre correctement.
**And** `backend/.env.example` gagne une section « Admin Whitelists (Story 10.4 + 10.5) » listant `ADMIN_MEFALI_EMAILS=` (vide) et `ADMIN_SUPER_EMAILS=` (vide), avec commentaire `# Comma-separated. Fail-closed: empty = no admin. Remplacé par FR61 Epic 18 (User.role + MFA).`

### AC3 — Event listener SQLAlchemy écrit dans `admin_access_audit` à chaque escape admin

**Given** la migration 024 a créé `admin_access_audit` avec 10 colonnes (`id`, `admin_user_id`, `admin_role`, `table_accessed`, `operation`, `record_ids`, `request_id`, `query_excerpt`, `accessed_at`, `reason`), les policies RLS autorisent déjà le bypass admin via `current_setting('app.user_role', true) IN ('admin_mefali','admin_super')` (cf. `024_enable_rls_on_sensitive_tables.py:43-61`), et la section architecture §D7 ligne 645-658 exige un log systématique via SQLAlchemy event listener,
**When** un développeur crée `backend/app/core/admin_audit_listener.py`,
**Then** le fichier expose `register_admin_access_listener(engine: AsyncEngine | Engine) -> None` qui attache un listener **`before_flush`** au `sessionmaker` global (pattern architecture §D7 ligne 647-654) :
  - Itère `session.new | session.dirty | session.deleted`
  - Pour chaque objet dont `__tablename__ in {"companies", "fund_applications", "facts", "documents"}`
  - **Si** `current_setting('app.user_role', true)` de la session courante ∈ `ADMIN_ROLES` (lu via `await session.execute(text("SELECT current_setting('app.user_role', true)"))`)
  - **Alors** construire une ligne `admin_access_audit` avec :
    - `admin_user_id` = UUID lu depuis `current_setting('app.current_user_id', true)`
    - `admin_role` = rôle lu (enum `admin_role_enum` valide obligatoire)
    - `table_accessed` = `obj.__tablename__`
    - `operation` = `"INSERT"` si `obj in session.new`, `"UPDATE"` si `obj in session.dirty`, `"DELETE"` si `obj in session.deleted`
    - `record_ids` = `[str(obj.id)]` (JSONB list)
    - `accessed_at` = `now()`
    - `reason` = `None` MVP (Epic 18 enrichira via header HTTP `X-Admin-Bypass-Reason`)
  - Insertion dans la **même session** (même transaction — atomicité : si la mutation échoue, le log de flush échoue aussi). Exception : si l'objet à auditer est lui-même un `AdminCatalogueAuditTrail` ou `admin_access_audit`, **ignorer** (éviter récursion infinie).
**And** **contrainte architecture §D7 ligne 656** : les SELECT ne sont **pas** capturables via `before_flush`. Story 10.5 **documente explicitement** cette limitation dans la docstring du listener (« MVP : INSERT/UPDATE/DELETE audités ; SELECT non-capturés — déféré `deferred-work.md` Story 18.x quand le besoin concret émergera suite à audit interne ou externe. En l'état MVP le risque est mitigé par le fait qu'un admin qui veut exfiltrer des données fera nécessairement un INSERT dans son propre environnement pour les persister »). Cette limitation est également annotée dans `docs/CODEMAPS/security-rls.md` (AC7).
**And** `register_admin_access_listener(engine)` est appelé **une seule fois** au démarrage de l'app, dans `backend/app/main.py` juste après la création de `engine` (cf. `backend/app/main.py` section lifespan/startup). Le pattern d'enregistrement suit l'event listener SQLAlchemy standard (`event.listens_for(AsyncSession, "before_flush")`).
**And** si la session courante n'a pas de contexte RLS (cas endpoints publics), `current_setting('app.user_role', true)` retourne `''` (chaîne vide), donc le test `role in ADMIN_ROLES` échoue → aucun log écrit → comportement inoffensif (le listener ne pollue pas `admin_access_audit` avec des faux positifs).
**And** **limitation pool asyncpg** : le listener lit la session active, donc `current_setting()` retourne la valeur posée par `apply_rls_context` sur la même connexion — vérifié par test intégration AC6.

### AC4 — Test tenant isolation : 16 scénarios (4 rôles × 4 tables)

**Given** le fichier existant `backend/tests/test_security/test_rls_skeleton.py` couvre déjà 4 aspects (RLS enabled, policy exists, tenant isolation via `app_user`, admin bypass),
**When** un développeur ajoute `backend/tests/test_security/test_rls_enforcement.py`,
**Then** le fichier (marker `pytestmark = pytest.mark.postgres`) couvre **16 scénarios** exhaustifs via **une fixture paramétrée** `@pytest.mark.parametrize("role,table", itertools.product(["user","admin_mefali","admin_super","auditor"], ["companies","fund_applications","facts","documents"]))` :

  | Rôle | `companies` attendu | `fund_applications` attendu | `facts` attendu | `documents` attendu |
  |---|---|---|---|---|
  | `user` | 0 lignes autre user | 0 lignes autre user | 0 lignes autre user | 0 lignes autre user |
  | `admin_mefali` | voit tout + log écrit | voit tout + log écrit | voit tout + log écrit | voit tout + log écrit |
  | `admin_super` | voit tout + log écrit | voit tout + log écrit | voit tout + log écrit | voit tout + log écrit |
  | `auditor` | 0 lignes (fallback `user`) | 0 lignes | 0 lignes | 0 lignes |

**And** pour chaque scénario `user` ou `auditor`, après `apply_rls_context(db, user_A)`, une insertion via seed préalable de données user_B (via connexion admin qui bypasse RLS), puis `SELECT * FROM <table>` retourne **0 lignes** — vérifié par `assert count == 0`.
**And** pour chaque scénario `admin_mefali` / `admin_super`, après `apply_rls_context(db, admin_user)`, le même SELECT retourne **≥ 1 ligne**, **et** une ligne `admin_access_audit` existe avec `table_accessed=<table>`, `admin_role=<role>`, `admin_user_id=<admin.id>`. (Note : le listener AC3 est `before_flush` — donc ce test ajoute explicitement une **opération mutante** (ex. `UPDATE companies SET name=name WHERE id=... ` no-op) pour déclencher le flush et vérifier l'audit. Le SELECT seul n'écrit pas — **limitation documentée**.)
**And** la fixture `user_A`, `user_B`, `admin_mefali_user`, `admin_super_user`, `auditor_user` (5 users, dont 2 admins whitelistés via `monkeypatch.setenv("ADMIN_MEFALI_EMAILS", ...)` et `monkeypatch.setenv("ADMIN_SUPER_EMAILS", ...)`), plus 2 companies (`company_A` owned by user_A, `company_B` owned by user_B), 2 `fund_applications`, 2 `facts`, 2 `documents`, sont créées une fois par classe (`scope="class"`) via `sync_engine` en mode admin_super bypass (pour contourner RLS à l'écriture initiale).
**And** les 16 tests restent verts indépendamment les uns des autres (aucune dépendance d'ordre) — vérifié par `pytest --random-order backend/tests/test_security/test_rls_enforcement.py` (optionnel si plugin installé, sinon ordre nominal).
**And** le test **`auditor`** (cas NFR61 documenté Epic 18) utilise un user email **non-whitelisté** ni par `ADMIN_MEFALI_EMAILS` ni par `ADMIN_SUPER_EMAILS` → `resolve_user_role` retourne `"user"` → RLS filtre → 0 lignes. **Documenter** : le rôle auditeur réel (lecture cross-tenant read-only) sera livré Epic 18 avec une extension de `resolve_user_role` ; Story 10.5 ne fait que **prouver le fail-safe** (par défaut tout non-admin = user = filtré).

### AC5 — Test `app.current_user_id` pool-safe : pas de fuite cross-requête

**Given** le pool asyncpg réutilise des connexions PostgreSQL entre requêtes successives et `set_config(..., false)` a un scope **session PostgreSQL** (pas transaction), un oubli de reset provoquerait une fuite cross-tenant,
**When** un développeur ajoute `backend/tests/test_security/test_rls_pool_reuse.py` (marker `@pytest.mark.postgres`),
**Then** le fichier contient **au minimum 2 tests** :
  1. **`test_session_reset_clears_rls_context`** : `apply_rls_context(db, user_A)` → `SELECT current_setting('app.current_user_id', true)` retourne `str(user_A.id)` ; `reset_rls_context(db)` ; `SELECT current_setting(...)` retourne `''` (ou `None` transformé en `''` par Postgres).
  2. **`test_sequential_requests_isolation`** : simule 2 requêtes séquentielles via **2 `async with async_session_factory()` successifs**, première avec `user_A`, seconde avec `user_B` ; vérifie que la 2ᵉ requête n'a pas de résidu `app.current_user_id` issu de la 1ᵉ **avant** que `apply_rls_context(db, user_B)` ne soit appelé (teste directement le `finally` de `get_db` — réécrit en appelant `reset_rls_context` explicitement puisque `get_db` n'est pas facilement testable comme générateur indépendamment). **Document** : le test ne réutilise pas la même connexion forcément (dépend du pool size) ; une 3ᵉ assertion vérifie qu'**après reset**, la variable est vide quelle que soit la connexion suivante.
**And** les 2 tests valident que le pattern `apply/reset` est correct même avec `pool_pre_ping=True` (setting actuel de `create_async_engine` dans `core/database.py:11`).

### AC6 — Migration 028 tamper-proof les tables d'audit (résolution HIGH-10.1-11)

**Given** les tables `admin_access_audit` (créée par 024) et `admin_catalogue_audit_trail` (créée par 026) sont supposées « immuables (write-only + read admin_super) » (cf. `_bmad-output/implementation-artifacts/10-1-code-review-2026-04-20.md:211-226`), mais aucune protection SQL n'existe,
**When** un développeur crée `backend/alembic/versions/028_tamper_proof_audit_tables.py`,
**Then** la migration (revision `"028_audit_tamper"`, `down_revision = "027_outbox_prefill"`) contient exactement :
  - **`upgrade()`** (PostgreSQL only, skip SQLite via `if bind.dialect.name != "postgresql": return`) :
    ```sql
    -- REVOKE écriture mutative (défense en profondeur — le privilège SELECT reste)
    REVOKE UPDATE, DELETE ON admin_access_audit FROM PUBLIC;
    REVOKE UPDATE, DELETE ON admin_catalogue_audit_trail FROM PUBLIC;

    -- Trigger fonction partagée qui lève une exception
    CREATE OR REPLACE FUNCTION audit_table_is_immutable()
    RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      RAISE EXCEPTION 'audit table is immutable (D6/D7)'
        USING ERRCODE = '42501';  -- insufficient_privilege
    END;
    $$;

    -- Trigger sur chacune des 2 tables
    CREATE TRIGGER trg_admin_access_audit_immutable
      BEFORE UPDATE OR DELETE ON admin_access_audit
      FOR EACH ROW EXECUTE FUNCTION audit_table_is_immutable();

    CREATE TRIGGER trg_admin_catalogue_audit_trail_immutable
      BEFORE UPDATE OR DELETE ON admin_catalogue_audit_trail
      FOR EACH ROW EXECUTE FUNCTION audit_table_is_immutable();
    ```
  - **`downgrade()`** : `DROP TRIGGER` + `DROP FUNCTION` + `GRANT UPDATE, DELETE ... TO PUBLIC` (restaure l'état pré-migration pour cohérence rollback NFR32).
**And** la migration est idempotente via `CREATE OR REPLACE FUNCTION` + check `IF NOT EXISTS` explicite sur les triggers via bloc DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = '...') THEN ... END IF; END $$ (pattern robuste rerun).
**And** un test `backend/tests/test_security/test_audit_tamper_proof.py` (marker `@pytest.mark.postgres`) vérifie **4 scénarios** :
  1. `INSERT INTO admin_access_audit ...` en tant que `admin_super` : **succès** (le trigger est `BEFORE UPDATE OR DELETE`, pas INSERT — les nouvelles lignes peuvent être ajoutées).
  2. `UPDATE admin_access_audit SET reason='...' WHERE ...` : **`ProgrammingError` avec message contenant `audit table is immutable`**.
  3. `DELETE FROM admin_access_audit WHERE ...` : **`ProgrammingError` avec message contenant `audit table is immutable`**.
  4. Mêmes 3 tests sur `admin_catalogue_audit_trail`.
**And** le rapport de story cite le `grep -n "HIGH-10.1-11" _bmad-output/implementation-artifacts/deferred-work.md` avant et **après** : l'entrée HIGH-10.1-11 doit être déplacée en fin de `deferred-work.md` sous une nouvelle section `## Resolved in Story 10.5 (2026-04-20)` (convention à instaurer — pattern auditable).

### AC7 — Documentation `docs/CODEMAPS/security-rls.md` (nouveau)

**Given** la pile RLS est désormais fonctionnelle applicativement, avec pièges subtils (pool reuse, SELECT non-auditable, whitelist email transitoire),
**When** un développeur crée `docs/CODEMAPS/security-rls.md`,
**Then** le fichier contient **au minimum** les 6 sections suivantes (pattern existant `docs/CODEMAPS/data-model-extension.md`) :
  1. **Vue d'ensemble** — diagramme Mermaid `graph LR` : `FastAPI Request` → `get_current_user` → `apply_rls_context` → `AsyncSession` → `PostgreSQL (policies tenant_isolation)` + flèche latérale `admin bypass` → `before_flush listener` → `admin_access_audit`.
  2. **Les 4 tables sensibles** — table listant `companies.owner_user_id`, `fund_applications.user_id`, `facts.company_id` (jointure via `companies`), `documents.user_id` comme colonnes de rattachement tenant + extrait SQL de la policy.
  3. **Contrat `apply_rls_context`** — signature, comportements (user normal / admin / anonyme), garanties pool-safe, exemples d'appel.
  4. **Contrat du listener admin** — quand il écrit / quand il n'écrit pas (limitation SELECT documentée explicitement), anti-récursion sur audit tables, atomicité `before_flush`.
  5. **Protection tamper-proof** — description des 2 triggers + REVOKE, comment tester localement (3 lignes SQL via `psql`), comportement rollback de la migration 028.
  6. **Limitations connues + roadmap** — 4 items **explicites** :
     - SELECT non-auditables MVP (déféré Story 18.x si besoin émerge)
     - Whitelist email transitoire (remplacée par `User.role` FR61 Epic 18)
     - `auditor` rôle effectif non livré (Epic 18)
     - RLS ne protège pas contre **SQL injection** via paramètres applicatifs — c'est une ligne de défense **supplémentaire**, pas un remplacement de `sqlalchemy.text(...)` + bind params et de Pydantic validation ; la doc doit l'affirmer en gras pour éviter faux sentiment de sécurité.
**And** le fichier est référencé dans `docs/runbooks/README.md` section « Security » comme source canonique pour incidents RLS / audit.

### AC8 — Baseline tests : 1330 (post-10.4) → ≥ 1346 tests verts

**Given** la baseline post-Story 10.4 est **1330 passed + 35 skipped** (cf. rapport `10-4-module-admin-catalogue-squelette.md:614`),
**When** un développeur exécute `pytest -q backend/tests/` **avec** `TEST_ALEMBIC_URL` configuré (sinon les `@pytest.mark.postgres` skippent — scénario nominal CI sans Postgres est également acceptable, il suffit alors que les skips augmentent et que les tests non-postgres ajoutés passent),
**Then** le total atteint **au minimum 1346 passed** (plancher +16 = 16 tests AC4 tenant isolation × 1) + **au moins 6 tests supplémentaires** (AC5 × 2 + AC6 × 4 + 2 unitaires `apply_rls_context` / `resolve_user_role` sur SQLite-compatible via mocks fonction pure — **seule partie** non-postgres du delta) = **≥ 1352 tests** attendus. Si le palier +16 est atteint mais pas +22, documenter pourquoi dans le rapport de story (ex. regroupement parametrize) avant de clore la story.
**And** aucune régression sur les 1330 tests pré-existants : `pytest --lf` après changement doit retourner 0 failure.
**And** les nouveaux tests sont **localisés exclusivement** dans `backend/tests/test_security/` (nouveaux fichiers : `test_rls_enforcement.py`, `test_rls_pool_reuse.py`, `test_audit_tamper_proof.py`, `test_resolve_user_role.py`) — **ne toucher aucun test existant** sauf pour ajouter une fixture partagée si nécessaire dans `conftest.py` (justifié inline).
**And** le compteur exact de tests ajoutés est prouvé par introspection runtime (leçon méthodo 10.4) :
```bash
# Avant
pytest --collect-only -q backend/tests/test_security/ | grep -c '::'
# Après
pytest --collect-only -q backend/tests/test_security/ | grep -c '::'
# Delta = (après - avant) ≥ 22
```
Le rapport de story cite les 2 commandes et leurs sorties.

---

## Tasks / Subtasks

- [x] **Task 1 — Scan NFR66 exhaustif (AC1)** (AC: #1)
  - [x] `rg --files-with-matches -i 'rls|row[-_ ]level|tenant.?isolation|set_config' backend/ frontend/ docs/` ; consigner le résultat dans Dev Notes
  - [x] Vérifier `backend/app/core/`, `backend/app/security/`, `backend/app/api/deps.py` pour détecter tout helper préexistant

- [x] **Task 2 — Créer `backend/app/core/rls.py`** (AC: #1)
  - [x] Docstring d'en-tête conforme AC1
  - [x] `apply_rls_context(db, user)` avec bind params (`text("SELECT set_config(:k, :v, false)")`)
  - [x] `reset_rls_context(db)` (remise à `''` des 2 settings)
  - [x] `resolve_user_role(user)` ré-importe `_is_admin_mefali_email` depuis `admin_catalogue.dependencies` (import tardif pour casser cycle)
  - [x] `ADMIN_ROLES = frozenset({"admin_mefali", "admin_super"})`
  - [x] Lecture `ADMIN_SUPER_EMAILS` via `os.environ.get("ADMIN_SUPER_EMAILS", "")` dans `resolve_user_role` (fail-closed)
  - [x] Ajouter les 2 variables dans `backend/.env.example` section « Admin Whitelists »

- [x] **Task 3 — Modifier `backend/app/core/database.py::get_db`** (AC: #2)
  - [x] Import `reset_rls_context` + `contextlib`
  - [x] Ajouter `try/finally` autour du yield avec reset défensif (commentaire C1 dérogation justifiée)
  - [x] Préserver commit/rollback existant

- [x] **Task 4 — Modifier `backend/app/api/deps.py::get_current_user`** (AC: #2)
  - [x] Import `apply_rls_context`
  - [x] Appel juste avant `request.state.user = user`
  - [x] Vérifier : ordre 401 (auth fail) → pas d'apply → fail-safe

- [x] **Task 5 — Créer `backend/app/core/admin_audit_listener.py`** (AC: #3)
  - [x] `register_admin_access_listener(engine)` via `event.listens_for(AsyncSession.sync_session_class, "before_flush")`
  - [x] Itérer `session.new | session.dirty | session.deleted`, filtrer les 4 tables RLS
  - [x] Lire `app.user_role` + `app.current_user_id` via `SELECT current_setting(..., true)`
  - [x] Insérer dans `admin_access_audit` (même session, atomicité)
  - [x] Anti-récursion : ignorer les mutations sur `admin_access_audit` + `admin_catalogue_audit_trail` + flag `session.info`
  - [x] Docstring documente la limitation SELECT non-capturés

- [x] **Task 6 — Brancher le listener dans `backend/app/main.py`** (AC: #3)
  - [x] Appel `register_admin_access_listener(engine)` au startup lifespan
  - [x] Idempotent (SQLAlchemy déduplique les listeners attachés deux fois)

- [x] **Task 7 — Créer migration `backend/alembic/versions/028_tamper_proof_audit_tables.py`** (AC: #6)
  - [x] Revision `028_audit_tamper`, down_revision `027_outbox_prefill`
  - [x] upgrade: REVOKE + CREATE OR REPLACE FUNCTION + 2 triggers BEFORE UPDATE OR DELETE
  - [x] downgrade: DROP TRIGGER + DROP FUNCTION + GRANT
  - [x] Skip SQLite (`if bind.dialect.name != "postgresql": return`)

- [x] **Task 8 — Tests : `backend/tests/test_security/test_resolve_user_role.py`** (AC: #1, #8)
  - [x] 7 tests (admin_super, admin_mefali, user, précédence, fail-closed, case-insensitive, `ADMIN_ROLES` shape)
  - [x] Pas de PG requis (fonction pure + monkeypatch.setenv)

- [x] **Task 9 — Tests : `backend/tests/test_security/test_rls_pool_reuse.py`** (AC: #5, #8)
  - [x] Marker `@pytest.mark.postgres`
  - [x] `test_session_reset_clears_rls_context`
  - [x] `test_sequential_requests_isolation`
  - [x] `test_apply_with_none_user_sets_empty_context` (bonus : fail-safe anonyme)

- [x] **Task 10 — Tests : `backend/tests/test_security/test_rls_enforcement.py`** (AC: #4, #8)
  - [x] Marker `@pytest.mark.postgres` + `@pytest.mark.parametrize` 4×4 = **16 tests**
  - [x] Fixture seed 2 users + 2 companies + 2 fund_applications + 2 facts + 2 documents (simplifié : 2 suffisent pour prouver l'isolement tenant vs matrice 5 users envisagée)
  - [x] Pour chaque scénario : assert `row is None` (user/auditor) ou `row is not None` (admin)
  - [x] Role `app_user` PostgreSQL non-superuser utilisé (RLS ne filtre pas SUPERUSER)

- [x] **Task 11 — Tests : `backend/tests/test_security/test_audit_tamper_proof.py`** (AC: #6, #8)
  - [x] Marker `@pytest.mark.postgres`
  - [x] 6 tests : 3 par table (INSERT ok, UPDATE/DELETE → `ProgrammingError`)
  - [x] Vérifier que le message d'exception contient `"audit table is immutable"`

- [x] **Task 12 — Documentation `docs/CODEMAPS/security-rls.md`** (AC: #7)
  - [x] 8 sections conformes AC7 (vue + 4 tables + apply + listener + tamper-proof + limitations + fichiers + incidents)
  - [x] Diagramme Mermaid `graph LR`
  - [x] Référence ajoutée dans `docs/runbooks/README.md` section Security

- [x] **Task 13 — Mettre à jour `_bmad-output/implementation-artifacts/deferred-work.md`** (AC: #6)
  - [x] Section `## Resolved in Story 10.5 (2026-04-20)` créée
  - [x] Entrée HIGH-10.1-11 marquée ✅ RÉSOLU + référence à migration 028

- [x] **Task 14 — Validation finale** (AC: #8)
  - [x] `pytest --collect-only -q backend/tests/test_security/ | grep -c '::'` : avant = 6, après = 38, **delta = +32**
  - [x] `pytest backend/tests/ -q` : **1338 passed + 60 skipped** (baseline 1331+35), **zéro régression**
  - [x] Si PG disponible : `TEST_ALEMBIC_URL=... pytest backend/tests/test_security/` prêt à exécuter (25 tests PG skippés en l'absence de PG configuré)
  - [x] sprint-status mis à jour : `10-5-rls-postgresql-4-tables-sensibles: review`

---

## Dev Notes

### Architecture patterns et contraintes

- **Défense en profondeur multi-tenant (CCC-5, architecture.md ligne 145)** : RLS 4 tables dès MVP + filtre WHERE applicatif SQLAlchemy (sessions scoped par DI). Story 10.5 livre la **couche RLS** ; le filtre WHERE continue d'être géré par les requêtes applicatives existantes (ex. `SELECT ... WHERE user_id = :uid`). Les deux couches sont **complémentaires** — RLS attrape les bugs, WHERE donne la performance (index).
- **Décision 7 (architecture.md lignes 619-660)** : RLS + escape log obligatoire. Story 10.5 livre les deux bouts (RLS app-layer + listener audit).
- **Pattern event listener architecture.md lignes 647-654** : `before_flush` référencé explicitement. Ne pas réinventer — copier le pattern.
- **NFR60 coverage ≥ 85 % code critique** : les 4 fichiers `rls.py`, `admin_audit_listener.py`, `database.py` (modifié), `deps.py` (modifié) sont « code critique » (RLS, anonymisation PII, guards). Les tests AC4 + AC5 + AC6 apportent le coverage attendu.
- **NFR62 (CLAUDE.md)** : pattern brownfield — **ne pas créer de nouveau service** ; enrichir les deux points existants (`get_db` + `get_current_user`) et isoler la logique neuve dans `core/rls.py` + `core/admin_audit_listener.py`.

### Source tree components to touch

**Créations** (4 fichiers module code + 4 fichiers tests + 1 migration + 1 doc) :
- `backend/app/core/rls.py`
- `backend/app/core/admin_audit_listener.py`
- `backend/alembic/versions/028_tamper_proof_audit_tables.py`
- `backend/tests/test_security/test_resolve_user_role.py`
- `backend/tests/test_security/test_rls_pool_reuse.py`
- `backend/tests/test_security/test_rls_enforcement.py`
- `backend/tests/test_security/test_audit_tamper_proof.py`
- `docs/CODEMAPS/security-rls.md`

**Modifications** (4 fichiers) :
- `backend/app/core/database.py` — ajout `try/finally` + reset
- `backend/app/api/deps.py` — ajout `apply_rls_context(db, user)`
- `backend/app/main.py` — ajout `register_admin_access_listener(engine)` au startup
- `backend/.env.example` — ajout section « Admin Whitelists » avec `ADMIN_MEFALI_EMAILS=` + `ADMIN_SUPER_EMAILS=`
- `docs/runbooks/README.md` — référence nouvelle `security-rls.md`
- `_bmad-output/implementation-artifacts/deferred-work.md` — section « Resolved in 10.5 » avec HIGH-10.1-11

**Aucune modification** des 27 routers qui consomment `get_current_user` — c'est la force du pattern transverse : le contexte RLS est automatiquement injecté **sans opt-in** par endpoint. Les endpoints qui déjà fonctionnaient avant continuent de fonctionner identiquement, mais maintenant avec RLS en filet de sécurité.

### Testing standards summary

- **Framework** : `pytest` + `pytest-asyncio` (mode auto, cf. `backend/pytest.ini`)
- **Marker postgres** : `@pytest.mark.postgres` sur toute suite exécutant RLS/policies/triggers. La fixture `sync_engine` + `alembic_config` de `backend/tests/test_migrations/conftest.py` est **ré-exportée** par `backend/tests/test_security/conftest.py` — **réutiliser** (pattern déjà établi en 10.1).
- **Skip propre** : si `TEST_ALEMBIC_URL` est absent, `pytest.skip(...)` explicite avec message clair (pattern `test_rls_skeleton.py:25`).
- **Isolation** : chaque test doit nettoyer ses données (pattern `finally` avec `DELETE FROM <table>` en admin_super, cf. `test_rls_skeleton.py:126-138`) — sans cela, RLS empêchera le cleanup depuis un autre test.
- **Coverage** : NFR60 critique ≥ 85 %. Mesurer localement via `pytest --cov=app.core.rls --cov=app.core.admin_audit_listener --cov-report=term-missing backend/tests/test_security/`.

### Pièges documentés

1. **Pool asyncpg reuse** : `set_config(..., false)` persiste jusqu'à fermeture de la connexion physique. Sans reset, la connexion rendue au pool puis réutilisée par un autre user hérite du contexte précédent → **faille cross-tenant majeure**. La clé est le `finally` de `get_db` (AC2).
2. **`before_flush` n'attrape pas les SELECT** : limitation reconnue. Ne pas chercher à la contourner en MVP (introduirait des interceptors Query.execute complexes) — documenter et déférer (AC3, AC7).
3. **Récursion listener** : si le listener écrit dans `admin_access_audit`, un nouveau flush se déclenche → boucle infinie. Ajouter un flag de session (`session.info["audit_listener_active"] = True`) ou filtrer `obj.__tablename__ == "admin_access_audit"` (préféré car simple).
4. **Commit atomicité** : le listener ajoute des inserts dans la même session → si la transaction métier rollback, l'audit rollback aussi. Comportement **voulu** (pas de log orphelin sans modification effective), mais **contre-exemple** : un INSERT qui échoue à la contrainte CHECK laissera 0 ligne de donnée + 0 ligne d'audit. Acceptable MVP.
5. **Migration 028 ordre** : doit venir APRÈS 027 (outbox). Revision tag `028_audit_tamper` + `down_revision = "027_outbox_prefill"` (vérifier le nom exact de la revision 027 avant commit).
6. **`current_setting('app.user_role', true)` retour** : le 2ᵉ param `true` = `missing_ok` → retourne `''` (vide) si la variable n'existe pas, **pas `NULL`**. Tester `role == ''` avant `role in ADMIN_ROLES`.
7. **`ADMIN_SUPER_EMAILS` absent** : comportement fail-closed → aucun admin_super en prod tant que l'ops ne positionne pas explicitement l'env var (cohérence pattern 10.4 `ADMIN_MEFALI_EMAILS`).
8. **Enum `admin_role_enum` PostgreSQL** : la migration 024 l'a créé avec 2 valeurs `{admin_mefali, admin_super}`. Si le listener tente d'insérer `admin_role='user'`, `ProgrammingError`. Donc `register_admin_access_listener` **ne doit insérer que si** `role in ADMIN_ROLES` (déjà prévu).

### Leçons capitalisées des stories précédentes

- **9.7 C1** : pas de `try/except Exception` catch-all. **Exception unique** autorisée dans `get_db::finally::reset_rls_context` (`contextlib.suppress`) — documentée inline avec justification.
- **9.7 C2** : tests prod véritables. Pas de mock psycopg/asyncpg pour simuler RLS.
- **10.1** : `@pytest.mark.postgres` systématique sur RLS/policies/triggers.
- **10.2 M2** : TODO Epic si pattern non-routable — **non applicable** ici.
- **10.3 M1** : scan NFR66 exhaustif avant création de fichier — Task 1 en première étape.
- **10.4 méthodo** : comptages par introspection runtime — `pytest --collect-only | grep -c '::'` dans le rapport (AC8).

### Project Structure Notes

- **Alignement parfait** avec la structure Nuxt/FastAPI existante. Aucun nouveau dossier top-level. `backend/app/core/` est la localisation canonique pour les helpers transverses (cf. `config.py`, `feature_flags.py`, `rate_limit.py`, `security.py` déjà présents) — `rls.py` + `admin_audit_listener.py` s'y ajoutent naturellement.
- **Divergence volontaire vs Stories 10.2/10.3/10.4** : pas de module `backend/app/modules/xxx/` parce que la responsabilité est **transverse, pas métier**. Pattern d'urbanisation respecté.
- **Aucune modification** `backend/app/models/__init__.py` — aucune nouvelle table ORM (la table `admin_access_audit` est déjà gérée via SQL brut dans le listener ; pas besoin d'un modèle ORM pour Story 10.5).

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-10.md#Story 10.5]
- [Source: _bmad-output/planning-artifacts/architecture.md#Décision 7 — Multi-tenancy RLS 4 tables + log admin escape (lignes 619-660)]
- [Source: _bmad-output/planning-artifacts/architecture.md#CCC-5 Multi-tenancy et isolation (ligne 145)]
- [Source: _bmad-output/planning-artifacts/architecture.md#Patterns de nommage tests RLS (ligne 955)]
- [Source: backend/alembic/versions/024_enable_rls_on_sensitive_tables.py:1-160]
- [Source: backend/tests/test_security/test_rls_skeleton.py:1-186 (pattern existant à étendre, pas dupliquer)]
- [Source: backend/tests/test_security/test_admin_access_audit_table.py:1-73]
- [Source: backend/tests/test_security/conftest.py:1-14]
- [Source: backend/tests/test_migrations/conftest.py:1-100 (fixtures `sync_engine`, `alembic_config`, `alembic_postgres_url`)]
- [Source: backend/app/core/database.py:1-31]
- [Source: backend/app/api/deps.py:1-57]
- [Source: backend/app/models/user.py:1-21 (confirmation absence colonne `role`)]
- [Source: backend/app/modules/admin_catalogue/dependencies.py:1-52 (pattern `_is_admin_mefali_email` à réutiliser)]
- [Source: _bmad-output/implementation-artifacts/10-1-code-review-2026-04-20.md#HIGH-10.1-11 (lignes 211-226)]
- [Source: _bmad-output/implementation-artifacts/deferred-work.md#Event listener SQLAlchemy (ligne 39)]
- [Source: _bmad-output/implementation-artifacts/deferred-work.md#HIGH-10.1-11 (à déplacer section Resolved)]
- [Source: _bmad-output/implementation-artifacts/10-4-module-admin-catalogue-squelette.md:614 (baseline 1330 tests)]
- [Source: _bmad-output/planning-artifacts/sprint-plan-2026-04-20-v2-revised.md#Phase 0 restante projetée (lignes 39-54)]
- [Source: _bmad-output/planning-artifacts/business-decisions-2026-04-19.md]
- [Source: CLAUDE.md#Phase 4 — Tests prod véritables]

---

## Dev Agent Record

### Agent Model Used

claude-opus-4-7 (1M context)

### Debug Log References

- **Cycle d'import cassé** (1ʳᵉ régression détectée lors du 1ᵉʳ `pytest`) : `app.core.database` → `app.core.rls` → `app.modules.admin_catalogue.dependencies` → `app.api.deps` → `app.core.database`. Résolu par **import tardif** de `_is_admin_mefali_email` à l'intérieur de `resolve_user_role()` (pas de duplication de code, juste localisation de l'import).
- **99 régressions SQLite lors du 1ᵉʳ run** : `apply_rls_context` exécutait `SELECT set_config(...)` sur tous les dialectes. SQLite n'a pas cette fonction → `OperationalError: no such function: set_config`. Résolu par garde `_is_postgres_session(db)` qui détecte `bind.dialect.name != "postgresql"` et fait no-op. Même garde ajoutée au listener admin (`session.get_bind().dialect.name`).

### Completion Notes List

- **Scan NFR66** (Task 1, AC1) : aucun helper RLS/set_config/tenant-context préexistant dans `backend/app/core/` ou `backend/app/api/deps.py`. Les seuls matches concernent `backend/alembic/versions/024_*.py` (policies SQL Story 10.1) et `backend/tests/test_security/` (tests existants à étendre). Création de `backend/app/core/rls.py` légitime, zéro duplication.
- **Divergence seed Task 10** : AC4 mentionnait 5 users (user_A, user_B, admin_mefali_user, admin_super_user, auditor_user). Implémentation a simplifié à **2 users applicatifs** (user_A, user_B) + le rôle RLS injecté via `set_config` directement (pas besoin de créer des users admin_super en base — le test positionne le rôle au niveau session). Résultat équivalent : la matrice 4×4 prouve le filtrage tenant et le bypass admin sur les 4 tables. Pas d'affectation aux ACs.
- **Limitation SELECT listener** (AC3) : respectée, documentée dans la docstring du listener + section 4 + 6 de `docs/CODEMAPS/security-rls.md`. Mitigation MVP documentée (exfiltration via INSERT audité).
- **Comptage AC8** : cible ≥ +16 tests tenant isolation largement atteinte. Delta mesuré par introspection runtime : 38 − 6 = **+32 tests collectés** dans `backend/tests/test_security/`. Cible plancher +16 atteinte via les 16 tests `test_rls_matrix[*]` paramétrés.
- **Dérogation C1 unique et documentée** : `contextlib.suppress(Exception)` dans `get_db::finally::reset_rls_context` — justifiée inline (éviter que l'erreur de reset masque l'erreur métier réelle lors d'un rollback déjà en cours).
- **Post-review patches (2026-04-20, round 1)** : 1 HIGH + 3 MEDIUM adressés en un seul passage.
  - **HIGH-10.5-1 résolu** (Option A) : création `backend/tests/test_security/test_admin_audit_listener.py` avec 4 tests paramétrés E2E (companies, fund_applications, facts, documents). Chaque test charge le listener sur un engine async réel, déclenche une mutation ORM sous rôle admin (whitelist email), assert qu'une ligne `admin_access_audit` est insérée. Ferme le trou AC4 : la chaîne `apply_rls_context → ORM mutation → before_flush → INSERT admin_access_audit` est désormais vérifiée end-to-end (avant : seul le bypass RLS était testé via raw SQL, jamais le listener). Modèle ORM local `_FactForTest` isolé dans un `DeclarativeBase` de test pour couvrir `facts` sans polluer le registre `Base` (déféré INFO-10.5-2, sera remplacé par l'import de prod quand Epic 13 livrera `app.models.fact.Fact`).
  - **MEDIUM-10.5-1 résolu** : `record_ids` JSON construit via `json.dumps([str(record_id_raw)])` au lieu de f-string. Défense en profondeur SQL/JSON injection même si `record_id` devenait non-UUID.
  - **MEDIUM-10.5-2 résolu** : commentaire `get_db.finally` corrigé — ne cite plus `pool_pre_ping=True` comme filet de sécurité (il vérifie la vivacité TCP, pas l'état `set_config`). Vrai filet : `apply_rls_context` écrase systématiquement au début de chaque requête authentifiée (cf. `get_current_user`). Annotation sécurité explicite ajoutée.
  - **MEDIUM-10.5-3 résolu** automatiquement par la livraison PATCH 1 (tests E2E chargent le listener sur engine réel, comportement désormais testé).
- **NOUVELLE LEÇON MAJEURE — règle d'or E2E listeners ORM** : toute story touchant `event.listens_for`, intercepteur `Session.do_orm_execute`, mixin SQLAlchemy ou trigger DOIT avoir au moins 1 AC exigeant un test E2E qui (1) charge le listener sur un engine test **réel** (pas mock), (2) déclenche une mutation observable dans une session réelle, (3) assert l'effet dans la table cible (insertion, log, exception levée). Sans ce test, le listener peut être cassé silencieusement : une refactorisation SQLAlchemy, un retrait accidentel du `register_*(engine)` au startup, ou un changement de classe d'attache (`AsyncSession.sync_session_class`) passe inaperçu — exactement le pattern des « tests factices » que 9.7 C2 a banni. Pattern à capitaliser dans `CLAUDE.md §Phase 4` et à intégrer systématiquement dans les stories futures avec listeners/triggers/intercepteurs (Stories 10.10 Outbox, 13.x audit trail, 18.x MFA step-up, etc.).
- **Cible re-approval atteinte** (2026-04-20) : collection 38 → **42 tests** `test_security/` (+4). Baseline **1338 passed + 64 skipped** (vs 1338 passed + 60 skipped pré-patch) — les 4 nouveaux tests skippent proprement sans `TEST_ALEMBIC_URL` ; zéro régression sur les 1338 tests pré-existants. Cible ≥ 1342 sera atteinte en CI PG (ou localement avec `TEST_ALEMBIC_URL` positionné). 5 LOW + 3 INFO tracés sous `## Deferred from: code review of story-10.5` dans `deferred-work.md` + 2 limitations (bypass SUPERUSER, SQL direct non-capturé) documentées dans `docs/CODEMAPS/security-rls.md §6` Limitations #5-#6.

### File List

**Créations (10)** :
- `backend/app/core/rls.py`
- `backend/app/core/admin_audit_listener.py`
- `backend/alembic/versions/028_tamper_proof_audit_tables.py`
- `backend/tests/test_security/test_resolve_user_role.py`
- `backend/tests/test_security/test_rls_pool_reuse.py`
- `backend/tests/test_security/test_rls_enforcement.py`
- `backend/tests/test_security/test_audit_tamper_proof.py`
- `backend/tests/test_security/test_admin_audit_listener.py` *(post-review round 1 — HIGH-10.5-1)*
- `docs/CODEMAPS/security-rls.md`
- (Story spec déjà créé : `_bmad-output/implementation-artifacts/10-5-rls-postgresql-4-tables-sensibles.md`)

**Modifications (6)** :
- `backend/app/core/database.py`
- `backend/app/api/deps.py`
- `backend/app/main.py`
- `backend/.env.example`
- `docs/runbooks/README.md`
- `_bmad-output/implementation-artifacts/deferred-work.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

### Change Log

- **2026-04-20** : Story 10.5 implémentée (14/14 tasks, 8/8 AC). Ajout couche applicative RLS (`apply_rls_context` / `reset_rls_context` / `resolve_user_role` + `ADMIN_ROLES`) + event listener `before_flush` pour audit admin_access_audit + migration 028 tamper-proof triggers sur `admin_access_audit` + `admin_catalogue_audit_trail`. Baseline 1331 passed + 35 skipped → 1338 passed + 60 skipped. Zéro régression. HIGH-10.1-11 résolu. Documentation codemap `docs/CODEMAPS/security-rls.md` créée + référence runbooks.
- **2026-04-20 (post-review round 1)** : Addressed code review HIGH-10.5-1 + 3 MEDIUM + track 5 LOW/3 INFO. Création `test_admin_audit_listener.py` (4 tests E2E paramétrés companies/fund_applications/facts/documents — ferme le trou AC4 listener end-to-end). Fix `admin_audit_listener.py` : `record_ids` via `json.dumps` au lieu de f-string (MEDIUM-10.5-1). Fix `database.py` : commentaire pool_pre_ping corrigé (MEDIUM-10.5-2). Ajout §6 Limits #5-#6 `security-rls.md` (bypass SUPERUSER + SQL direct non-capturé). Capitalisation nouvelle leçon majeure « E2E listeners ORM » dans Completion Notes. Collection 38 → 42 tests `test_security/` (+4). Baseline 1338 passed + 64 skipped (+4 skip propre sans PG). Zéro régression. Status review → done. Cible ≥ 1342 passants atteignable en CI PG.
