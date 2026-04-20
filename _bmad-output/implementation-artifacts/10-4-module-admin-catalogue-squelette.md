# Story 10.4 : Module `admin_catalogue/` squelette (backend UI-only + 5 modèles catalogue + dépendance `require_admin_mefali`)

Status: done

> **Contexte** : 4ᵉ story Epic 10 Fondations Phase 0 (BLOQUANT Cluster B Epic 13 FR17–FR26 + Cluster intermediaries/funds admin workflows). Socle technique minimal du module `admin_catalogue` — router REST stub (5 sous-ressources CRUD N1 : `fact-types`, `criteria`, `packs`, `rules`, `referentials`), service, schemas Pydantic, models SQLAlchemy ORM mappés sur les tables catalogue (`criteria`, `packs`, `referentials`, `criterion_derivation_rules`, `admin_catalogue_audit_trail`), dépendance `require_admin_mefali` stub, `fact_type_registry.py` stub country-agnostic.
>
> **Divergence majeure vs Stories 10.2 / 10.3** (Clarification 2 architecture.md) :
> 1. **PAS de `admin_node`** dans `backend/app/graph/nodes.py` — module **UI-only**, aucun couplage LLM.
> 2. **PAS de tools dans `INSTRUMENTED_TOOLS`** — le catalogue est géré par formulaires admin, pas par chat conversationnel.
> 3. **Dépendance `require_admin_mefali`** distincte de `get_current_user` — les rôles user PME (`owner`/`editor`/`viewer`) accèdent 401/403, seuls `admin_mefali` + `admin_super` (quand Epic 18 livre le MFA) atteignent 501.
>
> **Scope strict MVP** : CRUD **N1 uniquement** (draft → review_requested par un admin_mefali). Les transitions N2 (peer review → reviewed) et N3 (published/archived) sont **déférées à Epic 13 Story 13.8b/c** (FR64 state machine complète). Le squelette **déclare** l'enum `NodeState` à 5 valeurs pour figer l'invariant, mais les endpoints N2/N3 n'existent pas encore.
>
> **Dépendances** :
> - Story 10.1 **done** (migrations 022 `create_esg_3_layers` + 025 `add_source_tracking_constraints` + 026 `create_admin_catalogue_audit_trail` — les tables consommées par les 5 modèles ORM existent déjà).
> - Story 9.7 **done** (`with_retry` + `log_tool_call` — **non consommés** ici car pas de tool LangChain, mais leçon C1/C2 restent applicable le jour où Epic 13 livrerait un tool admin_catalogue exceptionnel).
> - Story 10.2 **done** (pattern `projects/` — **dupliquer la structure**, retirer feature flag + graph wiring + tools).
> - Story 10.3 **done** (pattern `maturity/` — **dupliquer** la version sans feature flag, retirer node + tools).
>
> **Bloque** :
> - Story 10.12 (Audit trail catalogue) qui branche l'écriture dans `admin_catalogue_audit_trail` sur chaque mutation (à la fin de chaque POST/PATCH/DELETE Epic 13 réel).
> - Epic 13 entier (FR17–FR26 Cluster B ESG 3 couches admin workflows + workflows N2/N3).
> - Story 13.8b/c (workflow peer-review + transitions `review_requested → reviewed → published`).

---

## Story

**As a** Admin Mefali (représenté ici par l'Équipe Mefali backend),
**I want** disposer du socle technique minimal du module `admin_catalogue` **UI-only** côté backend (router REST stub CRUD N1 pour 5 entités catalogue, service 5+ fonctions stub, schemas Pydantic, models SQLAlchemy ORM mappés sur migrations 022/026, dépendance `require_admin_mefali` qui renvoie 403 aux rôles user PME et 401 aux non-authentifiés),
**So that** les 6 stories Epic 13 + Story 10.12 puissent y déposer la logique métier (facts/criteria CRUD, packs, referentials, rules, audit trail, workflow N2/N3 peer review) **sans recréer la plomberie**, et que l'architecture « chat user PME » / « UI admin Mefali » reste **étanche** dès le squelette (Clarification 2 : aucun `admin_node` LangGraph).

---

## Acceptance Criteria

### AC1 — Structure du module `backend/app/modules/admin_catalogue/` conforme au pattern `modules/maturity/` (sans feature flag, sans calculator)

**Given** le repository dans l'état `main @ HEAD` avec Story 10.1 mergée (migrations 022 + 025 + 026 appliquées) et Stories 10.2 + 10.3 mergées (patterns `projects/` / `maturity/` établis),
**When** un développeur exécute `ls backend/app/modules/admin_catalogue/`,
**Then** le dossier contient **exactement** les fichiers suivants (pattern brownfield `modules/maturity/` — NFR62 CLAUDE.md) :
  - `__init__.py` (docstring 1 ligne : « Module Admin Catalogue : workflow admin UI-only (FR17–FR26, FR64). »)
  - `router.py` (APIRouter préfixe `/api/admin/catalogue`, tags `["admin-catalogue"]`)
  - `service.py` (fonctions métier — stubs `NotImplementedError("Story 10.4 skeleton — implemented in Epic 13 story 13-X / Story 10.12")`)
  - `schemas.py` (Pydantic v2 : schemas lecture/écriture pour les 5 entités + `NodeStateEnum`, `CatalogueActionEnum`, `WorkflowLevelEnum`)
  - `models.py` (SQLAlchemy 2.0 ORM : `Criterion`, `Referential`, `Pack`, `CriterionDerivationRule`, `AdminCatalogueAuditTrail` — mappés **exactement** sur les tables créées par migrations 022 + 026 ; `FactType` **n'est PAS** une table physique MVP → exposé via `fact_type_registry.py` enum/constante, voir AC7)
  - `enums.py` (`NodeStateEnum`, `CatalogueActionEnum`, `WorkflowLevelEnum` — **source unique** réutilisée par `schemas.py`, `models.py`, `service.py`)
  - `events.py` (squelette avec 5 constantes `CATALOGUE_CRITERION_PUBLISHED_EVENT_TYPE`, `CATALOGUE_REFERENTIAL_PUBLISHED_EVENT_TYPE`, `CATALOGUE_PACK_PUBLISHED_EVENT_TYPE`, `CATALOGUE_RULE_PUBLISHED_EVENT_TYPE`, `CATALOGUE_ENTITY_RETIRED_EVENT_TYPE` + docstring documentant les payloads — **pas d'émission réelle MVP**, préparation D11 CCC-14 consommée par Story 10.10)
  - `fact_type_registry.py` (constante `FACT_TYPE_CATALOGUE: list[str]` country-agnostic + docstring rappelant FR17 + guard NFR66 — voir AC7)
  - `dependencies.py` (nouvelle dépendance FastAPI **`require_admin_mefali`** = stub retournant 401 si non-authentifié et 403 si rôle ≠ admin, voir AC4 — **fichier dédié pour faciliter import transverse Epic 13 + Story 10.12**)
**And** tous les fichiers ont une docstring d'en-tête `"""<description courte>.\n\nStory 10.4 — module `admin_catalogue/` squelette (UI-only).\nFR covered: [] (infra FR17–FR26 + FR64), NFR covered: [NFR27, NFR28, NFR62, NFR64, NFR66].\n"""`
**And** `from app.modules.admin_catalogue import router, service, schemas, models, enums, events, fact_type_registry, dependencies` **importe sans erreur** et sans warning d'import circulaire (vérifier `python -c "import app.modules.admin_catalogue as m; print(sorted(dir(m)))"`).
**And** **AUCUN** fichier `formalization_plan_calculator.py` ni équivalent — le module admin_catalogue n'a pas de calculator métier (différence vs `maturity/`).

### AC2 — `models.py` expose 5 modèles ORM SQLAlchemy 2.0 mappés sur migrations 022 + 026

**Given** les migrations 022 (`criteria`, `criterion_derivation_rules`, `referentials`, `referential_versions`, `referential_migrations`, `criterion_referential_map`, `packs`, `pack_criteria`, `referential_verdicts`) + 026 (`admin_catalogue_audit_trail`) appliquées,
**When** un développeur importe les modèles et exécute un cycle CRUD SQLite in-memory,
**Then** les 5 modèles **obligatoires** respectent strictement le schéma des migrations (vérifier `backend/alembic/versions/022_create_esg_3_layers.py` + `026_create_admin_catalogue_audit_trail.py` **ligne à ligne**) :

  1. **`Criterion`** (table `criteria` migration 022 lignes 107–140) : `id UUID PK, code UNIQUE String(64), label_fr String(255) NOT NULL, description TEXT NULLABLE, dimension String(32) NOT NULL, workflow_state String(16) DEFAULT 'draft', is_published Boolean DEFAULT false, source_url TEXT NULLABLE, source_accessed_at TIMESTAMPTZ NULLABLE, source_version String(64) NULLABLE, created_at, updated_at` + `UniqueConstraint("code", name="uq_criteria_code")`.
  2. **`Referential`** (table `referentials` migration 022 lignes 178–210) : mêmes colonnes que `Criterion` sauf `dimension` absent + `UniqueConstraint("code", name="uq_referentials_code")`.
  3. **`Pack`** (table `packs` migration 022 lignes 273–304) : `id UUID PK, code UNIQUE String(64), label_fr String(255) NOT NULL, workflow_state String(16) DEFAULT 'draft', is_published Boolean DEFAULT false, source_url/source_accessed_at/source_version`, `UniqueConstraint("code", name="uq_packs_code")`. **Pas de `dimension` ni `description`** (divergence migration — respecter).
  4. **`CriterionDerivationRule`** (table `criterion_derivation_rules` migration 022 lignes 154–175) : `id UUID PK, criterion_id UUID FK criteria.id ON DELETE CASCADE, rule_type String(32) CHECK IN ('threshold','boolean_expression','aggregate','qualitative_check'), rule_json JSONB NOT NULL, version Integer DEFAULT 1, created_at`. **Pas de `updated_at`** (la migration ne le déclare pas — respecter).
  5. **`AdminCatalogueAuditTrail`** (table `admin_catalogue_audit_trail` migration 026 lignes 35–89) : `id UUID PK, actor_user_id UUID FK users.id ON DELETE RESTRICT, entity_type String(64), entity_id UUID, action Enum('create','update','delete','publish','retire') CHECK, workflow_level Enum('N1','N2','N3') CHECK, workflow_state_before String(32) NULLABLE, workflow_state_after String(32) NULLABLE, changes_before JSONB NULLABLE, changes_after JSONB NULLABLE, ts TIMESTAMPTZ DEFAULT now() NOT NULL, correlation_id UUID NULLABLE` + 3 index composite (`entity_type+entity_id+ts`, `actor_user_id+ts`, `workflow_level+ts`). **Append-only côté ORM** : pas de `__table_args__` update/delete policy MVP (Story 10.12 ajoutera les triggers PostgreSQL).

**And** les types utilisent `UUIDMixin` + `TimestampMixin` de `app.models.base` **uniquement pour les 4 entités qui ont `created_at`+`updated_at`** (Criterion, Referential, Pack). **`CriterionDerivationRule` et `AdminCatalogueAuditTrail` N'UTILISENT PAS** `TimestampMixin` (leur migration ne déclare qu'une des deux colonnes ; respecter strict).
**And** `enums.py::NodeStateEnum` a **exactement** les 5 valeurs `{draft, review_requested, reviewed, published, archived}` (Décision 6 state machine N1/N2/N3 complète — figée **dès Story 10.4** pour éviter refactor invariant en Epic 13.8b/c). **Cohérence côté BDD** : la colonne `workflow_state` est `String(16)` donc les 5 valeurs tiennent ; l'enum Python est l'invariant code-side.
**And** `enums.py::CatalogueActionEnum` a **exactement** les 5 valeurs `{create, update, delete, publish, retire}` (miroir du `catalogue_action_enum` PostgreSQL migration 026 ligne 43–51).
**And** `enums.py::WorkflowLevelEnum` a **exactement** les 3 valeurs `{N1, N2, N3}` (miroir du `workflow_level_enum` PostgreSQL migration 026 ligne 56–62).
**And** les 5 modèles sont **enregistrés dans `app/models/__init__.py`** via import explicite `from app.modules.admin_catalogue.models import Criterion, Referential, Pack, CriterionDerivationRule, AdminCatalogueAuditTrail  # noqa: F401` (sinon `Base.metadata.create_all` les ignore, cassant tests SQLite — **piège validé en 10.2 et 10.3**).
**And** cross-dialects : `rule_json`, `changes_before`, `changes_after` utilisent `JSONB().with_variant(JSON(), "sqlite")` via helper `_jsonb()` local (pattern `projects/models.py:46-48` + `maturity/models.py` à dupliquer — auto-suffisance module).

### AC3 — `router.py` expose 5 endpoints stubs CRUD N1 avec ordre strict `401 → 403 → 501`

**Given** `backend/app/modules/admin_catalogue/router.py` branché dans `backend/app/main.py` via `app.include_router(admin_catalogue_router, prefix="/api/admin/catalogue", tags=["admin-catalogue"])`,
**When** un client appelle les endpoints sans JWT valide (header `Authorization` absent ou invalide),
**Then** **tous** les endpoints renvoient **401 Unauthorized** (dépendance `Depends(get_current_user)` **injectée transitivement** via `Depends(require_admin_mefali)` — voir AC4).
**And** les **5 endpoints CRUD N1 stubs** exposés sont (alignés sur les 5 entités catalogue AC2 + `fact-types` read-only registry) :
  - `GET /api/admin/catalogue/fact-types` → liste des fact types autorisés (lecture du registry `FACT_TYPE_CATALOGUE`) — **le SEUL endpoint qui retourne 200 effectivement** (pas de stub 501, voir AC7).
  - `POST /api/admin/catalogue/criteria` → création `Criterion` draft — stub 501.
  - `POST /api/admin/catalogue/referentials` → création `Referential` draft — stub 501.
  - `POST /api/admin/catalogue/packs` → création `Pack` draft — stub 501.
  - `POST /api/admin/catalogue/rules` → création `CriterionDerivationRule` draft — stub 501.
**And** les endpoints `POST /criteria`, `POST /referentials`, `POST /packs`, `POST /rules` acceptent un body Pydantic respectif (`CriterionCreate`, `ReferentialCreate`, `PackCreate`, `CriterionDerivationRuleCreate` définis dans `schemas.py`) validé **avant** le raise 501 (sémantique Epic 13 réelle préservée dans OpenAPI).
**And** **contrairement à `projects/` et `maturity/`**, **la dépendance principale n'est PAS `Depends(get_current_user)` mais `Depends(require_admin_mefali)`** (différence critique AC4 — les 4 endpoints mutants injectent cette dépendance en première position, l'endpoint `GET /fact-types` également pour cohérence — aucun rôle non-admin ne lit même les fact types en MVP).
**And** la documentation OpenAPI de chaque endpoint mutant **inclut** `responses={501: {"description": "Admin Catalogue skeleton — Epic 13 not yet delivered"}, 403: {"description": "Accès réservé au rôle admin_mefali"}}` ; l'endpoint `GET /fact-types` **inclut** uniquement `responses={403: {...}}` (pas de 501 car il retourne 200 effectif).
**And** l'ordre des dependencies respecte strictement **401 → 403 → 501** : `admin: User = Depends(require_admin_mefali)` en **premier argument positionnel** de chaque endpoint — FastAPI résout cette dépendance avant le corps, donc 401 (token absent) ou 403 (rôle user PME) primeront systématiquement sur 501.
**And** **AUCUN feature flag** n'est introduit (`ENABLE_ADMIN_CATALOGUE_MODEL` interdit — cohérence arbitrage 10.3 + parsimonie env var).
**And** **AUCUN endpoint de workflow N2/N3** (`POST /criteria/{id}/request-review`, `POST /criteria/{id}/approve`, `POST /criteria/{id}/publish`) n'est exposé dans Story 10.4 — **déféré à Epic 13 Story 13.8b/c**. Documenter ce défer dans la docstring de `router.py` (évite qu'un dev confonde MVP avec livraison complète).

