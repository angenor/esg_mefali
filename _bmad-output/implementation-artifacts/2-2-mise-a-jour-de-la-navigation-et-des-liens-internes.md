# Story 2.2 : Mise a jour de la navigation et des liens internes

Status: done

## Story

En tant qu'utilisateur,
je veux que tous les liens et boutons qui menaient a /chat ouvrent desormais le widget flottant,
afin que la navigation reste coherente et intuitive.

## Acceptance Criteria

1. **AC1 — Liens dans les pages modules (ESG, Carbone, Financement)**
   - **Given** un `NuxtLink to="/chat"` existe dans une page module (esg, carbon, financing)
   - **When** un developpeur remplace le `NuxtLink` par un `<button>` qui appelle `uiStore.chatWidgetOpen = true`
   - **Then** le clic ouvre le widget flottant au lieu de naviguer vers /chat
   - **And** le bouton conserve exactement le meme style visuel (classes CSS identiques)
   - **And** le dark mode fonctionne identiquement

2. **AC2 — Lien dans AppSidebar**
   - **Given** `AppSidebar.vue` contient `{ label: 'Chat IA', to: '/chat', icon: 'chat' }` dans `navItems`
   - **When** un developpeur remplace ce lien par un bouton ouvrant le widget flottant
   - **Then** l'item "Chat IA" dans la sidebar ouvre le widget au clic
   - **And** l'item est visuellement coherent avec les autres items de navigation (meme style, icone, dark mode)
   - **Or** l'item est supprime si redondant avec le bouton FAB (FloatingChatButton)

