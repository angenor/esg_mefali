# Audit Rétrospectif — Spec 012 : Intégration Tool Calling LangGraph

**Date d'audit** : 2026-04-16
**Auditeur** : Angenor (Project Lead) + assistant Amelia
**Spec** : [specs/012-langgraph-tool-calling/](../../../specs/012-langgraph-tool-calling/)
**Méthode** : rétrospective post-hoc + vérification code
**Statut rétro** : ⚠️ Dettes lourdes (FR-021/FR-022 non appliqués à 9/11 modules)

---

## 1. Portée de la spec

**Refactor architectural majeur** : ajout du tool-calling LangChain dans les 9 nœuds LangGraph pour que le LLM puisse **agir** (sauvegarder, lire, modifier) en base, pas seulement générer du texte. Affecte toutes les specs précédentes (002-011).

| Dimension | Livré |
|-----------|-------|
| Tâches | 58 / 58 `[x]` (100 %) (T056/T057 sautées dans la numérotation) |
| Discordance tasks↔code | 2 FR non appliqués (FR-021, FR-022 — cf. §3.1) |
| User Stories | 10 (US1-US3/US8/US9 P1, US4-US7 P2, US10 P3) |
| Clarifications | 4 (confirmation finalize, max 5 tools, 1 retry, logger tout) |
| Tools LangChain créés | 32 répartis dans 11 fichiers (`graph/tools/`) |
| Nouveau modèle | `ToolCallLog` + migration |
| Infrastructure | `create_tool_loop()` + `with_retry()` + `log_tool_call()` + `get_db_and_user()` |
| SSE events ajoutés | 3 (`tool_call_start`, `tool_call_end`, `tool_call_error`) |
| Composant frontend | `ToolCallIndicator.vue` |

---

## 2. Ce qui a bien fonctionné

### 2.1 Architecture tool-calling complète

- **32 tools** répartis intelligemment par domaine (11 fichiers dans `graph/tools/`)
- `create_tool_loop()` (graph.py:62) : pattern factory qui wrap chaque nœud en boucle LLM ↔ ToolNode
- `MAX_TOOL_CALLS_PER_TURN = 5` (graph.py:56) respectant la clarification Q2 sur le plafond
- Pattern cohérent appliqué aux 9 nœuds métier

### 2.2 Infrastructure partagée propre

- `common.py` expose 3 primitives : `get_db_and_user()`, `log_tool_call()`, `with_retry()`
- `ToolCallLog` model avec index (user_id, created_at DESC) et (tool_name, status) — bien pensé pour debug
- Injection `user_id` + `db` dans `RunnableConfig` (FR-004 automatique, pas de paramètre LLM)

### 2.3 Clarifications cadrées

- 4 questions résolues en session (confirmation, plafond 5, retry 1x, logger tout)
- Chaque clarification a sa justification dans la spec
- Pattern exemplaire d'élaboration de spec

### 2.4 Migration `extract_and_update_profile` propre