### AC4 — Dépendance `require_admin_mefali` stub enforce 401/403 sans model `role` en base

**Given** le modèle `User` actuel (`backend/app/models/user.py`) ne possède **PAS** de colonne `role` (vérifié : champs = `email`, `hashed_password`, `full_name`, `company_name`, `is_active`, + mixins `UUIDMixin`/`TimestampMixin`),
**When** `backend/app/modules/admin_catalogue/dependencies.py` est implémenté,
**Then** il expose **exactement** :

```python
from fastapi import Depends, HTTPException, status
from app.api.deps import get_current_user
from app.models.user import User

# AC4 — whitelist admin temporaire MVP (Story 10.4 squelette).
# Epic 18 (FR61) livrera le champ `User.role` + MFA ; en attendant, les emails
# admin sont whitelistés via variable d'env ADMIN_MEFALI_EMAILS (comma-separated)
# ou, à défaut, la liste retourne toujours 403 sauf si l'email correspond exactement.
def _is_admin_mefali_email(email: str) -> bool:
    import os
    allowed = os.environ.get("ADMIN_MEFALI_EMAILS", "")
    return email.strip().lower() in {e.strip().lower() for e in allowed.split(",") if e.strip()}

async def require_admin_mefali(
    current_user: User = Depends(get_current_user),
) -> User:
    """Stub : enforce l'accès admin_mefali tant que FR61 (Epic 18 — colonne User.role + MFA) n'est pas livrée.

    MVP : whitelist d'emails via env var `ADMIN_MEFALI_EMAILS` (comma-separated).
    Epic 18 remplacera cette logique par `if current_user.role not in {"admin_mefali","admin_super"}: raise 403`.
    """
    if not _is_admin_mefali_email(current_user.email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé au rôle admin_mefali (FR61 livré en Epic 18).",
        )
    return current_user
```

