# Story 1.5 : Integration du chat complet dans le widget

Status: done

## Story

En tant qu'utilisateur,
je veux retrouver toutes les fonctionnalites du chat (messages, streaming, upload, widgets interactifs, rich blocks) dans le widget flottant,
afin d'avoir une experience identique a l'ancien panneau lateral.

## Acceptance Criteria (BDD)

### AC1 — Envoi et streaming de messages
- **Given** widget ouvert et conversation active
- **When** l'utilisateur envoie un message via `ChatInput`
- **Then** le message apparait dans la liste, la reponse est streamee en temps reel via `useChat().sendMessage()` (FR2)

### AC2 — Upload de documents
- **Given** widget ouvert
- **When** l'utilisateur uploade un document (PDF, DOCX, XLSX, image) via `ChatInput`
- **Then** la barre de progression `documentProgress` s'affiche, le fichier est traite, la reponse apparait dans le widget (FR3)

### AC3 — Widgets interactifs (feature 018)
- **Given** l'assistant envoie un widget interactif QCU/QCM
- **When** le widget est affiche dans le chat
- **Then** `InteractiveQuestionInputBar` remplace `ChatInput` en bas du widget, interaction identique a `pages/chat.vue` (FR9, NFR20)

### AC4 — Rich blocks
- **Given** l'assistant envoie un rich block (chart, table, gauge, mermaid, timeline)
- **When** le block est affiche via `MessageParser`
- **Then** rendu correct avec scroll horizontal si le contenu deborde de la largeur du widget (FR10)

### AC5 — Tool call indicator
- **Given** un tool call est en cours (`activeToolCall` non null)
- **When** `ToolCallIndicator` est affiche
- **Then** l'indicateur est visible et lisible au-dessus de la zone d'input

### AC6 — Dark mode complet
- **Given** dark mode actif
- **When** tous les composants chat sont affiches dans le widget
- **Then** rendu dark mode identique a `pages/chat.vue` (FR35)

### AC7 — Welcome message
- **Given** aucune conversation selectionnee ou messages vides
- **When** le widget est en vue chat
- **Then** `WelcomeMessage` est affiche (les 4 quick-action cards doivent etre cliquables)

### AC8 — Auto-scroll
- **Given** de nouveaux messages arrivent (streaming ou reponse complete)
- **When** l'utilisateur n'a pas scroll vers le haut manuellement
- **Then** le conteneur scrolle automatiquement vers le bas

### AC9 — Zero regression
- **Given** les 13 composants `components/chat/` existants
- **When** integres dans le widget
- **Then** aucune modification de ces composants, 944+ tests backend verts, tous tests frontend verts

## Tasks / Subtasks

- [x] **Task 1** — Ajouter les imports et refs manquants dans `FloatingChatWidget.vue` (AC: 1,2,3,5,7,8)
  - [x] 1.1 Destructurer depuis `useChat()` : `messages`, `isStreaming`, `streamingContent`, `error`, `documentProgress`, `reportSuggestion`, `activeToolCall`, `currentInteractiveQuestion`, `interactiveQuestionsByMessage`, `sendMessage`, `submitInteractiveAnswer`, `onInteractiveQuestionAbandoned`, `fetchMessages`
  - [x] 1.2 Ajouter les refs locales : `messagesContainer` (ref template), `userScrolledUp` (ref boolean)

- [x] **Task 2** — Remplacer le placeholder par la vue chat complete (AC: 1,2,3,4,5,6,7)
  - [x] 2.1 Remplacer le `<div>` placeholder par le template chat
  - [x] 2.2 Structure du template chat avec WelcomeMessage, ChatMessage, ToolCallIndicator, error banner, InteractiveQuestionInputBar/ChatInput

- [x] **Task 3** — Implementer les handlers d'evenements (AC: 1,2,3)
  - [x] 3.1 `handleSend(content: string)` — appelle `sendMessage(content)` avec try/catch, cree conversation si necessaire
  - [x] 3.2 `handleSendWithFile(content: string, file: File)` — appelle `sendMessage(content, file)` avec try/catch
  - [x] 3.3 `handleInteractiveSubmit(answer)` — appelle `submitInteractiveAnswer(...)` avec try/catch
  - [x] 3.4 `handleAbandonAndSend(content: string)` — appelle `onInteractiveQuestionAbandoned(questionId)` puis `sendMessage(content)` avec try/catch
  - [x] 3.5 `handleQuickAction(action: string)` — appelle `handleSend(action)` (pour les cartes WelcomeMessage)

