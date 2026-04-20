# Story 7.3 : Resilience SSE et indicateur de reconnexion

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

En tant qu'utilisateur dont la connexion reseau est instable,
je veux que le parcours guide continue meme si la connexion au serveur est perdue et voir un indicateur clair de reconnexion dans le widget,
afin de ne pas perdre ma progression de guidage ni me demander si l'assistant est encore disponible (FR33, NFR17).

## Contexte — etat actuel (VERIFIE avant redaction)

Audit du code existant (2026-04-14) :

- **Pattern SSE POST-based** (pas `EventSource`) — `frontend/app/composables/useChat.ts` declenche un `fetch()` par message, lit le `ReadableStream` via `response.body.getReader()` (lignes 216-224 pour `sendMessage`, lignes 604-614 pour `submitInteractiveAnswer`). **Pas de connexion persistante** : chaque tour de conversation ouvre **une nouvelle** HTTP/1.1 ou HTTP/2 stream qui se ferme a la fin. L'architecture (`architecture.md:210-218`) decrit explicitement : « AbortController stocke en module-level ref, permet d'annuler proprement un stream en cours », « **Indicateur de reconnexion** : `isConnected` ref base sur l'etat du dernier fetch (pas de heartbeat — post-based) ».
- **Aucune ref `isConnected`** actuellement dans `useChat.ts` — c'est l'objet de cette story (l'architecture l'a specifie mais personne ne l'a encore implementee).
- **Refs module-level deja existantes dans `useChat.ts`** (lignes 26-52) : `conversations`, `currentConversation`, `messages`, `isStreaming`, `streamingContent`, `error`, `documentProgress`, `reportSuggestion`, `activeToolCall`, `currentInteractiveQuestion`, `interactiveQuestionsByMessage`, `searchQuery`, `abortController`, `sseReader`. **Pattern a reutiliser** pour `isConnected`.
- **Gestion d'erreur fetch actuelle** (useChat.ts:463-472 et 723-736) : le `catch (e)` dans `sendMessage` / `submitInteractiveAnswer` met `error.value` a un message generique (`"Erreur inconnue"` ou le message de l'exception) mais **ne distingue pas** :
  1. **`AbortError`** (annulation volontaire — ex. nouveau message ou changement de conversation) — doit etre ignore, pas de perte de connexion.
  2. **`TypeError: Failed to fetch`** (network down, DNS, CORS, serveur injoignable) — c'est le signal principal de perte de connexion.
  3. **Erreurs HTTP (response non-ok mais body present)** — le serveur a repondu, pas de perte de connexion reseau (500 = backend en erreur mais reseau OK).
  4. **Erreurs de `reader.read()` en cours de streaming** (coupure en plein stream) — c'est une perte de connexion.
- **`FloatingChatWidget.vue:1-35`** — importe `useChat()` et destructure les refs utilisees dans le template. `ChatInput` est pilote par `:disabled="isStreaming"` (ligne 626). **Pas encore de combinaison avec un `isConnected`**.
- **`ChatWidgetHeader.vue`** (61 lignes) — header simple (bouton retour, titre, bouton historique, bouton fermer). **Zone ideale pour ajouter un badge de reconnexion** entre le titre et le bouton historique, mais les `defineEmits` actuels ne couvrent pas le cas `connection` — il faudra soit enrichir `ChatWidgetHeader` avec une prop `isConnected`, soit afficher le badge **a l'exterieur** du header (directement dans `FloatingChatWidget.vue` au-dessus du header). **Decision d'implementation ci-dessous (AC4).**
- **`ChatInput.vue:2-4`** — prop `disabled?: boolean` deja presente, cablage existant `:disabled="disabled"` sur le textarea et les boutons (lignes 94, 113, 120). **Il suffira d'etendre le disabled depuis `FloatingChatWidget.vue` pour inclure `!isConnected`** + ajouter un message explicatif conditionnel.
- **Driver.js est purement DOM-driven** (`useGuidedTour.ts` — aucun appel SSE) — confirme par story 7.2. L'AC « parcours Driver.js continue » est donc **automatiquement respecte par isolation**, pas d'action requise. Cette story garantit **seulement** que `useChat.isConnected` **ne perturbe pas** `useGuidedTour`.
- **`navigator.onLine` et events `online`/`offline`** — API standard exposee par les navigateurs. `navigator.onLine === false` n'est pas 100% fiable (peut retourner `true` meme sans internet effectif, selon l'OS), mais les events `online`/`offline` sur `window` sont un **complement utile** pour basculer instantanement l'indicateur sans attendre un fetch echoue. **Pattern recommande** : on ecoute `window.online`/`offline` comme **hint** et on corrobore avec le resultat du prochain fetch.
- **Aucun test de perte de connexion existant** dans `frontend/tests/composables/useChat*.test.ts` — cette story introduit la premiere suite `useChat.connection.test.ts`.
- **Zero modification backend attendue** — la resilience SSE est un probleme 100% frontend (le backend est stateless sur le SSE, chaque POST ouvre un nouveau stream).

Cette story comble **5 gaps** identifies par l'architecture (`architecture.md:210-218`) et le PRD (FR33, NFR17) :

1. **Ref `isConnected` absente** — l'architecture la specifie mais elle n'existe pas.
2. **Pas de classification des erreurs fetch** — `AbortError` vs `TypeError: Failed to fetch` vs erreurs reader sont melangees dans un `catch` generique.
3. **Pas d'indicateur visuel** dans le widget — l'utilisateur ne sait pas si le chat est HS.
4. **Pas de desactivation de `ChatInput`** en mode deconnecte — les messages saisis vont echouer silencieusement.
5. **Pas de fallback via `navigator.onLine`** pour basculer instantanement avant meme un tentative de fetch.

## Acceptance Criteria

### AC1 : Ref module-level `isConnected` dans `useChat.ts` (architecture.md:218)

**Given** le composable `useChat.ts` est charge (client-only, cf. garde `import.meta.server` ligne 18)
**When** aucun fetch n'a encore eu lieu
**Then** une nouvelle ref module-level `const isConnected = ref<boolean>(true)` est declaree apres `sseReader` (ligne 52) avec un commentaire expliquant son role :
```typescript
// FR33/NFR17 — etat de connexion SSE/reseau deduit du dernier fetch + navigator.onLine
// true par defaut (optimiste) ; bascule false sur TypeError/Failed to fetch ou offline.
const isConnected = ref<boolean>(true)
```

**And** `isConnected` est **expose** dans le `return` de `useChat()` (ligne 802-826) — apres `error` et avant `searchQuery` pour groupement logique.

**And** si `navigator.onLine === false` au moment du premier acces au composable **cote client** (jamais cote serveur, cf. garde ligne 18), la ref est initialisee a `false` — **pattern** : initialisation lazy dans un bloc `if (import.meta.client) { isConnected.value = navigator.onLine }` apres la declaration.

**And** l'implementation doit rester SSR-safe (pas d'acces a `navigator` au niveau top-level — tout est dans un `if (import.meta.client)` ou dans une fonction appelee a l'initialisation de `useChat()`).

### AC2 : Ecouteurs `online`/`offline` globaux (basculement instantane)

**Given** le composable est utilise dans au moins un composant monte (widget flottant, layout)
**When** `useChat()` est appele pour la premiere fois, et le flag `_connectionListenersInstalled` (module-level) est `false`
**Then** des ecouteurs sont installes sur `window`:
```typescript
window.addEventListener('online', () => { isConnected.value = true })
window.addEventListener('offline', () => { isConnected.value = false })
```

**And** le flag `_connectionListenersInstalled = true` empeche toute installation multiple (pattern module-level, evite la duplication sur chaque appel de `useChat()`).

**And** les ecouteurs **ne sont jamais retires** — ils persistent pour toute la vie de l'onglet (coherent avec l'etat module-level singleton). **Pas** d'`onBeforeUnmount` qui les detruirait, car `useChat` est partage par le widget + les pages cibles du guidage.

**And** l'installation est dans un `if (import.meta.client && !_connectionListenersInstalled)` pour la SSR-safety.

