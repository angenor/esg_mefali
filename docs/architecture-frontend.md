# Architecture Frontend — Nuxt 4 + Vue 3

## 1. Résumé exécutif

Le frontend est une **SPA Nuxt 4** (compatibilityVersion 4, structure `app/`) construite autour de **Vue 3 Composition API**, **TypeScript strict**, **Pinia 3** et **TailwindCSS 4**. Il consomme le backend FastAPI via `fetch()` natif et un **stream SSE** pour le chat IA (qui gère les tokens, les tools, les mises à jour de profil et les widgets interactifs). L'UI est en français, avec **dark mode obligatoire** (classe `.dark` sur `<html>`, thème CSS custom). 18 pages, 56 composants, 14 composables, 11 stores Pinia.

## 2. Stack technologique

| Catégorie | Technologie | Version | Justification |
|---|---|---|---|
| Framework | Nuxt | ^4.4.2 | Routing auto, auto-imports, module `@pinia/nuxt` |
| Vue | Vue 3 (Composition API, `<script setup lang="ts">`) | 3.x (via Nuxt) | Réactivité fine, types stricts |
| Langage | TypeScript | ^5.7 (strict) | Sécurité type, auto-complétion |
| State | Pinia | ^3.0.4 | Store officiel Vue 3, DX optimale |
| CSS | TailwindCSS + @tailwindcss/postcss | ^4.2.2 | Tailwind 4, dark mode variant custom |
| Graphiques | Chart.js + vue-chartjs | ^4.4 / ^5.3 | Dashboard, gauges, radars, scoring |
| Diagrammes | Mermaid | ^11.4 | Timelines, flux, architecture inline chat |
| Animations | GSAP | ^3.12 | Transitions de widgets, landing |
| Markdown | marked + dompurify | ^17 / ^3.3 | Rendu sécurisé des réponses LLM |
| Tests unit | Vitest | ^3.0.0 | Compatible Vue 3 + env=node |
| Tests E2E | Playwright | ^1.49 | E2E headless |

## 3. Configuration Nuxt — `frontend/nuxt.config.ts`

```ts
export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  devtools: { enabled: true },
  modules: ['@pinia/nuxt'],
  postcss: { plugins: { '@tailwindcss/postcss': {} } },
  typescript: { strict: true },
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/api',
    },
  },
  css: ['~/assets/css/main.css'],
  components: [{ path: '~/components', pathPrefix: false }],
  future: { compatibilityVersion: 4 },
})
```

Points clés :

- `compatibilityVersion: 4` active la nouvelle structure Nuxt 4 (`app/` contient tout)
- Un seul module externe (`@pinia/nuxt`) — volontairement minimal
- `runtimeConfig.public.apiBase` expose l'URL backend (env `NUXT_PUBLIC_API_BASE`)
- `components.pathPrefix: false` : un composant dans `components/ui/Button.vue` s'utilise `<Button />` sans préfixe de dossier

## 4. Structure du dossier `app/`