**And** les tests (AC8) couvrent **exactement** les 3 cas :
  1. **401** : header `Authorization` absent → 401 (`get_current_user` prime, la dépendance `require_admin_mefali` ne s'exécute même pas).
  2. **403** : JWT valide d'un user **non-whitelisté** (env `ADMIN_MEFALI_EMAILS` vide OU email user absent de la liste) → 403 avec detail contenant `"admin_mefali"` ET `"Epic 18"`.
  3. **501** : JWT valide d'un user **whitelisté** (fixture `monkeypatch.setenv("ADMIN_MEFALI_EMAILS", "admin@mefali.test")` + fixture `authenticated_client` avec email `admin@mefali.test`) → 501 pour les 4 POST stubs et 200 pour `GET /fact-types`.
**And** **AUCUNE migration** n'est créée par cette story pour ajouter `User.role` — le scope est explicitement le stub whitelist (Epic 18 créera la migration 028+ pour la colonne `role` + MFA). Story 10.4 **ne préjuge pas** du schéma futur.
**And** le fichier `dependencies.py` fait **< 60 lignes** (simplicité stub).

### AC5 — `service.py` expose la surface d'API consommée par Epic 13 + Story 10.12 sans accéder directement aux tables (anti-God NFR64)

**Given** un futur consommateur Epic 13 (router Epic 13.1 `criteria` CRUD complet, workflow N2/N3 13.8b/c, handler audit trail 10.12),
**When** il importe `from app.modules.admin_catalogue.service import create_criterion, create_referential, create_pack, create_derivation_rule, list_fact_types, record_audit_event, transition_workflow_state`,
**Then** les **7 fonctions** sont **présentes** dans `service.py` avec signatures typées :
  - `async def create_criterion(db: AsyncSession, *, code: str, label_fr: str, dimension: str, description: str | None, actor_user_id: UUID) -> Criterion` — Epic 13.1.
  - `async def create_referential(db: AsyncSession, *, code: str, label_fr: str, description: str | None, actor_user_id: UUID) -> Referential` — Epic 13.2.
  - `async def create_pack(db: AsyncSession, *, code: str, label_fr: str, actor_user_id: UUID) -> Pack` — Epic 13.3.
  - `async def create_derivation_rule(db: AsyncSession, *, criterion_id: UUID, rule_type: str, rule_json: dict, actor_user_id: UUID) -> CriterionDerivationRule` — Epic 13.1bis.
  - `async def list_fact_types() -> list[str]` — **SEULE fonction non-stub** : retourne `list(FACT_TYPE_CATALOGUE)` depuis `fact_type_registry` (AC7 — cette fonction est appelée par `GET /fact-types` et doit retourner la liste réelle).
  - `async def record_audit_event(db: AsyncSession, *, actor_user_id: UUID, entity_type: str, entity_id: UUID, action: CatalogueActionEnum, workflow_level: WorkflowLevelEnum, workflow_state_before: str | None, workflow_state_after: str | None, changes_before: dict | None, changes_after: dict | None, correlation_id: UUID | None) -> AdminCatalogueAuditTrail` — Story 10.12 (point d'entrée **unique** pour toute écriture dans `admin_catalogue_audit_trail` — NFR64 anti-God).
  - `async def transition_workflow_state(db: AsyncSession, *, entity_type: str, entity_id: UUID, from_state: NodeStateEnum, to_state: NodeStateEnum, actor_user_id: UUID) -> None` — Story 13.8b/c (peer review + publish). Docstring documente l'invariant de transition légales (`draft → review_requested → reviewed → published → archived`, transitions illégales raise).

**And** chaque fonction **sauf `list_fact_types`** lève **`NotImplementedError("Story 10.4 skeleton — implemented in Epic 13 story 13-X / Story 10.12")`** (message explicite — les tests unitaires vérifient l'exception, PAS la logique).
**And** **`list_fact_types` retourne `list(FACT_TYPE_CATALOGUE)` effectivement** — c'est la seule fonction « active » du service MVP (testée par AC7 + AC8).
**And** **anti-pattern God service (NFR64)** : `service.py` **n'a aucun `select(...)` inline dans les 6 stubs** ; aucune autre fonction ne lit/écrit directement les tables `criteria`/`referentials`/`packs`/`criterion_derivation_rules`/`admin_catalogue_audit_trail`. Les consommateurs externes (router Epic 13, handler audit Story 10.12, workflow state machine 13.8b/c) **doivent passer par ces 7 fonctions**, jamais par un `select(Criterion)` inline.
**And** la fonction `record_audit_event` a une **docstring explicite** rappelant que toute mutation catalogue (Epic 13) **doit** l'appeler dans la même transaction DB — argument `correlation_id` reçoit le `request_id` pour traçabilité NFR37 (doc uniquement MVP, wiring Story 10.12).

### AC6 — Graphe LangGraph intouché : AUCUN `admin_node`, AUCUN tool, test smoke d'absence

**Given** Clarification 2 architecture.md et CLAUDE.md — **le module admin_catalogue est strictement UI-only, sans couplage LLM**,
**When** `backend/app/graph/nodes.py` et `backend/app/graph/graph.py` sont inspectés,
**Then** **AUCUN** `admin_node`, `admin_catalogue_node`, `catalogue_node` ou équivalent n'est ajouté. La liste des nœuds reste identique à post-10.3 (11 nœuds : `router_node`, `document_node`, `chat_node`, `esg_scoring_node`, `carbon_node`, `financing_node`, `application_node`, `credit_node`, `action_plan_node`, `project_node`, `maturity_node`).
**And** `backend/app/graph/tools/` ne reçoit **AUCUN** fichier `admin_catalogue_tools.py` ni équivalent. `INSTRUMENTED_TOOLS` reste à **36 tools** (inchangé vs post-10.3). Le compteur de `backend/app/graph/tools/README.md` **n'est pas modifié** par cette story.
**And** un **test smoke** `backend/tests/test_graph/test_admin_catalogue_absence_from_graph.py` vérifie :
  - `"admin" not in compiled_graph.nodes` ET `"admin_catalogue" not in compiled_graph.nodes` ET `"catalogue" not in compiled_graph.nodes`.
  - Aucun tool de `INSTRUMENTED_TOOLS` n'a `node_name == "admin"` ni `"admin_catalogue"`.
  - Aucun module Python n'existe sous `app/graph/tools/admin*` (scan `glob`).
**And** dans `backend/app/graph/graph.py::build_graph`, un **commentaire explicite** est ajouté au-dessus du dernier `create_tool_loop(...)` :

```python
# Story 10.4 : le module admin_catalogue est UI-only (Clarification 2 architecture.md).
# AUCUN admin_node n'est enregistré ici — les endpoints /api/admin/catalogue/*
# sont consommés par l'UI admin Mefali (formulaires), pas par le chat LLM.
# Cette absence est enforced par test_admin_catalogue_absence_from_graph.py.
```

**Rationale** : documenter explicitement l'ABSENCE empêche un futur contributeur Epic 13 ou Epic 18 de se demander « pourquoi il n'y a pas d'admin_node ? » et de casser l'architecture par tentative de « complétude ». **Applique la leçon capitalisée « TODO explicite Epic si pattern non-routable »** en version négative (commentaire au lieu de TODO).

### AC7 — `fact_type_registry.py` country-agnostic + scan NFR66 étendu EXHAUSTIF aux 9 fichiers du module

**Given** FR17 (« L'admin catalogue publie la liste des `fact_type` autorisés »),
**When** `backend/app/modules/admin_catalogue/fact_type_registry.py` est inspecté,
**Then** il expose **exactement** :

```python
"""Registry des fact_type autorisés (FR17 — Story 10.4 squelette).

Country-agnostic par construction — aucun pays listé ici. Les référentiels
spécifiques (ex. UEMOA, BCEAO) sont chargés en base via `AdminMaturityRequirement`
et `Referential`, pas dans ce registry.

Epic 13 Story 13.1 pourra étendre cette liste OU basculer vers une table BDD
`admin_fact_types` (décision déférée). Story 10.4 fige le contrat : liste
string immutable.
"""
from __future__ import annotations

from typing import Final

FACT_TYPE_CATALOGUE: Final[tuple[str, ...]] = (
    "energy_consumption_kwh",
    "water_consumption_m3",
    "waste_tonnes",
    "co2_scope1_tonnes",
    "co2_scope2_tonnes",
    "co2_scope3_tonnes",
    "employees_count",
    "female_employees_ratio",
    "training_hours_per_employee",
    "governance_board_independence_ratio",
    "financial_revenue_xof",
    "informal_activity_share_pct",
)
```

**And** la constante est un **`tuple`** (immutable), **pas une `list`** — protection contre mutation accidentelle.
**And** **`service.list_fact_types()` retourne `list(FACT_TYPE_CATALOGUE)`** (conversion explicite en list pour Pydantic response).
**And** un test `test_fact_type_registry.py::test_fact_type_catalogue_is_immutable_tuple` vérifie `isinstance(FACT_TYPE_CATALOGUE, tuple)`.

**Scan NFR66 EXHAUSTIF (leçon MEDIUM-10.3-1 Code Review) — étendu aux 9 fichiers Python du module** :

```python
# backend/tests/test_admin_catalogue/test_no_hardcoded_country_strings.py
from pathlib import Path

_ADMIN_CATALOGUE_DIR = Path(__file__).parent.parent.parent / "backend" / "app" / "modules" / "admin_catalogue"

_BANNED_COUNTRY_STRINGS = [
    "Sénégal", "Senegal",
    "Côte d'Ivoire", "Cote d'Ivoire", "Ivory Coast",
    "Mali", "Burkina Faso", "Niger", "Togo", "Bénin", "Benin",
    "Guinée", "Guinee", "Guinea",
]

def test_no_hardcoded_country_strings_in_admin_catalogue_module():
    """NFR66 — scan exhaustif des 9 fichiers .py du module (leçon 10.3 M1)."""
    targets = sorted(_ADMIN_CATALOGUE_DIR.glob("*.py"))  # scan TOUS les .py, pas seulement service+calculator
    assert len(targets) >= 9, f"Attendu ≥ 9 fichiers, trouvé {len(targets)}"
    for path in targets:
        content = path.read_text(encoding="utf-8")
        for banned in _BANNED_COUNTRY_STRINGS:
            assert banned not in content, (
                f"{path.name} contient le string pays banni '{banned}' "
                f"(NFR66 country-data-driven). Déplacer vers table BDD "
                f"(Criterion/Referential source_url) ou paramètre `country`."
            )
```

**And** **le scan se fait sur `glob("*.py")`** — pas de liste statique de 2 fichiers comme en 10.3 première itération (MEDIUM-10.3-1). Itération sur tous les fichiers du module **dès la story squelette**, même les 4 qui sont « peu à risque » (schemas, models, enums, events). Epic 13 ajoutera des fichiers → le scan les prendra automatiquement.
**And** le test vérifie également que `fact_type_registry.py` ne contient **aucun** pays (auto-vérifié par le glob).

### AC8 — Tests minimum livrés dans `backend/tests/test_admin_catalogue/` (plancher 14 tests verts)

**Given** `backend/tests/test_admin_catalogue/__init__.py` créé,
**When** `pytest backend/tests/test_admin_catalogue/ -v` + le test smoke graphe + le test instrumentation exécutés,
**Then** les **14 tests minimum** suivants passent tous (plancher +14 ≥ baseline +14 exigée) :

| # | Fichier test | Test | Vérifie |
|---|--------------|------|---------|
| 1 | `test_models.py` | `test_criterion_crud_sqlite` | INSERT → SELECT → UPDATE `is_published` → DELETE sur `Criterion` via AsyncSession SQLite |
| 2 | `test_models.py` | `test_referential_pack_unique_codes` | 2ᵉ INSERT même `code` sur `Referential` ou `Pack` lève `IntegrityError` (uq_referentials_code, uq_packs_code) |
| 3 | `test_models.py` | `test_criterion_derivation_rule_fk_cascade_on_criterion_delete` | Suppression d'un `Criterion` cascade les `CriterionDerivationRule` liés (ON DELETE CASCADE DDL validée) |
| 4 | `test_models.py` | `test_criterion_derivation_rule_check_rule_type` | INSERT `rule_type='invalid'` lève `IntegrityError` — **si PostgreSQL disponible** ; SQLite ne gère pas CHECK → test marqué `@pytest.mark.postgres` (pattern 10.1 + 10.3) |
| 5 | `test_models.py` | `test_admin_catalogue_audit_trail_indexes_declared` | `AdminCatalogueAuditTrail.__table__.indexes` contient au moins les 3 index composite (`entity_type+entity_id+ts`, `actor_user_id+ts`, `workflow_level+ts`) |
| 6 | `test_models.py` | `test_node_state_enum_has_exactly_5_values` | `NodeStateEnum` == `{draft, review_requested, reviewed, published, archived}` (figé 10.4 pour invariant 13.8b/c) |
| 7 | `test_models.py` | `test_catalogue_action_and_workflow_level_enums` | `CatalogueActionEnum` == `{create, update, delete, publish, retire}` **ET** `WorkflowLevelEnum` == `{N1, N2, N3}` (miroir PG enum migration 026) |
| 8 | `test_router.py` | `test_endpoints_return_401_without_auth` | Sans header `Authorization` → 5 endpoints (`GET /fact-types`, `POST /criteria`, `POST /referentials`, `POST /packs`, `POST /rules`) → 401 (get_current_user prime) |
| 9 | `test_router.py` | `test_endpoints_return_403_for_non_admin_user` | Fixture `authenticated_client` (user PME standard, email non-whitelisté, `ADMIN_MEFALI_EMAILS=""`) → 5 endpoints → 403 avec detail contenant `"admin_mefali"` ET `"Epic 18"` (AC4 §2) |
| 10 | `test_router.py` | `test_post_endpoints_return_501_for_admin_user` | Fixture `admin_authenticated_client` (user whitelisté via `monkeypatch.setenv("ADMIN_MEFALI_EMAILS", "admin@mefali.test")`) → 4 POST → 501 ; `GET /fact-types` → 200 avec list de 12 strings contenant `"energy_consumption_kwh"` (AC4 §3 + AC7) |
| 11 | `test_router.py` | `test_openapi_documents_403_and_501_responses` | `/openapi.json` contient `responses.403` pour les 5 endpoints **ET** `responses.501` pour les 4 POST (pas pour `GET /fact-types`) |
| 12 | `test_service.py` | `test_6_service_functions_raise_not_implemented` | Invocation des 6 fonctions service stub → `NotImplementedError` avec message contenant `"Story 10.4 skeleton"` ET (`"Epic 13"` OU `"Story 10.12"`) — `list_fact_types` exclue (table-driven `pytest.mark.parametrize`) |
| 13 | `test_service.py` | `test_list_fact_types_returns_registry_tuple_as_list` | `await list_fact_types()` retourne une `list[str]` de longueur ≥ 12 contenant les 12 fact types figés AC7 |
| 14 | `test_fact_type_registry.py` | `test_fact_type_catalogue_is_immutable_tuple_and_country_agnostic` | `isinstance(FACT_TYPE_CATALOGUE, tuple) is True` ET aucune valeur ne contient un des 13 pays bannis NFR66 (test redondant avec #15 mais ciblant la constante elle-même) |
| 15 | `test_no_hardcoded_country_strings.py` | `test_no_hardcoded_country_strings_in_admin_catalogue_module` | Scan `glob("*.py")` sur les 9 fichiers du module — AUCUN string pays banni (leçon MEDIUM-10.3-1 **appliquée exhaustivement** dès la story squelette) |
| 16 | `test_graph/test_admin_catalogue_absence_from_graph.py` | `test_no_admin_node_in_compiled_graph` | `compiled_graph.nodes` ne contient ni `"admin"`, `"admin_catalogue"`, `"catalogue"` (Clarification 2 architecture.md AC6) |
| 17 | `test_graph/test_admin_catalogue_absence_from_graph.py` | `test_no_admin_catalogue_tool_in_instrumented_tools` | `INSTRUMENTED_TOOLS` count inchangé (=36 post-10.3) **ET** aucun tool avec `node_name in {"admin", "admin_catalogue", "catalogue"}` (AC6) |
| 18 (bonus) | `test_dependencies.py` | `test_require_admin_mefali_whitelists_email_from_env` | `monkeypatch.setenv("ADMIN_MEFALI_EMAILS", "a@x.com,admin@mefali.test")` → user email `admin@mefali.test` passe, email `b@x.com` lève 403 (AC4) |
| 19 (bonus) | `test_dependencies.py` | `test_require_admin_mefali_returns_403_if_env_var_empty` | `monkeypatch.delenv("ADMIN_MEFALI_EMAILS", raising=False)` → any user email → 403 (fail-closed par défaut) |

**And** la baseline passe de **1305** tests verts (post-10.3) à **≥ 1319** tests verts (strictement +14 minimum, cible AC8 +14 tests) sans flakiness sur 3 runs consécutifs.
**And** coverage `backend/app/modules/admin_catalogue/` **≥ 80 %** (NFR60 CI gate — service stubs comptent car `NotImplementedError` est l'unique ligne, exécutée par les tests d'assertion d'exception ; `list_fact_types` et `require_admin_mefali` ont logique réelle donc coverage élevée naturellement).
**And** le scan `test_no_tool_escapes_wrapping` de `backend/tests/test_graph/test_tools_instrumentation.py` **n'a PAS besoin d'être étendu** (pas de tool ajouté) — vérifier simplement qu'il ne casse pas (**`INSTRUMENTED_TOOLS` compte toujours 36 tools**).

---

## Tasks / Subtasks

### Phase 1 — Squelette module + modèles ORM (AC1, AC2)

- [x] **Task 1 — Créer `backend/app/modules/admin_catalogue/` + 9 fichiers squelettes** (AC: 1)
  - [x] 1.1 `__init__.py` (docstring 1 ligne « Module Admin Catalogue : workflow admin UI-only (FR17–FR26, FR64). »)
  - [x] 1.2 `enums.py` : `NodeStateEnum(str, Enum)` 5 valeurs `{draft, review_requested, reviewed, published, archived}` + `CatalogueActionEnum(str, Enum)` 5 valeurs + `WorkflowLevelEnum(str, Enum)` 3 valeurs — source unique
  - [x] 1.3 `events.py` : 5 constantes `Literal[...]` payloads documentés Story 10.10
  - [x] 1.4 `fact_type_registry.py` : `FACT_TYPE_CATALOGUE: Final[tuple[str, ...]]` avec 12 entrées country-agnostic (AC7)
  - [x] 1.5 Vérifier import circulaire : `from app.modules.admin_catalogue import router, service, schemas, models, enums, events, fact_type_registry, dependencies` passe sans warning

- [x] **Task 2 — Écrire `models.py` (5 modèles ORM mappés sur migrations 022 + 026)** (AC: 2)
  - [x] 2.1 `Criterion` mappé sur `criteria` (table 022 lignes 107–140) — `UUIDMixin + TimestampMixin` + `UniqueConstraint("code", name="uq_criteria_code")` + colonnes SOURCE-TRACKING
  - [x] 2.2 `Referential` mappé sur `referentials` (022 lignes 178–210) — même pattern que `Criterion` moins `dimension`
  - [x] 2.3 `Pack` mappé sur `packs` (022 lignes 273–304) — pas de `dimension` ni `description`
  - [x] 2.4 `CriterionDerivationRule` mappé sur `criterion_derivation_rules` (022 lignes 154–175) — FK `criterion_id ON DELETE CASCADE`, CheckConstraint `rule_type IN (...)`, `rule_json` via `_jsonb()`, version Integer default 1, **PAS de TimestampMixin** (seulement `created_at`)
  - [x] 2.5 `AdminCatalogueAuditTrail` mappé sur `admin_catalogue_audit_trail` (026 lignes 35–89) — 3 index composite via `__table_args__`, enums action + workflow_level via `sa.Enum(...)`, `changes_before/after` via `_jsonb()`, **PAS de TimestampMixin** (seulement `ts`)
  - [x] 2.6 Helper `_jsonb()` local identique à `maturity/models.py` (duplication assumée, auto-suffisance module)
  - [x] 2.7 Enregistrement dans `app/models/__init__.py` via `from app.modules.admin_catalogue.models import Criterion, Referential, Pack, CriterionDerivationRule, AdminCatalogueAuditTrail  # noqa: F401`
  - [x] 2.8 `Base.metadata.create_all` SQLite crée les 5 tables — test CRUD passe (test #1)

### Phase 2 — Router stubs + service + dependencies (AC3, AC4, AC5)

- [x] **Task 3 — Créer `dependencies.py` (stub `require_admin_mefali`)** (AC: 4)
  - [x] 3.1 Fonction `_is_admin_mefali_email(email: str) -> bool` lisant `os.environ["ADMIN_MEFALI_EMAILS"]` (comma-separated, strip+lower)
  - [x] 3.2 `async def require_admin_mefali(current_user: User = Depends(get_current_user)) -> User` raise 403 avec detail contenant `"admin_mefali"` ET `"Epic 18"`
  - [x] 3.3 Docstring documente **fail-closed** par défaut (env var absente → 403) et Epic 18 remplacement prévu (`User.role` + MFA FR61)
  - [x] 3.4 Fichier < 60 lignes

- [x] **Task 4 — Créer `schemas.py` (Pydantic v2)** (AC: 1, 3)
  - [x] 4.1 Re-export `NodeStateEnum`, `CatalogueActionEnum`, `WorkflowLevelEnum` depuis `enums.py`
  - [x] 4.2 `CriterionCreate(code: str = Field(min_length=1, max_length=64), label_fr: str = Field(min_length=1, max_length=255), dimension: str = Field(min_length=1, max_length=32), description: str | None = None)`
  - [x] 4.3 `ReferentialCreate(code, label_fr, description)` similaire sans `dimension`
  - [x] 4.4 `PackCreate(code, label_fr)` minimal
  - [x] 4.5 `CriterionDerivationRuleCreate(criterion_id: UUID, rule_type: Literal["threshold","boolean_expression","aggregate","qualitative_check"], rule_json: dict, version: int = 1)`
  - [x] 4.6 `CriterionResponse`, `ReferentialResponse`, `PackResponse`, `CriterionDerivationRuleResponse`, `AdminCatalogueAuditTrailResponse` avec `ConfigDict(from_attributes=True)`
  - [x] 4.7 `FactTypeListResponse(fact_types: list[str])` pour `GET /fact-types`

- [x] **Task 5 — Créer `router.py` (5 endpoints CRUD N1)** (AC: 3, 7)
  - [x] 5.1 `GET /fact-types` → `Depends(require_admin_mefali)` + retourne `FactTypeListResponse(fact_types=await list_fact_types())` — **200 effectif** (AC7)
  - [x] 5.2 `POST /criteria` → body `CriterionCreate` validé → raise 501
  - [x] 5.3 `POST /referentials` → body `ReferentialCreate` validé → raise 501
  - [x] 5.4 `POST /packs` → body `PackCreate` validé → raise 501
  - [x] 5.5 `POST /rules` → body `CriterionDerivationRuleCreate` validé → raise 501
  - [x] 5.6 `responses={403: {...}, 501: {...}}` documenté sur les 4 POST ; `responses={403: {...}}` sur le GET
  - [x] 5.7 Dependency `admin: User = Depends(require_admin_mefali)` en **premier argument positionnel** de chaque endpoint
  - [x] 5.8 Docstring router.py documente l'ABSENCE des workflow endpoints N2/N3 (déférés Epic 13.8b/c)
  - [x] 5.9 Enregistrement dans `app/main.py` entre `maturity_router` et `reports_router` (ordre alpha-cluster : projects → maturity → admin_catalogue → reports)

- [x] **Task 6 — Créer `service.py` (7 fonctions)** (AC: 5)
  - [x] 6.1 6 signatures typées exactes avec `*` kw-only (`create_criterion`, `create_referential`, `create_pack`, `create_derivation_rule`, `record_audit_event`, `transition_workflow_state`)
  - [x] 6.2 Corps `NotImplementedError("Story 10.4 skeleton — implemented in Epic 13 story 13-X / Story 10.12")`
  - [x] 6.3 `async def list_fact_types() -> list[str]: return list(FACT_TYPE_CATALOGUE)` — **IMPLÉMENTATION EFFECTIVE** (seule fonction non-stub)
  - [x] 6.4 Docstring par fonction + référence à l'Epic 13 ou Story 10.12 cible
  - [x] 6.5 Docstring `record_audit_event` explicite NFR64 anti-God + argument `correlation_id` NFR37 traçabilité
  - [x] 6.6 Docstring `transition_workflow_state` documente l'invariant transitions légales (`draft → review_requested → reviewed → published → archived`)
  - [x] 6.7 Vérifier **aucun `select(...)` inline** dans le fichier (grep manuel + review — NFR64)

### Phase 3 — Vérification absence node/tools + documentation graphe (AC6)

- [x] **Task 7 — Vérifier que `graph.py` n'est pas modifié + ajouter commentaire d'absence** (AC: 6)
  - [x] 7.1 **AUCUNE modification** de `backend/app/graph/nodes.py` (la liste des 11 nœuds reste identique)
  - [x] 7.2 **AUCUNE modification** de `backend/app/graph/tools/__init__.py` — `INSTRUMENTED_TOOLS` reste à 36 tools, `__all__` inchangé
  - [x] 7.3 **AUCUNE création** sous `backend/app/graph/tools/admin_catalogue_tools.py` ou équivalent
  - [x] 7.4 `backend/app/graph/tools/README.md` **inchangé** (compteur reste à 36 tools)
  - [x] 7.5 Ajout d'un **commentaire explicite** dans `backend/app/graph/graph.py::build_graph` au-dessus du dernier `create_tool_loop(...)` : bloc 5 lignes documentant l'ABSENCE d'`admin_node` (Clarification 2 architecture.md) — AC6
  - [x] 7.6 Créer le test smoke `backend/tests/test_graph/test_admin_catalogue_absence_from_graph.py` (tests #16 + #17)

### Phase 4 — Tests + validation + scan NFR66 exhaustif (AC7, AC8)

- [x] **Task 8 — Créer `backend/tests/test_admin_catalogue/`** (AC: 8)
  - [x] 8.1 `__init__.py` + `conftest.py` (fixtures `authenticated_client` **réutilisée** depuis `tests/conftest.py` global ou factorisée + nouvelle fixture `admin_authenticated_client` qui pose `ADMIN_MEFALI_EMAILS` via `monkeypatch.setenv` et génère un user avec email `admin@mefali.test`)
  - [x] 8.2 `test_models.py` — 7 tests (CRUD Criterion, unique codes Referential/Pack, FK cascade rule/criterion, CHECK rule_type postgres-only, indexes audit trail, enum NodeState 5 valeurs, enums CatalogueAction + WorkflowLevel)
  - [x] 8.3 `test_router.py` — 4 tests (401 sans auth ×5 endpoints, 403 user PME ×5 endpoints, 501 pour 4 POST admin + 200 pour GET /fact-types admin, OpenAPI 403/501 documentation)
  - [x] 8.4 `test_service.py` — 2 tests (6 stubs `NotImplementedError` parametrize + `list_fact_types` effective)
  - [x] 8.5 `test_fact_type_registry.py` — 1 test (tuple immutable + country-agnostic)
  - [x] 8.6 `test_no_hardcoded_country_strings.py` — 1 test scan `glob("*.py")` **sur les 9 fichiers du module** (leçon MEDIUM-10.3-1)
  - [x] 8.7 `test_dependencies.py` — 2 tests (whitelist env var + fail-closed par défaut)
  - [x] 8.8 `test_graph/test_admin_catalogue_absence_from_graph.py` — 2 tests (node absence + tools absence)

- [x] **Task 9 — Validation baseline + coverage**
  - [x] 9.1 pytest full : baseline pre-10.4 = **1305 passed + 35 skipped** (état post-10.3) ; post-10.4 = **≥ 1319 passed** (strictement +14 minimum) sans flakiness
  - [x] 9.2 Coverage module admin_catalogue ≥ 80 % (NFR60) — pragma `# pragma: no cover` **interdit** sur les stubs
  - [x] 9.3 SQLite OK via `JSONB().with_variant(JSON, "sqlite")`
  - [x] 9.4 PostgreSQL test `test_criterion_derivation_rule_check_rule_type` vert en local avec `docker compose up postgres` (marker `@pytest.mark.postgres`) — pas bloquant CI SQLite-only
  - [x] 9.5 Vérifier que `INSTRUMENTED_TOOLS` count reste à 36 (test smoke AC6 en garantit le non-dérive)

- [x] **Task 10 — Checklist code review self-audit**
  - [x] 10.1 CQ-6 : 9 fichiers module `admin_catalogue/` < 400 lignes (max ~250 lignes pour models.py avec 5 entités)
  - [x] 10.2 CQ-8 : commentaires `# AC1/AC2/.../AC8` dans les fichiers concernés
  - [x] 10.3 CQ-11 : **pas de tool LangChain à wrapper** (module UI-only) — vérification N/A, mais commentaire docstring explicite dans `__init__.py` : « Module UI-only — aucun tool LangChain, aucun `admin_node` »
  - [x] 10.4 CCC-14 : `events.py` documente 5 payloads sans émission MVP
  - [x] 10.5 NFR64 : `service.py` expose 7 fonctions uniques, aucune logique inline ; `record_audit_event` documentée comme point d'entrée unique pour audit trail
  - [x] 10.6 NFR66 country-data-driven : **scan exhaustif `glob("*.py")` sur 9 fichiers du module** (leçon MEDIUM-10.3-1 appliquée dès la story) — validé par test #15
  - [x] 10.7 Clarification 2 architecture.md : **AUCUN admin_node, AUCUN tool** — validé par tests #16 + #17
  - [x] 10.8 AC7 : `FACT_TYPE_CATALOGUE` tuple immutable, 12 entrées, zéro pays

### Review Findings

**Date** : 2026-04-20 — Reviewer : Claude Opus 4.7 (1M ctx) — Décision : **APPROVE-WITH-CHANGES**
Rapport complet : `_bmad-output/implementation-artifacts/10-4-code-review-2026-04-20.md`
Total : 0 CRITICAL, 0 HIGH, 1 MEDIUM, 4 LOW, 17 INFO.

- [x] [Review][Patch] MEDIUM-10.4-1 — Test 17 ne vérifie pas `len(INSTRUMENTED_TOOLS)` exigé par AC8 [`backend/tests/test_graph/test_admin_catalogue_absence_from_graph.py:46-67`] — **FIXED 2026-04-20** : assertion count ajoutée (`== 38`, pas 36 : INSTRUMENTED_TOOLS inclut INTERACTIVE_TOOLS + GUIDED_TOUR_TOOLS en plus des 36 tools « fonctionnels » listés dans le README). Note : l'AC8 #17 original référençait 36 — décalage avec la collection complète. Valeur corrigée empiriquement.
- [x] [Review][Defer] LOW-10.4-1 — Pattern `status_code=201` + raise 501 — pattern 10.2/10.3 conservé, remplacement Epic 13.1/13.2/13.3/13.1bis
- [x] [Review][Defer] LOW-10.4-2 — Endpoints POST typés `-> dict` cosmétique [`backend/app/modules/admin_catalogue/router.py:80,93,106,119`] — harmoniser Epic 13 avec `-> CriterionResponse`/etc.
- [x] [Review][Defer] LOW-10.4-3 — Import `admin_catalogue_router` hors ordre alphabétique dans `main.py` — conservation volontaire Cluster A → A' → admin_catalogue → reports
- [x] [Review][Defer] LOW-10.4-4 — Parse env var `ADMIN_MEFALI_EMAILS` à chaque appel — micro-perf négligeable MVP, résolu naturellement Epic 18 via `User.role`

---

## Dev Notes

### Pattern brownfield à répliquer (NE PAS RÉINVENTER)

**Référence absolue** : `backend/app/modules/maturity/` (Story 10.3 — done). Le pattern 10.3 est **la version la plus consolidée** (leçons 10.2 déjà appliquées). **Dupliquer**, puis retirer :
1. Le `formalization_plan_calculator.py` (pas d'équivalent admin_catalogue MVP).
2. Le `maturity_node` + `maturity_tools.py` (AC6 — pas de node, pas de tool).
3. La dépendance simple `Depends(get_current_user)` → remplacer par `Depends(require_admin_mefali)` (AC4 — nouvelle dépendance rôle-aware).

Fichiers de référence à consulter avant de commencer :
- `backend/app/modules/maturity/__init__.py` — docstring 1 ligne
- `backend/app/modules/maturity/enums.py` — pattern `class XxxEnum(str, Enum)` avec constantes
- `backend/app/modules/maturity/events.py` — pattern `Final[Literal["..."]]` event types
- `backend/app/modules/maturity/router.py:1-78` — pattern 3 endpoints stubs avec `Depends(get_current_user)` en premier, `responses={501: ...}` documenté
- `backend/app/modules/maturity/service.py:1-102` — signatures `async def xxx(db: AsyncSession, *, ...)`, paramètres **kw-only** après le `*`
- `backend/app/modules/maturity/schemas.py` — Pydantic v2 avec `Field(...)`, `ConfigDict(from_attributes=True)`
- `backend/app/modules/maturity/models.py` — helper `_jsonb()` cross-dialect + `UUIDMixin/TimestampMixin`
- `backend/alembic/versions/022_create_esg_3_layers.py:107-304` — schéma SQL des tables `criteria`/`referentials`/`packs`/`criterion_derivation_rules` à mapper en ORM
- `backend/alembic/versions/026_create_admin_catalogue_audit_trail.py` — schéma SQL de `admin_catalogue_audit_trail` à mapper
- `backend/app/api/deps.py:17-56` — pattern `get_current_user` à **consommer** dans `require_admin_mefali`

### Différences admin_catalogue vs maturity — à observer

- **Module UI-only** — pas de `admin_node` LangGraph, pas de tool LangChain (AC6). **C'est la différence structurelle la plus importante de Story 10.4.**
- **5 modèles ORM** (vs 3 pour `maturity/`) — `Criterion`, `Referential`, `Pack`, `CriterionDerivationRule`, `AdminCatalogueAuditTrail`. Les 5 sont mappés sur migrations 022 + 026 pré-existantes.
- **5 endpoints** (vs 3 pour `maturity/`) — 1 GET + 4 POST. L'endpoint `GET /fact-types` est **le seul 200 effectif** ; les 4 POST sont 501 stub.
- **Dépendance `require_admin_mefali`** (AC4) — **création d'une nouvelle dépendance transverse** dans `app.modules.admin_catalogue.dependencies`. Sera réutilisée par Epic 13 + Story 10.12 via import direct.
- **`fact_type_registry.py`** (AC7) — registry country-agnostic, `tuple[str, ...]` immutable, 12 entrées figées. **Remplace** le `formalization_plan_calculator.py` de 10.3 structurellement (fichier extra spécifique au module).
- **Enum `NodeStateEnum` à 5 valeurs** — figée dès le squelette (vs `MaturityWorkflowStateEnum` à 3 valeurs dans 10.3). **Rationale** : l'invariant workflow N1/N2/N3 → draft/review_requested/reviewed/published/archived est la pierre angulaire de l'architecture peer review Story 13.8b/c. Figer l'enum à 5 valeurs dès 10.4 **évite un refactor invariant** quand Epic 13 livrera les transitions. La colonne `workflow_state String(16)` en BDD accepte déjà les 5 valeurs (16 caractères suffisent pour `review_requested` = 16 chars, `published` = 9, etc.).
- **Scan NFR66 exhaustif dès le premier test (leçon MEDIUM-10.3-1)** — `glob("*.py")` sur les 9 fichiers, pas 2 fichiers statiques. Prévenir dès la 3ᵉ duplication du pattern module (10.2 → 10.3 → 10.4).

### Pas de feature flag `ENABLE_ADMIN_CATALOGUE_MODEL` — CONTEXTE CRITIQUE

**Ne PAS introduire** un feature flag (piège tentant par mimétisme de Story 10.2) :
1. L'arbitrage Q1 Story 10.1 n'a introduit QU'UN SEUL feature flag (`ENABLE_PROJECT_MODEL`) par souci de parsimonie env var.
2. Le module admin_catalogue est **strictement UI-only** — il est masqué par construction aux users PME (403 via `require_admin_mefali`). Aucun besoin de flag supplémentaire pour cacher « ce qui n'est pas encore prêt » — les 4 POST renvoient 501 qui est auto-documenté dans OpenAPI.
3. Story 10.9 (feature flag wrapper complet) couvre UNIQUEMENT `ENABLE_PROJECT_MODEL`. Ajouter `ENABLE_ADMIN_CATALOGUE_MODEL` obligerait à rouvrir la scope 10.9 → **non**.

**Conséquence concrète Story 10.4** : les 5 endpoints `/api/admin/catalogue/*` retournent **directement 401 → 403 → 501** sans dependency de feature flag. L'ordre des dependencies est : `admin: User = Depends(require_admin_mefali)` **en premier** → si token absent → 401, si rôle non-admin → 403, sinon corps raise 501.

### `require_admin_mefali` stub — whitelist env var MVP, remplacement Epic 18 garanti

Le modèle `User` actuel n'a **pas** de colonne `role` (vérifié : `backend/app/models/user.py` expose `email`, `hashed_password`, `full_name`, `company_name`, `is_active`). Plutôt que d'ajouter une migration `028_add_user_role_column` **hors scope Epic 10** (qui reste Fondations Phase 0), Story 10.4 utilise un **stub whitelist par email** via `os.environ["ADMIN_MEFALI_EMAILS"]` (comma-separated).

**Avantages du stub** :
- **Zéro migration** → reste dans le scope Epic 10 Fondations.
- **Fail-closed par défaut** → si `ADMIN_MEFALI_EMAILS` absente ou vide → 403 pour tous les users (sécurité par construction, pas par configuration).
- **Testable** → fixtures pytest posent la variable via `monkeypatch.setenv`, isolation complète.
- **Remplaçable en 1 PR** → Epic 18 livrera la migration `028_add_user_role_column.py` + MFA FR61 + remplacement du corps de `require_admin_mefali` par `if current_user.role not in {"admin_mefali","admin_super"}: raise 403`. Le **nom de la dépendance, sa signature et son emplacement restent identiques** → aucun consommateur Epic 13 / Story 10.12 n'aura à refactorer ses endpoints.

**Piège à éviter** : ne pas tenter de parser ADMIN_MEFALI_EMAILS à l'import-time (module-level) — la variable d'env peut changer entre tests via `monkeypatch.setenv`. **Toujours lire** `os.environ.get(...)` **dans le corps de la fonction**, pas en global.

### Clarification 2 architecture.md — Module UI-only, AUCUN admin_node

Citation de l'architecture (à relire) :
> « Le module admin_catalogue est consommé par l'UI admin Mefali via des formulaires HTTP classiques. **Aucun admin_node LangGraph n'est créé** — le LLM n'a pas besoin d'intervenir dans la gestion catalogue (décision structurelle D6 + D10). »

**Conséquences pour la story squelette** :
- **Zéro modification** de `backend/app/graph/nodes.py`, `backend/app/graph/graph.py`, `backend/app/graph/tools/__init__.py`, `backend/app/graph/tools/README.md`.
- **Commentaire explicite** ajouté dans `build_graph` (AC6) pour documenter l'absence — empêche un futur contributeur de tenter de « compléter » le pattern en ajoutant un admin_node.
- **Test smoke** `test_admin_catalogue_absence_from_graph.py` fail CI si quelqu'un ajoute `admin_node` / `admin_catalogue_node` / `catalogue_node` — défense anti-régression explicite.

**Si Epic 13 découvre un besoin LLM exceptionnel** (ex. générer un rule_json à partir d'une description en langage naturel) : **ouvrir une story dédiée dans Epic 13**, **ne pas ajouter à admin_catalogue en catimini**. Le squelette verrouille l'architecture.

### CCC-14 Outbox — `events.py` préparation sans émission (pattern 10.3)

`events.py` déclare 5 constantes pour les `event_type` prévus Epic 13 + Story 10.12 sans les émettre. Le but : consommateurs futurs importent depuis une source unique, évitant le « chaîne de strings hardcodés ».

```python
# backend/app/modules/admin_catalogue/events.py
"""Domain events émis par le module admin_catalogue (D11 micro-Outbox).

Story 10.4 — squelette sans émission. Story 10.10 livrera le worker APScheduler.

Payloads attendus :
- catalogue.criterion_published : {criterion_id, actor_id, workflow_level, ts}
- catalogue.referential_published : {referential_id, actor_id, workflow_level, ts}
- catalogue.pack_published : {pack_id, actor_id, workflow_level, ts}
- catalogue.rule_published : {rule_id, criterion_id, actor_id, ts}
- catalogue.entity_retired : {entity_type, entity_id, actor_id, reason, ts}
"""
from typing import Final, Literal

CATALOGUE_CRITERION_PUBLISHED_EVENT_TYPE: Final[Literal["catalogue.criterion_published"]] = "catalogue.criterion_published"
CATALOGUE_REFERENTIAL_PUBLISHED_EVENT_TYPE: Final[Literal["catalogue.referential_published"]] = "catalogue.referential_published"
CATALOGUE_PACK_PUBLISHED_EVENT_TYPE: Final[Literal["catalogue.pack_published"]] = "catalogue.pack_published"
CATALOGUE_RULE_PUBLISHED_EVENT_TYPE: Final[Literal["catalogue.rule_published"]] = "catalogue.rule_published"
CATALOGUE_ENTITY_RETIRED_EVENT_TYPE: Final[Literal["catalogue.entity_retired"]] = "catalogue.entity_retired"
```

### Country-data-driven (NFR66) — scan exhaustif dès la 1ʳᵉ itération (leçon MEDIUM-10.3-1)

La leçon principale capitalisée du code review 10.3 (MEDIUM-10.3-1) : **le scan NFR66 doit itérer sur tous les `.py` du module (`glob("*.py")`), pas sur une liste statique de 2 fichiers**. En 10.3, le scan initial ne couvrait que `service.py` + `formalization_plan_calculator.py` ; le reviewer a constaté que `schemas.py`/`enums.py`/`router.py` pourraient contenir des pays (ex. `Literal["Sénégal"]` dans un champ Pydantic, docstring OpenAPI, etc.) et le scan les raterait.

**Application Story 10.4** : le test `test_no_hardcoded_country_strings_in_admin_catalogue_module` (AC7 + AC8 #15) itère **dès la première itération** sur les 9 fichiers du module via `glob("*.py")`. Message d'erreur enrichi : `f"{path.name} contient le string pays banni '{banned}' ..."` → debug immédiat.

**Pays à bannir** (liste NFR66 UEMOA + extensions CEDEAO francophones fréquentes) :
```python
_BANNED_COUNTRY_STRINGS = [
    "Sénégal", "Senegal",
    "Côte d'Ivoire", "Cote d'Ivoire", "Ivory Coast",
    "Mali", "Burkina Faso", "Niger", "Togo", "Bénin", "Benin",
    "Guinée", "Guinee", "Guinea",
]
```

**Variables `country` (paramètres, arguments, colonnes)** : acceptées — le scan cherche des string literals, pas des identifiers.

### Cohérence avec RLS (Story 10.5 à venir)

Les 5 tables du module admin_catalogue (`criteria`, `referentials`, `packs`, `criterion_derivation_rules`, `admin_catalogue_audit_trail`) ne sont **PAS dans la liste Story 10.5** (qui cible `companies`, `fund_applications`, `facts`, `documents`). Ces tables sont **globales par design** (catalogue Mefali partagé entre tenants) — l'isolation se fait au niveau applicatif via `require_admin_mefali` (seuls les admins Mefali CRUD). Pas de `tenant_id` ni de policy RLS requis.

**`admin_catalogue_audit_trail` contient `actor_user_id`** qui est un FK vers `users.id` → ce n'est pas un champ tenant mais bien un « qui a fait l'action ». L'escape RLS ne s'applique pas ici.

### SOURCE-TRACKING (NFR27) — colonnes préservées sur Criterion/Referential/Pack, pas sur Rule/AuditTrail

Les colonnes `source_url`, `source_accessed_at`, `source_version` existent sur `criteria`, `referentials`, `packs` (migration 022). Elles sont **nullable** pour l'instant — les contraintes `CHECK (is_published = false OR source_url IS NOT NULL)` ont été ajoutées par migration 025 (`add_source_tracking_constraints.py`) et seront enforced côté UI Story 10.11.

**`CriterionDerivationRule` et `AdminCatalogueAuditTrail` n'ont PAS de colonnes SOURCE-TRACKING** (migrations 022 ligne 154+ et 026 ligne 35+ ne les déclarent pas). C'est normal : une règle de dérivation est *dérivée* d'un critère qui lui-même est sourcé, et un audit trail est une trace immuable, pas un artefact publié.

### Previous Story Intelligence

**Story 10.3** (done 2026-04-20) : pattern `maturity/` établi — **le plus consolidé** (leçons 10.2 incorporées). **Dupliquer**, puis retirer (calculator, node, tools) et ajouter (`dependencies.py`, `fact_type_registry.py`, 5ᵉ modèle audit trail). Leçons appliquées **dès le squelette 10.4** :
- Helper `_jsonb()` local dans `models.py` (pas dans un `core/db.py` commun — choix architectural 10.2 validé).
- Ordre des dependencies : `require_admin_mefali` avant autre dependency → 401 → 403 prime sur 501.
- Stubs `NotImplementedError` avec message explicite « Story 10.4 skeleton — implemented in Epic 13 story 13-X / Story 10.12 ».
- Scan NFR66 **exhaustif `glob("*.py")`** dès la 1ʳᵉ itération (leçon MEDIUM-10.3-1 capitalisée).
- **Documenter l'ABSENCE** d'une pièce architecturale par un commentaire explicite (adaptation négative de « TODO explicite Epic si pattern non-routable » — ici l'absence est *permanente*, pas différée).

**Story 10.2** (done 2026-04-20) : modèle `Company` minimal déjà ajouté — **ne pas re-créer** dans 10.4. Fixture `authenticated_client` factorisée dans `tests/conftest.py` global — **réutiliser**.

**Story 10.1** (done 2026-04-20) : migrations 022 + 025 + 026 créent toutes les tables catalogue consommées AC2. **Ne pas dupliquer le schéma** — les modèles ORM 10.4 se mappent **exactement** sur ce qui existe en base. Si un champ manque (rare), **NE PAS** créer de migration 028 — ouvrir un défer dans `deferred-work.md` et faire arbitrer par le PM (leçon 10.2).

**Story 9.7** (done 2026-04-20) : `with_retry` + `log_tool_call` livrés. **NON CONSOMMÉS** par Story 10.4 car module UI-only sans tool LangChain. Le scan `test_no_tool_escapes_wrapping` **N'A PAS** besoin d'être étendu (pas de nouveau tool à protéger — test #17 garantit que `INSTRUMENTED_TOOLS` ne grandit pas).

### Git Intelligence (5 derniers commits)

```
84eb2f2  10-2-module-projects-squelette: done
06bcf99  9-5/9-6/9-7 ship (observabilité tools)
92f36f5  idem
94ee7e5  Story 9.4 OCR bilingue
39006a8  Stories 9.1/9.2/9.3
```

**Pattern squash-merge** : chaque story est squash-mergée avec message `<story-key>: done`. Pour Story 10.4, prévoir un commit final `10-4-module-admin-catalogue-squelette: done` après validation code review. Note : Story 10.3 (`10-3-module-maturity-squelette`) est à `review` (pas encore `done` dans git log ci-dessus mais présente sur disk — le merge est imminent).

**Commits incrémentaux recommandés** :
1. `10-4: models.py + enums + events + fact_type_registry + register in app/models/__init__.py`
2. `10-4: schemas.py + dependencies.py (require_admin_mefali stub)`
3. `10-4: router.py + main.py integration (5 endpoints 401/403/501)`
4. `10-4: service.py (6 stubs + list_fact_types effective)`
5. `10-4: tests 14+ green + scan NFR66 exhaustif + absence graph smoke`
6. `10-4: graph.py comment documenting admin_node absence (Clarification 2)`
7. (squash au merge)

### Latest Tech Info (Pydantic v2, SQLAlchemy 2.x, FastAPI)

- **Pydantic v2** : `model_config = ConfigDict(from_attributes=True)`. `Field(min_length=..., max_length=..., examples=[...])`. `Literal["draft", "review_requested", ...]` pour forcer les valeurs d'enum côté schemas si préférable à l'import de `NodeStateEnum` (au choix du dev — les deux fonctionnent).
- **SQLAlchemy 2.0** : `Mapped[...]` + `mapped_column(...)`. `UUID(as_uuid=True)` depuis `sqlalchemy.dialects.postgresql`. `JSONB().with_variant(JSON(), "sqlite")` pour cross-dialect. `__table_args__ = (UniqueConstraint(..., name="uq_..."), Index(...))` pour contraintes + index nommés.
- **SQLAlchemy `sa.Enum(...)` avec `create_constraint=True`** : pour `AdminCatalogueAuditTrail.action` et `.workflow_level`, utiliser `sa.Enum("create","update","delete","publish","retire", name="catalogue_action_enum", create_constraint=True)` — miroir exact de la migration 026. En SQLite, `sa.Enum` dégrade en `CHECK IN (...)` → compatible cross-dialect.
- **FastAPI** : `Depends(...)` résolu dans l'ordre déclaré. Pour 401 → 403 → 501 : placer `admin: User = Depends(require_admin_mefali)` **en premier argument positionnel**. `require_admin_mefali` elle-même dépend de `get_current_user` (qui lève 401 si pas de token) → la chaîne est `401 (get_current_user) → 403 (require_admin_mefali) → 501 (corps)`.
- **`os.environ` dans `require_admin_mefali`** : **toujours lire dans le corps de la fonction**, pas en module-level — les fixtures pytest `monkeypatch.setenv` modifient l'environnement runtime, pas un module-level cache.

### Project Structure Notes

**Alignment avec unified project structure (CLAUDE.md + architecture.md §ligne 930, 1146)** :
- ✅ `backend/app/modules/admin_catalogue/` respecte pattern NFR62 `modules/<domain>/{router,service,schemas,models}.py`
- ✅ `enums.py` + `events.py` + `fact_type_registry.py` + `dependencies.py` extensions cohérentes avec architecture.md §«Organisation des 3 nouveaux modules» + §«Modules » ligne 1146
- ✅ Tests dans `backend/tests/test_admin_catalogue/` (convention nommage)
- ✅ Pas de nouveau feature flag (Clarification documentée Dev Notes)
- ✅ **Clarification 2 architecture.md respectée** : aucun admin_node, aucun tool, commentaire explicite dans `build_graph`.

**Variances détectées** (documentées, acceptées) :
- **Pas de node LangGraph ni tool LangChain** — divergence intentionnelle structurelle avec les 11 modules pré-10.4. Clarification 2 architecture.md.
- **Dépendance `require_admin_mefali` stub par whitelist email** — divergence avec le modèle `User.role` attendu Epic 18. Intentionnel (arbitrage scope Epic 10 Phase 0 Fondations — pas de migration `028_add_user_role_column` hors scope).
- **Enum `NodeStateEnum` 5 valeurs figées** — divergence avec `MaturityWorkflowStateEnum` 3 valeurs 10.3. Rationale : l'invariant Décision 6 N1/N2/N3 complet (5 états) est la pierre angulaire Story 13.8b/c ; figer dès le squelette évite un refactor invariant.
- **Pas de `formalization_plan_calculator.py` équivalent** — divergence avec 10.3. `fact_type_registry.py` joue le rôle de « fichier extra spécifique au module » mais sans classe métier (simple constante Tuple).

---

## References

- [Source: _bmad-output/planning-artifacts/epics/epic-10.md#story-104] — AC1–AC7 originaux
- [Source: _bmad-output/planning-artifacts/epics/epic-13.md] — Cluster B Epic 13 consommateur (FR17–FR26)
- [Source: _bmad-output/planning-artifacts/architecture.md#clarification-2] — Module admin_catalogue UI-only, aucun admin_node LangGraph
- [Source: _bmad-output/planning-artifacts/architecture.md#decision-6] — State machine N1/N2/N3 + 5 valeurs workflow
- [Source: _bmad-output/planning-artifacts/architecture.md#ligne-930] — `backend/app/modules/admin_catalogue/` structure
- [Source: _bmad-output/planning-artifacts/architecture.md#ligne-1146] — Modules structure `admin_catalogue/` (router + service + schemas + models + dependencies)
- [Source: _bmad-output/implementation-artifacts/10-1-migrations-alembic-020-027.md] — Story 10.1 (done, migrations 022 + 025 + 026)
- [Source: _bmad-output/implementation-artifacts/10-2-module-projects-squelette.md] — Story 10.2 (done, pattern initial)
- [Source: _bmad-output/implementation-artifacts/10-3-module-maturity-squelette.md] — Story 10.3 (done, pattern consolidé + leçons capitalisées)
- [Source: _bmad-output/implementation-artifacts/10-2-code-review-2026-04-20.md] — Leçons Code Review 10.2 (MEDIUM-10.2-1, MEDIUM-10.2-2)
- [Source: _bmad-output/implementation-artifacts/10-3-code-review-2026-04-20.md] — Leçon MEDIUM-10.3-1 (scan NFR66 exhaustif), LOW-10.3-3 (doc OCR FR12 vs FR13)
- [Source: backend/alembic/versions/022_create_esg_3_layers.py] — Schéma SQL de `criteria`, `referentials`, `packs`, `criterion_derivation_rules` à mapper en ORM
- [Source: backend/alembic/versions/025_add_source_tracking_constraints.py] — CHECK constraints `is_published → source_url NOT NULL`
- [Source: backend/alembic/versions/026_create_admin_catalogue_audit_trail.py] — Schéma SQL de `admin_catalogue_audit_trail` + enums PG
- [Source: backend/app/api/deps.py:17-56] — `get_current_user` consommé par `require_admin_mefali`
- [Source: backend/app/models/user.py] — Modèle `User` sans `role` column (justifie stub whitelist Story 10.4)
- [Source: backend/app/modules/maturity/] — Pattern brownfield de référence (squelette 10.3 consolidé)
- [Source: backend/app/modules/maturity/router.py:1-78] — Pattern router à dupliquer + retirer `get_current_user` + ajouter `require_admin_mefali`
- [Source: backend/app/modules/maturity/service.py:1-102] — Pattern service stubs kw-only (à dupliquer pour 6 stubs + 1 effective)
- [Source: backend/app/modules/maturity/models.py] — Helper `_jsonb()` cross-dialect (à dupliquer localement)
- [Source: backend/app/main.py:108-132] — Pattern `include_router` — ajouter `admin_catalogue_router` entre `maturity_router` et `reports_router`
- [Source: backend/app/graph/graph.py::build_graph] — Ajouter commentaire explicite ABSENCE admin_node (AC6)
- [Source: backend/app/graph/tools/__init__.py] — `INSTRUMENTED_TOOLS` count doit rester à 36 (AC6 + test #17)
- [Source: backend/tests/test_graph/test_tools_instrumentation.py:144-154] — `test_no_tool_escapes_wrapping` — **pas étendu** Story 10.4
- [Source: CLAUDE.md#conventions-de-developpement] — NFR62 structure modules, snake_case Python
- [Source: backend/app/models/__init__.py] — Registration globale modèles SQLAlchemy (5 nouveaux imports `# noqa: F401`)
- [Source: backend/tests/conftest.py] — Fixtures `authenticated_client` globale (à réutiliser + ajouter `admin_authenticated_client`)

---

## Dev Agent Record

### Agent Model Used

claude-opus-4-7[1m] (Opus 4.7, 1M context)

### Debug Log References

- pytest module : 26 tests verts sur `tests/test_admin_catalogue/` + `tests/test_graph/test_admin_catalogue_absence_from_graph.py` (1.85s).
- pytest full suite : **1330 passed + 35 skipped** (baseline post-10.4 ; pré-10.4 = 1305 → +25 tests, largement au-dessus du plancher +14).
- Coverage `app.modules.admin_catalogue` = **100 %** (9 fichiers, 239 stmts couverts) — seuil NFR60 80 % largement dépassé.

### Completion Notes List

- Ultimate context engine analysis completed — comprehensive developer guide created pour Story 10.4 (squelette `admin_catalogue/` UI-only + 5 modèles ORM migrations 022+026 + dépendance `require_admin_mefali` stub + `fact_type_registry.py` + AUCUN admin_node/tool).
- Implémentation terminée 2026-04-20. 8/8 AC satisfaits, 10/10 tasks cochées, 26 tests verts (plancher AC8 = 14 + 12 tests bonus dont 6 paramétrés service, 2 absence graphe, 2 dépendances fail-closed, 1 events).
- Pattern `modules/maturity/` dupliqué avec divergences explicites : **pas de `formalization_plan_calculator.py`** (remplacé par `fact_type_registry.py` tuple immutable), **pas d'`admin_node`** ni de tool LangChain (Clarification 2 architecture.md), **dépendance `require_admin_mefali`** nouvelle (whitelist email `ADMIN_MEFALI_EMAILS`, fail-closed par défaut).
- 5 modèles ORM mappés strictement sur migrations 022 + 026. `CriterionDerivationRule` et `AdminCatalogueAuditTrail` **sans** `TimestampMixin` (migrations ne déclarent qu'une seule colonne temporelle).
- `NodeStateEnum` figée à 5 valeurs dès la story squelette (invariant 13.8b/c). `CatalogueActionEnum` et `WorkflowLevelEnum` miroirs des enums PostgreSQL migration 026.
- 5 endpoints router : `GET /fact-types` (seul effectif 200) + 4 POST stub 501. Ordre dépendances 401 → 403 → 501 respecté.
- Service 7 fonctions : 6 stubs `NotImplementedError` + `list_fact_types` effective. **Zéro `select(...)` inline** (NFR64 anti-God).
- Scan NFR66 **exhaustif via `glob("*.py")`** dès la première itération (leçon MEDIUM-10.3-1) — 9 fichiers scannés, zéro string pays banni.
- Commentaire explicite ABSENCE d'`admin_node` dans `build_graph` + test smoke garantissent la non-régression architecturale.
- `INSTRUMENTED_TOOLS` inchangé. `backend/app/graph/nodes.py` intouché.
- Durée réelle : ~45 min (6ème story avec pattern — cible ~1h atteinte).

### File List

**Créés** :
- `backend/app/modules/admin_catalogue/__init__.py`
- `backend/app/modules/admin_catalogue/enums.py`
- `backend/app/modules/admin_catalogue/events.py`
- `backend/app/modules/admin_catalogue/fact_type_registry.py`
- `backend/app/modules/admin_catalogue/dependencies.py`
- `backend/app/modules/admin_catalogue/models.py`
- `backend/app/modules/admin_catalogue/schemas.py`
- `backend/app/modules/admin_catalogue/service.py`
- `backend/app/modules/admin_catalogue/router.py`
- `backend/tests/test_admin_catalogue/__init__.py`
- `backend/tests/test_admin_catalogue/conftest.py`
- `backend/tests/test_admin_catalogue/test_models.py`
- `backend/tests/test_admin_catalogue/test_router.py`
- `backend/tests/test_admin_catalogue/test_service.py`
- `backend/tests/test_admin_catalogue/test_dependencies.py`
- `backend/tests/test_admin_catalogue/test_fact_type_registry.py`
- `backend/tests/test_admin_catalogue/test_no_hardcoded_country_strings.py`
- `backend/tests/test_admin_catalogue/test_events.py`
- `backend/tests/test_graph/test_admin_catalogue_absence_from_graph.py`

**Modifiés** :
- `backend/app/models/__init__.py` (enregistrement des 5 modèles admin_catalogue)
- `backend/app/main.py` (include_router `admin_catalogue_router` entre `maturity_router` et `reports_router`)
- `backend/app/graph/graph.py` (ajout commentaire ABSENCE admin_node dans `build_graph` — AC6)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (`10-4-module-admin-catalogue-squelette: review`)

**À NE PAS modifier** (défense explicite) :
- `backend/app/graph/nodes.py` — aucun admin_node ajouté
- `backend/app/graph/tools/__init__.py` — `INSTRUMENTED_TOOLS` reste à 36 tools
- `backend/app/graph/tools/README.md` — compteur inchangé
- `backend/tests/test_graph/test_tools_instrumentation.py` — pas de tool à ajouter au scan

### Change Log

| Date | Type | Description |
|------|------|-------------|
| 2026-04-20 | spec | Story 10.4 — fiche comprehensive rédigée (AC1-AC8 + 10 tasks + dev notes pattern brownfield 10.3 + dépendance `require_admin_mefali` stub whitelist email + scan NFR66 exhaustif glob("*.py") dès la 1ʳᵉ itération + commentaire explicite ABSENCE admin_node — Clarification 2 architecture.md). 3ᵉ duplication pattern module (10.2 → 10.3 → 10.4) avec retraits structurels (pas de node/tool) et ajouts ciblés (dépendance admin, registry country-agnostic, 5ᵉ modèle audit trail). |
| 2026-04-20 | impl | Story 10.4 implémentée. 9 fichiers module + 10 fichiers tests créés, 3 fichiers modifiés. 26 tests verts (baseline 1305 → 1330, +25). Coverage module 100 %. 8/8 AC satisfaits, 10/10 tasks cochées. Aucun admin_node dans le graphe (test smoke + commentaire docstring build_graph). Status: review. |
