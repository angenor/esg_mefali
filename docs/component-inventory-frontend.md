# Inventaire frontend — composants, composables, stores

60 composants Vue 3 dans [frontend/app/components/](../frontend/app/components/), regroupés en ~12 sous-dossiers par feature. Tous compatibles **dark mode** obligatoire et écrits en `<script setup lang="ts">`. Complété par 18 composables réutilisables et 11 stores Pinia.

## 1. Composants par domaine

### 1.1 Widget chat flottant — `copilot/` (5 composants, spec 019)

| Composant | Rôle |
|---|---|
| `FloatingChatWidget.vue` | Conteneur principal du widget ; gère rétraction GSAP, résilience SSE, chat + widgets interactifs |
| `FloatingChatButton.vue` | Bouton de relance quand le widget est minimisé |
| `ChatWidgetHeader.vue` | En-tête (titre conversation, actions) |
| `ConnectionStatusBadge.vue` | Indicateur online/offline pour SSE resilience (spec 7-3) |
| `GuidedTourPopover.vue` | Popover custom driver.js avec contenu Vue, dark mode, ARIA (spec 5-4) |

### 1.2 Chat — `chat/` (11 composants)

Messages, widgets interactifs (spec 018) et indicateurs tool (spec 012) :

| Composant | Rôle |
|---|---|
| `ChatMessage.vue` | Bulle message user/assistant + rendu markdown + blocs richblocks |
| `ChatInput.vue` | Zone de saisie + upload fichier |
| `ConversationList.vue` | Liste latérale des conversations |
| `WelcomeMessage.vue` | Message d'accueil en début de conversation |
| `MessageParser.vue` | Parse le markdown et hydrate les blocs richblocks |
| `ToolCallIndicator.vue` | Indicateur contextualisé en français pour chaque tool call |
| `InteractiveQuestionHost.vue` | Hôte des widgets interactifs (monte le composant adapté selon le type) |
| `SingleChoiceWidget.vue` | Widget QCU (type `qcu` / `qcu_justification`) |
| `MultipleChoiceWidget.vue` | Widget QCM (type `qcm` / `qcm_justification`) avec bornes min/max |
| `JustificationField.vue` | Textarea 400 char max pour les variantes `*_justification` |
| `AnswerElsewhereButton.vue` | Bouton "Répondre autrement" → passe la question en `abandoned` |

### 1.3 Blocs visuels streamés — `richblocks/` (8 composants)

Les blocs sont émis par les nœuds LangGraph (contenu inline dans un message) et hydratés par `MessageParser.vue`.

