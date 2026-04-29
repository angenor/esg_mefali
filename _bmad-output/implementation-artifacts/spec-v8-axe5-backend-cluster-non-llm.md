---
title: 'V8-AXE5 — Cluster backend non-LLM (validators Pydantic + dashboard in_progress + hooks gamification + setup.sh libgobject)'
type: 'bugfix'
created: '2026-04-29'
status: 'done'
baseline_commit: '26c7e869dc832fe00fedff8f556f1ebf142802f9'
context:
  - '{project-root}/CLAUDE.md'
  - '{project-root}/_bmad-output/implementation-artifacts/tests-manuels-vague-7-2026-04-28.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Quatre bugs backend orthogonaux persistent indépendamment du provider LLM (RÉFUTATION switch Claude V7.1) : (1) `PATCH /api/company/profile` accepte whitespace/empty et écrase la valeur courante (BUG-V7-002 / V7.1-002) ; (2) le dashboard ignore les bilans `status='in_progress'` et n'affiche aucune donnée même quand le total tCO2e existe (BUG-V7-009 / V7.1-014) ; (3) la gamification n'attribue jamais le badge `first_carbon` car `check_and_award_badges` n'est appelée que depuis `update_action_item` (BUG-V7-010 / V7.1-013) ; (4) WeasyPrint plante au démarrage sur macOS faute de libgobject/pango/cairo/gdk-pixbuf (BUG-V7.1-012, env système non automatisé).

**Approach:** Quatre sous-patchs ciblés sur layers indépendants, un par fichier ou nouveau fichier : validator Pydantic strip+blank-rejection ; élargissement du filtre dashboard à `in_progress` quand `total_emissions_tco2e` est non-null ; appel direct de `check_and_award_badges` aux call-sites de finalization (carbon/esg/application/credit) puisque listener SQLAlchemy `after_commit` est anti-pattern avec `AsyncSession` ; nouveau `setup.sh` qui détecte macOS et installe pango/cairo/glib/gdk-pixbuf/libffi via brew + venv + dépendances Python.

## Boundaries & Constraints

**Always:**
- Le validator Pydantic doit accepter `None` (champ omis) et la string vide explicite ne doit JAMAIS écraser une valeur existante en BDD : rejeter via `ValueError` (HTTP 422).
- Trim systématique des strings non-vides (`"  AgriVert  "` → `"AgriVert"`) côté Pydantic, avant de toucher la BDD.
- Le dashboard inclut les assessments `in_progress` UNIQUEMENT quand `total_emissions_tco2e IS NOT NULL` (sinon la carte « Aucune donnée » reste pertinente).
- `check_and_award_badges` reste idempotent (déjà conçu ainsi) : appel ajouté en fin de transaction de finalization, après `db.commit()`.
- `setup.sh` est idempotent (`brew install --quiet` accepté si déjà installé) et non-destructif (ne réécrit pas `.env` existant).

**Ask First:**
- Aucune décision humaine attendue : tous les paths sont déterminés par le repo réel.

**Never:**
- Pas de listener SQLAlchemy `event.listens_for(Session, "after_commit")` global : incompatible avec `AsyncSession` (la session sync ouverte par le listener crée une fuite ou un deadlock). Approche par appels directs aux call-sites de finalization, identique au pattern existant `update_action_item`.
- Pas de migration Alembic, pas de modification de modèle SQLAlchemy.
- Pas de fix LLM (prompts/tools) : laissé aux autres axes V8.
- Pas de modification de `deploy.sh` (cible VPS distant, hors-scope).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| PATCH whitespace | `{"company_name":"   "}` | HTTP 422 `Field cannot be blank or whitespace only` | ValueError remonté par Pydantic |
| PATCH string vide | `{"company_name":""}` | HTTP 422 même message | ValueError |
| PATCH valeur trim | `{"company_name":"  AgriVert  "}` | HTTP 200 → BDD `company_name='AgriVert'` | N/A |
| PATCH `null` | `{"company_name":null}` | HTTP 200, champ inchangé (None passe-through) | N/A |
| Dashboard carbon in_progress + total | `CarbonAssessment(status=in_progress, total=16.9)` | Carte affiche `16.9 tCO2e` + label `(en cours)` | N/A |
| Dashboard carbon in_progress sans total | `total=NULL` | Carte « Aucune donnée » | N/A |
| Badge first_carbon | `complete_assessment(...)` appelé pour la 1re fois | Badge `first_carbon` créé en BDD | log warning si commit hors-transaction échoue |
| Badge idempotent | Bilan déjà completé, badge déjà attribué | Aucun nouveau badge, pas d'erreur | N/A |
| setup.sh macOS sans brew | `command -v brew` échoue | Erreur explicite + lien install brew | exit 1 |
| setup.sh Linux | `uname` ≠ Darwin | Skip étape brew, continue venv | N/A |

