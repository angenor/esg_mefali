# Story 10.2 : Module `projects/` squelette (router + service + schemas + models + node LangGraph)

Status: done

> **Contexte** : 2ᵉ story Epic 10 Fondations Phase 0 (BLOQUANT Cluster A Epic 11 FR1–FR10). Socle technique minimal du module `projects` — router REST stub, service bus, schemas Pydantic, models SQLAlchemy ORM, nœud LangGraph `project_node` + `projects_tools.py`. **Aucune logique métier MVP** : les endpoints renvoient 404/501 selon le feature flag `ENABLE_PROJECT_MODEL`. Epic 11 y déposera la vraie implémentation.
>
> **Dépendances** :
> - Story 10.1 **done** (migration `020_create_projects_schema.py` : tables `companies`, `projects`, `project_memberships`, `project_role_permissions`, `project_snapshots`, `company_projections`, `beneficiary_profiles` créées ; `fund_applications.project_id` FK ajoutée).
> - Story 9.7 **done** (`with_retry` + `log_tool_call` dans `backend/app/graph/tools/common.py` — **OBLIGATOIRE** dès la création des tools, pas de dette à rattraper).
> - Story 10.9 (feature flag) : **pas livré** — cette story définit `is_project_model_enabled()` en stub simple pour que le routing 404/501 fonctionne immédiatement, Story 10.9 formalisera le wrapper complet + tests dédiés sans casser l'API définie ici.
>
> **Bloque** :
> - Story 10.3 (`maturity/` squelette) — duplique le pattern.
> - Story 10.4 (`admin_catalogue/` squelette) — duplique le pattern (UI-only, sans node).
> - Epic 11 entier (FR1–FR10 Cluster A Company × Project) — consomme ce squelette.

---

## Story

**As a** PME User (owner) — represented here by l'Équipe Mefali backend,
**I want** disposer du socle technique minimal du module `projects` (router REST stub, service bus, schemas Pydantic, models ORM, `project_node` LangGraph + `projects_tools.py` avec au moins 1 tool `create_project` **déjà instrumenté** `with_retry` + `log_tool_call`),
**So that** les 10 stories Epic 11 (FR1–FR10) puissent y déposer la logique métier sans recréer la plomberie, et que les autres modules squelettes (`maturity`, `admin_catalogue`) aient un pattern de référence identique à dupliquer.

---

## Acceptance Criteria

### AC1 — Structure du module `backend/app/modules/projects/` conforme au pattern `modules/esg/`

