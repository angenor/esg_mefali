# Architecture Frontend — Nuxt 4 + Vue 3

## 1. Résumé exécutif

Application SPA/SSR bâtie sur **Nuxt 4.4** avec Vue 3 Composition API stricte en TypeScript. State global Pinia, styling TailwindCSS 4 avec dark mode intégré, animations GSAP, rendu de diagrammes Mermaid, graphiques Chart.js et tours guidés driver.js. L'expérience utilisateur clé est un **widget de chat flottant** (refactor spec 019) disponible sur toutes les pages, piloté par un state module-level qui survit à la navigation.

**Philosophie** : code et identifiants en anglais, UI et commentaires en français accentué, composition par modules métier, réutilisation forte via composables + composants `ui/`.

## 2. Stack technique

| Catégorie | Techno | Version | Justification |
|---|---|---|---|
| Framework | Nuxt | `^4.4.2` | Structure Nuxt 4 (tout sous `app/`), routing fichier, runtimeConfig |
| UI | Vue | 3 Composition API | `<script setup lang="ts">` systématique |
| Langage | TypeScript | `^5.7.0` (strict) | Garantie de types, refactor sûr |
| State | Pinia | `^3.0.4` | Setup stores, meilleur DX qu'avec Vuex |
| Styling | TailwindCSS | `^4.2.2` + `@nuxtjs/tailwindcss 6.14` | Utility-first + @theme pour variables dark mode |
| Animations | GSAP | `^3.12.0` | Rétraction du widget chat synchronisée avec driver.js |
| Charts | Chart.js + vue-chartjs | `^4.4.0` / `^5.3.0` | Scores, timelines, benchmarks |
| Diagrammes | Mermaid | `^11.4.0` | Rendu de blocs mermaid streamés par le backend |
| Tours guidés | driver.js | `^1.4.0` | Popovers, lazy-loadé (ADR7) |
| Markdown | marked + dompurify | `^17.0.5` / `^3.3.3` | Parsing + sanitization des messages assistant |
| Tests unit | Vitest + @vue/test-utils + happy-dom | `^3.0.0` | Rapide, pas de jsdom |
| Tests E2E | Playwright | `^1.49.0` | Chromium, mono-worker, backend mocké |
| Nuxt modules | `@pinia/nuxt` | `^0.11.3` | Seul module Nuxt activé |

## 3. Architecture — pattern

- **Composition par domaine métier** : chaque grand module (ESG, carbon, financing, applications, credit, action-plan, dashboard) a son trio `components/<domain>/ + composables/use<Domain>.ts + stores/<domain>.ts + pages/<domain>/`.
- **Composables à state module-level** : 3 composables partagent leur état au niveau du module (donc unique par runtime) :
  - `useAuth` — single-flight refresh token ;
  - `useChat` — SSE reader + conversations + widgets interactifs (survit à la navigation) ;
  - `useGuidedTour` — machine à états du tour actif (un seul tour à la fois).
- **Runtime config** : URL API via `runtimeConfig.public.apiBase` (pas de hard-code).
- **Accessibilité** : focus trap pour le widget chat et les popovers, ARIA sur les widgets QCU/QCM (`radiogroup`, `checkbox`, `aria-checked`, `aria-describedby`), `prefersReducedMotion`.

## 4. Point d'entrée et layout

- [frontend/nuxt.config.ts](../frontend/nuxt.config.ts) — déclare modules, css, runtimeConfig.
- [frontend/app/app.vue](../frontend/app/app.vue) — racine Vue.
- [frontend/app/layouts/default.vue](../frontend/app/layouts/default.vue) — layout unique : `AppHeader` + `AppSidebar` + `<slot />` + widget chat flottant (copilot). Intègre le `FloatingChatButton` pour ouvrir/rouvrir le widget.

Le layout par défaut est appliqué à toutes les pages sauf `login.vue` et `register.vue` qui n'ont pas besoin du chrome applicatif (middleware public).

