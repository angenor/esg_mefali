# Audit Rétrospectif — Spec 018 : Widgets Interactifs pour les Questions de l'Assistant IA

**Date d'audit** : 2026-04-16
**Auditeur** : Angenor (Project Lead) + assistant Amelia
**Spec** : [specs/018-interactive-chat-widgets/](../../../specs/018-interactive-chat-widgets/)
**Méthode** : rétrospective post-hoc sur **dernière spec speckit** — 18/18
**Statut rétro** : ✅ Audité — **dernière spec speckit, la plus mature**

---

## 1. Portée de la spec

**Dernière spec speckit du projet.** Widgets interactifs (QCU/QCM/justification) pour les questions fermées de l'assistant IA, inspirés de l'extension Claude Code dans VS Code. Élimine la saisie texte libre répétitive sur les parcours ESG/carbone/profiling/crédit/financement.

| Dimension | Livré |
|-----------|-------|
| Tâches | ~65 sur 95 `[x]` (68 %) — **`[ ]` explicites et justifiés** (honnêteté tasks.md) |
| Discordance tasks↔code | 0 (contrairement aux specs 002/006/008/010) |
| User Stories | 4 (US1-US2-US4 P1, US3 P2) |
| Clarifications | **5 (le plus élevé de toutes les specs)** |
| Nouveau modèle | `InteractiveQuestion` + migration Alembic 018 |
| Nouveau tool | `ask_interactive_question` (4 variantes : qcu/qcm/qcu_justification/qcm_justification) |
| Helper | `WIDGET_INSTRUCTION` (reproduit le pattern STYLE_INSTRUCTION spec 014) |
| Composants frontend | **6 livrés** (5 planifiés + 1 bonus `InteractiveQuestionInputBar.vue`) |
| Events SSE nouveaux | 2 (`interactive_question`, `interactive_question_resolved`) |
| Endpoints REST | 2 (POST `/abandon`, GET `/interactive-questions`) + extension `POST /messages` |
| Nœuds LangGraph touchés | 7 (chat, esg_scoring, carbon, financing, application, credit, action_plan) |
| Tests backend | 34 nouveaux (19 schemas + 7 tool + 8 API) |
| Résultat global | **935 tests backend verts, zéro régression** |

---

## 2. Ce qui a bien fonctionné

### 2.1 ⭐ Clarifications exhaustives (5 questions)

- **5 clarifications en session** — **le plus élevé de toutes les specs du projet**
- Chaque clarification résout une ambiguïté critique :
  - Q1 : qui widgetise ? → LLM à la volée via tool dédié (pas de catalogue backend)
  - Q2 : autorité data → double forme (texte + payload structuré)
  - Q3 : fallback libre → bouton "Répondre autrement" explicite
  - Q4 : reprise module → expiration + régénération
  - Q5 : limite justification → 400 caractères
- **Contraste frappant avec spec 016** (zéro clarification malgré bugs complexes)
- **Leçon** : plus de clarifications en amont → moins de bugs en aval

### 2.2 ⭐ Honnêteté documentaire dans tasks.md

- **Innovation méthodologique** : tasks.md contient une section *"⚠️ État d'implémentation (2026-04-11)"* qui liste explicitement ce qui est **livré vs reporté**
- Les tâches `[ ]` restent visibles avec justifications inline :
  - T011 : "reporté — la table est créée via `Base.metadata.create_all()` en SQLite test"
  - T021 : "(le champ est utilisé via `config["configurable"]["widget_response"]` sans ajout de clé d'état)"
  - T038 : "(non requis : le widget est rendu via props sur `ChatMessage.vue`, pas via parsing markdown — choix architectural pour éviter des artefacts SSE dans le contenu persisté)"
- **Contraste frappant** avec specs 002/006/008/010 où les `[x]` étaient parfois **faussement déclarés** (discordances speckit)
- **Leçon** : accepter explicitement ce qui n'est pas fait > maquiller en `[x]`

### 2.3 Architecture : tool LLM dynamique > catalogue statique

- Choix fondamental (clarification Q1) : **le LLM structure le widget à la volée** via `ask_interactive_question`
- Pas de catalogue statique à maintenir côté backend
- 4 variantes du tool (qcu/qcm/qcu_justification/qcm_justification) couvrent tous les cas
- Validation Pydantic croisée : type ↔ cardinalité ↔ justification

### 2.4 Invariant "1 question pending max / conversation"