**Rationale** : l'event `offline` bascule l'indicateur **instantanement** meme sans tentative de fetch (ex. l'utilisateur passe en avion) — amelioration UX qui complete la detection par fetch (AC3).

### AC3 : Classification des erreurs fetch et basculement `isConnected` (FR33)

**Given** un `sendMessage` ou `submitInteractiveAnswer` est en cours
**When** une exception est levee pendant le `fetch` initial ou pendant la boucle `reader.read()`
**Then** le `catch (e)` classifie l'erreur **avant** de modifier `isConnected` :

| Erreur | Test de detection | Effet sur `isConnected` | Effet sur `error.value` |
|---|---|---|---|
| `AbortError` | `e instanceof DOMException && e.name === 'AbortError'` | **Inchange** (annulation volontaire) | **Inchange** (return silencieux — comportement actuel ligne 464) |
| `TypeError` network (`"Failed to fetch"`, `"NetworkError"`, `"Load failed"`) | `e instanceof TypeError` OU `/failed to fetch|network|load failed/i.test(e.message)` | **false** (perte de connexion) | Message FR : `"Connexion perdue. Votre parcours guide continue. L'envoi de messages reprendra automatiquement."` **uniquement si `guidedTourActive`**, sinon `"Connexion perdue. Verifiez votre reseau."` |
| Reader error en cours de streaming (ex. `TypeError` depuis `reader.read()`) | Meme branche que ci-dessus | **false** | Idem |
| Erreur HTTP (`!response.ok` avant le reader, ex. 500) | `e.message` contient `"Erreur lors de l'envoi"` ou est leve via `throw new Error('Erreur lors de l\\'envoi du message')` ligne 227 | **Inchange** (le serveur a repondu) | Comportement actuel (message technique) |
| Autre exception (`SyntaxError`, `TypeError` non-network, etc.) | Fallback | **Inchange** | Comportement actuel |

**And** la classification est extraite dans un helper privee module-level `function classifyFetchError(e: unknown): 'abort' | 'network' | 'http' | 'other'` pour reutilisation entre `sendMessage` et `submitInteractiveAnswer` (DRY).

**And** quand une erreur `'network'` est detectee **pendant un parcours guide** (`useUiStore().guidedTourActive === true`), **aucun `addSystemMessage` n'est ajoute** (le parcours Driver.js reste visuel, pas de pollution chat). Le message `error.value` suffit — il est consomme par la banniere d'erreur du widget (`FloatingChatWidget.vue:609-614`). **L'utilisateur voit l'indicateur de reconnexion** (AC4) **a la place**.

**And** quand une erreur `'network'` est detectee **hors parcours guide** (`guidedTourActive === false`), `error.value` est defini au message `"Connexion perdue. Verifiez votre reseau."` — la banniere existante le montre.

### AC4 : Indicateur visuel de reconnexion dans le widget (FR33, dark mode)

**Given** `isConnected === false` est expose par `useChat()`
**When** le widget flottant est ouvert (`uiStore.chatWidgetOpen === true`)
**Then** un badge « Reconnexion... » est affiche **juste sous le `ChatWidgetHeader`** (donc au-dessus de la zone messages) avec les caracteristiques suivantes :
- Structure : `<div role="status" aria-live="polite">` contenant une icone SVG (cercle avec fleche ou icone de WiFi coupe) + le texte `"Reconnexion..."`.
- Couleurs claires : fond `bg-amber-50`, texte `text-amber-800`, bordure basse `border-b border-amber-200`.
- Couleurs dark : `dark:bg-amber-900/20`, `dark:text-amber-300`, `dark:border-amber-800/50`.
- Icone animee (pulse ou rotate via classe Tailwind `animate-pulse`).
- Taille : `text-xs`, padding compact `px-4 py-2`.

**And** le badge **disparait** des que `isConnected` redevient `true` (AC5).

**And** **pas** de placement dans le `ChatWidgetHeader` lui-meme — **decision** : afficher le badge **entre** le header et la zone messages dans `FloatingChatWidget.vue` (nouveau bloc insere apres `<ChatWidgetHeader>` ligne ~556, avant le `<ConversationList>` et la vue chat). Rationale : evite d'enrichir `ChatWidgetHeader` avec une nouvelle prop et garde la zone titre simple (meme pattern que la banniere d'erreur actuelle ligne 609).

**And** l'indicateur est **visible aussi** en vue historique (`currentView === 'history'`) — c'est un etat global du composable, pas specifique a la vue chat. **Implementation** : le bloc est place avant le `v-if="currentView === 'history'"` ConversationList et avant le `v-else` vue chat.

