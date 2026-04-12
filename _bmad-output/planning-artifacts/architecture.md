---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
lastStep: 8
status: 'complete'
completedAt: '2026-04-12'
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/product-brief-esg-mefali-copilot.md
  - docs/architecture-frontend.md
  - docs/architecture-backend.md
  - docs/integration-architecture.md
  - docs/data-models-backend.md
  - CLAUDE.md
workflowType: 'architecture'
project_name: 'esg_mefali'
user_name: 'Angenor'
date: '2026-04-12'
featureId: '019-floating-copilot-guided-nav'
---

# Document de Décisions Architecturales — ESG Mefali Copilot

_Ce document se construit collaborativement à travers une découverte étape par étape. Les sections sont ajoutées au fur et à mesure des décisions architecturales._

## Analyse du contexte projet

### Vue d'ensemble des exigences

**Exigences fonctionnelles (35 FR) :**

| Catégorie | FRs | Implications architecturales |
|---|---|---|
| Widget de chat flottant | FR1-FR10 | Composant `position: fixed` dans le layout, réutilisation des 13 composants chat existants, glassmorphism + fallback, redimensionnement, historique conversations |
| Conscience contextuelle | FR11-FR13 | Transmission de la route courante au LLM via le state LangGraph, adaptation des prompts |
| Consentement et déclenchement | FR14-FR17 | Réutilisation du widget interactif 018 (SingleChoiceWidget), fréquence adaptative côté frontend |
| Navigation guidée Driver.js | FR18-FR25 | Intégration librairie tierce DOM, orchestration cross-routes, décompteur multi-pages, retry éléments manquants |
| Registre de parcours | FR26-FR28 | Registre extensible de parcours pré-définis, mapping identifiant → configuration Driver.js |
| Détection mobile + résilience | FR29-FR35 | Breakpoint 1024px, fallback gracieux, SSE cross-routes, renouvellement JWT transparent |

**Exigences non-fonctionnelles (24 NFR) :**

| Catégorie | NFRs | Contraintes architecturales |
|---|---|---|
| Performance | NFR1-NFR7 | Widget < 300ms, Driver.js lazy < 500ms, popover < 200ms, 0 Ko bundle initial Driver.js, < 5 MB mémoire widget, blur sans chute FPS < 30, SSE sans reconnexion |
| Sécurité | NFR8-NFR11 | Blur ≥ 12px confidentialité, renouvellement JWT transparent, aucune donnée sensible dans les identifiants de parcours |
| Accessibilité | NFR12-NFR15 | WCAG AA contraste 4.5:1, navigation clavier + Tab + Escape, prefers-reduced-motion, aria-live |
| Fiabilité réseau | NFR16-NFR19 | Tolérance latence 5s/timeout 10s, guidage continue hors-ligne (frontend-only), retry 3×500ms éléments DOM, zéro régression 935 tests |
| Intégration existant | NFR20-NFR24 | Compat feature 018 (widgets interactifs), pattern tool calling 012, active_module 013, dark mode, conventions code |

### Échelle et complexité

- **Domaine principal** : Full-stack (backend LangGraph + frontend Nuxt 4)
- **Niveau de complexité** : Élevé
- **Composants architecturaux estimés** : ~15 nouveaux fichiers (5 composants Vue, 3 composables, 1 store extension, 1 type, 1 registre parcours, 1 tool LangChain, 1 prompt, 1 migration potentielle, 1 plugin)

### Contraintes techniques et dépendances

1. **Stack existante figée** — Nuxt 4 (compatibilityVersion 4), Vue 3 Composition API, Pinia 3, TailwindCSS 4, GSAP, FastAPI, LangGraph ≥ 0.2, LangChain ≥ 0.3
2. **Pattern SSE existant** — Format `data: {JSON}\n\n` via `ReadableStream`, 12 types d'events déjà définis
3. **Marker SSE pour tools spéciaux** — Pattern `<!--SSE:{...}-->` détecté dans `stream_graph_events` (précédent : `__sse_interactive_question__`)
4. **Layout unique** — `layouts/default.vue` contient déjà `AppSidebar`, `AppHeader`, `ChatPanel`. Le widget remplacera `ChatPanel`
5. **Convention composants** — `pathPrefix: false`, PascalCase, auto-import Nuxt
6. **Dark mode** — Classe `.dark` sur `<html>`, variables CSS dans `main.css`, variantes Tailwind obligatoires
7. **Driver.js** — Dépendance externe nouvelle, doit être lazy-loadée, manipule le DOM directement

### Préoccupations transversales identifiées

1. **Cycle de vie SSE cross-routes** — La connexion SSE doit survivre aux navigations Nuxt. Actuellement liée au composable `useChat` qui est monté dans les pages. Doit être hoisté au niveau du layout.
2. **Orchestration DOM : Vue vs Driver.js** — Driver.js ajoute des overlays, manipule les z-index, pointe des éléments. Vue gère le DOM virtuellement. Les transitions de page détruisent/recréent les nœuds DOM. Synchronisation critique.
3. **État partagé widget/guidage** — Le store `ui` Pinia doit orchestrer : widget ouvert/fermé/rétracté, guidage actif/inactif, page courante. Plusieurs machines à états imbriquées.
4. **Animations concurrentes** — GSAP anime le widget (ouverture/fermeture/rétraction), Driver.js anime ses overlays/popovers. Les deux touchent le DOM simultanément pendant les transitions guidage.
5. **Lazy loading et timing** — Driver.js chargé dynamiquement au premier guidage. Le CSS Driver.js aussi. Impact sur le timing du premier parcours (budget < 500ms).
6. **Accessibilité multi-couche** — Le widget est un composant `aria-live` avec trap focus. Les popovers Driver.js doivent aussi être accessibles. Coexistence des deux systèmes d'accessibilité.

## Évaluation du starter / Fondation technique

### Domaine technique principal

Full-stack brownfield — Nuxt 4 (frontend) + FastAPI (backend) + LangGraph (orchestration IA)

### Contexte : projet brownfield mature

**Aucun starter template n'est applicable.** Le projet a 18 features livrées, 935+ tests, 56 composants, 14 composables, 11 stores Pinia. Toutes les décisions techniques de fondation sont prises et validées en production.

### Stack existante (fondation de la feature 019)