</frozen-after-approval>

## Code Map

- `backend/app/modules/company/schemas.py` — `CompanyProfileUpdate` Pydantic, déjà `extra="forbid"` ; manque validator strip+blank-rejection sur `company_name`/`sub_sector`/`city`/`country`/`governance_structure`/`environmental_practices`/`social_practices`/`notes`.
- `backend/app/modules/dashboard/service.py` — `_get_carbon_summary` filtre `status == CarbonStatusEnum.completed` (ligne 105). Élargir à `in_progress OR completed` quand `total_emissions_tco2e IS NOT NULL`.
- `backend/app/modules/action_plan/badges.py` — `check_and_award_badges` correct, mais appelée UNIQUEMENT depuis `action_plan/service.py:623` (update_action_item). À ajouter en fin de `complete_assessment` (carbon), de la finalization ESG, de la création d'application et de la création de credit_score.
- `backend/app/modules/carbon/service.py:192` — `complete_assessment(...)` ajoute hook badges après commit (passe par le caller car cette fonction fait flush et non commit).
- `backend/app/modules/esg/service.py` — finalization ESG (à localiser).
- `backend/app/modules/applications/service.py` — création FundApplication.
- `backend/app/modules/credit/service.py` — `generate_credit_score` (idempotence déjà fixe par V8-AXE3).
- `setup.sh` (NEW à la racine) — script bootstrap macOS/Linux : brew deps + python venv + npm install.
- `backend/tests/test_company/test_schemas.py` (NEW si absent) — unit tests validator strip/blank.
- `backend/tests/test_dashboard/test_service.py` — étendre tests carbon summary in_progress.
- `backend/tests/test_action_plan/test_badges_integration.py` (NEW) — tests intégration badge after carbon completion.

## Tasks & Acceptance

**Execution:**
- [x] `backend/app/modules/company/schemas.py` -- ajouter `@field_validator(...mode="before")` `_strip_or_reject_blank` sur les 8 champs string optionnels (`company_name`, `sub_sector`, `city`, `country`, `governance_structure`, `environmental_practices`, `social_practices`, `notes`) -- BUG-V7.1-002 défense en profondeur côté REST (le tool LLM est déjà fixe par V6-011).
- [x] `backend/tests/test_company/test_schemas.py` -- 6 tests : whitespace `"   "` → ValueError ; empty `""` → ValueError ; trim `"  X  "` → `"X"` ; None passe-through ; valeur normale inchangée ; payload mixte (un champ trim, un autre None).
- [x] `backend/app/modules/dashboard/service.py` -- élargir filtre `_get_carbon_summary` à `status IN (completed, in_progress) AND total_emissions_tco2e IS NOT NULL` ; ajouter clé `in_progress: bool` au dict retourné -- BUG-V7.1-014.
- [x] `backend/tests/test_dashboard/test_service.py` -- ajouter 2 tests : in_progress + total → renvoie summary avec `in_progress=True` ; in_progress sans total → renvoie None.
- [x] `backend/app/modules/carbon/service.py` -- ajouter appel non-bloquant `check_and_award_badges(db, user_id)` dans `complete_assessment` après le `flush` (le commit est géré par le caller, donc envelopper try/except WARN log) -- BUG-V7.1-013.
- [x] `backend/app/modules/applications/service.py` -- repérer la fonction de création FundApplication, ajouter même hook fire-and-forget après commit.
- [x] `backend/app/modules/credit/service.py` -- repérer la création/persistance CreditScore (cf V8-AXE3 idempotence), ajouter même hook fire-and-forget après commit.
- [x] `backend/app/modules/esg/service.py` -- repérer la finalization ESG (status → completed avec score), ajouter même hook fire-and-forget après commit.
- [x] `backend/tests/test_action_plan/test_badges_integration.py` (NEW) -- 4 tests : `complete_assessment` carbon → badge `first_carbon` créé ; idempotence (2e appel = no-op) ; flow ESG complete → badge `esg_above_50` ; create FundApplication → badge `first_application`.
- [x] `setup.sh` (NEW) -- script bash idempotent, détecte macOS via `uname -s` ; sur macOS appelle `brew install pango cairo glib gdk-pixbuf libffi`; sur Linux delègue à `apt-get install` les paquets équivalents (`libpango-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 libffi-dev`) si possible sinon hint message ; crée `backend/venv` si absent ; `pip install -r backend/requirements.txt` ; `npm install` dans `frontend/` ; copie `.env.example` → `.env` SEULEMENT si `.env` absent.