- Expiration automatique des questions précédentes à l'insertion d'une nouvelle
- `_expire_pending_questions` + `_resolve_interactive_question` (CLAUDE.md Recent Changes)
- Protège contre les états incohérents (plusieurs questions ouvertes simultanément)

### 2.5 Double forme message (texte + payload structuré)

- Clarification Q2 résout une vraie ambiguïté :
  - **Texte lisible** : continuité conversationnelle, historique, compat client ancien
  - **Payload structuré** : consommation directe par les tools du module actif sans re-parsing LLM
- `active_module_data["widget_response"]` injecté via `config["configurable"]`
- Élégant : un seul message, deux usages

### 2.6 Pattern `WIDGET_INSTRUCTION` hérité de spec 014

- Helper `WIDGET_INSTRUCTION` reproduit le pattern `STYLE_INSTRUCTION` de spec 014
- Injection dans les 6 prompts modules + chat_node
- Cohérence méthodologique avec le projet

### 2.7 Accessibilité ARIA native

- FR-012 : navigation clavier (Tab, Espace/Entrée, flèches)
- `role="radiogroup"`, `role="checkbox"`, `aria-checked`, `aria-describedby`, `aria-invalid`
- **Le seul SC avec 100 % mesurable** : SC-005 "100 % utilisables au clavier"
- Dark mode complet (variantes `dark:` systématiques)

### 2.8 6 composants Vue livrés (dont 1 bonus)

- Planifiés : `InteractiveQuestionHost`, `SingleChoiceWidget`, `MultipleChoiceWidget`, `JustificationField`, `AnswerElsewhereButton`
- Bonus : `InteractiveQuestionInputBar.vue` (non planifié mais livré)
- Tous vérifiés dans `frontend/app/components/chat/`

### 2.9 Résilience : client ancien voit texte lisible (FR-013)

- L'énoncé et les options restent sous forme texte même si le client ne rend pas le widget
- Défense en profondeur
- Compat rétroactive avec les anciens frontends

### 2.10 935 tests backend verts, zero régression

- 34 nouveaux tests (19 schemas + 7 tool + 8 API)
- Pattern anti-régression cohérent avec spec 017 (qui a nettoyé les failures)
- **Base la plus saine** du projet à la fin de la spec speckit

---

## 3. Ce qui a posé problème

### 3.1 🟠 ~30 tâches `[ ]` non réalisées — majoritairement des tests E2E/unit frontend

- Liste (extraits) :
  - T022-T031 : tests unit backend + E2E Playwright US1 — *la plupart `[ ]`*
  - T045-T051 : tests unit + E2E US2 — **tous `[ ]`**
  - T058-T065 : tests US4 — **tous `[ ]`**
  - T071-T077 : tests US3 — **tous `[ ]`**
  - T085 : audit accessibilité formel — `[ ]`
  - T089 : validation manuelle quickstart — `[ ]`
  - T094/T095 : code/security review — `[ ]`
- **Pattern** : les tests unitaires **backend** sont livrés (34 tests = 19 schemas + 7 tool + 8 API), mais les tests **frontend (Vitest) + E2E (Playwright)** sont reportés
- **Impact** :
  - Robustesse backend confirmée (935 tests)
  - Robustesse frontend **non validée formellement** — les 6 composants Vue marchent mais ne sont couverts que par tests manuels
  - Couverture `vitest --coverage` non mesurée
- **Leçon** : même si la transparence des `[ ]` est une amélioration, cela reste une dette. Les tests frontend E2E ajouteraient ~2 jours de dev mais garantiraient la non-régression UX

### 3.2 🟠 SC-002 / SC-003 / SC-004 / SC-006 mesurables en théorie, pas mesurés

- SC-002 : *"Le temps moyen de réponse diminue d'au moins 30 %"* — pas de mesure avant/après
- SC-003 : *"Le taux de complétion des questionnaires augmente d'au moins 15 points"* — pas d'instrumentation
- SC-004 : *"Moins de 2 % des réponses génèrent une incompréhension"* — pas de détection
- SC-006 : *"Temps médian de complétion reste ≤ avant widget"* — pas de mesure
- SC-005 (a11y 100 %) + SC-007 (rechargement) sont les seuls réellement validables
- **Cohérent avec dette transverse P3 #39** (tests de conformité spec 014 non instrumentés)
- **Leçon** : pour une feature UX qui vise un impact mesurable (temps, taux de complétion), l'instrumentation doit être **obligatoire** — sinon on ne saura jamais si la feature vaut le coût

