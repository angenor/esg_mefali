# Implementation Plan: Interactive Chat Widgets

**Branch**: `018-interactive-chat-widgets` | **Date**: 2026-04-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/018-interactive-chat-widgets/spec.md`

## Summary

Rendre les questions du LLM plus interactives via des widgets cliquables
(QCU, QCM, avec ou sans justification fun) à la manière de l'extension
Claude Code VS Code, afin d'optimiser l'expérience utilisateur et d'accélérer
la collecte d'informations dans les 7 modules métier (ESG, carbone,
financement, candidatures, crédit, plan d'action, profilage).

**Approche technique** :

- Nouveau tool LangChain `ask_interactive_question` injecté dans les 7 nœuds
  LangGraph concernés, avec 4 variantes (qcu / qcm / qcu_justification /
  qcm_justification).
- Transport via le pattern existant `<!--SSE:{…}-->` dans le retour du tool
  (déjà utilisé pour `profile_update` en feature 012).
- 2 nouveaux événements SSE : `interactive_question` et
  `interactive_question_resolved`.
- Persistance dans une nouvelle table satellite `interactive_questions`
  (aucune modification des tables existantes `messages`/`conversations`).
- 1 seule migration Alembic additive, rollback trivial.
- Extension du parseur frontend `useMessageParser` avec un 7ème type de bloc
  + nouveaux composants `InteractiveQuestionHost`, `SingleChoiceWidget`,
  `MultipleChoiceWidget`, `JustificationField`, `AnswerElsewhereButton`.
- Fallback « Répondre autrement » explicite (clarification Q3), expiration
  automatique si un nouveau message assistant arrive (clarification Q4),
  justification limitée à 400 caractères (clarification Q5).

## Technical Context

**Language/Version** : Python 3.12 (backend), TypeScript 5.x strict (frontend)
**Primary Dependencies** :
- Backend : FastAPI, SQLAlchemy async, Alembic, LangGraph ≥ 0.2.0,
  LangChain ≥ 0.3.0, langchain-openai, Pydantic v2
- Frontend : Nuxt 4, Vue 3 Composition API, Pinia, TailwindCSS (dark mode
  obligatoire), composables existants `useChat`, `useMessageParser`

**Storage** : PostgreSQL 16 + pgvector (via asyncpg), Alembic pour migrations.
Nouvelle table `interactive_questions` uniquement.

**Testing** :
- Backend : pytest + pytest-asyncio (unitaires + intégration), ≥ 80% coverage
- Frontend : Vitest (unitaires composants), Playwright (E2E parcours critiques)

**Target Platform** : Web (desktop + mobile responsive), navigateurs
modernes supportant EventSource SSE, connexions lentes tolérées.

**Project Type** : Web application (backend FastAPI + frontend Nuxt 4).

**Performance Goals** :
- Affichage du widget ≤ 200 ms après réception du dernier event SSE
- Clic utilisateur → nouveau tour LLM ≤ 1 s (pas de rafraîchissement page)
- Hydratation historique : ≤ 300 ms pour une conversation de 50 questions

**Constraints** :
- Conservation intégrale du flux texte classique (zéro régression)
- Dark mode obligatoire (constitution CLAUDE.md)
- Accessibilité : navigation clavier, focus visible, ARIA roles sur radios/checkboxes
- UI 100% en français avec accents
- Justification ≤ 400 caractères (clarification Q5)

**Scale/Scope** :
- 7 modules métier concernés (ESG, carbone, financement, candidatures,
  crédit, plan d'action, profilage)
- ~8 options maximum par question (YAGNI, UX mobile)
- Au plus 1 question `pending` simultanément par conversation (invariant)
- ~25 tests nouveaux (10 unitaires backend + 5 intégration backend +
  5 unitaires frontend + 5 E2E)

## Constitution Check

*Gate : doit passer avant Phase 0, re-vérifié après Phase 1.*

### I. Francophone-First & Contextualisation Africaine

- [x] UI 100% française (widgets, libellés, justifications, messages d'erreur)
- [x] Code anglais (noms de tables, fonctions, variables, types)
- [x] Commentaires et docs en français
- [x] Neutralité africaine : les exemples (agriculture, Mobile Money,
  recyclage) respectent le contexte UEMOA/CEDEAO
- [x] Secteur informel pris en compte : les options peuvent inclure des
  réponses adaptées (« Pas de structure formelle », etc.)

### II. Architecture Modulaire

- [x] Le tool `ask_interactive_question` est un nouveau tool générique
  consommable par les 7 nœuds sans couplage spécifique
- [x] Aucun des 8 modules existants ne voit son schéma BDD modifié
- [x] Frontières claires : le frontend consomme le tool via SSE, la BDD
  isolée dans une table satellite, les prompts modules partagent un helper
  unique `backend/app/prompts/widget.py`
- [x] Aucune dépendance inter-modules introduite

### III. Conversation-Driven UX

- [x] **PRINCIPE CŒUR** de la feature : remplacer les listes textuelles par
  des widgets cliquables tout en restant dans une logique conversationnelle
- [x] Fallback texte libre préservé via « Répondre autrement »
- [x] La collecte reste progressive (1 question à la fois, jamais un
  formulaire multi-champs)
- [x] La mémoire contextuelle (feature 013 `active_module_data`) est
  étendue, pas remplacée

### IV. Test-First (NON-NEGOTIABLE)

- [x] Tests unitaires backend écrits avant le tool et les schémas
- [x] Tests d'intégration SSE écrits avant le handler `stream_graph_events`
- [x] Tests unitaires composants Vue écrits avant les composants
- [x] Tests E2E Playwright écrits avant les parcours critiques
- [x] Coverage cible ≥ 80% maintenue

### V. Sécurité & Protection des Données

- [x] Aucun secret introduit
- [x] Toutes les entrées validées via Pydantic (`InteractiveOption`,
  `InteractiveQuestionAnswerInput`)
- [x] Ownership vérifié sur tous les endpoints REST (403 si la question
  appartient à un autre user)
- [x] Aucun SQL brut : SQLAlchemy ORM uniquement
- [x] Longueurs bornées (prompt 500, justification 400, options max 8)
  protègent contre les payloads abusifs
- [x] Pas de données Mobile Money ou crédit directement manipulées
  (la feature est neutre sur ce plan)

### VI. Inclusivité & Accessibilité

- [x] Dark mode natif (Tailwind `dark:` obligatoire)
- [x] Navigation clavier : radios/checkboxes accessibles, focus visible
- [x] Lecteurs d'écran : `role="radiogroup"` / `role="group"`,
  `aria-labelledby`, `aria-describedby`
- [x] Messages d'erreur en français clairs
- [x] Support connexions lentes : widget rendu localement dès réception SSE
  (pas de polling)
- [x] Compteur de caractères visible pour la justification

### VII. Simplicité & YAGNI

- [x] **Pas** de nouvelle table satellite pour les options/réponses : tout
  en JSONB sur la ligne principale
- [x] **Pas** de CREATE TYPE PostgreSQL : VARCHAR + Enum Python (rollback
  simple, ajout de types futurs sans migration destructive)
- [x] **Pas** de modification des tables existantes (messages,
  conversations) : zéro risque de régression
- [x] **Pas** de nouveau parseur frontend : extension de `useMessageParser`
  avec un 7ème type de bloc
- [x] **Pas** de nouveau mécanisme de transport : réutilisation du pattern
  `<!--SSE:-->` déjà en place (feature 012)
- [x] **Pas** de file d'attente, pas de Redis, pas de Celery : tout reste
  synchrone
- [x] 3 lignes similaires > abstraction prématurée (chaque module prompt
  ajoute sa propre mention du tool, helper partagé seulement pour les
  règles d'emploi communes)

**Résultat initial** : ✅ PASS — aucune dérogation nécessaire.

## Project Structure

### Documentation (this feature)

```text
specs/018-interactive-chat-widgets/
├── plan.md                               # Ce fichier
├── spec.md                               # Spécification fonctionnelle
├── research.md                           # Phase 0 : 11 décisions techniques
├── data-model.md                         # Phase 1 : entité InteractiveQuestion
├── quickstart.md                         # Phase 1 : parcours dev + démo
├── contracts/
│   ├── tool-ask-interactive-question.md  # Contrat du tool LangChain
│   ├── sse-events.md                     # Contrat des événements SSE
│   └── rest-endpoints.md                 # Contrat des endpoints REST
├── checklists/
│   └── requirements.md                   # Checklist qualité spec
└── tasks.md                              # Phase 2 (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   └── interactive_question.py            # Nouveau : modèle SQLAlchemy
│   ├── schemas/
│   │   └── interactive_question.py            # Nouveau : schémas Pydantic
│   ├── graph/
│   │   ├── state.py                           # Extension : doc widget_response
│   │   ├── tools/
│   │   │   ├── __init__.py                    # Extension : register tool
│   │   │   └── interactive_tools.py           # Nouveau : ask_interactive_question
│   │   └── nodes.py                           # Extension : widget_response → message
│   ├── api/
│   │   └── chat.py                            # Extension : send_message, 2 nouveaux endpoints
│   └── prompts/
│       ├── widget.py                          # Nouveau : helper WIDGET_INSTRUCTION
│       ├── esg_scoring.py                     # Extension : règle d'emploi widget
│       ├── carbon.py                          # Extension
│       ├── financing.py                       # Extension
│       ├── application.py                     # Extension
│       ├── credit.py                          # Extension
│       ├── action_plan.py                     # Extension
│       └── profiling.py                       # Extension
├── alembic/
│   └── versions/
│       └── 018_create_interactive_questions.py  # Nouveau : migration additive
└── tests/
    ├── unit/
    │   ├── test_ask_interactive_question_tool.py
    │   └── test_interactive_question_schemas.py
    └── integration/
        ├── test_interactive_question_api.py
        └── test_chat_interactive_sse.py