## 5. Architecture par dossier (`app/`)

### Pages (17)

Les pages suivent le routing automatique de Nuxt. Toutes protégées par `auth.global.ts` sauf `/login` et `/register`.

| Route | Fichier | Rôle |
|---|---|---|
| `/` | `pages/index.vue` | Accueil (redirige vers le dashboard selon contexte) |
| `/login` | `pages/login.vue` | Connexion (publique) |
| `/register` | `pages/register.vue` | Inscription (publique) |
| `/dashboard` | `pages/dashboard.vue` | KPIs agrégés : ESG / carbone / crédit / financements (tour `show_dashboard_overview`) |
| `/profile` | `pages/profile.vue` | Édition profil entreprise |
| `/documents` | `pages/documents.vue` | Liste, upload, aperçu documents |
| `/esg` | `pages/esg/index.vue` | Questionnaire ESG conversationnel |
| `/esg/results` | `pages/esg/results.vue` | Scores + recommandations (tour `show_esg_results`) |
| `/carbon` | `pages/carbon/index.vue` | Bilan carbone |
| `/carbon/results` | `pages/carbon/results.vue` | Dashboard émissions + plan de réduction (tour `show_carbon_results`) |
| `/credit-score` | `pages/credit-score/index.vue` | Score crédit vert (tour `show_credit_score`) |
| `/financing` | `pages/financing/index.vue` | Catalogue fonds verts (tour `show_financing_catalog`) |
| `/financing/[id]` | `pages/financing/[id].vue` | Fiche fonds + matching |
| `/applications` | `pages/applications/index.vue` | Liste dossiers de financement |
| `/applications/[id]` | `pages/applications/[id].vue` | Rédaction dossier |
| `/action-plan` | `pages/action-plan/index.vue` | Timeline 6/12/24 mois + badges (tour `show_action_plan`) |
| `/reports` | `pages/reports/index.vue` | Rapports ESG PDF |

### Composants (60, groupés par dossier)

Inventaire détaillé : [component-inventory-frontend.md](./component-inventory-frontend.md). Groupes principaux :

- **`copilot/`** — Widget chat flottant (spec 019) : `FloatingChatWidget`, `FloatingChatButton`, `ChatWidgetHeader`, `ConnectionStatusBadge`, `GuidedTourPopover`.
- **`chat/`** — Messages + widgets interactifs (spec 018) : 11 composants dont les 5 du système Q&A (`InteractiveQuestionHost`, `SingleChoiceWidget`, `MultipleChoiceWidget`, `JustificationField`, `AnswerElsewhereButton`) + `ToolCallIndicator` (spec 012).
- **`richblocks/`** — Blocs visuels streamés (8) : Chart, Mermaid, Gauge, Progress, Table, Timeline + BlockError / BlockPlaceholder.
- **Domaine** — `esg/`, `credit/`, `financing/`, `applications/`, `action-plan/`, `dashboard/`, `documents/`, `profile/`.
- **Structurels** — `layout/` (`AppHeader`, `AppSidebar`), `ui/` (`ToastNotification`, `FullscreenModal`).

### Composables (18)

