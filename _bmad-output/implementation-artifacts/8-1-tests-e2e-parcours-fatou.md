# Story 8.1 : Tests E2E — Parcours Fatou (guidage propose et accepte, multi-pages)

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

En tant que product owner,
je veux valider le parcours complet d'un utilisateur qui accepte un guidage propose apres completion d'un module (bilan carbone),
afin de garantir que la chaine de bout en bout (widget flottant → consentement → retraction → popovers Driver.js multi-pages → reapparition) fonctionne sans regression en condition reelle d'utilisation.

## Contexte — etat actuel (VERIFIE avant redaction)

Audit de l'infrastructure e2e existante (2026-04-14) :

- **Playwright 1.49 est deja installe** comme devDependency dans `frontend/package.json` ligne 29 (`"@playwright/test": "^1.49.0"`) et le script `"test:e2e": "playwright test"` est expose ligne 13. **AUCUNE config `playwright.config.ts` n'existe**, **AUCUN dossier `tests/e2e/`** n'existe — cette story est la **premiere** a instancier l'infrastructure E2E du projet. Architecture (`architecture.md:96`) confirme « Vitest 3.0 (tests unitaires), Playwright 1.49 (E2E) » + lacune documentee ligne 1022 « Tests E2E Playwright pour le flux complet guidage — post-MVP ».
- **Dossier tests Vitest existant** : `frontend/tests/` contient `components/`, `composables/`, `layouts/`, `lib/`, `middleware/`, `pages/`, `stores/`, `setup.ts`. **Convention** : les tests E2E iront dans un nouveau dossier **frere** `frontend/tests/e2e/` (pas dans `frontend/tests/components/`). Cela evite le conflit avec `vitest.config.ts` qui indexe `frontend/tests/**` pour les tests unitaires — Playwright a sa propre config (`playwright.config.ts`) et peut exclure `e2e/` cote Vitest via `test.exclude` si collision.
- **Selectors stables deja en place sur les elements cibles du parcours `show_carbon_results`** :
  - `[data-testid="floating-chat-button"]` — `components/copilot/FloatingChatButton.vue:15`
  - `[data-guide-target="sidebar-carbon-link"]` — `components/layout/AppSidebar.vue:61` (genere via `{ guideTarget: 'sidebar-carbon-link' }`)
  - `[data-guide-target="carbon-donut-chart"]` — `pages/carbon/results.vue:219` (conditionne par `v-if="doughnutData"`)
  - `[data-guide-target="carbon-benchmark"]` — `pages/carbon/results.vue:337`
  - `[data-guide-target="carbon-reduction-plan"]` — `pages/carbon/results.vue:280`
  - `[data-testid="popover-next-btn"]`, `[data-testid="popover-close-btn"]`, `[data-testid="countdown-badge"]` — `components/copilot/GuidedTourPopover.vue:100, 128, 137`
- **Registre parcours `show_carbon_results`** (`lib/guided-tours/registry.ts:58-96`) — entryStep pointe `[data-guide-target="sidebar-carbon-link"]` avec `DEFAULT_ENTRY_COUNTDOWN = 8` secondes ; `targetRoute: '/carbon/results'` ; 3 steps (donut, benchmark, plan). **Ce parcours est celui utilise par Fatou**.
- **SSE POST-based pattern** : `frontend/app/composables/useChat.ts` (lignes 216-224, 604-614) ouvre un `fetch()` POST qui retourne un `ReadableStream`. Le backend emet des markers dans le contenu du message :
  - `<!--SSE:{"__sse_guided_tour__":true,"tour_id":"show_carbon_results","context":{...}}-->` → declenche le guidage via `useChat.ts:828-860`
  - `<!--SSE:{"__sse_interactive_question__":true,"id":"...","variant":"qcu","prompt":"...","choices":[...],"allow_answer_elsewhere":true}-->` → declenche le widget interactif de consentement (feature 018)
  - **Ces markers sont extraits et consommes dans `useChat.ts`** puis **masques** de l'affichage final du message.
- **Widget de consentement (Story 6.3)** : quand le LLM propose un guidage, il emet d'abord **un widget interactif QCU** avec choix « Oui, montre-moi » / « Non merci », puis — apres la reponse — un second marker `__sse_guided_tour__` si l'utilisateur a accepte. Le widget QCU est rendu par `components/chat/SingleChoiceWidget.vue` via `InteractiveQuestionHost.vue` — **selectors a identifier** : il n'y a pas encore de `data-testid` sur le bouton « Oui » du consentement, **il faudra l'ajouter** dans la story (sous-tache 1.x) ou utiliser un selecteur par texte (`page.getByRole('button', { name: 'Oui, montre-moi' })`).
- **Aucun utilitaire de login programmatique** n'existe pour les tests : `pages/login.vue` consomme `/auth/login` → JWT stockes par `composables/useAuth.ts` dans un cookie HTTP-only. Pour E2E, **deux strategies** envisageables (voir AC0 — Design) :
  1. **Login UI** (robuste, lent) : `page.goto('/login')` + `fill` + `click` → ~2s par test
  2. **Login programmatique** (rapide) : POST direct sur `/auth/login` via `request.post()` Playwright puis `page.context().addCookies(...)` → <500ms par test
- **Le backend doit etre accessible** pendant les tests E2E (contrairement aux tests Vitest qui moquent fetch). **Deux strategies** envisageables :
  1. **Backend reel** + base de donnees de test + `playwright.config.webServer` qui lance `uvicorn` + `nuxt dev` avant les tests
  2. **Backend mocke** via `page.route()` qui intercepte tous les appels `/api/**` et retourne des fixtures JSON + un SSE reader scripte
- **Decision prise ci-dessous (AC0)** : **backend mocke via `page.route()`** pour la Story 8.1 (et toutes les stories 8.x) — rationale :
  - Isolation : pas de dependance a la BDD, Redis, OpenRouter, MinIO → tests deterministes et rapides (<10s par spec)
  - CI-friendly : le workflow GH Actions n'a pas a orchestrer Docker Compose complet
  - Le but de l'epic 8 est de valider l'**integration frontend**, pas le backend (deja couvert par 935+ tests pytest)
  - Le SSE peut etre simule en renvoyant un `ReadableStream` fabrique avec les markers qu'on veut tester
- **Variable d'environnement pour le backend URL** : `frontend/nuxt.config.ts` utilise `NUXT_PUBLIC_API_BASE` (lignes a verifier) et `useRuntimeConfig().public.apiBase` dans `composables/apiFetch.ts`. **Dans les tests E2E** on laisse la valeur par defaut (ex. `http://localhost:3000/api`) et on moque tous les appels avec `page.route('**/api/**', ...)`.
- **Reduced-motion** : `FloatingChatWidget.vue` et `useGuidedTour.ts` gerent `prefers-reduced-motion: reduce` pour desactiver les animations GSAP. **En E2E**, on **active** reduced-motion via `page.emulateMedia({ reducedMotion: 'reduce' })` pour supprimer les 500-800ms d'animations GSAP et rendre les assertions deterministes. **Tests dedies reduced-motion possibles mais hors scope** de 8.1 (pas d'AC specifique dans les epics).

Cette story comble **6 gaps** identifies :

1. **Pas de `playwright.config.ts`** — l'infrastructure E2E n'existe pas.
2. **Pas de dossier `tests/e2e/`** — aucun test E2E.
3. **Pas de fixtures partagees** (auth, mock backend, mock SSE) — a creer pour les 5 parcours de l'epic 8.
4. **Pas de `data-testid` sur les boutons du widget de consentement QCU** — il faut les ajouter pour des selectors stables.
5. **Pas de helpers `test/utils/`** pour simuler les markers SSE et scripter les reponses backend.
6. **Pas de workflow CI pour lancer Playwright** — hors scope 8.1 (l'infrastructure CI Playwright sera ajoutee quand toute l'epic 8 sera implementee — story 8.6 ou post-epic).

## Acceptance Criteria

### AC0 : Infrastructure Playwright — config, fixtures, mocks (FOUNDATIONNELLE pour epic 8)

**Given** le projet n'a pas encore de config Playwright
**When** on initialise l'infrastructure E2E
**Then** un fichier `frontend/playwright.config.ts` est cree avec les options suivantes (TypeScript strict compatible) :

```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false, // Sequentiel pour stabilite SSE/guidage
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: process.env.CI ? 'github' : [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    viewport: { width: 1280, height: 800 }, // Desktop >= 1024px (requis widget)
  },
  projects: [
    { name: 'chromium-desktop', use: { ...devices['Desktop Chrome'] } },
  ],
  // webServer: lance Nuxt en dev avant les tests (backend mocke via page.route)
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    stdout: 'pipe',
    stderr: 'pipe',
  },
})
```

**And** `frontend/vitest.config.ts` exclut `tests/e2e/**` de ses specs via `test.exclude: [...defaults, 'tests/e2e/**']` (verifier la config actuelle et ajouter si absent).

**And** un fichier `frontend/tests/e2e/fixtures/auth.ts` est cree et expose une fonction `loginAs(page: Page, user: TestUser): Promise<void>` qui :
1. Intercepte `POST **/api/auth/login` avec `page.route()` et renvoie `{ access_token, refresh_token, user: {...} }` depuis la fixture.
2. Intercepte `GET **/api/auth/me` et renvoie `user`.
3. Navigue vers `/login`, remplit les champs, clique submit, attend `page.waitForURL('/dashboard')`.

**Alternative (acceptable si login UI trop lent)** : `loginAs` pose directement les cookies via `page.context().addCookies([{ name: 'access_token', value: 'fake-jwt', domain: 'localhost', path: '/' }])` puis `page.goto('/dashboard')` — **choix laisse au dev** mais documenter en commentaire.

**And** un fichier `frontend/tests/e2e/fixtures/mock-backend.ts` est cree et expose :

```typescript
export interface MockBackendOptions {
  user?: TestUser
  companyProfile?: CompanyProfile
  carbonData?: CarbonSummary
  // Scenarios SSE pre-scriptes pour le chat
  chatScenario?: 'propose_guided_tour_after_carbon' | 'refuse_guided_tour' | ...
}

