# Audit Rétrospectif — Spec 001 : Foundation Technique ESG Mefali

**Date d'audit** : 2026-04-16
**Auditeur** : Angenor (Project Lead) + assistant Amelia
**Spec** : [specs/001-technical-foundation/](../../../specs/001-technical-foundation/)
**Méthode** : rétrospective post-hoc (spec close depuis ~2 semaines, 17 specs construites dessus)
**Statut rétro** : ✅ Complet

---

## 1. Portée de la spec

Socle technique complet de la plateforme. Aucune logique métier ESG.

| Dimension | Livré |
|-----------|-------|
| Tâches | 69 / 69 `[X]` (100 %) |
| User Stories | 5 (US1 Auth P1, US2 Chat IA P1, US3 Docker P1, US4 UI P2, US5 Health P3) |
| Phases | 8 (Setup → Foundational → US1→US5 → Polish) |
| Constitution gates | 7 / 7 passés |
| Couverture tests visée | ≥ 80 % (SC-006) |
| Specs aval construites dessus | 17 (002 → 018) — dont **5 correctifs** (013, 014, 015, 016, 017) |

---

## 2. Ce qui a bien fonctionné

### 2.1 Décisions d'architecture valides 6 mois plus tard

- **AD-001 (JWT stateless)** — toujours en place, pas de refactor nécessaire.
- **AD-002 (LangGraph + AsyncPostgresSaver)** — a permis d'ajouter 8 modules métier (esg, carbon, financing, application, credit, action_plan, document, profiling) sans refactor lourd du système de conversation.
- **AD-003 (chat latéral persistant)** — pattern central, étendu en widget flottant dans spec 019.
- **AD-004 (SSE `fetch` + `ReadableStream`)** — a tenu la charge jusqu'aux events `tool_call_*`, `interactive_question`, `guided_tour`.

### 2.2 Research R-002 prescient

Rejet explicite de `ChatAnthropic` pour OpenRouter (bug `/v1/v1/messages`). Choix `ChatOpenAI + base_url OpenRouter` : décision structurante qui a évité une dette majeure.

### 2.3 Discipline de phases

- Séparation Setup / Foundational / User Stories claire.
- Checkpoints entre phases → validation MVP (US1) avant d'engager US2.
- Parallélisation explicite documentée (US4/US5 ⟂ US1/US2).

### 2.4 Test-First respecté sur US1, US2, US5

Tests écrits avant implémentation (T019-T020, T034, T063). Couverture ≥ 80 % vérifiée (T033, T051, T068).

---

## 3. Ce qui a posé problème (révélé a posteriori)

### 3.1 `ConversationState` sous-dimensionné

- Spec 013 a dû ajouter `active_module` + `active_module_data` pour fixer le routing multi-tour.
- Spec 003 a ajouté `current_page` → **pas d'annotation reducer** détectée plus tard (dette story 3-1 de spec 019).
- **Cause racine** : T040 a livré un TypedDict sans anticiper les modules futurs.
- **Leçon** : `ConversationState` est un contrat extensible, pas une struct de convenance.

### 3.2 `chat_node` monolithique → explosion en 9 nœuds

- T041 a livré un unique `chat_node`.
- Spec 012 (tool-calling) a dû injecter 32 tools dans 9 nœuds — refactor architectural majeur.
- AD-002 anticipait l'ajout de nœuds métier mais pas l'injection de `ToolNode` + boucle conditionnelle.

### 3.3 Composables non migrés vers `apiFetch`

- `useAuth`, `useChat` créés sans intercepteur 401 centralisé.
- Dette retrouvée story 7-2 (spec 019) : 7 composables à migrer (`useApplications`, `useCreditScore`, `useActionPlan`, `useReports`, `useDocuments`, `useCompanyProfile`, `useChat`).
- **Leçon** : l'intercepteur 401 transparent aurait dû être une brique Foundational (Phase 2).

### 3.4 SSE whitelist implicite dans `generate_sse`

- T045 a introduit un `elif` sur `event["type"]` sans contrat explicite.
- Conséquence : BUG event `guided_tour` drop silencieusement (feature 019, 2026-04-15).
- `profile_update` / `profile_completion` dans le même état latent (non investigué).
- **Leçon** : une whitelist → un test statique qui force la cohérence émetteur ↔ forwarder.
- **Correctif** : test `test_sse_event_whitelist.py` ajouté a posteriori.