**Acceptance Criteria:**
- Given AgriVert Sarl a un profil existant, when l'utilisateur envoie `PATCH /api/company/profile {"company_name":"   "}`, then la réponse est HTTP 422 et la valeur en BDD reste `AgriVert Sarl` (BUG-V7.1-002 résolu).
- Given un bilan carbone `status=in_progress` avec `total_emissions_tco2e=16.9`, when le frontend appelle `GET /api/dashboard`, then la carte carbone affiche `16.9 tCO2e` avec marqueur `in_progress=true` (BUG-V7.1-014 résolu).
- Given un utilisateur sans badge `first_carbon`, when `complete_assessment` est appelée pour son premier bilan, then une ligne `Badge(badge_type=first_carbon)` existe en BDD après commit (BUG-V7.1-013 résolu).
- Given un développeur clone le repo sur macOS vierge, when il exécute `bash setup.sh`, then les libs WeasyPrint sont installées via brew, le venv est créé et les dépendances backend/frontend installées sans intervention manuelle (BUG-V7.1-012 résolu).
- Given la suite backend existante (1928 tests verts post-AXE4), when la nouvelle suite tourne, then le total est ≥ `1928 + 12 nouveaux` tests verts, zéro régression.

## Spec Change Log

### 2026-04-29 — Review patches (4 findings)

Review (3 reviewers : code-reviewer blind, python-reviewer edge-case, general-purpose acceptance auditor) : auditor PASS, 11 findings techniques classifies en 4 patches + 5 defer + 2 reject.