- [x] **Task 4** — Implementer l'auto-scroll (AC: 8)
  - [x] 4.1 `handleScroll()` — detecte si l'utilisateur a scroll vers le haut (seuil 50px)
  - [x] 4.2 `scrollToBottom()` — `messagesContainer.value?.scrollTo({ top: scrollHeight, behavior: 'smooth' })`
  - [x] 4.3 `watch` sur dernier message content pour auto-scroll
  - [x] 4.4 `watch` sur `streamingContent` pour scroll pendant le streaming

- [x] **Task 5** — Gerer le chargement des messages a la selection de conversation (AC: 1,7)
  - [x] 5.1 Dans `handleSelectConversation` : appel `scrollToBottom()` apres `selectConversation` (fetchMessages est deja appele par selectConversation)
  - [x] 5.2 Dans `handleCreateConversation` : la creation reset les messages (deja gere par useChat)

- [x] **Task 6** — Styles, ProfileNotification et responsive dans le widget (AC: 4,6)
  - [x] 6.1 Rich blocks : `overflow-x-auto` ajoute sur le conteneur messages
  - [x] 6.2 Dark mode : tous les nouveaux elements ont les variantes `dark:`
  - [x] 6.3 Document progress : passe via prop `documentProgress` a ChatMessage (gere internement)
  - [x] 6.4 ProfileNotification : gere internement par ChatMessage via `companyStore.recentUpdates` — zero integration explicite necessaire

- [x] **Task 7** — Ecrire les tests Vitest (AC: 9)
  - [x] 7.1 Test : widget affiche WelcomeMessage quand aucun message
  - [x] 7.2 Test : widget affiche ChatMessage pour chaque message
  - [x] 7.3 Test : widget affiche ChatInput quand pas de question interactive pending
  - [x] 7.4 Test : widget affiche InteractiveQuestionInputBar quand question pending
  - [x] 7.5 Test : widget affiche ToolCallIndicator quand activeToolCall
  - [x] 7.6 Test : widget affiche erreur quand `error` est non null
  - [x] 7.7 Test : handleSend appelle sendMessage
  - [x] 7.8 Test : handleSendWithFile appelle sendMessage avec fichier
  - [x] 7.9 Test : auto-scroll apres nouveau message (mock scrollTo)
  - [x] 7.10 Test : dark mode classes presentes sur les nouveaux elements
  - [x] 7.11 35 tests verts, couverture des fonctionnalites principales

## Dev Notes

### Implementation de reference : `pages/chat.vue`

Le fichier `pages/chat.vue` est la **reference d'implementation** (PAS `ChatPanel.vue` qui est une version simplifiee legacy). Reproduire la meme logique pour :
- Auto-scroll avec detection du scroll utilisateur (`userScrolledUp`)
- Gestion de `InteractiveQuestionInputBar` vs `ChatInput` selon `currentInteractiveQuestion?.state`
- Handlers `handleBottomSheetSubmit` et `handleBottomSheetAbandonAndSend` (renommer pour le widget)
- Passage de `interactiveQuestionsByMessage` a chaque `ChatMessage`

### REGLE ABSOLUE : Zero modification des composants chat existants

Les 13 composants dans `components/chat/` sont **read-only** pour cette story :
`ChatInput`, `ChatMessage`, `MessageParser`, `ToolCallIndicator`, `ProfileNotification`, `WelcomeMessage`, `InteractiveQuestionHost`, `SingleChoiceWidget`, `MultipleChoiceWidget`, `JustificationField`, `AnswerElsewhereButton`, `InteractiveQuestionInputBar`, `ConversationList`

Tous sont auto-importes par Nuxt (`pathPrefix: false`). Aucun import explicite necessaire.

### Etat actuel de `FloatingChatWidget.vue`

Le fichier (183 lignes) contient deja :
- Imports : `ref`, `watch`, `nextTick`, `onBeforeUnmount`, `gsap`, `useUiStore`, `useChat`
- Destructuration useChat : `conversations`, `currentConversation`, `searchQuery`, `filteredConversations`, `fetchConversations`, `selectConversation`, `createConversation`, `deleteConversation`, `renameConversation`
- Refs : `widgetRef`, `isVisible`, `currentView: ref<'chat' | 'history'>('chat')`
- Animations GSAP : `animateOpen`/`animateClose` avec `prefersReducedMotion`
- Handlers : `handleToggleHistory`, `handleSelectConversation`, `handleCreateConversation`
- Template : conteneur fixe `bottom-24 right-6 z-50 w-[400px] h-[600px]`, glassmorphism `.widget-glass`
- Vue history avec `ConversationList` + `ChatWidgetHeader`
- **Placeholder div** dans la vue chat a remplacer