/**
 * Pose tous les intercepteurs page.route() pour simuler le backend.
 * Doit etre appele AVANT page.goto() pour garantir la capture.
 */
export async function installMockBackend(page: Page, options?: MockBackendOptions): Promise<void>
```

**Responsabilites minimales pour 8.1** (etendre dans les stories suivantes) :
- `GET **/api/auth/me` → renvoie `user` depuis fixture
- `GET **/api/company-profile` → renvoie `companyProfile`
- `GET **/api/carbon/summary` → renvoie `carbonData` avec `total_tco2: 47.2, top_category: "transport", top_category_pct: 62, sector: "agroalimentaire"`
- `GET **/api/carbon/bilans` → renvoie la liste avec 1 bilan completable
- `GET **/api/dashboard/summary` → renvoie un dashboard avec esg/carbon/credit/financing agreges
- `POST **/api/chat/messages` → renvoie un `ReadableStream` scripte contenant :
  1. Quelques chunks de texte markdown (simule la reponse LLM)
  2. Un marker `<!--SSE:{"__sse_interactive_question__":true,"id":"iq-tour-consent-001","variant":"qcu","prompt":"Voulez-vous voir vos resultats carbone ?","choices":[{"value":"yes","label":"Oui, montre-moi"},{"value":"no","label":"Non merci"}],"allow_answer_elsewhere":false}-->`
  3. Fin du stream
- `POST **/api/chat/interactive-questions/iq-tour-consent-001/answer` → renvoie un SSE stream qui contient le marker `<!--SSE:{"__sse_guided_tour__":true,"tour_id":"show_carbon_results","context":{"total_tco2":47.2,"top_category":"transport","top_category_pct":62,"sector":"agroalimentaire"}}-->` + un message de confirmation.
- `POST **/api/auth/refresh` → stub minimal qui renvoie un `access_token` frais (non utilise dans 8.1 mais prepare 8.3/8.4)

**And** un helper `frontend/tests/e2e/fixtures/sse-stream.ts` est cree et expose :

```typescript
/**
 * Construit un Response avec ReadableStream SSE-compatible pour page.route fulfill.
 * @param chunks Sequence de strings a emettre (un chunk = un read()).
 * @param delayMs Delai optionnel entre chunks pour simuler la latence reseau.
 */
export function createSSEResponse(chunks: string[], delayMs?: number): {
  body: ReadableStream<Uint8Array>
  headers: Record<string, string>
}
```

**Rationale** : le SSE POST-based du projet n'est pas du vrai SSE EventSource, c'est du streaming HTTP — un simple `ReadableStream` suffit. Les chunks contiennent du **markdown + markers** consommes par `useChat.ts`.

**And** une fixture TypeScript `frontend/tests/e2e/fixtures/users.ts` definit :

```typescript
export const FATOU: TestUser = {
  id: 'user-fatou-001',
  email: 'fatou.diallo@pme-agro.sn',
  full_name: 'Fatou Diallo',
  // ... champs utilises par l'app
}
export const FATOU_COMPANY: CompanyProfile = {
  id: 'company-fatou-001',
  name: 'PME Agro Dakar',
  sector: 'agroalimentaire',
  country: 'SN',
  employee_count: 15,
  // ...
}
export const FATOU_CARBON_SUMMARY: CarbonSummary = {
  total_tco2: 47.2,
  top_category: 'transport',
  top_category_pct: 62,
  sector: 'agroalimentaire',
  // ...
}
```

**And** un fichier `frontend/tests/e2e/README.md` est cree (~30 lignes) qui explique :
- Comment lancer les tests localement (`npm run test:e2e`)
- Comment debugger (`npm run test:e2e -- --debug`, `--headed`, `--ui`)
- Strategie de mocking (backend entierement mocke, pas de BDD reelle)
- Convention de nommage des specs (`{epic}-{num}-parcours-{prenom}.spec.ts`)
- Ou ajouter de nouvelles fixtures (`fixtures/users.ts`, `fixtures/mock-backend.ts`)

### AC1 : Spec E2E Fatou — preparation et login initial

**Given** le fichier `frontend/tests/e2e/8-1-parcours-fatou.spec.ts` est cree
**When** le test demarre via `test.beforeEach`
**Then** les operations suivantes sont executees dans l'ordre :
1. `await installMockBackend(page, { user: FATOU, companyProfile: FATOU_COMPANY, carbonData: FATOU_CARBON_SUMMARY, chatScenario: 'propose_guided_tour_after_carbon' })`
2. `await page.emulateMedia({ reducedMotion: 'reduce' })` — supprime les animations GSAP pour determinisme
3. `await loginAs(page, FATOU)` — authentification Fatou
4. `await page.goto('/dashboard')` — arrivee sur le dashboard (meme page que la scene d'ouverture PRD)
5. `await page.waitForLoadState('networkidle')`

**And** une assertion verifie que :
- Le bouton flottant est visible : `await expect(page.getByTestId('floating-chat-button')).toBeVisible()`
- Le widget est ferme au depart : `await expect(page.locator('#copilot-widget')).toBeHidden()` (ou assertion equivalente sur `chatWidgetOpen = false`)
- Aucun overlay Driver.js n'est present : `await expect(page.locator('.driver-active')).toHaveCount(0)`

### AC2 : Ouverture du widget + envoi d'un message + reception du consentement

**Given** Fatou est sur `/dashboard` avec le widget ferme
**When** elle clique sur le bouton flottant puis tape et envoie un message dans le chat (« Montre-moi mes resultats carbone s'il te plait »)
**Then** les assertions suivantes passent :
1. `await page.getByTestId('floating-chat-button').click()`
2. `await expect(page.locator('#copilot-widget')).toBeVisible()` — le widget est ouvert
3. `await page.getByRole('textbox', { name: /Posez.*question|message/i }).fill('Montre-moi mes resultats carbone s\'il te plait')` (ou selecteur plus specifique selon `ChatInput.vue`)
4. `await page.getByRole('button', { name: /envoyer/i }).click()` (ou `Enter`)
5. Attendre que la reponse assistant apparaisse dans la conversation : `await expect(page.getByText(/Voulez-vous voir vos resultats carbone/i)).toBeVisible({ timeout: 10_000 })`
6. Le widget interactif de consentement apparait : `await expect(page.getByRole('button', { name: 'Oui, montre-moi' })).toBeVisible()` **ET** `await expect(page.getByRole('button', { name: 'Non merci' })).toBeVisible()`

**And** aucune erreur n'est affichee dans le DOM (`await expect(page.locator('[role="alert"]')).toHaveCount(0)`).

**Note dev** : pour des selectors plus stables, **ajouter** `data-testid="interactive-choice-yes"` et `data-testid="interactive-choice-no"` sur les boutons du `SingleChoiceWidget.vue` quand utilise en mode consentement (ou `data-choice-value="yes"|"no"` genere automatiquement par la valeur du choix). Sous-tache dediee en section Tasks.

### AC3 : Acceptation du guidage + retraction du widget

**Given** le widget interactif de consentement est affiche
**When** Fatou clique sur « Oui, montre-moi »
**Then** les assertions suivantes passent dans l'ordre temporel :
1. `await page.getByRole('button', { name: 'Oui, montre-moi' }).click()` (ou `getByTestId('interactive-choice-yes')` si ajoute)
2. Le widget se retracte en bouton flottant **ou** (si `reducedMotion = 'reduce'`) le widget disparait instantanement : `await expect(page.locator('#copilot-widget')).toBeHidden({ timeout: 2_000 })`
3. Le bouton flottant reste visible : `await expect(page.getByTestId('floating-chat-button')).toBeVisible()`
4. Un overlay Driver.js apparait sur le lien sidebar carbone : `await expect(page.locator('[data-guide-target="sidebar-carbon-link"]')).toBeVisible()` **ET** `await expect(page.locator('.driver-popover, .driver-active-element')).toHaveCount(1)` (au moins 1 element Driver.js actif)
5. Le popover contient le titre « Resultats Empreinte Carbone » : `await expect(page.getByRole('heading', { name: /R.sultats.*Empreinte Carbone/i })).toBeVisible()`
6. Le decompteur est visible et commence a 8 : `await expect(page.getByTestId('countdown-badge')).toContainText(/8|7|6/)` (tolere une lecture a 7 ou 6 si le test est legerement en retard sur le tick)

**And** `uiStore.guidedTourActive === true` est implicitement verifie via le fait que le bouton flottant est en mode `cursor-not-allowed opacity-60` (cf. `FloatingChatButton.vue:18`) — assertion optionnelle via `await expect(page.getByTestId('floating-chat-button')).toHaveClass(/cursor-not-allowed|opacity-60/)`.

### AC4 : Clic sidebar avant expiration du decompteur + navigation + reprise du parcours

**Given** le popover d'entree pointe `[data-guide-target="sidebar-carbon-link"]` avec un decompteur actif
**When** Fatou clique sur le lien sidebar **avant** l'expiration du decompteur (test reaction rapide, < 3s apres l'apparition)
**Then** les assertions suivantes passent :
1. `await page.locator('[data-guide-target="sidebar-carbon-link"]').click()`
2. `await page.waitForURL('**/carbon/results')` avec timeout 5_000ms
3. Le parcours Driver.js **reprend automatiquement** sur `/carbon/results` : `await expect(page.locator('[data-guide-target="carbon-donut-chart"]')).toBeVisible({ timeout: 10_000 })` — le premier popover du parcours pointe le donut
4. Le popover affiche le titre « Repartition de vos emissions » : `await expect(page.getByRole('heading', { name: /R.partition.*.missions/i })).toBeVisible()`
5. Le texte interpole contient les donnees carbone : `await expect(page.locator('.driver-popover')).toContainText(/47.*tCO2e/i)` **ET** `await expect(page.locator('.driver-popover')).toContainText(/transport/i)` **ET** `await expect(page.locator('.driver-popover')).toContainText(/62/i)`

**And** le bouton « Suivant » du popover est visible et cliquable : `await expect(page.getByTestId('popover-next-btn')).toBeVisible()`.

**Rationale** : les placeholders `{{total_tco2}}`, `{{top_category}}`, `{{top_category_pct}}`, `{{sector}}` doivent etre interpoles par `useGuidedTour` a partir du `context` passe dans le marker SSE `__sse_guided_tour__`. Si l'interpolation echoue, on verra `{{total_tco2}}` brut — le test echoue.

### AC5 : Progression sur les popovers successifs + completion du parcours

**Given** le premier popover (donut) est affiche
**When** Fatou clique 2 fois sur « Suivant » pour parcourir donut → benchmark → plan de reduction
**Then** les assertions suivantes passent :
1. **Step 1 (donut)** → clic sur `[data-testid="popover-next-btn"]`
2. **Step 2 (benchmark)** : `await expect(page.locator('[data-guide-target="carbon-benchmark"]')).toBeVisible()` ET le popover contient « Comparaison sectorielle » (titre) et « agroalimentaire » (interpolation `{{sector}}`)
3. Clic suivant → **Step 3 (plan reduction)** : `await expect(page.locator('[data-guide-target="carbon-reduction-plan"]')).toBeVisible()` ET le popover contient « Plan de reduction »
4. Sur le dernier step, le bouton devient « Terminer » (ou equivalent) — clic pour fermer le parcours

**And** apres le clic final :
- `await expect(page.locator('.driver-popover')).toHaveCount(0)` — tous les popovers Driver.js ont disparu
- `await expect(page.getByTestId('floating-chat-button')).toBeVisible()` — le bouton flottant reapparait (FR20)
- Le bouton n'est plus en mode disabled : `await expect(page.getByTestId('floating-chat-button')).not.toHaveClass(/cursor-not-allowed/)`

### AC6 : Message de conclusion dans le chat apres completion

**Given** le parcours est termine et le widget est reapparu
**When** Fatou reouvre le widget
**Then** un message de conclusion est visible dans l'historique de la conversation :
1. `await page.getByTestId('floating-chat-button').click()`
2. `await expect(page.locator('#copilot-widget')).toBeVisible()`
3. `await expect(page.locator('#copilot-widget')).toContainText(/(evaluation ESG|profil de durabilit|completer|continuer)/i)` — un des messages de conclusion suggerant un module suivant (scene finale PRD : « Vous pouvez maintenant lancer votre evaluation ESG... »)

**Note** : ce message peut provenir soit d'un SSE marker emit par le backend a la fin du parcours (pas encore implemente ?), **soit** d'un message pre-existant deja affiche avant le parcours (le widget n'efface pas son historique). Le test doit tolerer les deux sources — **dev decide** de la strategie de mock backend en fonction de ce qui est reellement emis par le backend en production (verifier le comportement avant d'ecrire le mock).

**Fallback acceptable si aucun message n'est emit automatiquement** : remplacer AC6 par une verification que le chat est **fonctionnel** apres le parcours (saisie possible dans le textarea, historique precedent preserve) — c.-a-d. `await expect(page.getByRole('textbox')).toBeEnabled()` + `await expect(page.locator('#copilot-widget')).toContainText('Voulez-vous voir vos resultats carbone')` (le message precedent est toujours la).

### AC7 : Ajout `data-testid` sur les boutons du widget de consentement (prerequis pour AC2/AC3)

**Given** `SingleChoiceWidget.vue` rend dynamiquement les boutons de choix
**When** on etend le composant pour supporter des selecteurs E2E stables
**Then** chaque bouton de choix **recoit** un `data-testid` calcule depuis la valeur (slugifiee) :

```vue
<button
  v-for="choice in choices"
  :key="choice.value"
  :data-testid="`interactive-choice-${choice.value}`"
  :data-choice-value="choice.value"
  ...
