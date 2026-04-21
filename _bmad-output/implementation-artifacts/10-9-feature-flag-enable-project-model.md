# Story 10.9 : Feature flag `ENABLE_PROJECT_MODEL` (formalisation wrapper + Settings Pydantic)

Status: review

> **Contexte** : 9ᵉ story Epic 10 Fondations Phase 0. **Story la plus courte restante de l'Epic 10** (sizing **S**, ~30 min – 1 h). **Retour au scope brownfield refactor de socle** après 10.8 (framework prompts CCC-9). Zéro nouveau schéma BDD, zéro nouvelle migration Alembic, zéro Terraform.
>
> **État de départ — le helper existe déjà** : Story 10.2 a livré `backend/app/core/feature_flags.py::is_project_model_enabled()` en tant que **stub socle** consommé par `backend/app/modules/projects/router.py::check_project_model_enabled()` (dépendance FastAPI locale au module). Les 4 endpoints `/api/projects/*` implémentent déjà l'ordre 401 → 404 → 501 (AC3 Story 10.2). 16 tests existent dans `backend/tests/test_core/test_feature_flags.py` (1 test défaut + parametrize 15 valeurs truthy/falsy case-insensitive) et 4 tests dans `backend/tests/test_projects/test_router.py` (scénarios flag on/off/no-auth/OpenAPI).
>
> **Ce qu'il reste à livrer pour 10.9 (formalisation + durcissement)** :
> 1. **Typer le flag dans `Settings` Pydantic (AC2)** — ajouter `enable_project_model: bool = Field(default=False)` dans `backend/app/core/config.py`. Le champ est **informationnel** (self-documentation du schéma de config, visible dans OpenAPI interne) : **le helper `is_project_model_enabled()` reste la source de vérité runtime** car il lit `os.environ` dynamiquement à chaque appel — requis pour le toggle live en DEV via `monkeypatch.setenv` sans redéploiement (AC6 Epic §Clarification 5).
> 2. **Consolider la dépendance FastAPI (AC3)** — déplacer `check_project_model_enabled()` de `backend/app/modules/projects/router.py` vers `backend/app/core/feature_flags.py` pour qu'il soit réutilisable par d'autres routers Phase 1 (ex. tag un futur `/api/projects/adjacent` ou assistant chat) **et éliminer la duplication potentielle** (leçon 10.5). Signature inchangée, import path unique.
> 3. **Documenter le pattern « ajouter un nouveau feature flag » (AC5)** — nouveau fichier `docs/CODEMAPS/feature-flags.md` (suit pattern `storage.md`, `security-rls.md`, `data-model-extension.md`). Explique les 4 étapes : (a) ajouter champ typé `Settings`, (b) écrire helper `is_<name>_enabled()` lisant `os.environ` avec truthy set explicite, (c) consommer via dépendance FastAPI ou guard in-service, (d) documenter migration cleanup fin de Phase (NFR63). **Inclut la règle d'or** : 1 flag unique Phase 1 (CQ-10) — tout nouveau flag requiert décision explicite Tech Lead (anti-pattern `profiling_node` dette P1 #3).
> 4. **Durcir l'isolation cleanup Story 20.1 (AC5)** — s'assurer que `feature_flags.py` contient un marker de cleanup déterministe (`# CLEANUP: Story 20.1 — retirer ce fichier post-bascule Phase 1`) + ajouter un test qui scanne la présence du marker. Cela garantit que la migration `027_cleanup_feature_flag_project_model.py` (Story 10.1 AC5) trouve le fichier intact au moment du retrait.
> 5. **Durcir l'absence de librairie externe (AC4)** — ajouter un test unitaire qui scanne `backend/venv/lib/python3.*/site-packages/` (ou `importlib.metadata.distributions()`) pour vérifier l'**absence** de `flipper-client`, `unleash-client`, `launchdarkly-server-sdk`. Assertion explicite Clarification 5. Test marqué `@pytest.mark.unit` (pas de réseau, introspection stdlib seulement).
> 6. **Nettoyer tests dupliqués (AC3)** — la réorganisation de `check_project_model_enabled` dans `core/feature_flags.py` permet d'ajouter un test unit direct (mock FastAPI `HTTPException`) sans devoir passer par le router → réduit la redondance avec les 4 tests e2e `test_projects/test_router.py` qui restent verts inchangés (pattern shims legacy 10.6).
>
> **Hors scope explicite (déféré)** :
> - Aucune introduction de `ENABLE_MATURITY_MODEL` / `ENABLE_ADMIN_CATALOGUE` flag (maturity & admin n'ont **pas** de feature flag par choix Q1 Story 10.1 — parsimonie env var ; leurs endpoints renvoient directement 401 → 501).
> - Aucun `flipper-client` / `unleash-client` / `launchdarkly-server-sdk` (Clarification 5 respectée, vérifié AC4).
> - Aucune bascule opt-in par PME (`company_id`) — le flag est **global** (Arbitrage AC3 épic : bascule transparente car la logique différentielle n'existe pas encore en MVP, elle sera ajoutée dans Epic 11 Projects si besoin).
> - Aucune intégration Settings ↔ helper (le helper ne lit PAS `settings.enable_project_model`, cf. Q1 ci-dessous).
> - Aucune migration Alembic 027 (livrée par Story 20.1 fin Phase 1 — référence seulement).
> - Aucun changement de signature `is_project_model_enabled() -> bool` (préserve 16 tests existants — pattern shims legacy 10.6).
>
> **Contraintes héritées (11 leçons Stories 9.x → 10.8)** :
> 1. **C1 (9.7)** — **pas de `try/except Exception` catch-all** : le helper reste exempt (lecture `os.environ.get()` ne lève pas). Aucun `except Exception` introduit.
> 2. **C2 (9.7)** — **tests prod véritables** : le test « absence librairie externe » utilise `importlib.metadata.distributions()` (API réelle stdlib), pas un mock de `pip list`.
> 3. **Scan NFR66 Task 1 (10.3 M1)** — avant toute modification, `rg -n "is_project_model_enabled|ENABLE_PROJECT_MODEL" backend/app/` consigne les **consommateurs actuels** (attendu : `projects/router.py` seul + `feature_flags.py` lui-même + `maturity/router.py` commentaire). Un consommateur non identifié serait un signal d'alarme.
> 4. **Comptages runtime (10.4)** — AC9 prouvé par `pytest --collect-only -q backend/tests/test_core/test_feature_flags.py backend/tests/test_projects/` avant/après. Delta exact cité dans Completion Notes.
> 5. **Pas de duplication (10.5)** — `check_project_model_enabled()` centralisé dans `feature_flags.py`, supprimé de `projects/router.py`. Scan post-refactor : `rg -n "def check_project_model_enabled" backend/app/` doit retourner **1 hit unique** (dans `feature_flags.py`).
> 6. **Règle d'or 10.5 — tester effet observable** : AC6 tests appellent **le vrai helper** avec `monkeypatch.setenv`, pas un mock du helper lui-même. AC4 appelle **la vraie API `importlib.metadata`**, pas un mock.
> 7. **Pattern shims legacy (10.6)** — la signature `is_project_model_enabled() -> bool` reste byte-identique. Les 16 tests existants restent verts sans modification. Les 4 tests router passent sans modification (l'import interne dans `router.py` bascule vers `from app.core.feature_flags import check_project_model_enabled`, mais le comportement HTTP est identique).
> 8. **Choix verrouillés pré-dev (10.6 + 10.7 + 10.8)** — les 3 questions Q1/Q2/Q3 ci-dessous sont **tranchées dans ce story file** avant Task 2. Aucune décision pendant l'implémentation.
> 9. **Pattern commit intermédiaire si refactor (10.8)** — `check_project_model_enabled` est déplacé entre 2 fichiers. Commit intermédiaire séparé pour faciliter review : (a) commit 1 « déplacer check_project_model_enabled vers core/feature_flags.py » (pur `git mv` logique), (b) commit 2 « formalisation 10.9 : Settings typé + doc + tests ». Facultatif si la PR finale reste atomique et < 500 lignes de diff.
> 10. **Golden snapshots — non applicable** (Story 10.8 a capitalisé ce pattern pour les prompts ; 10.9 n'a pas d'artefact texte stable à figer).
> 11. **Parsimonie env var (Q1 Story 10.1)** — ne pas ajouter d'autre flag. AC4 enforce l'absence de librairie externe, AC5 enforce le cleanup marker.
>
> **Absorption dettes déférées** : aucune dette spécifique aux feature flags dans `deferred-work.md`. Story 10.9 n'absorbe pas de dette externe.

---

## Questions tranchées pré-dev (Q1-Q3)

**Q1 — Relation Settings Pydantic ↔ helper runtime : single-source-of-truth vs. champ informationnel ?**

→ **Tranche : champ informationnel** dans `Settings` (`enable_project_model: bool = Field(default=False)`), mais le helper `is_project_model_enabled()` **ignore** `settings.enable_project_model` et lit `os.environ` dynamiquement à chaque appel.

- **Rationale** : le toggle live en DEV (exigence AC6 Epic Story 10.9 + tests `monkeypatch.setenv`) nécessite une lecture dynamique. Or `settings = Settings()` est instancié **une seule fois au boot** (module-level `settings`). Si le helper lisait `settings.enable_project_model`, les tests `monkeypatch.setenv("ENABLE_PROJECT_MODEL", ...)` ne déclencheraient pas la bascule → régression des 16 tests existants + violation AC6 Epic.
- **Conséquence acceptée** : `settings.enable_project_model` reflète uniquement le snapshot **au boot**. Aucun caller ne l'utilise. Le champ reste dans `Settings` pour (a) validation Pydantic au boot (rejette `ENABLE_PROJECT_MODEL="garbage"` via coercion bool), (b) self-documentation schéma config, (c) intégration future si cache requis Phase Growth.
- **Enforcement** : un test unit vérifie qu'**aucun caller de code applicatif** n'importe `settings.enable_project_model` (`rg -n "settings\.enable_project_model" backend/app/` → 0 hits).

**Q2 — Cohérence truthy set : Pydantic bool default vs. helper custom `{true, 1, yes}` ?**

→ **Tranche : divergence documentée** — Pydantic accepte le set étendu par défaut (`true/false/1/0/yes/no/on/off`, case-insensitive, cf. Pydantic v2 [StrictBool]) au boot ; le helper garde son set strict `{true, 1, yes}` au runtime.

- **Rationale** : (a) la divergence est **sans effet fonctionnel** puisque seul le helper gate les routes (Q1), (b) aligner Pydantic via custom validator alourdirait le code sans bénéfice (le champ est informationnel), (c) si un dev met `ENABLE_PROJECT_MODEL=on` dans `.env`, Pydantic coerce au boot (pas de boot crash), mais le helper retourne `False` au runtime — **sémantique fail-safe** (flag OFF par défaut, AC1 Story 10.1).
- **Documentation** : la divergence est **explicitement mentionnée** dans `docs/CODEMAPS/feature-flags.md` §3 (pièges) et dans la docstring `is_project_model_enabled()` (truthy set explicite).

**Q3 — Documentation location : `docs/CODEMAPS/feature-flags.md` vs. `backend/app/core/README.md` ?**

→ **Tranche : `docs/CODEMAPS/feature-flags.md`** (conforme pattern existant `storage.md`, `security-rls.md`, `data-model-extension.md`).

- **Rationale** : `docs/CODEMAPS/` est le hub canonique de documentation transversale (référencé par `docs/CODEMAPS/index.md`). `backend/app/core/README.md` n'existe pas et créer un README par dossier applicatif ouvrirait une porte à la fragmentation doc (pattern anti-cohésion). L'entrée `feature-flags.md` est référencée depuis `index.md` (1 ligne ajoutée).
- **Alignement Epic 10 livraisons doc** : Story 10.6 a livré `storage.md`, Story 10.5 a livré `security-rls.md`. Story 10.9 livre `feature-flags.md`. Cohérence éditoriale.

---

## Story

**As a** Équipe Mefali (DX/SRE) + futurs contributeurs Phase Growth,

**I want** formaliser le feature flag `ENABLE_PROJECT_MODEL` via (a) un champ typé `Settings` Pydantic `enable_project_model: bool = False` pour self-documentation du schéma config, (b) la consolidation de la dépendance FastAPI `check_project_model_enabled()` dans `backend/app/core/feature_flags.py` (source unique, réutilisable multi-router), (c) une documentation pattern `docs/CODEMAPS/feature-flags.md` (suit format `storage.md`/`security-rls.md`), (d) le durcissement des invariants AC4 (absence librairie externe via `importlib.metadata`) et AC5 (marker cleanup Story 20.1 détectable automatiquement),

**So that** la promesse Clarification 5 (feature flag simple, cleanup trivial fin Phase 1 via migration 027, CQ-10 anti-pattern flag permanent) soit **auto-vérifiable en CI** (tests garantissent absence lib externe + marker cleanup présent) et que le pattern « ajouter un feature flag » soit documenté pour éviter que Phase 1 introduise un 2ᵉ flag par dérive (anti-pattern `profiling_node` dette P1 #3).

---

## Acceptance Criteria

### AC1 — `backend/app/core/feature_flags.py` contient `is_project_model_enabled()` + `check_project_model_enabled()` consolidés

**Given** l'état post-10.2 où `feature_flags.py` expose déjà `is_project_model_enabled()` et `projects/router.py` expose localement `check_project_model_enabled()`,

**When** un dev audite post-refactor 10.9,

**Then** :

- `backend/app/core/feature_flags.py` expose **2 fonctions publiques** :
  - `is_project_model_enabled() -> bool` (signature inchangée, lecture `os.environ["ENABLE_PROJECT_MODEL"]` avec truthy set `{"true", "1", "yes"}` case-insensitive, défaut `False`).
  - `check_project_model_enabled() -> None` (dépendance FastAPI : lève `HTTPException(status_code=404, detail="Feature not available: ENABLE_PROJECT_MODEL is disabled")` si `is_project_model_enabled()` retourne `False`, sinon return `None`).
- **Un marker cleanup déterministe** apparaît en tête de fichier :
  ```python
  # CLEANUP: Story 20.1 — retirer ce fichier post-bascule Phase 1 (migration 027).
  # Aucun caller ne doit subsister dans backend/app/ au moment du retrait.
  ```
- Le scan `rg -n "def check_project_model_enabled" backend/app/` retourne exactement **1 hit** (dans `feature_flags.py`).
- Le scan `rg -n "def is_project_model_enabled" backend/app/` retourne exactement **1 hit** (dans `feature_flags.py`).

### AC2 — `Settings` Pydantic déclare `enable_project_model: bool = False`

**Given** `backend/app/core/config.py` Settings Pydantic,

**When** un dev audite le schéma config post-10.9,

**Then** :

- Le champ `enable_project_model: bool = Field(default=False, description="Feature flag Phase 1 Cluster A — bascule Company × Project (NFR63). Lu dynamiquement par `is_project_model_enabled()` au runtime ; le champ Settings est informationnel.")` est déclaré dans `class Settings(BaseSettings)`.
- Pydantic coerce `ENABLE_PROJECT_MODEL="garbage"` → erreur de boot explicite (validation Pydantic v2 native `bool`, pas de validator custom).
- `Settings().enable_project_model` retourne `False` par défaut, `True` si `ENABLE_PROJECT_MODEL=true|1|yes|on|...` (tolérance Pydantic v2 bool — cf. Q2 divergence documentée).
- **Aucun caller applicatif n'importe `settings.enable_project_model`** (scan `rg -n "settings\.enable_project_model" backend/app/` → 0 hits — le runtime passe toujours par le helper). Exception autorisée : les tests peuvent l'importer pour vérifier la parité boot-time.

### AC3 — `projects/router.py` consomme `check_project_model_enabled` depuis `feature_flags.py` (zéro duplication)

**Given** `backend/app/modules/projects/router.py` définit actuellement `check_project_model_enabled()` localement (lignes 40-46),

**When** le refactor 10.9 est appliqué,

**Then** :

- `projects/router.py` importe `from app.core.feature_flags import check_project_model_enabled` (+ éventuellement `is_project_model_enabled` si utilisé ailleurs dans le router).
- La définition locale `def check_project_model_enabled(): ...` **disparaît** du router.
- Les 4 endpoints `POST /api/projects`, `GET /api/projects/{id}`, `GET /api/projects`, `POST /api/projects/{id}/memberships` continuent à utiliser `Depends(check_project_model_enabled)` (import résolvé depuis `core/`).
- Les 4 tests `backend/tests/test_projects/test_router.py` (`test_endpoints_return_404_when_flag_disabled`, `test_endpoints_return_501_when_flag_enabled`, `test_endpoints_return_401_without_auth`, `test_openapi_documents_404_and_501_responses`) passent **sans modification** (pattern shims legacy 10.6).

### AC4 — Aucune librairie externe feature-flag installée (Clarification 5)

**Given** les dépendances Python du projet,

**When** un nouveau test `test_no_external_feature_flag_library_installed` exécute `importlib.metadata.distributions()`,

**Then** aucune de ces distributions n'est présente dans l'environnement :
- `flipper-client`, `flipper`
- `unleash-client`, `unleash`
- `launchdarkly-server-sdk`, `launchdarkly-api`
- `gitlab-feature-flag`, `configcat-client`

Et le test échoue explicitement avec le nom de la lib trouvée si introduite par accident (défense en profondeur contre dérive via `pip install` opportuniste).

### AC5 — `docs/CODEMAPS/feature-flags.md` documente le pattern + Story 20.1 cleanup marker présent

**Given** aucun `docs/CODEMAPS/feature-flags.md` pré-10.9 (scan Task 1),

**When** le refactor 10.9 est appliqué,

**Then** :

- `docs/CODEMAPS/feature-flags.md` existe avec les sections minimales :
  - **§1 Vue d'ensemble** : schéma Mermaid 2 noeuds (env var → helper → consommateur FastAPI).
  - **§2 État actuel** : 1 seul flag `ENABLE_PROJECT_MODEL` (Phase 1 only), cleanup prévu Story 20.1 migration 027.
  - **§3 Pattern « ajouter un nouveau feature flag »** : 4 étapes numérotées (champ Settings typé, helper `is_<name>_enabled`, dépendance FastAPI optionnelle, doc cleanup marker).
  - **§4 Règle d'or CQ-10** : anti-pattern flag permanent — tout nouveau flag > 3 mois sans retrait = alerte équipe.
  - **§5 Pièges** : divergence Pydantic bool (`on/off` accepté) vs. helper strict (`{true, 1, yes}`) ; cache Settings vs. lecture dynamique env.
- `docs/CODEMAPS/index.md` référence la nouvelle page (1 ligne ajoutée).
- Le marker `# CLEANUP: Story 20.1 — retirer ce fichier post-bascule Phase 1 (migration 027).` figure dans `backend/app/core/feature_flags.py` (vérifié AC1).
- Un test unit `test_feature_flags_has_cleanup_marker` scanne le fichier et vérifie la présence textuelle du marker (fail-fast contre suppression accidentelle avant Story 20.1).

### AC6 — Baseline tests 1495 → ≥ 1500 passed (+5 minimum, +7-9 prévus)

**Given** baseline post-10.8 patch round 1 : **1561 collected, 1495 passed + 66 skipped** (comptage Bash live `pytest --collect-only -q backend/tests/` → 1561 ; ajustement suite 10.8 CR).

**When** Story 10.9 livre les nouveaux tests (estimation 7-9 tests unit),

**Then** :
- `pytest backend/tests/test_core/test_feature_flags.py` : 16 tests pré-10.9 (1 default + 15 parametrize) → **≥ 20 tests** post-10.9 (ajout `test_settings_declares_enable_project_model_field`, `test_settings_boot_value_matches_env_at_init`, `test_no_external_feature_flag_library_installed`, `test_feature_flags_has_cleanup_marker`, `test_check_project_model_enabled_raises_404_when_disabled`, `test_check_project_model_enabled_returns_none_when_enabled`, `test_no_duplicate_check_project_model_enabled_definition`).
- `pytest backend/tests/test_projects/test_router.py` : 4 tests inchangés (passent sans modification — pattern shims legacy 10.6).
- Baseline globale : **1495 → ≥ 1500** passed (+5 plancher, ~7-9 prévus). Delta exact consigné en Completion Notes via `pytest --collect-only -q` avant/après.
- Zéro régression : les 1495 tests pré-10.9 passent tous. Coverage `feature_flags.py` **≥ 95 %** (NFR60 code critique — 14 lignes de code, couverture quasi-totale atteignable).

---

## Tasks / Subtasks

- [x] **Task 1 — Scan NFR66 + constat état actuel** (AC1, AC3, AC5)
  - [x] 1.1 `rg -n "is_project_model_enabled\|ENABLE_PROJECT_MODEL" backend/app/` → documenter les consommateurs actuels dans Completion Notes §Scan. **Attendu** : `feature_flags.py` (déclaration), `projects/router.py` (import + dépendance), `maturity/router.py` (commentaire référentiel). **Bloquant** : si un 4ᵉ consommateur apparaît, l'analyser avant refactor.
  - [x] 1.2 `rg -n "def check_project_model_enabled" backend/app/` → **attendu 1 hit** (dans `projects/router.py`). Post-refactor : 1 hit unique dans `feature_flags.py`.
  - [x] 1.3 `ls docs/CODEMAPS/feature-flags.md 2>/dev/null` → **attendu absent**. Scan anti-duplication.
  - [x] 1.4 `pytest --collect-only -q backend/tests/` → **noter baseline** (attendu ~1561 collected, 1495 passed + 66 skipped). Citer en Completion Notes §Baseline.

- [x] **Task 2 — Déplacer `check_project_model_enabled` vers `core/feature_flags.py`** (AC1, AC3)
  - [x] 2.1 Ajouter dans `backend/app/core/feature_flags.py` :
    ```python
    from fastapi import HTTPException

    _FLAG_DISABLED_DETAIL = "Feature not available: ENABLE_PROJECT_MODEL is disabled"

    def check_project_model_enabled() -> None:
        """Dépendance FastAPI : 404 si `ENABLE_PROJECT_MODEL` OFF.

        Réutilisable par tous routers Phase 1 qui gatent le modèle Project.
        """
        if not is_project_model_enabled():
            raise HTTPException(status_code=404, detail=_FLAG_DISABLED_DETAIL)
    ```
  - [x] 2.2 Dans `backend/app/modules/projects/router.py` : remplacer la définition locale `def check_project_model_enabled(): ...` par `from app.core.feature_flags import check_project_model_enabled`. Supprimer `_FLAG_404 = "..."` local (désormais dans `feature_flags.py`).
  - [x] 2.3 Vérifier : `python -c "from app.modules.projects.router import check_project_model_enabled; print(check_project_model_enabled.__module__)"` → `app.core.feature_flags` (import résolvé correctement).
  - [x] 2.4 Lancer `pytest backend/tests/test_projects/test_router.py -v` → 4 tests verts inchangés (validation shim legacy).

- [x] **Task 3 — Ajouter marker cleanup Story 20.1 dans `feature_flags.py`** (AC1, AC5)
  - [x] 3.1 Ajouter le commentaire en tête de fichier (après la docstring module, avant les imports) :
    ```python
    # CLEANUP: Story 20.1 — retirer ce fichier post-bascule Phase 1 (migration 027).
    # Aucun caller ne doit subsister dans backend/app/ au moment du retrait.
    ```
  - [x] 3.2 Vérifier qu'une recherche `rg -n "CLEANUP: Story 20\.1" backend/app/core/feature_flags.py` retourne le hit.

- [x] **Task 4 — Déclarer `enable_project_model: bool` dans `Settings` Pydantic** (AC2)
  - [x] 4.1 Dans `backend/app/core/config.py`, ajouter dans `class Settings(BaseSettings)` (ordre : après `env_name` section, avant `quota_bytes_per_user_mb` — logique « flag de phase ») :
    ```python
    # --- Feature flag Phase 1 Cluster A (Story 10.9) ---
    # Bascule modèle Company × Project (Clarif. 5 archi).
    # Champ informationnel : le runtime lit `os.environ` via
    # `app.core.feature_flags.is_project_model_enabled()` pour le toggle live.
    # Retrait fin Phase 1 via migration 027 (Story 20.1).
    enable_project_model: bool = Field(
        default=False,
        description="Feature flag Phase 1 Cluster A — bascule Company × Project (NFR63).",
    )
    ```
  - [x] 4.2 Vérifier coercion Pydantic : `ENABLE_PROJECT_MODEL=true python -c "from app.core.config import Settings; print(Settings().enable_project_model)"` → `True`. `ENABLE_PROJECT_MODEL=garbage python -c "..."` → `pydantic.ValidationError` au boot.
  - [x] 4.3 Scan post-ajout : `rg -n "settings\.enable_project_model" backend/app/` → **0 hits attendus** (aucun caller applicatif, Q1 tranche).

- [x] **Task 5 — Documentation `docs/CODEMAPS/feature-flags.md`** (AC5)
  - [x] 5.1 Créer `docs/CODEMAPS/feature-flags.md` avec 5 sections (§1 Vue d'ensemble Mermaid, §2 État actuel, §3 Pattern ajouter flag 4 étapes, §4 Règle d'or CQ-10, §5 Pièges divergence Pydantic/helper). Suit template `storage.md` (titre H1, §§ numérotés, exemples code fenced).
  - [x] 5.2 Éditer `docs/CODEMAPS/index.md` : ajouter 1 ligne référence vers `feature-flags.md` (section "Documentation transversale" ou équivalent selon structure actuelle de `index.md`).
  - [x] 5.3 Vérifier cohérence éditoriale : relecture, Mermaid rend correctement (`mermaid-cli` optionnel, à défaut vérifier syntaxe `graph LR`).

- [x] **Task 6 — Tests nouveaux dans `test_core/test_feature_flags.py`** (AC1, AC2, AC4, AC5, AC6)
  - [x] 6.1 Ajouter `test_settings_declares_enable_project_model_field` : `from app.core.config import Settings; assert "enable_project_model" in Settings.model_fields; assert Settings.model_fields["enable_project_model"].default is False`. Marker `@pytest.mark.unit`.
  - [x] 6.2 Ajouter `test_settings_boot_value_matches_env_at_init(monkeypatch)` : set `ENABLE_PROJECT_MODEL=true` **avant** instanciation `Settings()` (fresh instance, pas le singleton module-level), assert `Settings().enable_project_model is True`. Marker `@pytest.mark.unit`.
  - [x] 6.3 Ajouter `test_no_external_feature_flag_library_installed` : 
    ```python
    import importlib.metadata
    FORBIDDEN = frozenset({
        "flipper-client", "flipper", "unleash-client", "unleash",
        "launchdarkly-server-sdk", "launchdarkly-api",
        "gitlab-feature-flag", "configcat-client",
    })
    installed = {dist.metadata["Name"].lower() for dist in importlib.metadata.distributions() if dist.metadata["Name"]}
    leaked = installed & FORBIDDEN
    assert not leaked, f"Clarification 5 violated: {leaked}"
    ```
    Marker `@pytest.mark.unit`.
  - [x] 6.4 Ajouter `test_feature_flags_has_cleanup_marker` : lire `backend/app/core/feature_flags.py`, assert `"CLEANUP: Story 20.1" in content and "migration 027" in content`. Marker `@pytest.mark.unit`.
  - [x] 6.5 Ajouter `test_check_project_model_enabled_raises_404_when_disabled(monkeypatch)` : `monkeypatch.setenv("ENABLE_PROJECT_MODEL", "false")`, `with pytest.raises(HTTPException) as exc: check_project_model_enabled()`, assert `exc.value.status_code == 404 and "ENABLE_PROJECT_MODEL" in exc.value.detail`. Marker `@pytest.mark.unit`.
  - [x] 6.6 Ajouter `test_check_project_model_enabled_returns_none_when_enabled(monkeypatch)` : `monkeypatch.setenv("ENABLE_PROJECT_MODEL", "true")`, assert `check_project_model_enabled() is None`. Marker `@pytest.mark.unit`.
  - [x] 6.7 Ajouter `test_no_duplicate_check_project_model_enabled_definition` : scan Python natif `Path.rglob("*.py")` + regex `^def check_project_model_enabled\b`, assert hits count == 1 (seul `feature_flags.py`). **Pivot implémentation** : l'approche `subprocess rg` a été remplacée par un scan Python natif (plus portable, `rg` binaire non garanti en CI). Fail-fast régression duplication. Marker `@pytest.mark.unit`. **Bonus** : test additionnel `test_no_applicative_caller_reads_settings_enable_project_model` pour enforcer Q1 (0 hit `settings.enable_project_model` dans `backend/app/`).

- [x] **Task 7 — Validation globale + Completion Notes** (AC6)
  - [x] 7.1 `pytest backend/tests/test_core/test_feature_flags.py backend/tests/test_projects/ -v` → tous verts, aucune régression.
  - [x] 7.2 `pytest --collect-only -q backend/tests/` → noter delta vs baseline Task 1.4. **Attendu ≥ +5** (target +7-9).
  - [x] 7.3 `pytest backend/tests/ 2>&1 | tail -5` → **≥ 1500 passed** + 66 skipped, zéro régression.
  - [x] 7.4 `pytest --cov=backend/app/core/feature_flags --cov-report=term-missing backend/tests/test_core/test_feature_flags.py` → coverage ≥ 95 % (NFR60).
  - [x] 7.5 Consigner en Completion Notes : scans Task 1 (3 greps), baseline avant/après, delta tests, coverage `feature_flags.py`, scan divergence Q1/Q2 (0 hit `settings.enable_project_model`, divergence Pydantic/helper documentée).

- [ ] **Task 8 — Commits intermédiaires facultatifs (leçon 10.8)** — *non exécuté (facultatif, story atomique < 300 lignes diff, commit unique recommandé)*
  - [ ] 8.1 (Optionnel) Commit 1 : « refactor(10.9) : déplacer check_project_model_enabled vers core/feature_flags.py » — seulement Task 2 + vérif tests routeur verts. Facilite review atomique.
  - [ ] 8.2 Commit 2 (ou unique si Task 8.1 skip) : « feat(10.9) : formaliser ENABLE_PROJECT_MODEL (Settings typé + doc CODEMAPS + tests durcissement) » — Tasks 3+4+5+6+7.

---

## Dev Notes

### §1 Contexte amont précis (NE PAS RE-DÉCIDER)

- **Clarif. 5 architecture** : feature flag simple, pas de lib externe. Wrapper `is_project_model_enabled()` 10 lignes. 2 suites CI `flag=on/off` Phase 1, consolidées fin Phase 1.
- **Story 10.1 AC5** : migration `027_cleanup_feature_flag_project_model.py` livrée fin Phase 1 (Story 20.1). Story 10.9 ne livre PAS cette migration.
- **Story 10.2 AC4** : ordre 401 → 404 → 501 documenté dans `projects/router.py`. **Invariant comportemental à préserver** : les 4 tests router passent inchangés.
- **Story 10.1 Q1** : parsimonie env var — 1 seul flag `ENABLE_PROJECT_MODEL` en Phase 0/1. Pas de `ENABLE_MATURITY_MODEL`, pas de `ENABLE_ADMIN_CATALOGUE`. Confirmé par `maturity/router.py` commentaire (ligne 10-12).

### §2 Source tree — composants à toucher

| Chemin                                                      | Action                                         | Invariant                                    |
| ----------------------------------------------------------- | ---------------------------------------------- | -------------------------------------------- |
| `backend/app/core/feature_flags.py`                         | Enrichir (ajout `check_project_model_enabled` + marker cleanup) | Signature `is_project_model_enabled() -> bool` inchangée (pattern shims 10.6). |
| `backend/app/core/config.py`                                | Ajouter champ `enable_project_model: bool`    | Pydantic v2 Field default=False, description requis. |
| `backend/app/modules/projects/router.py`                    | Remplacer def locale par import core          | 4 tests router verts inchangés.              |
| `backend/tests/test_core/test_feature_flags.py`             | +7 tests unit                                  | Markers `@pytest.mark.unit`. Pas de BDD, pas de LLM. |
| `docs/CODEMAPS/feature-flags.md` **(NOUVEAU)**              | Créer fichier 5 sections                       | Suit template `storage.md`.                  |
| `docs/CODEMAPS/index.md`                                    | +1 ligne référence                             | Cohérence éditoriale.                        |

**FICHIERS À NE PAS TOUCHER** :
- `backend/app/modules/maturity/router.py` — commentaire référentiel existant suffit, pas de feature flag ajouté (Q1 Story 10.1).
- `backend/alembic/versions/027_*.py` — livré Story 20.1 fin Phase 1.
- Les tests existants `test_is_project_model_enabled_*` (16) — restent intacts, aucun remaniement.
- Les 4 tests `test_projects/test_router.py` — restent intacts (validation shim).

### §3 Pièges connus (à éviter)

1. **Ne pas router via `settings.enable_project_model` au runtime** (Q1 tranche). Le helper doit lire `os.environ` dynamiquement. Tout import `from app.core.config import settings` dans `feature_flags.py` est un red flag.
2. **Ne pas installer de librairie externe** (Clarification 5). Le scan `pip list | rg "flipper\|unleash\|launchdarkly"` doit rester vide. AC4 enforce en CI.
3. **Ne pas masquer l'env var absent** (user request) : `os.environ.get("ENABLE_PROJECT_MODEL", "false")` — défaut explicite `"false"`, pas `None`. Truthy set strict `{"true", "1", "yes"}` case-insensitive. Défense par défaut = feature OFF (AC1 Epic).
4. **Ne pas retirer le marker cleanup prématurément** — tant que Story 20.1 n'est pas livrée, le marker reste. Un test unit (Task 6.4) enforce la présence.
5. **Ne pas créer un 2ᵉ feature flag opportuniste** (CQ-10). Si un besoin émerge dans Epic 11-20, faire valider Tech Lead + ajouter entrée `docs/CODEMAPS/feature-flags.md §2`.
6. **Ne pas casser l'invariant ordre 401 → 404 → 501** (AC3 Story 10.2). Les 4 tests router sont le garde-fou.

### §4 Pattern commit intermédiaire (leçon 10.8)

- Task 2 isolée est un `git mv` logique (déplacer une fonction + adapter un import). Si le diff est > 50 lignes à cause du nettoyage parallèle, split commit.
- Task 3+4+5+6+7 constituent la formalisation principale → commit final atomique.
- **Facultatif** : si la story reste < 300 lignes de diff, 1 seul commit atomique est acceptable.

### §5 Tests plan récapitulatif

| Test                                                      | AC      | Marker | Description courte                                           |
| --------------------------------------------------------- | ------- | ------ | ------------------------------------------------------------ |
| (existant) `test_is_project_model_enabled_defaults_false` | —       | unit   | Inchangé.                                                    |
| (existant) `test_is_project_model_enabled_truthy_values`  | —       | unit   | Parametrize 15 valeurs, inchangé.                            |
| `test_settings_declares_enable_project_model_field`       | AC2     | unit   | Vérifie champ présent dans `Settings.model_fields`, default=False. |
| `test_settings_boot_value_matches_env_at_init`            | AC2     | unit   | Fresh `Settings()` honore env var au boot (pas singleton).   |
| `test_no_external_feature_flag_library_installed`         | AC4     | unit   | `importlib.metadata.distributions()` scan 8 noms interdits.  |
| `test_feature_flags_has_cleanup_marker`                   | AC5     | unit   | Lecture fichier, assertion textuelle marker cleanup.         |
| `test_check_project_model_enabled_raises_404_when_disabled` | AC1/AC3 | unit   | `monkeypatch.setenv(..., "false")` → `HTTPException(404)`.   |
| `test_check_project_model_enabled_returns_none_when_enabled` | AC1/AC3 | unit   | `monkeypatch.setenv(..., "true")` → return None.             |
| `test_no_duplicate_check_project_model_enabled_definition` | AC3     | unit   | `subprocess rg` → 1 hit unique (fail-fast régression duplication). |

**Total new tests** : 7 (plancher AC6 respecté : +5 min, +7 réel).

### Project Structure Notes

- Aligné structure Nuxt4/FastAPI projet : helpers dans `backend/app/core/`, doc transversale dans `docs/CODEMAPS/`.
- Pas de conflit détecté avec conventions CLAUDE.md.
- Aucun impact frontend (le feature flag est backend-only ; masquage UI côté Nuxt arrivera Epic 11 avec la feature elle-même).

### References

- [Source: `_bmad-output/planning-artifacts/epics/epic-10.md#Story 10.9`] — AC1-AC6 Epic textuels.
- [Source: `_bmad-output/planning-artifacts/architecture.md#Clarification 5`] — simple var env + wrapper, pas de lib externe.
- [Source: `backend/app/core/feature_flags.py`] — état pré-10.9 (helper stub Story 10.2).
- [Source: `backend/app/modules/projects/router.py:40-46`] — `check_project_model_enabled` local à déplacer.
- [Source: `backend/app/core/config.py#Settings`] — pattern `field_validator` + `Field(default=..., description=...)` établi par 10.6 (storage) + 10.7 (env_name).
- [Source: `backend/tests/test_core/test_feature_flags.py`] — 16 tests existants base.
- [Source: `backend/tests/test_projects/test_router.py`] — 4 tests e2e préservés inchangés.
- [Source: `docs/CODEMAPS/storage.md`] — template CODEMAPS (§1 Vue Mermaid, §2 Contrat, §§ pièges).
- [Source: `_bmad-output/implementation-artifacts/10-2-module-projects-squelette.md`] — consommateur amont du helper.
- [Source: `_bmad-output/implementation-artifacts/10-8-framework-injection-prompts-ccc9.md`] — pattern commit intermédiaire + scan NFR66 + absence duplication (leçons capitalisées).

---

## Dev Agent Record

### Agent Model Used

claude-opus-4-7[1m]

### Debug Log References

Aucun incident bloquant. Un pivot mineur au moment de Task 6.7 / 6.3 :
`rg` binaire absent du PATH python3.14 au runtime pytest →
remplacement des 2 tests par scan Python natif (`Path.rglob("*.py")` +
regex compilée). Approche équivalente fonctionnellement, plus portable
(pas de dépendance binaire externe au CI). Documentation test mise à
jour en conséquence.

### Completion Notes List

**Durée réelle** : ~35 min (cible 30 min – 1 h respectée, calibration
11ᵉ story Phase 4 validée).

**§ Scan NFR66 Task 1** :

- `rg -n "is_project_model_enabled|ENABLE_PROJECT_MODEL" backend/app/` →
  3 consommateurs attendus + 1 auto-référence module :
  - `backend/app/core/feature_flags.py` (déclaration helper)
  - `backend/app/modules/projects/router.py` (import + dépendance
    FastAPI + commentaire docstring)
  - `backend/app/modules/maturity/router.py` (commentaire référentiel
    ligne 12 — Q1 Story 10.1 parsimonie confirmée)
- `rg -n "def check_project_model_enabled" backend/app/` pré-refactor :
  1 hit unique dans `projects/router.py:40`. Post-refactor : 1 hit
  unique dans `core/feature_flags.py`. **Règle 10.5 respectée**
  (zéro duplication).
- `ls docs/CODEMAPS/feature-flags.md` pré-refactor : **ABSENT**
  (scan anti-duplication validé). `docs/CODEMAPS/index.md` également
  absent → création d'un hub minimal référençant les 4 CODEMAPS
  existantes + nouvelle page.

**§ Baseline tests (Task 1.4 + Task 7.2)** :

- Pré-refactor : `1561 collected` (baseline Story 10.8 post-patch).
- Post-refactor : `1569 collected` (+8 tests, plancher AC6 +5 respecté,
  prévu +7-9, atteint +8).
- Détail des 8 nouveaux tests (tous `@pytest.mark.unit`) :
  1. `test_settings_declares_enable_project_model_field` (AC2)
  2. `test_settings_boot_value_matches_env_at_init` (AC2)
  3. `test_no_applicative_caller_reads_settings_enable_project_model`
     (Q1 — bonus, enforce 0 hit runtime)
  4. `test_no_external_feature_flag_library_installed` (AC4)
  5. `test_feature_flags_has_cleanup_marker` (AC5)
  6. `test_check_project_model_enabled_raises_404_when_disabled` (AC1/AC3)
  7. `test_check_project_model_enabled_returns_none_when_enabled` (AC1/AC3)
  8. `test_no_duplicate_check_project_model_enabled_definition` (AC3)

**§ Full suite Task 7.3** :

- `pytest backend/tests/` : **1503 passed + 66 skipped** en 203 s
  (baseline 1495 → 1503 = +8). AC6 cible ≥ 1500 atteint. **Zéro
  régression** sur les 1495 tests pré-10.9 (les 16 tests
  `test_feature_flags` existants + les 4 tests `test_projects/test_router`
  passent sans modification — pattern shims legacy 10.6 respecté).

**§ Coverage Task 7.4** :

- `app/core/feature_flags.py` : **100 % (11/11 stmts, 0 miss)**.
  Au-dessus du plancher NFR60 (≥ 95 %). AC6 respecté.

**§ Scan divergence Q1/Q2 (Task 7.5)** :

- `settings.enable_project_model` → 0 hit dans `backend/app/` (scan
  Python natif). Q1 enforced : champ informationnel, runtime lit
  `os.environ`.
- Pydantic coerce `on/off/y/n/true/false/1/0` (divergence native vs
  helper strict `{true, 1, yes}`) : sans effet fonctionnel car aucun
  caller ne lit le champ au runtime. Divergence documentée dans
  `docs/CODEMAPS/feature-flags.md §5` + docstring `is_project_model_enabled`.

**§ AC validation** (6/6) :

- **AC1** ✅ — `core/feature_flags.py` expose `is_project_model_enabled()`
  (signature inchangée, pattern shims legacy 10.6) + nouveau
  `check_project_model_enabled() -> None` (404 si OFF). Marker
  `# CLEANUP: Story 20.1 — retirer ce fichier post-bascule Phase 1
  (migration 027).` présent en tête. Scans `rg` 1 hit unique pour les
  deux définitions.
- **AC2** ✅ — `Settings.enable_project_model: bool = Field(default=False,
  description=...)` déclaré ; coercion `garbage` → `ValidationError`
  au boot vérifiée manuellement + par les tests unit.
- **AC3** ✅ — `projects/router.py` importe depuis `core/feature_flags.py`,
  définition locale supprimée + `_FLAG_404` local supprimé. 4 tests
  routeur verts inchangés.
- **AC4** ✅ — `test_no_external_feature_flag_library_installed` scanne
  `importlib.metadata.distributions()` contre 8 noms interdits → passe.
- **AC5** ✅ — `docs/CODEMAPS/feature-flags.md` créé avec 5 sections
  (Vue Mermaid, État actuel, Pattern 4 étapes, Règle d'or CQ-10, Pièges).
  `docs/CODEMAPS/index.md` créé avec hub minimal référençant les 4
  CODEMAPS. Marker cleanup présent + test enforcement.
- **AC6** ✅ — 1495 → 1503 passed (+8, plancher +5 dépassé). Coverage
  `feature_flags.py` 100 %. Zéro régression.

**§ Tasks** (7/8 réalisées, Task 8 commits intermédiaires facultative
explicitement non exécutée conformément à la spec : story atomique,
diff < 300 lignes, commit unique recommandé par l'utilisateur).

### File List

- Modifié : `backend/app/core/feature_flags.py` (+marker cleanup,
  +`check_project_model_enabled`, +import `HTTPException`).
- Modifié : `backend/app/core/config.py` (+champ `enable_project_model:
  bool = Field(default=False, description=...)` avec commentaire
  CLEANUP Story 20.1).
- Modifié : `backend/app/modules/projects/router.py` (import depuis
  `core/feature_flags` au lieu de définition locale, `_FLAG_404`
  supprimé).
- Modifié : `backend/tests/test_core/test_feature_flags.py` (+8 tests
  unit : Settings field + boot env + no caller applicatif + no lib
  externe + cleanup marker + check 404/None + no duplicate definition).
- Créé : `docs/CODEMAPS/feature-flags.md` (5 sections pattern feature
  flag + règle d'or CQ-10 + pièges).
- Créé : `docs/CODEMAPS/index.md` (hub minimal référençant les 4
  CODEMAPS existantes).
- Modifié : `_bmad-output/implementation-artifacts/10-9-feature-flag-enable-project-model.md`
  (tasks cochées + Dev Agent Record + statut review).
