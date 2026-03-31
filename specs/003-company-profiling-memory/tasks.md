# Tasks: Profilage Intelligent et Memoire Contextuelle

**Input**: Design documents from `/specs/003-company-profiling-memory/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Inclus conformement au principe IV (Test-First) de la constitution.

**Organization**: Taches groupees par user story pour implementation et test independants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut s'executer en parallele (fichiers differents, pas de dependances)
- **[Story]**: User story concernee (US1, US2, US3, US4, US5)
- Chemins exacts inclus dans les descriptions

---

## Phase 1: Setup

**Purpose**: Initialisation des nouveaux modules et dependances

- [x] T001 Creer la structure du module company dans backend/app/modules/company/__init__.py
- [x] T000 [P] Creer le dossier backend/app/chains/ avec __init__.py
- [x] T000 [P] Creer le dossier frontend/app/components/profile/ vide
- [x] T000 [P] Creer le fichier de types frontend/app/types/company.ts avec les interfaces TypeScript (CompanyProfile, SectorEnum, CompletionResponse, ProfileUpdateEvent)
- [x] T000 [P] Creer le store Pinia frontend/app/stores/company.ts avec le state initial et les actions placeholder

---

## Phase 2: Foundational (Bloquant)

**Purpose**: Infrastructure partagee par toutes les user stories — DOIT etre complete avant les phases suivantes

**CRITICAL**: Aucune user story ne peut commencer avant la fin de cette phase

- [x] T000 Creer le modele SQLAlchemy CompanyProfile dans backend/app/models/company.py avec tous les champs (20 colonnes, SectorEnum, UUIDMixin, TimestampMixin)
- [x] T000 Generer la migration Alembic pour la table company_profiles et l'ajout du champ summary sur conversations (alembic revision --autogenerate)
- [x] T000 Appliquer la migration (alembic upgrade head) et verifier la structure en base
- [x] T000 [P] Creer les schemas Pydantic dans backend/app/modules/company/schemas.py (CompanyProfileResponse, CompanyProfileUpdate, CompletionResponse, ProfileExtraction)
- [x] T00 [P] Creer le service company dans backend/app/modules/company/service.py (get_or_create_profile, update_profile, get_completion — avec calcul separe identite/localisation vs ESG)
- [x] T00 Ecrire les tests unitaires du service company dans backend/tests/test_company_service.py (calcul completion, update partiel, get_or_create)
- [x] T00 Enrichir le ConversationState dans backend/app/graph/state.py : ajouter user_profile (dict | None), context_memory (list[str]), profile_updates (list[dict] | None)
- [x] T00 Refactorer le graphe dans backend/app/graph/graph.py : passer du noeud unique chat a un graphe multi-noeuds avec router_node comme point d'entree et edges conditionnels
- [x] T00 Ecrire les tests du graphe refactore dans backend/tests/test_graph.py (routage correct, state enrichi, edges conditionnels)

**Checkpoint**: Fondation prete — modele en base, service CRUD fonctionnel, graphe multi-noeuds operationnel

---

## Phase 3: User Story 1 - Extraction automatique du profil via conversation (Priority: P1) MVP

**Goal**: Quand l'utilisateur mentionne des informations d'entreprise dans le chat, le systeme les extrait automatiquement et met a jour le profil

**Independent Test**: Envoyer "je fais du recyclage de plastique a Abidjan avec 15 employes" et verifier que le profil contient sector=recyclage, city=Abidjan, employee_count=15

### Tests US1

- [x] T00 [P] [US1] Ecrire le test de la chaine d'extraction dans backend/tests/test_extraction_chain.py (message FR → ProfileExtraction avec bons champs, message vide → aucun champ, message ambigu → seuls champs haute confiance)
- [x] T00 [P] [US1] Ecrire le test du profiling_node dans backend/tests/test_profiling_node.py (extraction + update profil + profile_updates dans le state)
- [x] T00 [P] [US1] Ecrire le test d'integration SSE dans backend/tests/test_chat_profiling.py (message avec infos → events token + profile_update + profile_completion dans le stream)

### Implementation US1

- [x] T00 [US1] Implementer la chaine d'extraction structuree dans backend/app/chains/extraction.py (ChatOpenAI.with_structured_output(ProfileExtraction), prompt avec profil actuel en contexte, instructions d'extraction en francais)
- [x] T00 [US1] Implementer le router_node dans backend/app/graph/nodes.py (heuristiques regex/mots-cles pour detecter infos extractibles, decision de routage chat seul vs chat+profiling)
- [x] T00 [US1] Implementer le profiling_node dans backend/app/graph/nodes.py (appel chaine extraction, filtrage champs non-null, update profil via service, stockage profile_updates dans state)
- [x] T00 [US1] Refactorer le streaming SSE dans backend/app/api/chat.py : passer de llm.astream() a graph.astream_events(), emettre les events profile_update et profile_completion en plus des tokens
- [x] T00 [US1] Charger le profil utilisateur depuis la BDD dans le state au debut de chaque invocation du graphe (dans backend/app/api/chat.py, avant graph.ainvoke/astream_events)
- [x] T00 [US1] Mettre a jour le composable frontend/app/composables/useChat.ts : ecouter les events SSE profile_update et profile_completion, mettre a jour le store company
- [x] T00 [US1] Creer le composant frontend/app/components/chat/ProfileNotification.vue (notification discrete "Profil mis a jour : champ = valeur", dark mode)
- [x] T00 [US1] Integrer ProfileNotification dans frontend/app/components/chat/ChatMessage.vue (affichage apres reception d'un event profile_update)
- [x] T00 [US1] Verifier les tests T015-T017 passent

**Checkpoint**: L'extraction automatique fonctionne de bout en bout — message → extraction → update BDD → notification chat

---

## Phase 4: User Story 2 - Personnalisation contextuelle des reponses (Priority: P1)

**Goal**: Le conseiller adapte ses reponses au profil connu et maintient la continuite entre sessions via la memoire contextuelle

**Independent Test**: Avec un profil sector=agriculture, city=Bamako, verifier que les reponses mentionnent des referentiels agricoles maliens. Demarrer une nouvelle conversation et verifier que le conseiller ne redemande pas le secteur.

### Tests US2

- [x] T00 [P] [US2] Ecrire le test du prompt dynamique dans backend/tests/test_system_prompt.py (prompt contient les infos du profil quand user_profile est present, prompt sans profil quand vide)
- [x] T00 [P] [US2] Ecrire le test de generation de resume dans backend/tests/test_conversation_summary.py (resume genere a la creation d'un nouveau thread, 3 derniers resumes charges dans context_memory)

### Implementation US2

- [x] T00 [US2] Refactorer le prompt systeme dans backend/app/prompts/system.py : creer une fonction build_system_prompt(user_profile, context_memory) qui injecte dynamiquement le profil et les resumes dans le prompt
- [x] T030 [US2] Modifier le chat_node dans backend/app/graph/nodes.py : lire user_profile et context_memory depuis le state, appeler build_system_prompt() au lieu du prompt statique
- [x] T030 [US2] Implementer la generation de resume de conversation dans backend/app/chains/summarization.py (chaine LangChain qui prend les messages d'un thread et retourne un resume concis en francais)
- [x] T030 [US2] Modifier l'endpoint de creation de conversation dans backend/app/api/chat.py : a la creation d'un nouveau thread, generer le resume du thread precedent (si pas deja fait) et le stocker dans conversation.summary
- [x] T030 [US2] Charger les 3 derniers resumes de conversation dans context_memory du state au debut de chaque invocation du graphe (dans backend/app/api/chat.py)
- [x] T030 [US2] Verifier les tests T027-T028 passent

**Checkpoint**: Le conseiller repond de maniere contextualisee et ne repose pas de questions deja connues

---

## Phase 5: User Story 3 - Profilage guide quand le profil est incomplet (Priority: P2)

**Goal**: Quand le profil identite/localisation est < 70% et l'utilisateur n'est pas dans un module specifique, le conseiller integre naturellement des questions de profilage

**Independent Test**: Avec un profil a 40% de completion identite, envoyer une question generique et verifier que la reponse contient une question sur un champ manquant. Envoyer une demande de scoring ESG et verifier que le profilage n'est PAS force.

### Tests US3

- [x] T035 [P] [US3] Ecrire le test du routeur pour l'injection de profilage dans backend/tests/test_router_profiling.py (profil < 70% + message generique → instructions de profilage injectees, profil < 70% + demande ESG → pas d'injection, profil >= 70% → pas d'injection)

### Implementation US3

- [x] T036 [US3] Etendre le router_node dans backend/app/graph/nodes.py : ajouter la logique de detection du seuil 70% (completion identite/localisation), verifier si le message est une demande de module specifique, injecter les instructions de profilage dans le state si conditions remplies
- [x] T037 [US3] Ajouter les instructions de profilage au prompt dans backend/app/prompts/system.py : section optionnelle injectee par build_system_prompt() quand le routeur le demande, listant les champs manquants et demandant au LLM de poser une question naturelle
- [x] T038 [US3] Verifier le test T035 passe

**Checkpoint**: Le conseiller guide naturellement l'utilisateur pour completer son profil sans etre intrusif

---

## Phase 6: User Story 4 - Page profil et edition manuelle (Priority: P2)

**Goal**: L'utilisateur peut consulter et editer son profil entreprise depuis une page dediee avec pourcentage de completion

**Independent Test**: Acceder a /profile, verifier l'affichage des champs par categorie, modifier un champ et verifier la mise a jour du pourcentage

### Tests US4

- [x] T039 [P] [US4] Ecrire les tests des endpoints REST dans backend/tests/test_company_api.py (GET /company/profile, PATCH /company/profile, GET /company/profile/completion — succes, 404, validation 422)

### Implementation US4

- [x] T040 [US4] Creer le router FastAPI dans backend/app/modules/company/router.py (GET /company/profile, PATCH /company/profile, GET /company/profile/completion) avec injection de dependance auth
- [x] T041 [US4] Enregistrer le router company dans backend/app/main.py (app.include_router avec prefix /api/company)
- [x] T042 [US4] Creer le composable frontend/app/composables/useCompanyProfile.ts (fetchProfile, updateProfile, fetchCompletion, avec appels API REST)
- [x] T043 [P] [US4] Creer le composant frontend/app/components/profile/ProfileField.vue (champ individuel : label, valeur, etat rempli/manquant, edition inline, dark mode)
- [x] T044 [P] [US4] Creer le composant frontend/app/components/profile/ProfileProgress.vue (barres de progression identite/localisation et ESG, pourcentage global, dark mode)
- [x] T045 [US4] Creer le composant frontend/app/components/profile/ProfileForm.vue (formulaire organise par categorie : Identite, Localisation, ESG — utilise ProfileField et ProfileProgress, message d'encouragement conversationnel, dark mode)
- [x] T046 [US4] Creer la page frontend/app/pages/profile.vue (layout avec ProfileForm, chargement du profil au mount, sauvegarde sur modification, dark mode)
- [x] T047 [US4] Ajouter le lien "Profil" dans frontend/app/components/layout/AppSidebar.vue avec navigation vers /profile
- [x] T048 [US4] Verifier le test T039 passe

**Checkpoint**: La page profil est fonctionnelle avec edition manuelle et affichage de la completion

---

## Phase 7: User Story 5 - Indicateurs visuels sidebar et chat (Priority: P3)

**Goal**: Badge de completion dans la sidebar et blocs visuels (progress, gauge) dans le chat pour motiver l'utilisateur

**Independent Test**: Verifier le badge dans la sidebar avec le bon pourcentage. Verifier que le conseiller utilise des blocs progress/gauge quand il mentionne le profil.

### Implementation US5

- [x] T049 [US5] Modifier frontend/app/components/layout/AppSidebar.vue : ajouter un badge affichant le pourcentage de completion globale a cote du lien Profil (reactif au store company, dark mode)
- [x] T050 [US5] Charger la completion du profil au demarrage dans le store company (appel GET /company/profile/completion au login ou au mount de AppSidebar)
- [x] T051 [US5] Mettre a jour le prompt systeme dans backend/app/prompts/system.py : ajouter les instructions pour utiliser les blocs progress (completion par categorie) et gauge (celebration 100%) quand le profil est mentionne dans la conversation
- [x] T052 [US5] Ajouter la logique dans le chat_node (backend/app/graph/nodes.py) : quand le profil atteint 100% pour la premiere fois, ajouter une instruction pour celebrer avec un bloc gauge

**Checkpoint**: Les indicateurs visuels motivent l'utilisateur — badge sidebar reactif et blocs visuels dans le chat

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Ameliorations transversales affectant plusieurs user stories

- [x] T053 [P] Verifier le dark mode sur tous les nouveaux composants (ProfileField, ProfileProgress, ProfileForm, ProfileNotification, page profile, badge sidebar)
- [x] T054 [P] Verifier que les messages d'erreur des endpoints REST sont en francais (conformite constitution I)
- [x] T055 Executer la suite de tests complete (pytest backend + vitest frontend) et verifier la couverture >= 80%
- [x] T056 Executer le scenario complet du quickstart.md et documenter les resultats
- [x] T057 Revue de securite : verifier que les endpoints company sont proteges par auth JWT, que les schemas Pydantic valident correctement, que pas de SQL injection possible

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Aucune dependance — peut demarrer immediatement
- **Foundational (Phase 2)**: Depend de Phase 1 — BLOQUE toutes les user stories
- **US1 (Phase 3)**: Depend de Phase 2 — MVP, a faire en premier
- **US2 (Phase 4)**: Depend de Phase 2 — peut etre fait en parallele de US1 (pas de dependance directe)
- **US3 (Phase 5)**: Depend de Phase 2 + T010 (service completion) — peut etre fait en parallele de US1/US2
- **US4 (Phase 6)**: Depend de Phase 2 + T010 (service company) — peut etre fait en parallele de US1/US2/US3
- **US5 (Phase 7)**: Depend de US4 (badge sidebar utilise le meme composant) + US1 (events SSE pour reactivite)
- **Polish (Phase 8)**: Depend de toutes les user stories

### User Story Dependencies

- **US1 (P1)**: Apres Phase 2 — Aucune dependance sur d'autres stories
- **US2 (P1)**: Apres Phase 2 — Aucune dependance sur d'autres stories
- **US3 (P2)**: Apres Phase 2 — Utilise le service completion de Phase 2
- **US4 (P2)**: Apres Phase 2 — Aucune dependance sur d'autres stories
- **US5 (P3)**: Apres US1 (events SSE) + US4 (sidebar) — Depend des stories precedentes

### Within Each User Story

- Tests DOIVENT etre ecrits et ECHOUER avant l'implementation
- Modeles avant services
- Services avant endpoints/noeuds
- Backend avant frontend (pour les endpoints)
- Implementation avant integration

### Parallel Opportunities

- T002, T003, T004, T005 (Setup) — tous en parallele
- T009, T010 (schemas + service) — en parallele apres T006
- T015, T016, T017 (tests US1) — tous en parallele
- T027, T028 (tests US2) — en parallele
- T043, T044 (composants profile) — en parallele
- US1, US2, US3, US4 — peuvent etre faites en parallele par differents developpeurs

---

## Parallel Example: User Story 1

```bash
# Tests US1 en parallele :
Task T015: "Test chaine extraction dans backend/tests/test_extraction_chain.py"
Task T016: "Test profiling_node dans backend/tests/test_profiling_node.py"
Task T017: "Test integration SSE dans backend/tests/test_chat_profiling.py"

