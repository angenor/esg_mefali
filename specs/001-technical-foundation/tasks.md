# Tasks: Foundation Technique ESG Mefali

**Input**: Design documents from `/specs/001-technical-foundation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Inclus — la constitution exige Test-First (Principe IV, NON-NEGOTIABLE).

**Organization**: Taches groupees par user story pour une implementation et des tests independants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut etre execute en parallele (fichiers differents, pas de dependances)
- **[Story]**: User story associee (US1, US2, US3, US4, US5)
- Chemins exacts inclus dans les descriptions

---

## Phase 1: Setup (Infrastructure partagee)

**Purpose**: Initialisation du projet et structure de base

- [X] T001 Creer la structure de repertoires backend/ conforme au plan dans backend/app/
- [X] T002 Initialiser le projet Python avec requirements.txt et requirements-dev.txt dans backend/
- [X] T003 Creer la structure de repertoires frontend/ conforme au plan
- [X] T004 Initialiser le projet Nuxt 4 avec TypeScript strict dans frontend/
- [X] T005 [P] Configurer TailwindCSS 4 avec le design system (couleurs marque) dans frontend/assets/css/main.css et frontend/tailwind.config.ts
- [X] T006 [P] Creer le fichier .env.example a la racine avec toutes les variables d'environnement
- [X] T007 [P] Creer le fichier .gitignore complet (Python + Node + IDE) a la racine
- [X] T008 [P] Installer et configurer les plugins client-only GSAP dans frontend/plugins/gsap.client.ts
- [X] T009 [P] Installer et configurer le plugin client-only Chart.js (vue-chartjs) dans frontend/plugins/chartjs.client.ts
- [X] T010 [P] Installer et configurer Mermaid.js comme plugin client-only dans frontend/plugins/mermaid.client.ts

---

## Phase 2: Foundational (Prerequis bloquants)

**Purpose**: Infrastructure de base qui DOIT etre terminee AVANT toute user story

**CRITICAL**: Aucune user story ne peut commencer avant la fin de cette phase

- [X] T011 Configurer pydantic-settings pour la gestion de config dans backend/app/core/config.py
- [X] T012 Configurer SQLAlchemy async engine et session factory dans backend/app/core/database.py
- [X] T013 Creer la DeclarativeBase SQLAlchemy dans backend/app/models/base.py
- [X] T014 Initialiser Alembic avec configuration async dans backend/alembic/
- [X] T015 [P] Creer le point d'entree FastAPI avec lifespan, CORS et inclusion des routers dans backend/app/main.py
- [X] T016 [P] Creer les types TypeScript partages (User, Conversation, Message, Token) dans frontend/types/index.ts
- [X] T017 [P] Creer le Pinia store UI (sidebar ouverte/fermee, theme) dans frontend/stores/ui.ts
- [X] T018 Configurer les fixtures de test pytest (client async httpx, db test) dans backend/tests/conftest.py

**Checkpoint**: Foundation prete — l'implementation des user stories peut commencer

---

## Phase 3: User Story 1 — Inscription et connexion (Priority: P1) MVP

**Goal**: Un utilisateur peut s'inscrire, se connecter, et acceder a la page d'accueil protegee

**Independent Test**: Creer un compte, se connecter, verifier l'acces a la page protegee, tester le refus d'acces sans token

### Tests pour User Story 1

> **Ecrire ces tests EN PREMIER, verifier qu'ils ECHOUENT avant l'implementation**

- [X] T019 [P] [US1] Tests des endpoints auth (register, login, refresh, me) dans backend/tests/test_auth.py
- [X] T020 [P] [US1] Tests du modele User (creation, unicite email, hashing) dans backend/tests/test_auth.py

### Implementation User Story 1

- [X] T021 [US1] Creer le modele SQLAlchemy User dans backend/app/models/user.py
- [X] T022 [US1] Creer la migration Alembic 001_create_users (table users + index email + pgvector) dans backend/alembic/versions/
- [X] T023 [P] [US1] Creer les schemas Pydantic auth (RegisterRequest, LoginRequest, TokenResponse, UserResponse) dans backend/app/schemas/auth.py
- [X] T024 [US1] Implementer les fonctions de securite (hash_password, verify_password, create_access_token, create_refresh_token, decode_token) dans backend/app/core/security.py
- [X] T025 [US1] Implementer la dependance get_current_user dans backend/app/api/deps.py
- [X] T026 [US1] Implementer le router /api/auth (register, login, refresh, me) dans backend/app/api/auth.py
- [X] T027 [US1] Creer le Pinia store auth (user, tokens, actions login/register/refresh/logout) dans frontend/stores/auth.ts
- [X] T028 [US1] Creer le composable useAuth (login, register, refresh, logout, isAuthenticated) dans frontend/composables/useAuth.ts
- [X] T029 [US1] Creer le middleware auth global Nuxt dans frontend/middleware/auth.global.ts
- [X] T030 [US1] Creer la page de connexion dans frontend/pages/login.vue
- [X] T031 [P] [US1] Creer la page d'inscription dans frontend/pages/register.vue
- [X] T032 [US1] Creer la page d'accueil protegee (placeholder dashboard) dans frontend/pages/index.vue
- [X] T033 [US1] Verifier que les tests T019-T020 passent et couvrent >= 80% du code auth

**Checkpoint**: US1 completement fonctionnelle — inscription, connexion, acces protege

---

## Phase 4: User Story 2 — Conversation IA de base (Priority: P1)

**Goal**: Un utilisateur connecte peut envoyer un message et recevoir une reponse streamee de l'IA, avec persistance des conversations multiples

**Independent Test**: Envoyer un message, verifier la reponse streamee, recharger et verifier l'historique, creer une nouvelle conversation

### Tests pour User Story 2

> **Ecrire ces tests EN PREMIER, verifier qu'ils ECHOUENT avant l'implementation**

- [X] T034 [P] [US2] Tests des endpoints chat (CRUD conversations, envoi message, streaming) dans backend/tests/test_chat.py

### Implementation User Story 2

- [X] T035 [US2] Creer le modele SQLAlchemy Conversation dans backend/app/models/conversation.py
- [X] T036 [US2] Creer le modele SQLAlchemy Message dans backend/app/models/message.py
- [X] T037 [US2] Creer les migrations Alembic 002_create_conversations et 003_create_messages dans backend/alembic/versions/
- [X] T038 [P] [US2] Creer les schemas Pydantic chat (ConversationCreate, ConversationResponse, MessageCreate, MessageResponse, PaginatedResponse) dans backend/app/schemas/chat.py
- [X] T039 [US2] Creer le prompt systeme de base (francais, professionnel, bienveillant) dans backend/app/prompts/system.py
- [X] T040 [US2] Definir le ConversationState (TypedDict) dans backend/app/graph/state.py
- [X] T041 [US2] Implementer le chat_node (ChatOpenAI via OpenRouter, streaming) dans backend/app/graph/nodes.py
- [X] T042 [US2] Configurer le AsyncPostgresSaver (checkpointer) dans backend/app/graph/checkpointer.py
- [X] T043 [US2] Compiler le graphe LangGraph (StateGraph, chat_node, checkpointer) dans backend/app/graph/graph.py
- [X] T044 [US2] Initialiser le graphe LangGraph dans le lifespan FastAPI dans backend/app/main.py
- [X] T045 [US2] Implementer le router /api/chat (CRUD conversations, envoi message + SSE streaming) dans backend/app/api/chat.py
- [X] T046 [US2] Creer le composable useChat (SSE fetch + ReadableStream, gestion messages, CRUD conversations) dans frontend/composables/useChat.ts
- [X] T047 [US2] Creer le composant ChatMessage (bulle user/assistant, streaming) dans frontend/components/chat/ChatMessage.vue
- [X] T048 [P] [US2] Creer le composant ChatInput (zone de saisie, validation 1-5000 chars, envoi) dans frontend/components/chat/ChatInput.vue
- [X] T049 [P] [US2] Creer le composant ConversationList (liste threads, creation, selection) dans frontend/components/chat/ConversationList.vue
- [X] T050 [US2] Creer le composant ChatPanel (panneau lateral persistant, assemblage des sous-composants) dans frontend/components/layout/ChatPanel.vue
- [X] T051 [US2] Verifier que les tests T034 passent et couvrent >= 80% du code chat

**Checkpoint**: US2 completement fonctionnelle — conversation IA streamee avec persistance multi-threads

---

## Phase 5: User Story 3 — Environnement de developpement (Priority: P1)

**Goal**: Un developpeur peut lancer les 3 services (frontend, backend, postgres) avec une seule commande

**Independent Test**: Cloner le projet, lancer `make dev`, verifier les 3 services accessibles

### Implementation User Story 3

- [X] T052 [P] [US3] Creer le Dockerfile backend dans backend/Dockerfile
- [X] T053 [P] [US3] Creer le Dockerfile frontend dans frontend/Dockerfile
- [X] T054 [US3] Creer le docker-compose.yml avec 3 services (frontend, backend, postgres pgvector) a la racine
- [X] T055 [US3] Creer le Makefile avec commandes (dev, build, migrate, test, test-back, test-front, down, logs) a la racine
- [X] T056 [US3] Creer le README.md avec instructions de setup local a la racine

**Checkpoint**: US3 completement fonctionnelle — environnement de dev lance en une commande

---

## Phase 6: User Story 4 — Navigation et interface de base (Priority: P2)

**Goal**: Layout responsive avec sidebar retractable, header, panneau chat persistant, et notifications toast

**Independent Test**: Naviguer entre pages, replier/deployer la sidebar, verifier le responsive mobile, declencher des toasts

### Implementation User Story 4

- [X] T057 [US4] Creer le composant AppSidebar (navigation retractable, responsive) dans frontend/components/layout/AppSidebar.vue
- [X] T058 [P] [US4] Creer le composant AppHeader (logo, menu utilisateur, bouton menu mobile) dans frontend/components/layout/AppHeader.vue
- [X] T059 [US4] Creer le composant ToastNotification (succes, erreur, info, auto-dismiss) dans frontend/components/ui/ToastNotification.vue
- [X] T060 [US4] Creer le composable useToast (show, dismiss, types) dans frontend/composables/useToast.ts
- [X] T061 [US4] Assembler le layout par defaut (sidebar + header + contenu + chat panel) dans frontend/layouts/default.vue
- [X] T062 [US4] Configurer app.vue pour utiliser le layout et integrer le toast global dans frontend/app.vue

**Checkpoint**: US4 completement fonctionnelle — layout responsive avec tous les elements

---

## Phase 7: User Story 5 — Verification de sante du systeme (Priority: P3)

**Goal**: Endpoint health check qui indique l'etat du backend et de la base de donnees

**Independent Test**: Requeter /api/health, verifier la reponse positive, simuler une panne DB

### Tests pour User Story 5

- [X] T063 [P] [US5] Tests du endpoint health (sain et degrade) dans backend/tests/test_health.py

### Implementation User Story 5

- [X] T064 [US5] Implementer le router /api/health (verification DB, version) dans backend/app/api/health.py
- [X] T065 [US5] Verifier que les tests T063 passent

**Checkpoint**: US5 completement fonctionnelle — health check operationnel

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Ameliorations transversales affectant plusieurs user stories

- [X] T066 [P] Creer le fichier .env.example backend avec valeurs documentees dans backend/.env.example
- [X] T067 Validation de bout en bout : suivre le quickstart.md pour verifier le parcours complet
- [X] T068 Verifier la couverture de test globale >= 80% sur le backend
- [X] T069 Nettoyage et revue de code finale (imports inutilises, console.log, TODO restants)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Pas de dependances — peut commencer immediatement
- **Foundational (Phase 2)**: Depend de la fin du Setup — BLOQUE toutes les user stories
- **US1 (Phase 3)**: Depend de Foundational — pas de dependances sur d'autres stories
- **US2 (Phase 4)**: Depend de Foundational + US1 (authentification requise pour le chat)
- **US3 (Phase 5)**: Depend de US1 + US2 (les services doivent exister pour Docker Compose)
- **US4 (Phase 6)**: Depend de Foundational — peut etre fait en parallele avec US1/US2 (pure UI)
- **US5 (Phase 7)**: Depend de Foundational — peut etre fait en parallele avec US1/US2
- **Polish (Phase 8)**: Depend de la completion de toutes les user stories souhaitees

### User Story Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational)
                      ├──→ US1 (Auth) ──→ US2 (Chat) ──→ US3 (Docker)
                      ├──→ US4 (UI) [parallele]
                      └──→ US5 (Health) [parallele]
                                                            └──→ Phase 8 (Polish)
```