**Frontend :**
- Nuxt 4 (compatibilityVersion 4, structure `app/`)
- Vue 3 Composition API (`<script setup lang="ts">`)
- TypeScript 5.x (strict)
- Pinia 3 (state management)
- TailwindCSS 4 (dark mode via variant custom `@custom-variant dark`)
- GSAP 3.12 (animations)
- Chart.js 4.4 + vue-chartjs 5.3
- Mermaid 11.4
- Vitest 3.0 (tests unitaires), Playwright 1.49 (E2E)

**Backend :**
- Python 3.12 + FastAPI ≥ 0.115
- LangGraph ≥ 0.2 + LangChain ≥ 0.3 + langchain-openai ≥ 0.3
- SQLAlchemy 2.x async + asyncpg
- PostgreSQL 16 + pgvector
- Alembic (13 migrations)
- Claude Sonnet 4 via OpenRouter

**Nouvelle dépendance à introduire :**
- **Driver.js** — librairie de navigation guidée (highlighting d'éléments DOM avec popovers). Chargée en lazy loading (import dynamique). Pas de dépendance transitive lourde.

### Décisions architecturales héritées de la stack existante

| Aspect | Décision déjà prise | Impact sur la feature 019 |
|---|---|---|
| Routing | Nuxt file-based routing, `pages/` | Le widget vit dans le layout, pas dans les pages |
| State management | Pinia stores dans `stores/` | Extension du store `ui` pour l'état du widget/guidage |
| Streaming IA | SSE via `ReadableStream` dans `useChat` | Réutilisation et hoisting au niveau layout |
| Tool calling | Pattern `graph/tools/` + marker SSE | Nouveau tool `trigger_guided_tour` suit le pattern |
| Composants chat | 13 composants dans `components/chat/` | Réutilisés tels quels dans le widget flottant |
| Dark mode | Classe `.dark` + variables CSS + variantes Tailwind | Appliqué à tous les nouveaux composants |
| Animations | GSAP injecté via plugin `gsap.client.ts` | Réutilisé pour les animations du widget |
| Tests | pytest + pytest-asyncio (backend), Vitest (frontend) | Nouveaux tests dans les mêmes suites |

## Décisions architecturales fondamentales

### Analyse de priorité des décisions

**Décisions critiques (bloquent l'implémentation) :**

1. Persistance de l'état chat cross-routes (hoisting `useChat`)
2. Connexion SSE unique maintenue à travers les navigations
3. Intégration Driver.js avec le cycle de vie Vue/Nuxt
4. Design du tool LangChain `trigger_guided_tour` + marker SSE

**Décisions importantes (structurent l'architecture) :**

5. Registre `data-guide-target` et enregistrement dynamique des composants
6. Orchestration rétraction/réapparition animée du widget (GSAP + Driver.js)
7. Lazy loading de Driver.js (impact bundle et timing)

**Décisions reportées (post-MVP) :**

- Analytics des parcours guidés
- Fréquence adaptative avancée (ML-based)
- Support mobile du widget

---

### Décision 1 — Persistance de l'état chat cross-routes

**Problème :** `useChat` est aujourd'hui un composable appelé dans les pages. Quand la page `/chat` ou le composant `ChatPanel` unmount lors d'une navigation Nuxt, l'état réactif (messages, conversations, connexion SSE) est perdu.

**Décision : Pattern singleton via module-level state**

```
composables/useChat.ts
├── État réactif déclaré au NIVEAU MODULE (hors de la fonction composable)
│   ├── const messages = ref<Message[]>([])
│   ├── const conversations = ref<Conversation[]>([])
│   ├── const currentConversationId = ref<string | null>(null)
│   ├── const isStreaming = ref(false)
│   └── const sseReader = ref<ReadableStreamDefaultReader | null>(null)
│
└── export function useChat() { ... }   // retourne les refs partagées + méthodes
```

**Justification :**
- Les `ref()` déclarées au niveau module persistent tant que le module JS est chargé — indépendamment du cycle de vie des composants Vue
- Le composable `useChat()` retourne toujours les mêmes références réactives
- Pas besoin de Pinia pour cet état : le state SSE/streaming est trop couplé au composable pour être découplé dans un store
- Le layout `default.vue` appelle `useChat()` une seule fois au mount — les pages n'ont plus besoin de le rappeler
- Pattern déjà validé dans l'écosystème Vue 3 (cf. VueUse `createSharedComposable`)

**Cycle de vie :**
- **Création** : au premier appel de `useChat()` dans le layout (module importé)
- **Maintien** : l'état persiste tant que l'application Nuxt est vivante (SPA)
- **Destruction** : uniquement au refresh complet de la page ou logout

**Impact :**
- `ChatPanel` actuel et la page `/chat` doivent être refactorés pour ne plus gérer l'état chat localement
- Le nouveau `FloatingChatWidget` dans le layout consomme `useChat()` comme unique point d'entrée

---

### Décision 2 — Connexion SSE unique cross-routes

**Problème :** La connexion SSE (ReadableStream) est aujourd'hui créée à chaque `sendMessage()` et lue jusqu'à `done`. Si l'utilisateur navigue pendant le streaming, le reader est garbage collected.

**Décision : Connexion SSE par message, pas persistante — mais le reader survit aux navigations**

```
┌─────────────────────────────────────────────────────┐
│  layout/default.vue                                  │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │  FloatingChatWidget                              │ │
│  │  └─ useChat() ← module-level state              │ │
│  │     └─ sseReader (ref)                           │ │
│  │        - Créé à chaque sendMessage()             │ │
│  │        - Lu dans une boucle async                │ │
│  │        - La ref persiste cross-routes            │ │
│  │        - AbortController pour annulation propre  │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │  <NuxtPage />  (change à chaque navigation)     │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

**Justification :**
- Le pattern SSE actuel est **POST-based** (pas EventSource), donc chaque message crée une nouvelle requête fetch → un nouveau ReadableStream
- Le reader est stocké dans une `ref()` module-level (Décision 1), donc il n'est pas garbage collected quand une page unmount
- La boucle `while(true) { reader.read() }` est une Promise async qui continue indépendamment du DOM
- Pas besoin de refactorer en EventSource persistent (ce qui casserait le pattern POST multipart existant)

**Gestion des cas limites :**
- **Navigation pendant streaming** : le reader continue, les tokens arrivent, les `ref()` sont mises à jour, le widget affiche en temps réel
- **AbortController** : stocké en module-level ref, permet d'annuler proprement un stream en cours
- **Indicateur de reconnexion** : `isConnected` ref basé sur l'état du dernier fetch (pas de heartbeat — post-based)

---

### Décision 3 — Intégration Driver.js avec le cycle de vie Vue/Nuxt

**Problème :** Driver.js manipule le DOM directement (overlays, z-index, classes CSS). Vue/Nuxt gère le DOM virtuellement. Les navigations détruisent/recréent des composants et leurs nœuds DOM.

**Décision : Composable `useGuidedTour` comme orchestrateur avec machine à états**

```
composables/useGuidedTour.ts
│
├── État machine (module-level) :
│   idle → loading → ready → navigating → waiting_dom → highlighting → complete
│                                  │              │
│                                  └──── interrupted (user cancel)
│
├── startTour(tourId: string, context?: TourContext)
│   1. Charge Driver.js (lazy, cf. Décision 7)
│   2. Résout le parcours depuis le registre (cf. Décision 5)
│   3. Rétracte le widget (cf. Décision 6)
│   4. Exécute les étapes séquentiellement
│
├── Gestion navigation cross-pages :
│   - Si étape.route !== currentRoute :
│     a. État → navigating
│     b. router.push(étape.route)
│     c. watch(route, () => { état → waiting_dom })
│     d. Attente DOM stable (nextTick + polling élément cible)
│     e. État → highlighting
│     f. driver.highlight(étape)
│
├── Retry pattern pour éléments manquants :
│   - waitForElement(selector, { maxRetries: 3, interval: 500 })
│   - Si échec après 3 tentatives : skip étape + message chat
│
├── Décompteur multi-pages :
│   - Affiché dans le popover Driver.js (pas dans le chat)
│   - Configurable par étape (défaut 8s)
│   - À expiration : navigation automatique via router.push()
│
└── Cleanup :
    - driver.destroy() à la fin du parcours ou sur interruption
    - Réapparition du widget (cf. Décision 6)
    - État → idle
```

**Synchronisation DOM post-navigation :**

```ts
async function waitForElement(selector: string): Promise<HTMLElement | null> {
  await nextTick()
  for (let i = 0; i < 3; i++) {
    const el = document.querySelector(selector)
    if (el) return el
    await new Promise(r => setTimeout(r, 500))
  }
  return null
}
```

**Timeout global page :**
- Si la page ne charge pas en 5s → retry silencieux
- Si > 10s → abandon du parcours + message d'erreur dans le chat via `useChat().addSystemMessage()`

---

### Décision 4 — Tool LangChain `trigger_guided_tour` + marker SSE

**Problème :** Le LLM doit pouvoir déclencher un parcours guidé côté frontend. Le mécanisme existant pour les widgets interactifs (feature 018) utilise un marker SSE dans le contenu du message.

**Décision : Nouveau marker SSE `__sse_guided_tour__` + event SSE dédié `guided_tour`**

**Backend — Tool LangChain :**

```python
# graph/tools/guided_tour_tools.py

@tool
def trigger_guided_tour(
    tour_id: str,
    context: dict | None = None
) -> str:
    """Déclenche un parcours de navigation guidée côté frontend.
    
    Args:
        tour_id: Identifiant du parcours pré-défini (ex: 'show_carbon_results')
        context: Contexte optionnel pour personnaliser les textes (ex: {'score': 58})
    """
    marker = json.dumps({
        "__sse_guided_tour__": True,
        "tour_id": tour_id,
        "context": context or {}
    })
    return f"<!--SSE:{marker}-->"
```

**Backend — Détection dans `stream_graph_events` :**

```python
if "__sse_guided_tour__" in content:
    payload = extract_sse_marker(content, "__sse_guided_tour__")
    yield f"data: {json.dumps({'event': 'guided_tour', **payload})}\n\n"
```

**Frontend — Parsing dans `useChat` :**

```ts
case 'guided_tour':
  const { tour_id, context } = eventData
  useGuidedTour().startTour(tour_id, context)
  break
```

**Nœuds LangGraph autorisés à déclencher un guidage :**

| Nœud | Peut trigger ? | Cas d'usage |
|---|---|---|
| `chat_node` | **Oui** | Demande explicite utilisateur ("montre-moi...") |
| `esg_scoring_node` | **Oui** | Fin d'évaluation ESG → guider vers résultats |
| `carbon_node` | **Oui** | Fin de bilan carbone → guider vers résultats |
| `financing_node` | **Oui** | Matching terminé → guider vers fonds |
| `credit_node` | **Oui** | Score calculé → guider vers page crédit |
| `action_plan_node` | **Oui** | Plan généré → guider vers timeline |
| `application_node` | Non | Processus en cours, pas de page de résultats |
| `document_node` | Non | L'analyse reste dans le chat |
| `profiling_node` | Non | Le profil se remplit dans le chat |
| `router_node` | Non | Pur routage, pas de logique métier |

**Injection dans les prompts :**

```python
# prompts/guided_tour.py
GUIDED_TOUR_INSTRUCTION = """
## NAVIGATION GUIDÉE
Tu disposes d'un outil `trigger_guided_tour` qui permet de montrer visuellement 
à l'utilisateur les éléments pertinents de l'interface.

PARCOURS DISPONIBLES :
- show_esg_results : Résultats ESG (score, forces/faiblesses, recommandations)
- show_carbon_results : Résultats empreinte carbone (donut, benchmark, plan réduction)
- show_financing_catalog : Catalogue des fonds de financement
- show_credit_score : Score crédit vert
- show_action_plan : Plan d'action et timeline
- show_dashboard_overview : Vue d'ensemble du tableau de bord

RÈGLES :
- Propose le guidage UNIQUEMENT après la complétion d'un module ou sur demande explicite
- Utilise d'abord ask_interactive_question pour obtenir le consentement (sauf demande explicite)
- Le tour_id doit correspondre exactement à un parcours du registre
- Le context peut contenir des données pour personnaliser les textes des popovers
"""
```

**Sécurité :** Le `tour_id` est un identifiant opaque (string alphanumérique). Aucune donnée sensible (scores, montants, IDs) ne transite dans le marker. Le `context` est optionnel et ne contient que des données de personnalisation des textes.

---

### Décision 5 — Registre `data-guide-target` et parcours pré-définis

**Problème :** Driver.js a besoin de sélecteurs CSS pour pointer les éléments. Les éléments dynamiques (listes, résultats async) n'existent pas au moment de la définition des parcours.

**Décision : Double système — attributs `data-guide-target` sur les composants + registre de parcours dans un fichier de configuration**

**A. Convention `data-guide-target` :**

```
Format : [module]-[element]
Exemples :
  data-guide-target="sidebar-esg-link"
  data-guide-target="esg-score-circle"
  data-guide-target="esg-strengths-badges"
  data-guide-target="carbon-donut-chart"
  data-guide-target="carbon-benchmark"
  data-guide-target="carbon-reduction-plan"
  data-guide-target="financing-fund-list"
  data-guide-target="credit-score-gauge"
  data-guide-target="action-plan-timeline"
  data-guide-target="dashboard-esg-card"
```

**Application directe dans les templates Vue (pas de composable) :**

```vue
<!-- components/esg/ScoreCircle.vue -->
<div data-guide-target="esg-score-circle" class="...">
  <!-- contenu du cercle de score -->
</div>
```

**Justification :** Pas besoin d'un composable `useGuideTarget` — un simple attribut HTML statique suffit. Les éléments existent dans le DOM quand la page est montée. Le pattern `waitForElement` (Décision 3) gère le cas où les données async ne sont pas encore chargées.

**B. Registre de parcours :**

```ts
// lib/guided-tours/registry.ts

import type { GuidedTourDefinition } from '~/types/guided-tour'

export const tourRegistry: Record<string, GuidedTourDefinition> = {
  show_carbon_results: {
    id: 'show_carbon_results',
    steps: [
      {
        route: '/carbon/results',
        selector: '[data-guide-target="carbon-donut-chart"]',
        popover: {
          title: 'Répartition de vos émissions',
          description: 'Ce graphique montre la répartition de votre empreinte carbone par catégorie.',
          side: 'bottom',
        },
      },
      {
        selector: '[data-guide-target="carbon-benchmark"]',
        popover: {
          title: 'Comparaison sectorielle',
          description: 'Votre position par rapport à la moyenne de votre secteur.',
          side: 'right',
        },
      },
      {
        selector: '[data-guide-target="carbon-reduction-plan"]',
        popover: {
          title: 'Plan de réduction',
          description: 'Les actions recommandées pour réduire votre empreinte.',
          side: 'top',
        },
      },
    ],
    entryStep: {
      selector: '[data-guide-target="sidebar-carbon-link"]',
      popover: {
        title: 'Résultats Empreinte Carbone',
        description: 'Cliquez ici pour voir vos résultats détaillés.',
        countdown: 8,
      },
      targetRoute: '/carbon/results',
    },
  },
}
```

**Extensibilité :** Ajouter un parcours = ajouter une entrée dans `tourRegistry` + des attributs `data-guide-target` sur les composants cibles. Zéro modification du moteur de guidage.

**Personnalisation dynamique par le LLM :**
Le `context` envoyé par le tool permet de personnaliser les textes. Le registre définit des templates avec placeholders :

```ts
description: 'Votre empreinte est de {{total_tco2}} tCO2e, dont {{top_category_pct}}% liés au {{top_category}}.',
```

Le composable `useGuidedTour` interpole les valeurs du `context` avant de passer à Driver.js.

---

### Décision 6 — Orchestration rétraction/réapparition du widget (GSAP + Driver.js)

**Problème :** Le widget doit se rétracter pendant le guidage pour ne pas masquer les éléments pointés. GSAP et Driver.js touchent tous les deux le DOM.

**Décision : Machine à états dans le store `ui` + séquence GSAP → Driver.js avec promesses**

**Extension du store `ui` :**

```ts
// stores/ui.ts — nouveaux champs
chatWidgetOpen: boolean       // true = widget visible et étendu
chatWidgetMinimized: boolean  // true = rétracté en bouton pendant guidage
guidedTourActive: boolean     // true = parcours Driver.js en cours
currentPage: string           // route.path courante, envoyée au LLM
```

**Séquence d'orchestration :**

```
1. Event SSE 'guided_tour' reçu
   │
2. useGuidedTour.startTour(tourId)
   │
3. uiStore.guidedTourActive = true
   uiStore.chatWidgetMinimized = true
   │
4. GSAP anime le widget → bouton flottant réduit
   (scale: 1→0.3, opacity: 1→0.8, durée: 250ms)
   │
5. Attente fin animation GSAP (onComplete callback ou Promise)
   │
6. Driver.js démarre le parcours
   │   ├─ Étapes sur la page courante
   │   ├─ Navigation si nécessaire (Décision 3)
   │   └─ Décompteur sur les étapes de navigation
   │
7. Parcours terminé OU utilisateur interrompt
   │
8. driver.destroy()
   │
9. GSAP anime le widget → réapparition
   (scale: 0.3→1, opacity: 0.8→1, durée: 250ms)
   │
10. uiStore.chatWidgetMinimized = false
    uiStore.guidedTourActive = false
    │
11. Message de conclusion dans le chat (optionnel, via le LLM)
```

**Gestion de l'interruption utilisateur :**
- L'utilisateur clique hors zone ou appuie Escape → Driver.js callback `onDestroyStarted`
- Appel immédiat des étapes 8-10 (cleanup + réapparition widget)
- Un message dans le chat confirme l'interruption

**prefers-reduced-motion :**
- Si actif, les animations GSAP sont remplacées par des transitions instantanées (durée 0ms)
- Driver.js `animate: false` est passé dans la config

---

### Décision 7 — Lazy loading de Driver.js

**Problème :** Driver.js (~15 Ko gzipped) ne doit pas être inclus dans le bundle initial. Le premier parcours doit démarrer en < 500ms.

**Décision : Import dynamique avec pré-chargement opportuniste + CSS inclus dans main.css**

```ts
// composables/useGuidedTour.ts

let driverModule: typeof import('driver.js') | null = null

export function prefetchDriverJs() {
  if (driverModule) return
  requestIdleCallback(() => {
    import('driver.js').then(m => { driverModule = m })
  })
}

async function loadDriver(): Promise<typeof import('driver.js')> {
  if (!driverModule) {
    driverModule = await import('driver.js')
  }
  return driverModule
}
```

**Timing :**
- Le `FloatingChatWidget` appelle `prefetchDriverJs()` dans son `onMounted()` via `requestIdleCallback`
- Sur les connexions rapides : Driver.js est déjà en cache quand le premier guidage arrive
- Sur les connexions lentes : le `loadDriver()` attend le chargement (inclus dans le budget 500ms)

**CSS Driver.js :**
- Inclus dans `main.css` via `@import 'driver.js/dist/driver.css'` — ~2 Ko, acceptable
- Les overrides dark mode sont ajoutés dans le même fichier

**Overrides CSS Driver.js pour dark mode :**

```css
.driver-popover {
  @apply bg-white text-surface-text border border-gray-200 rounded-lg shadow-xl;
}
.dark .driver-popover {
  @apply bg-dark-card text-surface-dark-text border-dark-border;
}
```

---

### Analyse d'impact des décisions

**Séquence d'implémentation recommandée :**

1. **Décision 1** (module-level state `useChat`) — Fondation, tout en dépend
2. **Décision 2** (SSE cross-routes) — Découle de 1, validation que le streaming survit
3. **Widget flottant** — Nouveau composant dans le layout utilisant `useChat()`
4. **Décision 7** (lazy loading Driver.js) — Installation dépendance, CSS, prefetch
5. **Décision 5** (registre parcours + `data-guide-target`) — Structure des données de guidage
6. **Décision 3** (composable `useGuidedTour`) — Moteur de guidage
7. **Décision 6** (orchestration animations) — Lien widget ↔ guidage
8. **Décision 4** (tool LangChain backend) — Déclenchement par le LLM

**Dépendances croisées :**

```
Décision 1 (state) ──► Décision 2 (SSE) ──► Widget flottant
                                                    │
Décision 7 (lazy) ──► Décision 5 (registre) ──► Décision 3 (moteur)
                                                    │
                                              Décision 6 (animations)
                                                    │
                                              Décision 4 (tool backend)
```

## Patterns d'implémentation et règles de consistance

### Points de conflit potentiels identifiés

14 zones où un agent IA pourrait diverger lors de l'implémentation de la feature 019.

### Patterns de nommage

**Nouveaux composants Vue :**

| Composant | Fichier | Usage |
|---|---|---|
| `FloatingChatWidget` | `components/copilot/FloatingChatWidget.vue` | Widget principal, monté dans le layout |
| `FloatingChatButton` | `components/copilot/FloatingChatButton.vue` | Bouton FAB en bas à droite |
| `ChatWidgetHeader` | `components/copilot/ChatWidgetHeader.vue` | Barre titre du widget (réduire, historique) |
| `GuidedTourPopover` | `components/copilot/GuidedTourPopover.vue` | Wrapper custom popover Driver.js avec décompteur |
| `CountdownBadge` | `components/copilot/CountdownBadge.vue` | Badge décompteur dans les popovers |

**Règle :** Nouveau dossier `components/copilot/` — **pas** dans `components/chat/` (les composants chat existants restent inchangés et sont réutilisés par composition, pas par modification).

**Nouveaux composables :**

| Composable | Fichier | Rôle |
|---|---|---|
| `useGuidedTour` | `composables/useGuidedTour.ts` | Orchestrateur machine à états des parcours |
| `useDeviceDetection` | `composables/useDeviceDetection.ts` | Détection desktop/mobile (breakpoint 1024px) |

**Règle :** `useChat.ts` existant est **modifié** (module-level state), pas remplacé. Aucun nouveau composable chat.

**Nouveaux types :**

```ts
// types/guided-tour.ts
export interface GuidedTourStep { ... }
export interface GuidedTourDefinition { ... }
export interface TourContext { ... }
export type TourState = 'idle' | 'loading' | 'ready' | 'navigating' | 'waiting_dom' | 'highlighting' | 'complete' | 'interrupted'
```

**Registre de parcours :**

```
lib/guided-tours/registry.ts      // Registre principal
lib/guided-tours/tours/            // Un fichier par parcours (optionnel si le registre grandit)
```

**Convention d'identifiants de parcours :** `show_[module]_[page]` en snake_case
- `show_esg_results`, `show_carbon_results`, `show_financing_catalog`, `show_credit_score`, `show_action_plan`, `show_dashboard_overview`

**Convention `data-guide-target` :** `[module]-[element]` en kebab-case
- Exemples : `esg-score-circle`, `carbon-donut-chart`, `sidebar-esg-link`

### Patterns structurels

**Fichiers backend :**

| Fichier | Emplacement | Pattern existant suivi |
|---|---|---|
| `guided_tour_tools.py` | `graph/tools/` | Identique aux 12 fichiers existants |
| `guided_tour.py` | `prompts/` | Identique aux 9 prompts existants |

**Pas de nouveau router, service, ou modèle backend.** Le tool émet un marker SSE, `stream_graph_events` le détecte — zéro endpoint REST nouveau.

**Tests :**

| Test | Emplacement |
|---|---|
| Backend : tool `trigger_guided_tour` | `tests/test_tools/test_guided_tour_tools.py` |
| Backend : prompt guided_tour | `tests/test_prompts/test_guided_tour_prompt.py` |
| Backend : détection marker SSE | `tests/test_graph/test_stream_guided_tour.py` |
| Frontend : `useGuidedTour` | `tests/composables/useGuidedTour.test.ts` |
| Frontend : `FloatingChatWidget` | `tests/components/FloatingChatWidget.test.ts` |
| Frontend : registre parcours | `tests/lib/guided-tours/registry.test.ts` |

### Patterns de format

**Nouveau type d'event SSE :**

```json
{
  "event": "guided_tour",
  "tour_id": "show_carbon_results",
  "context": { "total_tco2": 47, "top_category": "transport" }
}
```

**Règle :** Suit exactement le format des events existants (`event` string + payload JSON plat). Pas d'enveloppe supplémentaire.

**Marker SSE :**

```
<!--SSE:{"__sse_guided_tour__":true,"tour_id":"show_carbon_results","context":{}}-->
```

**Règle :** Le marker est `__sse_guided_tour__` (double underscore, snake_case) — convention identique à `__sse_interactive_question__`.

### Patterns de communication

**Événements entre composables :**

```
useChat (event SSE 'guided_tour')
  └──► useGuidedTour.startTour(tourId, context)
         ├──► uiStore.guidedTourActive = true
         ├──► uiStore.chatWidgetMinimized = true
         └──► [parcours Driver.js]
                └──► uiStore.guidedTourActive = false
                     uiStore.chatWidgetMinimized = false
```

**Règle :** La communication passe par les stores Pinia (état observable) et les appels directs entre composables (pas d'EventBus, pas de provide/inject custom, pas de $emit global).

**Conscience contextuelle (page courante → LLM) :**

```ts
// Dans FloatingChatWidget ou le layout
const route = useRoute()
watch(() => route.path, (newPath) => {
  uiStore.currentPage = newPath
})

// Dans useChat.sendMessage() — ajout du champ current_page au FormData
formData.append('current_page', uiStore.currentPage)
```

**Backend :** Le champ `current_page` est ajouté au `ConversationState` et injecté dans les prompts système.

### Patterns de processus

**Gestion des erreurs guidage :**

| Situation | Comportement | Message chat |
|---|---|---|
| Élément DOM introuvable (3 retries échoués) | Skip l'étape, continue le parcours | « Je n'ai pas pu pointer cet élément. Passons à la suite. » |
| Page ne charge pas (> 10s) | Abandon du parcours | « La page met trop de temps à charger. Réessayez plus tard. » |
| Driver.js crash/erreur | Cleanup + réapparition widget | « Le guidage a rencontré un problème. Le chat est toujours disponible. » |
| Utilisateur interrompt (Escape/clic hors zone) | Cleanup propre | Aucun message (action volontaire) |

**Règle :** Les messages d'erreur sont en **français** avec un ton empathique (pas technique). Ils sont ajoutés via `useChat().addSystemMessage()` (nouvelle méthode — message local, pas envoyé au LLM).

**États de chargement :**

| État | Variable | Affichage |
|---|---|---|
| Widget ouvert | `uiStore.chatWidgetOpen` | Widget visible |
| Widget rétracté | `uiStore.chatWidgetMinimized` | Bouton FAB seul |
| Guidage en cours | `uiStore.guidedTourActive` | Overlay Driver.js |
| Driver.js en chargement | `tourState === 'loading'` | Spinner dans le bouton FAB |
| Streaming SSE | `isStreaming` (useChat) | Indicateur dans le widget |

### Règles d'enforcement

**Tout agent IA DOIT :**

1. Ne JAMAIS modifier les 13 composants existants dans `components/chat/` — les réutiliser par composition
2. Ne JAMAIS ajouter d'état chat dans un store Pinia — tout reste dans `useChat.ts` (module-level)
3. Toujours utiliser `[data-guide-target="xxx"]` comme sélecteur Driver.js, JAMAIS de classes CSS ou d'IDs
4. Toujours vérifier `uiStore.guidedTourActive` avant d'ouvrir le widget (ne pas ouvrir pendant un guidage)
5. Toujours respecter `prefers-reduced-motion` sur toute animation GSAP ou transition Driver.js
6. Ne JAMAIS transmettre de données sensibles (scores, montants, IDs utilisateur) dans le `tour_id` ou le marker SSE
7. Toujours ajouter les variantes `dark:` Tailwind sur chaque nouvel élément visuel
8. Messages d'erreur UX en français avec accents, ton empathique

### Anti-patterns à éviter

| Anti-pattern | Correct |
|---|---|
| `document.getElementById('esg-score')` | `document.querySelector('[data-guide-target="esg-score-circle"]')` |
| Stocker l'état du guidage dans le composant local | Utiliser `uiStore` (Pinia) |
| Créer un nouveau `EventSource` pour le guidage | Réutiliser le pattern POST + ReadableStream existant |
| `import driverJs from 'driver.js'` (top-level) | `const { driver } = await import('driver.js')` (lazy) |
| Modifier `ChatMessage.vue` pour le widget | Réutiliser `ChatMessage.vue` tel quel dans `FloatingChatWidget` |
| `@click="router.push(...)"` dans les popovers Driver.js | Utiliser le décompteur + `useGuidedTour` pour la navigation |

## Structure du projet et frontières — Feature 019

### Arborescence des fichiers nouveaux et modifiés

```
frontend/app/
├── layouts/
│   └── default.vue                          # MODIFIÉ — remplace ChatPanel par FloatingChatWidget
│
├── components/
│   ├── chat/                                # INCHANGÉ — 13 composants réutilisés tel quel
│   │   ├── ChatInput.vue
│   │   ├── ChatMessage.vue
│   │   ├── ConversationList.vue
│   │   ├── MessageParser.vue
│   │   ├── SingleChoiceWidget.vue
│   │   ├── MultipleChoiceWidget.vue
│   │   ├── InteractiveQuestionHost.vue
│   │   ├── JustificationField.vue
│   │   ├── ToolCallIndicator.vue
│   │   ├── ProfileNotification.vue
│   │   ├── AnswerElsewhereButton.vue
│   │   ├── WelcomeMessage.vue
│   │   └── InteractiveQuestionInputBar.vue
│   │
│   ├── copilot/                             # NOUVEAU — dossier dédié feature 019
│   │   ├── FloatingChatWidget.vue           # Widget principal glassmorphism
│   │   ├── FloatingChatButton.vue           # Bouton FAB bas-droite
│   │   ├── ChatWidgetHeader.vue             # Barre titre (réduire, historique, fermer)
│   │   ├── GuidedTourPopover.vue            # Popover custom Driver.js avec décompteur
│   │   └── CountdownBadge.vue               # Badge décompteur (8s par défaut)
│   │
│   ├── layout/
│   │   └── ChatPanel.vue                    # SUPPRIMÉ (remplacé par FloatingChatWidget)
│   │
│   └── [existants]                          # esg/, credit/, dashboard/, etc.
│       └── *.vue                            # MODIFIÉ — ajout data-guide-target sur ~15 composants
│
├── composables/
│   ├── useChat.ts                           # MODIFIÉ — module-level state + event 'guided_tour'
│   ├── useGuidedTour.ts                     # NOUVEAU — machine à états, orchestrateur parcours
│   └── useDeviceDetection.ts                # NOUVEAU — détection desktop/mobile (1024px)
│
├── stores/
│   └── ui.ts                                # MODIFIÉ — +4 champs widget/guidage
│
├── types/
│   └── guided-tour.ts                       # NOUVEAU — types du système de guidage
│
├── lib/
│   └── guided-tours/
│       └── registry.ts                      # NOUVEAU — tourRegistry avec 6 parcours
│
├── pages/
│   └── chat.vue                             # SUPPRIMÉ (migré dans le widget)
│
└── assets/css/
    └── main.css                             # MODIFIÉ — @import driver.js CSS + overrides dark


backend/app/
├── graph/tools/
│   └── guided_tour_tools.py                 # NOUVEAU — tool trigger_guided_tour
│
├── prompts/
│   └── guided_tour.py                       # NOUVEAU — GUIDED_TOUR_INSTRUCTION
│
├── graph/
│   ├── nodes.py                             # MODIFIÉ — injection tool dans 7 nœuds
│   └── state.py                             # MODIFIÉ — +current_page dans ConversationState
│
└── api/
    └── chat.py                              # MODIFIÉ — current_page + détection marker


tests/
├── backend/
│   ├── test_tools/test_guided_tour_tools.py        # NOUVEAU
│   ├── test_prompts/test_guided_tour_prompt.py     # NOUVEAU
│   └── test_graph/test_stream_guided_tour.py       # NOUVEAU
│
└── frontend/
    ├── components/FloatingChatWidget.test.ts       # NOUVEAU
    ├── composables/useGuidedTour.test.ts           # NOUVEAU
    ├── composables/useDeviceDetection.test.ts      # NOUVEAU
    └── lib/guided-tours/registry.test.ts           # NOUVEAU
```

### Frontières architecturales

**Frontière 1 — Widget ↔ Chat existant :**

```
FloatingChatWidget (nouveau)
  └── compose ──► ChatInput, ChatMessage, ConversationList, etc. (existants)
  └── appelle ──► useChat() (module-level state partagé)
```

Le widget est un **conteneur** qui compose les composants chat existants. Aucune logique chat n'est dupliquée. La frontière est claire : `components/copilot/` orchestre, `components/chat/` rend.

**Frontière 2 — Guidage ↔ Widget :**

```
useGuidedTour (composable)
  ├── lit    ──► uiStore (guidedTourActive, chatWidgetMinimized)
  ├── écrit  ──► uiStore (même champs)
  └── appelle ──► Driver.js (lazy loaded)

FloatingChatWidget (composant)
  └── observe ──► uiStore.chatWidgetMinimized (GSAP anime en réaction)
```

Communication unidirectionnelle via le store Pinia. Le guidage ne connaît pas le widget directement — il manipule l'état, le widget réagit.

**Frontière 3 — Frontend ↔ Backend (nouveau contrat) :**

```
Frontend                              Backend
─────────                             ─────────
useChat.sendMessage()     ──POST──►   chat.py (+ current_page dans FormData)
                          ◄──SSE───   stream_graph_events (+ event 'guided_tour')
```

Un seul nouveau champ dans le contrat : `current_page` (string). Un seul nouvel event SSE : `guided_tour`. Zéro endpoint REST nouveau.

**Frontière 4 — LLM ↔ Guidage :**

```
LLM (nœud LangGraph)
  └── appelle ──► trigger_guided_tour(tour_id, context)
                    └── retourne marker SSE
                          └── stream_graph_events détecte
                                └── émet event SSE 'guided_tour'
                                      └── useChat parse
                                            └── useGuidedTour.startTour()
```

Le LLM ne connaît que des identifiants de parcours. Il ne connaît ni Driver.js, ni les sélecteurs CSS, ni le DOM. Découplage total.

### Mapping exigences → fichiers

| Catégorie FR | Fichiers principaux |
|---|---|
| FR1-FR10 (Widget flottant) | `FloatingChatWidget.vue`, `FloatingChatButton.vue`, `ChatWidgetHeader.vue`, `useChat.ts`, `ui.ts`, `default.vue` |
| FR11-FR13 (Conscience contextuelle) | `ui.ts` (+currentPage), `chat.py` (+current_page), `state.py`, prompts |
| FR14-FR17 (Consentement) | `SingleChoiceWidget.vue` (réutilisé), `guided_tour.py` |
| FR18-FR25 (Navigation guidée) | `useGuidedTour.ts`, `GuidedTourPopover.vue`, `CountdownBadge.vue`, `registry.ts` |
| FR26-FR28 (Registre parcours) | `registry.ts`, `guided-tour.ts` (types) |
| FR29-FR30 (Détection mobile) | `useDeviceDetection.ts`, `FloatingChatWidget.vue` |
| FR31-FR35 (Résilience) | `useGuidedTour.ts` (retry, timeout), `useChat.ts` (AbortController) |

### Flux de données — Parcours guidé complet

```
1. Utilisateur complète bilan carbone via le chat
   │
2. carbon_node (LangGraph) décide de proposer un guidage
   │
3. LLM appelle ask_interactive_question("Voir vos résultats ?", ["Oui","Non"])
   │
4. Frontend affiche SingleChoiceWidget → utilisateur clique "Oui, montre-moi"
   │
5. Réponse → LLM appelle trigger_guided_tour("show_carbon_results", {total: 47})
   │
6. Backend émet marker SSE → stream_graph_events → event 'guided_tour'
   │
7. useChat parse → useGuidedTour.startTour("show_carbon_results", {total: 47})
   │
8. useGuidedTour :
   a. Charge Driver.js (lazy, déjà prefetched)
   b. Résout parcours depuis tourRegistry
   c. Rétracte widget (uiStore → GSAP)
   d. Si page courante ≠ /carbon/results :
      - entryStep sur sidebar-carbon-link avec décompteur 8s
      - Navigation auto ou clic → router.push('/carbon/results')
   e. waitForElement('[data-guide-target="carbon-donut-chart"]')
   f. Driver.js highlight étape par étape
   g. Fin → driver.destroy() → widget réapparaît
   │
9. Message de conclusion optionnel dans le chat
```

## Résultats de validation architecturale

### Validation de cohérence ✅

**Compatibilité des décisions :**
- Les 7 décisions forment une chaîne cohérente : module-level state (D1) → SSE survit (D2) → widget dans layout → Driver.js lazy (D7) → registre parcours (D5) → orchestrateur (D3) → animations (D6) → tool backend (D4)
- Aucune décision ne contredit une autre
- Le pattern SSE POST-based existant est préservé intact — la D2 s'appuie dessus sans le modifier
- GSAP (existant) et Driver.js (nouveau) ne se marchent pas dessus : séquence GSAP-d'abord puis Driver.js via promesses (D6)

**Consistance des patterns :**
- Nommage uniforme : snake_case pour les tour_ids, kebab-case pour les data-guide-target, PascalCase pour les composants Vue — cohérent avec les conventions existantes
- Le marker SSE `__sse_guided_tour__` suit exactement le pattern de `__sse_interactive_question__`
- Le tool `trigger_guided_tour` suit le pattern des ~100 tools existants dans `graph/tools/`
- Communication par stores Pinia — pas d'introduction de pattern alternatif

**Alignement structurel :**
- Le dossier `components/copilot/` isole les nouveaux composants sans toucher les existants
- Les composants chat existants sont composés, pas modifiés — frontière respectée
- Le backend n'a que 2 nouveaux fichiers (tool + prompt) — empreinte minimale

### Validation de couverture des exigences ✅

**Exigences fonctionnelles : 35/35 couvertes**

| FR | Couverture architecturale |
|---|---|
| FR1-FR10 | `FloatingChatWidget` + composants chat existants + `useChat` module-level + glassmorphism CSS |
| FR11-FR13 | `uiStore.currentPage` → `current_page` dans FormData → `ConversationState` → prompts |
| FR14-FR17 | `SingleChoiceWidget` (018) réutilisé + `GUIDED_TOUR_INSTRUCTION` |
| FR18-FR25 | `useGuidedTour` (machine à états, waitForElement, décompteur, navigation auto) |
| FR26-FR28 | `tourRegistry` extensible + types `GuidedTourDefinition` + interpolation templates |
| FR29-FR30 | `useDeviceDetection` (breakpoint 1024px) + `v-if` conditionnel |
| FR31-FR35 | Retry 3×500ms, timeout 10s, cleanup, AbortController, dark mode, SSE cross-routes |

**Exigences non-fonctionnelles : 24/24 couvertes**

| NFR | Couverture |
|---|---|
| NFR1-NFR7 (performance) | GSAP 250ms, prefetch idle, import dynamique 0 Ko, module-level state, backdrop-filter GPU |
| NFR8-NFR11 (sécurité) | Blur ≥ 12px, identifiants opaques, aucune donnée dans markers, auth existante |
| NFR12-NFR15 (accessibilité) | aria-live, Tab/Escape, prefers-reduced-motion, contraste WCAG AA |
| NFR16-NFR19 (résilience) | waitForElement retry, timeout 5s/10s, guidage frontend-only, zéro régression |
| NFR20-NFR24 (intégration) | Compat 018, pattern tool 012, pas de conflit active_module 013, dark mode |

### Analyse des lacunes

**Lacunes critiques : aucune** ✅

**Lacunes importantes (à adresser pendant l'implémentation) :**

1. **Refresh token pendant guidage multi-pages (FR32/NFR9)** — La logique de refresh token dans `useAuth` est documentée comme "à compléter" dans l'architecture existante. L'implémentation devra s'assurer que `apiFetch` intercepte les 401 et refresh automatiquement.

2. **Personnalisation des textes de popovers** — Le mécanisme d'interpolation `{{variable}}` est décrit mais la liste exacte des variables par parcours n'est pas formalisée. À définir lors de l'implémentation de chaque parcours.

3. **Fréquence adaptative des propositions de guidage (FR17)** — Le comptage des refus n'est pas détaillé. Recommandation : compteur côté frontend dans `useGuidedTour` (module-level), transmis au LLM dans le payload.

**Lacunes mineures (post-MVP) :**
- Analytics des parcours
- Tests E2E Playwright pour le flux complet guidage
- Documentation développeur pour ajouter un nouveau parcours

### Checklist de complétude architecturale

**✅ Analyse des exigences**
- [x] Contexte projet analysé en profondeur
- [x] Échelle et complexité évaluées
- [x] Contraintes techniques identifiées
- [x] Préoccupations transversales cartographiées

**✅ Décisions architecturales**
- [x] 7 décisions critiques documentées avec pseudo-code
- [x] Stack technologique spécifiée (brownfield, Driver.js ajouté)
- [x] Patterns d'intégration définis (SSE, markers, stores)
- [x] Considérations de performance adressées

**✅ Patterns d'implémentation**
- [x] Conventions de nommage établies
- [x] Patterns structurels définis
- [x] Patterns de communication spécifiés
- [x] Patterns de processus documentés
- [x] Anti-patterns identifiés

**✅ Structure du projet**
- [x] Arborescence complète des fichiers nouveaux/modifiés
- [x] Frontières de composants établies
- [x] Points d'intégration cartographiés
- [x] Mapping exigences → structure complet

### Évaluation de préparation

**Statut global : PRÊT POUR L'IMPLÉMENTATION** ✅

**Niveau de confiance : Élevé**

**Forces clés :**
- Architecture hybride LLM-trigger / Frontend-guide — économie de tokens, extensibilité native
- Module-level state pour `useChat` — persistance cross-routes sans refactoring lourd
- Empreinte backend minimale (2 fichiers nouveaux) — risque de régression quasi nul
- Frontières claires : copilot/ orchestre, chat/ rend, uiStore communique

**Priorité d'implémentation :**
1. Refactoring `useChat.ts` → module-level state
2. `FloatingChatWidget` dans le layout (remplacement ChatPanel)
3. `useDeviceDetection` + détection mobile
4. Installation Driver.js + lazy loading + CSS
5. Registre de parcours + types
6. `useGuidedTour` (orchestrateur)
7. Orchestration animations GSAP/Driver.js
8. Tool backend `trigger_guided_tour` + prompt
9. Ajout `data-guide-target` sur les composants existants
10. Tests
