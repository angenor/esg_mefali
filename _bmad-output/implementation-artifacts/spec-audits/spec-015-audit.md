# Audit Rétrospectif — Spec 015 : Correction Tool-Calling ESG Timeout

**Date d'audit** : 2026-04-16
**Auditeur** : Angenor (Project Lead) + assistant Amelia
**Spec** : [specs/015-fix-toolcall-esg-timeout/](../../../specs/015-fix-toolcall-esg-timeout/)
**Méthode** : rétrospective post-hoc sur spec-correctif
**Statut rétro** : ✅ Audité — correctif chirurgical réussi, 1 dette transverse non propagée

---

## 1. Portée de la spec

**Spec-correctif P1** pour 3 anomalies révélées par les tests d'intégration :
- **Anomalie 3** : `application_node` ne sauvegardait pas en base — répondait uniquement en texte
- **Anomalie 4** : `credit_node` donnait des estimations textuelles sans appeler le tool
- **Anomalie 5** : évaluation ESG 30 critères → timeout SSE/HTTP sur sauvegardes séquentielles

| Dimension | Livré |
|-----------|-------|
| Tâches | 18 / 18 `[X]` (100 %) |
| Discordance tasks↔code | 0 (tous les ajouts vérifiés par grep) |
| User Stories | 4 (US1-US2 P1, US3 P2, US4 P1 non-régression) |
| Nouveaux tools | 2 (`create_fund_application`, `batch_save_esg_criteria`) |
| Prompts modifiés | 3 (application.py, credit.py, esg_scoring.py) |
| Nouveau timeout | `request_timeout=60` dans `get_llm()` |
| CLAUDE.md mentionne | "14 nouveaux tests unitaires prompts/tools, zero regression sur les 856 tests existants" |

---

## 2. Ce qui a bien fonctionné

### 2.1 Diagnostic précis = 3 anomalies distinctes

- Anomalie 3/4 : cause racine identifiée (prompts passifs, tools non appelés)
- Anomalie 5 : cause racine identifiée (30 appels séquentiels → timeout cumulé)
- 3 fixes **chirurgicaux** appliqués aux bons endroits (prompts + 2 nouveaux tools + timeout)

### 2.2 Pattern "REGLE ABSOLUE" injecté dans 3 prompts

- `application.py:18` : *"REGLE ABSOLUE — TOOL CALLING OBLIGATOIRE"*
- `credit.py:19-20` : *"Ne donne JAMAIS une estimation de score en texte sans appeler `generate_credit_score`"*
- `credit.py:31-33` : triple INTERDIT (estimation, fourchette, description)
- `esg_scoring.py:31` : *"SAUVEGARDE PAR LOT — REGLE ABSOLUE"*
- **Pattern cohérent** pour forcer le tool-calling via prompt injection

### 2.3 `batch_save_esg_criteria` élégant

- `esg_tools.py:264` : sauvegarde N critères en 1 transaction (update unique `assessment_data` + `evaluated_criteria`)
- Remplace 10 appels LLM séquentiels par 1 seul pour un pilier entier
- SC-005 : "Le nombre d'allers-retours pour sauvegarder un pilier ESG passe de 10 à 1" ✅
- Ajout au tuple `ESG_TOOLS` (esg_tools.py:363)

### 2.4 `create_fund_application` comblant un vide

- Spec 009 avait livré les tools `generate_application_section` et autres, **mais pas de tool pour créer un dossier from scratch**
- Le LLM ne pouvait qu'enrichir un dossier existant, pas en créer un nouveau
- Spec 015 ajoute ce tool qui débloque le flux end-to-end chat → dossier créé

### 2.5 Timeout LLM explicite (FR-008)

- `get_llm()` ajoute `request_timeout=60` (nodes.py:315)
- Sécurité supplémentaire : même si un appel LLM ralentit, le workflow ne pend pas indéfiniment
- Choix raisonnable (60s ~2x la latence max observée)

### 2.6 Non-régression validée (US4)