frontend/
├── app/
│   ├── components/
│   │   └── chat/
│   │       ├── MessageParser.vue                # Extension : 7ème type de bloc
│   │       ├── InteractiveQuestionHost.vue      # Nouveau : conteneur
│   │       ├── SingleChoiceWidget.vue           # Nouveau : QCU (radio)
│   │       ├── MultipleChoiceWidget.vue         # Nouveau : QCM (checkbox)
│   │       ├── JustificationField.vue           # Nouveau : textarea 400 car
│   │       └── AnswerElsewhereButton.vue        # Nouveau : fallback
│   ├── composables/
│   │   ├── useChat.ts                           # Extension : 2 nouveaux events
│   │   └── useMessageParser.ts                  # Extension : BLOCK_TYPES + 1
│   └── types/
│       └── interactive-question.ts              # Nouveau : types TS
└── tests/
    ├── unit/
    │   ├── SingleChoiceWidget.spec.ts
    │   ├── MultipleChoiceWidget.spec.ts
    │   └── JustificationField.spec.ts
    └── e2e/
        └── interactive-widgets.spec.ts
```

**Structure Decision** : Web application (backend FastAPI + frontend Nuxt 4)
conformément à l'architecture monolithique modulaire ESG Mefali. Aucun
nouveau projet, aucun nouveau service. Tous les ajouts respectent les
conventions existantes (snake_case Python, PascalCase Vue, kebab-case routes).

## Complexity Tracking

> Aucun écart de constitution à justifier.

La feature reste dans le périmètre YAGNI :

- 1 seule nouvelle table
- 1 seule migration Alembic
- 1 seul tool LangChain
- 2 seuls nouveaux events SSE
- 2 nouveaux endpoints REST (+ extension d'un existant)
- 5 nouveaux composants Vue, tous sous les limites de taille

La seule « complexité » assumée est la coordination multi-fichiers
(7 prompts modules à mettre à jour + 7 nœuds LangGraph à exposer au tool),
mais elle est **obligatoire** pour atteindre le critère de succès SC-001
(≥ 70% des questions éligibles passent par un widget). La factoriser plus
loin serait de l'abstraction prématurée (3 lignes > abstraction spéculative).