**Patches appliques (defense en profondeur, pas de loopback) :**
- R3-1 (HIGH) Zero-width unicode (\\u200B/\\u200C/\\u200D/\\u2060/\\uFEFF) bypassait `_strip_or_reject_blank` (str.strip natif n'inclut que NBSP, pas zero-width). Ajout `invisible_chars` au strip + 6 nouveaux tests parametrises.
- R3-3 (HIGH) Multiple in_progress meme annee → `variation_percent` non-deterministe. Ajout tri secondaire `updated_at desc` dans `_get_carbon_summary`.
- R3-4 (MEDIUM) `safe_check_and_award_badges` accepte `user_id=None` silencieusement. Ajout fast-fail au top de la fonction.
- R3-5 (MEDIUM) `setup.sh` `set -e` + `brew install` multi-formules → un echec coupe le bootstrap entier. Boucle for + `|| echo warn` pour install par formule resiliente.

**Defer :** R1-2/R3-2 commit hook prematuré (risque marginal, pattern coherent avec `update_action_item:617-625`), R3-6 stale .env, R1-1/R3-8 deferred imports (pattern volontaire), R1-3 `carbon_mapping.py` dict order (hors scope V8-AXE5 = V8-AXE4), R3-7 variation vs in_progress previous (cosmetique).

**Reject :** R1-5 TOCTOU `/tmp/_setup_smoke.pdf` (dev local), R1-4 `sector` validator (champ enum, pas string libre).

## Design Notes

**Validator Pydantic — pattern réutilisable :**
```python
@field_validator(
    "company_name", "sub_sector", "city", "country",
    "governance_structure", "environmental_practices",
    "social_practices", "notes",
    mode="before",
)
@classmethod
def _strip_or_reject_blank(cls, value: object) -> object:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise ValueError("Le champ ne peut pas être vide ou contenir uniquement des espaces")
        return stripped
    return value
```

**Hook badges fire-and-forget — pattern (déjà existant pour update_action_item) :**
```python
try:
    from app.modules.action_plan.badges import check_and_award_badges
    await check_and_award_badges(db, user_id)
except Exception:
    logger.warning("Erreur vérification badges (non bloquant)", exc_info=True)
```

**Pourquoi pas un listener SQLAlchemy `after_commit` global ?** L'API `Session.events.after_commit` est synchrone par design. Avec `AsyncSession`, l'execution du callback bloque l'event loop ou ouvre une session sync orpheline qui contourne la pool async. SQLAlchemy 2.x officiellement déconseille cette voie pour les hooks async (cf. discussion #6700). L'alternative idiomatique = appel explicite aux call-sites de finalization, déjà adoptée par le code existant (`action_plan/service.py:623`).

**setup.sh — détection OS :**
```bash
case "$(uname -s)" in
  Darwin)
    command -v brew >/dev/null 2>&1 || { echo "Brew requis : https://brew.sh"; exit 1; }
    brew install pango cairo glib gdk-pixbuf libffi
    ;;
  Linux)
    if command -v apt-get >/dev/null 2>&1; then
      sudo apt-get update && sudo apt-get install -y libpango-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 libffi-dev
    else
      echo "⚠️  Distribution non Debian — installer pango/cairo/gdk-pixbuf/libffi manuellement."
    fi
    ;;
esac
```

## Verification

**Commands:**
- `cd backend && source venv/bin/activate && pytest tests/test_company/test_schemas.py -v` -- expected: 6 tests passed
- `cd backend && source venv/bin/activate && pytest tests/test_dashboard/test_service.py tests/test_action_plan/test_badges_integration.py -v` -- expected: tous tests passed
- `cd backend && source venv/bin/activate && pytest -q` -- expected: ≥1928+ tests passed, 0 failed
- `bash setup.sh` (macOS) -- expected: exit 0, brew deps installées, venv créé
- `cd backend && source venv/bin/activate && python -c "import weasyprint; weasyprint.HTML(string='<p>x</p>').write_pdf('/tmp/_w.pdf')"` -- expected: génération PDF sans OSError

**Manual checks:**
- `curl -X PATCH /api/company/profile -d '{"company_name":"   "}'` doit renvoyer 422.
- Dashboard carte carbone : status=in_progress + total=16.9 → carte affiche `16.9 tCO2e` (pas « Aucune donnée »).
- Après `complete_assessment` carbon : `SELECT * FROM badges WHERE badge_type='first_carbon'` doit renvoyer 1 ligne.

## Suggested Review Order

**Validator REST (BUG-V7.1-002)**

- Validator strip+blank+invisible appliqué aux 8 champs string ; entry point du fix
  [`schemas.py:81`](../../backend/app/modules/company/schemas.py#L81)

- Tests parametrés : whitespace, empty, zero-width unicode, trim, mixte
  [`test_company_schemas.py:1`](../../backend/tests/test_company_schemas.py#L1)

**Dashboard in_progress (BUG-V7.1-014)**

- Filtre élargi `completed OR in_progress`, tri secondaire updated_at, flag `in_progress` dans le dict
  [`service.py:97`](../../backend/app/modules/dashboard/service.py#L97)

- Tests : in_progress+total → données ; in_progress sans total → None
  [`test_service.py:191`](../../backend/tests/test_dashboard/test_service.py#L191)

**Hooks gamification SQLAlchemy-friendly (BUG-V7.1-013)**

- Helper fire-and-forget avec fast-fail user_id=None
  [`badges.py:134`](../../backend/app/modules/action_plan/badges.py#L134)

- Hook après `complete_assessment` carbon
  [`carbon_tools.py:251`](../../backend/app/graph/tools/carbon_tools.py#L251)

- Hook après `finalize_assessment_with_benchmark` ESG
  [`esg_tools.py:219`](../../backend/app/graph/tools/esg_tools.py#L219)

- Hook après `create_application` (deux tools application + financing)
  [`application_tools.py:80`](../../backend/app/graph/tools/application_tools.py#L80)
  [`financing_tools.py:194`](../../backend/app/graph/tools/financing_tools.py#L194)

- Hook après persistance CreditScore
  [`service.py:752`](../../backend/app/modules/credit/service.py#L752)

- Tests intégration : carbon completion → first_carbon, idempotence
  [`test_badges.py:211`](../../backend/tests/test_action_plan/test_badges.py#L211)

**Bootstrap macOS (BUG-V7.1-012)**

- Script idempotent, install brew formule par formule, smoke WeasyPrint
  [`setup.sh:1`](../../setup.sh#L1)
