# Tasks: Interface de Chat Conversationnel avec Rendu Visuel Enrichi

**Input**: Design documents from `/specs/002-chat-rich-visuals/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Inclus (Constitution Principe IV: Test-First NON-NEGOTIABLE)

**Organization**: Tasks groupees par user story pour implementation et tests independants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut tourner en parallele (fichiers differents, pas de dependances)
- **[Story]**: User story concernee (US1-US8)
- Chemins exacts des fichiers inclus

---

## Phase 1: Setup

**Purpose**: Installation des dependances et creation des types partages

- [X] T001 Installer les dependances frontend `marked` et `dompurify` dans frontend/package.json
- [X] T002 [P] Creer les types Rich Blocks dans frontend/app/types/richblocks.ts (ChartBlockData, TableBlockData, GaugeBlockData, ProgressBlockData, TimelineBlockData, ParsedSegment)
- [X] T003 [P] Enrichir le systeme prompt avec les instructions de visualisation dans backend/app/prompts/system.py (blocs chart, mermaid, table, gauge, progress, timeline + regles visuelles + palette couleurs)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infrastructure partagee par toutes les user stories

**CRITICAL**: Aucune user story ne peut commencer avant la fin de cette phase

### Tests Foundational

- [X] T004 Test du composable useMessageParser : parser texte simple, blocs visuels, blocs mixtes, JSON invalide, bloc incomplet dans frontend/tests/unit/useMessageParser.test.ts

### Implementation Foundational

- [X] T005 Creer le composable useMessageParser dans frontend/app/composables/useMessageParser.ts (split contenu en segments texte/bloc, detection des 6 types, gestion streaming incomplet)
- [X] T006 [P] Creer le composant BlockError dans frontend/app/components/richblocks/BlockError.vue (affiche code brut + message "Impossible d'afficher la visualisation", dark mode)
- [X] T007 [P] Creer le composant BlockPlaceholder dans frontend/app/components/richblocks/BlockPlaceholder.vue (spinner + "Generation du graphique...", dark mode)
- [X] T008 [P] Creer le composant FullscreenModal dans frontend/app/components/ui/FullscreenModal.vue (modale plein ecran avec slot, bouton fermer, dark mode)

**Checkpoint**: Infrastructure de parsing et composants utilitaires prets

---

## Phase 3: User Story 1 - Conversation de base avec le conseiller ESG (Priority: P1) MVP

**Goal**: L'utilisateur peut creer une conversation, envoyer un message, recevoir une reponse en streaming, et retrouver ses conversations dans l'historique.

**Independent Test**: Creer une conversation, envoyer "Qu'est-ce que l'ESG ?", verifier la reponse en streaming, retrouver la conversation dans l'historique.

### Tests US1

- [X] T009 [P] [US1] Test du composant MessageParser : rendu markdown (listes, gras, code, liens), sanitization XSS dans frontend/tests/unit/MessageParser.test.ts
- [X] T010 [P] [US1] Test backend generation de titre automatique dans backend/tests/test_title_generation.py

### Implementation US1

- [X] T011 [US1] Creer le composant MessageParser dans frontend/app/components/chat/MessageParser.vue (recoit content string, utilise useMessageParser, rend markdown via marked + DOMPurify, route les blocs visuels vers les composants correspondants, affiche BlockPlaceholder pour blocs incomplets)
- [X] T012 [US1] Creer la page chat dans frontend/app/pages/chat.vue (layout deux panneaux : ConversationList a gauche, zone messages + ChatInput a droite, utilise useChat composable, auto-scroll, dark mode)
- [X] T013 [US1] Enrichir ChatMessage.vue dans frontend/app/components/chat/ChatMessage.vue (utiliser MessageParser au lieu de v-html brut, bulles utilisateur vert a droite / assistant gris a gauche, dark mode)
- [X] T014 [US1] Enrichir ChatInput.vue dans frontend/app/components/chat/ChatInput.vue (bloquer envoi pendant streaming, desactiver bouton si message vide, indicateur de chargement anime quand isStreaming)
- [X] T015 [US1] Implementer la generation automatique de titre dans backend/app/graph/nodes.py (appel LLM separe apres premier echange, prompt "Resume en 5 mots max en francais", mise a jour du titre en base)
- [X] T016 [US1] Enrichir les tests chat existants dans backend/tests/test_chat.py (tester creation conversation, envoi message, listing conversations ordonnees)

**Checkpoint**: Conversation de base fonctionnelle avec streaming et historique

---

## Phase 4: User Story 2 - Visualisation de graphiques Chart.js (Priority: P1)

**Goal**: Quand Claude genere un bloc chart, un graphique Chart.js interactif s'affiche avec tooltips, boutons Agrandir et Telecharger.

**Independent Test**: Demander "Montre-moi un exemple de radar chart ESG" → graphique radar interactif dans le chat.

### Tests US2

- [X] T017 [P] [US2] Test du composant ChartBlock : rendu des 6 types (bar, line, pie, doughnut, radar, polarArea), JSON invalide → BlockError, boutons Agrandir/Telecharger presents dans frontend/tests/unit/ChartBlock.test.ts

### Implementation US2

- [X] T018 [US2] Creer le composant ChartBlock dans frontend/app/components/richblocks/ChartBlock.vue (recoit JSON Chart.js, valide type/data/options, rend via vue-chartjs, tooltips interactifs, responsive 250px mobile/300px desktop, bouton Agrandir → FullscreenModal, bouton Telecharger → export PNG via canvas.toDataURL, dark mode)

**Checkpoint**: Graphiques Chart.js rendus dans le chat

---

## Phase 5: User Story 3 - Visualisation de diagrammes Mermaid (Priority: P1)

**Goal**: Quand Claude genere un bloc mermaid, un diagramme SVG s'affiche avec les couleurs de la marque et bouton Agrandir.

**Independent Test**: Demander "Explique-moi le processus de certification ESG" → diagramme Mermaid dans le chat.

### Tests US3

- [X] T019 [P] [US3] Test du composant MermaidBlock : rendu SVG, syntaxe invalide → BlockError, bouton Agrandir present dans frontend/tests/unit/MermaidBlock.test.ts

### Implementation US3

- [X] T020 [US3] Creer le composant MermaidBlock dans frontend/app/components/richblocks/MermaidBlock.vue (recoit code Mermaid, valide via mermaid.parse(), rend SVG via mermaid.render() avec themeVariables marque, responsive, bouton Agrandir → FullscreenModal, dark mode)

**Checkpoint**: Diagrammes Mermaid rendus dans le chat — les 3 user stories P1 sont completes

---

## Phase 6: User Story 4 - Blocs visuels complementaires (Priority: P2)

**Goal**: Tableaux, jauges, barres de progression et frises chronologiques s'affichent correctement dans le chat.

**Independent Test**: Envoyer des prompts declenchant chaque type de bloc et verifier le rendu.

### Tests US4

- [X] T021 [P] [US4] Test du composant TableBlock : rendu tableau, tri par colonne, scroll mobile, highlightColumn dans frontend/tests/unit/TableBlock.test.ts
- [X] T022 [P] [US4] Test du composant GaugeBlock : rendu jauge, couleurs par seuils, animation dans frontend/tests/unit/GaugeBlock.test.ts
- [X] T023 [P] [US4] Test du composant ProgressBlock : rendu barres, labels, couleurs dans frontend/tests/unit/ProgressBlock.test.ts
- [X] T024 [P] [US4] Test du composant TimelineBlock : rendu frise, couleurs par statut (done/in_progress/todo) dans frontend/tests/unit/TimelineBlock.test.ts

### Implementation US4

- [X] T025 [P] [US4] Creer le composant TableBlock dans frontend/app/components/richblocks/TableBlock.vue (recoit JSON headers/rows, rendu tableau Tailwind, tri optionnel sortable, scroll horizontal mobile, highlightColumn fond colore, dark mode)
- [X] T026 [P] [US4] Creer le composant GaugeBlock dans frontend/app/components/richblocks/GaugeBlock.vue (recoit JSON value/max/label/thresholds, arc SVG custom 150x150px, couleur dynamique par seuil, animation remplissage, dark mode)
- [X] T027 [P] [US4] Creer le composant ProgressBlock dans frontend/app/components/richblocks/ProgressBlock.vue (recoit JSON items, barres horizontales empilees, label a gauche/barre au centre/valeur a droite, animation remplissage, dark mode)
- [X] T028 [P] [US4] Creer le composant TimelineBlock dans frontend/app/components/richblocks/TimelineBlock.vue (recoit JSON events, frise verticale, points colores done=vert/in_progress=bleu/todo=gris, description optionnelle, responsive, dark mode)

**Checkpoint**: Les 6 types de blocs visuels sont tous fonctionnels

---

## Phase 7: User Story 5 - Gestion des conversations (Priority: P2)

**Goal**: L'utilisateur peut renommer, supprimer et rechercher ses conversations.

**Independent Test**: Creer plusieurs conversations, en renommer une, en supprimer une, rechercher par titre.

### Tests US5

- [X] T029 [P] [US5] Test du composable useChat enrichi : renameConversation, searchConversations dans frontend/tests/unit/useChat.test.ts

### Implementation US5

- [X] T030 [US5] Enrichir le composable useChat dans frontend/app/composables/useChat.ts (ajout renameConversation via PATCH, searchConversations filtrage local par titre, gestion erreur 429 rate limit avec message francais)
- [X] T031 [US5] Enrichir ConversationList dans frontend/app/components/chat/ConversationList.vue (champ recherche par titre en haut, bouton rename inline avec editable title, confirmation suppression, dark mode)

**Checkpoint**: Gestion complete des conversations

---

## Phase 8: User Story 6 - Mode guide (Priority: P2)

**Goal**: Message d'accueil avec diagramme de navigation quand une nouvelle conversation est creee.

**Independent Test**: Creer une nouvelle conversation et verifier le message d'accueil avec diagramme.

### Implementation US6

- [X] T032 [US6] Creer le composant WelcomeMessage dans frontend/app/components/chat/WelcomeMessage.vue (affiche quand messages.length === 0, diagramme Mermaid des 4 actions principales via MermaidBlock, texte "Comment puis-je vous aider aujourd'hui ?", dark mode)

**Checkpoint**: Mode guide fonctionnel pour les nouvelles conversations

---

## Phase 9: User Story 7 - Experience mobile responsive (Priority: P2)

**Goal**: Sur mobile, drawer lateral pour les conversations, graphiques adaptatifs, tableaux scrollables.

**Independent Test**: Ouvrir le chat sur mobile (< 768px), naviguer conversations, verifier rendu visuels.

### Implementation US7

- [X] T033 [US7] Ajouter l'etat drawer mobile dans frontend/app/stores/ui.ts (conversationDrawerOpen, toggleConversationDrawer)
- [X] T034 [US7] Enrichir la page chat.vue dans frontend/app/pages/chat.vue (responsive: ConversationList dans drawer overlay sur mobile < 768px, bouton hamburger, transition slide, detection swipe pour ouvrir/fermer)
- [X] T035 [US7] Enrichir ConversationList dans frontend/app/components/chat/ConversationList.vue (mode drawer avec bouton fermer, hauteur plein ecran, overlay fond sombre)

**Checkpoint**: Interface responsive et utilisable sur mobile

---

## Phase 10: User Story 8 - Copie de messages et streaming fluide (Priority: P3)

**Goal**: Bouton copier (texte brut sans visuels), indicateur de chargement, placeholder streaming, auto-scroll.

**Independent Test**: Envoyer un message, observer indicateur + placeholder, copier la reponse.

### Implementation US8

- [X] T036 [US8] Ajouter bouton copier dans ChatMessage.vue frontend/app/components/chat/ChatMessage.vue (copie le content brut markdown dans le presse-papiers via navigator.clipboard.writeText, feedback visuel "Copie !")
- [X] T037 [US8] Verifier et polir auto-scroll dans frontend/app/pages/chat.vue (scrollIntoView smooth sur chaque nouveau token streaming, respecter scroll manuel si utilisateur a remonte)

**Checkpoint**: Experience de streaming polie et complete

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Tests E2E, securite, validation finale

- [X] T038 [P] Test E2E du flux chat complet dans frontend/tests/e2e/chat.spec.ts (Playwright: login → /chat → nouvelle conversation → envoi message → streaming → verifier graphique radar → agrandir → telecharger → historique → recherche → mobile drawer)
- [X] T039 Verification securite XSS : tester injection dans JSON de blocs visuels, verifier sanitization DOMPurify sur toutes les sorties markdown
- [X] T040 Validation quickstart.md : suivre le guide de verification rapide de specs/002-chat-rich-visuals/quickstart.md et confirmer tous les points

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Pas de dependance — peut demarrer immediatement
- **Foundational (Phase 2)**: Depend de Phase 1 — BLOQUE toutes les user stories
- **US1 (Phase 3)**: Depend de Phase 2 — MVP minimum
- **US2 (Phase 4)**: Depend de Phase 2 + MessageParser (T011) — peut etre parallele avec US3
- **US3 (Phase 5)**: Depend de Phase 2 + MessageParser (T011) — peut etre parallele avec US2
- **US4 (Phase 6)**: Depend de Phase 2 + MessageParser (T011) — peut etre parallele avec US2/US3
- **US5 (Phase 7)**: Depend de Phase 2 — independant des rich blocks
- **US6 (Phase 8)**: Depend de MermaidBlock (T020) — necessite le rendu Mermaid
- **US7 (Phase 9)**: Depend de chat.vue (T012) — enrichissement responsive
- **US8 (Phase 10)**: Depend de chat.vue (T012) + ChatMessage.vue (T013) — polish
- **Polish (Phase 11)**: Depend de toutes les phases precedentes

### User Story Dependencies

- **US1 (P1)**: Apres Foundational — Aucune dependance sur autres stories
- **US2 (P1)**: Apres Foundational + MessageParser — Peut etre parallele avec US3
- **US3 (P1)**: Apres Foundational + MessageParser — Peut etre parallele avec US2
- **US4 (P2)**: Apres Foundational + MessageParser — Peut etre parallele avec US2/US3/US5
- **US5 (P2)**: Apres Foundational — Independant des rich blocks, parallele avec US2-US4
- **US6 (P2)**: Apres US3 (MermaidBlock) — Dependance sur le composant Mermaid
- **US7 (P2)**: Apres US1 (chat.vue) — Enrichissement responsive de la page existante
- **US8 (P3)**: Apres US1 (ChatMessage.vue) — Polish de l'existant

### Within Each User Story

- Tests DOIVENT etre ecrits et ECHOUER avant l'implementation (TDD)
- Composants utilitaires avant composants dependants
- Implementation avant integration
- Commit apres chaque tache ou groupe logique

### Parallel Opportunities

- T002 + T003 (setup) en parallele
- T006 + T007 + T008 (composants utilitaires foundational) en parallele
- US2 + US3 + US5 peuvent etre travaillees en parallele apres US1
- T025 + T026 + T027 + T028 (4 blocs visuels US4) tous en parallele
- T021 + T022 + T023 + T024 (tests US4) tous en parallele

---

## Parallel Example: User Story 4

```bash
# Lancer tous les tests US4 en parallele :
Task: "Test TableBlock dans frontend/tests/unit/TableBlock.test.ts"
Task: "Test GaugeBlock dans frontend/tests/unit/GaugeBlock.test.ts"
Task: "Test ProgressBlock dans frontend/tests/unit/ProgressBlock.test.ts"
Task: "Test TimelineBlock dans frontend/tests/unit/TimelineBlock.test.ts"