3. **AC3 — Redirection /chat via middleware**
   - **Given** un utilisateur tape `/chat` dans la barre d'adresse
   - **When** la page se charge
   - **Then** il est redirige vers `/` (page d'accueil)
   - **And** le widget flottant s'ouvre automatiquement apres la redirection

4. **AC4 — Zero reference residuelle**
   - **Given** toutes les modifications sont terminees
   - **When** on effectue un grep de `to="/chat"`, `href="/chat"`, `navigateTo.*chat` (hors API `/api/chat/`)
   - **Then** aucune reference de navigation vers la route `/chat` n'est trouvee

5. **AC5 — Dark mode**
   - **Given** le dark mode est actif
   - **When** les elements de navigation mis a jour sont affiches
   - **Then** ils respectent le theme dark existant (variantes `dark:` sur tous les elements visuels)

6. **AC6 — Zero regression tests**
   - **Given** les modifications sont terminees
   - **When** on execute `npx vitest run`
   - **Then** tous les tests existants passent sans regression
   - **And** les nouveaux tests couvrent les fichiers modifies (couverture >= 80%)

## Tasks / Subtasks

- [x] **Task 1 : Remplacer les liens `/chat` dans `pages/esg/index.vue`** (AC: 1, 5)
  - [x] 1.1 Ligne 63 — Header "Nouvelle evaluation" : remplacer `<NuxtLink to="/chat">` par `<button @click="openChatWidget()">` avec les memes classes CSS
  - [x] 1.2 Ligne 105 — Etat vide "Demarrer dans le chat" : remplacer `<NuxtLink to="/chat">` par `<button @click="openChatWidget()">`
  - [x] 1.3 Ligne 161 — Evaluation in_progress "Continuer" : remplacer `<NuxtLink to="/chat">` par `<button @click="openChatWidget()">`
  - [x] 1.4 Ajouter `const uiStore = useUiStore()` et la fonction `openChatWidget` dans le `<script setup>`

- [x] **Task 2 : Remplacer les liens `/chat` dans `pages/esg/results.vue`** (AC: 1, 5)
  - [x] 2.1 Ligne 116 — Etat vide "Demarrer une evaluation" : remplacer `<NuxtLink to="/chat">` par `<button @click="openChatWidget()">`
  - [x] 2.2 Ajouter `const uiStore = useUiStore()` et `openChatWidget` si pas deja present

- [x] **Task 3 : Remplacer les liens `/chat` dans `pages/carbon/index.vue`** (AC: 1, 5)
  - [x] 3.1 Ligne 70 — Header "Nouveau bilan" : remplacer par `<button @click="openChatWidget()">`
  - [x] 3.2 Ligne 111 — Etat vide "Demarrer dans le chat" : remplacer par `<button @click="openChatWidget()">`
  - [x] 3.3 Ligne 175 — Bilan in_progress "Continuer" : remplacer par `<button @click="openChatWidget()">`
  - [x] 3.4 Ajouter `const uiStore = useUiStore()` et `openChatWidget`

- [x] **Task 4 : Remplacer le lien `/chat` dans `pages/carbon/results.vue`** (AC: 1, 5)
  - [x] 4.1 Ligne 185 — Etat vide "Demarrer un bilan" : remplacer par `<button @click="openChatWidget()">`
  - [x] 4.2 Ajouter `const uiStore = useUiStore()` et `openChatWidget`

- [x] **Task 5 : Remplacer le lien `/chat` dans `pages/financing/index.vue`** (AC: 1, 5)
  - [x] 5.1 Ligne 154 — Header "Conseils IA" : remplacer par `<button @click="openChatWidget()">`
  - [x] 5.2 Ajouter `const uiStore = useUiStore()` et `openChatWidget`

- [x] **Task 6 : Mettre a jour `AppSidebar.vue`** (AC: 2, 5)
  - [x] 6.1 Retirer l'entree `{ label: 'Chat IA', to: '/chat', icon: 'chat' }` de `navItems` (ligne 15)
  - [x] 6.2 **Option recommandee** : supprimer completement l'item "Chat IA" de la sidebar — le bouton FAB (FloatingChatButton) remplit deja ce role. L'ajout d'un bouton custom dans la sidebar creerait une duplication de point d'acces.
  - [x] 6.3 **Option alternative** (si l'utilisateur souhaite conserver l'item) : transformer l'item en `<button>` special avec `@click="uiStore.chatWidgetOpen = true"` au lieu d'un `NuxtLink`

- [x] **Task 7 : Creer le middleware de redirection `/chat`** (AC: 3)
  - [x] 7.1 Creer `frontend/app/middleware/chat-redirect.global.ts`
  - [x] 7.2 Implementer la logique : si `to.path === '/chat'`, rediriger vers `/` et marquer un flag pour ouvrir le widget
  - [x] 7.3 Le flag peut utiliser un query param transitoire (`?openChat=true`) ou un state dans le store UI
  - [x] 7.4 Dans `layouts/default.vue`, watcher le query param ou le flag pour ouvrir le widget a l'arrivee

- [x] **Task 8 : Nettoyage dead code dans `stores/ui.ts`** (AC: 4)
  - [x] 8.1 Supprimer `chatPanelOpen` ref (ligne 15) — plus aucun consommateur depuis story 2-1
  - [x] 8.2 Supprimer `toggleChatPanel()` fonction (lignes 55-57)
  - [x] 8.3 Retirer `chatPanelOpen` et `toggleChatPanel` du `return` (lignes 145, 159)
  - [x] 8.4 Mettre a jour les tests de `ui.ts` si existants

- [x] **Task 9 : Verification exhaustive des references** (AC: 4)
  - [x] 9.1 Grep global : `to="/chat"`, `href="/chat"`, `navigateTo.*chat` (hors `/api/chat/`)
  - [x] 9.2 Grep : `chatPanelOpen`, `toggleChatPanel` — confirmer zero reference residuelle
  - [x] 9.3 Verifier que les commentaires referençant `/chat` dans `FloatingChatWidget.vue` (lignes 355, 395) sont coherents (ce sont des commentaires de reference, pas des liens — les conserver est OK)

- [x] **Task 10 : Tests unitaires** (AC: 6)
  - [x] 10.1 Test : `pages/esg/index.vue` — les boutons appellent `openChatWidget` au clic
  - [x] 10.2 Test : `pages/carbon/index.vue` — les boutons appellent `openChatWidget` au clic
  - [x] 10.3 Test : middleware `chat-redirect.global.ts` — `/chat` redirige vers `/`
  - [x] 10.4 Test : `AppSidebar.vue` — l'item "Chat IA" n'apparait plus (ou ouvre le widget)
  - [x] 10.5 Test : `stores/ui.ts` — `chatPanelOpen` et `toggleChatPanel` n'existent plus dans l'interface

- [x] **Task 11 : Verification finale** (AC: 1, 2, 3, 4, 5, 6)
  - [x] 11.1 Lancer `npx vitest run` et confirmer zero echec — 155 tests passes, 15 fichiers, zero echec
  - [ ] 11.2 Demarrer le serveur dev (`npm run dev`) et verifier :
    - Cliquer sur "Nouvelle evaluation" dans /esg → le widget s'ouvre
    - Cliquer sur "Nouveau bilan" dans /carbon → le widget s'ouvre
    - Cliquer sur "Conseils IA" dans /financing → le widget s'ouvre
    - Taper /chat dans la barre d'adresse → redirection + widget ouvert
    - Sidebar : "Chat IA" absent (ou fonctionne via widget)
    - Tout fonctionne en dark mode

## Dev Notes

### Pattern de remplacement NuxtLink → button

Chaque `<NuxtLink to="/chat">` doit devenir un `<button>` (pas un `<a>`) pour la semantique (action, pas navigation) :

```vue
<!-- AVANT -->
<NuxtLink to="/chat" class="inline-flex items-center gap-2 ...">
  Nouvelle evaluation
</NuxtLink>

<!-- APRES -->
<button @click="openChatWidget()" class="inline-flex items-center gap-2 ...">
  Nouvelle evaluation
</button>
```

La fonction helper dans chaque page :
```vue
<script setup lang="ts">
import { useUiStore } from '~/stores/ui'
const uiStore = useUiStore()

function openChatWidget() {
  uiStore.chatWidgetOpen = true
}
</script>
```

**IMPORTANT** : Nuxt auto-importe `useUiStore` si le store est dans `stores/`. Verifier si l'import explicite est deja present dans chaque fichier avant d'en ajouter un.

### Inventaire complet des references `/chat` (navigation uniquement)

| Fichier | Ligne(s) | Contexte | Action |
|---------|----------|----------|--------|
| `components/layout/AppSidebar.vue` | 15 | `{ label: 'Chat IA', to: '/chat' }` dans navItems | Supprimer l'item ou transformer en bouton |
| `pages/esg/index.vue` | 63, 105, 161 | Header CTA, etat vide, evaluation in_progress | Remplacer par `<button @click="openChatWidget()">` |
| `pages/esg/results.vue` | 116 | Etat vide, pas d'evaluation | Remplacer par `<button @click="openChatWidget()">` |
| `pages/carbon/index.vue` | 70, 111, 175 | Header CTA, etat vide, bilan in_progress | Remplacer par `<button @click="openChatWidget()">` |
| `pages/carbon/results.vue` | 185 | Etat vide, pas de bilan | Remplacer par `<button @click="openChatWidget()">` |
| `pages/financing/index.vue` | 154 | Header CTA "Conseils IA" | Remplacer par `<button @click="openChatWidget()">` |

### References `/chat` a NE PAS modifier (appels API REST)

Ces references pointent vers l'API backend (`/api/chat/`), pas vers la route de navigation :
- `composables/useChat.ts` — 8 occurrences (`${apiBase}/chat/conversations`, etc.)
- `components/copilot/FloatingChatWidget.vue` — 1 occurrence (`/chat/interactive-questions/`)
- `components/chat/AnswerElsewhereButton.vue` — 1 occurrence (`/chat/interactive-questions/`)

Les commentaires de reference dans `FloatingChatWidget.vue` (lignes 355, 395) mentionnant `pages/chat.vue` sont des annotations historiques — les conserver ou mettre a jour le commentaire pour refleter la suppression.

### Middleware de redirection Nuxt

Creer `frontend/app/middleware/chat-redirect.global.ts` :

```typescript
// Redirige /chat vers / et ouvre le widget flottant
export default defineNuxtRouteMiddleware((to) => {
  if (to.path === '/chat') {
    return navigateTo({ path: '/', query: { openChat: '1' } })
  }
})
```

Dans `layouts/default.vue`, ajouter un watcher pour le query param :

```typescript
const route = useRoute()
const router = useRouter()

watch(() => route.query.openChat, (val) => {
  if (val === '1') {
    uiStore.chatWidgetOpen = true
    // Nettoyer le query param
    router.replace({ query: { ...route.query, openChat: undefined } })
  }
}, { immediate: true })
```

**Alternative plus simple** : utiliser un flag transitoire dans le store UI (`pendingChatOpen: boolean`). Le middleware set le flag, le layout le consomme et le reset. Evite de polluer l'URL.

### Nettoyage dead code `stores/ui.ts` (item differe D1 de story 2-1)

La story 2-1 a identifie `chatPanelOpen` et `toggleChatPanel` comme dead code (deferred item D1). C'est le moment de les nettoyer :
- `chatPanelOpen` ref (ligne 15) — aucun consommateur
- `toggleChatPanel()` (lignes 55-57) — aucun consommateur
- Exports dans le `return` (lignes 145, 159) — a retirer

Verifier avec grep que `chatPanelOpen` et `toggleChatPanel` ne sont references nulle part avant suppression.

### Fichiers existants avec middleware

Un seul middleware global existe : `frontend/app/middleware/auth.global.ts`. Le nouveau middleware `chat-redirect.global.ts` coexistera sans conflit (Nuxt execute tous les middlewares globaux en sequence).

### Composants du widget (NE PAS TOUCHER)

Les fichiers suivants ne doivent **PAS** etre modifies :
- `frontend/app/components/copilot/*.vue` — Le widget flottant fonctionne deja
- `frontend/app/composables/useChat.ts` — Module-level state inchange
- `frontend/app/components/chat/*.vue` — 13 composants chat inchanges

### Dark mode

Tous les boutons remplaces doivent conserver les variantes `dark:` des `NuxtLink` originaux. Les classes CSS existantes incluent deja les variantes dark — il suffit de les copier integralement sur les `<button>`.

### Tests existants

- `frontend/tests/stores/ui.test.ts` — Contient des tests pour `chatPanelOpen` et `toggleChatPanel` qui devront etre supprimes/adaptes apres le nettoyage dead code
- `frontend/tests/components/copilot/FloatingChatWidget.test.ts` — Ne teste pas les liens `/chat`, pas d'impact
- `frontend/tests/layouts/default.test.ts` — 5 tests (story 2-1), pas d'impact direct sauf si watcher ajout

### Intelligence de la story precedente (2-1)

**Learnings cles :**
- Les auto-imports Nuxt fonctionnent pour les composants (`pathPrefix: false`) — pas besoin d'imports explicites dans le layout
- Le retrait du bouton toggle chat panel dans `AppHeader.vue` a ete fait en 2-1 — ne pas re-toucher `AppHeader.vue`
- Les tests existants ne couvraient pas `ChatPanel` ni `pages/chat.vue` — prudent de verifier la couverture des fichiers modifies
- 138 tests au total apres story 2-1 (133 + 5 nouveaux)

### Commits recents (contexte)

```
b7314e2 2-1-suppression-de-la-page-chat-et-de-chatpanel: done
39bbb14 1-6-redimensionnement-du-widget: done + 1-7-accessibilite: done
e27120c 1-3 + 1-4 + 1-5: done
2785a59 1-1 + 1-2: done
```

### Project Structure Notes

- Nuxt 4 : fichiers source dans `frontend/app/` (pages, components, composables, layouts, stores)
- Routing file-based : `pages/chat.vue` est deja supprime (story 2-1), donc `/chat` donne deja un 404
- Middleware global : tous les fichiers `*.global.ts` dans `middleware/` sont executes automatiquement
- Le store `ui.ts` est accessible via auto-import Pinia (`useUiStore()`)

### References

- [Source: _bmad-output/planning-artifacts/epics.md — Epic 2, Story 2.2]
- [Source: _bmad-output/planning-artifacts/architecture.md — ADR1 (module-level state), Arborescence (ChatPanel SUPPRIME)]
- [Source: _bmad-output/implementation-artifacts/2-1-suppression-de-la-page-chat-et-de-chatpanel.md — Dev Notes, File List, Review Findings]
- [Source: _bmad-output/implementation-artifacts/deferred-work.md — D1 dead code chatPanelOpen/toggleChatPanel]

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6 (1M context)

### Debug Log References
- Tests initiaux echoues a cause des auto-imports Nuxt (onMounted, computed, useRoute, useRouter) non disponibles en environnement vitest. Resolution : stub global de chaque auto-import Vue/Nuxt dans les fichiers de test concernes.
- Test middleware echoue a cause du hoisting des imports ES. Resolution : utilisation de `globalThis` pour definir les stubs avant l'import dynamique du module.

### Completion Notes List
- **Tasks 1-5** : Remplacement de 9 `<NuxtLink to="/chat">` par des `<button @click="openChatWidget()">` dans 5 fichiers (esg/index, esg/results, carbon/index, carbon/results, financing/index). Classes CSS conservees identiques. Import `useUiStore` + fonction `openChatWidget()` ajoutes dans chaque fichier.
- **Task 6** : Suppression complete de l'item "Chat IA" de `navItems` dans AppSidebar.vue (option recommandee — le FAB FloatingChatButton remplit deja ce role). Le bloc SVG de l'icone chat a egalement ete retire du template.
- **Task 7** : Creation du middleware `chat-redirect.global.ts` qui redirige `/chat` vers `/` avec query param `?openChat=1`. Watcher ajoute dans `layouts/default.vue` pour ouvrir le widget et nettoyer le query param a l'arrivee.
- **Task 8** : Suppression de `chatPanelOpen` (ref) et `toggleChatPanel()` (fonction) du store `ui.ts`, incluant leurs exports dans le return. Dead code identifie dans story 2-1 (deferred item D1). Aucune reference residuelle (grep confirme).
- **Task 9** : Verification grep exhaustive — zero `to="/chat"`, zero `href="/chat"`, zero `chatPanelOpen`, zero `toggleChatPanel` dans tout le frontend.
- **Task 10** : 17 nouveaux tests dans 5 fichiers : middleware (4 tests), AppSidebar (3 tests), ui dead code (4 tests), esg-index (3 tests), carbon-index (3 tests). Test existant `default.test.ts` adapte pour les mocks useRoute/useRouter.
- **Task 11** : 155 tests passes (15 fichiers), zero regression. Verification manuelle (11.2) a effectuer par l'utilisateur.

### Review Findings

- [x] [Review][Decision] DRY : `openChatWidget()` duplique dans 5 fichiers — **Resolution : action ajoutee au store `ui.ts`, fonctions locales supprimees des 5 pages**
- [x] [Review][Decision] Mobile : `openChatWidget()` set `chatWidgetOpen = true` mais le widget n'est pas rendu sur mobile — **Resolution : no-op accepte, deja traque dans D2 story 2-1**
- [x] [Review][Decision] Tests manquants pour `esg/results.vue`, `carbon/results.vue`, `financing/index.vue` — **Resolution : 3 fichiers de test crees (9 tests)**
- [x] [Review][Patch] Indentation cassee sur la ligne ESG dans navItems [AppSidebar.vue:15]
- [x] [Review][Patch] `type="button"` manquant sur les 9 boutons remplaces [5 fichiers pages]
- [x] [Review][Patch] `router.replace` avec `undefined` ne supprime pas fiablement le query param [default.vue:19]
- [x] [Review][Patch] Watcher `immediate: true` s'execute cote SSR — garde `import.meta.client` ajoutee [default.vue:17-23]
- [x] [Review][Patch] Boucle infinie Back button — `replace: true` ajoute au middleware [chat-redirect.global.ts]
- [x] [Review][Patch] Trailing slash `/chat/` non redirige — condition elargie [chat-redirect.global.ts]
- [x] [Review][Patch] Aucun test pour le watcher `openChat` dans default.vue — 2 tests ajoutes [default.test.ts]
- [x] [Review][Defer] Icone 'applications' manquante dans la chaine `v-else-if` de AppSidebar — deferred, pre-existant

### Change Log
- 2026-04-13 : Implementation complete story 2-2. 9 NuxtLink remplaces, sidebar mise a jour, middleware de redirection cree, dead code nettoye, 17 nouveaux tests.

### File List
- frontend/app/pages/esg/index.vue (modifie)
- frontend/app/pages/esg/results.vue (modifie)
- frontend/app/pages/carbon/index.vue (modifie)
- frontend/app/pages/carbon/results.vue (modifie)
- frontend/app/pages/financing/index.vue (modifie)
- frontend/app/components/layout/AppSidebar.vue (modifie)
- frontend/app/middleware/chat-redirect.global.ts (nouveau)
- frontend/app/layouts/default.vue (modifie)
- frontend/app/stores/ui.ts (modifie)
- frontend/tests/middleware/chat-redirect.test.ts (nouveau)
- frontend/tests/components/layout/AppSidebar.test.ts (nouveau)
- frontend/tests/stores/ui-dead-code.test.ts (nouveau)
- frontend/tests/pages/esg-index.test.ts (nouveau)
- frontend/tests/pages/carbon-index.test.ts (nouveau)
- frontend/tests/layouts/default.test.ts (modifie)
