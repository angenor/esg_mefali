# Story 2.1 : Suppression de la page /chat et de ChatPanel

Status: done

## Story

En tant qu'utilisateur,
je veux une seule interface de chat (le widget flottant),
afin de ne pas etre perdu entre deux points d'acces differents a l'assistant.

## Acceptance Criteria

1. **AC1 — Suppression de la page /chat**
   - **Given** le fichier `pages/chat.vue` existe
   - **When** un developpeur le supprime
   - **Then** la route `/chat` n'est plus accessible (404 ou redirection)
   - **And** aucune regression dans le routing Nuxt des autres pages

2. **AC2 — Suppression de ChatPanel**
   - **Given** le composant `components/layout/ChatPanel.vue` existe
   - **When** un developpeur le supprime
   - **Then** `layouts/default.vue` ne reference plus ChatPanel
   - **And** le FloatingChatWidget (Epic 1) est le seul point d'acces au chat dans le layout

3. **AC3 — Zero regression tests**
   - **Given** la suppression est effectuee
   - **When** on execute la suite de tests existante
   - **Then** zero regression — tous les tests frontend passent
   - **And** les tests qui referençaient ChatPanel ou la page `/chat` sont mis a jour ou supprimes

4. **AC4 — Couverture de tests >= 80%**
   - **Given** les modifications sont terminees
   - **When** on mesure la couverture de tests
   - **Then** la couverture reste >= 80% sur les fichiers modifies

## Tasks / Subtasks

- [x] **Task 1 : Supprimer `pages/chat.vue`** (AC: 1)
  - [x] 1.1 Supprimer le fichier `frontend/app/pages/chat.vue`
  - [x] 1.2 Verifier que la route `/chat` retourne bien un 404 (Nuxt file-based routing, suppression du fichier = suppression de la route)

- [x] **Task 2 : Supprimer `components/layout/ChatPanel.vue`** (AC: 2)
  - [x] 2.1 Supprimer le fichier `frontend/app/components/layout/ChatPanel.vue`
  - [x] 2.2 Retirer la reference `<ChatPanel />` dans `frontend/app/layouts/default.vue` (ligne 29)
  - [x] 2.3 Verifier que le layout ne contient plus que `FloatingChatButton` et `FloatingChatWidget` comme points d'acces au chat

- [x] **Task 3 : Nettoyer les imports et references orphelines** (AC: 1, 2)
  - [x] 3.1 Recherche globale de `ChatPanel` dans tout le frontend — supprimer toute reference
  - [x] 3.2 Recherche globale de `pages/chat` ou `chat.vue` (en tant que page) — supprimer tout import
  - [x] 3.3 Verifier qu'aucun composant n'importe directement depuis les fichiers supprimes

- [x] **Task 4 : Mettre a jour ou supprimer les tests impactes** (AC: 3, 4)
  - [x] 4.1 Rechercher les tests qui referençaient `ChatPanel` ou `pages/chat.vue` — les supprimer ou adapter
  - [x] 4.2 S'assurer que les 131 tests existants (Epic 1) passent sans regression
  - [x] 4.3 Ajouter un test Vitest verifiant que le layout `default.vue` monte bien `FloatingChatWidget` et `FloatingChatButton` mais pas `ChatPanel`

- [x] **Task 5 : Verification finale** (AC: 1, 2, 3, 4)
  - [x] 5.1 Lancer `npx vitest run` et confirmer zero echec
  - [x] 5.2 Demarrer le serveur dev (`npm run dev`) et verifier visuellement que `/chat` donne bien un 404
  - [x] 5.3 Verifier que le widget flottant fonctionne normalement apres suppression

## Dev Notes

### Fichiers a SUPPRIMER

| Fichier | Raison |
|---------|--------|
| `frontend/app/pages/chat.vue` | Page /chat remplacee par le widget flottant (Epic 1) |
| `frontend/app/components/layout/ChatPanel.vue` | Panneau lateral remplace par FloatingChatWidget |

### Fichiers a MODIFIER

| Fichier | Modification |
|---------|-------------|
| `frontend/app/layouts/default.vue` | Retirer `<ChatPanel />` (ligne 29). Conserver `FloatingChatButton` et `FloatingChatWidget` (lignes 33-36) |

### Etat actuel de `layouts/default.vue` (ligne 28-37)

```vue
    <!-- Panneau chat IA -->
    <ChatPanel />
  </div>

  <!-- Widget flottant copilot (desktop uniquement) -->
  <template v-if="isDesktop">
    <FloatingChatButton />
    <FloatingChatWidget />
  </template>
```

**Apres modification :**

```vue
  </div>

  <!-- Widget flottant copilot (desktop uniquement) -->
  <template v-if="isDesktop">
    <FloatingChatButton />
    <FloatingChatWidget />
  </template>
```

### ATTENTION — NE PAS TOUCHER

Les fichiers suivants ne doivent **PAS** etre modifies dans cette story :

- `frontend/app/components/chat/*.vue` — Les 13 composants chat existants sont reutilises par le widget flottant via composition. Ne pas les supprimer ni les modifier.
- `frontend/app/composables/useChat.ts` — Le composable chat module-level state est utilise par le widget. Ne pas modifier.
- `frontend/app/stores/ui.ts` — Le store UI gere l'etat du widget. Ne pas modifier.
- `frontend/app/components/copilot/*.vue` — Les composants du widget flottant. Ne pas modifier.

### Liens vers /chat a NE PAS traiter ici

Les references a `/chat` dans les composants de navigation et les pages (AppSidebar, pages/financing, pages/carbon, pages/esg) seront traitees dans la **Story 2.2** (mise a jour de la navigation et des liens internes). Cette story se concentre uniquement sur la suppression des fichiers et du layout.