### 3.5 Pas d'observabilité sur les tool calls initialement

- `tool_call_logs` n'est apparu qu'avec la spec 012.
- Bugs comme "LLM hallucine outil indisponible" (feature 019) impossibles à diagnostiquer sans logs.
- Les tools métier n'instrumentent toujours pas `log_tool_call` (seuls `interactive_tools` et `guided_tour_tools` le font).

### 3.6 Tests E2E absents à l'origine

- Phase 8 Polish (T067) : "quickstart.md à suivre" → pas d'E2E Playwright automatisé.
- Les parcours E2E n'ont été formalisés qu'avec spec 019 stories 8-1 à 8-3.
- Couverts aujourd'hui par Fatou/Moussa/Aminata, donc dette résorbée naturellement.

---

## 4. Leçons transversales

1. **Le ConversationState est un contrat** — chaque champ impose un reducer (`Annotated[..., reducer]`), documenter qui écrit / qui lit / comportement en merge.
2. **Les points d'extension SSE doivent être explicites** — whitelist → test statique de cohérence.
3. **Foundational doit inclure l'observabilité** — `tool_call_logs` + traces LangGraph dès la Phase 2.
4. **Les extensibilité du graphe LangGraph doit être prévue dès l'origine** — `ToolNode` + boucle conditionnelle, pas juste `chat_node`.

---

## 5. Actions résiduelles retenues

| # | Action | Priorité | Statut | Source |
|---|--------|----------|--------|--------|
| 1 | Migration composables → `apiFetch` (7 composables) | P1 | À ouvrir | Deferred story 7-2 |
| 2 | Reducer `current_page` dans `ConversationState` | P2 | À ouvrir | Deferred story 3-1 |
| 3 | Instrumenter `log_tool_call` dans les tools métier | P2 | À ouvrir | Deferred carbon bug 2026-04-14 |
| 4 | ~~E2E smoke tests foundation~~ | ~~P3~~ | **DIFFÉRÉ** | Couvert par parcours Fatou/Moussa/Aminata |

**Actions déjà en place** :
- ✅ Test anti-régression whitelist SSE (`test_sse_event_whitelist.py`)
- ✅ Observabilité `tool_call_logs` (spec 012)
- ✅ `active_module` dans state (spec 013)

---

## 6. Observations personnelles d'Angenor

> "Je regrette d'avoir développé avec speckit, j'aurais dû le faire avec BMAD qui est plus rigoureux. Je crains que certaines choses aient été négligées."

**Lecture de cet audit à la lumière de cette remarque** :

- Les 6 problèmes identifiés en §3 confirment partiellement cette inquiétude : `ConversationState` sous-dimensionné, whitelist SSE implicite, observabilité absente, E2E manquants à l'origine — des négligences qu'une méthode plus rigoureuse (checklists architecture, revue adversariale, edge-case hunter) aurait probablement capturées en amont.
- **Inversement** : 17 specs ont pu être construites dessus en ~2 semaines, les 5 specs-correctifs (013-017) représentent une part acceptable du volume, et les décisions structurantes (AD-002, R-002) tiennent encore. La méthode speckit a tenu sur le "what" mais a été faible sur le "how to verify completeness".
- **Décision pragmatique pour la suite** : ne pas refaire les 18 specs sous BMAD (coût prohibitif). Utiliser ce rolling audit spec-par-spec pour capturer les dettes, puis appliquer BMAD aux **nouvelles** features à partir d'aujourd'hui (le projet tourne déjà sous BMAD depuis la spec 019-guided-tour).

---

## 7. Verdict

**Spec 001 livrée à 100 %, fondation solide dans ses grandes lignes, mais 3 dettes P1/P2 résiduelles héritées de négligences de conception (state, intercepteur 401, observabilité).**

Les correctifs ne sont pas bloquants pour le projet tel qu'il tourne aujourd'hui, mais les ouvrir comme stories BMAD dédiées évitera qu'ils reviennent en tant que bugs live.