>
  {{ choice.label }}
</button>
```

**And** la modification **n'affecte pas** le rendu visuel ni l'accessibilite (aria-labels, role radio/checkbox conservees).

**And** les **tests Vitest existants** de `SingleChoiceWidget.vue` (dans `frontend/tests/components/`) passent toujours — si un test verifie la structure HTML complete avec snapshot, il faudra **mettre a jour** le snapshot. Zero regression fonctionnelle.

**Rationale** : sans `data-testid`, les tests E2E dependent des labels FR des choix qui peuvent changer (« Oui, montre-moi » → « Oui, continuer », etc.) — couplage fragile. `data-testid="interactive-choice-yes"` est stable par design (base sur la `value` du choix, pas le `label`).

**Alternative acceptable** : utiliser `getByRole('button', { name: ... })` avec des labels fixes — **choix du dev** si l'ajout de `data-testid` casse trop de tests unitaires existants, mais **preferer** `data-testid` pour la pattern E2E de l'epic 8 entier (reutilisable dans 8.2 parcours Moussa qui verifie le bouton « Non merci »).

### AC8 : Script `npm run test:e2e` lance la spec Fatou avec succes + 0 regression Vitest

**Given** l'infrastructure E2E est en place (AC0 + AC1-AC6 implementes)
**When** on execute `cd frontend && npm run test:e2e -- 8-1-parcours-fatou` (ou `--project=chromium-desktop`)
**Then** :
1. Playwright demarre le `webServer` Nuxt (`npm run dev`) si pas deja lance
2. La spec passe sans erreur ni timeout : **1 test greened, 0 failed, 0 flaky**
3. Duree totale **< 60s** en local (hors demarrage webServer qui est ~10-30s)

**And** **zero regression** sur la suite Vitest : `cd frontend && npm run test` → 330+ tests verts (incluant les tests potentiellement modifies de `SingleChoiceWidget` si AC7 a impacte des snapshots).

**And** `npx nuxi typecheck` (ou `npx tsc --noEmit`) passe sans nouvelle erreur TypeScript sur les fichiers crees (`tests/e2e/**/*.ts`, `playwright.config.ts`) ni sur les fichiers modifies (`SingleChoiceWidget.vue`).

**And** si Playwright n'a pas encore telecharge son navigateur Chromium, le dev doit executer `npx playwright install chromium --with-deps` (commande a documenter dans `tests/e2e/README.md`).

### AC9 : Tests robustes et deterministes (anti-flake)

**Given** les assertions E2E peuvent etre instables a cause du SSE, des animations et du timing du decompteur
**When** on ecrit les tests, on applique les **bonnes pratiques** suivantes :

1. **Pas de `page.waitForTimeout(N)`** en dur dans le code (sauf cas exceptionnel documente) — utiliser `expect(...).toBeVisible({ timeout })` qui re-essaye jusqu'au succes.
2. **Timeouts explicites** pour les operations SSE : `{ timeout: 10_000 }` sur les `expect` post-envoi de message (le mock SSE a quelques chunks a emettre).
3. **Pas de selecteurs CSS fragiles** (ex. `.bg-amber-50 > div:nth-child(2)`) — preferer `getByTestId`, `getByRole`, `getByText`.
4. **`reducedMotion: 'reduce'`** actif (AC1) pour supprimer la variabilite des animations GSAP.
5. **Assertions auto-retry de Playwright** : `expect(page.locator(...)).toBeVisible()` retry automatiquement jusqu'au timeout — **ne jamais** wrapper dans un `if (await locator.isVisible())` manuel.
6. **Mock SSE avec `createSSEResponse`** : les chunks sont envoyes synchronement (pas de `delayMs`) pour minimiser la latence du test. Si un test specifique veut verifier le streaming progressif, il peut passer `delayMs: 100`.
7. **`page.route()` installe AVANT `page.goto()`** : systematiquement dans `beforeEach` avant tout `goto`.

**And** le test est **repete 3 fois localement** (`npm run test:e2e -- --repeat-each=3 8-1-parcours-fatou`) et passe 3/3 sans flake. Cette verification fait partie de la validation dev avant le passage en `review`.

### AC10 : Documentation traceabilite + decisions design

**Given** la story est complete
**When** on lit la section `## Dev Notes` en fin de story
**Then** elle contient un tableau « AC → fichier(s) / zone / test(s) » (pattern stories 7.1-7.3).