**Fichiers avec liens `/chat` (pour reference, Story 2.2) :**
- `components/layout/AppSidebar.vue` (ligne 15) — `{ label: 'Chat IA', to: '/chat' }`
- `pages/financing/index.vue` (ligne 154) — `to="/chat"`
- `pages/carbon/results.vue` (ligne 185) — `to="/chat"`
- `pages/carbon/index.vue` (lignes 70, 111, 175) — `to="/chat"`
- `pages/esg/index.vue` (lignes 63, 105, 161) — `to="/chat"`
- `pages/esg/results.vue` (ligne 116) — `to="/chat"`

### Composants chat existants (NE PAS SUPPRIMER)

```
frontend/app/components/chat/
├── AnswerElsewhereButton.vue
├── ChatInput.vue
├── ChatMessage.vue
├── ConversationList.vue
├── InteractiveQuestionHost.vue
├── InteractiveQuestionInputBar.vue
├── JustificationField.vue
├── MessageParser.vue
├── MultipleChoiceWidget.vue
├── ProfileNotification.vue
├── SingleChoiceWidget.vue
├── ToolCallIndicator.vue
└── WelcomeMessage.vue
```

### API endpoints `/api/chat/*`

Les endpoints API backend (`/api/chat/conversations`, `/api/chat/messages`, etc.) dans `useChat.ts` sont des appels **API REST**, pas des liens de navigation vers la page `/chat`. Ils ne sont **pas** impactes par cette suppression.

### Tests existants (131 tests, Epic 1)

Il n'existe **aucun** fichier de test specifique pour `ChatPanel.vue` ni pour `pages/chat.vue` dans le repertoire `frontend/tests/`. Les tests existants couvrent uniquement les composants copilot et stores :
- `frontend/tests/components/copilot/FloatingChatWidget.test.ts`
- `frontend/tests/composables/useFocusTrap.test.ts`
- `frontend/tests/stores/ui.test.ts`
- `frontend/tests/composables/useDeviceDetection.test.ts`

### Deferred items herites (contexte)

Les items differes des stories 1.1-1.7 (F8-F11, W1-W6, D1-D4) ne sont **pas** dans le scope de cette story. Ils concernent principalement `useChat.ts` et le widget flottant qui ne sont pas modifies ici.

### Project Structure Notes

- Routing Nuxt file-based : la suppression de `pages/chat.vue` supprime automatiquement la route `/chat`
- Auto-imports Nuxt : la suppression de `ChatPanel.vue` supprime automatiquement le composant des auto-imports (`pathPrefix: false` dans la config)
- Pas besoin de modifier `nuxt.config.ts` ni aucun fichier de configuration

### References

- [Source: _bmad-output/planning-artifacts/epics.md — Epic 2, Story 2.1]
- [Source: _bmad-output/planning-artifacts/architecture.md — Decision 1, Frontiere 1, Arborescence]
- [Source: _bmad-output/implementation-artifacts/1-7-accessibilite-et-navigation-clavier-du-widget.md — Dev Notes, File List]
- [Source: _bmad-output/implementation-artifacts/deferred-work.md — Items D1-D4]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Completion Notes List

- Supprime `pages/chat.vue` (303 lignes) — route `/chat` automatiquement supprimee par le routing file-based Nuxt
- Supprime `components/layout/ChatPanel.vue` (114 lignes) — panneau lateral chat remplace par le widget flottant
- Retire `<ChatPanel />` et son commentaire de `layouts/default.vue` — le layout ne contient plus que `FloatingChatButton` et `FloatingChatWidget`
- Retire le bouton "ouvrir/fermer chat panel" de `AppHeader.vue` (references `toggleChatPanel` et `chatPanelOpen` devenues code mort)
- `stores/ui.ts` conserve `chatPanelOpen` et `toggleChatPanel` (non modifie, conformement aux Dev Notes)
- Commentaires de reference dans `FloatingChatWidget.vue` conserves (fichier copilot/* non modifie)
- Aucun test existant ne referençait ChatPanel ou pages/chat — zero suppression de tests
- 5 nouveaux tests pour `layouts/default.vue` : presence FloatingChatButton/Widget, absence ChatPanel, presence AppSidebar/AppHeader, rendu du slot, masquage widget sur mobile
- 138 tests au total (133 existants + 5 nouveaux), zero regression

### Change Log

- 2026-04-13 : Suppression de la page /chat et de ChatPanel, nettoyage du layout et de AppHeader, ajout de 5 tests layout

### File List

- `frontend/app/pages/chat.vue` — SUPPRIME
- `frontend/app/components/layout/ChatPanel.vue` — SUPPRIME
- `frontend/app/layouts/default.vue` — MODIFIE (retrait de `<ChatPanel />`)
- `frontend/app/components/layout/AppHeader.vue` — MODIFIE (retrait du bouton toggle chat panel)
- `frontend/tests/layouts/default.test.ts` — NOUVEAU (5 tests)

### Review Findings

- [x] [Review][Defer] **Aucun acces chat sur mobile** — deferred. Le widget flottant occupera tout l'ecran sur mobile (epic dedie).
- [x] [Review][Patch] **AC4 couverture verifiee** — `default.vue` 100%, `AppHeader.vue` suppression pure (0 nouveau code), `ui.ts` 74.64% pre-existant (hors scope 2-1). AC4 satisfait.
- [x] [Review][Defer] **Dead code `chatPanelOpen`/`toggleChatPanel` dans `stores/ui.ts`** — deferred, pre-existant. `stores/ui.ts` est hors scope de cette story (DO NOT TOUCH). Nettoyage a planifier dans une story dediee.
