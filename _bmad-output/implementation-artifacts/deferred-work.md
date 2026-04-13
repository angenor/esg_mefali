# Deferred Work

## Deferred from: code review of story 1-1-refactoring-usechat-en-module-level-state (2026-04-12)

- **F8** — Parsing SSE sans buffer inter-chunks : les events SSE tronqués aux frontières TCP sont silencieusement ignorés. `useChat.ts:200`. Pré-existant, non introduit par cette story.
- **F9** — Logique SSE dupliquée entre `sendMessage` et `submitInteractiveAnswer` : le second n'écoute qu'un sous-ensemble d'events (manque profile_update, tool_call_*, report_suggestion, error). `useChat.ts:536-613`. Pré-existant.
- **F10** — Pas de fonction `reset()` au logout : le state singleton module-level persiste entre sessions utilisateur dans le même onglet. `useChat.ts:15-41`. Scope plus large que cette story.
- **F11** — `computed()` appelé au module-level sans `effectScope` : l'effet réactif n'est jamais garbage-collecté. `useChat.ts:43-49`. Impact marginal en SPA.
- **F7** — Test T3.4 n'assert pas réellement l'appel à `abort()` : le test vérifie le comportement fonctionnel mais pas le mécanisme interne. `useChat.test.ts:165`. Amélioration nice-to-have.

## Deferred from: code review of story 1-2-composable-usedevicedetection (2026-04-12)

- **W1** — State module-level ne se réinitialise pas au logout : conversations, messages et questions interactives persistent entre sessions utilisateur. `useChat.ts:18-44`. Pré-existant (voir aussi F10).
- **W2** — Race condition concurrent sendMessage + submitInteractiveAnswer : les deux fonctions écrivent dans le même `streamingContent` ref et le même index de messages. `useChat.ts:261, 588`. Pré-existant.
- **W3** — interactiveQuestionsByMessage clé UUID temporaire orpheline quand l'event `done` est absent. `useChat.ts:362-368`. Pré-existant (feature 018).
- **W4** — Boucle SSE dupliquée entre sendMessage et submitInteractiveAnswer (~200 lignes). `useChat.ts:208-415, 561-638`. Pré-existant (voir aussi F9).
- **W5** — Pas d'AbortController sur fetchConversations/fetchMessages/deleteConversation. `useChat.ts:71-77, 96-103, 429-439`. Pré-existant.
- **W6** — TextDecoder sans `{ stream: true }` — caractères multi-octets tronqués aux frontières de chunks. `useChat.ts:197, 551`. Pré-existant (voir aussi F8).

## Deferred from: code review of story 1-3-bouton-flottant-et-conteneur-du-widget (2026-04-12)

- **W1** — `prefersReducedMotion` non-réactif (snapshot au mount, pas de listener `change`). `FloatingChatWidget.vue:12`. Story 1.7 accessibilité.
- **W2** — AbortController/sseReader jamais cleanup à la navigation. `useChat.ts:43-44`. Pré-existant (scope story 1-1).
- **W3** — `sseReader.cancel()` race condition entre check et reassignment (yield entre await et assignment). `useChat.ts:190-195`. Pré-existant (scope story 1-1).
- **W4** — `isStreaming` guard bloque les nouveaux messages sans aborter le stream en cours. `useChat.ts:133`. Pré-existant (scope story 1-1).
- **W5** — `useDeviceDetection` listener leak si appelé hors scope Vue en production (warning dev-only). `useDeviceDetection.ts:22-29`. Pré-existant (scope story 1-2).
- **W6** — Widget `h-[600px]` overflow viewport sur écrans courts (<680px), header clippé. `FloatingChatWidget.vue:67`. Story 1.6 redimensionnement.

## Deferred from: code review of story 1-4-en-tete-du-widget-et-historique-des-conversations (2026-04-13)

- **F5** — Double appel `fetchConversations` possible en cas de toggle rapide (pas de guard `isFetching`). `FloatingChatWidget.vue:67`. Edge case mineur, pas de consequence grave.
- **F7** — Decalage visuel du titre quand le bouton retour apparait/disparait (flex layout shift). `ChatWidgetHeader.vue:17-30`. Cosmetic, a traiter en Story 1.7 accessibilite.

## Deferred from: code review of story 1-5-integration-du-chat-complet-dans-le-widget (2026-04-13)

- **D1** — Quick actions WelcomeMessage non cablees : `handleQuickAction` defini mais jamais lie au template. Gap pre-existant (pages/chat.vue non plus). Story dediee necessaire pour ajouter emit a WelcomeMessage sans violer AC9.
- **D3** — `reportSuggestion` non affiche dans le widget : banniere rapport PDF omise, widget 400px trop etroit. Enhancement future.
- **W1** — `prefersReducedMotion` non-reactif (snapshot au mount, pas de listener `change`). `FloatingChatWidget.vue:41`. Deja traque pour story 1.7 accessibilite.
- **W2** — Race condition concurrente dans `sendMessage` de `useChat.ts` : pas de mutex atomique entre le guard `isStreaming` et son assignment. `useChat.ts:132`. Pre-existant (scope story 1-1).
