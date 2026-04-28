---
title: 'BUG-V6-001 — 500 sur génération PDF rapport ESG (timeout LLM résumé exécutif)'
type: 'bugfix'
created: '2026-04-28'
status: 'done'
baseline_commit: 'c2ffba3b5ca79920462c411b4e820379339a4703'
context:
  - '{project-root}/backend/app/modules/reports/service.py'
  - '{project-root}/backend/app/core/llm_guards.py'
  - '{project-root}/backend/app/core/llm/provider.py'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem :** `POST /api/reports/esg/<id>/generate` retourne 500 (`Erreur generation executive_summary : guard LLM echoue apres retry`) après ~33 s sur des évaluations à 30 critères ESG. Cause : `generate_executive_summary` (reports/service.py) instancie un `ChatOpenAI` **sans** `request_timeout` explicite (défaut httpx ≈ 30 s) et **sans** filet infra (le `with_retry` LangGraph n'enveloppe pas ce chemin). Sous charge le LLM répond tard ou tronqué → `LLMGuardError` (`too_short`) ou `httpx.TimeoutException` → 500 utilisateur, rapport `failed`, aucune sortie.

**Approach :** Combiner deux défenses :
- **A (prévention)** : passer `request_timeout=120` au `ChatOpenAI` local de `generate_executive_summary` (timeout long justifié sur résumé executif unique).
- **B (récupération)** : encapsuler l'appel `run_guarded_llm_call` dans un `try/except Exception` qui retourne un **résumé déterministe en français** construit depuis les données structurées (chiffres, forces, lacunes, position benchmark). Le rapport reste généré, le résumé fallback respecte les guards (longueur, langue FR, vocab autorisé, cohérence numérique = sources réelles).

## Boundaries & Constraints

**Always :**
- Modifications limitées à `backend/app/modules/reports/service.py` + `backend/tests/test_report_service.py` (et nouveaux tests unitaires).
- Le résumé fallback doit produire un texte FR de longueur ∈ [`MIN_SUMMARY_LEN`=200, `MAX_SUMMARY_LEN`=3000] caractères, n'utiliser que les valeurs numériques sources (`overall/E/S/G`), n'employer **aucun** terme de `FORBIDDEN_VOCAB` (`garanti`, `certifie`, `valide par`, `homologue`, `accredite`).
- Logger `WARNING` structuré quand le fallback est déclenché : `metric="executive_summary_fallback"`, cause exception class+message, `user_id`, `assessment_id`. Métrique consommable côté Grafana.
- Préserver la signature publique `generate_executive_summary(...)` (même paramètres, même type de retour `str`).
- Le rapport PDF doit aboutir à `ReportStatusEnum.completed` même quand le fallback est emprunté (pas de `failed`).

**Ask First :** aucun — patch ciblé, pattern défense en profondeur déjà validé sur V5/V6 batch.

**Never :**
- Ne pas modifier `llm_guards.py` ni `core/llm/provider.py` (timeout 60 s du provider partagé reste inchangé pour les autres modules).
- Ne pas changer le contrat HTTP du router (statut 200/202 inchangé).
- Ne pas streamer le résumé (Option C écartée : sur-ingénierie pour un texte de 1-2 paragraphes).
- Ne pas introduire de nouvelle dépendance Python ni de nouveau template Jinja2.
- Ne pas modifier le prompt `ESG_REPORT_EXECUTIVE_SUMMARY_PROMPT`.
- Ne pas régresser les tests existants (`test_report_service.py`, `test_report_guards.py`, `test_report_router.py`, `test_report_charts.py`).
- Ne pas masquer un `ValueError` métier (`evaluation introuvable`, `not completed`, `generation deja en cours`) dans le fallback — ces erreurs doivent continuer à remonter telles quelles.

## I/O & Edge-Case Matrix

| Scénario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|----------------------------|----------------|
| **Happy path** | LLM répond < 120 s, contenu conforme | retour LLM brut | N/A |
| **LLM lent mais OK** | LLM répond entre 30 s et 120 s | retour LLM brut (timeout 120 s absorbé) | N/A |
| **LLM timeout dur** | `httpx.TimeoutException` après 120 s | fallback déterministe retourné, log `WARNING metric=executive_summary_fallback cause=TimeoutException`, rapport `completed` | exception capturée |
| **Guard échec post-retry** | `HTTPException(500)` levée par `run_guarded_llm_call` (drift numérique persistant) | fallback déterministe retourné, log `WARNING metric=executive_summary_fallback cause=HTTPException`, rapport `completed` | exception capturée |
| **Erreur réseau / 5xx provider** | `ConnectionError`, `RateLimitError`, `httpx.HTTPStatusError` | fallback déterministe retourné, log `WARNING metric=executive_summary_fallback cause=<class>`, rapport `completed` | exception capturée |
| **Données minimales** | `strengths=[]`, `gaps=[]`, `benchmark_position="unknown"` | fallback ≥ 200 chars en FR centré sur les 4 scores et le secteur | N/A |
| **Tous scores à 0** | `overall=0, E=0, S=0, G=0` (cas dégénéré) | fallback ≥ 200 chars sans drift numérique (les sources `0` sont filtrées par `assert_numeric_coherence`) | N/A |
| **Erreur métier amont** | `ValueError("Evaluation ESG introuvable")` levé avant l'appel LLM | propagée telle quelle au router (404/422), pas de fallback | re-raise |

</frozen-after-approval>

## Code Map

- `backend/app/modules/reports/service.py` -- contient `generate_executive_summary()` (lignes 74-160) et `generate_report()` (lignes 238-384). Cible principale du patch (ajout `request_timeout=120`, wrapping try/except, helper `_build_deterministic_summary`).
- `backend/app/core/llm_guards.py` -- définit `run_guarded_llm_call`, `MIN_SUMMARY_LEN=200`, `MAX_SUMMARY_LEN=3000`, `FORBIDDEN_VOCAB`. Lecture seule, contrats à respecter par le fallback.
- `backend/app/core/llm/provider.py` -- montre le timeout 60 s du provider partagé (référence). Non modifié.
- `backend/app/prompts/esg_report.py` -- prompt LLM (référence, non modifié).
- `backend/tests/test_report_service.py` -- tests existants `TestGenerateReport` (3 tests). Étendu avec 2 nouveaux tests.

## Tasks & Acceptance

**Execution :**
- [x] `backend/app/modules/reports/service.py` -- dans `generate_executive_summary`, passer `request_timeout=120` au `ChatOpenAI` (paramètre supplémentaire ligne ~143). Justification : génération longue d'un texte unique, vs 60 s du provider partagé.
- [x] `backend/app/modules/reports/service.py` -- ajouter helper `_build_deterministic_summary(company_name, sector_label, overall_score, environment_score, social_score, governance_score, strengths, gaps, benchmark_position_label) -> str` au-dessus de `generate_executive_summary`. Construit un texte FR de 400-1500 chars : intro (entreprise + secteur + score global), bloc 4 scores, top 2-3 forces si présentes, top 2-3 lacunes si présentes, position benchmark, conclusion neutre (pas d'engagement type "garanti"). Doit passer les 4 guards.
- [x] `backend/app/modules/reports/service.py` -- dans `generate_executive_summary`, wrapper l'appel `await run_guarded_llm_call(...)` dans `try/except Exception as exc`. Sur exception : `logger.warning("...", extra={"metric": "executive_summary_fallback", "cause": type(exc).__name__, "cause_msg": str(exc)[:200], "user_id": user_id or "anonymous"})` puis `return _build_deterministic_summary(...)`.
- [x] `backend/tests/test_report_service.py` -- ajouter `test_executive_summary_timeout_fallback` : patch `app.modules.reports.service.run_guarded_llm_call` pour lever `asyncio.TimeoutError` ; appeler `generate_executive_summary(...)` avec données réalistes ; asserter résultat string non vide ≥ 200 chars, contient le nom entreprise et le score global, ne contient pas `garanti/certifie`, aucune exception remontée.
- [x] `backend/tests/test_report_service.py` -- ajouter `test_pdf_generation_succeeds_with_30_criteria_via_fallback` : créer assessment avec 30 critères (E1-E10, S1-S10, G1-G10) ; patcher `run_guarded_llm_call` pour lever `HTTPException(500)` ; mocker WeasyPrint ; appeler `generate_report` ; asserter `report.status == ReportStatusEnum.completed`, `report.file_size > 0`, log `metric=executive_summary_fallback` émis (capture via `caplog`).
- [x] `backend/tests/test_report_guards.py` -- mise à jour `test_hallucinated_summary_triggers_retry_then_fails` → `test_hallucinated_summary_triggers_retry_then_fallback` pour refléter le nouveau contrat (pas de 500, fallback à la place ; télémétrie `llm_guard_failure` préservée + nouvelle métrique `executive_summary_fallback`).

**Acceptance Criteria :**
- Given un assessment ESG completed à 30 critères et un LLM qui timeout à 33 s, when `POST /api/reports/esg/<id>/generate` est appelé, then la réponse n'est plus 500 et le rapport PDF est créé avec un résumé exécutif fallback non vide.
- Given une exception infra (`TimeoutException`, `ConnectionError`, `RateLimitError`, `HTTPException(500)`) levée par `run_guarded_llm_call`, when `generate_executive_summary` s'exécute, then la fonction retourne le fallback déterministe et émet un log `WARNING metric=executive_summary_fallback`.
- Given une `ValueError` métier (assessment introuvable / not completed / generation déjà en cours), when `generate_report` s'exécute, then l'exception remonte inchangée (pas de fallback).
- Given le fallback est emprunté, when ses sorties sont passées aux 4 guards (`assert_length`, `assert_language_fr`, `assert_no_forbidden_vocabulary`, `assert_numeric_coherence`), then aucun `LLMGuardError` n'est levé.
- Given les tests existants `test_report_service.py`, `test_report_guards.py`, `test_report_router.py`, `test_report_charts.py`, when la suite est rejouée, then 100 % verts sans modification.

## Spec Change Log

### 2026-04-28 — Patches review (3 sous-agents : blind / edge-case / acceptance)

5 patches appliqués sans loopback (aucun bad_spec ni intent_gap) :

- **PATCH-1** [E1+B4+E3 CRITICAL/HIGH] : `_build_deterministic_summary` re-applique les 4 guards (`assert_length`, `assert_language_fr`, `assert_no_forbidden_vocabulary`, `assert_numeric_coherence`) après construction. Bascule vers constante `_FALLBACK_MINIMAL_SUMMARY` (texte fixe FR pré-validé sans données dynamiques) si le fallback dynamique échoue. Évite : un `company_name="Garantie SARL"` produirait un texte avec vocab interdit qui passerait silencieusement. Log dédié `metric=executive_summary_fallback_minimal`.
- **PATCH-2** [B3+E2 CRITICAL/MEDIUM] : log fallback ne contient plus `cause_msg=str(exc)[:200]` (risque de fuite clé API / payload OpenRouter). Capture `type(exc).__name__` + `status_code` (uniquement si attribut entier présent, ex. `HTTPException` FastAPI). Test asserte l'absence de `cause_msg`.
- **PATCH-3** [A1 MEDIUM] : `generate_executive_summary` accepte un paramètre optionnel `assessment_id: str | None = None`, passé depuis `generate_report`. Émis dans le log fallback pour corrélation Grafana (le spec « Always » l'exigeait sans qu'il soit dans la signature originale).
- **PATCH-4** [A3 LOW] : test paramétré `test_executive_summary_fallback_on_infra_errors` couvrant `ConnectionError`, `RuntimeError` (proxy `RateLimitError`), `HTTPException(503)` — verrouille la matrice I/O « Erreur réseau / 5xx provider ».
- **PATCH-5** [A4 LOW] : 3 tests supplémentaires sur cas dégénérés du fallback : `test_fallback_with_minimal_data_passes_guards`, `test_fallback_with_zero_scores_passes_guards`, `test_fallback_with_forbidden_company_name_falls_to_minimal` (verrouille PATCH-1).

**Findings rejetés (spec a tranché, pas de re-débat) :** B1 (`except Exception` large) — choix explicite des Design Notes. B2/E4 (hallucination → fallback) — intention de l'Approach. B5 (timeout 120 vs 60) — analyse incorrecte (provider partagé pas sur ce chemin).

**KEEP instructions (à préserver lors d'une éventuelle re-dérivation) :**
- Re-application des guards sur le fallback dynamique + bascule vers constante minimale = défense en profondeur, **non négociable**.
- Aucun `str(exc)` brut dans les logs warning (vecteur d'exfiltration).
- `assessment_id` propagé jusqu'au log pour télémétrie Grafana.

**Différé (ajouté à `deferred-work.md`) :** DEF-BUG-V6-1-1 (cache de résumé exécutif sur `(assessment_id, version)`).

## Design Notes

Squelette du fallback (≈ 600 chars typique, sûr pour les guards) :

```python
def _build_deterministic_summary(
    company_name: str,
    sector_label: str,
    overall_score: float,
    environment_score: float,
    social_score: float,
    governance_score: float,
    strengths: list[dict],
    gaps: list[dict],
    benchmark_position_label: str,
) -> str:
    parts = [
        f"L'entreprise {company_name} ({sector_label}) obtient un score ESG global "
        f"de {overall_score}/100, avec un pilier Environnement a {environment_score}/100, "
        f"un pilier Social a {social_score}/100 et un pilier Gouvernance a "
        f"{governance_score}/100."
    ]
    if strengths:
        top = ", ".join(s.get("title", "") for s in strengths[:3] if s.get("title"))
        if top:
            parts.append(f"Les principaux points forts identifies sont : {top}.")
    if gaps:
        top = ", ".join(g.get("title", "") for g in gaps[:3] if g.get("title"))
        if top:
            parts.append(f"Les axes d'amelioration prioritaires concernent : {top}.")
    if benchmark_position_label:
        parts.append(f"Positionnement sectoriel : {benchmark_position_label}.")
    parts.append(
        "Ce resume est genere a partir des donnees structurees de l'evaluation. "
        "Une lecture detaillee des piliers et critere par critere est recommandee "
        "pour orienter le plan d'action."
    )
    return " ".join(parts)
```

**Pourquoi pas de Jinja2 dédié :** une fonction Python pure tient en ~25 lignes, reste co-localisée avec son consommateur, et évite un nouveau fichier template. Le template HTML existant (`esg_report.html`) reçoit le résumé via la variable `executive_summary` — il ignore la provenance (LLM ou fallback).

**Pourquoi capturer `Exception` large :** la chaîne d'erreurs possibles est hétérogène (`httpx.TimeoutException`, `openai.RateLimitError`, `fastapi.HTTPException`, `LLMError`, `LLMRateLimitError`). Filtrer pour ne garder que `ValueError`/`KeyError` métier serait fragile ; l'inversion (laisser passer `ValueError` levé en amont, capturer le reste localement à l'appel LLM) est plus sûre puisque `_build_deterministic_summary` est lui-même infaillible (pure data → string).

## Verification

**Commands :**
- `cd backend && source venv/bin/activate && pytest tests/test_report_service.py -v` -- attendu : 3 anciens tests + 2 nouveaux tests, tous verts.
- `cd backend && source venv/bin/activate && pytest tests/test_report_guards.py tests/test_report_router.py tests/test_report_charts.py -v` -- attendu : zéro régression.
- `cd backend && source venv/bin/activate && pytest tests/ -x` -- attendu : suite complète verte (baseline ~1829 tests).

**Manual checks :**
- Lancer le backend, créer un assessment ESG avec 30 critères, déclencher `POST /api/reports/esg/<id>/generate`. Vérifier statut HTTP 200/202 et présence d'un PDF téléchargeable contenant un résumé exécutif lisible (LLM ou fallback selon la latence du provider).
- Inspecter les logs : si `metric=executive_summary_fallback` apparaît, confirmer que le PDF a néanmoins le statut `completed` côté table `reports`.

## Suggested Review Order

**Logique du fallback (cœur du patch)**

- Bloc `try/except Exception` qui transforme un 500 en fallback déterministe avec log warning sécurisé.
  [`service.py:266`](../../backend/app/modules/reports/service.py#L266)

- Builder du résumé fallback : construit le texte FR puis re-applique les 4 guards ; bascule sur la constante minimale en cas d'échec.
  [`service.py:90`](../../backend/app/modules/reports/service.py#L90)

- Constante de dernier recours, texte FR fixe sans données dynamiques (immune aux noms d'entreprise pathologiques).
  [`service.py:79`](../../backend/app/modules/reports/service.py#L79)

**Configuration LLM**

- `request_timeout=120` ajouté localement au `ChatOpenAI` du résumé exécutif (vs ~30 s défaut httpx).
  [`service.py:246`](../../backend/app/modules/reports/service.py#L246)

- Propagation de `assessment_id` depuis `generate_report` jusqu'au log fallback (corrélation Grafana).
  [`service.py:289`](../../backend/app/modules/reports/service.py#L289)

**Tests — chemin nominal**

- Test scénario timeout LLM : mock `asyncio.TimeoutError`, assertion 4 guards re-passent + log sans `cause_msg`.
  [`test_report_service.py:180`](../../backend/tests/test_report_service.py#L180)

- Test paramétré matrice I/O : `ConnectionError`, `RuntimeError`, `HTTPException(503)`.
  [`test_report_service.py:271`](../../backend/tests/test_report_service.py#L271)

- Test PDF de bout-en-bout avec 30 critères ESG + LLM en échec → rapport `completed`.
  [`test_report_service.py:404`](../../backend/tests/test_report_service.py#L404)

**Tests — cas dégénérés**

- Données minimales (strengths/gaps vides, benchmark vide) : fallback ≥ 200 chars conforme.
  [`test_report_service.py:311`](../../backend/tests/test_report_service.py#L311)

- Tous scores à 0 : `source_values` vide, pas de drift numérique.
  [`test_report_service.py:346`](../../backend/tests/test_report_service.py#L346)

- `company_name="Garantie SARL"` (vocab interdit) → bascule vers constante minimale.
  [`test_report_service.py:372`](../../backend/tests/test_report_service.py#L372)

**Mise à jour test guards (nouveau contrat sans 500)**

- Renommé `..._then_fails` → `..._then_fallback` ; vérifie retry x2 + métrique `llm_guard_failure` préservée + nouvelle métrique `executive_summary_fallback`.
  [`test_report_guards.py:70`](../../backend/tests/test_report_guards.py#L70)