**And** les **decisions de design** suivantes sont documentees dans Completion Notes :
- Pourquoi backend mocke via `page.route()` plutot qu'un backend reel + BDD de test.
- Pourquoi `workers: 1` et `fullyParallel: false` dans `playwright.config.ts`.
- Pourquoi `reducedMotion: 'reduce'` en defaut sur tous les tests de l'epic 8.
- Pourquoi choix login programmatique vs UI (si login UI retenu, documenter le temps par test).
- Choix du placement `tests/e2e/` vs `e2e/` racine (vs. placement dans chaque module).
- Structure de la fixture `installMockBackend` : comment l'etendre pour les stories 8.2-8.6 sans la reecrire.

## Tasks / Subtasks

- [x] Task 1 : Infrastructure Playwright — config + structure dossier + README (AC: #0)
  - [x] 1.1 Creer `frontend/playwright.config.ts` avec le contenu specifie AC0 (+ port dedie 4321 pour eviter les conflits avec un dev server tiers occupant 3000)
  - [x] 1.2 Creer la structure `frontend/tests/e2e/fixtures/`
  - [x] 1.3 Creer `frontend/tests/e2e/README.md`
  - [x] 1.4 Mettre a jour `frontend/vitest.config.ts` : `test.exclude` inclut `'tests/e2e/**'`
  - [x] 1.5 `npm run test:e2e --list` liste 1 test (sans erreur)
  - [x] 1.6 `npx playwright install chromium` documente dans README

- [x] Task 2 : Fixtures auth + utilisateurs + data (AC: #0)
  - [x] 2.1 Creer `frontend/tests/e2e/fixtures/users.ts` — `FATOU`, `FATOU_COMPANY`, `FATOU_CARBON_SUMMARY`, `FATOU_DASHBOARD_SUMMARY`
  - [x] 2.2 Creer `frontend/tests/e2e/fixtures/auth.ts` avec `loginAs(page, user)` — injection tokens localStorage via `page.addInitScript` (plus rapide et deterministe qu'un login UI, decision documentee en commentaire)
  - [x] 2.3 Verifie : `loginAs(page, FATOU)` + `page.goto('/dashboard')` arrive sur le dashboard sans redirection `/login` (validation via la spec principale — le test passe les assertions AC1)

- [x] Task 3 : Helper SSE streams (AC: #0)
  - [x] 3.1 Creer `frontend/tests/e2e/fixtures/sse-stream.ts` avec `createSSEResponse(events)` — retourne `{ body: string (data: lignes), headers, contentType }`. Note dev : le vrai format SSE du projet est `data: {json}\n\n` avec event.type dans le JSON, PAS des markers HTML `<!--SSE:...-->`. Helper adapte au format reel.
  - [x] 3.2 Helpers haut niveau : `sseAssistantMessageWithConsent({questionId, conversationId, messageId, ...})` et `sseGuidedTourAcceptanceResponse({tourId, context, messageId, ...})`
  - [x] 3.3 Helpers valides via leur utilisation dans la spec (aucun test Vitest dedie)

- [x] Task 4 : Mock backend — `installMockBackend` (AC: #0)
  - [x] 4.1 Creer `frontend/tests/e2e/fixtures/mock-backend.ts` avec la signature specifiee
  - [x] 4.2 Routes implementees (chemins reels decouverts via grep composables) :
    - `POST/GET /api/auth/login`, `GET /api/auth/me`, `POST /api/auth/refresh`, `GET /api/auth/detect-country`
    - `GET /api/company/profile`, `GET /api/company/profile/completion`
    - `GET /api/dashboard/summary`
    - `GET /api/carbon/assessments(?query)`, `GET /api/carbon/assessments/{id}`, `GET /api/carbon/assessments/{id}/summary`, `GET /api/carbon/benchmarks/{sector}`
    - `GET/POST /api/chat/conversations`, `PATCH/DELETE /api/chat/conversations/{id}`, `GET /api/chat/conversations/{id}/interactive-questions`
    - `GET/POST /api/chat/conversations/{id}/messages` (SSE stream scripte selon `chatScenario`)
    - `POST /api/chat/interactive-questions/{id}/abandon`
  - [x] 4.3 Catch-all 404 + warn console pour route inconnue — **inscrite EN PREMIER** dans `installMockBackend` pour que Playwright l'evalue en DERNIER (Playwright LIFO). Bug correcte lors des premiers runs.
  - [x] 4.4 Extension point `options.extraRoutes` inscrit EN DERNIER (= evalue en premier) pour que les stories 8.2-8.6 puissent override.

- [x] Task 5 : Patch `SingleChoiceWidget.vue` + `InteractiveQuestionInputBar.vue` — ajout `data-testid` (AC: #7)
  - [x] 5.1 Patcher `frontend/app/components/chat/SingleChoiceWidget.vue` — ajout `data-testid="interactive-choice-{option.id}"` + `data-choice-value="{option.id}"` sur chaque bouton QCU
  - [x] 5.2 **DECOUVERTE CRITIQUE** : les questions `pending` sont en realite rendues via `InteractiveQuestionInputBar.vue` (bottom sheet), PAS par `SingleChoiceWidget`. ChatMessage.vue:149 filtre `state !== 'pending'`. J'ai donc patche AUSSI `InteractiveQuestionInputBar.vue` (QCU + QCM inline) pour les memes data-testid. SingleChoiceWidget reste patche pour les etats finaux (historique).
  - [x] 5.3 Aucun test Vitest existant sur SingleChoiceWidget ni InteractiveQuestionInputBar → zero snapshot a mettre a jour
  - [x] 5.4 Ajout aussi `data-testid="chat-textarea"` + `data-testid="chat-send-button"` sur `ChatInput.vue` — evite la fragilite d'un selecteur par role qui matche d'autres boutons du widget.

- [ ] Task 6 : Spec E2E principale — `8-1-parcours-fatou.spec.ts` (AC: #1-#6, #9)
  - [ ] 6.1 Creer `frontend/tests/e2e/8-1-parcours-fatou.spec.ts`
  - [ ] 6.2 Structure de base :
    ```typescript
    import { test, expect } from '@playwright/test'
    import { loginAs } from './fixtures/auth'
    import { installMockBackend } from './fixtures/mock-backend'
    import { FATOU, FATOU_COMPANY, FATOU_CARBON_SUMMARY } from './fixtures/users'

    test.describe('Parcours Fatou — guidage propose et accepte (multi-pages)', () => {
      test.beforeEach(async ({ page }) => {
        await installMockBackend(page, {
          user: FATOU,
          companyProfile: FATOU_COMPANY,
          carbonData: FATOU_CARBON_SUMMARY,
          chatScenario: 'propose_guided_tour_after_carbon',
        })
        await page.emulateMedia({ reducedMotion: 'reduce' })
        await loginAs(page, FATOU)
        await page.goto('/dashboard')
        await page.waitForLoadState('networkidle')
      })

      test('Fatou ouvre le widget, envoie un message, accepte le guidage, navigue vers /carbon/results et parcourt les popovers jusqu\'a la fin', async ({ page }) => {
        // AC1 : preparation verifiee par beforeEach
        await expect(page.getByTestId('floating-chat-button')).toBeVisible()

        // AC2 : ouverture + envoi + consentement
        await page.getByTestId('floating-chat-button').click()
        await expect(page.locator('#copilot-widget')).toBeVisible()
        await page.getByRole('textbox').first().fill('Montre-moi mes resultats carbone s\'il te plait')
        await page.getByRole('button', { name: /envoyer/i }).click()
        await expect(page.getByText(/Voulez-vous voir vos resultats carbone/i)).toBeVisible({ timeout: 10_000 })
        await expect(page.getByTestId('interactive-choice-yes')).toBeVisible()

        // AC3 : acceptation + retraction + popover entryStep
        await page.getByTestId('interactive-choice-yes').click()
        await expect(page.locator('#copilot-widget')).toBeHidden({ timeout: 2_000 })
        await expect(page.locator('[data-guide-target="sidebar-carbon-link"]')).toBeVisible()
        await expect(page.locator('.driver-popover')).toHaveCount(1)
        await expect(page.getByRole('heading', { name: /R.sultats.*Empreinte Carbone/i })).toBeVisible()
        await expect(page.getByTestId('countdown-badge')).toBeVisible()

        // AC4 : clic sidebar + navigation + reprise parcours
        await page.locator('[data-guide-target="sidebar-carbon-link"]').click()
        await page.waitForURL('**/carbon/results', { timeout: 5_000 })
        await expect(page.locator('[data-guide-target="carbon-donut-chart"]')).toBeVisible({ timeout: 10_000 })
        await expect(page.locator('.driver-popover')).toContainText(/47.*tCO2e/i)
        await expect(page.locator('.driver-popover')).toContainText(/transport/i)
        await expect(page.locator('.driver-popover')).toContainText(/62/i)

        // AC5 : progression sur les 3 popovers + completion
        await page.getByTestId('popover-next-btn').click()
        await expect(page.locator('[data-guide-target="carbon-benchmark"]')).toBeVisible()
        await expect(page.locator('.driver-popover')).toContainText(/agroalimentaire/i)
        await page.getByTestId('popover-next-btn').click()
        await expect(page.locator('[data-guide-target="carbon-reduction-plan"]')).toBeVisible()
        await page.getByTestId('popover-next-btn').click() // Terminer
        await expect(page.locator('.driver-popover')).toHaveCount(0)
        await expect(page.getByTestId('floating-chat-button')).toBeVisible()
        await expect(page.getByTestId('floating-chat-button')).not.toHaveClass(/cursor-not-allowed/)

        // AC6 : widget reapparait et chat fonctionnel
        await page.getByTestId('floating-chat-button').click()
        await expect(page.locator('#copilot-widget')).toBeVisible()
        await expect(page.getByRole('textbox').first()).toBeEnabled()
      })
    })
    ```
  - [ ] 6.3 Adapter les selectors au **vrai DOM** du projet apres lecture de `FloatingChatWidget.vue`, `ChatInput.vue`, `GuidedTourPopover.vue` (les `getByRole('button', { name: /envoyer/i })` peuvent necessiter un label plus specifique ou un `data-testid` ajoute en cours de dev).
  - [ ] 6.4 Si un selecteur doit etre ajoute au code source (ex. sur `ChatInput.vue` pour le bouton Envoyer), le faire sous forme de `data-testid="chat-send-button"` (pattern coherent avec l'existant).

- [x] Task 7 : Validation anti-flake + typecheck (AC: #8, #9)
  - [x] 7.1 `npm run test:e2e -- 8-1-parcours-fatou` → **green (12.0s)**
  - [x] 7.2 `npm run test:e2e -- --repeat-each=3 8-1-parcours-fatou` → **3/3 green (12.1s, 10.4s, 10.3s — 36.8s total), 0 flaky**
  - [x] 7.3 `npm run test -- --run` → **354/354 Vitest verts, 0 regression** (35 fichiers de test)
  - [x] 7.4 `npx tsc --noEmit` → aucune nouvelle erreur TS dans les fichiers crees/modifies (6 erreurs pre-existantes dans useChat/useFocusTrap/useGuidedTour non liees a cette story)

- [x] Task 8 : Documentation traceabilite (AC: #10)
  - [x] 8.1 Tableau AC → fichier → test complete dans Dev Notes (ajuste pour refleter les ecarts documents ci-dessous)
  - [x] 8.2 Decisions design documentees en Completion Notes ci-dessous
  - [x] 8.3 `sprint-status.yaml` : `ready-for-dev` → `in-progress` (en cours de dev) → `review` (a la completion)
  - [x] 8.4 File List completee ci-dessous

## Dev Notes

### Contexte — premiere story de l'epic 8 (Tests d'integration end-to-end)

L'epic 8 valide les 5 parcours utilisateur du PRD via Playwright :
- **8.1 Fatou** (cette story) — guidage propose et accepte, **multi-pages** — scenario le plus riche, valide la chaine complete
- 8.2 Moussa — guidage refuse, chat contextuel superpose
- 8.3 Aminata — guidage demande explicitement (sans consentement)
- 8.4 Ibrahim — decompteur expire, navigation auto
- 8.5 Aissatou — detection mobile, degradation gracieuse
- 8.6 Tests de non-regression globaux

**Cette story est FOUNDATIONNELLE** : elle instaure l'infrastructure Playwright (config, fixtures, mocks) qui sera reutilisee et etendue par les 5 stories suivantes. **L'attention portee aux points d'extension (`options.extraRoutes`, helpers SSE reutilisables) est critique** — toute friction dans la fixture `installMockBackend` se reportera sur 5 specs.

### Mapping AC → fichier → test (pattern story 7.1-7.3)

| AC | Fichier(s) impacte(s) | Zone / objet | Test / assertion |
|---|---|---|---|
| AC0 Config | `playwright.config.ts` (CREER), `vitest.config.ts` (MODIFIER exclude) | Config racine frontend | `npm run test:e2e --list` retourne sans erreur |
| AC0 Fixtures | `tests/e2e/fixtures/{users,auth,mock-backend,sse-stream}.ts` (CREER), `tests/e2e/README.md` (CREER) | Fixtures reutilisables epic 8 | Usage dans spec 8.1 |
| AC1 Login + dashboard | `tests/e2e/8-1-parcours-fatou.spec.ts` `beforeEach` | Smoke test initial | `expect(floating-chat-button).toBeVisible()` |
| AC2 Envoi message + consentement | Meme spec | Scenario chat | `expect(text 'Voulez-vous...').toBeVisible()`, `expect(interactive-choice-yes).toBeVisible()` |
| AC3 Acceptation + retraction | Meme spec | Transition widget → Driver.js | `expect(copilot-widget).toBeHidden()`, `expect(driver-popover).toHaveCount(1)`, `expect(countdown-badge).toBeVisible()` |
| AC4 Clic sidebar + navigation | Meme spec | Transition multi-pages | `waitForURL('/carbon/results')`, `expect(carbon-donut-chart).toBeVisible()`, interpolation `47 tCO2e`, `transport`, `62` |
| AC5 Progression popovers | Meme spec | Steps Driver.js | `expect(carbon-benchmark).toBeVisible()`, `expect(carbon-reduction-plan).toBeVisible()`, `expect(driver-popover).toHaveCount(0)` post-completion |
| AC6 Message conclusion | Meme spec | Reapparition widget | `expect(floating-chat-button).toBeVisible()` post-parcours, chat fonctionnel |
| AC7 `data-testid` sur choix | `components/chat/SingleChoiceWidget.vue` (MODIFIER) | Selecteurs stables | Tests Vitest existants passent |
| AC8 npm run test:e2e passe | — | Validation globale | `npm run test:e2e -- 8-1` = 1 passed, `npm run test` = 330+ passed |
| AC9 Anti-flake | Meme spec | Timeouts + reducedMotion | `--repeat-each=3` = 3/3 passed |
| AC10 Doc | Cette story (Dev Notes + Completion Notes) | — | Revue manuelle |

### Selectors critiques (deja presents dans le code — pas a creer)

| Selector | Fichier source | Ligne | Usage dans test |
|---|---|---|---|
| `[data-testid="floating-chat-button"]` | `components/copilot/FloatingChatButton.vue` | 15 | AC1, AC3, AC5, AC6 |
| `[data-guide-target="sidebar-carbon-link"]` | `components/layout/AppSidebar.vue` | 61 (genere) | AC3, AC4 |
| `[data-guide-target="carbon-donut-chart"]` | `pages/carbon/results.vue` | 219 | AC4 |
| `[data-guide-target="carbon-benchmark"]` | `pages/carbon/results.vue` | 337 | AC5 |
| `[data-guide-target="carbon-reduction-plan"]` | `pages/carbon/results.vue` | 280 | AC5 |
| `[data-testid="countdown-badge"]` | `components/copilot/GuidedTourPopover.vue` | 128 | AC3 |
| `[data-testid="popover-next-btn"]` | `components/copilot/GuidedTourPopover.vue` | 137 | AC5 |
| `[data-testid="popover-close-btn"]` | `components/copilot/GuidedTourPopover.vue` | 100 | (pas utilise 8.1 — prevu 8.4/8.5) |
| `#copilot-widget` | `components/copilot/FloatingChatWidget.vue` | (racine widget) | AC1, AC2, AC3, AC6 |

### Selectors **a creer** (Task 5 de cette story)

| Selector | Fichier cible | Valeur |
|---|---|---|
| `[data-testid="interactive-choice-yes"]` | `components/chat/SingleChoiceWidget.vue` | Genere depuis `choice.value === 'yes'` |
| `[data-testid="interactive-choice-no"]` | Idem | Genere depuis `choice.value === 'no'` |

### Markers SSE a emettre par le mock backend (`mock-backend.ts`)

**Scenario `propose_guided_tour_after_carbon`** — `POST /api/chat/messages` :

```
Je vais vous aider ! Votre empreinte carbone est de 47.2 tCO2e, principalement liee au transport (62%).

<!--SSE:{"__sse_interactive_question__":true,"id":"iq-tour-consent-001","variant":"qcu","prompt":"Voulez-vous voir vos resultats carbone detailles avec le plan de reduction ?","choices":[{"value":"yes","label":"Oui, montre-moi"},{"value":"no","label":"Non merci"}],"allow_answer_elsewhere":false}-->
```

**Scenario `propose_guided_tour_after_carbon`** — `POST /api/chat/interactive-questions/iq-tour-consent-001/answer` avec `choice_value === 'yes'` :

```
Parfait, je vous guide vers vos resultats carbone detailles.

<!--SSE:{"__sse_guided_tour__":true,"tour_id":"show_carbon_results","context":{"total_tco2":47.2,"top_category":"transport","top_category_pct":62,"sector":"agroalimentaire"}}-->
```

**Important** : le format exact des markers **doit** correspondre a celui consomme par `useChat.ts` — **verifier** en lisant `useChat.ts:828-860` (marker `__sse_guided_tour__`) et l'equivalent pour `__sse_interactive_question__` (probablement meme fichier). Si le format reel differe (ex. cle `question_id` au lieu de `id`), **corriger** le mock en consequence.

### Endpoints API a mocker (decouverts via grep dans `frontend/app/composables/`)

Le dev doit **grep** les composables suivants pour recuperer les chemins exacts des endpoints utilises lors du chargement de `/dashboard` et `/carbon/results` :

```bash
grep -rn "apiFetch\|apiFetchBlob\|\$fetch" frontend/app/composables/ | grep -E '/api/'
```

Liste attendue (non exhaustive — le dev doit la completer) :
- `useAuth` : `/api/auth/login`, `/api/auth/me`, `/api/auth/refresh`
- `useCompanyProfile` : `/api/company-profile` (verifier le chemin exact)
- `useCarbon` : `/api/carbon/summary`, `/api/carbon/bilans`, `/api/carbon/benchmark` (verifier)
- `useDashboard` : `/api/dashboard/summary` (verifier)
- `useChat` : `/api/chat/messages`, `/api/chat/conversations`, `/api/chat/interactive-questions/*/answer`

**Pour tout endpoint non liste mais appele par l'app** : le mock route par defaut (AC0 Task 4.3) renvoie 404 + log — le dev verra le warning et pourra ajouter l'endpoint manquant.

### Conventions de messages FR (a preserver)

| Situation | Message affiche | Source |
|---|---|---|
| Proposition guidage post-carbone | `"Voulez-vous voir vos resultats carbone detailles avec le plan de reduction ?"` | Mock `chatScenario` |
| Bouton « Oui » consentement | `"Oui, montre-moi"` | Mock + `SingleChoiceWidget` |
| Bouton « Non » consentement | `"Non merci"` | Mock + `SingleChoiceWidget` |
| Titre popover entryStep | `"Resultats Empreinte Carbone"` | `registry.ts:91` (fichier source) |
| Titre popover step 1 | `"Repartition de vos emissions"` | `registry.ts:64` |
| Titre popover step 2 | `"Comparaison sectorielle"` | `registry.ts:72` |
| Titre popover step 3 | `"Plan de reduction"` | `registry.ts:80` |
| Texte interpole donut | contient `"47.2 tCO2e"`, `"transport"`, `"62%"` | Interpolation `useGuidedTour` |

**Accents FR obligatoires** (convention CLAUDE.md) — certains textes au-dessus ont ete ecrits sans accents pour eviter les conflits de rendu en code snippet, mais les **assertions** utilisent `/regex/i` case-insensitive avec optionnellement `.`-wildcards pour tolerer accentuation et bruit typographique : `/R.partition.*.missions/i`.

### Architecture compliance

Cette story **n'introduit aucune nouvelle dependance** (Playwright 1.49 deja dans `devDependencies`) et **ne modifie pas** l'architecture runtime — elle ajoute uniquement :
- Infrastructure de test (`playwright.config.ts`, `tests/e2e/**`)
- Un selector `data-testid` dans `SingleChoiceWidget.vue` (non-breaking, non-visuel)

Respect des conventions projet :
- **Dark mode** : non applicable (tests invisibles pour l'utilisateur, mais les composants testes doivent fonctionner en dark mode — non verifie par 8.1, potentiellement par 8.5)
- **Dossier `components/`** : inchange (seul `SingleChoiceWidget.vue` modifie minimalement)
- **PascalCase sans prefixe** : respecte
- **TypeScript strict** : tous les fichiers `tests/e2e/**/*.ts` sont typed strict

### Library/framework requirements

| Dependance | Version | Etat | Commande |
|---|---|---|---|
| `@playwright/test` | `^1.49.0` | **Deja installee** (`frontend/package.json:29`) | Aucune |
| Chromium (navigateur) | Fourni par Playwright | **A telecharger une fois** | `npx playwright install chromium --with-deps` |
| `happy-dom` | `^20.8.9` | Deja installe (Vitest) — **non utilise par Playwright** | Aucune |

**Pas d'installation de nouveau package npm.** Pas de modification de `package.json` sauf si un script d'aide additionnel est ajoute (ex. `"test:e2e:ui": "playwright test --ui"` — optionnel).

### File structure requirements

```
frontend/
├── playwright.config.ts                                    [CREER — AC0]
├── vitest.config.ts                                        [MODIFIER — exclude e2e]
├── package.json                                            [INCHANGE]
├── app/
│   └── components/
│       └── chat/
│           └── SingleChoiceWidget.vue                      [MODIFIER — data-testid — AC7]
└── tests/
    ├── e2e/                                                [CREER — nouveau dossier]
    │   ├── README.md                                       [CREER — AC0]
    │   ├── 8-1-parcours-fatou.spec.ts                      [CREER — spec principale]
    │   └── fixtures/
    │       ├── auth.ts                                     [CREER — loginAs]
    │       ├── users.ts                                    [CREER — FATOU + fixtures]
    │       ├── mock-backend.ts                             [CREER — installMockBackend]
    │       └── sse-stream.ts                               [CREER — createSSEResponse]
    ├── components/                                         [INCHANGE]
    ├── composables/                                        [INCHANGE]
    └── setup.ts                                            [INCHANGE]
```

### Testing standards (AC8, AC9)

- **Framework E2E** : Playwright 1.49 (projet `chromium-desktop`)
- **Viewport** : 1280x800 (desktop >= 1024px — seuil widget flottant)
- **Reduced motion** : `prefers-reduced-motion: reduce` force pour determinisme
- **Workers** : 1 (sequentiel) pour stabiliser SSE/guidage — pas de parallelisation au niveau des tests
- **Retries** : 2 en CI, 0 en local (pour reveler les flakes)
- **Timeout global** : 30s par test, 5s par `expect` auto-retry
- **Trace** : `on-first-retry` — permet le debug post-mortem d'un test flaky
- **Screenshot** : `only-on-failure`
- **Video** : `retain-on-failure`

**Commandes principales** (documenter dans `tests/e2e/README.md`) :

```bash
npx playwright install chromium --with-deps    # Une fois, post-clone
npm run test:e2e                               # Lance tous les tests
npm run test:e2e -- 8-1-parcours-fatou         # Un seul fichier
npm run test:e2e -- --headed                   # Voir le navigateur
npm run test:e2e -- --debug                    # Mode debug pas-a-pas
npm run test:e2e -- --ui                       # Interface interactive Playwright
npm run test:e2e -- --repeat-each=3            # Anti-flake check
npx playwright show-report                     # Voir le rapport HTML post-run
```

### Previous story intelligence (story 7.3 — resilience SSE)

Story 7.3 a introduit `isConnected` + `ConnectionStatusBadge.vue` + classification `classifyFetchError`. **Impact sur 8.1** :

- **Aucun impact direct** sur le parcours Fatou (flux nominal, pas de perte de connexion)
- **Mais** le mock backend doit repondre **200 OK** sur tous les appels **sans throw `TypeError: Failed to fetch`** — sinon l'indicateur « Reconnexion... » apparaitra et le test pourrait echouer sur l'assertion « chat fonctionnel » (AC6)
- **Pattern a reutiliser** : Story 7.3 a ajoute un `data-testid="chat-input-hint"` dans `ChatInput.vue` (ligne 98) — meme pattern `data-testid` a suivre pour 8.1 (`interactive-choice-yes|no`)

### Git intelligence (5 derniers commits)

- `ad169c3` : 7-2-renouvellement-jwt-transparent-pendant-le-guidage: done + 7-3-resilience-sse: done
- `a58f6d1` : 7-1-gestion-des-elements-dom-absents-et-timeout-de-chargement: done
- `2278f35` : 6-4-frequence-adaptative-des-propositions-de-guidage: done
- `2bc3e15` : 6-3-consentement-via-widget-interactif-et-declenchement-direct: done
- `b7f6d62` : 6-1-tool-langchain-trigger-guided-tour-et-marker-sse: done

**Insights** :
- **Le flux `trigger_guided_tour` tool + marker SSE** est implemente et testable cote frontend uniquement (le tool cote backend est pas teste par 8.1 — on ne passe pas par lui, on moque directement le SSE).
- **Le consentement via widget QCU (6.3)** est la feature sous-jacente utilisee par AC2 — **verifier** que le widget QCU est toujours rendu dans la vue chat quand `interactive_question.state === 'pending'` (devrait l'etre, feature 018).
- **La frequence adaptative (6.4)** n'affecte pas 8.1 — le test ne boucle pas sur plusieurs propositions.

### Latest tech information — Playwright 1.49 (stable, pas de breaking recent)

- **`@playwright/test` 1.49** est stable (sortie octobre 2024, pas de breaking changes majeurs depuis).
- **`test.beforeEach`** supporte l'ordre d'installation des routes avant goto (non-blocker — simplement appeler avant).
- **`page.route()`** fonctionne avec patterns glob (`**/api/**`) et regex (`/\\/api\\//`).
- **`page.emulateMedia({ reducedMotion })`** disponible depuis 1.26 (2022) — stable.
- **`page.getByTestId()`** respecte la config `testIdAttribute` (defaut `data-testid`) — **verifier** que le projet n'override pas cet attribut (aucun override attendu).
- **`createSSEResponse`** custom : Playwright 1.49 supporte `route.fulfill({ body: ReadableStream })` via le `body` parameter accepting Buffer OR Uint8Array — **pour un ReadableStream**, il faut lire tout le stream en memoire et passer le Buffer concatene (OU utiliser `route.fulfill({ body: buffer })` chunk par chunk n'est pas directement supporte — utiliser `route.continue({ url: '...' })` vers un serveur local mockant le SSE, OU plus simple : **bufferiser tous les chunks** dans un `Uint8Array` unique et passer `body: Buffer.concat(chunks)`). **Choix recommande pour 8.1** : bufferisation complete (pas de vrai streaming cote test — l'interet pedagogique est le comportement final, pas l'experience progressive). Si un test specifique veut verifier le rendu progressif, **etendre** le helper avec un mode `streaming: true` qui utilise `page.route` + `route.fulfill` avec `Content-Type: text/event-stream` et envoie les chunks en serial (plus complexe, reporter a 8.6 si besoin).

### Project Structure Notes

Alignement avec la structure unifiee :
- `frontend/tests/e2e/` s'integre dans le dossier `tests/` existant (parallele a `components/`, `composables/`, etc.)
- Pas de conflit avec Nuxt 4 qui exige `app/` pour le code source — les tests restent dans `tests/`
- `playwright.config.ts` est a la racine `frontend/` (convention Playwright, pas dans `app/`)
- `vitest.config.ts` existe deja a la racine — il faut juste y exclure `tests/e2e/**`

Aucune variance ou conflit detecte.

### References

- PRD : [Source: _bmad-output/planning-artifacts/prd.md#FR14, FR20, FR22, FR23, NFR17]
- Architecture E2E : [Source: _bmad-output/planning-artifacts/architecture.md:96 (stack), ligne 1022 (lacune documentee)]
- Epic 8 + Story 8.1 : [Source: _bmad-output/planning-artifacts/epics.md:1189-1225]
- Parcours Fatou (PRD) : [Source: _bmad-output/planning-artifacts/architecture.md:83-93]
- Registre tours : [Source: frontend/app/lib/guided-tours/registry.ts:58-96 (show_carbon_results)]
- Selectors existants : [Source: frontend/app/components/copilot/FloatingChatButton.vue:15, components/copilot/GuidedTourPopover.vue:100-137, components/layout/AppSidebar.vue:61, pages/carbon/results.vue:219,280,337]
- Pattern SSE POST-based : [Source: frontend/app/composables/useChat.ts:216-224, 604-614, 828-860]
- Story precedente (7.3) : [Source: _bmad-output/implementation-artifacts/7-3-resilience-sse-et-indicateur-de-reconnexion.md]
- Package deja installe : [Source: frontend/package.json:29 (`@playwright/test`), ligne 13 (`test:e2e` script)]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6[1m])

### Debug Log References

Sequence de validation (tous greens finaux) :

1. `npx playwright test --list` → 1 test detecte (syntax valide)
2. `npx tsc --noEmit` : 0 nouvelle erreur TS sur les fichiers crees/modifies (6 erreurs pre-existantes non liees)
3. `npm run test -- --run` : 354/354 Vitest verts (35 files, 5.55s)
4. `npm run test:e2e -- 8-1-parcours-fatou` : 1 passed (12.0s)
5. `npm run test:e2e -- --repeat-each=3 8-1-parcours-fatou` : 3/3 passed (36.8s)

**Bugs resolus pendant le dev** :

- **LIFO Playwright** : la route catch-all `/.*\/api\/.*/` inscrite en dernier interceptait toutes les requetes AVANT les routes specifiques. Corrige en inscrivant la catch-all EN PREMIER dans `installMockBackend`. Playwright evalue les routes en LIFO (docs officielles).
- **Port 3000 occupe** : un autre dev server Nuxt (projet `uafricas_frontend`) tournait sur le port 3000. `reuseExistingServer: true` reutilisait ce serveur au lieu de lancer celui d'esg_mefali. Corrige en configurant un port dedie 4321 (override via `PLAYWRIGHT_PORT` env var).
- **Widget de consentement rendu par `InteractiveQuestionInputBar`, pas `SingleChoiceWidget`** : la story AC7 ciblait `SingleChoiceWidget`, mais en realite les questions `pending` sont rendues par `InteractiveQuestionInputBar` (bottom sheet) — `ChatMessage.vue:149` filtre `state !== 'pending'`. J'ai patche les deux composants pour coherence.

### Completion Notes List

**Implementation delivrees (AC0 a AC10)** :

- ✅ **AC0 Infrastructure Playwright complete** : `playwright.config.ts` (port 4321 dedie), `vitest.config.ts` exclut `tests/e2e/**`, 4 fixtures TypeScript strict, README explicatif.
- ✅ **AC1-AC6 Parcours Fatou end-to-end** : spec qui deroule tout le scenario (login → dashboard → ouverture widget → envoi message → consentement → acceptation → retraction → navigation sidebar → 3 popovers carbone → completion → chat fonctionnel).
- ✅ **AC7 Selecteurs stables** : `data-testid="interactive-choice-{id}"` sur SingleChoiceWidget ET InteractiveQuestionInputBar (decouverte critique), plus `chat-textarea`/`chat-send-button` sur ChatInput.
- ✅ **AC8 Validation** : test green, Vitest 354/354 vert, typecheck clean sur les nouveaux fichiers.
- ✅ **AC9 Anti-flake** : 3/3 passes en repeat-each=3 (aucune reelle instabilite), reducedMotion actif, timeouts explicites, selectors par testId.
- ✅ **AC10 Documentation** : tableau AC→fichier→test et decisions design ci-dessous.

**Decisions de design justifiees** :

1. **Backend integralement mocke via `page.route()`** plutot qu'un backend reel + BDD de test :
   - Isolation : pas de dependance Postgres/Redis/OpenRouter/MinIO
   - Rapidite : <15s par test (vs ~2min pour un backend reel avec migration + seeding)
   - CI-friendly : le workflow GH Actions n'a pas besoin de Docker Compose
   - Le but de l'epic 8 est l'integration frontend — les 935+ tests pytest couvrent le backend

2. **`workers: 1` + `fullyParallel: false`** :
   - Les tests partagent l'etat DOM (overlays Driver.js, animations GSAP)
   - La parallelisation provoquerait des flakes sur `uiStore.guidedTourActive` partage
   - Cout : tests sequentiels (~15s chacun) mais deterministes

3. **`reducedMotion: 'reduce'` par defaut dans chaque beforeEach** :
   - Supprime 500-800ms d'animations GSAP (widget open/close, retract, popover slide)
   - Rend le timing des assertions `toBeVisible/toBeHidden` deterministe
   - `GuidedTourPopover.css` et `InteractiveQuestionInputBar.scoped` respectent `@media (prefers-reduced-motion)`

4. **Login programmatique via `page.addInitScript` + localStorage** :
   - Alternative choisie : injection des tokens dans localStorage avant tout `goto` (<100 ms)
   - vs login UI : ~2s par test avec redirections + fetchUser
   - vs cookie-injection : le store utilise localStorage (pas cookie), l'injection directe est plus simple
   - Tous les endpoints auth sont mockes → aucun vrai JWT requis

5. **`tests/e2e/` (pas `e2e/` racine) + `vitest.config.exclude`** :
   - Les tests E2E cohabitent avec les tests Vitest dans `tests/`
   - Vitest exclut `tests/e2e/**` via `test.exclude`
   - Playwright utilise son propre `playwright.config.ts` (a la racine frontend par convention Playwright)

6. **Structure `installMockBackend` extensible via `options.extraRoutes`** :
   - Les stories 8.2-8.6 peuvent ajouter/override des routes sans reecrire le mock
   - Les `extraRoutes` sont inscrits EN DERNIER (evalues en premier par LIFO) → override par default
   - Types `ChatScenario` extensibles pour differents scenarios (refus, direct, expire, etc.)

7. **Port dedie 4321 (`PLAYWRIGHT_PORT` override possible)** :
   - Evite les conflits avec un dev server Nuxt tiers (vu en pratique : port 3000 occupe)
   - Variable env pour permettre l'override CI si necessaire

**Ecarts controles vs story d'origine** :

- **AC3 `toBeHidden(copilot-widget)`** : le widget n'est PAS cache pendant le guidage (il est retracte via GSAP scale=0.3/opacity=0.8, reste dans le DOM). Remplace par : `expect(floating-chat-button).toHaveClass(/cursor-not-allowed/)` qui indique `uiStore.guidedTourActive === true`. Documente dans la spec en commentaire.
- **AC6 "Fatou reouvre le widget"** : apres completion, `uiStore.chatWidgetMinimized = false` declenche automatiquement `expandWidget()` qui restaure scale=1 — le widget est deja visible. Re-cliquer le bouton flottant **fermerait** le widget (toggle). La spec verifie directement que le widget est visible + que l'historique est preserve + que `chat-textarea` est enable.
- **AC7** : patch etendu a `InteractiveQuestionInputBar.vue` (composant reellement utilise pour les questions pending) en plus de `SingleChoiceWidget.vue`. Zero regression car aucun test Vitest existant sur ces deux composants.
- **Format SSE** : la story parlait de markers HTML `<!--SSE:...-->`. Le vrai format observe dans `useChat.ts:303-514` est `data: {json}\n\n` avec `event.type` dans le JSON. Les helpers `sse-stream.ts` implementent le format reel.

### File List

**Crees** :

- `frontend/playwright.config.ts` — Configuration Playwright (port 4321, workers=1, reducedMotion)
- `frontend/tests/e2e/README.md` — Documentation commandes + strategie mocking + conventions
- `frontend/tests/e2e/fixtures/users.ts` — FATOU, FATOU_COMPANY, FATOU_CARBON_SUMMARY, FATOU_DASHBOARD_SUMMARY, type TestUser
- `frontend/tests/e2e/fixtures/auth.ts` — `loginAs(page, user)` via localStorage injection
- `frontend/tests/e2e/fixtures/sse-stream.ts` — `createSSEResponse`, `sseAssistantMessageWithConsent`, `sseGuidedTourAcceptanceResponse`
- `frontend/tests/e2e/fixtures/mock-backend.ts` — `installMockBackend(page, options)` avec tous les endpoints requis + catch-all + extension point
- `frontend/tests/e2e/8-1-parcours-fatou.spec.ts` — Spec E2E Fatou (AC1 a AC6)

**Modifies** :

- `frontend/vitest.config.ts` — Ajout `test.exclude: ['node_modules/**', 'dist/**', '.nuxt/**', 'tests/e2e/**']`
- `frontend/app/components/chat/SingleChoiceWidget.vue` — Ajout `data-testid="interactive-choice-{id}"` + `data-choice-value="{id}"` sur chaque bouton
- `frontend/app/components/chat/InteractiveQuestionInputBar.vue` — Ajout `data-testid="interactive-choice-{id}"` + `data-choice-value="{id}"` sur les boutons QCU et QCM (decouverte critique : c'est ce composant qui rend les questions pending)
- `frontend/app/components/chat/ChatInput.vue` — Ajout `data-testid="chat-textarea"` et `data-testid="chat-send-button"` pour selectors E2E stables
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — Status `ready-for-dev` → `in-progress` → `review`
- `_bmad-output/implementation-artifacts/8-1-tests-e2e-parcours-fatou.md` — Status, Tasks, Dev Agent Record, File List, Change Log

### Change Log

| Date | Description |
|---|---|
| 2026-04-14 | Story 8.1 implementee : infrastructure Playwright + spec parcours Fatou complete. 354/354 Vitest verts, 3/3 E2E repeat-each green, 0 regression. Status `ready-for-dev` → `review`. |
| 2026-04-14 | Code review BMAD adversarial (Blind Hunter + Edge Case Hunter + Acceptance Auditor). 4 decisions, 16 patches, 4 deferred, 6 dismissed. |
| 2026-04-14 | Patches batch-applied : 16/17 resolus (1 skippe = User state hydration, architectural). Modifs : `playwright.config.ts`, `fixtures/{auth,sse-stream,mock-backend}.ts`, `8-1-parcours-fatou.spec.ts`, `FloatingChatWidget.vue`, `{InteractiveQuestionInputBar,SingleChoiceWidget}.vue`. Fix en cascade : `parseInteractiveAnswer` decode `interactive_question_values` (JSON array) + multipart regex non-greedy. E2E relance : `1 passed (16.7s)`. Status → `review` (action item restant : hydrater user dans la fixture auth, documente en Review Findings). |

### Review Findings

**Decisions resolues (4)** :

- [x] [Review][Decision→Dismiss] **SSE single-shot** — Accepte. Le parser `useChat.ts` traite correctement un body SSE complet ; implementer un streaming chunke doublerait la complexite des fixtures sans benefice pour les AC de Fatou. A reconsiderer si une story future teste le parsing incremental.
- [x] [Review][Decision→Patch] **`#copilot-widget` hidden apres consent (AC3 step 2)** — Ajouter une assertion robuste via `toHaveAttribute('aria-hidden', 'true')` sur `#copilot-widget` apres `choiceYes.click()`. Documente comme patch ci-dessous.
- [x] [Review][Decision→Dismiss] **`reuseExistingServer: !CI`** — Accepte. Pattern standard Playwright, le risque de collision locale se detecte rapidement ; forcer `false` ralentirait le dev loop inutilement.
- [x] [Review][Decision→Dismiss] **CI `retries: 2` + `workers: 1`** — Accepte. Config standard pour une infra E2E naissante ; les retries absorbent les flakes reseau sans masquer de bugs produit. A revisiter quand l'epic 8 sera complet.

**Patch (17)** — 16 appliques en batch, 1 skippe (architectural ambigu) :

- [x] [Review][Patch][Applied] **Assertion `#copilot-widget` hidden apres consent (ex-Decision 2)** — Attribut `:aria-hidden` binde sur `uiStore.chatWidgetMinimized` dans `FloatingChatWidget.vue:517`. Assertion `toHaveAttribute('aria-hidden', 'true')` ajoutee apres `choiceYes.click()` dans la spec.
- [ ] [Review][Patch][Skipped] **User state non hydrate cote auth fixture** — Analyse poussee : `authStore.loadFromStorage()` ne charge que les tokens, `user` reste null au first render. Le fix necessite un choix architectural (init script qui trigger `fetchUser`, plugin Nuxt E2E-only, ou modification du middleware pour appeler `fetchUser` apres `loadFromStorage`) qui sort du scope batch-apply. Action item pour story suivante ou post-review.
- [x] [Review][Patch][Applied] **Driver.js overlay intercepte le clic sur sidebar** — `click({ force: true })` sur `[data-guide-target="sidebar-carbon-link"]` dans la spec.
- [x] [Review][Patch][Applied] **Detection `isYes` par substring match fragile** — Nouvelle fonction `parseInteractiveAnswer(postData, contentType)` dans `mock-backend.ts` qui parse correctement multipart/form-data ou urlencoded et extrait `interactive_question_answer_value`. Comparaison exacte `answerValue === 'yes'`.
- [x] [Review][Patch][Applied] **Commentaire du catch-all clarifie** — `mock-backend.ts:92-103` bloc-commentaire reecrit pour expliquer le LIFO Playwright correctement et le role des `extraRoutes`.
- [x] [Review][Patch][Applied] **`data-choice-value` supprime** — Retire des 3 emplacements : `InteractiveQuestionInputBar.vue` (QCU + QCM) et `SingleChoiceWidget.vue`.
- [x] [Review][Patch][Applied] **`waitForLoadState('networkidle')` remplace** — `beforeEach` utilise maintenant `page.getByTestId('floating-chat-button').waitFor({ state: 'visible' })`.
- [x] [Review][Patch][Applied] **Hardcoded `47.2/62/...` desync** — `handleChatPost` recoit `carbonData` en parametre et le propage dans le `context` du marker `guided_tour`.
- [x] [Review][Patch][Applied] **Assertion `/62/` durcie** — `/47[.,]2\s*tCO2e/` et `/62\s*%/` dans la spec (plus de faux positifs sur les versions/percentiles/dates).
- [x] [Review][Patch][Applied] **404 fallback durci** — Le catch-all renvoie maintenant un `500` avec `console.error` (apparait dans la trace Playwright), faisant echouer explicitement la spec au lieu de laisser le frontend simuler un 404 silencieux.
- [x] [Review][Patch][Applied] **Assertion `#copilot-widget toBeHidden` initiale ajoutee** — AC1 a maintenant 3 assertions : `floating-chat-button` visible, `#copilot-widget` hidden, `.driver-active` count=0.
- [x] [Review][Patch][Applied] **`localStorage.clear()` prefixe `addInitScript`** — `auth.ts:25` garantit l'isolation totale entre specs (theme, onboarded, etc.).
- [x] [Review][Patch][Applied] **`reducedMotion` deplace au config-level** — `playwright.config.ts` : `use.reducedMotion: 'reduce'`. L'appel `emulateMedia` retire du `beforeEach`.
- [x] [Review][Patch][Applied] **Bouton yes/no disabled apres click** — Assertions `toBeDisabled()` sur `choiceYes` et `choiceNo` immediatement apres `choiceYes.click()`.
- [x] [Review][Patch][Applied] **`created_at` fige** — Constante `FIXTURE_FROZEN_DATE = '2026-04-14T10:00:00.000Z'` exportee depuis `sse-stream.ts`. Appliquee dans SSE fixtures + `mock-backend.ts` (conversations POST/PATCH).
- [x] [Review][Patch][Applied] **Envelope `/interactive-questions` unifie** — `{ items: [], total: 0, page: 1, limit: 50 }` au lieu de `{ data: [] }`.
- [x] [Review][Patch][Applied] **Titres popovers steps 2 et 3 verifies** — `toContainText(/Comparaison sectorielle/i)` sur step 2 (benchmark), `toContainText(/Plan de r.duction/i)` sur step 3 (reduction plan).

**Defer (4)** — hors scope 8.1, a traiter ulterieurement :

- [x] [Review][Defer] Imports `../../../app/types/carbon` sans path alias — refactor global fixtures (hors scope 8.1)
- [x] [Review][Defer] `testMatch` ambiguite `.test.ts` sous `tests/e2e/` — convention a documenter (hors scope 8.1)
- [x] [Review][Defer] Pas de header `X-Accel-Buffering: no` sur SSE fixture — inutile tant que SSE reste single-shot
- [x] [Review][Defer] `route.continue()` sur methodes non-POST dans endpoints mockes — patch mineur, couvert par fallback 404 deja present