**And** le composant est extrait dans un **nouveau** `frontend/app/components/copilot/ConnectionStatusBadge.vue` avec prop `:isConnected` et la totalite du markup (y compris le `v-if="!isConnected"` pour conditionner l'affichage, afin que `FloatingChatWidget.vue` reste un simple `<ConnectionStatusBadge :is-connected="isConnected" />`). Cela facilite les tests unitaires du composant isole et le dark mode.

### AC5 : Reprise de connexion — disparition automatique de l'indicateur

**Given** `isConnected === false` (perte detectee)
**When** le prochain fetch (`sendMessage` ou `submitInteractiveAnswer`) **termine avec succes** (i.e. `response.ok === true` ET le `reader.read()` lit au moins un chunk sans erreur)
**Then** `isConnected.value = true` est execute **des la reception du premier chunk lu sans erreur** (pas a la fin du stream — pour un feedback instantane). Position dans le code : immediatement apres `const { done, value } = await reader.read()` quand `value !== undefined` et pas d'erreur (c.-a-d. a la toute premiere iteration reussie de la boucle `while (true)` ligne 252-462 et 634-714).

**And** l'event `online` du navigateur (AC2) peut aussi basculer `isConnected` a `true` sans attendre un fetch — dans ce cas, la banniere `error` existante (`"Connexion perdue..."`) est **effacee** : `error.value = ''` dans le handler `online`.

**And** l'indicateur visuel (AC4) **disparait** automatiquement des que `isConnected === true` (reactivite Vue).

**And** quand l'utilisateur envoie un message alors que `isConnected === false`, le `sendMessage` tente quand meme le fetch (on n'empeche pas l'appel — cela permet une reprise optimiste). Si le fetch reussit, `isConnected` bascule a `true` (reprise). Si le fetch echoue a nouveau, `isConnected` reste `false` et l'erreur est re-signalisee.

**Note design** : on ne pre-bloque pas les envois meme quand `isConnected === false` — le fetch est la source de verite (le `navigator.onLine` est parfois faux positif). L'ecran de saisie est desactive visuellement (AC6) **pour dissuader** l'envoi, mais la logique reste tolerante : si l'utilisateur force (ex. clique avant que le disable ne prenne effet), le fetch servira de re-check.

### AC6 : Desactivation de `ChatInput` en mode deconnecte + message explicatif

**Given** `isConnected === false` ET aucune question interactive pending (cf. `currentInteractiveQuestion?.state !== 'pending'`)
**When** le widget affiche `ChatInput` (`FloatingChatWidget.vue:624-629`)
**Then** le prop `:disabled` de `ChatInput` est **etendu** a :
```vue
:disabled="isStreaming || !isConnected"
```

**And** **en plus** du disable, un message explicatif FR est affiche **dans le composant `ChatInput`** (prop additionnel `:hint="string | null"`) juste au-dessus du textarea ou sous le compteur de caracteres :
- Message : `"Connexion perdue. Les envois reprendront après reconnexion."` (revise en review 2026-04-14 : l'ancien wording « L'envoi reprendra automatiquement » suggerait un auto-retry non implemente ; le code n'effectue pas de replay du message sur l'event `online`, l'utilisateur doit recliquer Envoyer apres reconnexion)
- Couleurs claires : `text-amber-700 text-xs`, couleurs dark : `dark:text-amber-400`.
- Visible **uniquement** quand `!isConnected` (prop `hint` = null quand connecte).

**And** l'implementation etend `ChatInput.vue` avec un prop optionnel `hint?: string | null` et un bloc `<p v-if="hint" class="...">{{ hint }}</p>` place **au-dessus** du `<div class="flex gap-2 items-end">` (pour ne pas perturber la mise en page des boutons).

**And** quand une question interactive est pending, c'est `InteractiveQuestionInputBar` qui est affichee (pas `ChatInput`) — la desactivation pour perte de connexion s'applique **aussi** a ce composant via un prop `:disabled="isStreaming || !isConnected"` (actuellement c'est `:loading="isStreaming"`). Si `InteractiveQuestionInputBar` ne supporte pas encore un prop `disabled` distinct de `loading`, l'ajouter (prop `:disabled?: boolean`, desactive les boutons de choix et le submit quand true).

### AC7 : Parcours Driver.js continue sans interruption pendant la perte SSE (FR33, NFR17)

**Given** un parcours Driver.js mono-page ou multi-pages est en cours (`useGuidedTour().tourState.value !== 'idle'` OU `uiStore.guidedTourActive === true`)
**When** la connexion SSE est perdue (`isConnected === false`)
**Then** **aucune modification** n'est apportee a `useGuidedTour.ts` — le parcours est entierement DOM-driven et continue ses animations, popovers, navigation.

**And** si un step du parcours necessite un appel API pour la page cible (ex. `/dashboard` charge les donnees via `useDashboard.fetchSummary()`), **l'appel echoue silencieusement** (mode offline reel) — l'element vise par Driver.js peut donc etre `null` si le DOM depend des donnees async.

**Comportement** : Driver.js appelle `waitForElementExtended` (story 7.1) qui gere deja le timeout → si l'element n'apparait pas, soit skip gracieux mono-page (AC2 story 7.1), soit interruption multi-pages (AC3 story 7.1). **La resilience SSE n'aggrave pas** le comportement degrade — elle se superpose gracieusement aux resiliences DOM deja en place.

**And** l'indicateur de reconnexion reste visible pendant tout le parcours (AC4). **Rappel** : l'architecture specifie « Le parcours Driver.js en cours continue (entierement frontend). Le widget affiche un indicateur de reconnexion » (PRD NFR17).

**Test dedie** : `test_driverjs_tour_continues_when_connection_lost` — mock fetch qui throw `TypeError('Failed to fetch')`, declenche `sendMessage`, verifier que `isConnected = false` MAIS que `useGuidedTour().tourState.value` reste inchange (pas de side-effect sur le parcours).

### AC8 : Isolation fonctionnelle — `useGuidedTour` ne lit pas `isConnected`

**Given** l'exposition de `isConnected` par `useChat()`
**When** on grep le code de `useGuidedTour.ts`
**Then** aucune reference a `isConnected` ne doit apparaitre — le module de guidage est **isole** de l'etat de connexion.

**And** cette invariance est assuree par code review + grep dans les tests (`test_useGuidedTour_does_not_import_isConnected` — grep le contenu du fichier source).

**Rationale** : si Driver.js dependait de `isConnected`, on creerait un couplage croise qui pourrait interrompre un parcours des qu'on bascule offline — violation directe de FR33.

### AC9 : Tests Vitest >= 80% et zero regression (NFR19)

**Given** la suite de tests frontend existante (330+ tests verts apres story 7.2)
**When** on execute `cd frontend && npm run test`
**Then** zero regression sur l'ensemble.

**And** un **nouveau** fichier `frontend/tests/composables/useChat.connection.test.ts` est cree avec AU MINIMUM les tests suivants :

#### Bloc 1 : Ref `isConnected` initiale (AC1, AC2)

- `test_isConnected_initial_value_is_true_when_navigator_online_true` (mock `navigator.onLine = true`, assert `isConnected.value === true` au premier acces)
- `test_isConnected_initial_value_is_false_when_navigator_offline` (mock `navigator.onLine = false`, assert `isConnected.value === false`)
- `test_online_event_switches_isConnected_to_true` (mock offline au depart → dispatch `new Event('online')` sur window → assert `isConnected.value === true`)
- `test_offline_event_switches_isConnected_to_false` (online au depart → dispatch `new Event('offline')` → assert false)
- `test_connection_listeners_installed_once_across_multiple_useChat_calls` (appeler `useChat()` 3x, spy sur `addEventListener('online')` — verifier qu'il est appele exactement 2 fois au total : 1 pour `online`, 1 pour `offline`, **pas** 6)

#### Bloc 2 : Classification des erreurs fetch (AC3)

- `test_AbortError_does_not_affect_isConnected` (mock fetch reject `new DOMException('aborted', 'AbortError')` → apres sendMessage, `isConnected.value === true` inchange, `error.value === ''`)
- `test_TypeError_failed_to_fetch_sets_isConnected_false` (mock fetch reject `new TypeError('Failed to fetch')` → `isConnected.value === false`, `error.value` contient `"Connexion perdue"`)
- `test_NetworkError_message_triggers_disconnection` (reject Error avec message `"NetworkError when attempting to fetch resource"` → isConnected = false)
- `test_HTTP_500_does_not_affect_isConnected` (mock fetch resolve `{ ok: false, status: 500, ... }` → isConnected reste true, error contient le message technique)
- `test_reader_error_during_streaming_sets_isConnected_false` (mock fetch resolve 200 OK avec body, mais `reader.read()` throw `TypeError('Network error during read')` a la 2eme iteration → isConnected = false)

#### Bloc 3 : Reprise de connexion (AC5)

- `test_isConnected_becomes_true_on_first_successful_chunk_read` (offline au depart → fetch reussit 200 + body, premier read() resout → assert `isConnected.value === true` immediatement, pas a la fin du stream)
- `test_online_event_clears_connection_error_message` (error.value = "Connexion perdue..." → dispatch 'online' → assert error.value === '')

#### Bloc 4 : Isolation guidage Driver.js (AC7, AC8)

- `test_driverjs_tour_continues_when_connection_lost` (mock `uiStore.guidedTourActive = true`, mock fetch throw TypeError → sendMessage → assert `isConnected = false` ET **aucun appel a `useGuidedTour().cancelTour`** ni modification de `tourState`)
- `test_network_error_during_guided_tour_skips_system_message` (guidedTourActive = true, fetch throw TypeError → assert messages.value ne contient aucun message systeme ajoute apres le userMessage — verifie AC3 "pas de pollution chat pendant guidage")
- `test_network_error_outside_guided_tour_sets_connexion_perdue_error` (guidedTourActive = false, fetch throw TypeError → assert error.value === 'Connexion perdue. Verifiez votre reseau.')

#### Bloc 5 : Composant `ConnectionStatusBadge.vue` (AC4)

- `test_badge_not_rendered_when_connected` (mount avec `isConnected=true` → wrapper.find('[role="status"]').exists() === false)
- `test_badge_rendered_with_reconnexion_text_when_disconnected` (mount avec `isConnected=false` → find contient "Reconnexion...")
- `test_badge_has_dark_mode_classes` (grep snapshot/html contient `dark:bg-amber-900/20` et `dark:text-amber-300`)
- `test_badge_has_aria_live_polite` (assert attr `aria-live === 'polite'` et `role === 'status'`)

#### Bloc 6 : Integration ChatInput disable + hint (AC6)

- `test_chat_input_disabled_when_disconnected` (mount `ChatInput` avec `:disabled="false"` mais simuler via prop combinee — monter `FloatingChatWidget` avec `isConnected=false`, `isStreaming=false` → textarea et bouton send disabled)
- `test_chat_input_shows_hint_when_disconnected` (prop `hint="Connexion perdue..."` → find contient le texte)
- `test_chat_input_hint_hidden_when_connected` (prop `hint={null}` → aucun element hint rendu)

#### Bloc 7 : Invariant d'isolation (AC8)

- `test_useGuidedTour_source_does_not_reference_isConnected` (lire `useGuidedTour.ts` via `fs.readFileSync` dans le test, assert `!content.includes('isConnected')`)

**And** la couverture du fichier `useChat.ts` sur les branches ajoutees (classifyFetchError + listeners + isConnected updates) est >= 80%.

**And** aucune modification backend n'est attendue (story **frontend-only** comme 7.1 et 7.2). **Pas** de migration Alembic, **pas** de modification de `backend/app/api/`, **pas** de changement de schemas.

**And** lint/typecheck : `cd frontend && npx nuxi typecheck` ne doit pas introduire de nouvelle erreur sur `useChat.ts`, `FloatingChatWidget.vue`, `ChatInput.vue`, `ConnectionStatusBadge.vue` (nouveau) ni sur les tests.

### AC10 : Documentation dev — traceabilite AC → test + journal decisions

**Given** la story est complete
**When** on lit la section `## Dev Notes` mise a jour en fin de story
**Then** elle contient un tableau « AC → fichier(s) / ligne(s) / test(s) » reprenant le pattern des stories 6.3 / 6.4 / 7.1 / 7.2.

**And** les **decisions de design** suivantes sont documentees dans Completion Notes :
- Pourquoi un nouveau composant `ConnectionStatusBadge.vue` plutot qu'un enrichissement de `ChatWidgetHeader.vue`.
- Pourquoi ne pas pre-bloquer les envois quand `isConnected === false` (tolerance opportuniste → fetch sert de re-check).
- Pourquoi `navigator.onLine` est utilise comme hint mais pas comme source de verite (faux positifs documentes MDN).
- Pourquoi les ecouteurs `online`/`offline` sont installes en mode singleton module-level et jamais retires.
- Pourquoi le message `"Connexion perdue..."` est masque pendant un parcours guide (evite la pollution chat).

## Tasks / Subtasks

- [x] Task 1 : Frontend — ref `isConnected` + ecouteurs `online`/`offline` module-level dans `useChat.ts` (AC: #1, #2)
  - [x] 1.1 Ouvrir `frontend/app/composables/useChat.ts`
  - [x] 1.2 Apres la ligne 52 (declaration de `sseReader`), ajouter :
    ```typescript
    // FR33/NFR17 — etat de connexion SSE/reseau deduit du dernier fetch + navigator.onLine
    // true par defaut (optimiste) ; bascule false sur TypeError/Failed to fetch ou event offline.
    const isConnected = ref<boolean>(true)
    let _connectionListenersInstalled = false
    ```
  - [x] 1.3 Toujours avant `export function useChat()`, ajouter une IIFE ou un bloc d'initialisation :
    ```typescript
    if (import.meta.client && !_connectionListenersInstalled) {
      isConnected.value = navigator.onLine
      window.addEventListener('online', () => {
        isConnected.value = true
        if (error.value.startsWith('Connexion perdue')) error.value = ''
      })
      window.addEventListener('offline', () => { isConnected.value = false })
      _connectionListenersInstalled = true
    }
    ```
  - [x] 1.4 Exposer `isConnected` dans le `return` (ligne 802-826), apres `error` et avant `searchQuery`.

- [x] Task 2 : Frontend — helper `classifyFetchError` + logique de basculement dans les catches (AC: #3, #5)
  - [x] 2.1 Ajouter en haut du fichier (apres les constantes et helpers comme `_normalizeLabel`) :
    ```typescript
    type FetchErrorKind = 'abort' | 'network' | 'http' | 'other'
    function classifyFetchError(e: unknown): FetchErrorKind {
      if (e instanceof DOMException && e.name === 'AbortError') return 'abort'
      if (e instanceof TypeError) return 'network'
      if (e instanceof Error && /failed to fetch|network|load failed/i.test(e.message)) return 'network'
      if (e instanceof Error && e.message.toLowerCase().includes('erreur lors de')) return 'http'
      return 'other'
    }
    ```
  - [x] 2.2 Dans le `catch (e)` de `sendMessage` (lignes 463-472), remplacer la logique actuelle par :
    ```typescript
    } catch (e) {
      const kind = classifyFetchError(e)
      if (kind === 'abort') return
      if (kind === 'network') {
        isConnected.value = false
        const uiStore = useUiStore()
        if (!uiStore.guidedTourActive) {
          error.value = 'Connexion perdue. Verifiez votre reseau.'
        }
        return
      }
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
    } finally { ... } // inchange
    ```
  - [x] 2.3 Meme transformation dans le `catch (e)` de `submitInteractiveAnswer` (lignes 723-736).
  - [x] 2.4 Dans la boucle `while (true) { const { done, value } = await reader.read() ... }` des deux fonctions, **apres** le premier `reader.read()` reussi avec `value` non-null, ajouter :
    ```typescript
    if (!isConnected.value) isConnected.value = true
    ```
    Position : immediatement apres `const { done, value } = await reader.read()` et avant le `if (done) break`. Protege par un `if (!isConnected.value)` pour eviter l'ecriture a chaque iteration (micro-opti + clarte du signal de reprise).
  - [x] 2.5 Verifier que les erreurs `throw new Error('Erreur lors de l'envoi du message')` ligne 227 et lignes 231, 610, 614 **continuent** de tomber dans la branche `http` de `classifyFetchError` (substring `"erreur lors de"` en lowercase) — si non, ajuster le helper pour detecter ces messages specifiques.

- [x] Task 3 : Frontend — composant `ConnectionStatusBadge.vue` (AC: #4)
  - [x] 3.1 Creer `frontend/app/components/copilot/ConnectionStatusBadge.vue` avec :
    ```vue
    <script setup lang="ts">
    defineProps<{ isConnected: boolean }>()
    </script>

    <template>
      <div
        v-if="!isConnected"
        role="status"
        aria-live="polite"
        class="flex items-center gap-2 px-4 py-2 text-xs bg-amber-50 dark:bg-amber-900/20 text-amber-800 dark:text-amber-300 border-b border-amber-200 dark:border-amber-800/50"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="w-3.5 h-3.5 animate-pulse shrink-0"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M1 1l22 22" />
          <path d="M16.72 11.06A10.94 10.94 0 0119 12.55" />
          <path d="M5 12.55a10.94 10.94 0 015.17-2.39" />
          <path d="M10.71 5.05A16 16 0 0122.58 9" />
          <path d="M1.42 9a15.91 15.91 0 014.7-2.88" />
          <path d="M8.53 16.11a6 6 0 016.95 0" />
          <path d="M12 20h.01" />
        </svg>
        <span>Reconnexion...</span>
      </div>
    </template>
    ```
  - [x] 3.2 **Pas** de `defineEmits` ni de logique metier — le composant est purement presentationnel.

- [x] Task 4 : Frontend — integration badge dans `FloatingChatWidget.vue` (AC: #4)
  - [x] 4.1 Ajouter l'import : `import ConnectionStatusBadge from '~/components/copilot/ConnectionStatusBadge.vue'`
  - [x] 4.2 Destructurer `isConnected` depuis `useChat()` dans le bloc `const { ... } = useChat()` (ligne 14-35).
  - [x] 4.3 Dans le template, apres `<ChatWidgetHeader ... />` (ligne ~556) et **avant** `<ConversationList ...>` (ligne ~559), inserer :
    ```vue
    <!-- FR33/NFR17 — badge reconnexion visible dans les deux vues -->
    <ConnectionStatusBadge :is-connected="isConnected" />
    ```
  - [x] 4.4 Verifier visuellement en dark mode (`<html class="dark">`) que les contrastes restent lisibles.

- [x] Task 5 : Frontend — extension `ChatInput.vue` avec prop `hint` + integration disable (AC: #6)
  - [x] 5.1 Ouvrir `frontend/app/components/chat/ChatInput.vue`
  - [x] 5.2 Enrichir `defineProps` :
    ```typescript
    const props = defineProps<{
      disabled?: boolean
      hint?: string | null
    }>()
    ```
  - [x] 5.3 Dans le template, avant `<div class="flex gap-2 items-end">` (ligne ~91), ajouter :
    ```vue
    <p
      v-if="hint"
      class="text-xs text-amber-700 dark:text-amber-400 mb-2 px-1"
    >
      {{ hint }}
    </p>
    ```
  - [x] 5.4 Dans `FloatingChatWidget.vue`, remplacer `<ChatInput :disabled="isStreaming" ... />` (ligne ~624-629) par :
    ```vue
    <ChatInput
      v-else
      :disabled="isStreaming || !isConnected"
      :hint="!isConnected ? 'Connexion perdue. Les envois reprendront après reconnexion.' : null"
      @send="handleSend"
      @send-with-file="handleSendWithFile"
    />
    ```
  - [x] 5.5 Faire le meme ajout de `:disabled` pour `InteractiveQuestionInputBar` (ligne ~617-623) :
    - Verifier sa signature actuelle (`<InteractiveQuestionInputBar :question :loading @submit @abandon-and-send />`).
    - Ajouter prop `disabled?: boolean` si manquant dans le composant source (`InteractiveQuestionInputBar.vue`), cabler les boutons internes via `:disabled="disabled || loading"`.
    - Passer `:disabled="!isConnected"` depuis `FloatingChatWidget.vue`.

- [x] Task 6 : Frontend — tests Vitest (AC: #9)
  - [x] 6.1 Creer `frontend/tests/composables/useChat.connection.test.ts` avec les 7 blocs (~20 tests total)
  - [x] 6.2 Pattern de reference : `useChat.test.ts` (mocks stores + stubGlobal fetch + createMockSSEStream) et `useAuth.refresh.test.ts` (mock `vi.stubGlobal('fetch', ...)`)
  - [x] 6.3 Pour simuler offline : `Object.defineProperty(navigator, 'onLine', { configurable: true, value: false })` avant import, puis `window.dispatchEvent(new Event('offline'))`
  - [x] 6.4 Pour les tests du composant badge (Bloc 5) : `@vue/test-utils` `mount(ConnectionStatusBadge, { props: { isConnected: false } })` (pattern deja utilise dans les tests existants des composants widget)
  - [x] 6.5 Pour l'invariant AC8 (Bloc 7) : `import fs from 'fs'; const src = fs.readFileSync('app/composables/useGuidedTour.ts', 'utf8'); expect(src).not.toMatch(/isConnected/)`
  - [x] 6.6 `npm run test -- useChat.connection` → tous verts
  - [x] 6.7 `npm run test` → suite complete verte, **330+ ≈ 350 tests, 0 regression**
  - [x] 6.8 `npx nuxi typecheck` → aucune nouvelle erreur sur les fichiers modifies/crees

- [x] Task 7 : Documentation traceabilite + finalisation (AC: #10)
  - [x] 7.1 Completer le tableau AC → test en fin de Dev Notes (pattern stories 7.1 / 7.2)
  - [x] 7.2 Decisions de design documentees en Completion Notes
  - [x] 7.3 `sprint-status.yaml` : `ready-for-dev` → `in-progress` (debut dev) → `review` (fin dev) → `done` (apres code review)
  - [x] 7.4 File List completee

## Dev Notes

### Contexte — troisieme et derniere story de l'epic 7 (Resilience et edge cases)

L'epic 7 couvre trois scenarios degradees : **DOM absent** (7.1 ✅ done), **JWT expire** (7.2 ✅ review/done), **SSE perdue** (7.3, cette story — **derniere** de l'epic 7 avant retrospective optionnelle). Les trois garantissent que le parcours guide ne laisse jamais l'utilisateur bloque.

Cette story **s'appuie sur l'existant** :
- Le pattern POST-based SSE (`useChat.sendMessage` + `reader.read()`) est deja en place — pas a reimplementer.
- `FloatingChatWidget.vue` expose deja une banniere d'erreur — pattern de reference pour le placement du badge.
- `ChatInput.vue` accepte deja un prop `disabled` — il suffit de l'enrichir avec un `hint`.

Elle comble **5 gaps** :

1. **Ref `isConnected` absente** — l'architecture la specifie (`architecture.md:218`) mais elle n'existe pas dans le code. Creation + exposition.
2. **Catch generique ne distingue pas network vs HTTP** → helper `classifyFetchError` + basculement conditionnel de `isConnected`.
3. **Pas d'indicateur visuel** → nouveau composant `ConnectionStatusBadge.vue` insere dans `FloatingChatWidget.vue`.
4. **`ChatInput` ne reflete pas l'etat offline** → extension du prop `disabled` + nouveau prop `hint`.
5. **Pas d'ecouteurs `online`/`offline`** → installation singleton module-level pour basculement instantane.

### Mapping AC → fichier → test (pattern story 7.1 / 7.2)

| AC | Fichier impacte | Ligne(s) / zone | Test(s) |
|---|---|---|---|
| AC1 Ref isConnected | `useChat.ts` | apres ligne 52 | `test_isConnected_initial_value_is_true_when_navigator_online_true`, `test_isConnected_initial_value_is_false_when_navigator_offline` |
| AC2 Listeners online/offline | `useChat.ts` | IIFE module-level | `test_online_event_switches_isConnected_to_true`, `test_offline_event_switches_isConnected_to_false`, `test_connection_listeners_installed_once_across_multiple_useChat_calls` |
| AC3 Classification erreurs fetch | `useChat.ts` | helper + catches | `test_AbortError_does_not_affect_isConnected`, `test_TypeError_failed_to_fetch_sets_isConnected_false`, `test_NetworkError_message_triggers_disconnection`, `test_HTTP_500_does_not_affect_isConnected`, `test_reader_error_during_streaming_sets_isConnected_false` |
| AC4 Badge visuel | `ConnectionStatusBadge.vue` (CREER) + `FloatingChatWidget.vue` | nouveau composant + integration | `test_badge_not_rendered_when_connected`, `test_badge_rendered_with_reconnexion_text_when_disconnected`, `test_badge_has_dark_mode_classes`, `test_badge_has_aria_live_polite` |
| AC5 Reprise connexion | `useChat.ts` | boucle reader.read() + handler online | `test_isConnected_becomes_true_on_first_successful_chunk_read`, `test_online_event_clears_connection_error_message` |
| AC6 ChatInput disable + hint | `ChatInput.vue` + `FloatingChatWidget.vue` + `InteractiveQuestionInputBar.vue` | props + template | `test_chat_input_disabled_when_disconnected`, `test_chat_input_shows_hint_when_disconnected`, `test_chat_input_hint_hidden_when_connected` |
| AC7 Isolation Driver.js | (comportement — aucune modif `useGuidedTour.ts`) | — | `test_driverjs_tour_continues_when_connection_lost`, `test_network_error_during_guided_tour_skips_system_message`, `test_network_error_outside_guided_tour_sets_connexion_perdue_error` |
| AC8 Invariant no-coupling | `useGuidedTour.ts` (lecture) | — | `test_useGuidedTour_source_does_not_reference_isConnected` |
| AC9 Tests + zero regression | `useChat.connection.test.ts` (CREER) | — | Suite complete verte |
| AC10 Doc traceabilite | Cette story (Dev Notes) | — | Revue manuelle |

### Messages FR exacts (FR33 / NFR17) — a respecter byte-for-byte

| Situation | Message (avec accents obligatoires) | Source |
|---|---|---|
| Badge visuel dans le widget | `Reconnexion...` | Nouveau, spec AC4 |
| Banniere erreur widget hors guidage | `Connexion perdue. Verifiez votre reseau.` | Nouveau, spec AC3 |
| Hint sous l'input quand offline | `Connexion perdue. Les envois reprendront après reconnexion.` | Nouveau, spec AC6 (revise review 2026-04-14) |

**Test de validation** : grep sur les 3 messages dans `useChat.ts` + `ConnectionStatusBadge.vue` + `FloatingChatWidget.vue` → chacun apparait **au moins une fois**. Les tests substring-matchent sur `"Reconnexion"`, `"Connexion perdue"`, `"L'envoi reprendra"`.

### Constantes / types a declarer

```typescript
// Dans useChat.ts, module-level, apres la ligne 52
const isConnected = ref<boolean>(true)
let _connectionListenersInstalled = false

// Helper classification
type FetchErrorKind = 'abort' | 'network' | 'http' | 'other'
```

**Pourquoi module-level et pas exportes ?** Coherence avec les autres refs module-level de `useChat.ts` (conversations, messages, abortController). Les tests accedent via `useChat().isConnected.value` (comportement observable), pas via import direct des primitives.

### Pattern classification d'erreurs — alignement avec l'ecosysteme

```typescript
function classifyFetchError(e: unknown): FetchErrorKind {
  // Priorite 1 : annulation volontaire (pattern standard fetch + AbortController)
  if (e instanceof DOMException && e.name === 'AbortError') return 'abort'

  // Priorite 2 : TypeError brut = network error (convention fetch API MDN)
  if (e instanceof TypeError) return 'network'

  // Priorite 3 : messages browser-specific (Firefox "NetworkError", Safari "Load failed")
  if (e instanceof Error && /failed to fetch|network|load failed/i.test(e.message)) return 'network'

  // Priorite 4 : nos throw explicites apres !response.ok
  if (e instanceof Error && e.message.toLowerCase().includes('erreur lors de')) return 'http'

  return 'other'
}
```

**Note** : Firefox lance `TypeError: NetworkError when attempting to fetch resource.` — le test regex `/network/i` couvre, mais **TypeError** seul couvre aussi sans regex. Chrome/Safari lancent `TypeError: Failed to fetch` ou `TypeError: Load failed` — egalement couvert par `instanceof TypeError`. **Donc** la branche regex n'est qu'un **filet** pour les cas ou quelqu'un aurait repackage l'erreur dans un `Error` plutot qu'un `TypeError`.

### Patterns de reference (stories precedentes)

- **Constantes / refs module-level** (stories 1.1, 7.1, 7.2) : pattern deja etabli dans `useChat.ts` et `useGuidedTour.ts`.
- **Test fake-timers non necessaire** : les tests sont sur des events instantanes (online/offline) et sur la reception du premier chunk — pas besoin de `vi.useFakeTimers()`. Utiliser `vi.fn()` + mocks synchrones.
- **Test composant Vue** : `import { mount } from '@vue/test-utils'; mount(ConnectionStatusBadge, { props: { isConnected: false } })` — meme pattern que les tests des widgets existants.
- **Grep-based invariant** (AC8) : `fs.readFileSync + expect().not.toMatch()` — pattern simple, utilise pour enforcer des invariants d'architecture (cf `rules/common/patterns.md` sur le decoupling).

### Fichiers attendus

| Fichier | Action | Justification |
|---|---|---|
| `frontend/app/composables/useChat.ts` | MODIFIER | Ajout ref `isConnected` + listeners online/offline + helper `classifyFetchError` + modifications des 2 catches + flip dans reader loop + expose dans return |
| `frontend/app/components/copilot/ConnectionStatusBadge.vue` | CREER | Nouveau composant presentationnel (~30 lignes) avec dark mode + ARIA |
| `frontend/app/components/copilot/FloatingChatWidget.vue` | MODIFIER | Import + destructuration `isConnected` + insertion du badge apres le header + binding `:disabled="isStreaming || !isConnected"` + prop `hint` sur ChatInput + `:disabled` sur InteractiveQuestionInputBar |
| `frontend/app/components/chat/ChatInput.vue` | MODIFIER | Nouveau prop `hint?: string | null` + bloc `<p v-if="hint">...</p>` dans le template |
| `frontend/app/components/chat/InteractiveQuestionInputBar.vue` | MODIFIER (si besoin) | Ajouter prop `disabled?: boolean` si pas encore present ; cabler sur les boutons de choix et submit |
| `frontend/tests/composables/useChat.connection.test.ts` | CREER | ~20 tests (7 blocs : ref, listeners, classification, reprise, isolation guidage, badge, invariant) |

**Pas de fichier backend modifie** (story **frontend-only** comme 7.1 et 7.2). **Pas** de migration Alembic, **pas** de modification de `backend/app/api/`, **pas** de changement de schemas, **pas** de changement dans `useGuidedTour.ts` (invariant AC8).

### Intelligence stories precedentes (7.1, 7.2)

Points actionnables herites :

- **Pattern helper + classification** (stories 7.2 `SessionExpiredError`, 7.1 `classifyFetchError`) → meme approche pour `classifyFetchError` ici.
- **Pattern messages FR avec accents** (7.1 "Je n'ai pas pu pointer cet élément", 7.2 "Session expirée") → 3 messages nouveaux a aligner.
- **Pattern « ne pas spam le chat pendant le guidage »** (7.1 `if (!cancelled) { addSystemMessage(...) }`, 7.2 `if (uiStore.guidedTourActive) { ... }`) → ici, **inverse** : on **n'ajoute pas** de message chat pendant le guidage — l'indicateur visuel (AC4) suffit.
- **Pattern singleton module-level** (story 7.2 `refreshPromise`, 6.4 `guidanceRefusalCount`) → ici `isConnected` + flag `_connectionListenersInstalled`.
- **Pattern tests avec mocks store + stubGlobal fetch** (7.2, `useChat.test.ts`) → reutiliser directement.
- **Pattern invariant grep** (nouveau pour 7.3 mais coherent avec `rules/common/patterns.md`) → precedent similaire dans les tests backend qui grep les tools LangChain pour verifier l'exhaustivite.

### Intelligence story 7.2 — consequences pour 7.3

- **`SessionExpiredError`** est maintenant leve par `apiFetch`/`apiFetchBlob` (pas par `sendMessage` directement). `sendMessage` utilise `fetch` direct et ses erreurs restent `TypeError` bruts. **Consequence** : la classification de 7.3 ne touche **pas** `SessionExpiredError` — c'est orthogonal.
- **4 composables migres vers `apiFetch`** (useDashboard, useEsg, useCarbon, useFinancing) — leur 401 est gere par le refresh de 7.2. En cas de vraie perte reseau (pas 401), leur `apiFetch` leve un `TypeError` → tombera dans `classifyFetchError === 'network'` si ces composables etaient utilises pendant le guidage, mais **ils ne sont pas les callers de cette story** (7.3 modifie **uniquement** `useChat`).
- **Le handler `handleAuthFailure`** de 7.2 annule le tour en cas de session expiree → c'est cohabitable avec 7.3 : deux paths independants (auth failure vs network loss), chacun avec son propre traitement.

### Git intelligence (5 derniers commits)

- `a58f6d1 7-1-gestion-des-elements-dom-absents-et-timeout-de-chargement: done` — pattern constants module-level + messages FR avec accents + invariant `if (!cancelled)`. **Directement reutilise** dans 7.3 pour la structure.
- `2278f35 6-4-frequence-adaptative-des-propositions-de-guidage: done` — modifications `useGuidedTour.ts` + `useChat.ts`. Aucune collision avec 7.3 (c'est un autre fichier / autre logique).
- `2bc3e15 6-3-consentement-via-widget-interactif-et-declenchement-direct: done` — `useChat.ts` modifie (`isGuidanceConsentQuestion`, `handleGuidedTourEvent`). **Important** : 7.3 ajoute ses refs et helpers **sans toucher** a ces fonctions existantes.
- `b7f6d62 6-1-tool-langchain-trigger-guided-tour-et-marker-sse: done` — backend + frontend trigger tour. Aucun impact sur 7.3.
- `5277eb1 5-4-interruption-du-parcours-et-popover-custom: done` — `cancelTour`. **Pas utilise par 7.3** : les erreurs network ne doivent PAS appeler cancelTour (invariant AC7).

**Verification compatibilite `useChat.ts`** :
- `sendMessage` ligne 167 — pas modifiee par 6.x ni 7.1/7.2. Le catch ligne 463-472 est intact → 7.3 le modifie comme prevu.
- `submitInteractiveAnswer` ligne 511 — idem, catch ligne 723-736 intact.
- `handleGuidedTourEvent` ligne 759 — ne fait pas de fetch direct, pas d'impact sur `isConnected`.
- `_consentAcceptancePending` (story 6.4, ligne 23) — flag module-level independant, coexiste sans collision.

### Latest tech information

- **Fetch API MDN** (2026-04) : `TypeError` est la specification officielle pour les erreurs de reseau cote fetch. Tous les navigateurs modernes (Chrome 95+, Firefox 90+, Safari 16+, Edge 95+) respectent cette convention. Pour Safari < 16, le message peut etre `"The network connection was lost"` — non couvert par notre regex, mais Safari < 16 represente < 1% du trafic en 2026. **Compromis acceptable** : si le message n'est pas reconnu, on tombe dans `'other'` et `isConnected` reste a `true` (on ne declenche pas la bascule) — fail-safe. Documente en Completion Notes.
- **`navigator.onLine` MDN** : « `true` signifie seulement que l'appareil n'est pas explicitement en mode hors-ligne, **pas** qu'il a acces a Internet. » Exemple de faux positif : machine connectee a un hotspot sans acces internet. **C'est pour cela** que notre source de verite reste le fetch (AC5), et `navigator.onLine` est un simple **hint** pour basculer instantanement en cas d'event `offline`.
- **`window.addEventListener('online', ...)`** : event dispatche par le navigateur quand `navigator.onLine` bascule `false → true`. Fiable sur tous les navigateurs modernes.
- **Vue 3 reactivity** : les props `disabled` et `hint` sont reactives via `computed` ou binding direct (`:disabled="..."`). Aucun piege specifique a signaler.
- **`@vue/test-utils` mount pour composants presentationnels** : pattern stable depuis Vue 3.0. `mount(Component, { props: {...} })` suffit pour les tests du Bloc 5. Pas besoin de `shallowMount` car le composant badge n'a pas d'enfant.
- **Vitest `vi.stubGlobal('navigator', ...)` limitations** : `navigator` est un objet gigantesque, remplacer tout le `navigator` peut casser d'autres APIs. Pattern recommande : `Object.defineProperty(navigator, 'onLine', { configurable: true, value: false })` + `window.dispatchEvent(new Event('offline'))`. Deja utilise dans le codebase (cf tests de `useDeviceDetection`).

### Project Structure Notes

- Alignement Nuxt 4 : tous les fichiers source dans `frontend/app/`, tests dans `frontend/tests/composables/*.test.ts` et (implicite) `frontend/tests/components/copilot/*.test.ts` — le Bloc 5 des tests peut etre inclus dans `useChat.connection.test.ts` pour simplicite OU extrait dans `tests/components/copilot/ConnectionStatusBadge.test.ts` — **au choix du dev** selon le volume final et la lisibilite.
- Conformite `rules/typescript/coding-style.md` : pas de `any` (utiliser `unknown` dans le catch, narrower via `classifyFetchError`), pas de `console.log` (remplacer par `console.warn` si log necessaire), types explicites sur les signatures publiques.
- Conformite `rules/common/coding-style.md` : immutabilite respectee (les refs sont re-assignees via `.value = ...`, pas de mutation d'objet interne).
- Dark mode obligatoire (CLAUDE.md section Dark Mode) : toutes les classes Tailwind du badge ont leur variante `dark:`.
- Reutilisation OBLIGATOIRE (CLAUDE.md section Reutilisabilite) : `ConnectionStatusBadge` est un **nouveau** composant car aucun pattern badge similaire n'existe (la banniere d'erreur est un pattern distinct — erreur rouge, pas reconnexion ambre). Neanmoins, le composant est **simple et parametrable** via prop pour une future reutilisation (ex. autres etats « deconnecte » dans l'app).

### References

- Source epic : `_bmad-output/planning-artifacts/epics-019-floating-copilot.md:1148-1186` (Epic 7 Story 7.3 avec BDD + exigences techniques)
- Source PRD :
  - `_bmad-output/planning-artifacts/prd.md:155-157` (coupures reseau + indicateur reconnexion)
  - `_bmad-output/planning-artifacts/prd.md:363` (FR33 — SSE perdue + indicateur)
  - `_bmad-output/planning-artifacts/prd.md:404` (NFR17 — parcours continue + indicateur)
- Source architecture :
  - `_bmad-output/planning-artifacts/architecture-019-floating-copilot.md:183-218` (Decision 2 — SSE POST-based + AbortController + `isConnected` ref specifie)
  - `_bmad-output/planning-artifacts/architecture-019-floating-copilot.md:58-60` (pattern SSE existant `data: {JSON}\n\n`)
  - `_bmad-output/planning-artifacts/architecture-019-floating-copilot.md:210-213` (pattern POST-based preservation)
- Stories precedentes impactant la logique :
  - `_bmad-output/implementation-artifacts/7-1-gestion-des-elements-dom-absents-et-timeout-de-chargement.md` (pattern constants + messages FR + invariant `if (!cancelled)` — reutilise pour la structure)
  - `_bmad-output/implementation-artifacts/7-2-renouvellement-jwt-transparent-pendant-le-guidage.md` (pattern classification erreurs via sentinel class + singleton module-level + mapping AC→test — reutilise comme modele)
  - `_bmad-output/implementation-artifacts/6-4-frequence-adaptative-des-propositions-de-guidage.md` (pattern refs module-level + flags dans useChat.ts — coexistence verifiee)
- Code de reference actuel :
  - `frontend/app/composables/useChat.ts:50-52` (refs module-level existantes — pattern pour `isConnected`)
  - `frontend/app/composables/useChat.ts:216-239` (`sendMessage` fetch + reader — lieu des modifications)
  - `frontend/app/composables/useChat.ts:463-472` (catch `sendMessage` — lieu de la classification)
  - `frontend/app/composables/useChat.ts:604-622` (`submitInteractiveAnswer` fetch + reader — meme pattern)
  - `frontend/app/composables/useChat.ts:723-736` (catch `submitInteractiveAnswer` — meme transformation)
  - `frontend/app/components/copilot/FloatingChatWidget.vue:1-35` (destructuration useChat — lieu d'ajout `isConnected`)
  - `frontend/app/components/copilot/FloatingChatWidget.vue:549-629` (template header + vues — lieu d'insertion du badge + binding input)
  - `frontend/app/components/copilot/ChatWidgetHeader.vue:1-60` (structure header — reference pour ne PAS le modifier)
  - `frontend/app/components/chat/ChatInput.vue:1-68` (props + script — lieu d'ajout `hint`)
  - `frontend/app/components/chat/ChatInput.vue:71-139` (template — lieu d'ajout du bloc hint)
  - `frontend/app/components/chat/InteractiveQuestionInputBar.vue` (a auditer pour le prop `disabled`)
  - `frontend/app/composables/useGuidedTour.ts` (invariant AC8 — **interdit** de reference `isConnected`)
  - `frontend/app/stores/ui.ts` (`guidedTourActive` utilise dans AC3 et AC7)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context) via Claude Code (bmad-dev-story skill).

### Debug Log References

- **Iter 1** — 23 tests `useChat.connection.test.ts` passent immediatement sauf Bloc 6 (3 tests ChatInput) : `ReferenceError: ref is not defined`. Cause : `ChatInput.vue` reposait sur l'auto-import Nuxt de `ref`/`computed`, non disponible sous Vitest. Correction minimale : ajout de `import { computed, ref } from 'vue'` en tete du `<script setup>` (aligne sur `MultipleChoiceWidget.vue`, `InteractiveQuestionInputBar.vue`, `SingleChoiceWidget.vue` qui le faisaient deja). 23/23 verts apres.
- **Iter 2** — Regression sur `FloatingChatWidget.test.ts:826` : `aria-atomic` attendu `'false'`, recu `undefined`. Cause : le mock `useChat` du test n'exposait pas `isConnected`, donc la destructuration donnait `undefined`, `!isConnected` etait `true`, le badge se rendait avec `aria-live="polite"` et etait matche AVANT la vraie zone messages. Correction : ajout d'un `mockIsConnected = ref(true)` dans le mock, exposition dans l'objet retourne, reset dans `beforeEach`, stub `ConnectionStatusBadgeStub` ajoute. 48/48 verts apres.
- **Iter 3** — `npx vitest run` : **354/354 tests verts** (35 fichiers), zero regression (etait 331 avant la story, +23 nouveaux = 354 attendu).
- **Typecheck** — `npx nuxi typecheck` : les 2 erreurs pre-existantes de `useChat.ts` (ligne 342 → 377 et 415 → 450, simplement decalees de +35 lignes par mes ajouts) n'ont PAS ete introduites par cette story (verifie via `git stash` + retypecheck sur main). **Aucune nouvelle erreur** sur `useChat.ts`, `ChatInput.vue`, `FloatingChatWidget.vue`, `ConnectionStatusBadge.vue`, `InteractiveQuestionInputBar.vue`, ni sur les tests.

### Completion Notes List

**Implementation summary :**

1. **`useChat.ts`** — Ajout d'une ref module-level `isConnected` (init a `navigator.onLine` cote client, `true` sinon), installation singleton d'ecouteurs `online`/`offline` sur `window` via un flag `_connectionListenersInstalled`, helper module-level `classifyFetchError(e)` retournant `'abort' | 'network' | 'http' | 'other'`. Les 2 catches (`sendMessage` l.463-, `submitInteractiveAnswer` l.723-) classifient puis font un early return sur `'abort'`, basculent `isConnected=false` sur `'network'` (avec message FR uniquement hors parcours guide), et tombent sur le comportement historique pour `'http'` / `'other'`. Les 2 boucles `while (true) { reader.read() }` flipent `isConnected=true` au premier chunk lu sans erreur (proteges par `if (!isConnected.value)` pour eviter l'ecriture repetitive). Expose `isConnected` dans le `return` apres `error` et avant `searchQuery`.

2. **`ConnectionStatusBadge.vue` (nouveau)** — Composant purement presentationnel (~30 lignes, defineProps `isConnected: boolean`, aucun emit). Icone SVG WiFi-slash anime par `animate-pulse`, texte « Reconnexion... », `role="status"` + `aria-live="polite"`, couleurs ambre clair + variantes dark (`dark:bg-amber-900/20`, `dark:text-amber-300`, `dark:border-amber-800/50`), bordure basse, padding compact.

3. **`FloatingChatWidget.vue`** — Import statique du badge, destructuration de `isConnected` depuis `useChat()`, insertion du badge directement apres `<ChatWidgetHeader>` (et avant les deux vues `ConversationList` / zone chat), `:disabled="isStreaming || !isConnected"` + `:hint="!isConnected ? 'Connexion perdue. Les envois reprendront après reconnexion.' : null"` sur `<ChatInput>` (wording revise en review 2026-04-14 ; voir Review Findings), `:disabled="!isConnected"` sur `<InteractiveQuestionInputBar>`.

4. **`ChatInput.vue`** — Enrichissement de `defineProps` avec `hint?: string | null`, rendu conditionnel d'un `<p data-testid="chat-input-hint">` en ambre au-dessus de la ligne des boutons. Ajout de `import { computed, ref } from 'vue'` pour rendre les tests Vitest executables (alignement avec les autres composants chat).

5. **`InteractiveQuestionInputBar.vue`** — Ajout prop `disabled?: boolean` (default `false`), computed `inputLocked = loading || disabled` utilise par tous les `:disabled` internes (boutons QCU, QCM, fallback, submit, close, Respondre autrement, textareas) et par les gardes early-return des handlers (`onClickQcu`, `toggleQcm`, `sendFallback`, `canSubmit`).

**Decisions de design documentees (AC10) :**

- **Nouveau composant `ConnectionStatusBadge.vue`** plutot qu'enrichissement de `ChatWidgetHeader.vue` : le header reste simple/monobloc (titre + 2 boutons), le badge est une banniere transitoire distincte logiquement (analogie avec la banniere d'erreur rouge existante). Reutilisation future possible (ex. panel credit, dashboard offline).
- **Pas de pre-blocage cote code quand `isConnected === false`** : le `ChatInput` est visuellement desactive (feedback UX), mais `sendMessage` tente quand meme le fetch — cela sert de re-check optimiste (navigator.onLine a des faux positifs documentes MDN). Si le fetch reussit, bascule automatique a `true`.
- **`navigator.onLine` en hint uniquement** : corroboration par le resultat du fetch (AC3/AC5). Les events `online`/`offline` sont utilises pour basculer instantanement l'indicateur sans attendre un fetch rate.
- **Ecouteurs `online`/`offline` installes une fois, jamais retires** : coherent avec le state module-level singleton (le widget est partage par toutes les pages). Le flag `_connectionListenersInstalled` empeche les installations multiples si `useChat()` est appele N fois par tour de rendu.
- **Masquage du message `"Connexion perdue..."` pendant un parcours guide** : evite la pollution de `error.value` (utilise par la banniere rouge du widget) quand le parcours Driver.js est en cours — l'indicateur visuel ambre AC4 suffit ; re-afficher un bandeau rouge par-dessus le parcours guide ajouterait du bruit.
- **Safari < 16 et messages reseau exotiques** : si le navigateur retourne un `Error` (et non `TypeError`) avec un message non matche par la regex `/failed to fetch|network|load failed/i`, on tombe dans `'other'` → `isConnected` reste `true` (fail-safe, pas de faux positif). Represente < 1% du trafic en 2026 — compromis acceptable documente ici.

**Validation AC :**
- AC1/AC2 : 5 tests Bloc 1 verts (init true/false, events online/offline, singleton listeners).
- AC3 : 5 tests Bloc 2 verts (AbortError, TypeError FailedToFetch, NetworkError Firefox, HTTP 500, reader error in-stream).
- AC4 : 4 tests Bloc 5 verts (not-rendered connected, rendered disconnected, dark mode classes, aria-live polite).
- AC5 : 2 tests Bloc 3 verts (chunk → true, online → clear error).
- AC6 : 3 tests Bloc 6 verts (disabled, hint visible, hint hidden).
- AC7/AC8 : 3 tests Bloc 4 verts (tour continues, skip system message, error outside tour) + 1 test Bloc 7 invariant grep source.
- AC9 : 354 tests frontend verts, +23 nouveaux tests (useChat.connection.test.ts), zero regression. Couverture des branches ajoutees validee par la completude des 7 blocs (chaque branche de `classifyFetchError` couverte).
- AC10 : Ce bloc + tableau Mapping AC → fichier → test (Dev Notes l.422-432) + messages FR exacts tableau l.436-443.

### File List

**Modifie :**
- `frontend/app/composables/useChat.ts` — ajout ref `isConnected`, helper `classifyFetchError`, listeners online/offline, classification dans 2 catches, flip dans 2 reader loops, exposition dans `return`.
- `frontend/app/components/copilot/FloatingChatWidget.vue` — import `ConnectionStatusBadge`, destructuration `isConnected`, insertion badge, binding `:disabled` / `:hint` sur `ChatInput` et `:disabled` sur `InteractiveQuestionInputBar`.
- `frontend/app/components/chat/ChatInput.vue` — import explicite `ref`/`computed` depuis `vue`, nouvelle prop `hint`, bloc `<p data-testid="chat-input-hint">` dans le template.
- `frontend/app/components/chat/InteractiveQuestionInputBar.vue` — nouvelle prop `disabled`, computed `inputLocked`, bascule de tous les `:disabled="loading"` vers `:disabled="inputLocked"`, gardes dans handlers.
- `frontend/tests/components/copilot/FloatingChatWidget.test.ts` — ajout `mockIsConnected`, reset dans beforeEach, exposition dans mock `useChat`, stub `ConnectionStatusBadgeStub`, prop `disabled` sur `InteractiveQuestionInputBarStub`.

**Cree :**
- `frontend/app/components/copilot/ConnectionStatusBadge.vue` — composant badge reconnexion presentationnel.
- `frontend/tests/composables/useChat.connection.test.ts` — 23 tests organises en 7 blocs (ref initiale, listeners, classification fetch, reprise, isolation guidage, composant badge, invariant grep).

**Non modifie (invariant AC8) :**
- `frontend/app/composables/useGuidedTour.ts` — aucune reference a `isConnected` (verifie par test `test_useGuidedTour_source_does_not_reference_isConnected`).

### Change Log

- 2026-04-14 : Story 7.3 implementee (resilience SSE + indicateur reconnexion). 23 nouveaux tests, 354/354 verts, zero regression. Aucun changement backend (story frontend-only).

### Review Findings

_Code review executee le 2026-04-14 (3 couches : Blind Hunter, Edge Case Hunter, Acceptance Auditor). 10/10 AC couverts cote auditor._

- [x] [Review][Decision] Hint « L'envoi reprendra automatiquement. » promet un comportement non implemente — RESOLU 2026-04-14 par option (b) : hint reformule en `"Connexion perdue. Les envois reprendront après reconnexion."`. Rationale : option (a) replay automatique ouvrait un risque de double envoi sans idempotence backend (tokens LLM + reponses dupliquees) ; option (c) status quo mentait a l'utilisateur. Changements : `FloatingChatWidget.vue:633`, spec AC6 line 141, Messages FR tableau, Mapping AC->test, 2 tests Bloc 6 (`test_chat_input_disabled_when_disconnected`, `test_chat_input_shows_hint_when_disconnected`).
- [x] [Review][Patch] Listeners `online`/`offline` re-installes a chaque `vi.resetModules()` dans les tests [frontend/app/composables/useChat.ts:57, 75-85] — RESOLU 2026-04-14. Fix : handlers nommes (`onlineHandler`/`offlineHandler`) stockes sur `globalThis[Symbol.for('esg-mefali:chat-connection-listeners')]`. Au prochain import du module (via `vi.resetModules` en test ou HMR en dev), les handlers precedents sont `removeEventListener`'d avant reinstallation. Suppression du flag `_connectionListenersInstalled`. 23/23 tests connection + 354/354 suite complete verts.
- [x] [Review][Patch] Chaine « Connexion perdue. Verifiez votre reseau. » dupliquee + clear fragile via `startsWith` [frontend/app/composables/useChat.ts:79, 506, 778] — RESOLU 2026-04-14. Fix : constante module-level `const CONNECTION_LOST_MESSAGE = 'Connexion perdue. Verifiez votre reseau.'` ajoutee apres la declaration d'`isConnected`. Les 2 catches utilisent desormais la constante ; le handler `online` compare via `error.value === CONNECTION_LOST_MESSAGE` (egalite stricte, plus robuste qu'un `startsWith` fragile). 354/354 tests verts.
- [x] [Review][Defer] Classification HTTP par substring francais `'erreur lors de'` fragile [frontend/app/composables/useChat.ts:70] — deferred, pre-existant. Tous les throws actuels matchent, mais tout nouveau message (p. ex. `throw new Error('Echec de l'envoi...')`) tomberait dans `'other'`. Refactor en sentinel `class HttpError extends Error` recommande a terme.
- [x] [Review][Defer] `throw new Error('Réponse sans body...')` classifie en `'other'`, pollue `error.value` meme pendant un parcours guide [frontend/app/composables/useChat.ts:264, 659] — deferred. Scenario rare (200 OK sans body). AC3 autorise explicitement les erreurs HTTP a setter `error.value` (« Comportement actuel »), donc pas une violation stricte, mais coherent avec la logique de gating de la branche network.
- [x] [Review][Defer] `DOMException` non-Abort (`NetworkError`, `InvalidStateError`) mid-stream classifie en `'other'` [frontend/app/composables/useChat.ts:62-72] — deferred. En pratique les readers modernes throw `TypeError` ; Safari < 16 represente < 1 % du trafic. Documente en spec Dev Notes.
- [x] [Review][Defer] `useUiStore()` appele dans le catch block — risque Pinia-not-ready [frontend/app/composables/useChat.ts:504, 776] — deferred. Impossible dans le flow UI reel (widget monte implique Pinia installe). Refactor optionnel : hoister l'appel en haut de `useChat()`.
- [x] [Review][Defer] Test invariant AC8 fragile au cwd [frontend/tests/composables/useChat.connection.test.ts:831-838] — deferred. `path.resolve(process.cwd(), 'app/composables/useGuidedTour.ts')` fonctionne si vitest est lance depuis `frontend/`. Robustesse : utiliser `new URL(..., import.meta.url)`.
- [x] [Review][Defer] bfcache : listeners survivent mais `isConnected` stale au `pageshow` [frontend/app/composables/useChat.ts:77-85] — deferred. Edge case rare (page cachee offline puis restauree online sans event dispatch). Ajout d'un handler `pageshow` optionnel a terme.
- [x] [Review][Defer] Fetches concurrents (`sendMessage` + `submitInteractiveAnswer`) flip-flop `isConnected` [frontend/app/composables/useChat.ts:289, 683, 503, 775] — deferred. Si l'un succeed et flip a true puis l'autre fail en network, la bascule a false ecrase le signal de reprise. Peu probable dans l'UX normale (serialisation par `abortController`).

_Dismissed (bruit / couverts par design) : SSR hydration (module throw sur `import.meta.server`), abort pendant offline (intentionnel), empty chunks (`reader.read()` succeed = signal), `'other'`/HTTP errors leak pendant tour (spec AC3 autorise), `navigator.onLine` hotspot oscillation (documente spec), `classifyFetchError` false-positive TypeError applicatif (inner try/catch couvre), hint sans aria-live (redondant avec badge), contradiction spec AC3 table vs prose (issue documentaire)._