### 3.3 🟠 Clarification Q4 : "expiration + régénération" pas totalement implémentée

- Q4 clarifie : *"widget non répondu → marqué expiré + régénération à la reprise"*
- **Expiration** : ✅ implémentée (`_expire_pending_questions`)
- **Régénération à la reprise** : tâche T044 marquée `[ ]` — *"la consommation fine côté chaque node ESG/profiling est un refinement futur"*
- **Impact** : à la reprise d'un module `in_progress`, le noeud spécialiste **ne détecte pas activement** l'absence de réponse structurée pour régénérer un widget équivalent
- L'utilisateur qui reprend voit un widget expiré grisé mais pas de nouveau widget automatique
- **Leçon** : les clarifications définissent un comportement — l'implémentation partielle doit être tracée explicitement comme feature incomplète, pas comme "spec livrée"

### 3.4 🟡 Bonus `InteractiveQuestionInputBar.vue` non documenté

- Composant livré **hors plan tasks.md**
- Pas de trace dans la spec ni les tasks de pourquoi il a été créé
- Probablement un composant d'intégration UI utile, mais sans documentation
- **Leçon** : les ajouts non planifiés gagnent à être mentionnés avec leur justification (même post-hoc)

### 3.5 🟡 `_has_minimum_profile` branche conditionnelle partagée × 3

- Pattern `STYLE_INSTRUCTION` (spec 014) → `WIDGET_INSTRUCTION` (spec 018) → `GUIDED_TOUR_INSTRUCTION` (spec 019) via la même branche `if _has_minimum_profile`
- Couplage déjà identifié dette spec 014 §3.1 et spec 013
- Spec 018 a **reproduit** le couplage au lieu de l'abstraire
- **Leçon** : quand une 3ème instruction arrive, c'est le signal clair qu'il faut un **framework d'injection** (dette P3 #38)

### 3.6 🟡 Validation Pydantic duplique la logique de cohérence LLM

- Schema Pydantic `InteractiveQuestionCreate` valide :
  - Type ↔ cardinalité (qcu → max_selections=1)
  - Type ↔ justification (qcu_justification → requires_justification=true)
- **Mais** : le prompt `WIDGET_INSTRUCTION` doit aussi dire au LLM comment construire un type cohérent
- **Double validation** : Pydantic (runtime) + prompt (intentionnel)
- Si le LLM se trompe, Pydantic rejette mais la conversation est rompue
- **Alternative** : un seul schéma source de vérité (Pydantic) + introspection pour générer le texte du prompt
- **Leçon** : la cohérence d'un schéma doit être définie une fois, pas dupliquée en docstring/prompt

### 3.7 🟡 Edge case "widget expiré puis reprise" côté UX

- Edge case documenté : *"widget non répondu s'affiche grisé + régénération nouveau widget adapté"*
- Si la régénération ne se déclenche pas (dette §3.3), l'utilisateur voit juste le widget grisé **sans nouveau widget**
- **Impact UX** : confusion potentielle ("la question est morte, comment je continue ?")
- **Leçon** : les edge cases UX doivent avoir un fallback visuel explicite (ex: bouton "Reposer la question" à côté du widget expiré)

### 3.8 🟡 Pas de test de résilience contre le LLM qui abuse du tool

- Un LLM mal prompté pourrait :
  - Appeler `ask_interactive_question` sur une question ouverte (ex: "Décrivez votre projet")
  - Générer un widget avec 15 options (dépassant la limite documentée dans assumptions)
  - Créer un widget pour chaque message (spam)
- Pas de test unitaire "ask_interactive_question rejette si 15+ options" — juste validation Pydantic sur 2-8
- **Leçon** : les tools LLM doivent avoir des garde-fous **testés** contre les abus du modèle

### 3.9 🟡 Pas de métrique d'adoption par module

- Comment savoir si le LLM utilise **réellement** les widgets dans les parcours ESG/carbone/... ?
- Aucune instrumentation "nb de widgets / nb de questions fermées par module"
- SC-001 vise "≥ 70 % des questions widgetisées" mais rien ne le mesure
- **Cohérent avec dette spec 015 §3.5** (instrumenter usage batch) — pattern récurrent

---

## 4. Leçons transversales