**Given** le repository dans l'état `main @ HEAD` avec Story 10.1 mergée (migration 020 appliquée),
**When** un développeur exécute `ls backend/app/modules/projects/`,
**Then** le dossier contient **exactement** les fichiers suivants (pattern brownfield `modules/esg/` — NFR62 CLAUDE.md) :
  - `__init__.py` (docstring 1 ligne : « Module Projects : Cluster A Company × Project N:N (D1). »)
  - `router.py` (APIRouter préfixe `/api/projects`, tags `["projects"]`)
  - `service.py` (fonctions métier — stubs `NotImplementedError("livré en Epic 11")`)
  - `schemas.py` (Pydantic v2 : `ProjectCreate`, `ProjectResponse`, `ProjectSummary`, `ProjectList`, `ProjectMembershipCreate`, `ProjectMembershipResponse`, `ProjectStatusEnum`, `ProjectRoleEnum`)
  - `models.py` (SQLAlchemy 2.0 ORM : `Project`, `ProjectMembership`, `ProjectRolePermission`, `ProjectSnapshot`, `CompanyProjection`, `BeneficiaryProfile` — mappées sur les tables créées par migration 020)
  - `enums.py` (`ProjectStatusEnum`, `ProjectRoleEnum` — **source unique** réutilisée par `schemas.py` et `models.py`)
  - `events.py` (squelette avec 1 constante `PROJECT_CREATED_EVENT_TYPE: Literal["project.created"]` + docstring documentant les payloads `domain_events` émis Epic 11 — **pas d'émission réelle MVP**, préparation D11 CCC-14)
**And** tous les fichiers ont une docstring d'en-tête `"""<description courte>.\n\nStory 10.2 — module `projects/` squelette.\nFR covered: [] (infra FR1–FR10), NFR covered: [NFR49, NFR62, NFR64].\n"""`
**And** `from app.modules.projects import router, service, schemas, models, enums, events` **importe sans erreur**.

### AC2 — `models.py` expose les 6 modèles ORM SQLAlchemy 2.0 mappés sur migration 020

**Given** la migration 020 appliquée (tables `projects`, `project_memberships`, `project_role_permissions`, `project_snapshots`, `company_projections`, `beneficiary_profiles`),
**When** un développeur importe les modèles et exécute un cycle CRUD SQLite in-memory,
**Then** chaque modèle respecte strictement le schéma de la migration :
  - `Project(id UUID PK, company_id UUID FK companies.id ON DELETE CASCADE, name STR(255) NOT NULL, status ProjectStatusEnum NOT NULL DEFAULT idea, version_number INT NOT NULL DEFAULT 1, description TEXT NULLABLE, metadata_json JSONB/JSON NULLABLE, created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ)`
  - `ProjectMembership(id UUID PK, project_id UUID FK projects.id ON DELETE CASCADE, company_id UUID FK companies.id ON DELETE CASCADE, role ProjectRoleEnum NOT NULL, created_at TIMESTAMPTZ, UNIQUE(project_id, company_id, role))`
  - `ProjectRolePermission(id UUID PK, role STR(32), permission STR(64), UNIQUE(role, permission))`
  - `ProjectSnapshot(id UUID PK, project_id UUID FK, snapshot_hash STR(64), payload JSONB, created_at TIMESTAMPTZ)`
  - `CompanyProjection(id UUID PK, company_id UUID FK, projection_type STR(64), payload JSONB, refreshed_at TIMESTAMPTZ, UNIQUE(company_id, projection_type))`
  - `BeneficiaryProfile(id UUID PK, company_id UUID FK, project_id UUID FK NULLABLE, survey_data JSONB NULLABLE, created_at, updated_at)`
**And** les types utilisent `UUIDMixin` + `TimestampMixin` de `app.models.base` quand applicable (cohérence avec `ESGAssessment`).
**And** `enums.py::ProjectStatusEnum` a **exactement** les 5 valeurs `{idea, planning, in_progress, operational, archived}` (cohérent avec migration 020 `project_status_enum`).
**And** `enums.py::ProjectRoleEnum` a **exactement** les 4 valeurs `{porteur_principal, beneficiaire, partenaire, observateur}` (cohérent avec `project_role_enum`).
**And** les 6 modèles sont **enregistrés dans `app/models/__init__.py`** via import explicite `from app.modules.projects.models import Project, ProjectMembership, ...  # noqa: F401` pour que SQLAlchemy metadata les connaisse (sinon `Base.metadata.create_all` les ignore, cassant tests SQLite).

### AC3 — `router.py` expose 4 endpoints stubs avec comportement 401/404/501 selon feature flag

**Given** `backend/app/modules/projects/router.py` branché dans `backend/app/main.py` via `app.include_router(projects_router, prefix="/api/projects", tags=["projects"])`,
**When** un client appelle les endpoints sans JWT valide (header `Authorization` absent ou invalide),
**Then** **tous** les endpoints renvoient **401 Unauthorized** (dépendance `Depends(get_current_user)` garantit ce comportement, cohérent avec `modules/esg/router.py`).
**And** les 4 endpoints stubs exposés sont :
  - `POST /api/projects` → création d'un project (body `ProjectCreate`)
  - `GET /api/projects/{project_id}` → détail d'un project
  - `GET /api/projects` → liste paginée des projects de l'owner (query params `page`, `limit`)
  - `POST /api/projects/{project_id}/memberships` → ajouter une `ProjectMembership` (body `ProjectMembershipCreate`)
**And** **quand `ENABLE_PROJECT_MODEL=false`** (défaut MVP, arbitrage Q1 Story 10.1), **les 4 endpoints renvoient 404** (feature masquée par routing — Story 10.9 AC2) avec payload `{"detail": "Feature not available: ENABLE_PROJECT_MODEL is disabled"}` (message en anglais cohérent avec convention FastAPI pour status codes standards, message utilisateur traduit côté frontend si nécessaire).
**And** **quand `ENABLE_PROJECT_MODEL=true`** mais Epic 11 pas encore livré (état actuel post-10.2), **les 4 endpoints renvoient 501 Not Implemented** avec payload `{"detail": "Projects module skeleton — implementation delivered in Epic 11"}`.
**And** la distinction sémantique 404 vs 501 est **documentée dans OpenAPI** via `responses={404: {"description": "Feature flag ENABLE_PROJECT_MODEL disabled"}, 501: {"description": "Projects module skeleton — Epic 11 not yet delivered"}}` sur chaque endpoint (CQ-8 documentation structurée).

### AC4 — `feature_flags.py` expose `is_project_model_enabled()` avec lecture env `ENABLE_PROJECT_MODEL`

**Given** aucun `backend/app/core/feature_flags.py` n'existe avant cette story,
**When** un développeur l'importe,
**Then** le fichier expose **exactement** une fonction `is_project_model_enabled() -> bool` qui :
  - Lit la variable d'env `ENABLE_PROJECT_MODEL` (via `os.environ.get("ENABLE_PROJECT_MODEL", "false")`)
  - Renvoie `True` **uniquement** pour les valeurs `"true"`, `"1"`, `"yes"` (case-insensitive via `.lower()`)
  - Renvoie `False` pour toute autre valeur ou absence (défaut MVP)
**And** la fonction est appelée **dynamiquement à chaque requête** (pas de cache module-level qui empêcherait le toggle live en DEV — AC6 Story 10.9).
**And** le router `projects/router.py` utilise un helper partagé (dependency FastAPI `Depends(check_project_model_enabled)`) qui lève **`HTTPException(status_code=404, detail="Feature not available: ENABLE_PROJECT_MODEL is disabled")`** avant toute logique métier.
**And** aucune librairie externe (`flipper-client`, `unleash-client`, `launchdarkly-server-sdk`) n'est ajoutée à `backend/requirements.txt` (Clarification 5 respectée — Story 10.9 formalisera AC4).

### AC5 — `projects_tools.py` expose ≥ 1 tool stub `create_project` wrappé `with_retry` + auto-journalisé (CQ-11)

**Given** `backend/app/graph/tools/projects_tools.py` créé,
**When** inspecté,
**Then** il expose au minimum le tool `@tool async def create_project(name: str, state: str, config: RunnableConfig) -> str` avec les caractéristiques suivantes :
  - Signature conforme au pattern `esg_tools.create_esg_assessment` (RunnableConfig dernier argument positionnel).
  - Docstring en français décrivant l'objectif, les args et la valeur de retour (exploitée par LangChain pour le prompt LLM).
  - Argument `state` valeur par défaut acceptée `'idée'` (coercée vers `ProjectStatusEnum.idea` côté application — **pas** stocké tel quel en base, anti-ambiguïté).
  - Implémentation : **retourne `"Module projects non encore implémenté (Epic 11)."`** (stub explicite, pas de `raise NotImplementedError` qui ferait crash côté LLM).
  - Journalisation **automatique** via le wrapper `with_retry` (aucun appel `log_tool_call` manuel dans le corps du tool, CQ-11 enforcement).
**And** `PROJECTS_TOOLS = [with_retry(create_project, max_retries=2, node_name="project")]` est défini en fin de fichier **(attribut sentinelle `_is_wrapped_by_with_retry=True` vérifiable via `assert PROJECTS_TOOLS[0]._is_wrapped_by_with_retry is True`)**.
**And** `PROJECTS_TOOLS` est **exporté** dans `backend/app/graph/tools/__init__.py` :
  - Import `from app.graph.tools.projects_tools import PROJECTS_TOOLS`
  - Ajouté à la liste `INSTRUMENTED_TOOLS` entre `PROFILING_TOOLS` et `ESG_TOOLS` (ordre alphabétique logique par nouveauté — documenté commentaire)
  - Exporté dans `__all__`
**And** `backend/app/graph/tools/README.md` est mis à jour : ligne ajoutée au tableau de la Section 1 `| projects_tools.py | project | create_project |` **ET** compteur tools passé de « 34 tools » à « 35 tools ».

### AC6 — `project_node` enregistré dans `graph.py` (10ᵉ nœud spécialiste, sans routing métier MVP)

**Given** `backend/app/graph/nodes.py` contient actuellement 9 nœuds (`router_node`, `document_node`, `chat_node`, `esg_scoring_node`, `carbon_node`, `financing_node`, `application_node`, `credit_node`, `action_plan_node`),
**When** une fonction `async def project_node(state: ConversationState) -> ConversationState` est ajoutée,
**Then** elle a le comportement **minimal** suivant (pas de logique métier — **ne construit pas de prompt, ne call pas le LLM** car Epic 11 livrera le prompt dédié et le routing LLM complet) :
  - **Pas de bind_tools ni d'invocation LLM** (diffère des 9 autres nodes).
  - Retourne simplement `{"messages": [AIMessage(content="Module projects — squelette activé (Epic 11 livre la logique métier).")]}` pour clôturer la boucle proprement.
  - Pose `active_module="project"` et `active_module_data={"node_visited": True}` dans le state retourné (pattern spec 013 multi-tour) pour que le router ne rebounce pas dessus au tour suivant tant qu'Epic 11 n'est pas livré.
  - **Aucun appel aux tools `PROJECTS_TOOLS`** dans ce corps (les tools sont accessibles via le `ToolNode` configuré dans `graph.py` mais le LLM ne les appellera pas tant qu'il n'y a pas de prompt métier).
**And** dans `backend/app/graph/graph.py` :
  - L'import ajoute `project_node` : `from app.graph.nodes import action_plan_node, application_node, carbon_node, chat_node, credit_node, document_node, esg_scoring_node, financing_node, project_node, router_node`
  - L'import ajoute `from app.graph.tools.projects_tools import PROJECTS_TOOLS`
  - Appel : `create_tool_loop(graph, "project", project_node, tools=PROJECTS_TOOLS + INTERACTIVE_TOOLS + GUIDED_TOUR_TOOLS)` (injection `INTERACTIVE_TOOLS` + `GUIDED_TOUR_TOOLS` cohérente avec les 6 autres nœuds spécialistes features 018 + 019)
  - La docstring `build_graph` est mise à jour pour lister le nouveau flux `→ [project] → project_node ⟲ project_tools → END` (pour documentation visuelle).
  - **⚠️ AUCUNE entrée dans `_route_after_router`** ni dans le `conditional_edges` dict de `router` — le node existe dans le graphe mais **n'est pas atteignable depuis le router tant qu'Epic 11 ne définit pas son heuristique de routage** (évite d'attirer du trafic LLM sans prompt). Le node est joignable uniquement via un test qui invoque `compiled_graph.invoke({...}, config={"configurable": {"active_module": "project"}})` — ce qui est le comportement attendu pour un squelette.

### AC7 — `service.py` expose la surface d'API consommée par Epic 14 + Epic 11 sans accéder directement à la table

**Given** un futur `matching_service` (Epic 14) ou n'importe quel module externe,
**When** il importe `from app.modules.projects.service import create_project, get_project, list_projects_by_owner, add_membership, get_memberships_for_project`,
**Then** les 5 fonctions sont **présentes** dans `service.py` avec signatures typées :
  - `async def create_project(db: AsyncSession, *, company_id: UUID, name: str, status: ProjectStatusEnum = ProjectStatusEnum.idea, description: str | None = None) -> Project`
  - `async def get_project(db: AsyncSession, *, project_id: UUID, owner_user_id: UUID) -> Project | None` (filtre par `Project.company_id IN (SELECT id FROM companies WHERE owner_user_id = ?)` pour cohérence avec RLS à venir 10.5)
  - `async def list_projects_by_owner(db: AsyncSession, *, owner_user_id: UUID, page: int = 1, limit: int = 10) -> tuple[list[Project], int]`
  - `async def add_membership(db: AsyncSession, *, project_id: UUID, company_id: UUID, role: ProjectRoleEnum) -> ProjectMembership`
  - `async def get_memberships_for_project(db: AsyncSession, *, project_id: UUID) -> list[ProjectMembership]`
**And** chaque fonction lève **`NotImplementedError("Story 10.2 skeleton — implemented in Epic 11 story 11-X")`** (message explicite — les tests unitaires vérifient l'exception, PAS la logique).
**And** **anti-pattern God service (NFR64)** : `service.py` **n'importe jamais `from sqlalchemy import select` dans son corps** sauf pour les 5 fonctions ci-dessus (les imports sont OK, l'interdit porte sur l'usage) ; aucune autre fonction ne lit/écrit directement les tables `projects`/`project_memberships`/etc. Les consommateurs externes (matching_service, router) **doivent passer par ces 5 fonctions**, jamais par un `select(Project)` inline.

### AC8 — Tests minimum livrés dans `backend/tests/test_projects/` (plan plancher 13 tests verts)

**Given** `backend/tests/test_projects/__init__.py` créé,
**When** `pytest backend/tests/test_projects/ -v` exécuté,
**Then** les **13 tests minimum** suivants passent tous (plancher +13 ≥ baseline +12 exigée) :

| # | Fichier test | Test | Vérifie |
|---|--------------|------|---------|
| 1 | `test_models.py` | `test_project_model_crud_sqlite` | INSERT → SELECT → UPDATE `status` → DELETE sur `Project` via AsyncSession SQLite |
| 2 | `test_models.py` | `test_project_membership_unique_triplet` | 2ᵉ INSERT même `(project_id, company_id, role)` lève `IntegrityError` (D1 cumul respecté) |
| 3 | `test_models.py` | `test_project_status_enum_values` | `ProjectStatusEnum` a exactement 5 valeurs `{idea, planning, in_progress, operational, archived}` |
| 4 | `test_models.py` | `test_project_role_enum_values` | `ProjectRoleEnum` a exactement 4 valeurs `{porteur_principal, beneficiaire, partenaire, observateur}` |
| 5 | `test_models.py` | `test_fk_cascade_project_delete_membership` | Suppression d'un `Project` cascade les `ProjectMembership` liés (`ON DELETE CASCADE`) |
| 6 | `test_router.py` | `test_endpoints_return_404_when_flag_disabled` | `monkeypatch.setenv("ENABLE_PROJECT_MODEL", "false")` → 4 endpoints → 404 (auth mockée via fixture `test_client_authenticated`) |
| 7 | `test_router.py` | `test_endpoints_return_501_when_flag_enabled` | `monkeypatch.setenv("ENABLE_PROJECT_MODEL", "true")` → 4 endpoints → 501 + message contient `"Epic 11"` |
| 8 | `test_router.py` | `test_endpoints_return_401_without_auth` | Sans header `Authorization` → 4 endpoints → 401 (prime sur 404/501 — FastAPI résout `Depends(get_current_user)` avant les custom deps) |
| 9 | `test_router.py` | `test_openapi_documents_404_and_501_responses` | `/openapi.json` contient `responses.404` ET `responses.501` pour chaque endpoint `/api/projects/*` |
| 10 | `test_feature_flags.py` | `test_is_project_model_enabled_defaults_false` | Sans env var → `False` |
| 11 | `test_feature_flags.py` | `test_is_project_model_enabled_truthy_values` | `"true"`, `"TRUE"`, `"1"`, `"yes"`, `"YES"` → `True` ; `"false"`, `"0"`, `""`, `"no"`, `"disabled"` → `False` (table-driven via `pytest.mark.parametrize`) |
| 12 | `test_projects_tools.py` | `test_create_project_tool_is_wrapped_with_retry` | `PROJECTS_TOOLS[0]._is_wrapped_by_with_retry is True` (enforcement CQ-11) |
| 13 | `test_projects_tools.py` | `test_create_project_tool_returns_skeleton_message` | Invocation avec mock `RunnableConfig` → retour contient `"non encore implémenté"` ET `"Epic 11"` |
| bonus | `test_graph/test_project_node_registered.py` | `test_project_node_registered_in_graph` | `compiled_graph.nodes` contient `"project"` ET `"project_tools"` (smoke test AC6) |

**And** la baseline passe de **1283** tests verts (post-10.1) à **≥ 1295** tests verts (strictement +12 minimum, +13 en pratique) sans flakiness sur 3 runs consécutifs.
**And** coverage `backend/app/modules/projects/` **≥ 80 %** (NFR60 CI gate — service stubs comptent car `NotImplementedError` est l'unique ligne du corps, exécutée par les tests d'assertion d'exception).

---

## Tasks / Subtasks

### Phase 1 — Squelette module + modèles ORM (AC1, AC2)

- [x] **Task 1 — Créer `backend/app/modules/projects/` + 7 fichiers squelettes** (AC: 1)
  - [x] 1.1 `__init__.py` (docstring 1 ligne)
  - [x] 1.2 `enums.py` : `ProjectStatusEnum(str, Enum)` 5 valeurs + `ProjectRoleEnum(str, Enum)` 4 valeurs — **source unique** réutilisée par `models.py`, `schemas.py`, `router.py`, `service.py`
  - [x] 1.3 `events.py` : constante `PROJECT_CREATED_EVENT_TYPE: Literal["project.created"] = "project.created"` + docstring payload schema prévu Epic 11
  - [x] 1.4 Vérifier import circulaire : `from app.modules.projects import router, service, schemas, models, enums, events` passe sans warning (vérifié via python -c)

- [x] **Task 2 — Écrire `models.py` (6 modèles ORM mappés sur migration 020 + 1 stub Company)** (AC: 2)
  - [x] 2.1 `Project` avec `version_number INT DEFAULT 1` + `metadata_json` via `JSONB().with_variant(JSON, "sqlite")`
  - [x] 2.2 `ProjectMembership` avec `UniqueConstraint` triplet
  - [x] 2.3 `ProjectRolePermission`, `ProjectSnapshot`, `CompanyProjection`, `BeneficiaryProfile`
  - [x] 2.4 `UUIDMixin` + `TimestampMixin` utilisés là où `created_at`/`updated_at` existent (Project, BeneficiaryProfile, Company)
  - [x] 2.5 Enregistrement dans `app/models/__init__.py`
  - [x] 2.6 `Base.metadata.create_all` SQLite crée les tables — test CRUD passe
  - **Note** : un modèle `Company` minimal (7e) est ajouté pour satisfaire les ForeignKey `company_id → companies.id` en SQLite. Epic 11 Story 11-1 enrichira ce modèle.

### Phase 2 — Feature flag + router stubs (AC3, AC4)

- [x] **Task 3 — Créer `backend/app/core/feature_flags.py`** (AC: 4)
  - [x] 3.1 `is_project_model_enabled()` lit env à chaque appel (pas de cache)
  - [x] 3.2 Truthy values : `"true"`, `"1"`, `"yes"` (case-insensitive via `.strip().lower()`)
  - [x] 3.3 Docstring référence Story 10.9
  - [x] 3.4 Note Story 20.1 cleanup

- [x] **Task 4 — Créer `schemas.py` (Pydantic v2)** (AC: 1, 3)
  - [x] 4.1 `ProjectStatusEnum` + `ProjectRoleEnum` réimportés depuis `enums.py`
  - [x] 4.2 `ProjectCreate`
  - [x] 4.3 `ProjectResponse` avec `ConfigDict(from_attributes=True)`
  - [x] 4.4 `ProjectSummary`, `ProjectList`
  - [x] 4.5 `ProjectMembershipCreate` + `ProjectMembershipResponse`

- [x] **Task 5 — Créer `router.py` (4 endpoints + dependency feature flag)** (AC: 3, 4)
  - [x] 5.1 `check_project_model_enabled` raise 404 si flag OFF
  - [x] 5.2 `POST /` `create_project_endpoint` → 501
  - [x] 5.3 `GET /{project_id}` → 501
  - [x] 5.4 `GET /` paginé → 501
  - [x] 5.5 `POST /{project_id}/memberships` → 501
  - [x] 5.6 `responses={404, 501}` sur chaque endpoint
  - [x] 5.7 Enregistrement dans `app/main.py` entre `esg_router` et `reports_router`

- [x] **Task 6 — Créer `service.py` (5 fonctions stubs)** (AC: 7)
  - [x] 6.1 5 signatures typées exactes
  - [x] 6.2 Corps `NotImplementedError("Story 10.2 skeleton — implemented in Epic 11 story 11-X")`
  - [x] 6.3 Docstring par fonction

### Phase 3 — Tools LangChain + project_node (AC5, AC6)

- [x] **Task 7 — Créer `backend/app/graph/tools/projects_tools.py`** (AC: 5)
  - [x] 7.1 Imports `with_retry`, `@tool`, `RunnableConfig`
  - [x] 7.2 `@tool async def create_project(name, state="idée", config=None)`
  - [x] 7.3 Corps `return "Module projects non encore implémenté (Epic 11)."` (stub sans raise)
  - [x] 7.4 `PROJECTS_TOOLS = [with_retry(create_project, max_retries=2, node_name="project")]`
  - [x] 7.5 Enregistrement dans `app/graph/tools/__init__.py`
  - [x] 7.6 README mis à jour (compteur 35 tools + ligne tableau)

- [x] **Task 8 — Créer `project_node` dans `backend/app/graph/nodes.py`** (AC: 6)
  - [x] 8.1 `async def project_node` juste avant `action_plan_node`
  - [x] 8.2 Corps : AIMessage + pose `active_module="project"` + `active_module_data={"node_visited": True}`
  - [x] 8.3 Pas de `get_llm()` ni `bind_tools`

- [x] **Task 9 — Brancher `project_node` dans `graph.py`** (AC: 6)
  - [x] 9.1 Import `project_node`
  - [x] 9.2 Import `PROJECTS_TOOLS` dans `build_graph`
  - [x] 9.3 `create_tool_loop("project", project_node, PROJECTS_TOOLS + INTERACTIVE_TOOLS + GUIDED_TOUR_TOOLS)`
  - [x] 9.4 Pas d'entrée dans `_route_after_router` ni conditional_edges
  - [x] 9.5 Docstring `build_graph` mise à jour

### Phase 4 — Tests + validation (AC8)

- [x] **Task 10 — Créer `backend/tests/test_projects/`** (AC: 8)
  - [x] 10.1 `__init__.py` + `conftest.py` (fixture `authenticated_client` + `company_factory`)
  - [x] 10.2 `test_models.py` — 5 tests (CRUD, unique triplet, enum values ×2, FK cascade DDL)
  - [x] 10.3 `test_router.py` — 4 tests (404 flag off, 501 flag on, 401 no auth, OpenAPI doc)
  - [x] 10.4 `test_feature_flags.py` dans `tests/test_core/` — default false + 15 valeurs parametrize
  - [x] 10.5 `test_projects_tools.py` — 2 tests (sentinel, stub message)
  - [x] 10.6 `test_graph/test_project_node_registered.py` — 1 smoke test
  - **Bonus** : `test_service.py` — 6 tests (5 service stubs NotImplementedError + 1 events)
  - **Bonus** : scan `test_no_tool_escapes_wrapping` étendu à `projects_tools`

- [x] **Task 11 — Validation baseline + coverage**
  - [x] 11.1 pytest full : 1283 passed + 6 skipped (baseline pre-10.2 = 1244 passed ; delta +39 ; objectif +12 largement dépassé)
  - [x] 11.2 Coverage module projects = **100 %** (173/173 stmts) ≥ 85 % cible, ≥ 80 % NFR60
  - [x] 11.3 34 tests Story 10.2 stables sur plusieurs runs
  - [x] 11.4 SQLite OK via `JSON().with_variant`

- [x] **Task 12 — Checklist code review self-audit**
  - [x] 12.1 CQ-6 : 7 fichiers module `projects/` < 400 lignes (max 175 lignes pour models.py)
  - [x] 12.2 CQ-8 : commentaires `# AC3` router, `# AC7` service, `# AC5` tools
  - [x] 12.3 CQ-11 : `PROJECTS_TOOLS = [with_retry(...)]` ; aucun `log_tool_call` manuel dans le tool
  - [x] 12.4 CCC-14 : `events.py` documente payloads Epic 11 sans émission MVP
  - [x] 12.5 NFR64 : `service.py` expose uniquement les 5 fonctions, aucune logique inline

---

## Dev Notes

### Pattern brownfield à répliquer (NE PAS RÉINVENTER)

**Référence absolue** : `backend/app/modules/esg/` (hors `criteria.py` et `weights.py` qui sont spécifiques ESG, pas de besoin projects).

Le module `modules/esg/` est livré depuis la spec 005. Consulter avant de commencer :
- `modules/esg/__init__.py:1` — docstring 1 ligne
- `modules/esg/router.py:1-103` — pattern endpoints CRUD, `Depends(get_current_user)`, `HTTPException` sans debug info, `response_model`, `status_code=201`
- `modules/esg/service.py:1-60` — signatures `async def xxx(db: AsyncSession, *, user_id: UUID, ...)`, paramètres kw-only après le `*` pour éviter les bugs positionnels
- `modules/esg/schemas.py:1-50` — Pydantic v2 avec `Field(ge=..., le=...)`, `model_config = ConfigDict(from_attributes=True)` pour les réponses mappées ORM
- `backend/app/graph/tools/esg_tools.py:1-80` puis ligne 335-340 — pattern `ESG_TOOLS = [with_retry(...)]`

**Différences avec ESG à observer** :
- `modules/esg/` livre la logique métier complète ; **projects/ livre uniquement le squelette**
- `service.py` ESG appelle `db.commit()` dans le router ; **projects/ raise NotImplementedError partout dans service.py**
- `ESG_TOOLS` a 5 tools matures ; **PROJECTS_TOOLS n'en a qu'1 stub**

### Feature flag — arbitrage Q1 404 vs 501 (CONTEXTE CRITIQUE)

La Story 10.1 (merged) a arbitré Q1 : **`ENABLE_PROJECT_MODEL=false` cache la feature entièrement (404)**, `=true` permet l'accès mais renvoie 501 tant qu'Epic 11 n'est pas livré.

**Implication concrète pour Story 10.2** :
1. La dependency FastAPI `check_project_model_enabled()` **doit lever avant** `Depends(get_current_user)` ? → **NON** : FastAPI résout les dependencies dans l'ordre déclaré dans la signature. En plaçant `_: None = Depends(check_project_model_enabled)` **après** `current_user: User = Depends(get_current_user)`, l'auth prime (401 d'abord, 404 ensuite). **C'est le comportement attendu** (AC3 + AC8 test 8).
2. Le 501 est déclenché **après** la dependency feature flag (qui a renvoyé 404 déjà filtré) + après l'auth. L'ordre final est donc : **401 → 404 → 501**.
3. Story 20.1 (fin Phase 1) supprimera `check_project_model_enabled` + la variable d'env — les endpoints passeront directement à l'Epic 11 real logic.

### Instrumentation tools — RÈGLE D'OR (retour post-9.7)

**Tout nouveau tool LangChain DOIT être wrappé `with_retry` dès sa création** — pas de dette à rattraper comme en Story 9.7 (qui a dû rétroactivement instrumenter 34 tools existants).

Pattern exact à copier depuis `esg_tools.py:335-340` :

```python
from app.graph.tools.common import with_retry
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool


@tool
async def create_project(
    name: str,
    state: str = "idée",
    config: RunnableConfig = None,
) -> str:
    """Créer un project pour l'entreprise (stub Epic 11).

    Args:
        name: Nom du projet (ex. « Ferme solaire 50 kW »).
        state: État initial (par défaut « idée »).
    Returns:
        Message d'état du squelette.
    """
    return "Module projects non encore implémenté (Epic 11)."


PROJECTS_TOOLS = [
    with_retry(create_project, max_retries=2, node_name="project"),
]
```

**⚠️ PIÈGE à éviter** : ne JAMAIS appeler `log_tool_call` manuellement dans le corps d'un tool — `with_retry` s'en charge automatiquement (voir `common.py:_safe_log`). Un appel manuel dupliquerait les lignes dans `tool_call_logs`.

### `project_node` minimal — pourquoi pas de LLM ?

Contrairement aux 9 autres nodes (chat, esg_scoring, carbon, financing, application, credit, action_plan, document, profiling) qui call `get_llm()` puis `bind_tools(...)` puis `ainvoke(messages)`, **`project_node` ne call pas le LLM**. Rationale :

1. **Pas de prompt dédié MVP** : Epic 11 Story 11-1 livrera `backend/app/prompts/project.py` avec le prompt système spécialisé. Sans prompt, le LLM hallucinerait.
2. **Pas de routing depuis `router`** : AC6 §5 interdit d'ajouter `"project"` dans `_route_after_router`. Le node est créé mais non-atteignable depuis une conversation normale. Le test smoke l'invoque explicitement via `config={"configurable": {"active_module": "project"}}`.
3. **Coût baseline** : éviter qu'une dépendance cassée `get_llm()` en CI (clé OpenRouter absente) ne casse les tests du squelette.

Le jour où Epic 11 S1 livre le prompt, la fonction `project_node` sera **réécrite** pour ressembler à `esg_scoring_node` (`get_llm`, `bind_tools`, `ainvoke`). C'est une réécriture, pas un ajout incrémental — le squelette actuel est jetable.

### Cohérence avec RLS (Story 10.5 à venir)

Le `service.get_project(db, project_id, owner_user_id)` filtre par `owner_user_id` via la chaîne `Project.company_id IN (SELECT id FROM companies WHERE owner_user_id = ?)`. Quand Story 10.5 activera RLS sur `companies` + `fund_applications` + `facts` + `documents` (pas directement sur `projects`), le filtre applicatif restera nécessaire car **`projects` n'est PAS dans la liste des 4 tables RLS Story 10.5**. L'isolation tenant sur `projects` vient indirectement via `companies.owner_user_id`.

**Test RLS futur** (Story 10.5) : créer un user A avec `project_A`, puis dans une session RLS user B, vérifier que `list_projects_by_owner(db, owner_user_id=user_A.id)` ne retourne rien. Mais **ce test n'est pas dans Story 10.2** — Story 10.5 le couvrira avec le pattern `test_rls_companies.py`.

### CCC-14 Outbox — `events.py` préparation sans émission

`events.py` déclare des constantes pour les `event_type` prévus Epic 11 sans les émettre (Story 10.10 livrera le worker). Le but : **consommateurs futurs importent depuis une source unique**, évitant le « chaîne de strings hardcodés » qui rendrait le refactor Outbox douloureux.

```python
# backend/app/modules/projects/events.py
"""Domain events émis par le module projects (D11 micro-Outbox).

Les events listés ici seront insérés dans `domain_events` par Epic 11.
Story 10.10 livrera le worker APScheduler qui les consomme.

Payloads attendus (documentation uniquement MVP) :
- project.created : {project_id: UUID, company_id: UUID, name: str}
- project.status_changed : {project_id: UUID, from: str, to: str}
"""
from typing import Final, Literal

PROJECT_CREATED_EVENT_TYPE: Final[Literal["project.created"]] = "project.created"
PROJECT_STATUS_CHANGED_EVENT_TYPE: Final[Literal["project.status_changed"]] = "project.status_changed"
```

### Previous Story Intelligence

**Story 10.1** (merged 2026-04-20) : migration 020 crée toutes les tables consommées par ce module. **Ne pas dupliquer le schéma** — les modèles ORM de Story 10.2 se mappent **exactement** sur ce qui existe en base. Si un champ manque dans 020 (rare, mais possible), **NE PAS** créer une nouvelle migration 028 — ouvrir un défer dans `deferred-work.md` et faire arbitrer par le PM.

**Leçons 10.1** (code review 2026-04-20) :
- `psycopg2-binary>=2.9.9` dans `requirements-dev.txt` (déjà ajouté) → les tests PostgreSQL marchent en local. Vérifier `backend/requirements-dev.txt` avant de lancer les tests postgres.
- Fixture `alembic_config` dans `conftest.py` — réutilisable pour `test_migrations` mais **pas nécessaire ici** (Story 10.2 utilise SQLite via `Base.metadata.create_all`).
- Marker `@pytest.mark.postgres` skippe automatiquement en SQLite — si un test RLS arrive accidentellement dans 10.2, le marker le skippe proprement.

**Story 9.7** (merged 2026-04-20) : `with_retry` + `log_tool_call` livrés. **Ne jamais appeler `log_tool_call` directement** dans un tool — laisser `with_retry` s'en charger (voir AC5).

### Git Intelligence (5 derniers commits)

```
06bcf99  Story 9.7 ship (observabilité tools)
92f36f5  idem
94ee7e5  Story 9.4 OCR bilingue
39006a8  Stories 9.1/9.2/9.3
99f2fb4  /bmad-document-project
```

**Pattern squash-merge** : chaque story est squash-mergée avec message `<story-key>: done`. Pour Story 10.2, prévoir un commit final `10-2-module-projects-squelette: done` après validation code review.

**Commits incrémentaux recommandés** :
1. `10-2: models.py + enums + register in app/models/__init__.py`
2. `10-2: feature_flags + schemas + router stubs 404/501`
3. `10-2: service.py stubs + NotImplementedError`
4. `10-2: projects_tools.py + register in INSTRUMENTED_TOOLS`
5. `10-2: project_node + graph.py registration`
6. `10-2: tests 13 green + coverage ≥ 80%`
7. (squash au merge)

### Latest Tech Info (Pydantic v2, SQLAlchemy 2.x, LangChain ≥ 0.3, FastAPI)

- **Pydantic v2** : `model_config = ConfigDict(from_attributes=True)` (ex `Config.orm_mode = True`). `Field(ge=0, le=100)` pour les bornes. `Literal["project.created"]` pour les event types (events.py).
- **SQLAlchemy 2.0** : `Mapped[...]` + `mapped_column(...)` (pas `Column()` legacy). `UUID(as_uuid=True)` depuis `sqlalchemy.dialects.postgresql`. `JSONB().with_variant(JSON(), "sqlite")` pour cross-dialect (pattern spec 018 validé).
- **FastAPI** : `Depends(...)` résolu dans l'ordre déclaré. Pour 401 before 404 : placer `current_user: User = Depends(get_current_user)` AVANT `_: None = Depends(check_project_model_enabled)` dans la signature (le test 8 AC8 vérifie).
- **LangGraph / LangChain ≥ 0.3** : `@tool` décorateur depuis `langchain_core.tools`. `ToolNode` depuis `langgraph.prebuilt`. `RunnableConfig` depuis `langchain_core.runnables`. Pattern `bind_tools` : Epic 11 l'implémentera dans `project_node`, pas ici.

### Project Structure Notes

**Alignment avec unified project structure (CLAUDE.md + architecture.md)** :
- ✅ `backend/app/modules/projects/` respecte pattern NFR62 `modules/<domain>/{router,service,schemas,models}.py`
- ✅ `enums.py` + `events.py` extensions cohérentes avec architecture.md §«Organisation des 3 nouveaux modules»
- ✅ Tests dans `backend/tests/test_projects/` (convention `test_<module>_<function>.py` pour nommage fichiers internes)
- ✅ Feature flag dans `backend/app/core/feature_flags.py` (pas de nouveau top-level)

**Variances détectées** (documentées, acceptées) :
- **`project_node` sans LLM** — divergence intentionnelle avec les 9 autres nodes (voir Dev Notes ci-dessus). Sera aligné Epic 11 Story 11-1.
- **`service.py` 100 % `NotImplementedError`** — divergence avec `modules/esg/service.py` qui livre logique complète. Intentionnel : squelette. Epic 11 comblera.

---

## References

- [Source: _bmad-output/planning-artifacts/epics/epic-10.md#story-102] — AC1-AC6 originaux
- [Source: _bmad-output/planning-artifacts/epics/epic-10.md#story-109] — AC1 feature flag `is_project_model_enabled`
- [Source: _bmad-output/planning-artifacts/epics/epic-11.md] — Cluster A Epic 11 consommateur
- [Source: _bmad-output/planning-artifacts/architecture.md#décision-1] — Modèle Company × Project N:N cumul rôles
- [Source: _bmad-output/planning-artifacts/architecture.md#décision-11] — Transaction boundaries + micro-Outbox MVP (D11)
- [Source: _bmad-output/planning-artifacts/architecture.md#patterns-structurels] — Organisation 3 nouveaux modules (§ lignes 921-958)
- [Source: _bmad-output/implementation-artifacts/10-1-migrations-alembic-020-027.md] — Story 10.1 (done, migration 020)
- [Source: backend/alembic/versions/020_create_projects_schema.py] — Schéma SQL des 6 tables à mapper en ORM
- [Source: backend/app/graph/tools/common.py] — `with_retry` + `log_tool_call` (Story 9.7)
- [Source: backend/app/modules/esg/router.py] — Pattern router à dupliquer
- [Source: backend/app/modules/esg/service.py] — Pattern service (signatures kw-only après `*`)
- [Source: backend/app/graph/tools/esg_tools.py:335-340] — Pattern `TOOLS = [with_retry(...)]`
- [Source: backend/app/graph/graph.py] — `create_tool_loop` + registration pattern
- [Source: backend/app/graph/nodes.py:554] — `esg_scoring_node` référence pour pattern node (à **diverger** : project_node sans LLM)
- [Source: backend/app/graph/tools/README.md] — Guide ajout tool (§2 Pattern)
- [Source: CLAUDE.md#conventions-de-developpement] — NFR62 structure modules, snake_case Python
- [Source: backend/app/models/__init__.py] — Registration globale modèles SQLAlchemy

---

## Dev Agent Record

### Agent Model Used

claude-opus-4-7[1m] (Opus 4.7, 1M context)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed — comprehensive developer guide created pour Story 10.2 (squelette `projects/` + `project_node` + `projects_tools.py`).
- **Implementation 2026-04-20** (dev-story workflow) — les 12 tasks + 8 AC sont satisfaits. Résumé :
  - **Phase 1** : 6 fichiers module `projects/` créés + 7e modèle `Company` minimal ajouté pour satisfaire les FK `company_id → companies.id` en SQLite (Epic 11 Story 11-1 enrichira). 6 modèles ORM enregistrés dans `app/models/__init__.py`.
  - **Phase 2** : `feature_flags.py` (no cache, truthy `true/1/yes`), 4 endpoints router avec dependency `check_project_model_enabled` + dependency `get_current_user` en premier (ordre 401 → 404 → 501 validé par test 8). `service.py` 5 fonctions kw-only avec `NotImplementedError` explicite. Router branché dans `main.py` entre `esg_router` et `reports_router`.
  - **Phase 3** : `projects_tools.py` avec `create_project` wrappé `with_retry(max_retries=2, node_name="project")` **dès la création** (règle d'or 9.7). Aucun try/except ni log manuel dans le corps du tool (CQ-11). `project_node` ajouté dans `nodes.py` avant `action_plan_node`, sans appel LLM (distingué des 9 autres nodes — rationale documenté dans les dev notes). Node branché via `create_tool_loop` dans `graph.py` **sans entrée dans `_route_after_router`** (Epic 11 ajoutera l'heuristique).
  - **Phase 4** : 34 tests Story 10.2 verts (dépasse plancher +12). Coverage module projects = **100 %**. Baseline pre-10.2 réelle = 1244 passed ; post-10.2 = 1283 passed + 6 skipped (test_security Story 10.5). Zero régression.
  - **Défenses anti-régression** : scan `test_no_tool_escapes_wrapping` étendu à `projects_tools` pour détecter automatiquement les futurs tools non-wrappés. Test DDL `test_fk_cascade_project_delete_membership` valide la metadata `ondelete="CASCADE"` (runtime cascade SQLite non garanti sans PRAGMA foreign_keys=ON sur la connexion — validation PostgreSQL future Story 10.5).
- **Durée réelle** : ~1h30 (calibration vélocité). Estimation originale story non indiquée dans le file, mais proche du budget « 2ᵉ story Epic 10 après 10.1 done ».
- **Patches post-review (2026-04-20)** — décision `APPROVE-WITH-CHANGES` du rapport `10-2-code-review-2026-04-20.md` adressée via 3 patches documentaires (zéro code métier touché, zéro régression) :
  - ✅ **MEDIUM-10.2-1** : docstring enrichie sur `backend/app/modules/projects/models.py::Company` (note explicite de coexistence avec `app.models.company.CompanyProfile`, plan migration Story 11-1 + dépréciation Story 20.1) + entrée dédiée dans `deferred-work.md` §« Migration Cluster A : CompanyProfile → Company ».
  - ✅ **MEDIUM-10.2-2** : TODO Epic 11 S1 explicite ajouté au-dessus de `_MODULE_ROUTE_FLAGS` et `module_labels` dans `backend/app/graph/nodes.py` (checklist 4 points à aligner avant d'activer le routing projet) + entrée `deferred-work.md` avec la checklist complète (route flag, label module, `_route_after_router`, conditional_edges).
  - ✅ **LOW-10.2-5** : docstring ASCII `build_graph` (`backend/app/graph/graph.py`) complétée avec la ligne `[project 🚧] → project_node ⟲ project_tools → END (squelette — unreachable Epic 11)` pour alignement visuel avec les 8 autres modules.
  - 📋 **LOW/INFO tracés dans `deferred-work.md`** : LOW-10.2-1 (rename `state` → `initial_status`), LOW-10.2-2 (coercion `"idée"` → enum), LOW-10.2-3 (test `flag OFF + no auth`), LOW-10.2-4 (coordination blacklist tool_args Epic 11), LOW-10.2-6 (test `test_migration_enum_values_match_python_enum`).
  - ✅ **Validation post-patches** : 66 tests verts (`tests/test_projects/` + `test_project_node_registered.py` + `test_tools_instrumentation.py`), aucune régression, `build_graph()` OK avec `project` node enregistré.

### File List

**Créés** :
- `backend/app/modules/projects/__init__.py`
- `backend/app/modules/projects/enums.py`
- `backend/app/modules/projects/events.py`
- `backend/app/modules/projects/models.py` (7 modèles : 6 story + Company stub)
- `backend/app/modules/projects/schemas.py`
- `backend/app/modules/projects/service.py`
- `backend/app/modules/projects/router.py`
- `backend/app/core/feature_flags.py`
- `backend/app/graph/tools/projects_tools.py`
- `backend/tests/test_projects/__init__.py`
- `backend/tests/test_projects/conftest.py`
- `backend/tests/test_projects/test_models.py`
- `backend/tests/test_projects/test_router.py`
- `backend/tests/test_projects/test_projects_tools.py`
- `backend/tests/test_projects/test_service.py` (bonus — AC7 service stubs + events)
- `backend/tests/test_core/test_feature_flags.py`
- `backend/tests/test_graph/test_project_node_registered.py`

**Modifiés** :
- `backend/app/models/__init__.py` (enregistrement des 6 modèles projects + Company)
- `backend/app/main.py` (include_router projects_router)
- `backend/app/graph/nodes.py` (ajout `project_node` + TODO Epic 11 S1 sur `_MODULE_ROUTE_FLAGS` et `module_labels` — patch MEDIUM-10.2-2)
- `backend/app/graph/graph.py` (import + `create_tool_loop("project", ...)` + docstring enrichie ligne `[project 🚧]` — patch LOW-10.2-5)
- `backend/app/graph/tools/__init__.py` (import + `PROJECTS_TOOLS` dans `INSTRUMENTED_TOOLS` + `__all__`)
- `backend/app/graph/tools/README.md` (tableau inventaire + compteur 35 tools)
- `backend/app/modules/projects/models.py` (docstring `Company` enrichie — patch MEDIUM-10.2-1)
- `backend/tests/test_graph/test_tools_instrumentation.py` (scan anti-régression étendu à `projects_tools`)
- `_bmad-output/implementation-artifacts/deferred-work.md` (section dédiée §« Deferred from: code review of story-10.2 (2026-04-20) » — 2 MEDIUM patchés traçés + 5 LOW defers)

### Change Log

| Date | Type | Description |
|------|------|-------------|
| 2026-04-20 | feat | Story 10.2 — module `projects/` squelette livré : 7 fichiers module + feature_flags + router 4 endpoints 401/404/501 + project_node 10ᵉ nœud + create_project tool instrumenté with_retry + 34 tests verts (coverage module 100 %). Zero régression sur 1244 tests baseline. |
| 2026-04-20 | docs | Addressed code review findings — 3 items resolved : MEDIUM-10.2-1 (docstring `Company` coexistence `CompanyProfile` + `deferred-work.md` Story 11-1 / 20.1), MEDIUM-10.2-2 (TODO Epic 11 S1 sur `_MODULE_ROUTE_FLAGS` + `module_labels` + checklist 4 points dans `deferred-work.md`), LOW-10.2-5 (docstring ASCII `build_graph` complétée avec ligne `[project 🚧]`). 5 LOW déférés tracés dans `deferred-work.md`. 66 tests ciblés verts, zéro régression. |