| Dossier | Nombre de fichiers | Rôle |
|---|---:|---|
| `pages/` | 18 | Routes Nuxt automatiques |
| `components/` | 56 | Composants Vue 3, groupés par feature |
| `composables/` | 14 | Logique métier partagée (fetch, SSE, gestion d'état) |
| `stores/` | 11 | Stores Pinia |
| `types/` | 11 | Interfaces TypeScript métier |
| `layouts/` | 1 | Layout `default.vue` (sidebar + header + main + chat panel) |
| `middleware/` | 1 | `auth.global.ts` — guard universel |
| `plugins/` | 3 | `mermaid.client.ts`, `chartjs.client.ts`, `gsap.client.ts` |
| `utils/` | 1 | `normalizeTimeline.ts` |
| `assets/css/` | 1 | `main.css` — thème Tailwind 4 |

## 5. Pages (routing Nuxt)

### Auth & profil

| Route | Fichier | Rôle |
|---|---|---|
| `/login` | `pages/login.vue` | Connexion email/password |
| `/register` | `pages/register.vue` | Inscription + détection pays automatique |
| `/profile` | `pages/profile.vue` | Édition profil utilisateur/entreprise |

### Navigation principale

| Route | Fichier | Rôle |
|---|---|---|
| `/` | `pages/index.vue` | Redirect vers `/dashboard` |
| `/dashboard` | `pages/dashboard.vue` | 4 cartes synthétiques (ESG, carbone, crédit, financement), flux d'activité, prochaines étapes |
| `/chat` | `pages/chat.vue` | Conversation IA avec SSE, upload documents, questions interactives |

### Modules métier

| Route | Fichier | Rôle |
|---|---|---|
| `/esg` | `pages/esg/index.vue` | Liste des évaluations ESG |
| `/esg/results` | `pages/esg/results.vue` | Dashboard scores E/S/G, recommandations, forces/faiblesses |
| `/carbon` | `pages/carbon/index.vue` | Calculateur empreinte carbone par catégorie |
| `/carbon/results` | `pages/carbon/results.vue` | Total tCO2e, plan réduction, benchmark |
| `/financing` | `pages/financing/index.vue` | Catalogue fonds filtrable (type, secteur, montant, accès) |
| `/financing/[id]` | `pages/financing/[id].vue` | Détail fonds + intermédiaires + timeline |
| `/credit-score` | `pages/credit-score/index.vue` | Score crédit vert (gauge), facteurs de risque, historique |
| `/action-plan` | `pages/action-plan/index.vue` | Timeline verticale chronologique, filtres catégories, barre progression |
| `/applications` | `pages/applications/index.vue` | Liste dossiers de candidature |
| `/applications/[id]` | `pages/applications/[id].vue` | Détail dossier + sections |
| `/documents` | `pages/documents.vue` | Upload, preview, liste docs |
| `/reports` | `pages/reports/index.vue` | Génération/export rapports |

## 6. Composants (56 fichiers, 11 sous-dossiers)

| Dossier | Composants | Exemple |
|---|---:|---|
| `ui/` | 2 | `FullscreenModal`, `ToastNotification` |
| `layout/` | 3 | `AppHeader`, `AppSidebar`, `ChatPanel` |
| `chat/` | 13 | `ChatInput`, `ChatMessage`, `ConversationList`, `MessageParser`, `SingleChoiceWidget`, `MultipleChoiceWidget`, `InteractiveQuestionHost`, `JustificationField`, `ToolCallIndicator`, `ProfileNotification`, `AnswerElsewhereButton`, `WelcomeMessage`, `InteractiveQuestionInputBar` |
| `richblocks/` | 8 | `ChartBlock`, `MermaidBlock`, `TableBlock`, `GaugeBlock`, `ProgressBlock`, `TimelineBlock`, `BlockError`, `BlockPlaceholder` |
| `esg/` | 6 | `ScoreCircle`, `CriteriaProgress`, `ScoreHistory`, `Recommendations`, `ReportButton`, `StrengthsBadges` |
| `credit/` | 7 | `ScoreGauge`, `SubScoreGauges`, `FactorsRadar`, `ScoreHistory`, `DataCoverage`, `CertificateButton`, `Recommendations` |
| `dashboard/` | 4 | `ScoreCard`, `FinancingCard`, `NextActions`, `ActivityFeed` |
| `action-plan/` | 6 | `ActionCard`, `ProgressBar`, `Timeline`, `CategoryFilter`, `BadgeGrid`, `ReminderForm` |
| `documents/` | 4 | `DocumentList`, `DocumentDetail`, `DocumentUpload`, `DocumentPreview` |
| `profile/` | 3 | `ProfileForm`, `ProfileField`, `ProfileProgress` |

### Composants génériques (réutilisables)

- **`components/ui/`** : seulement 2 composants UI de base (`FullscreenModal`, `ToastNotification`). La règle projet impose d'y extraire tout pattern répété 2+ fois — c'est une dette légère à surveiller.
- **`components/richblocks/`** : système de blocs visuels inline pour le chat (chart, mermaid, table, gauge, progress, timeline) + placeholders d'erreur. Parsés depuis les réponses LLM via `useMessageParser`.

## 7. Composables (14)

| Composable | Rôle |
|---|---|
| `useAuth` | `login`, `register`, `logout`, `apiFetch<T>()` wrapper fetch avec header JWT |
| `useChat` | SSE streaming, `sendMessage`, `createConversation`, `fetchMessages`, `submitInteractiveAnswer`, parsing des events SSE |
| `useEsg` | `fetchAssessments`, `getScore` (criteria + pillar details) |
| `useCarbon` | `calculateEmissions`, `getResults` |
| `useFinancing` | `fetchFunds`, `getFundDetail`, `trackMatch` |
| `useCreditScore` | `fetchScore`, `getGauges` |
| `useActionPlan` | `fetchPlan`, `updateItem`, `createReminder` |
| `useApplications` | `fetchApplications`, `submitApplication` |
| `useDocuments` | `uploadDocument`, `fetchDocuments` |
| `useCompanyProfile` | `fetchProfile`, `updateField`, `fetchCompletion` |
| `useDashboard` | `fetchSummary` |
| `useReports` | `generateReport`, `exportPDF` |
| `useMessageParser` | `parse(content)` → `ParsedSegment[]` (texte vs richblock) |
| `useToast` | Notifications in-app (`success`, `error`, `info`) |

## 8. Stores Pinia (11)

| Store | State principal | Actions |
|---|---|---|
| `auth` | `user`, `accessToken`, `refreshToken`, `isAuthenticated` | `setTokens`, `setUser`, `clearAuth`, `loadFromStorage` |
| `ui` | `theme` (`light`/`dark`), `sidebarOpen`, `chatPanelOpen`, `conversationDrawerOpen` | `initTheme`, `toggleTheme`, `toggleSidebar`, `toggleChatPanel`, `setTheme` |
| `company` | `profile`, `completion`, `recentUpdates` | `setProfile`, `updateProfileField`, `addProfileUpdate` |
| `dashboard` | `summary`, `loading`, `error` | `setSummary`, `setLoading`, `setError` |
| `esg` | `assessments[]`, `currentAssessment`, `currentScore` | `setAssessments`, `setCurrentAssessment`, `setCurrentScore` |
| `carbon` | `assessments[]`, `currentAssessment`, `total` | `setAssessments`, `setCurrentAssessment` |
| `financing` | `funds[]`, `currentFund`, `matches[]` | `setFunds`, `setCurrentFund`, `addMatch` |
| `creditScore` | `score`, `loading` | `setScore`, `setLoading` |
| `actionPlan` | `plan`, `items[]`, `reminders[]` | `setPlan`, `addItem`, `updateItem`, `addReminder` |
| `applications` | `applications[]`, `currentApplication` | `setApplications`, `setCurrentApplication`, `addApplication` |
| `documents` | `documents[]`, `currentDocument`, `uploading` | `setDocuments`, `setCurrentDocument`, `addDocument` |

Le store `ui` est le seul qui manipule directement le DOM : il applique la classe `dark` sur `document.documentElement` et persiste le choix dans `localStorage`.

## 9. Layouts et middleware

- **`layouts/default.vue`** — layout unique : sidebar de navigation + header (user menu + toggle dark) + slot contenu + `ChatPanel` toujours monté à droite
- **`middleware/auth.global.ts`** — middleware global : charge les tokens depuis `localStorage` au premier rendu client, redirige vers `/login` si non authentifié, laisse passer `/login` et `/register` sans auth

## 10. Plugins (`.client.ts`, exécutés côté navigateur)

| Plugin | Rôle |
|---|---|
| `mermaid.client.ts` | Init Mermaid (`startOnLoad: false`, theme `default`) |
| `chartjs.client.ts` | Enregistrement des éléments Chart.js (`BarElement`, `LineElement`, `PieElement`, `RadarChart`, `Filler`, ...) |
| `gsap.client.ts` | Injection GSAP globale (`$gsap` dans `useNuxtApp`) |

## 11. Types TypeScript (`app/types/`, 11 fichiers)

- `index.ts` — `User`, `Conversation`, `Message`, `TokenResponse`, `PaginatedResponse<T>`, `ApiError`
- `esg.ts` — `ESGPillar`, `ESGStatus`, `CriteriaScoreDetail`, `PillarDetail`, `AssessmentData`, `ScoreResponse`
- `carbon.ts` — `CarbonStatus`, `EmissionCategory`, `CarbonEmissionEntry`, `ReductionPlan`, `CarbonAssessment`, `BenchmarkPosition`
- `financing.ts` — `FundType`, `AccessType`, `IntermediaryType`, `Fund`, `FundIntermediary`, `MatchStatus`, `ApplicationStatus`
- `credit.ts` — `CreditScore`, `RiskFactor`, `SubScore`, `CertificateType`
- `actionPlan.ts` — `ActionItem`, `ActionPlan`, `ReminderType`, `BadgeType`
- `company.ts` — `CompanyProfile`, `CompletionResponse`, `ProfileUpdateEvent`
- `dashboard.ts` — `DashboardSummary`
- `documents.ts` — `Document`, `DocumentType`, `DocumentStatus`
- `richblocks.ts` — `ChartBlockData`, `TableBlockData`, `GaugeBlockData`, `ProgressBlockData`, `TimelineBlockData`, `RichBlockType`, `ParsedSegment`
- `interactive-question.ts` — `InteractiveQuestionType` (`qcu`/`qcm`/`qcu_justification`/`qcm_justification`), `InteractiveQuestion`, `InteractiveQuestionState` (`pending`/`answered`/`abandoned`/`expired`)
- `report.ts` — `ReportType`, `ReportStatus`, `Report`, `ExportFormat`

## 12. Thème et dark mode

`app/assets/css/main.css` :

```css
@import "tailwindcss";
@custom-variant dark (&:where(.dark, .dark *));
@theme {
  --color-brand-green: #10B981;
  --color-brand-blue: #3B82F6;
  --color-brand-purple: #8B5CF6;
  --color-brand-orange: #F59E0B;
  --color-brand-red: #EF4444;
  --color-surface-bg: #F9FAFB;
  --color-surface-text: #111827;
  --color-surface-dark-bg: #111827;
  --color-surface-dark-text: #F9FAFB;
  --color-dark-card: #1F2937;
  --color-dark-border: #374151;
}
```

**Règles dark mode (OBLIGATOIRES)** — appliquées à chaque nouveau composant :

| Usage | Classes Tailwind |
|---|---|
| Fond de page | `bg-surface-bg dark:bg-surface-dark-bg` |
| Fond de carte | `bg-white dark:bg-dark-card` |
| Texte principal | `text-surface-text dark:text-surface-dark-text` |
| Texte secondaire | `text-gray-600 dark:text-gray-400` |
| Bordures | `border-gray-200 dark:border-dark-border` |
| Inputs | `dark:bg-dark-input dark:text-surface-dark-text` |
| Hover | `hover:bg-gray-50 dark:hover:bg-dark-hover` |

## 13. Intégration backend

- **Base URL** : `useRuntimeConfig().public.apiBase` (env `NUXT_PUBLIC_API_BASE`, défaut `http://localhost:8000/api`)
- **Fetch** : API native `fetch()` (pas `$fetch` Nuxt ni `useFetch`) pour pouvoir lire le stream SSE ligne par ligne
- **Auth** : tokens JWT en `localStorage`, ajoutés en header `Authorization: Bearer <token>` dans tous les appels authentifiés via le wrapper `useAuth.apiFetch`
- **Streaming SSE** : géré par `useChat` avec un `ReadableStream` (pattern `data: {JSON}\n\n`). Les events typés sont dispatchés vers les stores concernés (`profile_update` → `companyStore`, `tool_call_*` → affichage `ToolCallIndicator`, etc.)
- **Upload** : `multipart/form-data` pour les documents (`FormData` avec champ `file`)
- **Refresh token** : logique à confirmer (pas immédiatement visible dans le composable `useAuth`) ; à documenter plus en détail

## 14. Tests frontend

- `frontend/tests/components/` :
  - `MessageParser.test.ts` (parsing richblocks)
  - `TimelineBlock.test.ts` (rendu timeline)
- Config : `vitest.config.ts` (env `node`, pattern `tests/**/*.test.ts`, alias `~` vers `app/`)
- E2E : Playwright configuré (`npm run test:e2e`), scénarios à compléter
- Couverture actuelle très faible (2 tests unitaires + E2E framework prêt) — c'est la principale dette de test du projet

## 15. Risques et points d'attention

- **Couverture tests frontend** trop faible — à renforcer (rule projet : 80 %)
- **`components/ui/` presque vide** — extraire plus de primitives réutilisables (boutons, badges, inputs) pour respecter la règle de réutilisabilité
- **Gestion du refresh token** — logique à documenter / compléter côté `useAuth`
- **Aucun rate-limit côté client** sur le chat SSE — dépendance à la robustesse du backend
- **Middleware global `auth.global.ts`** — seule barrière d'autorisation, à tester soigneusement (cas `localStorage` inaccessible, SSR/hydration)

## 16. Références croisées

- [Inventaire des composants](./component-inventory-frontend.md)
- [Architecture d'intégration](./integration-architecture.md)
- [Guide de développement](./development-guide.md)