# Lancer tous les composants US4 en parallele :
Task: "Creer TableBlock dans frontend/app/components/richblocks/TableBlock.vue"
Task: "Creer GaugeBlock dans frontend/app/components/richblocks/GaugeBlock.vue"
Task: "Creer ProgressBlock dans frontend/app/components/richblocks/ProgressBlock.vue"
Task: "Creer TimelineBlock dans frontend/app/components/richblocks/TimelineBlock.vue"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completer Phase 1: Setup
2. Completer Phase 2: Foundational (CRITIQUE — bloque toutes les stories)
3. Completer Phase 3: User Story 1 (conversation de base + streaming)
4. **STOP et VALIDER**: Tester US1 independamment
5. Deployer/demo si pret

### Incremental Delivery

1. Setup + Foundational → Infrastructure prete
2. US1 → Conversation fonctionnelle → Demo MVP
3. US2 + US3 (parallele) → Graphiques + Diagrammes → Demo visuels
4. US4 + US5 (parallele) → Blocs complementaires + Gestion conversations → Demo complete
5. US6 + US7 → Mode guide + Mobile → Demo responsive
6. US8 → Polish → Release candidate
7. Polish → Tests E2E + securite → Production ready

---

## Notes

- [P] tasks = fichiers differents, pas de dependances
- [Story] label relie la tache a sa user story pour tracabilite
- Constitution Principe IV impose TDD — tests inclus dans chaque phase
- Dark mode OBLIGATOIRE sur chaque composant (CLAUDE.md)
- Commit apres chaque tache ou groupe logique
- Arreter a tout checkpoint pour valider la story independamment