### Patterns etablis (stories 1.3 et 1.4)

- **try/catch** sur tous les handlers async (retour review story 1.4, finding F1)
- **Reset `currentView = 'chat'`** a la fermeture du widget (finding F2)
- **Reset `searchQuery = ''`** a la fermeture (finding F4)
- **`prefersReducedMotion`** : `window.matchMedia('(prefers-reduced-motion: reduce)').matches` (non-reactif, deferred W1 pour story 1.7)
- **Aria labels** en francais avec accents : `"Fermer l'assistant IA"`, `"Retour a la conversation"`, `"Historique des conversations"`

### useChat.ts — Exports necessaires (non encore destructures)

```typescript
// A ajouter dans la destructuration existante de useChat()
const {
  // Deja present :
  conversations, currentConversation, searchQuery, filteredConversations,
  fetchConversations, selectConversation, createConversation, deleteConversation, renameConversation,
  // A ajouter :
  messages, isStreaming, streamingContent, error,
  documentProgress, reportSuggestion, activeToolCall,
  currentInteractiveQuestion, interactiveQuestionsByMessage,
  sendMessage, submitInteractiveAnswer, onInteractiveQuestionAbandoned, fetchMessages
} = useChat()
```

### Composants implicites vs explicites

- `MessageParser` est utilise **internement** par `ChatMessage` — pas besoin de l'instancier directement dans le template du widget
- `SingleChoiceWidget`, `MultipleChoiceWidget`, `JustificationField`, `AnswerElsewhereButton` sont utilises **internement** par `InteractiveQuestionHost` et `InteractiveQuestionInputBar`
- `ProfileNotification` doit etre integre **explicitement** dans le template (voir Task 6.4), il est rendu a cote de chaque message assistant dans `pages/chat.vue`

### Contraintes de layout dans le widget 400px

- `InteractiveQuestionInputBar` : les grilles `sm:grid-cols-2` ciblent `min-width: 640px`, donc dans le widget de 400px tout sera en colonne unique — c'est acceptable
- Rich blocks (tables, charts) : `overflow-x-auto` indispensable pour eviter le debordement
- `WelcomeMessage` : les 4 quick-action cards seront plus etroites — fonctionnel en colonne unique

### Items differes pertinents

- **W6** (story 1.3) : `h-[600px]` peut deborder les viewports courts — sera resolu en story 1.6 (redimensionnement)
- **F5** (story 1.4) : double `fetchConversations` sur toggle rapide — edge case mineur, non bloquant

### Project Structure Notes

