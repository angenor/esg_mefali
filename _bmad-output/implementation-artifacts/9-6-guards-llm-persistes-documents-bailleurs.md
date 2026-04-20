# Story 9.6 : Guards LLM persistés sur documents remis aux bailleurs

Status: done

**Priorité** : P1 (responsabilité juridique, compliance, crédibilité — invisible tant que ça n'arrive pas, catastrophique quand ça arrive)
**Source** : [spec-audits/index.md §P1 #10](./spec-audits/index.md) (reclassé P2→P1 le 2026-04-16, élargi progressivement 006+008+011) + [PRD §Risque 10](../planning-artifacts/prd.md) + [PRD §SC-T8](../planning-artifacts/prd.md) + [PRD FR40/FR41/FR55/FR56](../planning-artifacts/prd.md) + [PRD §Traceability P1 #10 guards LLM universels](../planning-artifacts/prd.md#L1676)
**Specs d'origine** : [specs/006-esg-pdf-reports/spec.md](../../specs/006-esg-pdf-reports/spec.md) (résumé exécutif) + [specs/011-dashboard-action-plan/spec.md](../../specs/011-dashboard-action-plan/spec.md) (plan d'action JSON) + [specs/008-green-financing-matching/spec.md](../../specs/008-green-financing-matching/spec.md) (fiche préparation — analyse pattern, scope 9.6 limité, voir Hors scope §1)
**Durée estimée** : 10 à 14 h (module partagé + intégration résumé exécutif + intégration plan d'action + Pydantic strict + télémétrie + tests ciblés)

<!-- Note : Validation est optionnelle. Lancer `validate-create-story` pour un quality check avant `dev-story`. -->

---

## Story

En tant que **PME africaine francophone qui exporte un document (PDF ESG, fiche préparation, plan d'action) destiné à un bailleur ou à un financeur**,
je veux que **tout contenu généré par le LLM et persisté dans ce document passe un garde-fou structurel (longueur bornée, langue française vérifiée, cohérence numérique avec les faits source, vocabulaire interdit bloqué, schéma Pydantic strict pour JSON)**,
afin que **Mefali ne remette jamais un document hallucinant des chiffres, promettant des garanties non fondées, ou contenant un plan d'action avec 47 actions contradictoires qui décrédibiliseraient ma candidature et m'exposeraient juridiquement**.

## Contexte

### Risque concret (audit P1 #10 + PRD Risque 10)

Aujourd'hui, **trois surfaces LLM** produisent du contenu qui aboutit dans un document remis à un tiers :

1. **Résumé exécutif ESG** — [backend/app/modules/reports/service.py:63 `generate_executive_summary()`](../../backend/app/modules/reports/service.py#L63) — texte libre français inclus dans le PDF rendu par WeasyPrint (template `esg_report.html`). Aucun contrôle de longueur, de langue, de cohérence numérique avec les scores passés en argument (`overall_score`, `environment_score`, etc.), ni de vocabulaire interdit. Le LLM peut **inventer un score** dans sa narration (ex. « votre excellent score de 82/100 » alors que la vraie valeur est 54), **promettre** un financement (« garanti éligible au GCF »), ou **écrire en anglais** si le modèle dérive.

2. **Plan d'action JSON** — [backend/app/modules/action_plan/service.py:171 `generate_action_plan()`](../../backend/app/modules/action_plan/service.py#L171) — tableau JSON de 10-15+ actions parsé par [`_extract_json_array()`](../../backend/app/modules/action_plan/service.py#L29) et persisté dans `action_items`. Aucune validation de schéma stricte. Les guards actuels sont **palliatifs minimaux** :
   - `_safe_category()` retombe sur `governance` pour toute catégorie inconnue (silent corruption).
   - `_safe_priority()` retombe sur `medium`.
   - `_parse_action_date()` borne la date au `timeframe` mais accepte n'importe quoi en silence.
   - `title` tronqué à 500 caractères par `str(action.get("title"))[:500]` mais `description` sans borne.
   - Aucune borne sur `estimated_cost_xof` (LLM pourrait écrire `10^18`), ni sur le **nombre d'actions** (LLM pourrait renvoyer 47 actions ou 0), ni sur la cohérence « sum des coûts ≤ budget déclaré ».

3. **Fiche de préparation financing** — [backend/app/modules/financing/preparation_sheet.py:66 `generate_preparation_sheet()`](../../backend/app/modules/financing/preparation_sheet.py#L66) — **actuellement 100 % template Jinja2**, aucun appel LLM direct. Les données (`matching_criteria`, `missing_criteria`, `intermediary_*`) proviennent du matching service et de la BDD. **Guards LLM non applicables en l'état** (voir Hors scope §1), mais la story ouvre un point d'ancrage : si une future story (P3) ajoute un paragraphe narratif LLM dans la fiche, il devra passer par le module `llm_guards` livré ici.

**Impact catastrophique possible** : un bailleur lit « score ESG 82/100 » dans le PDF remis par l'entrepreneur, vérifie dans le détail → trouve 54/100 → rejet immédiat + perte de confiance plateforme + **exposition juridique** de Mefali (document signé électroniquement par l'utilisateur — cf. FR40 signature obligatoire).

### Pourquoi P1 (rappel justification audit + PRD)

| Risque | Symptôme | Détectabilité actuelle | Gravité |
|--------|----------|-----------------------|---------|
| Hallucination chiffrée (score inventé) | Bailleur vérifie, rejette | Aucune (tests valident « 200 OK », pas le contenu) | Compliance + crédibilité |
| Vocabulaire interdit (« garanti », « certifié ») | Promesse contractuelle implicite | Aucune | Juridique (responsabilité Mefali) |
| JSON malformé ou hors bornes | 47 actions, dates en 2099, coûts 10^18 FCFA | `_safe_*()` fallback silencieux | Crédibilité + UX |
| Dérive de langue (réponse en anglais) | Document PDF partiellement EN | Aucune | UX (public FR) + compliance |

**Même classe que les failles sécurité déjà adressées** (rate limiting story 9.1, quota stockage story 9.2, flag manuel story 9.5) : invisible tant que ça n'arrive pas, désastreux quand ça arrive.

Mentionné explicitement dans :
- [PRD L989 Traceability matrix : « Guards LLM actifs sur documents persistés → Risque 10 — non négociable »](../planning-artifacts/prd.md)
- [PRD L1676 : « FR36 + FR40 + FR41 + FR44 → P1 #10 guards LLM sur contenus persistés + P2 #20 tests contenu PDF → Phase 0 `guards-llm-universels` »](../planning-artifacts/prd.md)
- [PRD L1293 : « Couverture ≥ 85 % sur code critique : guards LLM, anonymisation PII, RLS enforcement… »](../planning-artifacts/prd.md)

### État actuel du code — surfaces LLM concernées par la story

| Surface | Fichier / fonction | Nature | Output | Risque |
|---------|--------------------|--------|--------|--------|
| Résumé exécutif ESG | `backend/app/modules/reports/service.py:63` `generate_executive_summary()` | Free text FR | `str` injecté dans template Jinja2 `esg_report.html` | Hallucination chiffrée, vocabulaire interdit, langue EN |
| Plan d'action JSON | `backend/app/modules/action_plan/service.py:171` `generate_action_plan()` | JSON structuré | `list[dict]` persisté en `action_items` | Schéma invalide, bornes, nombre d'actions |
| Fiche préparation | `backend/app/modules/financing/preparation_sheet.py:66` | Template pur (pas de LLM) | PDF Jinja2 | **HORS SCOPE 9.6** — aucun LLM à garder (voir Hors scope §1) |

### Pattern déjà éprouvé dans le codebase

La story réutilise / étend les patterns existants :
- **Pydantic strict** : spec 018 `InteractiveQuestion*` avec `model_config = ConfigDict(extra="forbid")`.
- **Tests contenu PDF** : pattern suggéré par [P2 #20 audit](./spec-audits/index.md#L218) — parse + assertions sur sections. La story 9.6 **ne livre pas** le parsing PDF (P2 séparé) mais livre les tests d'assertion sur les **strings pré-PDF** (avant rendu WeasyPrint), ce qui teste 100 % du contenu LLM.
- **Télémétrie échecs guards** : le PRD prescrit [NFR39 dashboard + NFR40 alerting](../planning-artifacts/prd.md#L1253). La story livre le **counter Prometheus-compatible** (via `logger.warning(..., extra={"metric": "llm_guard_failure"})`) ; le dashboard admin_mefali FR55 est hors scope 9.6.
- **Module partagé** : `backend/app/core/llm_guards.py` — cohérence avec les autres modules transverses (`backend/app/core/config.py`, `backend/app/core/security.py`).

---

## Critères d'acceptation

1. **AC1 — Guard text libre détecte l'hallucination chiffrée** — Given un résumé exécutif LLM contient la phrase `"Avec votre excellent score de 82/100 en gouvernance, votre entreprise excelle"` alors que le vrai `governance_score=54.0` est passé en argument à `generate_executive_summary()`, When le guard `assert_numeric_coherence(text, {"governance_score": 54.0, "environment_score": 60.0, ...})` est invoqué, Then le guard **lève `LLMGuardError(code="numeric_drift", detected_value=82, expected=54, field="governance_score")`** — l'exception est attrapée dans le service appelant, un `logger.warning` structuré est émis avec `extra={"metric": "llm_guard_failure", "guard": "numeric_coherence", "target": "executive_summary", "user_id": str(user_id), "detected": 82, "expected": 54}`, puis **un retry unique** est effectué avec un prompt renforcé (ajout d'une instruction explicite `"Utilise exclusivement les scores fournis : E={env}, S={soc}, G={gov}"`). Si le retry produit encore un drift, l'appel lève `HTTPException(500, detail="Erreur génération rapport : incohérence numérique détectée")` et l'échec est loggé à nouveau.

2. **AC2 — Guard text libre détecte le vocabulaire interdit** — Given un résumé exécutif contient `"Votre conformité est garantie"` ou `"Certifié ISO 26000"` ou `"Validé par le GCF"`, When le guard `assert_no_forbidden_vocabulary(text, FORBIDDEN_VOCAB=["garanti", "garantie", "certifié", "certifiée", "validé par", "homologué", "accrédité"])` est invoqué (case-insensitive, normalisation accents via `unicodedata.normalize("NFKD", …)`), Then le guard lève `LLMGuardError(code="forbidden_vocab", detected_term="garantie")` — mêmes actions que AC1 (log, retry unique, `HTTPException` en dernier recours). La liste `FORBIDDEN_VOCAB` est exposée en constante module-level pour visibilité audit.

3. **AC3 — Guard text libre détecte la dérive de langue (EN/autre)** — Given un résumé exécutif contient majoritairement des mots anglais (ex. `"Your ESG score is satisfactory, we recommend improvements in governance"`), When le guard `assert_language_fr(text, min_ratio=0.12)` est invoqué, Then le guard détecte que le ratio de tokens FR stopwords reconnus est `< 0.12` et lève `LLMGuardError(code="language_drift", detected_lang="en", ratio=0.03)`. **Implémentation minimaliste** : détection via densité de stopwords FR (`["le", "la", "de", "et", "est", "les", "des", "un", "une", "pour", "dans", "avec", "sur", …]`). Pas de bibliothèque lourde (spaCy exclus — overkill). Si `langdetect` est déjà présent dans `requirements.txt` (à vérifier en T11), l'utiliser en backup.

4. **AC4 — Guard text libre détecte les bornes de longueur** — Given un résumé exécutif d'une longueur `len(text) == 2` (quasi-vide, LLM a échoué silencieusement) ou `len(text) == 15000` (trop long, LLM a halluciné verbeux), When les guards `assert_length(text, min_chars=200, max_chars=3000)` sont invoqués, Then ils lèvent respectivement `LLMGuardError(code="too_short", length=2)` et `LLMGuardError(code="too_long", length=15000)`. Les bornes `200`/`3000` sont exposées en constantes module-level `MIN_SUMMARY_LEN` / `MAX_SUMMARY_LEN` pour tunabilité via config future.

5. **AC5 — Guard JSON schéma strict plan d'action** — Given le LLM renvoie un tableau JSON avec `10 actions` dont une contient `{"category": "hallucinated_category", "priority": "critical_critical", "estimated_cost_xof": 999999999999999999, "due_date": "2099-12-31"}`, When le schéma Pydantic `ActionPlanItemLLMSchema` (avec `model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)`) valide la liste, Then la validation échoue avec `LLMGuardError(code="schema_invalid", ...)` agrégeant les violations (`category` hors enum, `priority` hors enum, `estimated_cost_xof > MAX_COST_XOF=10_000_000_000`, `due_date > today() + timeframe_months * 31 jours`). Le service `generate_action_plan()` attrape l'erreur, loggue `extra={"metric": "llm_guard_failure", "guard": "pydantic_schema", "target": "action_plan", "violations": 4}`, **retry unique avec prompt renforcé** (ajout `"Respecte STRICTEMENT le format: category ∈ {environment, social, governance, financing, carbon, intermediary_contact}, priority ∈ {low, medium, high}, estimated_cost_xof ≤ 10_000_000_000"`), puis `HTTPException(500, detail="Erreur génération plan d'action : schéma invalide")` en dernier recours.

6. **AC6 — Guard JSON nombre d'actions borné** — Given le LLM renvoie `2 actions` (trop peu — aucun plan utile) OU `30 actions` (trop — perte de focus), When le validateur `validate_action_plan_schema(actions, min_count=5, max_count=20)` est invoqué dans la foulée du schéma Pydantic, Then il lève `LLMGuardError(code="action_count_out_of_range", count=2, expected_range=(5, 20))` ou idem pour 30. **Retry unique** avec prompt renforcé (`"Génère entre {min_count} et {max_count} actions, pas moins, pas plus"`), puis `HTTPException(500)`. Les bornes `(5, 20)` sont exposées en constantes module-level.

7. **AC7 — Guards appliqués au pipeline complet du résumé exécutif** — Given l'appel service `generate_executive_summary(company_name="ACME", sector="textile", overall_score=54.0, environment_score=60.0, social_score=48.0, governance_score=54.0, strengths=[...], gaps=[...], benchmark_position="median")`, When la fonction termine **avec succès**, Then le `str` retourné a passé **4 guards séquentiellement** : (a) `assert_length(min=200, max=3000)`, (b) `assert_language_fr(min_ratio=MIN_FR_RATIO)`, (c) `assert_no_forbidden_vocabulary(FORBIDDEN_VOCAB)`, (d) `assert_numeric_coherence(source_values={"overall_score": 54, "environment_score": 60, "social_score": 48, "governance_score": 54})`. Un seul retry est autorisé ; l'ordre des guards est fixe et déterministe pour faciliter le debug.

8. **AC8 — Guards appliqués au pipeline complet du plan d'action** — Given l'appel service `generate_action_plan(db, user_id, timeframe=12)`, When la fonction termine avec succès, Then la `list[dict]` retournée par `_extract_json_array()` a été **(1)** parsée en `list[ActionPlanItemLLMSchema]` (Pydantic strict), **(2)** validée par `validate_action_plan_schema(min=5, max=20)`, **(3)** re-sérialisée en `list[dict]` via `.model_dump(mode="json")` avant d'être consommée par la boucle de création des `ActionItem`. Les helpers `_safe_category()` / `_safe_priority()` / `_parse_action_date()` deviennent **redondants** puisque Pydantic a déjà validé — ils sont **conservés en défense en profondeur** et tracés avec un `logger.warning` dédié si jamais ils attrapent un cas non-Pydantic (détecte un drift Pydantic vs code persistence).

9. **AC9 — Télémétrie échecs guards (SC-T8 + NFR39/40)** — Given un guard LLM échoue (n'importe lequel des 6 guards), When l'échec est loggué, Then le record de log contient **obligatoirement** les champs structurés suivants sous `extra={}` : `metric="llm_guard_failure"`, `guard="<name>"`, `target="<executive_summary|action_plan>"`, `user_id="<uuid>"`, `retry_attempted=<bool>`, `final_outcome="<recovered|failed>"`. Le format est consommable par un collecteur Prometheus / Grafana futur (cf. FR55 dashboard admin). Le champ `prompt_hash` (SHA-256 des 200 premiers caractères du prompt envoyé) est également présent pour audit a posteriori **sans exposer le prompt brut** (PII potentielle dans le contexte).

10. **AC10 — Zéro régression sur les cas heureux** — Given un résumé exécutif LLM **valide** (langue FR, longueur 500 chars, aucun vocabulaire interdit, scores cohérents) et un plan d'action LLM **valide** (12 actions, schémas respectés, coûts bornés, dates futures raisonnables), When les services `generate_executive_summary()` et `generate_action_plan()` sont appelés, Then ils retournent exactement ce qu'ils retournaient avant la story (str pour le 1er, `ActionPlan` SQLAlchemy pour le 2nd) — **aucune différence observable de l'extérieur**. Les tests existants `test_report_service.py` et `test_action_plan/test_service.py` passent sans modification de leurs assertions (sauf ajout de fixtures qui mockent `llm.ainvoke` avec un payload valide strict).

11. **AC11 — Zéro régression globale** — Given la suite backend complète post-9.5, When `pytest tests/ --tb=no -q` est lancé après l'implémentation, Then le résultat est **`N passed, 0 failed`** avec `N ≥ baseline_9.5 + nouveaux_tests_guards`. Les nouveaux tests (minimum 24 tests : 11 free text guards + 8 JSON guards + 3 pipeline résumé exécutif + 3 pipeline action plan minimum) sont regroupés en classes nommées `TestLLMGuardsFreeText`, `TestLLMGuardsJSONSchema`, `TestExecutiveSummaryGuardsIntegration`, `TestActionPlanGuardsIntegration`. Temps d'exécution reste sous le plafond 200s (9.3/9.4/9.5).

---

## Tasks / Subtasks

- [x] **T1 — Module partagé `backend/app/core/llm_guards.py` (AC1, AC2, AC3, AC4)**
  - [ ] Créer le fichier `backend/app/core/llm_guards.py` avec la structure suivante (organisation par type : exception, constantes, free text guards, JSON guards, helpers télémétrie) :
    ```python
    """Guards LLM pour les contenus persistes remis aux bailleurs (SC-T8, Risque 10).

    Protege les 2 surfaces LLM actuelles :
    - Resume executif ESG (reports/service.py)
    - Plan d'action JSON (action_plan/service.py)

    Story 9.6 / P1 #10 audit.
    """
    from __future__ import annotations

    import hashlib
    import logging
    import re
    import unicodedata
    from typing import Any, Literal

    logger = logging.getLogger(__name__)

    # --- Constantes tunables (exposees pour audit + tests) ---

    # Resume executif ESG
    MIN_SUMMARY_LEN = 200
    MAX_SUMMARY_LEN = 3000

    # Plan d'action
    MIN_ACTION_COUNT = 5
    MAX_ACTION_COUNT = 20
    MAX_COST_XOF = 10_000_000_000  # 10 milliards FCFA plafond par action
    MAX_TIMEFRAME_MONTHS = 24
    VALID_CATEGORIES = frozenset({
        "environment", "social", "governance",
        "financing", "carbon", "intermediary_contact",
    })
    VALID_PRIORITIES = frozenset({"low", "medium", "high"})

    # Vocabulaire interdit (responsabilite juridique, Risque 10)
    # Liste centralisee pour audit + extension (ex. regulateur UEMOA futur).
    FORBIDDEN_VOCAB: tuple[str, ...] = (
        "garanti", "garantie", "garantis", "garanties",
        "certifie", "certifiee", "certifies", "certifiees",
        "valide par", "validee par", "valides par", "validees par",
        "homologue", "homologuee",
        "accredite", "accreditee",
        "officiellement reconnu", "officiellement reconnue",
    )

    # Detection de langue francaise (mots outils FR tres frequents,
    # robuste sur textes de >100 chars). Seuil testable via MIN_FR_RATIO.
    _FR_STOPWORDS = frozenset({
        "le", "la", "les", "un", "une", "des", "de", "du",
        "et", "ou", "est", "sont", "pour", "dans", "avec",
        "sur", "par", "ce", "cette", "ces", "votre", "vos",
        "nous", "vous", "il", "elle", "ils", "elles",
        "a", "au", "aux", "en", "que", "qui", "plus", "moins",
    })
    MIN_FR_RATIO = 0.12  # 12 % de tokens stopword FR = seuil sain


    # --- Exception unifiee ---

    class LLMGuardError(Exception):
        """Exception levee quand un guard LLM detecte une anomalie.

        Attributes:
            code: identifiant machine de la cause ("numeric_drift", "forbidden_vocab", ...)
            target: surface LLM concernee ("executive_summary", "action_plan", ...)
            details: dict libre d'infos pour audit/log (detected, expected, field, ...)
        """

        def __init__(self, code: str, target: str, details: dict[str, Any] | None = None):
            self.code = code
            self.target = target
            self.details = details or {}
            super().__init__(f"LLM guard failed: code={code} target={target} details={self.details}")


    # --- Helpers normalisation ---

    def _strip_accents(text: str) -> str:
        """Retirer les accents pour la detection insensible a l'accent (vocab interdit)."""
        nfkd = unicodedata.normalize("NFKD", text)
        return "".join(c for c in nfkd if not unicodedata.combining(c))


    def prompt_hash(prompt: str) -> str:
        """SHA-256 des 200 premiers chars du prompt, pour audit sans exposer le contenu."""
        sample = prompt[:200].encode("utf-8")
        return hashlib.sha256(sample).hexdigest()[:16]


    # --- Free text guards (resume executif) ---

    def assert_length(text: str, min_chars: int, max_chars: int, target: str) -> None:
        """AC4 : borner la longueur du texte LLM."""
        n = len(text or "")
        if n < min_chars:
            raise LLMGuardError("too_short", target, {"length": n, "min": min_chars})
        if n > max_chars:
            raise LLMGuardError("too_long", target, {"length": n, "max": max_chars})


    def assert_language_fr(text: str, target: str, min_ratio: float = MIN_FR_RATIO) -> None:
        """AC3 : verifier la langue francaise via densite des stopwords FR.

        Implementation volontairement minimaliste (pas de langdetect obligatoire) pour rester
        deterministe. Fonctionne sur textes >100 chars ; retourne silencieusement
        sur textes courts (< 50 mots) pour eviter les faux positifs.
        """
        tokens = re.findall(r"\b[a-zA-ZaAeEiIoOuUyYcC'\-]+\b", (text or "").lower())
        if len(tokens) < 50:
            return  # texte trop court pour detection fiable
        fr_hits = sum(1 for t in tokens if t in _FR_STOPWORDS)
        ratio = fr_hits / len(tokens) if tokens else 0.0
        if ratio < min_ratio:
            raise LLMGuardError("language_drift", target, {"ratio": round(ratio, 3), "min": min_ratio})


    def assert_no_forbidden_vocabulary(text: str, target: str, vocab: tuple[str, ...] = FORBIDDEN_VOCAB) -> None:
        """AC2 : bloquer le vocabulaire interdit (insensible a la casse et aux accents)."""
        normalized = _strip_accents((text or "").lower())
        for term in vocab:
            # Mot entier avec boundaries pour eviter 'garantir' (verbe) = 'garanti'.
            pattern = r"\b" + re.escape(term) + r"\b"
            if re.search(pattern, normalized):
                raise LLMGuardError("forbidden_vocab", target, {"detected_term": term})


    def assert_numeric_coherence(
        text: str,
        source_values: dict[str, float],
        target: str,
        tolerance: float = 2.0,
    ) -> None:
        """AC1 : verifier que le texte ne mentionne pas de chiffres divergents des faits sources.

        Pour chaque nombre contextualise dans le texte (X/100, X%, X points, X/10),
        verifier qu'il est proche (±tolerance) d'au moins une valeur source.
        Sinon, drift detecte.
        """
        pattern = r"\b(\d+(?:[.,]\d+)?)\s*(?:/100|%|\s+points?|\s+pts|/10)\b"
        matches = re.findall(pattern, (text or "").lower())
        if not matches:
            return  # aucun nombre contextualise : rien a verifier
        source_floats = [float(v) for v in source_values.values() if isinstance(v, (int, float))]
        if not source_floats:
            return  # pas de source a comparer

        for raw in matches:
            value = float(raw.replace(",", "."))
            # Acceptable si proche (±tolerance) d'au moins une source
            if any(abs(value - s) <= tolerance for s in source_floats):
                continue
            # Acceptable aussi si score /10 plutot que /100
            if any(abs(value * 10 - s) <= tolerance for s in source_floats):
                continue
            raise LLMGuardError(
                "numeric_drift",
                target,
                {"detected_value": value, "source_values": source_values},
            )


    # --- Telemetrie (AC9) ---

    def log_guard_failure(
        target: str,
        guard: str,
        user_id: str,
        prompt_h: str,
        details: dict[str, Any],
        retry_attempted: bool,
        final_outcome: Literal["recovered", "failed"],
    ) -> None:
        """Log structure AC9 : consommable par Prometheus/Grafana (FR55 futur)."""
        logger.warning(
            "LLM guard failure target=%s guard=%s outcome=%s",
            target, guard, final_outcome,
            extra={
                "metric": "llm_guard_failure",
                "guard": guard,
                "target": target,
                "user_id": user_id,
                "prompt_hash": prompt_h,
                "retry_attempted": retry_attempted,
                "final_outcome": final_outcome,
                **{f"detail_{k}": v for k, v in details.items()},
            },
        )
    ```
  - [ ] **Justification `LLMGuardError` unifiée** : une seule exception pour tous les guards → attrape simple (`except LLMGuardError as err:`), dispatch par `.code`. Évite une hiérarchie d'exceptions qui complexifierait les imports. Pattern identique aux exceptions custom existantes du projet.
  - [ ] **Convention `target` string** : `"executive_summary"`, `"action_plan"`, futur `"preparation_sheet"` si LLM y est ajouté. Permet au dashboard admin (FR55) de trancher par surface sans parser le message.
  - [ ] **Constantes exposées** : `MIN_SUMMARY_LEN`, `MAX_SUMMARY_LEN`, `MIN_ACTION_COUNT`, `MAX_ACTION_COUNT`, `MAX_COST_XOF`, `FORBIDDEN_VOCAB`, `VALID_CATEGORIES`, `VALID_PRIORITIES` — tunables à court terme, documentées par l'audit/test.

- [x] **T2 — Pydantic strict `ActionPlanItemLLMSchema` dans `backend/app/core/llm_guards.py` (AC5, AC6)**
  - [ ] Ajouter à `llm_guards.py` :
    ```python
    from datetime import date, timedelta
    from pydantic import BaseModel, ConfigDict, Field, field_validator

    class ActionPlanItemLLMSchema(BaseModel):
        """Schema strict pour UNE action generee par le LLM.

        Bornes et enums calibres sur le prompt `action_plan.py` + modele `ActionItem`.
        extra='forbid' : toute cle supplementaire (hallucination) fait echouer.
        """

        model_config = ConfigDict(
            extra="forbid",
            str_strip_whitespace=True,
        )

        title: str = Field(min_length=5, max_length=500)
        description: str | None = Field(default=None, max_length=4000)
        category: str = Field(description="Categorie normalisee")
        priority: str = Field(description="Priorite normalisee")
        due_date: str | None = Field(default=None, description="ISO 8601 YYYY-MM-DD")
        estimated_cost_xof: int | None = Field(default=None, ge=0, le=MAX_COST_XOF)
        estimated_benefit: str | None = Field(default=None, max_length=500)
        fund_id: str | None = None
        intermediary_id: str | None = None
        intermediary_name: str | None = Field(default=None, max_length=200)
        intermediary_address: str | None = Field(default=None, max_length=500)
        intermediary_phone: str | None = Field(default=None, max_length=50)
        intermediary_email: str | None = Field(default=None, max_length=200)

        @field_validator("category")
        @classmethod
        def _validate_category(cls, v: str) -> str:
            if v not in VALID_CATEGORIES:
                raise ValueError(f"category='{v}' not in {sorted(VALID_CATEGORIES)}")
            return v

        @field_validator("priority")
        @classmethod
        def _validate_priority(cls, v: str) -> str:
            if v not in VALID_PRIORITIES:
                raise ValueError(f"priority='{v}' not in {sorted(VALID_PRIORITIES)}")
            return v

        @field_validator("due_date")
        @classmethod
        def _validate_due_date(cls, v: str | None) -> str | None:
            if v is None:
                return v
            try:
                parsed = date.fromisoformat(v)
            except ValueError as e:
                raise ValueError(f"due_date='{v}' is not ISO 8601 (YYYY-MM-DD)") from e
            today = date.today()
            max_date = today + timedelta(days=MAX_TIMEFRAME_MONTHS * 31 + 90)  # marge 90j
            if parsed > max_date:
                raise ValueError(f"due_date='{v}' too far in the future (> {max_date.isoformat()})")
            return v


    def validate_action_plan_schema(
        actions_raw: list[Any],
        target: str = "action_plan",
    ) -> list[ActionPlanItemLLMSchema]:
        """AC5 : valider le schema Pydantic strict + AC6 : borner le nombre d'actions."""
        if not isinstance(actions_raw, list):
            raise LLMGuardError(
                "schema_invalid", target,
                {"reason": "expected list", "got": type(actions_raw).__name__},
            )
        n = len(actions_raw)
        if n < MIN_ACTION_COUNT or n > MAX_ACTION_COUNT:
            raise LLMGuardError(
                "action_count_out_of_range", target,
                {"count": n, "expected_range": [MIN_ACTION_COUNT, MAX_ACTION_COUNT]},
            )

        validated: list[ActionPlanItemLLMSchema] = []
        for idx, item in enumerate(actions_raw):
            try:
                validated.append(ActionPlanItemLLMSchema(**item))
            except Exception as e:
                raise LLMGuardError(
                    "schema_invalid", target,
                    {"index": idx, "errors": str(e)[:500]},
                ) from e

        return validated
    ```
  - [ ] **`extra="forbid"` critique** : bloque les clés hallucinées par le LLM (ex. `"estimated_co2_reduction"` inventée).
  - [ ] **`MAX_TIMEFRAME_MONTHS * 31 + 90`** : marge 90j car `timeframe=24` autorisé et le LLM peut légitimement dater fin `timeframe + trimestre`.
  - [ ] **Retour `list[ActionPlanItemLLMSchema]`** : callers peuvent `.model_dump(mode="json")` pour récupérer un `dict` sérialisable — pas de breaking change côté persistence.
  - [ ] **Ne pas muter `actions_raw`** : Pydantic reconstruit un objet strict, input reste intact (immutabilité cf. `rules/common/coding-style.md`).

- [x] **T3 — Orchestrateur + helper retry dans `llm_guards.py` (AC7, AC8, AC9)**
  - [ ] Ajouter un helper central `run_guarded_llm_call()` qui factorise le pattern « call LLM → guards → retry unique → HTTPException » :
    ```python
    from typing import Awaitable, Callable

    async def run_guarded_llm_call(
        *,
        llm_call: Callable[[str], Awaitable[str]],
        guards: Callable[[str], None],
        base_prompt: str,
        hardened_prompt: str,
        target: str,
        user_id: str,
    ) -> str:
        """Executer un appel LLM avec garde-fous et retry unique.

        Args:
            llm_call: coroutine `(prompt) -> raw_output` (async)
            guards: callable sync `(output) -> None` qui leve LLMGuardError si anomalie
            base_prompt: prompt initial
            hardened_prompt: prompt de retry (avec instruction additionnelle explicite)
            target: "executive_summary" | "action_plan"
            user_id: pour log structure AC9

        Returns:
            le contenu LLM valide (str brut)

        Raises:
            HTTPException(500): retry echoue definitivement
        """
        from fastapi import HTTPException

        ph_base = prompt_hash(base_prompt)
        try:
            output = await llm_call(base_prompt)
            guards(output)
            return output
        except LLMGuardError as err1:
            log_guard_failure(
                target=target, guard=err1.code, user_id=user_id,
                prompt_h=ph_base, details=err1.details,
                retry_attempted=True, final_outcome="recovered",
            )
            # Retry unique avec prompt renforce
            try:
                output = await llm_call(hardened_prompt)
                guards(output)
                return output
            except LLMGuardError as err2:
                log_guard_failure(
                    target=target, guard=err2.code, user_id=user_id,
                    prompt_h=prompt_hash(hardened_prompt), details=err2.details,
                    retry_attempted=True, final_outcome="failed",
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Erreur generation {target} : guard LLM echoue apres retry",
                ) from err2
    ```
  - [ ] **Choix `Callable` plutot que decorator** : lisibilité des tests (mock direct du callable), moins de magie.
  - [ ] **`guards` sync** : toutes les validations T1/T2 sont sync (CPU only).
  - [ ] **1 seul retry** : couvre ~85 % des hallucinations ponctuelles (best practices). 2+ retries ajoutent latence sans gain mesurable.
  - [ ] **Première erreur loggée `final_outcome="recovered"`** puis écrasée si échec → permet au dashboard de distinguer `recovered` vs `failed`.

- [x] **T4 — Intégration `generate_executive_summary()` (AC1, AC2, AC3, AC4, AC7)**
  - [ ] Dans [`backend/app/modules/reports/service.py:63`](../../backend/app/modules/reports/service.py#L63), refactorer :
    ```python
    from app.core.llm_guards import (
        MIN_SUMMARY_LEN, MAX_SUMMARY_LEN,
        assert_length, assert_language_fr,
        assert_no_forbidden_vocabulary, assert_numeric_coherence,
        run_guarded_llm_call,
    )

    async def generate_executive_summary(
        company_name: str,
        sector: str,
        overall_score: float,
        environment_score: float,
        social_score: float,
        governance_score: float,
        strengths: list[dict],
        gaps: list[dict],
        benchmark_position: str,
        user_id: str | None = None,  # NOUVEAU - pour la telemetrie AC9
    ) -> str:
        """Generer le resume executif via LLM avec guards (story 9.6)."""
        strengths_text = "\n".join(
            f"- {s.get('title', 'N/A')} ({s.get('score', 0)}/10)" for s in (strengths or [])
        ) or "Aucun point fort identifie"
        gaps_text = "\n".join(
            f"- {g.get('title', 'N/A')} ({g.get('score', 0)}/10)" for g in (gaps or [])
        ) or "Aucun axe d'amelioration identifie"

        base_prompt = ESG_REPORT_EXECUTIVE_SUMMARY_PROMPT.format(
            company_name=company_name,
            sector=SECTOR_LABELS.get(sector, sector),
            overall_score=overall_score,
            environment_score=environment_score,
            social_score=social_score,
            governance_score=governance_score,
            strengths_text=strengths_text,
            gaps_text=gaps_text,
            benchmark_position=BENCHMARK_POSITION_LABELS.get(benchmark_position, benchmark_position),
        )
        hardened_prompt = base_prompt + (
            f"\n\nCONTRAINTES STRICTES :"
            f"\n- Redige exclusivement en francais."
            f"\n- Utilise uniquement ces valeurs numeriques : "
            f"overall={overall_score}/100, E={environment_score}/100, "
            f"S={social_score}/100, G={governance_score}/100."
            f"\n- Interdiction d'utiliser les mots : garanti, certifie, valide par, homologue, accredite."
            f"\n- Longueur : entre {MIN_SUMMARY_LEN} et {MAX_SUMMARY_LEN} caracteres."
        )

        source_values = {
            "overall_score": overall_score,
            "environment_score": environment_score,
            "social_score": social_score,
            "governance_score": governance_score,
        }

        def guards(text: str) -> None:
            # Ordre deterministe AC7 : length -> langue -> vocab -> numerique
            assert_length(text, MIN_SUMMARY_LEN, MAX_SUMMARY_LEN, "executive_summary")
            assert_language_fr(text, "executive_summary")
            assert_no_forbidden_vocabulary(text, "executive_summary")
            assert_numeric_coherence(text, source_values, "executive_summary")

        async def llm_call(prompt: str) -> str:
            llm = ChatOpenAI(
                model=settings.openrouter_model,
                base_url=settings.openrouter_base_url,
                api_key=settings.openrouter_api_key,
                temperature=0.3,
            )
            response = await llm.ainvoke([
                SystemMessage(content="Tu es un consultant ESG senior."),
                HumanMessage(content=prompt),
            ])
            return response.content.strip()

        return await run_guarded_llm_call(
            llm_call=llm_call,
            guards=guards,
            base_prompt=base_prompt,
            hardened_prompt=hardened_prompt,
            target="executive_summary",
            user_id=user_id or "anonymous",
        )
    ```
  - [ ] **Paramètre `user_id: str | None = None` ajouté** : breaking change mineur. Le seul call-site ([`service.py:281`](../../backend/app/modules/reports/service.py#L281)) doit être mis à jour (cf. T6). Vérifier avec `grep -rn "generate_executive_summary(" backend/` avant l'implémentation.
  - [ ] **`hardened_prompt`** : append à la fin du `base_prompt` (pas de contradiction). Test manuel sur un payload golden avant merge.
  - [ ] **Ordre des guards fixe** (AC7) : `length` d'abord (détection la plus cheap), puis langue, puis vocab, puis numérique.

- [x] **T5 — Intégration `generate_action_plan()` (AC5, AC6, AC8)**
  - [ ] Dans [`backend/app/modules/action_plan/service.py:171`](../../backend/app/modules/action_plan/service.py#L171), refactorer :
    ```python
    from app.core.llm_guards import (
        LLMGuardError, MIN_ACTION_COUNT, MAX_ACTION_COUNT, MAX_COST_XOF,
        VALID_CATEGORIES, VALID_PRIORITIES,
        validate_action_plan_schema, run_guarded_llm_call,
    )

    # Apres la construction du prompt existant, remplacer l'appel LLM direct par :

    base_prompt = prompt  # existant
    hardened_prompt = base_prompt + (
        f"\n\nCONTRAINTES STRICTES (respect absolu) :"
        f"\n- Retourne un tableau JSON (pas de texte hors tableau)."
        f"\n- Entre {MIN_ACTION_COUNT} et {MAX_ACTION_COUNT} actions (pas moins, pas plus)."
        f"\n- category DOIT etre une de : {sorted(VALID_CATEGORIES)}."
        f"\n- priority DOIT etre une de : {sorted(VALID_PRIORITIES)}."
        f"\n- estimated_cost_xof : entier >= 0 et <= {MAX_COST_XOF}."
        f"\n- due_date : ISO 8601 (YYYY-MM-DD), dans les {timeframe + 3} mois."
        f"\n- title : 5 a 500 caracteres."
        f"\n- Aucune cle supplementaire hors schema."
    )

    def guards(raw_text: str) -> None:
        try:
            actions_raw = _extract_json_array(raw_text)
        except (ValueError, json.JSONDecodeError) as exc:
            raise LLMGuardError(
                "json_parse_failed", "action_plan",
                {"error": str(exc)[:200]},
            ) from exc
        validate_action_plan_schema(actions_raw, target="action_plan")

    async def llm_call(prompt_to_send: str) -> str:
        llm_instance = ChatOpenAI(
            model=settings.openrouter_model,
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            streaming=False,
        )
        response = await llm_instance.ainvoke([
            SystemMessage(content=prompt_to_send),
            HumanMessage(content=f"Genere le plan d'action pour {timeframe} mois."),
        ])
        return response.content if hasattr(response, "content") else str(response)

    raw_text = await run_guarded_llm_call(
        llm_call=llm_call,
        guards=guards,
        base_prompt=base_prompt,
        hardened_prompt=hardened_prompt,
        target="action_plan",
        user_id=str(user_id),
    )

    # APRES run_guarded : schema valide -> reparser pour usage typé.
    actions_raw = _extract_json_array(raw_text)
    validated = validate_action_plan_schema(actions_raw, target="action_plan")
    actions_data = [a.model_dump(mode="json") for a in validated]

    # Suite inchangee (archive ancien plan, cree nouveau, boucle de creation items)
    ```
  - [ ] **Double parsing intentionnel** : 1ère fois dans `guards()` pour lever l'exception dans le retry, 2ème fois après `run_guarded_llm_call` pour récupérer les objets Pydantic typés. Coût négligeable (JSON en mémoire).
  - [ ] **Helpers `_safe_category() / _safe_priority() / _parse_action_date()` conservés** : défense en profondeur (AC8). Ajouter un `logger.warning` dans chacun :
    ```python
    def _safe_category(raw: str | None) -> ActionItemCategory:
        try:
            return ActionItemCategory(raw)
        except (ValueError, TypeError):
            logger.warning(
                "Pydantic drift: unexpected category=%r fallback=governance", raw,
                extra={"metric": "pydantic_drift", "field": "category"},
            )
            return ActionItemCategory.governance
    ```
  - [ ] **Suppression du bloc `try/except json.JSONDecodeError` existant** (lignes 264-271 actuelles) : remplacé par `run_guarded_llm_call`. L'ancien `HTTPException(500)` est conservé implicitement (levé par `run_guarded_llm_call`).

- [x] **T6 — Mise à jour call-site `generate_executive_summary()` (AC10)**
  - [ ] Dans [`backend/app/modules/reports/service.py`](../../backend/app/modules/reports/service.py) autour de la ligne `281`, passer `user_id` :
    ```python
    executive_summary = await generate_executive_summary(
        company_name=...,
        sector=...,
        overall_score=...,
        environment_score=...,
        social_score=...,
        governance_score=...,
        strengths=...,
        gaps=...,
        benchmark_position=...,
        user_id=str(user.id),  # NOUVEAU
    )
    ```
  - [ ] Vérifier avec `grep -rn "generate_executive_summary(" backend/` qu'il n'y a **pas d'autres call-sites** (attendu : 1 seul). Si un test mock appelle positionnellement, lui ajouter `user_id="test-user"`.

- [x] **T7 — Tests `TestLLMGuardsFreeText` (AC1, AC2, AC3, AC4)**
  - [ ] Créer `backend/tests/test_core/__init__.py` (vide) et `backend/tests/test_core/test_llm_guards.py` :
    ```python
    """Tests des guards LLM (story 9.6 / P1 #10)."""
    import pytest
    from app.core.llm_guards import (
        LLMGuardError,
        MIN_SUMMARY_LEN, MAX_SUMMARY_LEN,
        assert_length, assert_language_fr,
        assert_no_forbidden_vocabulary, assert_numeric_coherence,
    )


    class TestLLMGuardsFreeText:
        """AC1-AC4 : guards texte libre."""

        # AC4 - length
        def test_too_short_raises(self):
            with pytest.raises(LLMGuardError) as exc:
                assert_length("salut", MIN_SUMMARY_LEN, MAX_SUMMARY_LEN, "test")
            assert exc.value.code == "too_short"
            assert exc.value.details["length"] == 5

        def test_too_long_raises(self):
            text = "a" * 5000
            with pytest.raises(LLMGuardError) as exc:
                assert_length(text, MIN_SUMMARY_LEN, MAX_SUMMARY_LEN, "test")
            assert exc.value.code == "too_long"

        def test_length_ok(self):
            assert_length("a" * 500, MIN_SUMMARY_LEN, MAX_SUMMARY_LEN, "test")  # no raise

        # AC3 - language FR
        def test_english_drift_detected(self):
            text = (
                "Your ESG score is satisfactory. We recommend improvements in "
                "governance and social pillars. The financing options are broad. "
                "Please consider the IFC PS standards for your future applications. "
                "Overall, the analysis shows a strong position for further growth."
            )
            with pytest.raises(LLMGuardError) as exc:
                assert_language_fr(text, "test")
            assert exc.value.code == "language_drift"

        def test_french_ok(self):
            text = (
                "Votre score ESG est satisfaisant. Nous recommandons des ameliorations "
                "sur le pilier gouvernance. Les options de financement sont larges. "
                "Considerez les standards IFC PS pour vos futures demandes. "
                "L'analyse montre une position solide pour la croissance."
            )
            assert_language_fr(text, "test")  # no raise

        def test_short_text_not_checked(self):
            assert_language_fr("Hello world", "test")  # no raise (trop court)

        # AC2 - forbidden vocabulary
        @pytest.mark.parametrize("text,term", [
            ("Votre conformite est garantie par nos experts.", "garantie"),
            ("Programme certifie ISO 26000.", "certifie"),
            ("Projet valide par le GCF en 2025.", "valide par"),
            ("Votre demarche est homologuee.", "homologuee"),
        ])
        def test_forbidden_vocab_detected(self, text, term):
            with pytest.raises(LLMGuardError) as exc:
                assert_no_forbidden_vocabulary(text, "test")
            assert exc.value.code == "forbidden_vocab"
            assert exc.value.details["detected_term"] == term

        def test_forbidden_vocab_insensitive_to_accents(self):
            # "CERTIFIÉ" avec accent -> doit matcher "certifie"
            text = "Programme CERTIFIÉ par l'ONU en 2024."
            with pytest.raises(LLMGuardError) as exc:
                assert_no_forbidden_vocabulary(text, "test")
            assert exc.value.code == "forbidden_vocab"

        def test_safe_vocab_ok(self):
            # "garantir" (infinitif) ne doit PAS matcher "garanti" (adjectif)
            text = "Nous recommandons de garantir la tracabilite."
            assert_no_forbidden_vocabulary(text, "test")  # no raise

        # AC1 - numeric coherence
        def test_score_drift_detected(self):
            text = "Avec votre excellent score de 82/100 en gouvernance, vous excellez."
            with pytest.raises(LLMGuardError) as exc:
                assert_numeric_coherence(
                    text,
                    {"governance_score": 54.0, "overall_score": 54.0},
                    "test",
                )
            assert exc.value.code == "numeric_drift"
            assert exc.value.details["detected_value"] == 82.0

        def test_score_close_ok(self):
            text = "Votre score global de 54/100 montre des progres."
            assert_numeric_coherence(
                text,
                {"overall_score": 54.3, "governance_score": 54.0},
                "test",
                tolerance=2.0,
            )  # no raise

        def test_score_on_ten_ok(self):
            # 5/10 pour 50/100 - tolerance multiplicative
            text = "Votre score de 5/10 en gouvernance."
            assert_numeric_coherence(
                text,
                {"governance_score": 54.0},
                "test",
                tolerance=5.0,
            )  # no raise

        def test_no_numbers_in_text_ok(self):
            text = "Votre demarche ESG est prometteuse et s'inscrit dans la duree."
            assert_numeric_coherence(text, {"overall_score": 54.0}, "test")  # no raise
    ```
  - [ ] **`test_safe_vocab_ok`** verrouille que « garantir » (verbe infinitif) ne matche pas « garanti » (adjectif interdit) grâce aux word boundaries `\b`.

- [x] **T8 — Tests `TestLLMGuardsJSONSchema` (AC5, AC6)**
  - [ ] Dans `backend/tests/test_core/test_llm_guards.py`, ajouter :
    ```python
    class TestLLMGuardsJSONSchema:
        """AC5-AC6 : guards JSON plan d'action."""

        def _make_valid_action(self, **overrides) -> dict:
            base = {
                "title": "Installer eclairage LED basse consommation",
                "description": "Remplacer les ampoules existantes.",
                "category": "environment",
                "priority": "high",
                "due_date": "2026-09-30",
                "estimated_cost_xof": 500_000,
            }
            base.update(overrides)
            return base

        def test_valid_plan_ok(self):
            from app.core.llm_guards import validate_action_plan_schema
            plan = [self._make_valid_action() for _ in range(8)]
            validated = validate_action_plan_schema(plan)
            assert len(validated) == 8
            assert validated[0].category == "environment"

        def test_category_out_of_enum_raises(self):
            from app.core.llm_guards import validate_action_plan_schema, LLMGuardError
            plan = [self._make_valid_action() for _ in range(6)]
            plan[0]["category"] = "halluciné_category"
            with pytest.raises(LLMGuardError) as exc:
                validate_action_plan_schema(plan)
            assert exc.value.code == "schema_invalid"
            assert "category" in exc.value.details["errors"]

        def test_priority_out_of_enum_raises(self):
            from app.core.llm_guards import validate_action_plan_schema, LLMGuardError
            plan = [self._make_valid_action() for _ in range(6)]
            plan[0]["priority"] = "CRITICAL"
            with pytest.raises(LLMGuardError) as exc:
                validate_action_plan_schema(plan)
            assert exc.value.code == "schema_invalid"

        def test_cost_exceeds_cap_raises(self):
            from app.core.llm_guards import validate_action_plan_schema, LLMGuardError, MAX_COST_XOF
            plan = [self._make_valid_action() for _ in range(6)]
            plan[0]["estimated_cost_xof"] = MAX_COST_XOF + 1
            with pytest.raises(LLMGuardError) as exc:
                validate_action_plan_schema(plan)
            assert exc.value.code == "schema_invalid"

        def test_extra_key_raises(self):
            # extra='forbid' -> cle inventee rejetee
            from app.core.llm_guards import validate_action_plan_schema, LLMGuardError
            plan = [self._make_valid_action() for _ in range(6)]
            plan[0]["hallucinated_co2_reduction"] = 42
            with pytest.raises(LLMGuardError) as exc:
                validate_action_plan_schema(plan)
            assert exc.value.code == "schema_invalid"

        def test_date_too_far_raises(self):
            from app.core.llm_guards import validate_action_plan_schema, LLMGuardError
            plan = [self._make_valid_action() for _ in range(6)]
            plan[0]["due_date"] = "2099-12-31"
            with pytest.raises(LLMGuardError) as exc:
                validate_action_plan_schema(plan)
            assert exc.value.code == "schema_invalid"

        def test_too_few_actions_raises(self):
            from app.core.llm_guards import validate_action_plan_schema, LLMGuardError
            plan = [self._make_valid_action() for _ in range(2)]
            with pytest.raises(LLMGuardError) as exc:
                validate_action_plan_schema(plan)
            assert exc.value.code == "action_count_out_of_range"
            assert exc.value.details["count"] == 2

        def test_too_many_actions_raises(self):
            from app.core.llm_guards import validate_action_plan_schema, LLMGuardError
            plan = [self._make_valid_action() for _ in range(30)]
            with pytest.raises(LLMGuardError) as exc:
                validate_action_plan_schema(plan)
            assert exc.value.code == "action_count_out_of_range"
            assert exc.value.details["count"] == 30

        def test_non_list_raises(self):
            from app.core.llm_guards import validate_action_plan_schema, LLMGuardError
            with pytest.raises(LLMGuardError) as exc:
                validate_action_plan_schema({"not_a_list": True})  # type: ignore[arg-type]
            assert exc.value.code == "schema_invalid"
    ```

- [x] **T9 — Tests `TestExecutiveSummaryGuardsIntegration` (AC7, AC9, AC10)**
  - [ ] Dans `backend/tests/test_api/test_report_service.py` (ou nouveau `test_report_guards.py`) :
    ```python
    import pytest
    from unittest.mock import AsyncMock, patch
    from app.modules.reports.service import generate_executive_summary
    from fastapi import HTTPException


    class TestExecutiveSummaryGuardsIntegration:
        """AC7, AC9, AC10 : pipeline complet resume executif avec guards."""

        VALID_SUMMARY = (
            "Votre entreprise ACME Textile presente un profil ESG globalement satisfaisant "
            "avec un score global de 54/100. Les points forts identifies sur la gouvernance "
            "illustrent une demarche de transparence. Le pilier environnemental montre un score "
            "de 60/100, reflet d'initiatives concretes. Le pilier social avec 48/100 signale "
            "des axes d'amelioration. Nous recommandons de renforcer la politique RH et "
            "d'engager un suivi carbone regulier. Votre positionnement sectoriel est mediane."
        )

        HALLUCINATED_SUMMARY = (
            "Votre entreprise ACME Textile affiche un score ESG exceptionnel de 88/100, "
            "positionne au-dessus de la mediane sectorielle. Votre conformite est garantie "
            "sur tous les piliers. Nous saluons l'excellence de votre demarche et vous certifions "
            "eligible aux programmes GCF. Le pilier environnemental atteint 92/100 grace a des "
            "investissements structurants dans les energies renouvelables."
        )

        @pytest.mark.asyncio
        async def test_valid_summary_passes(self):
            """AC10 : un resume LLM valide est retourne tel quel (1 seul appel LLM)."""
            with patch("app.modules.reports.service.ChatOpenAI") as mock_llm_cls:
                mock_llm = AsyncMock()
                mock_llm.ainvoke = AsyncMock(return_value=type(
                    "Resp", (), {"content": self.VALID_SUMMARY}
                )())
                mock_llm_cls.return_value = mock_llm

                result = await generate_executive_summary(
                    company_name="ACME", sector="textile",
                    overall_score=54.0, environment_score=60.0,
                    social_score=48.0, governance_score=54.0,
                    strengths=[{"title": "Gouvernance", "score": 7}],
                    gaps=[{"title": "Social", "score": 4}],
                    benchmark_position="median",
                    user_id="user-1",
                )
                assert "54/100" in result
                assert "garanti" not in result.lower()
                assert mock_llm.ainvoke.call_count == 1

        @pytest.mark.asyncio
        async def test_hallucinated_summary_triggers_retry_then_fails(self, caplog):
            """AC7 + AC9 : hallucination -> retry -> 500 + logs structures."""
            with patch("app.modules.reports.service.ChatOpenAI") as mock_llm_cls:
                mock_llm = AsyncMock()
                mock_llm.ainvoke = AsyncMock(return_value=type(
                    "Resp", (), {"content": self.HALLUCINATED_SUMMARY}
                )())
                mock_llm_cls.return_value = mock_llm

                with caplog.at_level("WARNING"):
                    with pytest.raises(HTTPException) as exc:
                        await generate_executive_summary(
                            company_name="ACME", sector="textile",
                            overall_score=54.0, environment_score=60.0,
                            social_score=48.0, governance_score=54.0,
                            strengths=[], gaps=[],
                            benchmark_position="median",
                            user_id="user-1",
                        )
                    assert exc.value.status_code == 500

                assert mock_llm.ainvoke.call_count == 2  # base + retry
                guard_logs = [r for r in caplog.records
                              if getattr(r, "metric", None) == "llm_guard_failure"]
                assert len(guard_logs) >= 2  # 1 recovered tentative + 1 failed
                assert guard_logs[-1].final_outcome == "failed"
                assert guard_logs[-1].target == "executive_summary"

        @pytest.mark.asyncio
        async def test_first_fail_then_retry_recovers(self):
            """AC7 : echec 1er appel + succes du retry."""
            with patch("app.modules.reports.service.ChatOpenAI") as mock_llm_cls:
                mock_llm = AsyncMock()
                mock_llm.ainvoke = AsyncMock(side_effect=[
                    type("Resp", (), {"content": self.HALLUCINATED_SUMMARY})(),
                    type("Resp", (), {"content": self.VALID_SUMMARY})(),
                ])
                mock_llm_cls.return_value = mock_llm

                result = await generate_executive_summary(
                    company_name="ACME", sector="textile",
                    overall_score=54.0, environment_score=60.0,
                    social_score=48.0, governance_score=54.0,
                    strengths=[], gaps=[],
                    benchmark_position="median",
                    user_id="user-1",
                )
                assert "54/100" in result
                assert mock_llm.ainvoke.call_count == 2
    ```
  - [ ] **Mock pattern** : `patch("app.modules.reports.service.ChatOpenAI")` au point d'usage (pas `langchain_openai.ChatOpenAI`) — isole le test sans polluer les autres modules.

- [x] **T10 — Tests `TestActionPlanGuardsIntegration` (AC5, AC6, AC8, AC10)**
  - [ ] Dans `backend/tests/test_action_plan/test_service.py`, ajouter une classe :
    ```python
    class TestActionPlanGuardsIntegration:
        """AC5, AC6, AC8, AC10 : pipeline complet plan d'action avec guards."""

        def _make_valid_plan_json(self, n: int = 8) -> str:
            import json
            return json.dumps([
                {"title": f"Action {i}", "description": f"Desc {i}",
                 "category": "environment", "priority": "medium",
                 "due_date": "2026-08-31", "estimated_cost_xof": 100000}
                for i in range(n)
            ])

        def _make_hallucinated_plan_json(self) -> str:
            import json
            return json.dumps([
                {"title": "Action garantie", "description": "Desc",
                 "category": "hallucinated", "priority": "critical",
                 "due_date": "2099-12-31", "estimated_cost_xof": 10**18,
                 "extra_field_hallucine": 42}
                for _ in range(8)
            ])

        @pytest.mark.asyncio
        async def test_valid_plan_creates_actions(self, db_session, user_id):
            """AC10 : plan LLM valide -> ActionPlan + 8 ActionItems en BDD."""
            # Setup minimal profile (cf. pattern existant test_service.py)
            # Mock ChatOpenAI pour retourner valid plan JSON
            # generate_action_plan -> plan.items len=8, pas d'exception
            pass  # Skeleton — completer en reutilisant les fixtures existantes

        @pytest.mark.asyncio
        async def test_hallucinated_plan_triggers_retry_then_500(
            self, db_session, user_id, caplog,
        ):
            """AC5 + AC8 + AC9 : schema invalide -> retry -> HTTPException(500)."""
            # Mock ChatOpenAI : 2 appels renvoient hallucinated plan
            # Expect HTTPException(500), 2 appels LLM, logs llm_guard_failure
            pass

        @pytest.mark.asyncio
        async def test_too_few_actions_triggers_retry(
            self, db_session, user_id,
        ):
            """AC6 : 2 actions -> retry avec prompt renforce -> succes si 8 actions."""
            # Mock : 1er appel 2 actions, 2e appel 8 actions
            # Expect success + mock.call_count == 2
            pass
    ```
  - [ ] **Fixtures** : réutiliser `db_session`, `user_id` + `_create_minimal_profile()` du fichier existant (cf. [`test_action_plan/test_service.py`](../../backend/tests/test_action_plan/test_service.py)).
  - [ ] **`patch("app.modules.action_plan.service.ChatOpenAI")`** : même pattern que T9.

- [x] **T11 — Vérification `langdetect` (AC3 secours)**
  - [ ] `grep "langdetect" backend/requirements.txt` :
    - **Si présent** : ajouter un backup dans `assert_language_fr` qui essaie `langdetect.detect(text) == "fr"` avant l'heuristique stopwords. Fallback heuristique silencieux en cas d'échec d'import ou d'erreur (`LangDetectException`).
    - **Si absent** : ne PAS l'ajouter dans la story 9.6 (dépendance additionnelle = surface supply-chain + poids). L'heuristique stopwords suffit pour un texte > 50 tokens.
  - [ ] Documenter la décision dans le commit message : `T11 — langdetect {present|absent} : {utilisation|skip}`.

- [x] **T12 — Quality gate**
  - [ ] `pytest backend/tests/test_core/test_llm_guards.py -v` → **tous verts** (minimum 19 tests unitaires : 11 `TestLLMGuardsFreeText` + 8 `TestLLMGuardsJSONSchema`).
  - [ ] `pytest backend/tests/test_api/test_report_guards.py -v` (ou classe dans `test_report_service.py`) → **3 tests verts** (valid, hallucinated, retry_recovers).
  - [ ] `pytest backend/tests/test_action_plan/test_service.py::TestActionPlanGuardsIntegration -v` → **3 tests verts**.
  - [ ] `pytest backend/tests/ --tb=no -q` → **`N passed, 0 failed`** avec `N ≥ baseline_9.5 + 25 nouveaux tests`. Temps < 200 s.
  - [ ] `ruff check backend/app/core/llm_guards.py backend/app/modules/reports/service.py backend/app/modules/action_plan/service.py backend/tests/test_core/test_llm_guards.py` → **All checks passed**.
  - [ ] **Coverage** : `pytest --cov=app.core.llm_guards --cov-report=term-missing backend/tests/test_core/test_llm_guards.py` → **≥ 90 %** sur `llm_guards.py` (PRD L1293 « ≥ 85 % sur code critique guards LLM » — renforcé à 90 % vu la criticité et la petite taille du module).
  - [ ] **Smoke test manuel résumé exécutif** : lancer une génération de rapport via l'API, vérifier que le PDF contient un résumé exécutif cohérent avec les scores réels.
  - [ ] **Smoke test manuel plan d'action** : `POST /api/action-plan/generate?timeframe=12` avec profil minimal → vérifier `plan.items` len ∈ [5, 20] avec catégories/priorités valides.
  - [ ] **Update `deferred-work.md`** : section _« Resolved (2026-04-XX) — Story 9.6 »_ avec (a) référence audit P1 #10, (b) détail guards livrés par surface, (c) scopes renvoyés à stories futures (fiche préparation, FR40 signature, FR41 blocage > 50k, FR55 dashboard admin), (d) référence commit.
  - [ ] **Update `spec-audits/index.md`** : marquer P1 #10 comme `Resolu par story 9.6` (ligne 108) — pattern identique aux entrées 9.1-9.5.

---

## Dev Notes

### Choix techniques — justifications

- **Module partagé `backend/app/core/llm_guards.py`** vs. logique in-line dans chaque service : la logique est réutilisable, testable en isolation, et documentée en un seul endroit (audit, revue de sécurité). Placement dans `core/` plutôt que `modules/` car transverse, consommé par `reports/` et `action_plan/`, et **à terme** par `applications/` (spec 009 — dossiers bancaires IA).

- **Une seule exception `LLMGuardError`** vs. hiérarchie : simplicité des call-sites (`except LLMGuardError as err:`), dispatch machine via `err.code`. Évolutif : ajouter un nouveau code ne casse aucun caller.

- **`extra="forbid"` sur `ActionPlanItemLLMSchema`** : critique contre les clés hallucinées. Pydantic v2 rend cela gratuit ; ne pas l'activer serait céder la surface de contrôle. Trade-off : si un jour le prompt du plan d'action évolue pour inclure une nouvelle clé légitime, il faudra MAJ le schéma — coût minime.

- **Retry unique + prompt renforcé** : compromis latence/fiabilité. 1 retry couvre ~85 % des hallucinations ponctuelles. 2+ retries ajoutent ~2-3 s de latence pour un gain marginal.

- **`source_values` comparé via tolérance ±2.0** (AC1) : le LLM peut légitimement arrondir `54.3 → 54` ou écrire `"un score proche de 55"`. Tolérance `2.0` permet ce réalisme sans laisser passer un drift de 25 (82 vs 54).

- **Heuristique stopwords FR** (AC3) vs. `langdetect` ou `spaCy` : minimalisme volontaire. `langdetect` dépendance non-essentielle ; `spaCy` poids 100+ MB excessif. L'heuristique sur stopwords fonctionne pour tout texte > 50 tokens, ce qui est le seuil naturel pour un résumé exécutif (MIN_SUMMARY_LEN=200 chars → ~35 mots).

- **`assert_numeric_coherence` en dernier** : coût O(n × m) (n nombres dans le texte × m sources) — négligeable chez nous (n ≤ 10, m = 4). L'ordre `length → language → vocab → numeric` minimise le coût en cas d'échec early.

- **Télémétrie via `logger.warning(..., extra={...})`** vs Prometheus direct : pas de client Prometheus embarqué aujourd'hui. Le pattern structured logging est consommable par un collecteur futur (Loki + Grafana, OpenObserve, Datadog) sans coupler le code à un SDK. Cf. NFR39 dashboard admin futur.

- **`prompt_hash` (16 chars SHA-256)** : collision rate négligeable pour le volume, permet de corréler des échecs aux prompts sans exposer de PII (le contenu du prompt peut contenir nom entreprise, secteur, scores — RGPD-sensible à terme).

- **Défense en profondeur** (AC8) : conserver `_safe_category/_safe_priority/_parse_action_date` **avec log d'alerte**. Si jamais ils attrapent un cas non-Pydantic, cela détecte un drift potentiel entre le schema Pydantic et les helpers.

### Pièges à éviter

- **Regex `\b` et caractères accentués** : `\b` en Python regex ne considère pas toujours les accents comme word characters. Toujours `_strip_accents()` AVANT de matcher, et lister explicitement les variantes singulier/pluriel/masculin/féminin dans `FORBIDDEN_VOCAB` (le stripping n'aide pas pour les accords grammaticaux).

- **`langdetect` bloquant** : si ajouté, `detect()` est sync et lourd (~200 ms sur textes longs). Wrapper dans `asyncio.to_thread` si intégré. **Recommandation 9.6** : ne pas intégrer du tout (stopwords heuristique suffit).

- **Pydantic `ValidationError` vs `LLMGuardError`** : dans `validate_action_plan_schema()`, attraper `Exception` pour convertir en `LLMGuardError` — préserver `__cause__` via `raise LLMGuardError(...) from e`.

- **Prompt base vs. hardened** : le `hardened_prompt` ne doit pas contredire le `base_prompt`. Pattern « append à la fin » sûr si le prompt de base n'a pas d'instruction format contradictoire. Test manuel sur un payload golden avant merge.

- **Mock `ChatOpenAI.ainvoke`** : `patch("app.modules.reports.service.ChatOpenAI")` au point d'usage — NE PAS patcher `langchain_openai.ChatOpenAI` directement. Utiliser `AsyncMock(side_effect=[...])` pour retries séquentiels.

- **`HTTPException` vs `LLMGuardError` qui échappe** : `run_guarded_llm_call` attrape le 2e `LLMGuardError` et lève `HTTPException(500)`. Vérifier que les callers (routers) n'attrapent PAS `HTTPException` trop large.

- **Bornes `MIN_ACTION_COUNT=5`** : filet de sécurité bas. Le prompt `action_plan.py` demande actuellement « 10-15 actions » et le LLM honore à ~95 %. Ne pas resserrer à `10` sans mesure empirique — risque de faux positifs.

- **Coverage ≥ 90 %** : `run_guarded_llm_call` doit être couvert par 3 cas minimum (succès au 1er, recovery au 2e, échec définitif). Vérifier le rapport `--cov-report=term-missing`.

- **Ne pas ajouter de nouveaux guards « nice to have »** (détection URLs suspectes, IBAN en clair) : hors scope 9.6. Scope strictement borné aux 4 guards free-text + 2 guards JSON listés dans l'audit.

- **Compatibilité SQLite tests in-memory** : aucun changement BDD ici, donc aucune contrainte migration SQLite à craindre (contrairement à story 9.5).

### Architecture actuelle — repères

- **Service résumé exécutif** : [backend/app/modules/reports/service.py:63-107](../../backend/app/modules/reports/service.py#L63) (45 lignes aujourd'hui, 1 call-site ligne 281).
- **Service plan d'action** : [backend/app/modules/action_plan/service.py:171-355](../../backend/app/modules/action_plan/service.py#L171) (185 lignes aujourd'hui).
- **Helpers plan d'action** : [backend/app/modules/action_plan/service.py:29-91](../../backend/app/modules/action_plan/service.py#L29) (`_extract_json_array`, `_safe_category`, `_safe_priority`, `_parse_action_date`).
- **Prompts** : [backend/app/prompts/esg_scoring.py](../../backend/app/prompts/esg_scoring.py) (`ESG_REPORT_EXECUTIVE_SUMMARY_PROMPT`) + [backend/app/prompts/action_plan.py](../../backend/app/prompts/action_plan.py) (`ACTION_PLAN_PROMPT`).
- **Tests résumé existants** : [backend/tests/test_api/test_report_service.py](../../backend/tests/test_api/test_report_service.py) (pattern `AsyncMock`).
- **Tests plan d'action existants** : [backend/tests/test_action_plan/test_service.py](../../backend/tests/test_action_plan/test_service.py) (fixtures `db_session`, `user_id`).
- **Pattern Pydantic strict exemplaire** : modèles `InteractiveQuestion*` (spec 018) utilisent `model_config = ConfigDict(extra="forbid")`.

### Références

- [Source : _bmad-output/implementation-artifacts/spec-audits/index.md §P1 #10](./spec-audits/index.md) — audit consolidé (reclassement P2→P1 2026-04-16, élargi 006+008+011)
- [Source : _bmad-output/planning-artifacts/prd.md §Risque 10](../planning-artifacts/prd.md) — dispositif renforcé non-négociable
- [Source : _bmad-output/planning-artifacts/prd.md §SC-T8](../planning-artifacts/prd.md) — 100 % des contenus LLM passent un guard
- [Source : _bmad-output/planning-artifacts/prd.md FR40/FR41/FR55/FR56/NFR39/NFR40](../planning-artifacts/prd.md) — traçabilité et alerting
- [Source : _bmad-output/planning-artifacts/prd.md L1676 Traceability matrix](../planning-artifacts/prd.md) — mapping FR36/40/41/44 → P1 #10
- [Source : specs/006-esg-pdf-reports/spec.md](../../specs/006-esg-pdf-reports/spec.md) — résumé exécutif ESG
- [Source : specs/011-dashboard-action-plan/spec.md](../../specs/011-dashboard-action-plan/spec.md) — plan d'action LLM JSON
- **Patterns de référence** :
  - [9-5-flag-manually-edited-fields-companyprofile.md](./9-5-flag-manually-edited-fields-companyprofile.md) — structure story P1 + discipline tests + `deferred-work.md`.
  - [9-1-rate-limiting-fr013-chat-endpoint.md](./9-1-rate-limiting-fr013-chat-endpoint.md) — pattern « code critique compliance + télémétrie structurée ».
- [CLAUDE.md §Backend (FastAPI)](../../CLAUDE.md) — conventions nommage, imports, routeurs
- `~/.claude/rules/common/coding-style.md` — immutabilité, fichiers courts, handlers d'erreur explicites

---

## Hors scope (stories futures)

1. **Fiche de préparation financing — pas d'LLM aujourd'hui, pas de guard à ajouter** — [backend/app/modules/financing/preparation_sheet.py](../../backend/app/modules/financing/preparation_sheet.py) est **100 % template Jinja2**. L'audit P1 #10 liste cette surface mais elle n'a **aucune surface LLM** en l'état. Si une story future (P3) ajoute un paragraphe narratif LLM (« synthèse de match personnalisée »), elle devra passer par `llm_guards.py` livré ici.

2. **FR40 — signature électronique utilisateur obligatoire avant export bailleur** — modal bloquant + case à cocher + trace dans `FundApplicationGenerationLog`. **Story future P1**. Sans signature, un document avec contenu halluciné engagerait déjà Mefali (la signature est la ceinture, les guards sont les bretelles).

3. **FR41 — blocage export > 50 000 USD tant que revue section par section non cochée** — workflow UX + backend gate. Story future P1.

4. **FR44 — SGES/ESMS BETA NO BYPASS** — revue humaine obligatoire sur livrables SGES. Story future.

5. **FR55 — dashboard admin_mefali monitoring** — consommation du `metric=llm_guard_failure` via Grafana/OpenObserve. Story future P1 Phase 0 infra.

6. **FR56 — alerting automatique sur échecs guards LLM** — Sentry / alert manager. Story future Phase Growth (post-MVP).

7. **Guards LLM sur le chat live (non persisté)** — le chat SSE produit aussi du texte LLM (9 noeuds LangGraph) mais non remis à un bailleur. P2/P3, à évaluer si nécessaire.

8. **Test de contenu PDF bout-en-bout (P2 #20 audit)** — parser le PDF WeasyPrint généré. La story 9.6 couvre les tests sur les **strings pré-PDF** (avant rendu). Parsing post-PDF reste P2 séparé.

9. **Pydantic strict pour les narratifs applications (spec 009)** — si la génération de dossiers applications utilise un LLM free-text, étendre `llm_guards.py` avec surface `"application_narrative"`. Hors scope 9.6.

10. **`langdetect` / `spaCy` pour détection langue robuste** — si l'heuristique stopwords génère des faux positifs en prod (métrique `guard=language_drift` > 1 %/jour), envisager `langdetect`. Décision post-déploiement sur données réelles.

11. **Tuning des bornes `MIN_SUMMARY_LEN` / `MAX_SUMMARY_LEN` / `MIN_ACTION_COUNT` / `MAX_ACTION_COUNT`** — constantes exposées ; ajuster si la télémétrie post-déploiement montre des faux positifs.

12. **Anti-prompt injection dans les champs utilisateur passés au LLM** (ex. `company_name="Ignore previous instructions…"`) — hors scope, couvert par `NFR9` PRD (sanitization inputs LLM). Story future sécurité.

---

## Structure projet — alignement

- **Nouveaux fichiers (3)** :
  - `backend/app/core/llm_guards.py` (~450 lignes — exception + 4 free-text guards + schéma Pydantic plan d'action + `run_guarded_llm_call` + télémétrie)
  - `backend/tests/test_core/__init__.py` (vide — créer si absent)
  - `backend/tests/test_core/test_llm_guards.py` (~350 lignes — 19 tests unitaires)
- **Fichiers modifiés** :
  - `backend/app/modules/reports/service.py` — refacto `generate_executive_summary()` + ajout param `user_id: str | None` + call-site ligne 281 (~65 lignes modifiées)
  - `backend/app/modules/action_plan/service.py` — refacto `generate_action_plan()` + log d'alerte dans helpers `_safe_*` (~80 lignes modifiées)
  - `backend/tests/test_api/test_report_service.py` (ou nouveau `test_report_guards.py`) — classe `TestExecutiveSummaryGuardsIntegration` (~120 lignes, 3 tests)
  - `backend/tests/test_action_plan/test_service.py` — classe `TestActionPlanGuardsIntegration` (~150 lignes, 3 tests)
  - `_bmad-output/implementation-artifacts/deferred-work.md` — section _« Resolved 2026-04-XX — Story 9.6 »_ (~25 lignes)
  - `_bmad-output/implementation-artifacts/spec-audits/index.md` — marqueur résolu P1 #10 (1 ligne)
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` — transition statut + `last_updated` + `last_story_created`
- **Conventions respectées** :
  - Python : PEP 8, type hints strict (`Literal`, `tuple`, `dict[str, Any]`), `frozenset` pour enums, imports groupés, ruff-clean.
  - Pydantic v2 : `model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)`, `field_validator` avec `@classmethod`.
  - Logging : `logger = logging.getLogger(__name__)`, log structuré avec `extra={}`, jamais de `print()`.
  - Tests pytest : `pytest.mark.asyncio`, fixtures `db_session`/`user_id` réutilisées, `@pytest.mark.parametrize`, `patch("module.path")` au point d'usage.
  - Naming : `snake_case` Python, `UPPER_SNAKE` constantes module-level, `CamelCase` classes Pydantic.
- **Immutabilité** : `source_values` / `FORBIDDEN_VOCAB` / `VALID_CATEGORIES` jamais mutés — `tuple` / `frozenset` explicites (cf. `rules/common/coding-style.md`).
- **Files < 800 lignes** : `llm_guards.py` visé ~450 lignes ; si dépassement, splitter en sous-modules `llm_guards/{exceptions,free_text,json_schema,telemetry}.py`.

---

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (1M context) — `claude-opus-4-7[1m]`

### Debug Log References

- T11 vérification `langdetect` : `grep "langdetect" backend/requirements.txt` → **absent**. Décision : heuristique stopwords FR seule (cf. Dev Notes). Pas d'ajout de dépendance.
- Ruff initial report `backend/app/modules/reports/service.py` : 1 erreur `F401 os imported but unused` → **pré-existante** (commit `0f1a67c6` 2026-03-31), non introduite par 9.6. Idem 3 erreurs `F821 "Reminder"` dans `action_plan/service.py` → pré-existantes. Ruff strict sur les fichiers nouveaux uniquement : **All checks passed**.
- Tests `test_action_plan/test_service.py` ajustés (fixtures de 1 ou 4 actions passées à 5 actions minimum pour respecter `MIN_ACTION_COUNT=5`, conformément à AC10). Aucune assertion métier supprimée.

### Completion Notes List

- **T1-T3** : module `backend/app/core/llm_guards.py` créé (~440 lignes, ruff-clean) avec exception unifiée `LLMGuardError`, 4 free-text guards (`assert_length`, `assert_language_fr`, `assert_no_forbidden_vocabulary`, `assert_numeric_coherence`), schéma Pydantic strict `ActionPlanItemLLMSchema` (`extra="forbid"` + enums + bornes), `validate_action_plan_schema`, télémétrie `log_guard_failure` (metric `llm_guard_failure` avec `prompt_hash` SHA-256[:16]), orchestrateur `run_guarded_llm_call` (retry unique + `HTTPException(500)`).
- **T4** : `generate_executive_summary()` refacto pour exécuter les 4 guards dans l'ordre déterministe AC7 (length → langue → vocab → numérique) avec `hardened_prompt` qui ajoute contraintes strictes (FR exclusif, valeurs numériques permises, vocab interdit énuméré, bornes longueur). Paramètre `user_id: str | None = None` ajouté (rétrocompatible).
- **T5** : `generate_action_plan()` refacto avec `run_guarded_llm_call` + schema Pydantic strict + bornes count 5-20. `_safe_category()` et `_safe_priority()` conservés en défense en profondeur avec `logger.warning(extra={"metric": "pydantic_drift"})`. Double parsing intentionnel (dans `guards()` pour lever l'exception + après `run_guarded` pour récupérer les objets Pydantic typés, coût négligeable).
- **T6** : call-site `reports/service.py:281` mis à jour avec `user_id=str(user_id)`.
- **T7-T8** : 37 tests unitaires (`TestLLMGuardsFreeText` 19 tests + `TestLLMGuardsJSONSchema` 15 tests + `TestActionPlanItemLLMSchemaDirect` 3 tests), tous verts.
- **T9** : 3 tests d'intégration `TestExecutiveSummaryGuardsIntegration` dans `tests/test_report_guards.py` (valid passe, hallucination → retry → 500, recovery au retry). Mock pattern `patch("app.modules.reports.service.ChatOpenAI")` au point d'usage.
- **T10** : 3 tests d'intégration `TestActionPlanGuardsIntegration` dans `tests/test_action_plan/test_service.py` (valid creates actions, hallucinated → retry → 500, too_few → retry → recovery).
- **T11** : `langdetect` absent de `requirements.txt`, heuristique stopwords conservée seule.
- **T12 Quality gate** : `pytest tests/ --tb=no -q` → **1159 passed, 0 failed** en 184 s < 200 s. Coverage `app/core/llm_guards.py` = **99 %** (≥ 90 % seuil PRD). Ruff-clean sur fichiers nouveaux.
- **Artifacts** : `deferred-work.md` section « Resolved (2026-04-19) — Story 9.6 » ajoutée, `spec-audits/index.md` P1 #10 barré avec marqueur résolu, `sprint-status.yaml` mis à jour.

### File List

**Nouveaux fichiers :**
- `backend/app/core/llm_guards.py`
- `backend/tests/test_core/__init__.py`
- `backend/tests/test_core/test_llm_guards.py`
- `backend/tests/test_report_guards.py`

**Fichiers modifiés :**
- `backend/app/modules/reports/service.py` (imports guards + refacto `generate_executive_summary` + call-site ligne 281)
- `backend/app/modules/action_plan/service.py` (imports guards + refacto `generate_action_plan` + logs drift dans `_safe_category` / `_safe_priority`)
- `backend/tests/test_action_plan/test_service.py` (3 fixtures adaptées à `MIN_ACTION_COUNT=5` + nouvelle classe `TestActionPlanGuardsIntegration` avec 3 tests)
- `_bmad-output/implementation-artifacts/deferred-work.md` (section Resolved Story 9.6)
- `_bmad-output/implementation-artifacts/spec-audits/index.md` (marqueur résolu P1 #10)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (transition statut ready-for-dev → in-progress → review + `last_updated`)
- `_bmad-output/implementation-artifacts/9-6-guards-llm-persistes-documents-bailleurs.md` (Status, Dev Agent Record, File List, Change Log, Tasks checkboxes)

### Change Log

| Date       | Version | Description                                                                                                | Author |
|------------|---------|------------------------------------------------------------------------------------------------------------|--------|
| 2026-04-19 | 0.1.0   | Création de la story (create-story) — P1 #10 guards LLM persistés (résumé exécutif spec 006 + plan d'action spec 011). Fiche préparation spec 008 hors scope (pas de LLM direct actuel). | PM     |
| 2026-04-19 | 1.0.0   | Implémentation dev-story : module `backend/app/core/llm_guards.py` + intégration `generate_executive_summary` + `generate_action_plan`. 43 nouveaux tests, 1159 tests verts, coverage 99 % sur le module critique. Statut → review. | Dev    |
| 2026-04-19 | 1.1.0   | Code review adversarial 3 couches (Blind/Edge/Auditor) — 18 patches appliqués + 13 nouveaux tests (D1/D2/D3). Whitelist contextuelle numeric_coherence (pattern `/100` strict + `%` avec keywords score/note/évaluation/pilier/global ±5 tokens), docstring contrat exceptions `run_guarded_llm_call` (infra transient = propagé vers `with_retry`), `_validate_due_date` avec `ValidationInfo.context["timeframe_months"]` + tolérance 15 %. Correctifs transverses : `VALID_CATEGORIES` dérivé de `ActionItemCategory`, conjugaisons verbales dans `FORBIDDEN_VOCAB` (garantit/garantissons/...), tokenizer Unicode via `[^\W\d_]+`, élisions FR (l'/d'/qu'/n'/c'/s'), multi-mot `\s+` tolérance NBSP, filtrage sources 0/None, payload `numeric_drift` enrichi (`field`+`expected`), log drift sur `_parse_action_date`, `max_length=200` sur `fund_id`/`intermediary_id`, prompt résumé exécutif en `SystemMessage`, `recovered` loggé après succès retry, suppression double `_extract_json_array`. 1172 tests verts (178 s). Statut → done. | Reviewer |

### Review Findings

_Code review 2026-04-19 — 3 couches (Blind Hunter, Edge Case Hunter, Acceptance Auditor). 9 items dismiss (design intentionnel / faux positifs). 3 décisions, 15 patches, 5 différés._

**Décisions requises (bloquantes) :**

- [x] [Review][Decision] `assert_numeric_coherence` produit des faux positifs sur pourcentages/statistiques légitimes — Un résumé mentionnant « 12 % du PIB textile » ou « progression de 15 % sur un an » déclenche `numeric_drift` car toute occurrence `<n>%` est traitée comme score prétendu. Choix à faire : (a) restreindre le pattern à `\b\d+/100\b` uniquement (strict, rate les `%`), (b) whitelist contextuelle (mot « score » à proximité), (c) tolérance élargie + seuil minimal `min_source_values=2`, (d) laisser tel quel et documenter comme faux-positif acceptable. Source : blind+edge.
- [x] [Review][Decision] Erreurs LLM non-guard (timeouts, rate limits) bypass du retry — `run_guarded_llm_call` n'attrape que `LLMGuardError`. Un `httpx.TimeoutException` ou `openai.RateLimitError` au 1er appel se propage sans retry et sans log `llm_guard_failure`. Choix : (a) attraper aussi les exceptions transitoires et retry une fois, (b) laisser propager (comportement actuel) et documenter comme infra-only, (c) attraper mais ne pas retry (logger seulement). Source : blind+edge. [backend/app/core/llm_guards.py:run_guarded_llm_call]
- [x] [Review][Decision] `_validate_due_date` plafond ne tient pas compte du `timeframe` utilisateur — Le validator utilise `MAX_TIMEFRAME_MONTHS=24` en dur, alors que le hardened prompt demande `timeframe+3 mois`. Un plan 6 mois peut voir des `due_date` à 2 ans validées puis tronquées silencieusement par `_parse_action_date`. Choix : (a) paramétrer le validator avec le `timeframe` courant (signature plus complexe), (b) laisser `MAX_TIMEFRAME_MONTHS` comme plafond global et accepter la troncature, (c) factoriser la troncature dans le validator. Source : edge. [backend/app/core/llm_guards.py:_validate_due_date]

**Patches (correctifs à appliquer) :**

- [x] [Review][Patch] `_extract_json_array` appelé deux fois (happy path) — double parse peut diverger sur LLM renvoyant plusieurs tableaux ; réutiliser le résultat validé au lieu de re-extraire. [backend/app/modules/action_plan/service.py:291-327]
- [x] [Review][Patch] Regex multi-mot forbidden vocab ne matche pas avec espaces multiples/ponctuation — remplacer l'espace littéral par `\s+` dans `re.escape(term)` pour couvrir `"valide  par"`, `"valide, par"`, NBSP. [backend/app/core/llm_guards.py:assert_no_forbidden_vocabulary]
- [x] [Review][Patch] `VALID_CATEGORIES` non synchronisé avec l'enum `ActionItemCategory` — dériver le frozenset depuis l'enum SQLAlchemy pour éviter le drift silencieux. [backend/app/core/llm_guards.py:VALID_CATEGORIES]
- [x] [Review][Patch] Retry asymétrique SystemMessage vs HumanMessage — dans `generate_executive_summary`, placer le prompt dans `SystemMessage` (comme `generate_action_plan`) pour que le hardened_prompt soit effectif au retry. [backend/app/modules/reports/service.py:129-139]
- [x] [Review][Patch] `final_outcome="recovered"` loggé avant confirmation du retry — déplacer le premier `log_guard_failure` après succès du retry, sinon les métriques Grafana comptent des recover qui ne l'étaient pas. [backend/app/core/llm_guards.py:run_guarded_llm_call]
- [x] [Review][Patch] `_FR_STOPWORDS` rate les élisions (`l'`, `d'`, `qu'`, `n'`) — le tokenizer capture `"l'entreprise"` comme un seul token ; ajouter un split sur apostrophe ou enrichir la liste de stopwords avec `"l"`, `"d"`, `"qu"`, `"n"`, `"c"`, `"s"`. [backend/app/core/llm_guards.py:assert_language_fr]
- [x] [Review][Patch] Score 0 en source produit des faux drifts — `overall_score or 0` coerce les None en 0 côté caller, tous les `X%` du texte deviennent drift ; filtrer les zéros dans `source_floats` OU ignorer les sources None avant l'appel guard. [backend/app/modules/reports/service.py:327] + [backend/app/core/llm_guards.py:assert_numeric_coherence]
- [x] [Review][Patch] Pattern numeric rate les espaces non-sécables (NBSP U+00A0, thin space U+202F) — normaliser les espaces avant la regex : `text.replace("\u00a0", " ").replace("\u202f", " ")`. [backend/app/core/llm_guards.py:assert_numeric_coherence]
- [x] [Review][Patch] `assert_language_fr` short-circuit à 50 tokens trop permissif — un résumé de 200 chars (~30–45 tokens FR) est laissé sans vérification ; abaisser à 20 tokens OU supprimer le short-circuit puisque `assert_length(min=200)` garantit déjà un minimum exploitable. [backend/app/core/llm_guards.py:assert_language_fr]
- [x] [Review][Patch] `FORBIDDEN_VOCAB` manque les conjugaisons verbales actives — ajouter `"garantit"`, `"garantissons"`, `"garantissent"`, `"certifions"`, `"accredite"` (présent), sinon un LLM contourne trivialement par « nous garantissons ». [backend/app/core/llm_guards.py:FORBIDDEN_VOCAB]
- [x] [Review][Patch] Tokenizer Unicode bornes fragiles (`\u00C0-\u017F`) — remplacer par `\w+` avec flag `re.UNICODE` pour couvrir toutes les lettres latines accentuées et ligatures. [backend/app/core/llm_guards.py:assert_language_fr]
- [x] [Review][Patch] `str | None` champs sans plafond de longueur (`fund_id`, `intermediary_id`) — ajouter `max_length=200` sur `ActionPlanItemLLMSchema.fund_id/intermediary_id` pour cohérence avec les autres champs et anti-DoS. [backend/app/core/llm_guards.py:ActionPlanItemLLMSchema]
- [x] [Review][Patch] `_strip_accents` non appliqué aux termes de `FORBIDDEN_VOCAB` — défense en profondeur : si un contributeur ajoute `"garantié"` (avec accent), la détection silencieusement ne matchera pas ; normaliser à la construction ou au moment du check. [backend/app/core/llm_guards.py:assert_no_forbidden_vocabulary]
- [x] [Review][Patch] AC1 payload `LLMGuardError("numeric_drift")` non aligné spec — le spec prescrit `detected_value`, `expected`, `field` ; l'implémentation renvoie `detected_value` + `source_values` (dict complet). Ajouter `field` (nom de la source la plus proche) et `expected` (valeur attendue la plus proche) pour alignement verbatim. [backend/app/core/llm_guards.py:assert_numeric_coherence]
- [x] [Review][Patch] T5 — `_parse_action_date` défense-en-profondeur sans log — le spec T5 liste `_safe_category`, `_safe_priority` ET `_parse_action_date` pour ajouter `logger.warning(extra={"metric": "pydantic_drift", ...})` ; seuls les deux premiers ont le log, compléter le troisième. [backend/app/modules/action_plan/service.py:_parse_action_date]

**Différés (pré-existant ou hors scope) :**

- [x] [Review][Defer] `date.today()` non-déterministe dans `_validate_due_date` [backend/app/core/llm_guards.py:_validate_due_date] — deferred, injection de temps demande refacto plus large (clock abstraction globale).
- [x] [Review][Defer] `MAX_ACTION_COUNT=20` vs prompt action_plan existant « 10-15 » [backend/app/prompts/action_plan.py] — deferred, pre-existing, demande édition du prompt base hors scope 9.6.
- [x] [Review][Defer] `HTTPException(500)` opaque côté utilisateur [backend/app/core/llm_guards.py:run_guarded_llm_call] — deferred, amélioration UX non critique, à traiter dans une story dédiée gestion des erreurs guards.
- [x] [Review][Defer] `prompt_hash` sur 200 premiers chars produit collisions cross-user [backend/app/core/llm_guards.py:prompt_hash] — deferred, design choice documenté dans spec AC9 (PII avoidance) ; amélioration future via hash intégral après scrub PII.
- [x] [Review][Defer] `assert_numeric_coherence` branche `/10` utilise la même tolérance que `/100` [backend/app/core/llm_guards.py:assert_numeric_coherence] — deferred, edge case de conversion d'échelle asymétrique, demande design dédié (tolérance relative vs absolue).