### Within Each User Story

- Tests DOIVENT etre ecrits et ECHOUER avant l'implementation
- Modeles avant services
- Services avant endpoints/routers
- Backend avant frontend (pour une meme story)
- Implementation de base avant integration

### Parallel Opportunities

- T005-T010 (Setup) : tous parallelisables
- T011-T018 (Foundational) : T015, T016, T017 parallelisables
- US1 : T019-T020 (tests) parallelisables, T023 parallelisable avec T021, T030-T031 parallelisables
- US2 : T038 parallelisable avec T035-T036, T047-T049 parallelisables
- US4 et US5 : peuvent etre faites en parallele avec US1/US2 (pas de dependances backend)
- US3 : T052-T053 (Dockerfiles) parallelisables

---

## Parallel Example: User Story 1

```bash
# Lancer les tests en parallele :
Task T019: "Tests endpoints auth dans backend/tests/test_auth.py"
Task T020: "Tests modele User dans backend/tests/test_auth.py"

# Lancer les schemas en parallele avec les modeles :
Task T021: "Modele User dans backend/app/models/user.py"
Task T023: "Schemas Pydantic auth dans backend/app/schemas/auth.py"

# Lancer les pages frontend en parallele :
Task T030: "Page login dans frontend/pages/login.vue"
Task T031: "Page register dans frontend/pages/register.vue"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completer Phase 1: Setup
2. Completer Phase 2: Foundational (CRITIQUE — bloque toutes les stories)
3. Completer Phase 3: User Story 1 (Inscription/Connexion)
4. **STOP et VALIDER**: Tester US1 independamment
5. Deployer/demo si pret

### Incremental Delivery

1. Setup + Foundational → Foundation prete
2. Ajouter US1 (Auth) → Tester → Demo (MVP!)
3. Ajouter US2 (Chat IA) → Tester → Demo
4. Ajouter US3 (Docker) → Tester → Demo
5. Ajouter US4 (UI/Layout) + US5 (Health) → Tester → Demo finale
6. Chaque story ajoute de la valeur sans casser les precedentes

### Parallel Team Strategy

Avec plusieurs developpeurs :

1. L'equipe complete Setup + Foundational ensemble
2. Une fois Foundational terminee :
   - Dev A : US1 (Auth backend + frontend)
   - Dev B : US4 (Layout/UI) + US5 (Health)
3. Apres US1 terminee :
   - Dev A : US2 (Chat IA)
   - Dev B : US3 (Docker/DevOps)

---

## Notes

- [P] = fichiers differents, pas de dependances
- [Story] = label tracabilite vers la user story spec.md
- Chaque user story est completable et testable independamment
- Verifier que les tests echouent avant d'implementer
- Commiter apres chaque tache ou groupe logique
- S'arreter a chaque checkpoint pour valider la story