- Tous les composants copilot sont dans `frontend/app/components/copilot/`
- Les composants chat reutilises sont dans `frontend/app/components/chat/`
- Tests dans `frontend/tests/components/copilot/`
- `useChat.ts` est un singleton module-level dans `frontend/app/composables/useChat.ts` (689 lignes)
- Auto-import Nuxt : aucun import explicite pour les composants (`pathPrefix: false` dans nuxt.config.ts)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.5]
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 1 — module-level state]
- [Source: _bmad-output/planning-artifacts/architecture.md#Regles d'enforcement]
- [Source: _bmad-output/planning-artifacts/prd.md#FR2, FR3, FR9, FR10, FR35]
- [Source: _bmad-output/implementation-artifacts/1-4-en-tete-du-widget-et-historique-des-conversations.md#Review findings]
- [Source: _bmad-output/implementation-artifacts/1-3-bouton-flottant-et-conteneur-du-widget.md#Deferred items]
- [Source: frontend/app/pages/chat.vue — implementation de reference]
- [Source: frontend/app/components/copilot/FloatingChatWidget.vue — fichier a modifier]

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6 (1M context)

### Debug Log References
- Test dark mode initial echoue car banniere erreur conditionnelle (v-if) — corrige en scindant le test en 2 cas (avec/sans erreur)

### Completion Notes List
- Task 1 : Ajoute 14 nouveaux exports destructures depuis `useChat()` + 2 refs locales (`messagesContainer`, `userScrolledUp`) + import type `InteractiveQuestionAnswer`
- Task 2 : Remplace le placeholder par template chat complet — WelcomeMessage, ChatMessage (v-for), ToolCallIndicator, banniere erreur, InteractiveQuestionInputBar/ChatInput conditionnel
- Task 3 : 5 handlers implementes — `handleSend` (cree conversation si absente), `handleSendWithFile`, `handleInteractiveSubmit`, `handleAbandonAndSend`, `handleQuickAction`. Tous avec try/catch.
- Task 4 : Auto-scroll via 2 watchers (messages content + streamingContent), `handleScroll` detecte scroll utilisateur (seuil 50px), `scrollToBottom` smooth
- Task 5 : `handleSelectConversation` enrichi avec `scrollToBottom()` apres selection. `fetchMessages` est deja appele par `selectConversation` dans useChat.
- Task 6 : `overflow-x-auto` pour rich blocks, dark mode complet, `documentProgress` passe via prop a ChatMessage, `ProfileNotification` gere internement par ChatMessage
- Task 7 : 35 tests ecrits et verts — couvrent WelcomeMessage, ChatMessage, ChatInput, InteractiveQuestionInputBar, ToolCallIndicator, erreur, handlers, auto-scroll, dark mode, navigation, animations
- Zero modification des 13 composants chat existants (AC9)
- 96/96 tests frontend verts, 944/944 tests backend verts

### File List
- frontend/app/components/copilot/FloatingChatWidget.vue (modifie)
- frontend/tests/components/copilot/FloatingChatWidget.test.ts (modifie)
- _bmad-output/implementation-artifacts/1-5-integration-du-chat-complet-dans-le-widget.md (modifie)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modifie)

### Review Findings

- [x] [Review][Decision→Defer] D1 — Quick actions WelcomeMessage non cablees (AC7 vs AC9) — differe, gap pre-existant dans pages/chat.vue aussi. AC9 (zero modification) prime. Story dediee necessaire pour ajouter emit a WelcomeMessage.
- [x] [Review][Decision→Accept] D2 — Stream SSE continue apres fermeture du widget — accepte tel quel, le state singleton conserve la reponse pour la reouverture. Aborter serait pire UX.
- [x] [Review][Decision→Defer] D3 — `reportSuggestion` non affiche dans le widget — differe, widget 400px trop etroit pour la banniere. Enhancement future.
- [x] [Review][Patch] P1 — `handleAbandonAndSend` : ajout appel backend `POST /api/chat/interactive-questions/{id}/abandon` (best effort) — aligne avec `pages/chat.vue` ✅
- [x] [Review][Patch] P2 — Catch handlers `handleSend`/`handleSendWithFile` : `error.value` mis a jour si useChat ne l'a pas fait ✅
- [x] [Review][Patch] P3 — `animateClose` : retour immediat quand `prefersReducedMotion` pour eviter `isVisible` bloquee ✅
- [x] [Review][Patch] P4 — `handleCreateConversation` : ajout `selectConversation(conv)` apres creation ✅
- [x] [Review][Patch] P5 — `userScrolledUp` reset a `false` dans `handleSelectConversation`, `handleCreateConversation`, et a l'ouverture du widget ✅
- [x] [Review][Patch] P6 — Watcher auto-scroll observe `messages.value.length` au lieu de `content` du dernier message ✅
- [x] [Review][Patch] P7 — `scrollToBottom` : guard `isVisible` ajoute + scroll initial a l'ouverture du widget ✅
- [x] [Review][Patch] P8 — `aria-controls="copilot-widget"` ajoute sur le bouton flottant + `id="copilot-widget"` sur le widget ✅
- [x] [Review][Patch] P9 — Seuil auto-scroll aligne a 100px (identique a `pages/chat.vue`) ✅
- [x] [Review][Patch] P10 — Guard `isCreatingConversation` ref pour eviter double creation de conversation ✅
- [x] [Review][Defer] W1 — `prefersReducedMotion` non-reactif (snapshot au mount) — differe, deja traque pour story 1.7 [FloatingChatWidget.vue:41] [edge]
- [x] [Review][Defer] W2 — Race condition concurrente dans `sendMessage` de `useChat.ts` (pas de mutex atomique) — differe, pre-existant [useChat.ts:132] [edge]

### Change Log
- 2026-04-13 : Implementation complete de la story 1.5 — integration du chat complet dans le widget flottant. FloatingChatWidget.vue passe de 183 a 334 lignes. 35 tests Vitest, zero regression.