# Implementation backend US1 (apres T018) :
Task T019: "router_node dans backend/app/graph/nodes.py"
Task T020: "profiling_node dans backend/app/graph/nodes.py"
# (T019 et T020 sont dans le meme fichier → sequentiels)

# Frontend US1 en parallele (apres T023) :
Task T024: "ProfileNotification.vue"
Task T025: "Integration dans ChatMessage.vue"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T014) — CRITIQUE
3. Complete Phase 3: US1 - Extraction automatique (T015-T026)
4. **STOP et VALIDER**: Tester l'extraction de profil de bout en bout
5. Le chat extrait et stocke les informations d'entreprise

### Incremental Delivery

1. Setup + Foundational → Fondation prete
2. US1 (Extraction) → **MVP** : le chat comprend et memorise l'entreprise
3. US2 (Personnalisation) → Les reponses sont contextualisees au profil
4. US3 (Profilage guide) → Le conseiller comble activement les lacunes du profil
5. US4 (Page profil) → Interface de consultation/edition manuelle
6. US5 (Indicateurs visuels) → Gamification et motivation
7. Polish → Qualite, securite, documentation

### Parallel Team Strategy

Avec plusieurs developpeurs apres Phase 2 :
- Dev A : US1 (Extraction) + US2 (Personnalisation) — backend graphe
- Dev B : US4 (Page profil) — backend REST + frontend page
- Dev C : US3 (Profilage guide) + US5 (Indicateurs) — apres US1/US4

---

## Notes

- [P] = fichiers differents, pas de dependances
- [Story] = traçabilite vers la user story de la spec
- Constitution IV (Test-First) : tests ecrits avant implementation
- Constitution I (Francophone-First) : messages d'erreur et UI en francais
- Constitution VII (Simplicite) : pas d'abstraction prematuree, routeur par heuristiques simples
- Commit apres chaque tache ou groupe logique
- Stopper a tout checkpoint pour valider la story independamment