| Composant | Rôle |
|---|---|
| `ChartBlock.vue` | Graphique Chart.js (bar, line, donut, radar) |
| `MermaidBlock.vue` | Diagramme mermaid |
| `GaugeBlock.vue` | Jauge circulaire (scores 0-100) |
| `ProgressBlock.vue` | Barre de progression |
| `TableBlock.vue` | Tableau structuré |
| `TimelineBlock.vue` | Timeline verticale (plan d'action, évaluations historiques). Normalisation tolérante aux variantes `phases/items/steps → events`, aliases `period→date`, `name→title` (spec 013) |
| `BlockError.vue` | Surface minimale en cas d'erreur de rendu |
| `BlockPlaceholder.vue` | Skeleton pendant chargement |

### 1.4 ESG — `esg/` (6 composants)

| Composant | Rôle |
|---|---|
| `ScoreCircle.vue` | Cercle score ESG global |
| `CriteriaProgress.vue` | Progression 30 critères E-S-G |
| `StrengthsBadges.vue` | Forces identifiées |
| `Recommendations.vue` | Recommandations |
| `ScoreHistory.vue` | Historique Chart.js |
| `ReportButton.vue` | Déclenche génération rapport PDF |

### 1.5 Crédit — `credit/` (7 composants)

| Composant | Rôle |
|---|---|
| `ScoreGauge.vue` | Jauge principale score crédit |
| `SubScoreGauges.vue` | Sous-scores (paiements, stabilité, etc.) |
| `FactorsRadar.vue` | Radar des facteurs |
| `DataCoverage.vue` | Taux de couverture des données source |
| `Recommendations.vue` | Recommandations spécifiques crédit |
| `ScoreHistory.vue` | Historique |
| `CertificateButton.vue` | Télécharge le certificat PDF |

### 1.6 Plan d'action — `action-plan/` (6 composants)

| Composant | Rôle |
|---|---|
| `Timeline.vue` | Timeline verticale chronologique |
| `ActionCard.vue` | Carte d'action unique (catégorie, priorité, completion) |
| `ProgressBar.vue` | Barre de progression globale / par catégorie |
| `CategoryFilter.vue` | Filtre environment/social/governance/financing/carbon/intermediary_contact |
| `BadgeGrid.vue` | Grille de 5 badges gamification |
| `ReminderForm.vue` | Création de rappel custom |

### 1.7 Dashboard — `dashboard/` (4 composants)

| Composant | Rôle |
|---|---|
| `ScoreCard.vue` | Carte synthétique (ESG / carbon / crédit) |
| `FinancingCard.vue` | Carte financements (parcours direct / intermédiaire) |
| `ActivityFeed.vue` | Activité récente |
| `NextActions.vue` | Prochaines actions recommandées |

### 1.8 Documents — `documents/` (4 composants)

`DocumentList.vue`, `DocumentDetail.vue`, `DocumentUpload.vue` (drag & drop), `DocumentPreview.vue`.

### 1.9 Profil — `profile/` (3 composants)

`ProfileForm.vue`, `ProfileField.vue`, `ProfileProgress.vue`.

### 1.10 Financements & Applications

Répartis entre `financing/` et `applications/` — cartes de fonds, matching, éditeur de dossier.

### 1.11 Structurels — `layout/` et `ui/`

| Composant | Rôle |
|---|---|
| `layout/AppHeader.vue` | Barre du haut (logo, theme toggle, user menu) |
| `layout/AppSidebar.vue` | Navigation latérale (marqueurs `data-guide-target` pour tours) |
| `ui/ToastNotification.vue` | Notification flottante (pilotée par `useToast`) |
| `ui/FullscreenModal.vue` | Modale plein écran réutilisable |

## 2. Composables (18)

[frontend/app/composables/](../frontend/app/composables/). **Gras** = state module-level (partagé entre composants, survit à la navigation).

| Composable | Responsabilité |
|---|---|
| **`useAuth.ts`** | Login, logout, refresh token (single-flight), `apiFetch<T>()` universal wrapper, `SessionExpiredError` |
| **`useChat.ts`** | SSE streaming (fetch reader), conversations, messages, widgets interactifs, résilience réseau, parsing marker SSE |
| **`useGuidedTour.ts`** | Machine à états tours guidés driver.js, polling DOM, countdown adaptatif, guidanceStats localStorage, multi-tab sync |
| `useDeviceDetection.ts` | Détection mobile/desktop, breakpoints (pour sizing widget) |
| `useDriverLoader.ts` | Lazy-load driver.js via dynamic import (ADR7) |
| `useMessageParser.ts` | Parse markdown + hydrate richblocks |
| `useFocusTrap.ts` | Focus trap clavier pour widget / modales (accessibilité) |
| `useToast.ts` | Queue de notifications in-app |
| `useCompanyProfile.ts` | API `/api/company/profile` |
| `useDocuments.ts` | API `/api/documents/*` + upload multipart |
| `useEsg.ts` | API `/api/esg/*` |
| `useCarbon.ts` | API `/api/carbon/*` |
| `useFinancing.ts` | API `/api/financing/*` |
| `useCreditScore.ts` | API `/api/credit/*` |
| `useApplications.ts` | API `/api/applications/*` |
| `useActionPlan.ts` | API `/api/action-plan/*` |
| `useReports.ts` | API `/api/reports/*` |
| `useDashboard.ts` | API `/api/dashboard/summary` |

## 3. Stores Pinia (11)

[frontend/app/stores/](../frontend/app/stores/). Pattern setup stores.

| Store | State clé | Actions clé |
|---|---|---|
| `auth.ts` | `user`, `accessToken`, `refreshToken` | `setTokens()`, `setUser()`, `clearAuth()`, `loadFromStorage()` |
| `ui.ts` | `sidebarOpen`, `chatWidgetOpen`, `chatWidgetMinimized`, `guidedTourActive`, `currentPage`, `theme`, `prefersReducedMotion`, widget geometry | `toggleTheme()`, `initTheme()`, `setChatWidgetOpen()`, `setCurrentPage()`, `setGuidedTourActive()` |
| `company.ts` | Profil entreprise + completion | `fetchProfile()`, `updateProfile()`, `markFieldUpdated()` |
| `documents.ts` | Liste + état d'upload | `fetchDocuments()`, `uploadDocument()`, `deleteDocument()` |
| `esg.ts` | Score courant, critères, historique | `fetchScore()`, `saveCriterion()`, `evaluate()` |
| `carbon.ts` | Bilans, entrées, résumé | `fetchAssessments()`, `saveEntry()`, `finalize()` |
| `financing.ts` | Catalogue + filtres + matches | `fetchFunds()`, `fetchMatches()`, `updateMatchStatus()` |
| `creditScore.ts` | Score + breakdown + history | `fetchScore()`, `generateScore()` |
| `actionPlan.ts` | Plan actif + items par bucket (6m/12m/24m) | `generatePlan()`, `updateItem()`, `createReminder()` |
| `applications.ts` | Liste + dossier en cours | `fetchApplications()`, `generateSection()`, `updateSection()` |
| `dashboard.ts` | KPIs agrégés | `fetchSummary()` |

## 4. Types TypeScript

[frontend/app/types/](../frontend/app/types/) — 12 fichiers.

| Fichier | Domaine principal |
|---|---|
| `index.ts` | Re-exports consolidés |
| `guided-tour.ts` | `GuidedTourDefinition`, `GuidedTourStep`, `TourState`, `TourContext` |
| `interactive-question.ts` | `InteractiveQuestion*`, 4 variantes, `InteractiveQuestionAnswer`, états |
| `richblocks.ts` | `ChartBlock`, `MermaidBlock`, `GaugeBlock`, `ProgressBlock`, `TableBlock`, `TimelineBlock`, `RichBlock` union |
| `company.ts`, `documents.ts`, `esg.ts`, `carbon.ts`, `financing.ts`, `actionPlan.ts`, `dashboard.ts`, `report.ts` | Un par domaine métier |

## 5. Layouts, middlewares, plugins

### Layouts (1)
- `default.vue` — header + sidebar + slot + widget chat flottant.

### Middlewares globaux (2)
- `auth.global.ts` — redirige non connectés vers `/login` (exceptions : `/login`, `/register`).
- `chat-redirect.global.ts` — `/chat` → `/?openChat=1` (legacy spec 019).

### Plugins client (3)
- `gsap.client.ts`, `mermaid.client.ts`, `chartjs.client.ts` — initialisent les libs client-only.

## 6. Assets & styles

- Stylesheet principal : [frontend/app/assets/css/main.css](../frontend/app/assets/css/main.css).
  - `@import 'driver.js/dist/driver.css';`
  - `@import 'tailwindcss';`
  - Bloc `@theme` avec variables brand (`--color-brand-green`, `-blue`, `-purple`, `-orange`, `-red`), surfaces (`--color-surface-bg`, `-text`, `-dark-bg`, `-dark-text`) et dark mode (`--color-dark-card`, `-border`, `-hover`, `-input`).
- Overrides driver.js : classes dark mode, couleurs brand sur les boutons de navigation du popover.

## 7. Registre des tours guidés

[frontend/app/lib/guided-tours/registry.ts](../frontend/app/lib/guided-tours/registry.ts) expose 6 tours :

| Tour ID | Page cible | Marquages `data-guide-target` |
|---|---|---|
| `show_esg_results` | `/esg/results` | `score-circle`, `strengths-badges`, `recommendations` |
| `show_carbon_results` | `/carbon/results` | `donut-chart`, `benchmark`, `reduction-plan` |
| `show_financing_catalog` | `/financing` | `fund-list` |
| `show_credit_score` | `/credit-score` | `score-gauge` |
| `show_action_plan` | `/action-plan` | `timeline` |
| `show_dashboard_overview` | `/dashboard` | `esg-card`, `carbon-card`, `credit-card`, `financing-card` |

Total : 14 marquages `data-guide-target` à travers 7 fichiers (sidebar + 6 pages cibles).

## 8. Patrons et conventions

- **Composition API uniquement**, `<script setup lang="ts">`.
- **Props explicites** + `defineEmits` pour tous les composants.
- **Pas de `style` scopé** pour les variables couleurs — utiliser Tailwind variants `dark:`.
- **Accessibilité** : chaque widget interactif annote `role`, `aria-checked`, `aria-describedby`.
- **Animations** : GSAP encapsulé dans le widget chat, respect `prefers-reduced-motion` via `useUiStore.prefersReducedMotion`.
- **Réutilisation** : si un pattern apparaît > 2 fois, extraction en `components/ui/` ou composable ([CLAUDE.md](../CLAUDE.md)).
- **Dark mode obligatoire** sur chaque composant (variables `dark:bg-dark-card`, etc.).
- **Format d'imports** : alias `~` → `app/` (défini dans `tsconfig.json`).

## 9. Axes d'évolution

- Composants `ui/` encore légers (2). À étoffer (boutons, inputs, badges, modals génériques) à mesure que les patterns se répètent.
- Tests de composants unitaires couvrent principalement les composables et stores ; les composants Vue ont moins de couverture. À renforcer via `@vue/test-utils` pour les richblocks critiques.
- Pas de Storybook ou équivalent — documentation visuelle des composants à envisager.
- Internationalisation : tout est en français en dur ; à extraire si élargissement à d'autres langues de la zone CEDEAO.
