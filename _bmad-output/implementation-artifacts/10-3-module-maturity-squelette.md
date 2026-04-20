# Story 10.3 : Module `maturity/` squelette (router + service + schemas + models + node LangGraph)

Status: ready-for-dev

> **Contexte** : 3ᵉ story Epic 10 Fondations Phase 0 (BLOQUANT Cluster A' Epic 12 FR11–FR16). Socle technique minimal du module `maturity` — router REST stub, service, schemas Pydantic, models SQLAlchemy ORM, `formalization_plan_calculator.py` stub, nœud LangGraph `maturity_node` + `maturity_tools.py`. **Aucune logique métier MVP** : les endpoints renvoient 501 Not Implemented avec message « livré en Epic 12 ». Epic 12 y déposera la vraie implémentation (self-déclaration, OCR validation, plan de formalisation pays-spécifique, auto-reclassement).
>
> **Dépendances** :
> - Story 10.1 **done** (migration `021_create_maturity_schema.py` : tables `admin_maturity_levels` 5 niveaux 1–5, `formalization_plans`, `admin_maturity_requirements` avec UNIQUE `(country, level_id)` + colonnes SOURCE-TRACKING `source_url/source_accessed_at/source_version`).
> - Story 9.7 **done** (`with_retry` + `log_tool_call` dans `backend/app/graph/tools/common.py` — **OBLIGATOIRE** dès la création des tools, pas de dette à rattraper).
> - Story 10.2 **review/done** (pattern `projects/` établi ci-dessous — **ne pas réinventer**).
>
> **Bloque** :
> - Story 10.11 (sourcing Annexe F + CI `source_url` HTTP 200) qui enforce les colonnes SOURCE-TRACKING de `admin_maturity_levels` + `admin_maturity_requirements`.
> - Epic 12 entier (FR11–FR16 Cluster A' maturité graduée + formalisation) — consomme ce squelette.

---

## Story

**As a** PME User (owner) — represented here by l'Équipe Mefali backend,
**I want** disposer du socle technique minimal du module `maturity` (router REST stub, service, schemas Pydantic, models ORM des 3 tables migration 021, `maturity_node` LangGraph 11ᵉ nœud spécialiste, `maturity_tools.py` avec au moins 1 tool `declare_maturity_level` **déjà instrumenté** `with_retry` + `log_tool_call`, squelette `formalization_plan_calculator.py`),
**So that** les 6 stories Epic 12 (FR11–FR16) puissent y déposer la logique métier (self-déclaration, OCR validation FR12, FormalizationPlan pays-spécifique FR13, auto-reclassement FR15, audit trail FR16) sans recréer la plomberie, et que le catalogue data-driven `admin_maturity_requirements(country, level_id)` soit consommable dès Epic 12.

---

## Acceptance Criteria

### AC1 — Structure du module `backend/app/modules/maturity/` conforme au pattern `modules/projects/`

**Given** le repository dans l'état `main @ HEAD` avec Story 10.1 mergée (migration 021 appliquée) et Story 10.2 mergée (pattern `projects/` établi),
**When** un développeur exécute `ls backend/app/modules/maturity/`,
**Then** le dossier contient **exactement** les fichiers suivants (pattern brownfield `modules/projects/` — NFR62 CLAUDE.md) :
  - `__init__.py` (docstring 1 ligne : « Module Maturity : Cluster A' maturité administrative graduée (FR11–FR16). »)
  - `router.py` (APIRouter préfixe `/api/maturity`, tags `["maturity"]`)
  - `service.py` (fonctions métier — stubs `NotImplementedError("livré en Epic 12 story 12-X")`)
  - `schemas.py` (Pydantic v2 : `MaturityLevelDeclaration`, `MaturityLevelResponse`, `FormalizationPlanResponse`, `FormalizationPlanStep`, `AdminMaturityRequirementResponse`, `MaturityWorkflowStateEnum`, `MaturityChangeDirectionEnum`)
  - `models.py` (SQLAlchemy 2.0 ORM : `AdminMaturityLevel`, `FormalizationPlan`, `AdminMaturityRequirement` — mappés **exactement** sur les 3 tables créées par migration 021)
  - `enums.py` (`MaturityWorkflowStateEnum`, `MaturityChangeDirectionEnum` — **source unique** réutilisée par `schemas.py`, `models.py`, `service.py`)
  - `events.py` (squelette avec 3 constantes `MATURITY_LEVEL_UPGRADED_EVENT_TYPE`, `MATURITY_LEVEL_DOWNGRADED_EVENT_TYPE`, `FORMALIZATION_PLAN_GENERATED_EVENT_TYPE` + docstring documentant les payloads `domain_events` émis Epic 12 — **pas d'émission réelle MVP**, préparation D11 CCC-14)
  - `formalization_plan_calculator.py` (stub classe `FormalizationPlanCalculator` avec méthode unique `async def generate(self, db, *, company_id, current_level, target_level, country) -> FormalizationPlan` qui raise `NotImplementedError("livré en Epic 12 story 12-3")` — **déclaré ici** pour réserver le point d'extension et la signature)
**And** tous les fichiers ont une docstring d'en-tête `"""<description courte>.\n\nStory 10.3 — module `maturity/` squelette.\nFR covered: [] (infra FR11–FR16), NFR covered: [NFR49, NFR62, NFR64, NFR66].\n"""`
**And** `from app.modules.maturity import router, service, schemas, models, enums, events, formalization_plan_calculator` **importe sans erreur**.

### AC2 — `models.py` expose les 3 modèles ORM SQLAlchemy 2.0 mappés sur migration 021

**Given** la migration 021 appliquée (tables `admin_maturity_levels`, `formalization_plans`, `admin_maturity_requirements`),
**When** un développeur importe les modèles et exécute un cycle CRUD SQLite in-memory,
**Then** chaque modèle respecte strictement le schéma de la migration (vérifier `backend/alembic/versions/021_create_maturity_schema.py` ligne par ligne) :
  - `AdminMaturityLevel(id UUID PK, level INT NOT NULL CHECK BETWEEN 1 AND 5, code STR(32) UNIQUE, label_fr STR(255) NOT NULL, description TEXT NULLABLE, workflow_state STR(16) NOT NULL DEFAULT 'draft', is_published BOOL NOT NULL DEFAULT false, source_url TEXT NULLABLE, source_accessed_at TIMESTAMPTZ NULLABLE, source_version STR(64) NULLABLE, created_at, updated_at)` **— `level` UNIQUE via `uq_maturity_level`, `code` UNIQUE via `uq_maturity_code`**.
  - `FormalizationPlan(id UUID PK, company_id UUID FK companies.id ON DELETE CASCADE, current_level_id UUID FK admin_maturity_levels.id ON DELETE SET NULL NULLABLE, target_level_id UUID FK admin_maturity_levels.id ON DELETE SET NULL NULLABLE, actions_json JSONB/JSON NULLABLE, status STR(32) NOT NULL DEFAULT 'draft', created_at, updated_at)` **— index `ix_formalization_plans_company_id`**.
  - `AdminMaturityRequirement(id UUID PK, country STR(64) NOT NULL, level_id UUID FK admin_maturity_levels.id ON DELETE RESTRICT NOT NULL, requirements_json JSONB/JSON NOT NULL, workflow_state STR(16) NOT NULL DEFAULT 'draft', is_published BOOL NOT NULL DEFAULT false, source_url TEXT NULLABLE, source_accessed_at TIMESTAMPTZ NULLABLE, source_version STR(64) NULLABLE, created_at, updated_at, UNIQUE (country, level_id))`.
**And** les types utilisent `UUIDMixin` + `TimestampMixin` de `app.models.base` pour les 3 modèles (tous ont `created_at`/`updated_at` dans la migration).
**And** `enums.py::MaturityWorkflowStateEnum` a **exactement** les 3 valeurs `{draft, review_requested, published}` (cohérent avec colonne `workflow_state` des tables — Décision 6 state machine N1/N2/N3 simplifiée MVP, valeurs stockées en String(16) côté BDD, l'enum Python est l'invariant côté code).
**And** `enums.py::MaturityChangeDirectionEnum` a **exactement** les 2 valeurs `{upgrade, downgrade}` (cohérent avec AC1 Epic 12 Story 12.5 `MaturityChangeLog.direction`).
**And** les 3 modèles sont **enregistrés dans `app/models/__init__.py`** via import explicite `from app.modules.maturity.models import AdminMaturityLevel, FormalizationPlan, AdminMaturityRequirement  # noqa: F401` pour que SQLAlchemy metadata les connaisse (sinon `Base.metadata.create_all` les ignore, cassant tests SQLite — **piège validé en 10.2**).
**And** les cross-dialects : `actions_json` et `requirements_json` utilisent `JSONB().with_variant(JSON(), "sqlite")` via helper `_jsonb()` (pattern `projects/models.py:46-48` à dupliquer).

### AC3 — `router.py` expose 3 endpoints stubs avec comportement 401/501 (pas de feature flag)

**Given** `backend/app/modules/maturity/router.py` branché dans `backend/app/main.py` via `app.include_router(maturity_router, prefix="/api/maturity", tags=["maturity"])`,
**When** un client appelle les endpoints sans JWT valide (header `Authorization` absent ou invalide),
**Then** **tous** les endpoints renvoient **401 Unauthorized** (dépendance `Depends(get_current_user)` garantit ce comportement, cohérent avec `modules/projects/router.py` **et** `modules/esg/router.py`).
**And** les 3 endpoints stubs exposés sont (alignés sur Epic 12 FR11–FR13) :
  - `POST /api/maturity/declare` → self-déclaration de niveau (body `MaturityLevelDeclaration` avec champ `level: str`) — **source Epic 12 Story 12.1 AC1**
  - `GET /api/maturity/formalization-plan` → récupération du plan de formalisation de l'entreprise courante — **source Epic 12 Story 12.3 AC1**
  - `GET /api/maturity/levels` → catalogue paginé des `AdminMaturityLevel` **publiés uniquement** (`is_published = true`)
**And** **contrairement à `projects/`, il n'y a PAS de feature flag `ENABLE_MATURITY_MODEL`** — aucune variable d'env introduite par cette story (arbitrage Q1 Story 10.1 visait uniquement `ENABLE_PROJECT_MODEL`). Les 3 endpoints renvoient **directement 501 Not Implemented** avec payload `{"detail": "Maturity module skeleton — implementation delivered in Epic 12"}` **pour les 3 endpoints indistinctement** tant qu'Epic 12 n'est pas livré.
**And** la documentation OpenAPI de chaque endpoint **inclut** `responses={501: {"description": "Maturity module skeleton — Epic 12 not yet delivered"}}` (CQ-8 documentation structurée).
**And** l'ordre des dependencies respecte **401 → 501** : `current_user: User = Depends(get_current_user)` est déclaré AVANT toute autre dépendance dans la signature de chaque endpoint (cohérent avec pattern 10.2 AC3).

### AC4 — `maturity_tools.py` expose ≥ 1 tool stub `declare_maturity_level` wrappé `with_retry` + auto-journalisé (CQ-11)

**Given** `backend/app/graph/tools/maturity_tools.py` créé,
**When** inspecté,
**Then** il expose au minimum le tool `@tool async def declare_maturity_level(level: str, config: RunnableConfig | None = None) -> str` avec les caractéristiques suivantes :
  - Signature conforme au pattern `esg_tools.create_esg_assessment` et `projects_tools.create_project` (`RunnableConfig` dernier argument positionnel, default `None`).
  - Docstring en français décrivant l'objectif, l'argument `level` (format attendu : code string `{informel, rccm_nif, comptes_cnps, ohada_audite}` — **documenté** mais **pas validé MVP** côté tool, Epic 12 ajoutera la validation contre `AdminMaturityLevel.code`), et la valeur de retour (exploitée par LangChain pour le prompt LLM).
  - Implémentation : **retourne `"Module maturity non encore implémenté (Epic 12)."`** (stub explicite, pas de `raise NotImplementedError` qui ferait crash côté LLM — leçon 10.2).
  - Journalisation **automatique** via le wrapper `with_retry` (aucun appel `log_tool_call` manuel dans le corps du tool, CQ-11 enforcement — piège documenté 10.2).
**And** `MATURITY_TOOLS = [with_retry(declare_maturity_level, max_retries=2, node_name="maturity")]` est défini en fin de fichier **(attribut sentinelle `_is_wrapped_by_with_retry=True` vérifiable via `assert MATURITY_TOOLS[0]._is_wrapped_by_with_retry is True`)**.
**And** `MATURITY_TOOLS` est **exporté** dans `backend/app/graph/tools/__init__.py` :
  - Import `from app.graph.tools.maturity_tools import MATURITY_TOOLS`
  - Ajouté à la liste `INSTRUMENTED_TOOLS` **entre `PROJECTS_TOOLS` et `ESG_TOOLS`** (ordre cohérent avec Cluster A → A' → ESG ; documenté commentaire).
  - Exporté dans `__all__`.
**And** `backend/app/graph/tools/README.md` est mis à jour : ligne ajoutée au tableau de la Section 1 `| maturity_tools.py | maturity | declare_maturity_level |` **ET** compteur tools passé de « 35 tools » à « 36 tools ».

### AC5 — `maturity_node` enregistré dans `graph.py` (11ᵉ nœud spécialiste, sans routing métier MVP)

**Given** `backend/app/graph/nodes.py` contient actuellement 10 nœuds (`router_node`, `document_node`, `chat_node`, `esg_scoring_node`, `carbon_node`, `financing_node`, `application_node`, `credit_node`, `action_plan_node`, `project_node` post-10.2),
**When** une fonction `async def maturity_node(state: ConversationState) -> ConversationState` est ajoutée **immédiatement après `project_node`** (ordre alpha cluster : project → maturity),
**Then** elle a le comportement **minimal** suivant (pas de logique métier — **ne construit pas de prompt, ne call pas le LLM** car Epic 12 Story 12-X livrera le prompt dédié et le routing LLM complet — même rationale que `project_node` 10.2 AC6) :
  - **Pas de bind_tools ni d'invocation LLM** (diffère des 9 autres nodes actifs, identique à `project_node`).
  - Retourne simplement `{"messages": [AIMessage(content="Module maturity — squelette activé (Epic 12 livre la logique métier).")], "active_module": "maturity", "active_module_data": {"node_visited": True}}` pour clôturer la boucle proprement et empêcher le router de re-router (pattern spec 013 multi-tour).
  - **Aucun appel aux tools `MATURITY_TOOLS`** dans ce corps (les tools sont accessibles via le `ToolNode` configuré dans `graph.py` mais le LLM ne les appellera pas tant qu'il n'y a pas de prompt métier).
**And** dans `backend/app/graph/graph.py` :
  - L'import ajoute `maturity_node` (ordre alpha) : `from app.graph.nodes import action_plan_node, application_node, carbon_node, chat_node, credit_node, document_node, esg_scoring_node, financing_node, maturity_node, project_node, router_node`
  - L'import ajoute `from app.graph.tools.maturity_tools import MATURITY_TOOLS` (après `PROJECTS_TOOLS`).
  - Appel : `create_tool_loop(graph, "maturity", maturity_node, tools=MATURITY_TOOLS + INTERACTIVE_TOOLS + GUIDED_TOUR_TOOLS)` immédiatement après l'appel `create_tool_loop(graph, "project", ...)` (injection `INTERACTIVE_TOOLS` + `GUIDED_TOUR_TOOLS` cohérente avec les autres nœuds features 018 + 019).
  - La docstring `build_graph` est mise à jour pour lister le nouveau flux `Story 10.3 : [maturity] → maturity_node ⟲ maturity_tools → END est déclaré mais non atteignable depuis le router (pas d'entrée dans _route_after_router) tant qu'Epic 12 ne définit pas son heuristique de routage` (pour documentation visuelle).
  - **⚠️ AUCUNE entrée dans `_route_after_router`** ni dans le `conditional_edges` dict de `router` — le node existe dans le graphe mais **n'est pas atteignable depuis le router tant qu'Epic 12 ne définit pas son heuristique de routage** (évite d'attirer du trafic LLM sans prompt). Le node est joignable uniquement via un test qui invoque `compiled_graph.invoke({...}, config={"configurable": {"active_module": "maturity"}})` — comportement attendu pour un squelette (cf. `test_graph/test_project_node_registered.py` Story 10.2 à dupliquer).

### AC6 — `service.py` expose la surface d'API consommée par Epic 12 sans accéder directement aux tables

**Given** un futur consommateur Epic 12 (router Epic 12, `FormalizationPlanCalculator`, handler auto-reclassement),
**When** il importe `from app.modules.maturity.service import declare_maturity_level, get_formalization_plan, list_published_levels, get_requirements_for_country_level, create_formalization_plan`,
**Then** les 5 fonctions sont **présentes** dans `service.py` avec signatures typées :
  - `async def declare_maturity_level(db: AsyncSession, *, company_id: UUID, level_code: str, actor_user_id: UUID) -> FormalizationPlan | None` (retourne le plan existant ou None — Epic 12 décidera si création implicite)
  - `async def get_formalization_plan(db: AsyncSession, *, company_id: UUID) -> FormalizationPlan | None` (FR13 Epic 12.3)
  - `async def list_published_levels(db: AsyncSession) -> list[AdminMaturityLevel]` (filtre `is_published = True`)
  - `async def get_requirements_for_country_level(db: AsyncSession, *, country: str, level_id: UUID) -> AdminMaturityRequirement | None` (point d'entrée data-driven FR13 : **zéro string hardcodé côté Python pour « Sénégal »/« Côte d'Ivoire »** — toute consommation passe par ce helper)
  - `async def create_formalization_plan(db: AsyncSession, *, company_id: UUID, current_level_id: UUID, target_level_id: UUID, actions: list[dict]) -> FormalizationPlan` (invoqué par `FormalizationPlanCalculator.generate` en Epic 12)
**And** chaque fonction lève **`NotImplementedError("Story 10.3 skeleton — implemented in Epic 12 story 12-X")`** (message explicite — les tests unitaires vérifient l'exception, PAS la logique).
**And** **anti-pattern God service (NFR64)** : `service.py` **n'importe jamais `from sqlalchemy import select` dans son corps** sauf pour les 5 fonctions ci-dessus (les imports sont OK, l'interdit porte sur l'usage) ; aucune autre fonction ne lit/écrit directement les tables `admin_maturity_levels`/`formalization_plans`/`admin_maturity_requirements`. Les consommateurs externes (router Epic 12, `formalization_plan_calculator.py`, OCR validator, auto-reclassement handler) **doivent passer par ces 5 fonctions**, jamais par un `select(AdminMaturityLevel)` inline.

### AC7 — `formalization_plan_calculator.py` squelette avec signature `generate()` documentée

**Given** le besoin de réserver le point d'extension Epic 12 Story 12.3 (FR13 — plan de formalisation pays-spécifique data-driven),
**When** `backend/app/modules/maturity/formalization_plan_calculator.py` est inspecté,
**Then** il expose une classe `FormalizationPlanCalculator` avec **exactement** :
  - Constructeur vide `def __init__(self) -> None` (pas de dépendance injectée MVP — Epic 12 décidera DI service).
  - Une méthode async unique `async def generate(self, db: AsyncSession, *, company_id: UUID, current_level_id: UUID, target_level_id: UUID, country: str) -> FormalizationPlan` qui :
    - Docstring détaillée : « Génère un plan de formalisation pays-spécifique (FR13). Les étapes sont **copiées depuis `AdminMaturityRequirement.requirements_json` du pays** au moment de la génération (zéro hardcoding Python). Epic 12 Story 12.3 livrera l'implémentation. »
    - Corps : `raise NotImplementedError("Story 10.3 skeleton — FormalizationPlanCalculator.generate delivered in Epic 12 story 12.3")`.
**And** **aucune logique métier** (pas de lookup de `AdminMaturityRequirement`, pas de construction de steps, pas d'insertion en base) n'est présente — la classe fait 1 fichier < 30 lignes, tout le corps est stub.
**And** le fichier est importable via `from app.modules.maturity.formalization_plan_calculator import FormalizationPlanCalculator` sans effet de bord au chargement (pas d'instanciation module-level).

### AC8 — Tests minimum livrés dans `backend/tests/test_maturity/` (plancher 14 tests verts + country-data-driven)

**Given** `backend/tests/test_maturity/__init__.py` créé,
**When** `pytest backend/tests/test_maturity/ -v` exécuté,
**Then** les **14 tests minimum** suivants passent tous (plancher +14 ≥ baseline +12 exigée) :

| # | Fichier test | Test | Vérifie |
|---|--------------|------|---------|
| 1 | `test_models.py` | `test_admin_maturity_level_crud_sqlite` | INSERT → SELECT → UPDATE `is_published` → DELETE sur `AdminMaturityLevel` via AsyncSession SQLite |
| 2 | `test_models.py` | `test_admin_maturity_level_unique_code_and_level` | 2ᵉ INSERT même `code` ou même `level` lève `IntegrityError` (UNIQUE migration 021) |
| 3 | `test_models.py` | `test_admin_maturity_level_check_level_between_1_and_5` | INSERT `level=0` ou `level=6` lève `IntegrityError` — **si PostgreSQL disponible** ; SQLite ne gère pas CHECK → test marqué `@pytest.mark.postgres` skippé proprement (pattern 10.1) |
| 4 | `test_models.py` | `test_formalization_plan_fk_cascade_on_company_delete` | Suppression d'une `Company` cascade les `FormalizationPlan` liés via `ON DELETE CASCADE` (DDL metadata validée) |
| 5 | `test_models.py` | `test_admin_maturity_requirement_unique_country_level` | 2ᵉ INSERT même `(country, level_id)` lève `IntegrityError` (uq_maturity_country_level) |
| 6 | `test_models.py` | `test_maturity_workflow_state_enum_values` | `MaturityWorkflowStateEnum` a exactement 3 valeurs `{draft, review_requested, published}` |
| 7 | `test_models.py` | `test_maturity_change_direction_enum_values` | `MaturityChangeDirectionEnum` a exactement 2 valeurs `{upgrade, downgrade}` |
| 8 | `test_router.py` | `test_endpoints_return_501_authenticated` | fixture `authenticated_client` → 3 endpoints (`POST /declare`, `GET /formalization-plan`, `GET /levels`) → 501 + message contient `"Epic 12"` |
| 9 | `test_router.py` | `test_endpoints_return_401_without_auth` | Sans header `Authorization` → 3 endpoints → 401 (prime sur 501 — FastAPI résout `Depends(get_current_user)` avant raise) |
| 10 | `test_router.py` | `test_openapi_documents_501_responses` | `/openapi.json` contient `responses.501` pour chaque endpoint `/api/maturity/*` |
| 11 | `test_service.py` | `test_all_5_service_functions_raise_not_implemented` | Invocation des 5 fonctions service → `NotImplementedError` avec message contenant `"Story 10.3 skeleton"` et `"Epic 12"` (table-driven via `pytest.mark.parametrize`) |
| 12 | `test_maturity_tools.py` | `test_declare_maturity_level_is_wrapped_with_retry` | `MATURITY_TOOLS[0]._is_wrapped_by_with_retry is True` (enforcement CQ-11) + `node_name == "maturity"` |
| 13 | `test_maturity_tools.py` | `test_declare_maturity_level_returns_skeleton_message` | Invocation avec mock `RunnableConfig` → retour contient `"non encore implémenté"` ET `"Epic 12"` |
| 14 | `test_graph/test_maturity_node_registered.py` | `test_maturity_node_registered_in_graph_but_not_routable` | `compiled_graph.nodes` contient `"maturity"` ET `"maturity_tools"` **AND** `_route_after_router` appelé avec messages arbitraires ne retourne jamais `"maturity"` (smoke test AC5 non-atteignabilité) |
| 15 (bonus) | `test_formalization_plan_calculator.py` | `test_country_data_driven_no_hardcoded_country_strings` | Scan du fichier `formalization_plan_calculator.py` **et** `service.py` via `pathlib.Path.read_text()` + assert aucune des chaînes `"Sénégal"`, `"Côte d'Ivoire"`, `"Mali"`, `"Burkina Faso"`, `"Niger"`, `"Togo"`, `"Bénin"` n'apparaît (AC6 Epic 10.3 country-data-driven — **piège critique Epic 12 à prévenir dès le squelette**) |
| 16 (bonus) | `test_formalization_plan_calculator.py` | `test_generate_raises_not_implemented` | `FormalizationPlanCalculator().generate(...)` raise `NotImplementedError` avec message contenant `"Story 10.3 skeleton"` et `"Epic 12 story 12.3"` |

**And** la baseline passe de **1283** tests verts (post-10.2) à **≥ 1297** tests verts (strictement +14 minimum) sans flakiness sur 3 runs consécutifs.
**And** coverage `backend/app/modules/maturity/` **≥ 80 %** (NFR60 CI gate — service stubs comptent car `NotImplementedError` est l'unique ligne du corps, exécutée par les tests d'assertion d'exception).
**And** le scan `test_no_tool_escapes_wrapping` de `backend/tests/test_graph/test_tools_instrumentation.py` est **étendu à `maturity_tools`** pour détecter automatiquement tout futur tool non-wrappé (leçon 10.2 — défense anti-régression identique).

---

## Tasks / Subtasks

### Phase 1 — Squelette module + modèles ORM (AC1, AC2)

- [ ] **Task 1 — Créer `backend/app/modules/maturity/` + 8 fichiers squelettes** (AC: 1)
  - [ ] 1.1 `__init__.py` (docstring 1 ligne « Module Maturity : Cluster A' maturité administrative graduée (FR11–FR16). »)
  - [ ] 1.2 `enums.py` : `MaturityWorkflowStateEnum(str, Enum)` 3 valeurs `{draft, review_requested, published}` + `MaturityChangeDirectionEnum(str, Enum)` 2 valeurs `{upgrade, downgrade}` — **source unique** réutilisée par `models.py`, `schemas.py`, `router.py`, `service.py`
  - [ ] 1.3 `events.py` : 3 constantes `MATURITY_LEVEL_UPGRADED_EVENT_TYPE: Literal["maturity.level_upgraded"]`, `MATURITY_LEVEL_DOWNGRADED_EVENT_TYPE: Literal["maturity.level_downgraded"]`, `FORMALIZATION_PLAN_GENERATED_EVENT_TYPE: Literal["maturity.formalization_plan_generated"]` + docstring payload schema prévu Epic 12
  - [ ] 1.4 `formalization_plan_calculator.py` : classe `FormalizationPlanCalculator` avec méthode unique `generate()` raising `NotImplementedError` (AC7)
  - [ ] 1.5 Vérifier import circulaire : `from app.modules.maturity import router, service, schemas, models, enums, events, formalization_plan_calculator` passe sans warning (vérifier via `python -c`)

- [ ] **Task 2 — Écrire `models.py` (3 modèles ORM mappés sur migration 021)** (AC: 2)
  - [ ] 2.1 `AdminMaturityLevel` avec `level INT CHECK 1–5`, `code UNIQUE`, `level UNIQUE`, `workflow_state String(16) DEFAULT 'draft'`, `is_published Boolean DEFAULT false`, colonnes SOURCE-TRACKING `source_url/source_accessed_at/source_version`, `UUIDMixin + TimestampMixin`
  - [ ] 2.2 `FormalizationPlan` avec FK `company_id ON DELETE CASCADE`, FK `current_level_id/target_level_id ON DELETE SET NULL nullable`, `actions_json` via `_jsonb()`, `status String(32) DEFAULT 'draft'`, index `ix_formalization_plans_company_id` (déclaré via `__table_args__`)
  - [ ] 2.3 `AdminMaturityRequirement` avec FK `level_id ON DELETE RESTRICT NOT NULL`, `requirements_json NOT NULL via _jsonb()`, UNIQUE `(country, level_id)` via `__table_args__ = (UniqueConstraint(..., name="uq_maturity_country_level"),)`
  - [ ] 2.4 Helper `_jsonb()` local identique à `projects/models.py:46-48` (dupliqué pour auto-suffisance du module)
  - [ ] 2.5 Enregistrement dans `app/models/__init__.py` via `from app.modules.maturity.models import AdminMaturityLevel, FormalizationPlan, AdminMaturityRequirement  # noqa: F401`
  - [ ] 2.6 `Base.metadata.create_all` SQLite crée les 3 tables — test CRUD passe

### Phase 2 — Router stubs + service (AC3, AC6)

- [ ] **Task 3 — Créer `schemas.py` (Pydantic v2)** (AC: 1, 3)
  - [ ] 3.1 Re-export `MaturityWorkflowStateEnum`, `MaturityChangeDirectionEnum` depuis `enums.py`
  - [ ] 3.2 `MaturityLevelDeclaration(level: str = Field(min_length=1, max_length=32))` pour `POST /declare`
  - [ ] 3.3 `MaturityLevelResponse` avec `ConfigDict(from_attributes=True)` + tous les champs de `AdminMaturityLevel`
  - [ ] 3.4 `FormalizationPlanStep(step: str, cost_xof: int | None, duration_days: int | None, coordinates: dict | None)` — structure validée Epic 12.3 AC1
  - [ ] 3.5 `FormalizationPlanResponse(id, company_id, status, current_level_id, target_level_id, steps: list[FormalizationPlanStep])`
  - [ ] 3.6 `AdminMaturityRequirementResponse(id, country, level_id, requirements_json, is_published)`

- [ ] **Task 4 — Créer `router.py` (3 endpoints + 501 stub)** (AC: 3)
  - [ ] 4.1 `POST /declare` → 501
  - [ ] 4.2 `GET /formalization-plan` → 501
  - [ ] 4.3 `GET /levels` → 501
  - [ ] 4.4 `responses={501: {...}}` documenté sur chaque endpoint
  - [ ] 4.5 Enregistrement dans `app/main.py` entre `projects_router` et `esg_router` (ordre alpha cluster A → A')

- [ ] **Task 5 — Créer `service.py` (5 fonctions stubs)** (AC: 6)
  - [ ] 5.1 5 signatures typées exactes (`declare_maturity_level`, `get_formalization_plan`, `list_published_levels`, `get_requirements_for_country_level`, `create_formalization_plan`)
  - [ ] 5.2 Corps `NotImplementedError("Story 10.3 skeleton — implemented in Epic 12 story 12-X")`
  - [ ] 5.3 Docstring par fonction + référence au story Epic 12 cible (12.1/12.2/12.3/12.5)
  - [ ] 5.4 `get_requirements_for_country_level(country: str, level_id: UUID)` documentée comme **point d'entrée data-driven FR13** — rappel explicite anti-hardcoding pays dans docstring

### Phase 3 — Tools LangChain + maturity_node + FormalizationPlanCalculator stub (AC4, AC5, AC7)

- [ ] **Task 6 — Créer `backend/app/graph/tools/maturity_tools.py`** (AC: 4)
  - [ ] 6.1 Imports `with_retry`, `@tool`, `RunnableConfig`
  - [ ] 6.2 `@tool async def declare_maturity_level(level: str, config: RunnableConfig | None = None) -> str`
  - [ ] 6.3 Corps `return "Module maturity non encore implémenté (Epic 12)."` (stub sans raise)
  - [ ] 6.4 `MATURITY_TOOLS = [with_retry(declare_maturity_level, max_retries=2, node_name="maturity")]`
  - [ ] 6.5 Enregistrement dans `app/graph/tools/__init__.py` (entre `PROJECTS_TOOLS` et `ESG_TOOLS` dans `INSTRUMENTED_TOOLS`, ajouté à `__all__`)
  - [ ] 6.6 README mis à jour (compteur 36 tools + ligne tableau `| maturity_tools.py | maturity | declare_maturity_level |`)

- [ ] **Task 7 — Créer `maturity_node` dans `backend/app/graph/nodes.py`** (AC: 5)
  - [ ] 7.1 `async def maturity_node` **juste après `project_node`** (ligne ~1318 actuelle)
  - [ ] 7.2 Corps : AIMessage + pose `active_module="maturity"` + `active_module_data={"node_visited": True}`
  - [ ] 7.3 Pas de `get_llm()` ni `bind_tools` (rationale doc dans docstring — référence 10.2 précédente)

- [ ] **Task 8 — Brancher `maturity_node` dans `graph.py`** (AC: 5)
  - [ ] 8.1 Import `maturity_node` (ordre alpha dans la liste)
  - [ ] 8.2 Import `MATURITY_TOOLS` dans `build_graph` (après `PROJECTS_TOOLS`)
  - [ ] 8.3 `create_tool_loop(graph, "maturity", maturity_node, tools=MATURITY_TOOLS + INTERACTIVE_TOOLS + GUIDED_TOUR_TOOLS)` immédiatement après l'appel `project` (ligne ~153)
  - [ ] 8.4 Pas d'entrée dans `_route_after_router` ni `conditional_edges`
  - [ ] 8.5 Docstring `build_graph` mise à jour (ajouter bloc Story 10.3 analogique au bloc Story 10.2)

- [ ] **Task 9 — `formalization_plan_calculator.py` stub** (AC: 7)
  - [ ] 9.1 Classe `FormalizationPlanCalculator` < 30 lignes
  - [ ] 9.2 Méthode `async def generate(...)` avec signature exacte AC7
  - [ ] 9.3 Corps raise `NotImplementedError("Story 10.3 skeleton — FormalizationPlanCalculator.generate delivered in Epic 12 story 12.3")`
  - [ ] 9.4 Docstring : rappel country-data-driven + référence FR13 + reference `AdminMaturityRequirement.requirements_json`

### Phase 4 — Tests + validation (AC8)

- [ ] **Task 10 — Créer `backend/tests/test_maturity/`** (AC: 8)
  - [ ] 10.1 `__init__.py` + `conftest.py` (fixture `authenticated_client` réutilisée depuis `tests/test_projects/conftest.py` ou factorisée dans `tests/conftest.py` global — **ne pas dupliquer**)
  - [ ] 10.2 `test_models.py` — 7 tests (CRUD, unique code/level, CHECK postgres-only, FK cascade, unique country/level, enum values ×2)
  - [ ] 10.3 `test_router.py` — 3 tests (501 authenticated ×3 endpoints, 401 sans auth ×3 endpoints, OpenAPI doc 501)
  - [ ] 10.4 `test_service.py` — 1 test parametrize 5 fonctions `NotImplementedError`
  - [ ] 10.5 `test_maturity_tools.py` — 2 tests (sentinel `_is_wrapped_by_with_retry` + stub message)
  - [ ] 10.6 `test_formalization_plan_calculator.py` — 2 tests (country-data-driven scan + `generate` raise)
  - [ ] 10.7 `test_graph/test_maturity_node_registered.py` — 1 smoke test (node dans graphe + non-atteignabilité router)
  - [ ] 10.8 Étendre `test_no_tool_escapes_wrapping` dans `test_graph/test_tools_instrumentation.py` pour inclure `maturity_tools` (défense anti-régression)

- [ ] **Task 11 — Validation baseline + coverage**
  - [ ] 11.1 pytest full : baseline pre-10.3 = **1283 passed + 6 skipped** (état post-10.2) ; post-10.3 = **≥ 1297 passed** (strictement +14 minimum) sans flakiness
  - [ ] 11.2 Coverage module maturity ≥ 80 % (NFR60) — pragma `# pragma: no cover` **interdit** sur les stubs (les tests `NotImplementedError` les couvrent)
  - [ ] 11.3 SQLite OK via `JSONB().with_variant(JSON, "sqlite")`
  - [ ] 11.4 PostgreSQL test `test_admin_maturity_level_check_level_between_1_and_5` vert en local avec `docker compose up postgres` (marker `@pytest.mark.postgres`) — pas bloquant CI SQLite-only

- [ ] **Task 12 — Checklist code review self-audit**
  - [ ] 12.1 CQ-6 : 8 fichiers module `maturity/` < 400 lignes (max ~200 lignes pour models.py)
  - [ ] 12.2 CQ-8 : commentaires `# AC1/AC2/.../AC8` dans les fichiers concernés
  - [ ] 12.3 CQ-11 : `MATURITY_TOOLS = [with_retry(...)]` ; aucun `log_tool_call` manuel dans le tool
  - [ ] 12.4 CCC-14 : `events.py` documente payloads Epic 12 sans émission MVP
  - [ ] 12.5 NFR64 : `service.py` expose uniquement les 5 fonctions, aucune logique inline
  - [ ] 12.6 NFR66 country-data-driven : **aucune occurrence** de `"Sénégal"`, `"Côte d'Ivoire"`, `"Mali"`, `"Burkina Faso"`, `"Niger"`, `"Togo"`, `"Bénin"` dans `backend/app/modules/maturity/**/*.py` (scan `grep -r` validé par test 15)

---

## Dev Notes

### Pattern brownfield à répliquer (NE PAS RÉINVENTER)

**Référence absolue** : `backend/app/modules/projects/` (Story 10.2 — review/done).

Le module `modules/projects/` est livré depuis Story 10.2 et établit **exactement** le pattern à dupliquer ici (hors feature flag qui est spécifique à `projects`). Consulter avant de commencer :
- `backend/app/modules/projects/__init__.py` — docstring 1 ligne
- `backend/app/modules/projects/router.py:1-103` — pattern 4 endpoints stubs avec `Depends(get_current_user)` en premier
- `backend/app/modules/projects/service.py:1-92` — signatures `async def xxx(db: AsyncSession, *, ...)`, paramètres **kw-only** après le `*` pour éviter les bugs positionnels
- `backend/app/modules/projects/schemas.py` — Pydantic v2 avec `Field(ge=..., le=...)`, `ConfigDict(from_attributes=True)`
- `backend/app/modules/projects/models.py:46-48` — helper `_jsonb()` cross-dialect (à dupliquer localement dans `maturity/models.py` pour auto-suffisance)
- `backend/app/graph/tools/projects_tools.py:1-45` — pattern `@tool` + `with_retry` + `PROJECTS_TOOLS = [...]`
- `backend/app/graph/nodes.py:1291-1317` — pattern `project_node` sans LLM (à dupliquer pour `maturity_node`)

**Différences maturity vs projects à observer** :
- **Pas de feature flag** — arbitrage Q1 Story 10.1 visait uniquement `ENABLE_PROJECT_MODEL`. Les endpoints `/api/maturity/*` retournent **directement 501** (pas de 404 conditionnel, pas de dependency `check_project_model_enabled` analogue).
- **3 modèles ORM** (vs 6 pour `projects/`) — plus simple : `AdminMaturityLevel`, `FormalizationPlan`, `AdminMaturityRequirement`. Pas de `Company` à ajouter (déjà fait en 10.2 Task 2.4).
- **3 endpoints** (vs 4) — `POST /declare`, `GET /formalization-plan`, `GET /levels`.
- **1 fichier extra** : `formalization_plan_calculator.py` stub (spécifique Cluster A' — préparer le point d'extension Epic 12.3 sans logique).
- **`maturity_node` est 11ᵉ nœud** (vs 10ᵉ pour `project_node`). Respecter l'ordre alpha dans l'import de `graph.py` : `action_plan, application, carbon, chat, credit, document, esg_scoring, financing, maturity, project, router_node`.
- **Country-data-driven** (NFR66) — spécifique au Cluster A' : **zéro string pays hardcodé** dans `service.py` ni `formalization_plan_calculator.py` ni ailleurs du module. Le test 15 scan le code pour le prouver. C'est **la dette que Story 10.3 prévient dès le squelette**.

### Pas de feature flag `ENABLE_MATURITY_MODEL` — CONTEXTE CRITIQUE

**Ne PAS introduire** un nouveau feature flag `ENABLE_MATURITY_MODEL` (piège tentant par mimétisme de Story 10.2) :
1. L'arbitrage Q1 Story 10.1 n'a introduit QU'UN SEUL feature flag (`ENABLE_PROJECT_MODEL`) par souci de parsimonie env var.
2. Le modèle maturité n'a pas la même sensibilité UI : contrairement au modèle `Company × Project` N:N qui doit être masqué tant qu'Epic 11 ne livre, la maturité est un concept admin data-only (le user ne voit rien tant que les endpoints renvoient 501).
3. Story 10.9 (feature flag wrapper complet) couvre UNIQUEMENT `ENABLE_PROJECT_MODEL`. Ajouter `ENABLE_MATURITY_MODEL` obligerait à rouvrir la scope 10.9 → **non**.

**Conséquence concrète Story 10.3** : les 3 endpoints `/api/maturity/*` retournent **directement 501** sans dependency de feature flag. L'ordre des dependencies reste simple : `current_user: User = Depends(get_current_user)` → corps `raise HTTPException(501)`. C'est **401 → 501** (pas de 404 intermédiaire).

### Instrumentation tools — RÈGLE D'OR (retour post-9.7 + 10.2)

**Tout nouveau tool LangChain DOIT être wrappé `with_retry` dès sa création** — leçon appliquée avec succès en 10.2.

Pattern exact à copier depuis `backend/app/graph/tools/projects_tools.py:23-44` :

```python
from app.graph.tools.common import with_retry
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool


@tool
async def declare_maturity_level(
    level: str,
    config: RunnableConfig | None = None,
) -> str:
    """Déclarer le niveau de maturité administrative de l'entreprise (stub Epic 12).

    Args:
        level: Code du niveau (ex. "informel", "rccm_nif", "comptes_cnps", "ohada_audite").
               Validation effective déférée à Epic 12 (match contre AdminMaturityLevel.code).
    Returns:
        Message d'état du squelette (pas de raise — évite crash côté LLM).
    """
    return "Module maturity non encore implémenté (Epic 12)."


MATURITY_TOOLS = [
    with_retry(declare_maturity_level, max_retries=2, node_name="maturity"),
]
```

**⚠️ PIÈGE à éviter (documenté 10.2)** : ne JAMAIS appeler `log_tool_call` manuellement dans le corps d'un tool — `with_retry` s'en charge automatiquement (voir `common.py:_safe_log`). Un appel manuel dupliquerait les lignes dans `tool_call_logs`.

### `maturity_node` minimal — pourquoi pas de LLM ? (rationale 10.2 répliqué)

Contrairement aux 9 nodes actifs qui callent `get_llm()` puis `bind_tools(...)` puis `ainvoke(messages)`, **`maturity_node` ne call pas le LLM** (même comportement que `project_node` 10.2) :

1. **Pas de prompt dédié MVP** : Epic 12 Story 12.1 livrera `backend/app/prompts/maturity.py` avec le prompt système spécialisé. Sans prompt, le LLM hallucinerait.
2. **Pas de routing depuis `router`** : AC5 §5 interdit d'ajouter `"maturity"` dans `_route_after_router`. Le node est créé mais non-atteignable depuis une conversation normale. Le test smoke l'invoque explicitement via `config={"configurable": {"active_module": "maturity"}}`.
3. **Coût baseline CI** : éviter qu'une dépendance cassée `get_llm()` en CI (clé OpenRouter absente) ne casse les tests du squelette.

Le jour où Epic 12 S1 livre le prompt, la fonction `maturity_node` sera **réécrite** pour ressembler à `esg_scoring_node` (`get_llm`, `bind_tools`, `ainvoke`). C'est une réécriture, pas un ajout incrémental — le squelette actuel est jetable.

### CCC-14 Outbox — `events.py` préparation sans émission

`events.py` déclare 3 constantes pour les `event_type` prévus Epic 12 sans les émettre (Story 10.10 livrera le worker APScheduler). Le but : **consommateurs futurs importent depuis une source unique**, évitant le « chaîne de strings hardcodés » qui rendrait le refactor Outbox douloureux.

Payloads prévus (documentation uniquement MVP — insérés dans `domain_events` table par Epic 12) :

```python
# backend/app/modules/maturity/events.py
"""Domain events émis par le module maturity (D11 micro-Outbox).

Story 10.3 — squelette sans émission. Story 10.10 livrera le worker.

Payloads attendus :
- maturity.level_upgraded : {company_id, from_level_code, to_level_code, actor_id, reason}
- maturity.level_downgraded : {company_id, from_level_code, to_level_code, actor_id, reason, justification_text}
- maturity.formalization_plan_generated : {company_id, plan_id, current_level_id, target_level_id, step_count}
"""
from typing import Final, Literal

MATURITY_LEVEL_UPGRADED_EVENT_TYPE: Final[Literal["maturity.level_upgraded"]] = "maturity.level_upgraded"
MATURITY_LEVEL_DOWNGRADED_EVENT_TYPE: Final[Literal["maturity.level_downgraded"]] = "maturity.level_downgraded"
FORMALIZATION_PLAN_GENERATED_EVENT_TYPE: Final[Literal["maturity.formalization_plan_generated"]] = "maturity.formalization_plan_generated"
```

### Country-data-driven (NFR66) — LA DETTE QUE CETTE STORY PRÉVIENT

Le Cluster A' (FR11–FR16) est particulièrement sensible au **hardcoding pays** (risque Epic 12.3 FormalizationPlanCalculator) :
- **Bonne pratique** : toute lecture de requirements passe par `service.get_requirements_for_country_level(db, country=company.country, level_id=...)` qui lit `AdminMaturityRequirement.requirements_json` en base.
- **Mauvaise pratique** (à prévenir dès Story 10.3) : `if country == "Sénégal": steps = [{...RCCM...}]` en dur dans le code Python.

**Pourquoi prévenir dès le squelette ?** Si Story 10.3 livre une version « provisoire » avec 2–3 lignes hardcodées « juste pour tester », Epic 12.3 héritera de la dette et devra re-factorer. Le test 15 (scan grep sur noms de pays UEMOA/CEDEAO) **échoue dès qu'un contributeur ajoute `"Sénégal"` en string** → CI red = feedback immédiat.

**Pays à bannir du scan** (liste NFR66 UEMOA + quelques extensions CEDEAO francophones fréquentes) :
```python
# tests/test_maturity/test_formalization_plan_calculator.py
_BANNED_COUNTRY_STRINGS = [
    "Sénégal", "Senegal",
    "Côte d'Ivoire", "Cote d'Ivoire", "Ivory Coast",
    "Mali", "Burkina Faso", "Niger", "Togo", "Bénin", "Benin",
    "Guinée", "Guinee", "Guinea",
]
```

Le scan accepte `country` paramètre (variable) mais rejette les string literals. Implémentation du test : lire le fichier `.read_text()`, `for banned in _BANNED_COUNTRY_STRINGS: assert banned not in content`.

### Cohérence avec RLS (Story 10.5 à venir)

Les 3 tables `admin_maturity_levels`, `formalization_plans`, `admin_maturity_requirements` ne sont **PAS dans la liste Story 10.5** (qui cible `companies`, `fund_applications`, `facts`, `documents`). L'isolation tenant sur `formalization_plans` vient indirectement via `companies.owner_user_id` (FK `company_id` côté `formalization_plans`). Les tables admin (`admin_maturity_levels`, `admin_maturity_requirements`) sont globales (pas de tenant) — publiées uniquement (`is_published=true`) côté user, CRUD réservé à `admin_mefali` (Story 10.4 admin_catalogue + Story 10.12 audit trail).

### SOURCE-TRACKING (NFR27) — colonnes préservées, enforcement déféré

Les colonnes `source_url`, `source_accessed_at`, `source_version` existent sur `admin_maturity_levels` et `admin_maturity_requirements` (migration 021 lignes 54-56 et 136-138). Elles sont **nullable** pour l'instant — les contraintes `CHECK (source_url IS NOT NULL OR workflow_state = 'draft')` seront ajoutées par migration 025 consommée par Story 10.11. Ne pas ajouter ces CHECK prématurément dans cette story.

### Previous Story Intelligence

**Story 10.2** (review/done 2026-04-20) : pattern `projects/` établi. **Dupliquer**, ne pas réinventer. Leçons appliquées :
- Helper `_jsonb()` local dans chaque `models.py` (pas dans un `core/db.py` commun — choix architectural 10.2 validé).
- Modèle `Company` minimal déjà ajouté par 10.2 → **ne pas re-créer** dans 10.3.
- Ordre des dependencies : `current_user` avant autre dependency → 401 prime.
- Test sentinelle `_is_wrapped_by_with_retry` + scan `test_no_tool_escapes_wrapping` — défenses anti-régression à reproduire.
- Stubs `NotImplementedError` avec message explicite « Story 10.3 skeleton — implemented in Epic 12 story 12-X ».

**Story 10.1** (done 2026-04-20) : migration 021 crée `admin_maturity_levels`, `formalization_plans`, `admin_maturity_requirements` avec exactement les colonnes documentées AC2. Ne pas dupliquer le schéma — les modèles ORM 10.3 se mappent **exactement** sur ce qui existe en base. Si un champ manque (rare), **NE PAS** créer de migration 028 — ouvrir un défer dans `deferred-work.md` et faire arbitrer par le PM (leçon 10.2).

**Story 9.7** (done 2026-04-20) : `with_retry` + `log_tool_call` livrés. **Ne jamais appeler `log_tool_call` directement** dans un tool — laisser `with_retry` s'en charger (AC4).

### Git Intelligence (5 derniers commits)

```
06bcf99  9-5/9-6/9-7 ship (observabilité tools) 
92f36f5  idem
94ee7e5  Story 9.4 OCR bilingue
39006a8  Stories 9.1/9.2/9.3
99f2fb4  /bmad-document-project
```

**Pattern squash-merge** : chaque story est squash-mergée avec message `<story-key>: done`. Pour Story 10.3, prévoir un commit final `10-3-module-maturity-squelette: done` après validation code review.

**Commits incrémentaux recommandés** :
1. `10-3: models.py + enums + events + register in app/models/__init__.py`
2. `10-3: schemas.py + router stubs 501`
3. `10-3: service.py stubs + formalization_plan_calculator.py stub`
4. `10-3: maturity_tools.py + register in INSTRUMENTED_TOOLS`
5. `10-3: maturity_node + graph.py registration`
6. `10-3: tests 14 green + country-data-driven scan + coverage ≥ 80%`
7. (squash au merge)

### Latest Tech Info (Pydantic v2, SQLAlchemy 2.x, LangChain ≥ 0.3, FastAPI)

- **Pydantic v2** : `model_config = ConfigDict(from_attributes=True)`. `Field(ge=..., le=..., min_length=..., max_length=...)`. `Literal["maturity.level_upgraded"]` pour les event types (events.py).
- **SQLAlchemy 2.0** : `Mapped[...]` + `mapped_column(...)` (pas `Column()` legacy). `UUID(as_uuid=True)` depuis `sqlalchemy.dialects.postgresql`. `JSONB().with_variant(JSON(), "sqlite")` pour cross-dialect. `__table_args__ = (UniqueConstraint(..., name="uq_..."),)` pour les contraintes nommées (migration nommage `uq_maturity_country_level` à respecter).
- **FastAPI** : `Depends(...)` résolu dans l'ordre déclaré. Pour 401 before 501 : placer `current_user: User = Depends(get_current_user)` AVANT `raise HTTPException(501)` (test 9 AC8 vérifie).
- **LangGraph / LangChain ≥ 0.3** : `@tool` décorateur depuis `langchain_core.tools`. `ToolNode` depuis `langgraph.prebuilt`. `RunnableConfig` depuis `langchain_core.runnables`. Pattern `bind_tools` : Epic 12 l'implémentera dans `maturity_node`, pas ici.

### Project Structure Notes

**Alignment avec unified project structure (CLAUDE.md + architecture.md §ligne 930, 1146)** :
- ✅ `backend/app/modules/maturity/` respecte pattern NFR62 `modules/<domain>/{router,service,schemas,models}.py`
- ✅ `enums.py` + `events.py` + `formalization_plan_calculator.py` extensions cohérentes avec architecture.md §«Organisation des 3 nouveaux modules» + §«Modules » ligne 1146 (`ocr_validator.py` et `formalization_plan_generator.py` listés Epic 12 — squelette livre uniquement `formalization_plan_calculator.py` renommé pour cohérence epic-10.md AC1 : `formalization_plan_calculator.py` **et non** `formalization_plan_generator.py` ; l'epic-10.md **est la source de vérité** pour le squelette, Epic 12 alignera si renommage nécessaire)
- ✅ Tests dans `backend/tests/test_maturity/` (convention nommage fichiers internes `test_<module>_<aspect>.py`)
- ✅ Pas de nouveau feature flag (Clarification documentée Dev Notes)

**Variances détectées** (documentées, acceptées) :
- **`maturity_node` sans LLM** — divergence intentionnelle avec les 9 nodes actifs (voir Dev Notes). Sera aligné Epic 12 Story 12.1.
- **`service.py` 100 % `NotImplementedError`** — divergence avec `modules/esg/service.py`. Intentionnel : squelette. Epic 12 comblera.
- **Pas de feature flag** — divergence avec Story 10.2 qui a introduit `ENABLE_PROJECT_MODEL`. Intentionnel (arbitrage Q1 10.1 + scope 10.9 limitée).
- **Nommage `formalization_plan_calculator.py`** — source de vérité `epic-10.md` AC1 Story 10.3. L'architecture.md ligne 1146 mentionne `formalization_plan_generator.py` ; divergence à lever par le PM lors de la livraison Epic 12 Story 12.3 (**non bloquant squelette** — aligner le nom sera un rename trivial).

---

## References

- [Source: _bmad-output/planning-artifacts/epics/epic-10.md#story-103] — AC1–AC6 originaux
- [Source: _bmad-output/planning-artifacts/epics/epic-12.md] — Cluster A' Epic 12 consommateur (FR11–FR16)
- [Source: _bmad-output/planning-artifacts/epics/epic-12.md#story-121] — `POST /api/maturity/declare` AC1 (Epic 12 Story 12.1)
- [Source: _bmad-output/planning-artifacts/epics/epic-12.md#story-123] — `GET /api/maturity/formalization-plan` AC1 + country-data-driven (Epic 12 Story 12.3)
- [Source: _bmad-output/planning-artifacts/architecture.md#ligne-46] — Maturité administrative FR11–FR16
- [Source: _bmad-output/planning-artifacts/architecture.md#ligne-272] — `maturity_node` description (self-declaration + OCR + FormalizationPlan + auto-reclassement)
- [Source: _bmad-output/planning-artifacts/architecture.md#ligne-930] — `backend/app/modules/maturity/` structure
- [Source: _bmad-output/planning-artifacts/architecture.md#ligne-1146] — Modules structure `maturity/` (router + service + schemas + models)
- [Source: _bmad-output/implementation-artifacts/10-1-migrations-alembic-020-027.md] — Story 10.1 (done, migration 021)
- [Source: _bmad-output/implementation-artifacts/10-2-module-projects-squelette.md] — Story 10.2 (review/done, pattern de référence)
- [Source: backend/alembic/versions/021_create_maturity_schema.py] — Schéma SQL des 3 tables à mapper en ORM
- [Source: backend/app/graph/tools/common.py] — `with_retry` + `log_tool_call` (Story 9.7)
- [Source: backend/app/modules/projects/router.py] — Pattern router à dupliquer (minus feature flag)
- [Source: backend/app/modules/projects/service.py] — Pattern service (signatures kw-only après `*`)
- [Source: backend/app/modules/projects/models.py:46-48] — Helper `_jsonb()` cross-dialect
- [Source: backend/app/graph/tools/projects_tools.py:1-45] — Pattern `@tool` + `with_retry` + `TOOLS = [...]`
- [Source: backend/app/graph/graph.py:113-153] — `create_tool_loop` + registration pattern Story 10.2
- [Source: backend/app/graph/nodes.py:1291-1317] — `project_node` référence (à dupliquer pour `maturity_node`)
- [Source: backend/app/graph/tools/__init__.py] — Enregistrement `INSTRUMENTED_TOOLS` + `__all__`
- [Source: backend/app/graph/tools/README.md] — Guide ajout tool (§2 Pattern)
- [Source: CLAUDE.md#conventions-de-developpement] — NFR62 structure modules, snake_case Python
- [Source: backend/app/models/__init__.py] — Registration globale modèles SQLAlchemy
- [Source: backend/tests/test_graph/test_tools_instrumentation.py] — Scan `test_no_tool_escapes_wrapping` à étendre
- [Source: backend/tests/test_projects/] — Suite de tests à dupliquer structurellement

---

## Dev Agent Record

### Agent Model Used

claude-opus-4-7[1m] (Opus 4.7, 1M context)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed — comprehensive developer guide created pour Story 10.3 (squelette `maturity/` + `maturity_node` 11ᵉ nœud + `maturity_tools.py` + `formalization_plan_calculator.py` stub).

### File List

**À créer** (attendus) :
- `backend/app/modules/maturity/__init__.py`
- `backend/app/modules/maturity/enums.py`
- `backend/app/modules/maturity/events.py`
- `backend/app/modules/maturity/models.py` (3 modèles ORM)
- `backend/app/modules/maturity/schemas.py`
- `backend/app/modules/maturity/service.py`
- `backend/app/modules/maturity/router.py`
- `backend/app/modules/maturity/formalization_plan_calculator.py` (stub classe + méthode `generate()`)
- `backend/app/graph/tools/maturity_tools.py`
- `backend/tests/test_maturity/__init__.py`
- `backend/tests/test_maturity/conftest.py` (fixture `authenticated_client` réutilisée/factorisée)
- `backend/tests/test_maturity/test_models.py`
- `backend/tests/test_maturity/test_router.py`
- `backend/tests/test_maturity/test_service.py`
- `backend/tests/test_maturity/test_maturity_tools.py`
- `backend/tests/test_maturity/test_formalization_plan_calculator.py`
- `backend/tests/test_graph/test_maturity_node_registered.py`

**À modifier** (attendus) :
- `backend/app/models/__init__.py` (enregistrement des 3 modèles maturity)
- `backend/app/main.py` (include_router `maturity_router` entre `projects_router` et `esg_router`)
- `backend/app/graph/nodes.py` (ajout `maturity_node` après `project_node`)
- `backend/app/graph/graph.py` (import + `create_tool_loop("maturity", ...)` + docstring)
- `backend/app/graph/tools/__init__.py` (import + `MATURITY_TOOLS` dans `INSTRUMENTED_TOOLS` entre PROJECTS et ESG + `__all__`)
- `backend/app/graph/tools/README.md` (tableau inventaire + compteur 36 tools)
- `backend/tests/test_graph/test_tools_instrumentation.py` (scan anti-régression étendu à `maturity_tools`)

### Change Log

| Date | Type | Description |
|------|------|-------------|
| 2026-04-20 | spec | Story 10.3 — fiche comprehensive rédigée (AC1-AC8 + 12 tasks + dev notes pattern brownfield 10.2 + garde-fou country-data-driven NFR66). |