1. **Clarifications = qualité** — spec 018 (5 clarifications) est la plus mature, spec 016 (0 clarification) a eu 5 bugs résiduels.
2. **Honnêteté `[ ]` > faux `[x]`** — la transparence documentaire évite la dette cachée.
3. **Implémentation partielle de clarifications** = feature incomplète (pas "livrée").
4. **SC mesurables = instrumentation obligatoire** (dette récurrente 014/015/018).
5. **3ème instruction = framework d'injection obligatoire** (spec 018 a reproduit le couplage spec 014/013).
6. **Cohérence schéma = source de vérité unique** (Pydantic + introspection > Pydantic + prompt duplicate).
7. **Garde-fous contre les abus du LLM** (nombre d'options, fréquence, contexte).
8. **Métriques d'adoption** pour les features UX — sinon impact non vérifiable.

---

## 5. Actions résiduelles retenues

| # | Action | Priorité | Source |
|---|--------|----------|--------|
| 1 | Implémenter **régénération de widget** à la reprise de module `in_progress` (Clarification Q4 partielle) | P2 | §3.3 |
| 2 | Tests Vitest **6 composants Vue** (SingleChoiceWidget, MultipleChoiceWidget, JustificationField, AnswerElsewhereButton, InteractiveQuestionHost, InteractiveQuestionInputBar) | P2 | §3.1 |
| 3 | Tests E2E Playwright pour les 4 user stories (QCU, QCM, justification, fallback) | P2 | §3.1 |
| 4 | **Instrumentation SC** : mesurer temps de réponse avant/après widget, taux de complétion, nb widgets/question fermée par module | P3 | §3.2, §3.9 |
| 5 | Fallback UX "Reposer la question" sur widget expiré | P3 | §3.7 |
| 6 | Garde-fous testés contre abus du LLM (15+ options, widgets sur questions ouvertes, fréquence) | P3 | §3.8 |
| 7 | Documentation `InteractiveQuestionInputBar.vue` | P3 | §3.4 |
| 8 | Introspection Pydantic pour générer le texte du prompt `WIDGET_INSTRUCTION` | P3 | §3.6 |

**Actions déjà en place** :
- ✅ 34 tests backend + 935 tests totaux verts
- ✅ 6 composants Vue avec dark mode + ARIA complet
- ✅ Invariant 1 question pending max
- ✅ Expiration automatique + fallback "Répondre autrement"
- ✅ Validation Pydantic croisée

**Consolidation avec autres audits** :
- §3.5 framework d'injection → dette P3 #38 (spec 014) devient plus urgente (3 usages = abstraction nécessaire)
- §3.2 instrumentation SC → consolider avec dette transverse "métriques d'adoption" (specs 014, 015, 018)

---

## 6. Verdict

**Spec 018 est la plus mature du cycle speckit** — **dernière spec** du cycle, elle **apprend des 17 précédentes** :
- ⭐ **5 clarifications** (record du projet, vs 0 pour spec 016)
- ⭐ **Honnêteté documentaire** : `[ ]` explicites avec justifications (vs faux `[x]` specs 002/006/008/010)
- ⭐ **6 composants Vue livrés** (1 bonus) avec dark mode + ARIA complet
- ⭐ **Validation Pydantic croisée** (type ↔ cardinalité ↔ justification)
- ⭐ **Pattern cohérent** avec spec 014 (WIDGET_INSTRUCTION hérite de STYLE_INSTRUCTION)
- ⭐ **935 tests backend verts**, zero régression

**Dettes résiduelles** sont **principalement des tests frontend** (Vitest + E2E Playwright reportés) et **l'implémentation partielle de la Clarification Q4** (régénération à la reprise). Rien de critique, mais une dette P2 de ~2-3 jours de dev frontend.

**Importance méthodologique** : spec 018 démontre que **speckit peut produire des specs matures** quand on investit dans les clarifications. Le **contraste** entre spec 016 (0 clarification, 5 bugs) et spec 018 (5 clarifications, 0 bug bloquant) est une leçon claire.

**Contexte BMAD** (feedback Angenor saved in memory) : BMAD est la méthode préférée pour les **nouvelles features** depuis 2026-04-16. Spec 018 marque la **fin du cycle speckit** et a bénéficié de ses enseignements cumulés.

**Recommandation** : spec 018 est la **référence finale** pour le cycle speckit du projet. Pattern à retenir pour les futures features BMAD : 5 clarifications min + tasks.md avec `[ ]` explicites + 34+ tests backend + 6+ composants frontend testés.