[frontend/app/composables/](../frontend/app/composables/) — logique réutilisable. Voir [component-inventory-frontend.md](./component-inventory-frontend.md#composables) pour la liste complète. Les trois composables à **state module-level** sont critiques pour la résilience inter-pages :

- `useAuth.ts` — `let refreshPromise: Promise<string> | null` garantit qu'une seule requête `/refresh` est en vol.
- `useChat.ts` — `conversations`, `currentMessages`, `abortController`, `reader` partagés entre composants. Permet au widget flottant de conserver le contexte pendant la navigation.
- `useGuidedTour.ts` — `tourState`, `currentTourId`, `guidanceStats` — une seule instance de tour driver.js active globalement.

### Stores Pinia (11)

[frontend/app/stores/](../frontend/app/stores/). Voir [component-inventory-frontend.md](./component-inventory-frontend.md#stores-pinia).

- `auth.ts` — `user`, tokens, `loadFromStorage()`.
- `ui.ts` — transverse : `theme`, `sidebarOpen`, `chatWidgetOpen`, `chatWidgetMinimized`, `currentPage` (spec 3), `guidedTourActive`, `prefersReducedMotion`, dimensions du widget.
- Un store par domaine métier pour les données récupérées de l'API.

### Middlewares (2, globaux)

- [auth.global.ts](../frontend/app/middleware/auth.global.ts) — bloque l'accès aux pages non publiques si `authStore.accessToken` absent. Charge depuis localStorage au premier passage.
- [chat-redirect.global.ts](../frontend/app/middleware/chat-redirect.global.ts) — redirige `/chat` (route obsolète depuis spec 019) vers `/?openChat=1`.

### Plugins (3, tous `client`)

- [gsap.client.ts](../frontend/app/plugins/gsap.client.ts) — register GSAP pour animations widget.
- [mermaid.client.ts](../frontend/app/plugins/mermaid.client.ts) — init Mermaid.
- [chartjs.client.ts](../frontend/app/plugins/chartjs.client.ts) — registerables Chart.js.

### Types (12 fichiers `.ts`)

Organisés par domaine. Notables :
- [guided-tour.ts](../frontend/app/types/guided-tour.ts) — `GuidedTourDefinition`, `GuidedTourStep`, `TourState`, `TourContext`.
- [interactive-question.ts](../frontend/app/types/interactive-question.ts) — 4 variantes de questions, payload de réponse, états.
- [richblocks.ts](../frontend/app/types/richblocks.ts) — types des blocs streamés.

### Librairie (`app/lib/`)

- [guided-tours/registry.ts](../frontend/app/lib/guided-tours/registry.ts) — registre de 6 tours.
- `guided-tours/definitions/` — définitions par tour (pas sous forme de fichier unique).

## 6. Systèmes transverses

### Dark mode

- Variables CSS dans [frontend/app/assets/css/main.css](../frontend/app/assets/css/main.css) via `@theme` : `--color-dark-card`, `--color-dark-bg`, `--color-dark-border`, `--color-dark-hover`, `--color-dark-input`, surfaces claires équivalentes, palette brand (green/blue/purple/orange/red).
- Activation : classe `dark` sur `<html>` pilotée par `useUiStore.toggleTheme()`.
- Persistance : `localStorage['esg-theme']`, fallback `prefers-color-scheme: dark`.
- Convention de code : chaque composant utilise les variantes `dark:` Tailwind (règle projet — voir [CLAUDE.md](../CLAUDE.md)).

### Tours guidés (driver.js)

- Lazy-load de driver.js pour ne pas peser sur le premier paint ([useDriverLoader.ts](../frontend/app/composables/useDriverLoader.ts)).
- Machine à états (`idle → loading → navigating → waiting_dom → highlighting → complete → idle`) encapsulée dans `useGuidedTour`.
- Multi-pages via `entryStep` et champ `route` par step.
- Countdown adaptatif basé sur `guidanceStats` (persisté localStorage, synchronisé entre onglets via `storage` event, cap 5 refus).
- Popover custom Vue monté par step : `GuidedTourPopover.vue`.
- Consentement obligatoire via widget interactif QCU yes/no avant chaque tour (détection heuristique côté frontend ; voir [integration-architecture.md](./integration-architecture.md#8-tours-guidés-spec-019)).

### Widgets interactifs chat

- 4 types : `qcu`, `qcm`, `qcu_justification`, `qcm_justification`.
- Hôte : [InteractiveQuestionHost.vue](../frontend/app/components/chat/InteractiveQuestionHost.vue). Instancie dynamiquement le bon composant selon `type`.
- Verrouille l'input texte tant qu'une question `pending` existe (invariant : une seule question pending par conversation).
- Bouton "Répondre autrement" → abandon (`state=abandoned`) + input texte libre.
- Justification bornée à 400 caractères (validation double côté client + serveur).
- ARIA roles complets : `radiogroup`, `checkbox`, `aria-checked`, `aria-describedby`.

### SSE resilience

- AbortController + `navigator.onLine` + classification d'erreurs (`abort`, `network`, `http`, `other`).
- Badge visuel `ConnectionStatusBadge.vue`.
- Bannière "Connexion perdue. Vérifiez votre réseau." en cas de rupture.

## 7. Tests

| Niveau | Outil | Localisation | Volume approximatif |
|---|---|---|---|
| Unitaire | Vitest + @vue/test-utils | `frontend/tests/components/`, `tests/composables/`, `tests/stores/`, `tests/pages/`, `tests/middleware/`, `tests/layouts/`, `tests/lib/` | ~37 fichiers |
| E2E mocké | Playwright | `frontend/tests/e2e/` (2 specs : `8-1-parcours-fatou`, `8-2-parcours-moussa`) | Backend mocké intégralement via `fixtures/mock-backend.ts` |
| E2E live | bash scripts | `frontend/tests/e2e-live/` (ex. `8-3-parcours-aminata.sh`) | Stack réelle (dépendances externes nécessaires) |

Configurations :
- [frontend/vitest.config.ts](../frontend/vitest.config.ts) — `happy-dom`, setup `tests/setup.ts`, plugin `nuxtImportMetaPlugin()` pour `import.meta.client/server`.
- [frontend/playwright.config.ts](../frontend/playwright.config.ts) — port 4321, workers=1, `reducedMotion: 'reduce'` par défaut, trace sur retry, screenshots + video on failure.

## 8. Build & déploiement

- **Dev** : `npm run dev` (HMR, port 3000).
- **Build SSR** : `npm run build` → `.output/` (exécuté dans `Dockerfile.prod`).
- **Image prod** : Nuxt SSR exposé sur port 3000 (127.0.0.1:3010 via `docker-compose.prod.yml`). Consommé par nginx UAfricas.
- Env build-time : `NUXT_PUBLIC_API_BASE`.

## 9. Décisions architecturales notables (ADRs implicites)

| Décision | Ref spec | Justification |
|---|---|---|
| Widget chat flottant au lieu de page dédiée | 019 | Accès au copilote sur toutes les pages, contexte page envoyé au backend, réduction de la friction UX |
| Fetch streaming (pas EventSource) pour SSE | — | Besoin de poster du FormData + Authorization ; EventSource ne supporte que GET |
| State module-level pour useChat / useAuth / useGuidedTour | 019, 7-2 | Survit à la navigation, garantit le single-flight, évite les races |
| Lazy-load driver.js | ADR7 (spec 4-1) | Ne pas pénaliser le TTI des utilisateurs qui ne prennent aucun tour |
| Popover custom Vue au lieu du popover natif driver.js | spec 5-4 | Contrôle total UI/UX, intégration dark mode, accessibilité |
| Marker SSE HTML-commentaire | 018, 019 | Passe le canal token sans ajouter de type SSE distinct côté transport |
| `reducedMotion: 'reduce'` par défaut en E2E | — | Déterminisme des tests Playwright |

## 10. Dette technique et axes d'amélioration

Voir [technical-debt-backlog.md](./technical-debt-backlog.md). Principaux points côté frontend :
- Absence de lint dédié JS/TS au-delà de `tsc`.
- Couverture E2E encore partielle (3 parcours, plusieurs modules non couverts par des scénarios live).
- Pas de i18n — tout est en français en dur. L'extraction sera nécessaire pour scaler à d'autres langues africaines.
- Les blocs `richblocks/` n'ont pas de test unitaire dédié pour les cas d'erreur (décision assumée : surface minimale `BlockError.vue`).