- 14 nouveaux tests unitaires sans casser les 856 existants
- Phase 6 dédiée à la vérification (T015-T016)

### 2.7 Parallélisation des 3 user stories

- US1/US2/US3 entièrement indépendantes (fichiers différents, pas de dépendances croisées)
- Exécution possible en 3 agents parallèles → gain de temps réel

---

## 3. Ce qui a posé problème

### 3.1 🟠 `batch_save_*` pattern NON étendu aux modules similaires

- Spec 015 résout le timeout pour ESG mais **ne l'applique qu'à ESG**
- **Pattern identique existe** dans :
  - **Carbone** : `save_emission_entry` appelé par entrée (5-15 fois/bilan) → même risque de timeout (dette spec 007 §3.1, déjà P1 #12)
  - **Credit** : `generate_credit_score` ne fait qu'un appel, pas de batch
  - **Application** : `generate_application_section` appelé par section (5-7/dossier)
- **Cause racine** : spec 015 est focalisée sur 3 anomalies observées — pas sur le **pattern** sous-jacent
- **Impact** : la même classe de bug reviendra sur carbone en prod
- **Leçon** : les specs-correctif gagnent à **généraliser le fix** au pattern sous-jacent, pas seulement à l'instance signalée

### 3.2 🟠 "REGLE ABSOLUE" dupliquée dans 3 prompts sans helper

- Pattern "ROLE actif + OUTILS DISPONIBLES + REGLE ABSOLUE" copié 3× (application, credit, esg_scoring)
- Variations cosmétiques (casse, wording) mais structure identique
- Si une 4ème REGLE est ajoutée (ex: prompt rate limiting, prompt anti-hallucination), duplication multiple
- **Dette transverse** avec spec 014 §3.2 (framework d'injection d'instructions)
- **Leçon** : les patterns de prompt injection répétés méritent un helper `build_tool_calling_rule(tool_names: list[str], role: str, forbidden: list[str])`

### 3.3 🟠 Tests vérifient le contenu du prompt, pas le comportement

- T002 : *"vérifier que le prompt application contient les noms des tools et la REGLE ABSOLUE"*
- T007 : *"vérifier que le prompt crédit contient les noms des 3 tools et la REGLE ABSOLUE"*
- Ces tests vérifient que la **string** contient les mots-clés
- **Mais** : rien ne garantit que le **LLM respecte** l'instruction à l'exécution
- Pas de test d'intégration : "envoyer 'Crée-moi un dossier SUNREF' et vérifier que `create_fund_application` est bien appelé"
- **Impact** : un upgrade LLM ou une régression prompt peut casser le comportement sans détection
- **Leçon** : tests de prompt = 2 niveaux — unité (contenu string) + intégration (comportement LLM observé)

### 3.4 🟠 `request_timeout=60` : magic number sans constante

- `nodes.py:315` : `request_timeout=60` hard-codé
- Pas de constante `LLM_REQUEST_TIMEOUT_SECONDS = 60` avec commentaire
- Si un autre module créé un LLM ailleurs, oubli de mettre le même timeout possible
- **Leçon** : timeouts réseau méritent constantes nommées avec justification

### 3.5 🟡 Pas de métrique sur l'usage du batch

- `batch_save_esg_criteria` existe, mais aucune instrumentation pour vérifier :
  - Combien de fois il est appelé vs `save_esg_criterion_score` ?
  - Le LLM respecte-t-il l'instruction de batcher (post-pilier) ?
  - Nombre moyen de critères par batch ?
- Sans métrique, impossible de savoir si le fix a vraiment résolu le problème ou si le LLM ignore l'instruction
- **Leçon** : instrumenter les tools "optimisation" pour valider leur adoption

### 3.6 🟡 Finalisation ESG non testée au-delà de SC-003

- SC-003 : *"le test 3.5 (ESG 30 critères) passe — la finalisation complète se termine en moins de 15 secondes"*
- Objectif raisonnable mais pas de test de charge
- Comportement à 50, 100 critères (futures extensions) ? Non testé
- **Leçon** : les fixes de timeout gagnent à tester la courbe de latence (N=10, N=30, N=50), pas juste le cas nominal

### 3.7 🟡 Pas d'analyse "pourquoi le LLM ne respectait pas les tools initialement"

- Specs 006 (reports) et 008 (financing) ont des prompts similaires qui fonctionnent probablement bien
- Pourquoi application_node et credit_node (spec 009, 010) ont eu le bug ?
- Différence dans la structure du prompt initial ? Dans le nombre de tools bindés ?
- **Pas d'analyse root cause documentée** dans la spec — juste le fix
- **Leçon** : les specs-correctif gagnent à documenter "pourquoi ce bug ici et pas ailleurs" pour éviter récidive

---

## 4. Leçons transversales

1. **Généraliser le fix au pattern sous-jacent** — pas seulement à l'instance signalée.
2. **Helper pour prompts répétés** (REGLE ABSOLUE, ROLE actif, OUTILS DISPONIBLES).
3. **Tests de prompt = 2 niveaux** (contenu + comportement LLM).
4. **Timeouts réseau = constantes nommées** avec justification.
5. **Instrumenter les tools "optimisation"** pour valider leur adoption par le LLM.
6. **Test de charge courbe** pour les fixes de timeout (N=10/30/50).
7. **Root cause analysis documentée** dans les specs-correctif.

---

## 5. Actions résiduelles retenues

| # | Action | Priorité | Source |
|---|--------|----------|--------|
| 1 | **Étendre `batch_save_*` au module carbon** (déjà P1 #12 — même dette confirmée) | P1 | §3.1 |
| 2 | Extraire helper `build_tool_calling_rule()` pour prompts répétés | P3 | §3.2 |
| 3 | Tests d'intégration "le LLM appelle-t-il vraiment le tool ?" avec fixtures | P3 | §3.3 |
| 4 | Constante nommée `LLM_REQUEST_TIMEOUT_SECONDS = 60` | P3 | §3.4 |
| 5 | Instrumenter l'usage du batch vs individual (métriques `batch_size` dans `tool_call_logs`) | P3 | §3.5 |
| 6 | Tests de charge courbe de latence finalisation ESG (N=10/30/50/100) | P3 | §3.6 |

**Actions déjà en place** :
- ✅ `request_timeout=60` dans get_llm()
- ✅ `batch_save_esg_criteria` pour ESG (1 appel vs 10)
- ✅ `create_fund_application` comble un vide du module application
- ✅ 3 prompts renforcés avec ROLE actif + REGLE ABSOLUE
- ✅ 14 nouveaux tests, zero régression sur 856 existants

**Consolidation avec autres audits** :
- §3.1 batch pattern → déjà couvert par P1 #12 (source spec 007) — **fusion confirmée**, spec 015 aurait dû étendre ce pattern dès sa livraison
- §3.2 pattern REGLE ABSOLUE dupliqué → consolider avec spec 014 §3.2 (framework d'injection d'instructions)

---

## 6. Verdict

**Spec 015 est un correctif P1 chirurgical réussi** — 3 anomalies résolues, 14 tests ajoutés, zero régression. Le pattern "ROLE actif + REGLE ABSOLUE" + 2 nouveaux tools adressent **précisément** les bugs observés.

**MAIS** : spec 015 **ne généralise pas** le fix batch au pattern sous-jacent. Le même bug de timeout reviendra sur carbon (5-15 appels `save_emission_entry`) — dette **déjà P1 #12** dans l'index. Spec 015 aurait dû livrer `batch_save_emission_entries` en même temps que `batch_save_esg_criteria`.

Les autres dettes sont **opérationnelles** (instrumentation, constantes, tests d'intégration) — toutes P3.

**Recommandation** : spec 015 est une **bonne référence pour les spec-correctif chirurgicaux** (diagnostic + fix + tests + non-régression). Leçon clé : **quand un fix s'applique à un pattern, généraliser au pattern** — pas seulement à l'instance. Dette P1 #12 reste à résoudre (batch carbon) — cohérente avec cette leçon.