- `grep "extract_and_update_profile"` → **aucun résultat dans le code actuel**
- Migration vers le tool `update_company_profile` faite (T055 ✅)
- Events SSE `profile_update` + `profile_completion` émis depuis le tool (profiling_tools.py:99)
- **Contraste avec le dead code dénoncé dans spec 003 §3.1** : la migration a bien eu lieu, mais le `profiling_node` + `chains/extraction.py` (qui appelaient `extract_and_update_profile`) **n'ont PAS été supprimés** — c'est là la vraie dette (déjà P1 #3 dans l'index, attribuée à spec 003)

### 2.5 Refactor SSE avec `astream_events`

- `llm.astream()` remplacé par `graph.astream_events(version="v2")`
- Mapping propre `on_chat_model_stream` → `token`, `on_tool_start` → `tool_call_start`, etc.
- Pattern natif LangGraph utilisé — pas de hack manuel

### 2.6 Frontend `ToolCallIndicator` + parsing

- `useChat.ts` parse les 3 nouveaux events SSE
- `ToolCallIndicator.vue` affiche le label français du tool en cours
- Dark mode + mapping tool_name → label (ex: `update_company_profile` → "Sauvegarde du profil...")

### 2.7 Test d'intégration global

- T058 : `test_full_tool_flow.py` simule un parcours complet profil → ESG → carbone → financement → plan d'action
- Garantie de non-régression transverse

---

## 3. Ce qui a posé problème

### 3.1 🔴 FR-021 (retry) + FR-022 (journalisation) NON appliqués à 9/11 modules

- **FR-021** prescrit : *"1 retry automatique silencieux ... **utilisé par tous les tools**"*
- **FR-022** prescrit : *"chaque tool call DOIT être journalisé avec : nom, paramètres, résultat, durée, statut"*
- T012a : *"Implémenter la journalisation complète des tool calls ... appel après chaque exécution"*
- T012b : *"wrapper `with_retry()` ... **Utilisé par tous les tools des phases suivantes**"*
- **Vérification code** :
  - `grep "with_retry"` dans `backend/app/graph/tools/` → **défini dans common.py mais utilisé nulle part**
  - `grep "log_tool_call"` dans les 11 fichiers tools → **seuls `interactive_tools.py` et `guided_tour_tools.py` l'importent**
- **9 modules sans retry ni journalisation** : `profiling_tools`, `esg_tools`, `carbon_tools`, `financing_tools`, `credit_tools`, `application_tools`, `document_tools`, `action_plan_tools`, `chat_tools`
- **Impact** :
  - En cas d'échec BDD (timeout, connexion perdue), **aucun retry automatique** → user voit l'erreur alors qu'un retry aurait probablement réussi
  - **Aucune trace dans `tool_call_logs`** pour 9 modules → debug impossible en prod sur les tools métier
  - Confirmé empiriquement par les bugs 2026-04-15 (feature 019) où les logs absents ont compliqué l'investigation carbon et guided_tour
- **Cause racine** : le wrapper `with_retry` a été créé mais jamais **appliqué** aux tools. Les tâches T012a/T012b sont marquées `[x]` sans avoir été réellement exécutées sur les tools qui suivent.
- **Leçon** : **5ème cas systémique** de discordance speckit — les tasks `[x]` déclarent l'intention (créer le wrapper) sans vérifier qu'il est consommé par les fichiers qui en dépendent.
- Cohérent avec la dette **P2 #2 "Instrumenter `log_tool_call` dans les tools métier"** déjà dans l'index (doublonnée maintenant avec le retry).

### 3.2 🟠 Création de `profile_update`/`profile_completion` events sans dépréciation de l'ancien chemin

- T055 a migré l'émission des events SSE profil depuis `generate_sse()` vers le tool `update_company_profile`
- **Mais** : `profiling_node` + `chains/extraction.py` (anciens consommateurs de `extract_and_update_profile`) **n'ont pas été supprimés**
- Le code est orphelin — référencé nulle part, mais présent (dette P1 #3 spec 003)
- **Cause racine** : spec 012 a ajouté le nouveau chemin sans fermer l'ancien
- **Leçon** : un refactor architectural doit explicitement lister les composants à retirer dans une tâche dédiée, pas laisser en sous-entendu

### 3.3 🟠 Pas de détection des tools manquants au démarrage

- Le LLM peut hallucinier qu'un tool existe (bug confirmé feature 019 : "outil indisponible" halluciné)
- Si `GUIDED_TOUR_TOOLS` est bindé côté `llm.bind_tools()` mais absent du `ToolNode`, le LLM appelle un tool fantôme → crash
- **Pas de validation au startup** que `bind_tools(X) == ToolNode(X)`
- Bug spec 019 (2026-04-15) a dû ajouter `test_guided_tour_toolnode_registration.py` en anti-régression statique
- **Leçon** : l'infrastructure tool-calling a besoin d'un **health check startup** vérifiant la cohérence bind/ToolNode — ajoutable en spec 012 patch

### 3.4 🟠 FR-019 confirmation finalize : seulement via prompt, pas verrou applicatif

- Clarification Q1 : confirmation requise pour `finalize_esg_assessment` + `finalize_carbon_assessment`
- Implémenté via instructions dans la docstring des tools (lisible par le LLM)
- **Mais** : si le LLM ignore la consigne (hallucination, prompt injection), finalisation directe possible
- Pas de mécanisme applicatif (ex: tool `finalize` refuse si le tour précédent n'a pas un `pending_confirmation` flag)
- **Leçon** : les confirmations critiques doivent être **enforced** côté applicatif, pas seulement documentées dans le prompt

### 3.5 🟡 Pas de limite par tool (fréquence)

- Plafond global 5 tools/tour (FR-020) ✅
- Mais un user malveillant peut déclencher 5 `generate_credit_certificate` en 5 messages = 5 PDFs générés
- Pas de rate limiting par tool (ex: 1 `generate_credit_certificate`/jour max)
- Lié à la dette globale rate limiting (P1 #2)
- **Leçon** : pour les tools coûteux (PDF, LLM long, calcul intensif), rate limit par tool utile

### 3.6 🟡 Pas de trace de la version du prompt utilisée

- Les prompts évoluent (spec 013, 014, 015 ont modifié les prompts)
- `ToolCallLog` ne stocke pas le prompt utilisé au moment de l'appel
- Pas de reproductibilité : "pourquoi ce tool a été appelé dans ce contexte ?" reste dans le noir
- **Leçon** : pour les systèmes agentiques, logger `prompt_version` + `model_version` dans le tool_call_log

### 3.7 🟡 `with_retry` silencieux peut masquer des erreurs systémiques

- FR-021 : retry silencieux sans informer le user
- Pattern OK pour les erreurs transientes (timeout DB)
- Mais si `save_emission_entry` échoue systématiquement (bug code, pas timeout), le retry silencieux **masque l'incident** au lieu de le surfacer
- Pas de circuit breaker : 5 retries successifs échouent → alerte ops
- **Leçon** : retry silencieux + surveillance des taux d'erreur → alerte si > X% d'échecs par tool/heure

---

## 4. Leçons transversales

1. **Infrastructure créée ≠ infrastructure consommée** — T012a/T012b déclarent les primitives, mais leur usage par les tools aurait dû être une tâche distincte vérifiée.
2. **Refactor architectural = liste explicite des composants à retirer** — évite le dead code.
3. **Health checks startup** pour la cohérence bind/ToolNode LangGraph.
4. **Confirmations critiques = enforcement applicatif**, pas seulement prompt.
5. **Rate limiting par tool** pour les tools coûteux.
6. **Logger `prompt_version` + `model_version`** dans tool_call_log.
7. **Retry + circuit breaker** — pas de retry silencieux aveugle.

---

## 5. Actions résiduelles retenues

| # | Action | Priorité | Source |
|---|--------|----------|--------|
| 1 | **Appliquer `with_retry` + `log_tool_call` aux 9 modules** (profiling, esg, carbon, financing, credit, application, document, action_plan, chat) | **P1** | §3.1 |
| 2 | Health check startup : vérifier cohérence `bind_tools() == ToolNode.tools` au démarrage | P2 | §3.3 |
| 3 | Enforcement applicatif des confirmations finalize (flag `pending_confirmation` dans state) | P2 | §3.4 |
| 4 | Logger `prompt_version` + `model_version` dans `ToolCallLog` | P3 | §3.6 |
| 5 | Rate limiting par tool coûteux (PDF, LLM long) | P3 | §3.5 |
| 6 | Circuit breaker sur retry : alerte ops si > X% échecs/heure | P3 | §3.7 |

**Consolidation avec index** :
- §3.1 fusionne avec P2 #2 existant ("instrumenter log_tool_call") → reclasser **P1** en absorbant le wrapper retry + logging
- §3.2 déjà couvert par P1 #3 (suppression dead code spec 003)

**Actions déjà en place** :
- ✅ 32 tools + 11 fichiers + `create_tool_loop`
- ✅ `ToolCallLog` model + migration
- ✅ Plafond 5 tools/tour
- ✅ SSE events + ToolCallIndicator frontend
- ✅ Migration `extract_and_update_profile` → `update_company_profile`
- ✅ Test d'intégration global

---

## 6. Verdict

**Spec 012 est un refactor architectural majeur réussi** : transforme 8 modules passifs en agents LLM actifs avec 32 tools. Infrastructure propre (`create_tool_loop`, `ToolCallLog`, `with_retry`, `log_tool_call`). **Contribution la plus structurante du projet après spec 001.**

**MAIS** : la primitive `with_retry` + la journalisation `log_tool_call` **ne sont pas consommées par 9/11 modules**. C'est le 5ème cas systémique de discordance speckit — cette fois particulièrement coûteux car :
- Les investigations bugs récents (feature 019, 2026-04-15) ont été **ralenties par l'absence de logs** sur les tools métier
- FR-021 (retry) + FR-022 (journalisation) sont cités explicitement dans la spec, implémentés en infrastructure, mais jamais câblés

**Recommandation** : l'action §3.1 (appliquer with_retry + log_tool_call aux 9 modules) doit être **P1 urgent** — c'est une PR de 50-100 lignes qui résout simultanément une dette d'observabilité critique (P2 #2 actuellement) et la non-implémentation de FR-021 (retry).

Spec 012 est aussi la référence architecturale pour tout futur module LLM-actif. Sa maturité n'est pas remise en cause — seule l'exécution finale (câblage des primitives) a raté.
