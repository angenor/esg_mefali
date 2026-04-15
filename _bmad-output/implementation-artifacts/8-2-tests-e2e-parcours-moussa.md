# Story 8.2 : Tests E2E — Parcours Moussa (guidage refuse, chat contextuel)

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

En tant que product owner,
je veux valider qu'un utilisateur experimente (Moussa) puisse poser une question contextuelle sur la page `/financing`, recevoir une reponse adaptee a la page, refuser la proposition de guidage sans friction, puis continuer a discuter normalement via le widget flottant en superposition,
afin de garantir que les utilisateurs experimentes ne sont pas genes par le guidage et que le chat en superposition reste **utilisable** et **confidentiel** (glassmorphism qui laisse voir la page mais pas lire les donnees financieres).

## Contexte — etat actuel (VERIFIE avant redaction)

Audit realise le 2026-04-15 avant redaction. L'infrastructure E2E livree par la **story 8.1** est **reutilisee integralement** ; cette story l'**etend** (nouvelles fixtures utilisateur, nouveaux scenarios de chat, nouvelles routes API mockees) mais **ne modifie pas** `playwright.config.ts` ni les fichiers `fixtures/{auth,sse-stream}.ts` qui sont deja generiques.

### Acquis Story 8.1 (a ne PAS reinventer)

- `frontend/playwright.config.ts` — config Playwright finalisee (port 4321, `workers: 1`, `reducedMotion: 'reduce'` global, `reuseExistingServer: !CI`). **Aucun changement requis** pour 8.2.
- `frontend/tests/e2e/fixtures/auth.ts` — helper `loginAs(page, user)` par injection localStorage (`access_token`, `refresh_token`) + `localStorage.clear()` prefixe pour isolation totale. **Reutilisable avec MOUSSA sans modification**.
- `frontend/tests/e2e/fixtures/sse-stream.ts` — `createSSEResponse(events, { delayMs?, frozenDate? })`, `FIXTURE_FROZEN_DATE = '2026-04-14T10:00:00.000Z'`, helpers haut niveau `sseAssistantMessageWithConsent(...)` et `sseGuidedTourAcceptanceResponse(...)`. **Reutilisable** — **ajouter** deux helpers 8.2-specific : `sseAssistantMessageWithConsentOnFinancing(...)` (reponse contextuelle `/financing` + marker `__sse_interactive_question__`) et `sseRefusalAcknowledgement(...)` (SANS marker guided_tour) pour `POST /api/chat/interactive-questions/{id}/answer` lorsque `answerValue === 'no'`.
- `frontend/tests/e2e/fixtures/mock-backend.ts` — `installMockBackend(page, options)` avec `options.extraRoutes` (inscrits **EN DERNIER**, donc **evalues EN PREMIER** par LIFO Playwright) + catch-all `500` + `console.error` (fait echouer la spec si un endpoint non mocke est sollicite). `handleChatPost(carbonData)` existe, mais **8.2 a besoin d'une variante `handleChatPostOnFinancing(financingData)`** ou d'une extension du `chatScenario` courant pour brancher des donnees `financing` au lieu de `carbon`. **Decision dev** : etendre `MockBackendOptions` avec un champ `financingData?: FundMatchListFixture` + ajouter deux nouveaux `chatScenario` — `'propose_guided_tour_after_financing_question'` et `'refuse_guided_tour_after_financing_question'` (non utilise directement : la **meme** route `/api/chat/messages` emet le marker de consent ; c'est le handler `POST /api/chat/interactive-questions/{id}/answer` qui differencie accept/refus en parsant `interactive_question_answer_value`).
- `frontend/tests/e2e/fixtures/users.ts` — `FATOU`, `FATOU_COMPANY`, `FATOU_CARBON_SUMMARY`, `FATOU_DASHBOARD_SUMMARY`, types `TestUser` / `CompanyProfile` / `CarbonSummary`. **Ajouter** : `MOUSSA`, `MOUSSA_COMPANY`, `MOUSSA_FINANCING_MATCHES` (liste de fund matches), `MOUSSA_FUNDS` (catalogue fonds), types `FundMatchListFixture`, `FundListFixture`.
- `frontend/tests/e2e/README.md` — documentation generale et commandes. **Ajouter** une section « Conventions fixtures par parcours » qui rappelle que chaque story 8.x ajoute ses fixtures user sans casser les precedentes.
- `frontend/app/components/chat/SingleChoiceWidget.vue` et `InteractiveQuestionInputBar.vue` — `data-testid="interactive-choice-{id}"` deja patches (story 8.1). **Rien a patcher cote composants** pour 8.2.
- `frontend/app/components/chat/ChatInput.vue` — `data-testid="chat-textarea"` et `data-testid="chat-send-button"` deja poses. **Rien a patcher** pour 8.2.

### Elements du parcours Moussa deja presents dans le code

- Page `/financing` : `frontend/app/pages/financing/index.vue` — **existe** et rend un listing de fonds verts. Selecteur deja stable : `[data-guide-target="financing-fund-list"]` (ligne 187).
- Sidebar : `[data-guide-target="sidebar-financing-link"]` genere automatiquement via `{ guideTarget: 'sidebar-financing-link' }` dans `components/layout/AppSidebar.vue` (ligne 61 — meme boucle que pour le carbone).
- Registre parcours : `show_financing_catalog` existe dans `frontend/app/lib/guided-tours/registry.ts:98-120` — `entryStep` pointe le lien sidebar, step unique sur `financing-fund-list`. **Ce tour n'est PAS joue dans 8.2** (Moussa refuse), mais il **doit rester non declenche** : assertion negative `await expect(page.locator('.driver-popover, .driver-overlay')).toHaveCount(0)` apres le refus.
- Widget glassmorphism : `frontend/app/components/copilot/FloatingChatWidget.vue` — classe `.widget-glass` appliquee ligne 520, styles `backdrop-filter: blur(24px)` lignes 643-667 avec fallback `@supports not (backdrop-filter: blur(1px))` qui force un fond opaque. **Le widget a `aria-hidden` binde sur `uiStore.chatWidgetMinimized`** (ligne 517) — cet attribut est **la** facon fiable de verifier l'etat.
- Composables finance : `frontend/app/composables/useFinancing.ts` appelle `/financing/matches`, `/financing/matches/{id}`, `/financing/funds?...`, `/financing/intermediaries?...`. **Tous ces endpoints doivent etre mockes** (uniquement ceux sollicites par le chargement `/financing`, typiquement `/financing/matches` + `/financing/funds?...` pour l'onglet catalogue).
- Store `uiStore.currentPage` : deja mis a jour lors de la navigation (infrastructure de la feature 019 pre-existante). **8.2 n'a pas a valider** la mise a jour du store ; le test valide la **consequence utilisateur** = reponse contextuelle « financing » dans le chat.

### Lacunes / gaps identifies (a combler dans cette story)

1. **Aucun utilisateur Moussa** en fixture → **creer** `MOUSSA`, `MOUSSA_COMPANY`, `MOUSSA_FINANCING_MATCHES` dans `fixtures/users.ts`.
2. **Aucun scenario chat "financing"** cote mock backend → **ajouter** `propose_guided_tour_after_financing_question` dans `ChatScenario` + handler qui emet un SSE de reponse contextuelle (mention `/financing`, nombre de fonds recommandes, secteur Moussa) suivi d'un marker `__sse_interactive_question__` (meme format que 8.1).
3. **Aucune route API financing mockee** → **ajouter** `GET /api/financing/matches`, `GET /api/financing/funds?...`, `GET /api/financing/intermediaries?...` dans `installMockBackend` (les routes 8.1 `/api/carbon/**` restent, pour permettre une future execution croisee — le catch-all 500 reste actif pour tout endpoint oublie).
4. **Aucune assertion de glassmorphism** dans les specs existantes → **designer** un check robuste (CSS computed + screenshot heuristique, voir AC3 ci-dessous) qui verifie a la fois la classe CSS et le rendu reel (contenu de la page `/financing` derriere le widget visible mais donnees financieres floues).
5. **Spec 8-2 n'existe pas** → **creer** `frontend/tests/e2e/8-2-parcours-moussa.spec.ts`.
6. **Helpers SSE manquants pour le flux de refus** → **ajouter** `sseRefusalAcknowledgement(...)` dans `fixtures/sse-stream.ts` (reponse du backend apres refus : message d'accuse de reception SANS marker guided_tour).

### Decisions dev locked-in (issues du contexte 8.1)

- **Backend integralement mocke** via `page.route()` + `installMockBackend` : meme rationale que 8.1 (isolation, rapidite, CI-friendly). **Pas de retour en arriere** sur ce choix.
- **Format SSE reel** `data: {json}\n\n` avec `event.type` dans le JSON (story 8.1 review finding #4 a corrige la premiere intuition « markers HTML `<!--SSE:...-->` »). Les helpers `sse-stream.ts` implementent deja le format reel — les 8.2 ajouts (messages financing) suivent la meme convention.
- **`reducedMotion: 'reduce'`** au niveau `playwright.config.ts` (deja en place). **Ne PAS** le surcharger dans 8.2.
- **Login programmatique** via `page.addInitScript` + `localStorage.clear()` prefixe. Meme pattern pour MOUSSA.
- **Catch-all renvoyant 500 + `console.error`** : 8.2 ne doit pas le contourner — tout endpoint non-mocke doit etre ajoute explicitement.

## Acceptance Criteria

### AC1 : Extension des fixtures — Moussa (utilisateur, entreprise, matches financement)

**Given** les fixtures existantes contiennent uniquement `FATOU*`
**When** on ajoute `MOUSSA` et ses donnees associees
**Then** `frontend/tests/e2e/fixtures/users.ts` expose :

```typescript
export const MOUSSA: TestUser = {
  id: 'user-moussa-001',
  email: 'moussa.ba@coop-cacao.ci',
  full_name: 'Moussa Ba',
  // memes champs que FATOU selon le type TestUser
}

export const MOUSSA_COMPANY: CompanyProfile = {
  id: 'company-moussa-001',
  name: 'Cooperative Cacao Cote d\'Ivoire',
  sector: 'agriculture', // secteur different de Fatou pour eviter toute collision de cache
  country: 'CI',
  employee_count: 48,
  // autres champs requis par le type CompanyProfile
}

export interface FundMatchFixture {
  id: string
  fund_id: string
  fund_name: string
  match_score: number
  amount_min_eur: number
  amount_max_eur: number
  sector_match: boolean
  // autres champs reflets du type reel de /financing/matches (a verifier dans types/financing)
}

export const MOUSSA_FINANCING_MATCHES: { items: FundMatchFixture[]; total: number } = {
  total: 4,
  items: [
    { id: 'match-001', fund_id: 'fund-gcf-agri', fund_name: 'GCF Agriculture Resilient', match_score: 87, amount_min_eur: 50_000, amount_max_eur: 500_000, sector_match: true },
    { id: 'match-002', fund_id: 'fund-boad-pme', fund_name: 'BOAD Ligne PME Verte', match_score: 78, amount_min_eur: 20_000, amount_max_eur: 200_000, sector_match: true },
    { id: 'match-003', fund_id: 'fund-sunref', fund_name: 'SUNREF Cacao Durable', match_score: 71, amount_min_eur: 30_000, amount_max_eur: 300_000, sector_match: true },
    { id: 'match-004', fund_id: 'fund-fnde', fund_name: 'FNDE Cote d\'Ivoire', match_score: 64, amount_min_eur: 10_000, amount_max_eur: 100_000, sector_match: false },
  ],
}

export const MOUSSA_FUNDS: { items: Array<{ id: string; name: string; type: string; sector: string[]; amount_min_eur: number; amount_max_eur: number }>; total: number } = {
  // catalogue fonds complet tel que retourne par /financing/funds
  // reutiliser les memes entries que MOUSSA_FINANCING_MATCHES + 2-3 fonds non-match pour enrichir le catalogue
  // ...
}
```

**And** les types `FundMatchFixture`, `FundListFixture` sont exposes en `export` pour reutilisation dans `mock-backend.ts`.

**And** le type `TestUser` existant est **inchange** (Moussa a le meme shape que Fatou). Si un champ manque dans `TestUser`, **etendre** le type, pas le dupliquer.

**And** les fixtures Fatou restent **intactes** et **exportees** (zero regression sur 8-1-parcours-fatou).

### AC2 : Extension du mock backend — routes financing + scenario chat contextuel

**Given** `installMockBackend` existe avec les routes `carbon`, `auth`, `chat`, `dashboard`, `company`
**When** on etend le mock avec les routes `financing` et un nouveau `chatScenario`
**Then** `frontend/tests/e2e/fixtures/mock-backend.ts` est modifie comme suit :

**2.1** `MockBackendOptions` gagne un champ optionnel :

```typescript
export interface MockBackendOptions {
  user?: TestUser
  companyProfile?: CompanyProfile
  carbonData?: CarbonSummary // story 8.1
  financingData?: { matches: FundMatchListFixture; funds: FundListFixture } // NOUVEAU — 8.2
  chatScenario?:
    | 'propose_guided_tour_after_carbon'            // story 8.1
    | 'propose_guided_tour_after_financing_question' // NOUVEAU — 8.2
  extraRoutes?: (page: Page) => Promise<void>
}
```

**2.2** Trois nouvelles routes sont **ajoutees dans le registre principal** (ordre : **apres** les routes existantes mais **avant** le catch-all et `extraRoutes`) :

- `GET **/api/financing/matches` → 200 JSON `options.financingData?.matches ?? { items: [], total: 0 }`
- `GET **/api/financing/funds**` (pattern inclut query string) → 200 JSON `options.financingData?.funds ?? { items: [], total: 0 }` — tolerant aux filtres eventuels (secteur, type, etc.)
- `GET **/api/financing/intermediaries**` → 200 JSON `{ items: [], total: 0 }` (stub vide acceptable pour 8.2 si l'onglet n'est pas consulte ; documenter en commentaire).

**2.3** Le handler `POST /api/chat/conversations/{id}/messages` est **etendu** : quand `options.chatScenario === 'propose_guided_tour_after_financing_question'`, il emet un `ReadableStream` SSE construit par le nouvel helper `sseAssistantMessageWithConsentOnFinancing({ questionId: 'iq-moussa-tour-001', conversationId, messageId, financingData: options.financingData })`. Le contenu du message assistant **DOIT** :
- Mentionner **explicitement** la page courante `/financing` ou un mot reconnaissable (« financement », « catalogue », « fonds verts » — cf. AC3 « reponse contextuelle »)
- Nommer au moins **un** des fonds de `MOUSSA_FINANCING_MATCHES` OU le nombre total de matches (`4` fonds recommandes)
- Etre suivi d'un marker `__sse_interactive_question__` identique au format story 8.1 : `variant: 'qcu'`, `choices: [{ value: 'yes', label: 'Oui, montre-moi' }, { value: 'no', label: 'Non merci' }]`, `prompt: 'Voulez-vous que je vous guide dans le catalogue des fonds ?'`

**2.4** Le handler `POST /api/chat/interactive-questions/{id}/answer` (deja existant) reste inchange **dans sa signature**, mais son branche « `answerValue === 'no'` » **doit** emettre une reponse via le nouvel helper `sseRefusalAcknowledgement({ messageId, conversationId })` qui :
- Contient un court message d'accuse de reception francophone (ex. « Pas de souci, je reste a votre disposition. Si vous avez d'autres questions, n'hesitez pas. »)
- **N'emet AUCUN marker** `__sse_guided_tour__`
- **N'emet AUCUN marker** `__sse_interactive_question__` (pas de relance automatique)
- Pose `FIXTURE_FROZEN_DATE` comme `created_at` (determinisme)

**And** la branche `answerValue === 'yes'` du meme handler **reste fonctionnelle** pour la story 8.1 (zero regression : spec 8-1-parcours-fatou doit passer apres les modifications).

**And** le catch-all 500 reste actif en derniere position.

### AC3 : Spec E2E Moussa — preparation + navigation `/financing` + question contextuelle

**Given** les fixtures et le mock backend sont etendus
**When** on cree `frontend/tests/e2e/8-2-parcours-moussa.spec.ts`
**Then** le fichier commence par :

```typescript
import { test, expect } from '@playwright/test'
import { loginAs } from './fixtures/auth'
import { installMockBackend } from './fixtures/mock-backend'
import { MOUSSA, MOUSSA_COMPANY, MOUSSA_FINANCING_MATCHES, MOUSSA_FUNDS } from './fixtures/users'

test.describe('Parcours Moussa — guidage refuse, chat contextuel sur /financing', () => {
  test.beforeEach(async ({ page }) => {
    await installMockBackend(page, {
      user: MOUSSA,
      companyProfile: MOUSSA_COMPANY,
      financingData: { matches: MOUSSA_FINANCING_MATCHES, funds: MOUSSA_FUNDS },
      chatScenario: 'propose_guided_tour_after_financing_question',
    })
    await loginAs(page, MOUSSA)
    await page.goto('/financing')
    await page.getByTestId('floating-chat-button').waitFor({ state: 'visible' })
  })
  // ... tests suivants
})
```

**And** un premier test nomme **`'Moussa arrive sur /financing, ouvre le widget et recoit une reponse contextuelle adaptee a la page'`** valide **AC3** :

1. `await expect(page.getByTestId('floating-chat-button')).toBeVisible()` — le bouton flottant est present sur `/financing` (desktop ≥ 1024px confirme par le viewport 1280x800 de la config).
2. `await expect(page.locator('#copilot-widget')).toHaveAttribute('aria-hidden', 'true')` — le widget est retracte au chargement.
3. `await expect(page.locator('[data-guide-target="financing-fund-list"]')).toBeVisible()` — la page `/financing` a bien charge son contenu (assert que les mocks backend n'ont pas echoue).
4. `await page.getByTestId('floating-chat-button').click()` — ouverture du widget.
5. `await expect(page.locator('#copilot-widget')).toHaveAttribute('aria-hidden', 'false')` — confirmation visuelle.
6. `await page.getByTestId('chat-textarea').fill('Quels fonds sont compatibles avec mon profil ?')`
7. `await page.getByTestId('chat-send-button').click()`
8. Attendre la reponse contextuelle : **au moins une** des assertions suivantes doit passer (tolerance sur la formulation FR) :
   - `await expect(page.locator('#copilot-widget')).toContainText(/fonds|financement|catalogue/i, { timeout: 10_000 })`
   - `await expect(page.locator('#copilot-widget')).toContainText(/4\s*fonds|GCF|BOAD|SUNREF/i)` — nom d'un fond OU compte total
9. Le widget interactif de consentement apparait : `await expect(page.getByTestId('interactive-choice-yes')).toBeVisible({ timeout: 10_000 })` **ET** `await expect(page.getByTestId('interactive-choice-no')).toBeVisible()`.
10. `await expect(page.locator('[role="alert"]')).toHaveCount(0)` — aucune erreur affichee.

**Rationale AC3** : cette etape valide que l'injection `current_page` dans le payload `POST /api/chat/messages` (feature 019 pre-existante) est bien **transmise** au backend et que le backend **adapte sa reponse**. Comme le backend est mocke, le test ne verifie pas **la chaine backend complete** ; il verifie que le frontend affiche **correctement** une reponse contextuelle financement. La veritable validation backend est realisee par les **935+ tests pytest** existants.

### AC4 : Refus du guidage — aucun Driver.js, chat fonctionnel, widget preserve

**Given** le widget de consentement est affiche (fin de AC3)
**When** Moussa clique sur « Non merci »
**Then** le test suivant (dans le meme describe ou un test dedie) valide :

1. `await page.getByTestId('interactive-choice-no').click()`
2. Les boutons du widget interactif sont **desactives immediatement** apres le clic (pattern 8.1 patch Review) :
   - `await expect(page.getByTestId('interactive-choice-yes')).toBeDisabled({ timeout: 2_000 })`
   - `await expect(page.getByTestId('interactive-choice-no')).toBeDisabled()`
3. **Aucun Driver.js** n'est declenche : attendre un court delai deterministe (`await page.waitForTimeout(500)` — **seule** exception autorisee car il faut laisser le moteur SSE consommer le stream de refus et ne **rien** rendre, l'absence d'element est difficile a assertionner via `toHaveCount(0, { timeout })` qui re-essaie mais retourne tot si deja `0` — justification : on veut **detecter** un declenchement erratique), **puis** :
   - `await expect(page.locator('.driver-popover')).toHaveCount(0)`
   - `await expect(page.locator('.driver-overlay, .driver-highlight, .driver-active-element')).toHaveCount(0)`
4. Le widget **reste ouvert** : `await expect(page.locator('#copilot-widget')).toHaveAttribute('aria-hidden', 'false')`.
5. Le bouton flottant **n'est pas** en mode `cursor-not-allowed` : `await expect(page.getByTestId('floating-chat-button')).not.toHaveClass(/cursor-not-allowed|opacity-60/)`.
6. Le chat est fonctionnel : l'input textarea est enable, l'utilisateur peut taper un nouveau message :
   - `await expect(page.getByTestId('chat-textarea')).toBeEnabled()`
   - `await page.getByTestId('chat-textarea').fill('Montre-moi juste le fond GCF Agriculture')`
   - `await expect(page.getByTestId('chat-send-button')).toBeEnabled()`
7. Un **accuse de reception** du refus s'affiche dans l'historique : `await expect(page.locator('#copilot-widget')).toContainText(/(disposition|pas de souci|d'accord|compris)/i)`.

**Rationale AC4** : la simple absence de Driver.js ne suffit pas — on valide aussi que le chat **reste utilisable**, que les boutons sont **disabled** (previent le double-clic qui declencherait un tour fantome), et qu'un message d'accuse de reception informe l'utilisateur que son refus a ete pris en compte. L'ensemble constitue la definition fonctionnelle de « refus sans friction ».

### AC5 : Glassmorphism — page `/financing` visible derriere le widget, donnees financieres NON lisibles

**Given** le widget est en superposition sur `/financing`
**When** on inspecte le rendu visuel
**Then** **deux** types d'assertion sont combinees pour robustesse :

**5.1 Assertion CSS computed (deterministe, prioritaire)** :
- `const widget = page.locator('#copilot-widget')`
- `await expect(widget).toHaveClass(/widget-glass/)` — la classe glassmorphism est appliquee (verifiable sans dependre du navigateur).
- `const filter = await widget.evaluate((el) => getComputedStyle(el).backdropFilter || getComputedStyle(el).webkitBackdropFilter)` → attendre que la string contienne `'blur('` :
  - Si `filter.includes('blur(')` **OU** `filter === 'none'` → assert que :
    - si `'blur('` : l'assertion passe (glassmorphism actif), **ET** verifier que la valeur est `>= 20px` (ex. `blur(24px)`) pour garantir que les donnees financieres derriere seront illisibles.
    - si `filter === 'none'` : **verifier que le fallback opaque** est actif — `const bg = await widget.evaluate((el) => getComputedStyle(el).backgroundColor)` doit etre une couleur **non-transparente** (alpha = 1, ex. `rgb(255, 255, 255)`). Ceci implemente l'acceptance criterion « glassmorphism ou fallback opaque visible ».
- En mode dark, la meme regle s'applique mais la couleur de fallback est sombre : `rgb(31, 41, 55)` ou similaire.

**5.2 Assertion fonctionnelle — contenu `/financing` visible derriere le widget** :
- **Verifier** que la page `/financing` a bien charge son contenu **avant** l'ouverture du widget : deja fait en AC3 step 3 (assertion sur `[data-guide-target="financing-fund-list"]`). **Ne pas re-tester** — cette assertion passe dans le `beforeEach`.
- **Verifier** qu'apres ouverture du widget, le listing financier est **toujours** dans le DOM (pas cache par le widget, seulement flou) : `await expect(page.locator('[data-guide-target="financing-fund-list"]')).toBeAttached()` (assertion `attached` = present dans DOM ; `toBeVisible()` suffirait mais peut etre fragile a cause du flou perceptuel).
- **Verifier** qu'au moins un nom de fond est dans le DOM derriere le widget : `await expect(page.locator('[data-guide-target="financing-fund-list"]')).toContainText(/GCF|BOAD|SUNREF|FNDE/)` — le contenu **existe** meme si flou.

**5.3 Verifier l'empilement z-index (ni le widget ni Driver.js ne cassent le layout `/financing`)** :
- `const widgetZ = await widget.evaluate((el) => parseInt(getComputedStyle(el).zIndex) || 0)` → **devrait etre ≥ 50** (cf. FloatingChatWidget.vue:520 `z-50`).
- La page `/financing` derriere n'est pas en `z-index` superieur : `const fundListZ = await page.locator('[data-guide-target="financing-fund-list"]').evaluate((el) => parseInt(getComputedStyle(el).zIndex) || 0)` → **devrait etre 0 ou `auto`**.

**Note dev** : **ne PAS** tenter d'assertionner « les donnees financieres ne sont pas lisibles a travers le blur » par OCR ou screenshot pixel-a-pixel. C'est fragile et coute cher. On se **base** sur la valeur de `backdrop-filter: blur(>=20px)` **OU** le fallback opaque, qui **par construction** rendent les chiffres illisibles pour l'oeil humain. La story **accepte** cette abstraction.

**Rationale AC5** : le PRD exige « les donnees financieres ne sont pas lisibles a travers le blur » — cette exigence est **satisfiable** par la configuration `backdrop-filter: blur(24px)` (attestee dans `FloatingChatWidget.vue:644`) **OU** le fallback opaque (ligne 657-667). Les deux chemins sont verifies par 5.1. L'assertion 5.2 garantit en plus que la page n'est **pas** masquee (fail-fast si un futur refactor pose un overlay noir au lieu d'un blur).

### AC6 : Non-regression — spec 8-1-parcours-fatou reste verte

**Given** les modifications apportees a `mock-backend.ts`, `sse-stream.ts`, `users.ts`
**When** on execute la suite E2E complete
**Then** :
1. `npm run test:e2e -- 8-1-parcours-fatou` → **1 passed**, **0 failed**, **0 flaky**.
2. `npm run test:e2e -- 8-2-parcours-moussa` → **1 passed (ou plus selon decoupage `test()`)**, **0 failed**, **0 flaky**.
3. `npm run test:e2e` (sans filtre) → **toutes** les specs passent.
4. `npm run test:e2e -- --repeat-each=3 8-2-parcours-moussa` → **3/3 passed**, confirmation anti-flake.
5. `npm run test -- --run` → **tests Vitest 354+ verts** (aucun test Vitest modifie, mais revalidation systematique).
6. `npx tsc --noEmit` → **aucune nouvelle erreur TS** dans `tests/e2e/**` ni `app/components/**` (aucun composant n'est modifie dans 8.2).

### AC7 : Robustesse — anti-flake appliquee (pattern story 8.1 / 7.3)

**Given** les risques de flakiness sont les memes que 8.1 (SSE, glassmorphism timing)
**When** on ecrit 8.2, on **reapplique** les conventions deja validees :

1. **Pas de `page.waitForTimeout(N)` en dur** sauf **AC4 step 3** (justification dans le commentaire de code : detection d'absence d'element nouveau → `waitForTimeout(500)` est necessaire et documente).
2. **Timeouts explicites** sur toutes les assertions post-SSE : `{ timeout: 10_000 }`.
3. **Pas de selectors CSS fragiles** — `getByTestId` et `getByRole` prioritaires. Selectors `[data-guide-target="..."]` toleres (ils sont **plus stables** que les classes Tailwind et servent aussi au guidage runtime).
4. **`reducedMotion: 'reduce'`** est **deja** au niveau config (inutile de le redeclarer).
5. **Assertions auto-retry** via `expect(...).toBeVisible({ timeout })` sans wrapping manuel.
6. **Ordre d'installation** : `installMockBackend(...)` → `loginAs(...)` → `page.goto(...)` (respecte le contrat LIFO + early-bird pour les routes).
7. **Repeat-each=3** execute localement pour AC6.4.

### AC8 : Documentation traceabilite + decisions design

**Given** la story est complete
**When** on lit la section `## Dev Notes` en fin de story
**Then** elle contient :
- Un tableau « AC → fichier(s) / zone / test(s) » (pattern story 8.1).
- Les **decisions de design** documentees en Completion Notes :
  - Pourquoi le fallback `waitForTimeout(500)` en AC4 (detection d'absence).
  - Pourquoi ajouter `financingData` dans `MockBackendOptions` plutot que de creer un deuxieme helper `installMockBackendForFinancing` (reuse > duplication — CLAUDE.md « Reutilisabilite des Composants »).
  - Strategie de verification glassmorphism (CSS computed + z-index, pas de OCR).
  - Pourquoi 8.2 n'introduit **aucun** nouveau `data-testid` dans les composants (ils ont deja ete ajoutes par 8.1 — AC7 de 8.1 — et sont suffisants).
  - Pourquoi le mock `/api/financing/intermediaries` renvoie une liste vide (non consulte par le parcours Moussa — le test ne va pas sur l'onglet intermediaires).

## Tasks / Subtasks

- [x] Task 1 : Extension fixtures users (AC: #1)
  - [x] 1.1 Lire les types reels `TestUser`, `CompanyProfile` dans `frontend/tests/e2e/fixtures/users.ts` pour ajuster les shapes.
  - [x] 1.2 Lire `frontend/app/types/financing.ts` (ou equivalent) pour typer correctement `FundMatchFixture` et `FundListFixture` conformement aux types utilises par `useFinancing.ts`.
  - [x] 1.3 Ajouter `MOUSSA`, `MOUSSA_COMPANY`, `MOUSSA_FINANCING_MATCHES`, `MOUSSA_FUNDS` en fin de fichier sans modifier les exports existants `FATOU*`.
  - [x] 1.4 Exporter `FundMatchFixture`, `FundListFixture` pour utilisation dans `mock-backend.ts`.

- [x] Task 2 : Helpers SSE financing + refus (AC: #2)
  - [x] 2.1 Ajouter dans `sse-stream.ts` la fonction `sseAssistantMessageWithConsentOnFinancing(...)` — contenu qui cite le secteur et/ou le nom d'un fond.
  - [x] 2.2 Ajouter `sseRefusalAcknowledgement({ messageId })` — stream minimal : token d'accuse + done. AUCUN marker guided_tour ou interactive_question.
  - [x] 2.3 Helpers existants `sseAssistantMessageWithConsent`, `sseGuidedTourAcceptanceResponse` **inchanges** (zero regression 8.1 verifiee).

- [x] Task 3 : Extension mock backend (AC: #2)
  - [x] 3.1 `MockBackendOptions` etendu avec `financingData?: { matches; funds }` + type `chatScenario` elargi avec `'propose_guided_tour_after_financing_question'`.
  - [x] 3.2 3 routes financing ajoutees (`/matches`, `/funds?...`, `/intermediaries?...`). `intermediaries` renvoie stub vide (commentaire dans le code).
  - [x] 3.3 `handleChatPost` branche sur `options.chatScenario` : carbon inchange / financing = nouveau helper.
  - [x] 3.4 Reponse interactive detectee par le POST messages (FormData `interactive_question_id`). `yes` → tour `show_financing_catalog` ; `no` → `sseRefusalAcknowledgement` ; autre → 500 + console.error (garde-fou).
  - [x] 3.5 Catch-all et `extraRoutes` **non touches**.

- [x] Task 4 : Spec E2E principale — `8-2-parcours-moussa.spec.ts` (AC: #3, #4, #5, #7)
  - [x] 4.1 Fichier cree avec imports depuis fixtures + mock etendu.
  - [x] 4.2 `beforeEach` : `installMockBackend` → `loginAs(MOUSSA)` → `page.goto('/financing')` → `floatingChatButton.waitFor`.
  - [x] 4.3 **Test A** (AC3) — reponse contextuelle + widget de consentement.
  - [x] 4.4 **Test B** (AC4) — refus + aucun Driver.js + chat fonctionnel. Helper `setupUntilConsent(page)` factorise le setup commun.
  - [x] 4.5 **Test C** (AC5) — glassmorphism decoupe en test separe (lisibilite > fusion).
  - [x] 4.6 `test.describe('Parcours Moussa — guidage refuse, chat contextuel sur /financing')`.

- [x] Task 5 : Validation complete (AC: #6, #7)
  - [x] 5.1 `npx playwright test 8-2-parcours-moussa` → **3/3 passed (9.3 s)**.
  - [x] 5.2 `npx playwright test 8-2-parcours-moussa --repeat-each=3` → **9/9 passed (17.5 s)** — zero flake.
  - [x] 5.3 `npx playwright test 8-1-parcours-fatou` → **2/2 passed (31.5 s)** — non-regression OK.
  - [x] 5.4 Suite e2e complete covered (8.1 + 8.2).
  - [x] 5.5 `npm run test -- --run` → 353 passed / 1 fail pre-existant (useGuidedTour.resilience — confirme en echec avant les changements 8.2, hors scope).
  - [x] 5.6 `npx tsc --noEmit` → aucune nouvelle erreur TS introduite par 8.2 (6 erreurs pre-existantes sur `useChat.ts`, `useFocusTrap.ts`, `useGuidedTour.ts`).
  - [x] 5.7 README E2E enrichi : convention fixtures par parcours + mode visuel ralenti (`PLAYWRIGHT_SLOWMO` + `PLAYWRIGHT_FULL_MOTION`).

- [x] Task 6 : Documentation traceabilite (AC: #8)
  - [x] 6.1 Tableau AC → fichier → test present dans Dev Notes (inchange).
  - [x] 6.2 Decisions design documentees en Completion Notes (voir ci-dessous).
  - [x] 6.3 `sprint-status.yaml` : `8-2-tests-e2e-parcours-moussa` → `in-progress` (au demarrage) → `review` (a la completion, dans la section finale).
  - [x] 6.4 File List completee.

## Dev Notes

### Contexte — deuxieme story de l'epic 8 (Tests d'integration end-to-end)

Story 8.2 est la **premiere** story qui **consomme** et **etend** l'infrastructure posee par 8.1 — elle valide que l'architecture de 8.1 (`options.extraRoutes`, helpers SSE parametriques, catch-all 500) **supporte reellement** de nouveaux parcours **sans refonte**. **Si cette extension se revele lourde** (par exemple duplication massive du handler chat), la **retrospective epic-8** devra documenter le gap architectural.

**Cette story est PURE-EXTENSION** : aucun composant UI n'est modifie (les `data-testid` de 8.1 AC7 suffisent), aucune route d'API n'est changee cote backend reel (le backend est mocke), aucune migration BDD. Les seuls fichiers **non-test** touches sont eventuellement `tests/e2e/README.md` pour la documentation.

### Mapping AC → fichier → test

| AC | Fichier(s) impacte(s) | Zone / objet | Test / assertion |
|---|---|---|---|
| AC1 Fixtures Moussa | `tests/e2e/fixtures/users.ts` (MODIFIER) | Ajout `MOUSSA*`, types Fund* | Import sans erreur dans la spec ; typecheck OK |
| AC2 Mock financing | `tests/e2e/fixtures/mock-backend.ts`, `fixtures/sse-stream.ts` (MODIFIER) | 3 routes financing + 2 helpers SSE + branch `chatScenario` + branch `answerValue === 'no'` | `npm run test:e2e` ne log aucun `console.error` 500 catch-all |
| AC3 Reponse contextuelle | `tests/e2e/8-2-parcours-moussa.spec.ts` (CREER) | Test A | `toContainText(/fonds|financement|catalogue/i)` + `getByTestId('interactive-choice-no').toBeVisible()` |
| AC4 Refus + aucun Driver.js | Meme spec — Test B | Transition refus | `locator('.driver-popover').toHaveCount(0)` + chat fonctionnel + message d'accuse reception |
| AC5 Glassmorphism | Meme spec — Test C (ou fusion) | Assertions CSS computed | `backdrop-filter: blur(>=20px)` OU `backgroundColor` opaque ; `financing-fund-list` reste `toBeAttached()` |
| AC6 Non-regression | — | Suite complete | `test:e2e` + `test:e2e -- 8-1-parcours-fatou` + Vitest + typecheck |
| AC7 Anti-flake | Meme spec | Conventions | `--repeat-each=3` green |
| AC8 Doc | Cette story | Dev Notes + Completion Notes | Revue manuelle |

### Selectors critiques (deja presents — pas a creer)

| Selector | Fichier source | Ligne | Usage 8.2 |
|---|---|---|---|
| `[data-testid="floating-chat-button"]` | `components/copilot/FloatingChatButton.vue` | 15 | AC3 beforeEach, AC4 assertion `not.toHaveClass` |
| `[data-guide-target="financing-fund-list"]` | `pages/financing/index.vue` | 187 | AC3.3 (page chargee), AC5.2 (page visible derriere widget) |
| `[data-guide-target="sidebar-financing-link"]` | `components/layout/AppSidebar.vue` | 61 (genere) | Non utilise (pas de navigation sidebar dans 8.2 car refus) |
| `[data-testid="interactive-choice-yes"]` | `components/chat/InteractiveQuestionInputBar.vue` | (pose par 8.1) | AC3.9 (visible) |
| `[data-testid="interactive-choice-no"]` | Idem | Idem | AC3.9 + AC4.1 (click) + AC4.2 (disabled) |
| `[data-testid="chat-textarea"]` | `components/chat/ChatInput.vue` | (pose par 8.1) | AC3.6 (fill), AC4.6 (enabled) |
| `[data-testid="chat-send-button"]` | Idem | Idem | AC3.7 (click), AC4.6 (enabled) |
| `#copilot-widget` | `components/copilot/FloatingChatWidget.vue` | 517 (racine + aria-hidden) | AC3.2, AC3.5 (aria-hidden state), AC4.4 (ouvert), AC5 (classe `.widget-glass`) |
| `.driver-popover`, `.driver-overlay`, `.driver-highlight` | Classes runtime Driver.js | — | AC4.3 (assertion COUNT = 0) |

### Helpers SSE a ajouter (`fixtures/sse-stream.ts`)

```typescript
// NOUVEAU — 8.2
export function sseAssistantMessageWithConsentOnFinancing(opts: {
  questionId: string
  conversationId: string
  messageId: string
  financingData: { matches: FundMatchListFixture; funds: FundListFixture }
  frozenDate?: string
}): { body: string; headers: Record<string, string>; contentType: string }

// NOUVEAU — 8.2
export function sseRefusalAcknowledgement(opts: {
  messageId: string
  conversationId: string
  frozenDate?: string
}): { body: string; headers: Record<string, string>; contentType: string }
```

**Contenu du message du helper `sseAssistantMessageWithConsentOnFinancing`** — exemple de chunks :

```
data: {"event":"message_start","message_id":"{messageId}","conversation_id":"{conversationId}","created_at":"{frozenDate}"}\n\n
data: {"event":"content_delta","delta":"J'ai identifie **4 fonds** verts compatibles avec votre cooperative cacao en Cote d'Ivoire :"}\n\n
data: {"event":"content_delta","delta":" GCF Agriculture Resilient (87%), BOAD Ligne PME Verte (78%), SUNREF Cacao Durable (71%) et FNDE (64%)."}\n\n
data: {"event":"interactive_question","id":"{questionId}","variant":"qcu","prompt":"Voulez-vous que je vous guide dans le catalogue des fonds ?","choices":[{"value":"yes","label":"Oui, montre-moi"},{"value":"no","label":"Non merci"}],"allow_answer_elsewhere":false}\n\n
data: {"event":"done"}\n\n
```

**Contenu du message du helper `sseRefusalAcknowledgement`** :

```
data: {"event":"message_start","message_id":"{messageId}","conversation_id":"{conversationId}","created_at":"{frozenDate}"}\n\n
data: {"event":"content_delta","delta":"Pas de souci, je reste a votre disposition. Si vous avez d'autres questions, n'hesitez pas."}\n\n
data: {"event":"done"}\n\n
```

**Important** : **verifier le format exact** en relisant le code actuel de `sseAssistantMessageWithConsent` (story 8.1) et en alignant les noms d'event (`content_delta` vs `content.delta`, etc.). Si un champ est different dans la realite, **corriger** les helpers — le test doit refleter le vrai contrat SSE backend, pas une intuition.

### Routes API a mocker (recap consolide 8.1 + 8.2)

| Route | Story source | Notes |
|---|---|---|
| `POST /api/auth/login`, `GET /api/auth/me`, `POST /api/auth/refresh`, `GET /api/auth/detect-country` | 8.1 | Inchange |
| `GET /api/company/profile`, `GET /api/company/profile/completion` | 8.1 | Inchange |
| `GET /api/dashboard/summary` | 8.1 | Inchange |
| `GET /api/carbon/assessments(?query)`, etc. | 8.1 | Inchange (pas sollicite par 8.2 mais doit rester disponible si future spec multi-page) |
| `GET /api/financing/matches` | **8.2 NOUVEAU** | Renvoie `options.financingData.matches` |
| `GET /api/financing/funds?...` | **8.2 NOUVEAU** | Renvoie `options.financingData.funds` (tolerant aux query params) |
| `GET /api/financing/intermediaries?...` | **8.2 NOUVEAU** | Renvoie `{ items: [], total: 0 }` stub |
| `POST /api/chat/conversations/{id}/messages` | 8.1 **ETENDU** | Branche `chatScenario` ; ajout `propose_guided_tour_after_financing_question` |
| `POST /api/chat/interactive-questions/{id}/answer` | 8.1 **ETENDU** | Branche `answerValue` ; ajout `'no'` → `sseRefusalAcknowledgement` |
| `POST /api/chat/interactive-questions/{id}/abandon` | 8.1 | Inchange |
| `GET /api/chat/conversations`, `POST /api/chat/conversations`, `PATCH/DELETE {id}`, `GET {id}/interactive-questions`, `GET/POST {id}/messages` | 8.1 | Inchange |

### Verification de la reponse contextuelle — sans fausse precision

**Attention** : le test ne doit **pas** coupler a la formulation exacte du LLM (meme si c'est un mock, la tentation est reelle). Les assertions AC3.8 sont **regex case-insensitive** et tolerent :
- Le mot « financement » ou « fonds » ou « catalogue » (garantie contextuelle)
- Le nom d'un fond (`GCF|BOAD|SUNREF|FNDE`) ou le count `4\s*fonds` (garantie que la reponse est **reellement** adaptee aux donnees de Moussa).

Si le helper `sseAssistantMessageWithConsentOnFinancing` est ulterieurement reecrit pour emettre une formulation differente, **mettre a jour** les regex simultanement — pas de debuggage a l'aveugle.

### Architecture compliance

- **Pas de nouvelle dependance npm** — Playwright 1.49 est deja installe (story 8.1).
- **Pas de modification** de l'architecture runtime — uniquement fixtures de test.
- **Pas d'impact** sur le backend Python — backend integralement mocke.
- **TypeScript strict** : tous les fichiers modifies/crees doivent etre `strict` compatible. `npx tsc --noEmit` passe.
- **Dark mode** : non applicable en soi (tests). Toutefois, AC5.1 **tolere** le cas dark (fallback `rgb(31, 41, 55)`) — si le projet exige de tester dark mode en E2E, **reporter** dans la story 8.5 (Aissatou, detection mobile) ou une story dediee post-epic 8.
- **Convention CLAUDE.md « Reutilisabilite »** : respectee via l'extension de `installMockBackend` et `sse-stream.ts` (pas de duplication).

### Library/framework requirements

| Dependance | Version | Etat |
|---|---|---|
| `@playwright/test` | `^1.49.0` | Deja installe (story 8.1) |
| Chromium | Fourni par Playwright | Deja telecharge (story 8.1) |

Aucune installation supplementaire requise.

### File structure requirements

```
frontend/
├── playwright.config.ts                                    [INCHANGE — story 8.1]
├── vitest.config.ts                                        [INCHANGE — story 8.1]
├── app/
│   └── components/                                         [INCHANGE — 8.1 AC7 suffit]
└── tests/
    └── e2e/
        ├── README.md                                       [MODIFIER — section "fixtures par parcours"]
        ├── 8-1-parcours-fatou.spec.ts                      [INCHANGE]
        ├── 8-2-parcours-moussa.spec.ts                     [CREER — spec principale]
        └── fixtures/
            ├── auth.ts                                     [INCHANGE]
            ├── users.ts                                    [MODIFIER — ajout MOUSSA*]
            ├── mock-backend.ts                             [MODIFIER — +routes financing, +branche chatScenario, +branche answerValue='no']
            └── sse-stream.ts                               [MODIFIER — +sseAssistantMessageWithConsentOnFinancing, +sseRefusalAcknowledgement]
```

### Testing standards (AC6, AC7)

Repris integralement de 8.1 — meme stack Playwright, memes options, meme anti-flake :
- Viewport 1280x800 (desktop ≥ 1024px seuil widget)
- `reducedMotion: 'reduce'` au niveau config global
- `workers: 1`, `fullyParallel: false`
- Retries 2 en CI, 0 en local
- Trace `on-first-retry`, screenshot `only-on-failure`, video `retain-on-failure`

Commandes :
```bash
npm run test:e2e -- 8-2-parcours-moussa
npm run test:e2e -- --repeat-each=3 8-2-parcours-moussa
npm run test:e2e                                   # execute TOUTES les specs (8.1 + 8.2)
```

### Previous story intelligence

#### Story 8.1 — Infrastructure Playwright + Fatou

- **Leve des 6 gaps** infrastructure (`playwright.config.ts`, dossier `tests/e2e/`, fixtures, mock backend, helpers SSE, selecteurs `data-testid` sur les composants de consentement).
- **Decouverte critique** : les questions **pending** sont rendues par `InteractiveQuestionInputBar.vue`, pas `SingleChoiceWidget.vue`. **8.2 reutilise les memes testids** — le dev n'a pas a refaire la decouverte.
- **Bug LIFO Playwright** : le catch-all doit etre **en premier** (inscrit en premier = evalue en dernier). **8.2 doit respecter** — inscrire `extraRoutes` avant le catch-all implique d'inscrire les nouvelles routes financing **apres** le catch-all **si on veut les preceder**... **STOP** : revelecture de `mock-backend.ts` : le catch-all est inscrit **en premier** (donc evalue en dernier = fallback). Les routes specifiques inscrites **apres** le catch-all sont evaluees **avant** (= overrident le catch-all). **Conclusion 8.2** : les nouvelles routes financing doivent etre inscrites **apres** les routes existantes (ordre d'ajout), pas avant le catch-all specifiquement. **Verifier** le code reel de 8.1 avant d'implementer — le README explique le LIFO.
- **Format SSE reel** : `data: {json}\n\n` avec `event.type` dans le JSON. **8.2 utilise** le meme format.
- **Port 4321** : dedie pour eviter les collisions avec d'autres dev servers Nuxt. **Inchange** pour 8.2.
- **Login par localStorage** (pas cookie ni UI) : `loginAs` est deterministe et rapide. **Inchange**.
- **Determinisme** : `FIXTURE_FROZEN_DATE` fige les `created_at` dans les fixtures SSE. **8.2 doit reutiliser** la meme constante pour tous les SSE streams qu'il emet.

#### Stories 7.1-7.3 (resilience + SSE reconnexion)

- **`isConnected` cote widget** : si le mock backend renvoie 500 ou timeout, le badge « Reconnexion... » apparait et bloque `ChatInput`. **Impact 8.2** : le catch-all 500 ne doit **jamais** etre atteint dans le parcours nominal — toutes les routes `/financing/**` doivent etre explicitement mockees (pas de fallback silencieux).

### Git intelligence (5 derniers commits)

- `2cc5c11` : **spec 019 guided-tour-post-fix-debts + dette aval** (contexte values par tour_id)
- `ee04069` : fix(guided-tour) — supprimer bulle vide + fallback messages
- `d10edd2` : fix(chat-sse) — whitelist profile_update / profile_completion
- `8c71101` : fix(guided-tour) — cles context par tour_id dans GUIDED_TOUR_INSTRUCTION
- `95871ea` : correction bug driver.js

**Insights pour 8.2** :
- Les commits recents concernent la **stabilisation** de la feature 019, pas l'extension du chat ou des tools. **8.2 n'est pas impacte** par ces patches car il teste le **refus** (Driver.js jamais active).
- **Dette 019 documentee** dans `spec-019-guided-tour-post-fix-debts.md` — a lire si un dev bloque sur l'integration, mais **pas bloquant** pour 8.2.

### Latest tech information — Playwright 1.49 + Nuxt 4

- Playwright 1.49 stable. Features utilisees : `page.route`, `page.evaluate`, `getByTestId`, `toHaveAttribute`, `toHaveClass`, `toBeAttached`. Toutes documentees et stables.
- `getComputedStyle(el).backdropFilter` : supporte en Chromium moderne depuis longtemps ; Playwright 1.49 + Chromium Launch + viewport desktop = support garanti.
- Nuxt 4 + Vue Composition API : **pas** de piege particulier pour E2E ; les composants hydratent normalement apres `page.goto` + `networkidle` (ou dans notre cas `floatingChatButton.waitFor`).

### Project Structure Notes

Alignement avec la structure unifiee (story 8.1) :
- `tests/e2e/8-2-parcours-moussa.spec.ts` suit la convention de nommage `{epic}-{num}-parcours-{prenom}.spec.ts`.
- Les fixtures restent organisees en un seul fichier `users.ts` (par parcours, pas par fichier dedie) — **decision deliberee** pour eviter l'eparpillement ; les parcours 8.3-8.6 ajouteront leurs fixtures au meme fichier.
- Aucune variance ou conflit detecte vs. story 8.1.

### References

- PRD (parcours Moussa) : [Source: _bmad-output/planning-artifacts/prd.md#FR-* — chercher section "Moussa"]
- Epic 8 : [Source: _bmad-output/planning-artifacts/epics.md:1189-1254]
- Story 8.2 (origine) : [Source: _bmad-output/planning-artifacts/epics.md:1228-1254]
- Story precedente 8.1 : [Source: _bmad-output/implementation-artifacts/8-1-tests-e2e-parcours-fatou.md]
- Dette feature 019 (contexte) : [Source: _bmad-output/implementation-artifacts/spec-019-guided-tour-post-fix-debts.md]
- Architecture E2E : [Source: _bmad-output/planning-artifacts/architecture.md:96, 1022]
- Registre parcours `show_financing_catalog` : [Source: frontend/app/lib/guided-tours/registry.ts:98-120]
- Widget glassmorphism : [Source: frontend/app/components/copilot/FloatingChatWidget.vue:517 (aria-hidden), 520 (.widget-glass), 643-667 (CSS)]
- Page financing + selector `financing-fund-list` : [Source: frontend/app/pages/financing/index.vue:187]
- Sidebar financing link : [Source: frontend/app/components/layout/AppSidebar.vue:61]
- Composable useFinancing (endpoints API) : [Source: frontend/app/composables/useFinancing.ts:38, 114, 150]
- useChat `current_page` : [Source: frontend/app/composables/useChat.ts:253, 653]
- Infrastructure 8.1 (fixtures) : [Source: frontend/tests/e2e/fixtures/{auth,users,mock-backend,sse-stream}.ts]

## Dev Agent Record

### Agent Model Used

claude-opus-4-6[1m] (via Claude Code)

### Debug Log References

- Premier run des 3 tests : 3 echecs sur `toHaveAttribute('aria-hidden', 'true')` a l'etat initial. Cause racine : le widget `FloatingChatWidget.vue:511` utilise `v-show="isVisible || uiStore.chatWidgetOpen"` — quand `chatWidgetOpen = false`, le widget est `display:none` mais son attribut `aria-hidden` n'est PAS "true" (il reflete `chatWidgetMinimized`, separe). Le story AC3 step 2 conjecturait un couplage inexistant. Correction : alignement sur le pattern 8.1 (`toBeHidden()` / `toBeVisible()`), documente inline dans la spec.
- Apres correction : **3/3 passed (9.3 s)** puis **9/9 passed** en `--repeat-each=3` sans aucun flake.
- Non-regression 8.1 confirmee (2/2 passed, 31.5 s).

### Completion Notes List

**Architecture & design**

1. **Assertion initiale `aria-hidden`** : le story AC3 step 2 prescrivait `toHaveAttribute('aria-hidden', 'true')` a l'etat initial. Verifie sur le composant reel, c'est faux : le widget se cache via `v-show` (selon `chatWidgetOpen`), alors que `aria-hidden` reflete `chatWidgetMinimized` (vaut `false` par defaut). La spec utilise donc `toBeHidden()` / `toBeVisible()` (pattern 8.1) et annote la deviation inline. **Decision dev** : ne pas modifier l'AC (instruction « Only modify the story file in Tasks/Subtasks... »), corriger la spec pour refleter le comportement reel.

2. **`setupUntilConsent(page)` helper local** : factorise le setup commun entre les tests AC4 (refus) et AC5 (glassmorphism). Evite la duplication sans casser l'isolation — chaque test reste autonome, le helper n'est pas un hook global.

3. **Detection du refus via POST messages** : le backend reel ET le mock utilisent un seul endpoint `POST /api/chat/conversations/{id}/messages` avec FormData (`interactive_question_id` + `interactive_question_values`). Pas de `POST /api/chat/interactive-questions/{id}/answer` separe. La story AC2.4 supposait l'existence d'un endpoint dedie — en realite c'est le meme handler `handleChatPost` qui branche sur la presence du champ FormData. **Implementation** : un seul handler, deux branches (`isInteractiveAnswer === true` avec `values.includes('no')` → `sseRefusalAcknowledgement`).

4. **Fallback `waitForTimeout(500)` en AC4 step 3** : seul `waitForTimeout` dur dans la spec. Justifie inline : `toHaveCount(0)` retourne tot si la valeur est deja 0, on ne DETECTERAIT pas un popover qui demarrerait 300 ms apres le clic. Le timeout deterministe laisse au moteur SSE le temps de consommer le stream de refus avant qu'on affirme l'absence de Driver.js.

5. **`financingData` dans `MockBackendOptions` (reuse > duplication)** : pas de `installMockBackendForFinancing()` parallele. Le mock backend est un point d'extension canonique (CLAUDE.md « Reutilisabilite des Composants »). Les prochaines stories 8.3-8.6 ajouteront leurs propres champs optionnels sans refonte.

6. **Glassmorphism — CSS computed + z-index, pas d'OCR** : conformement au AC5 rationale, on valide `backdrop-filter: blur(>=20px)` OU fallback opaque (couleur non-transparente). Test passe systematiquement (blur(24px) configure dans `FloatingChatWidget.vue:644`). Assertion fonctionnelle `toContainText(/GCF|BOAD|SUNREF|FNDE/)` sur le listing garantit que la page n'est pas masquee par un overlay.

7. **Stub vide `/api/financing/intermediaries`** : l'onglet intermediaires n'est jamais ouvert par le parcours Moussa (refus immediat). La route est cependant sollicitee par `onMounted` de `pages/financing/index.vue:18` qui appelle `fetchIntermediaries()` systematiquement. Stub vide `{ items: [], total: 0 }` suffit — aucune assertion sur le contenu.

8. **Mode visuel ralenti** : infrastructure 8.1 prevoyait deja `PLAYWRIGHT_SLOWMO` + `PLAYWRIGHT_FULL_MOTION` dans `playwright.config.ts`. Aucune modification de config — simple documentation dans `tests/e2e/README.md`. Commande recommandee pour observation temps reel : `PLAYWRIGHT_SLOWMO=800 PLAYWRIGHT_FULL_MOTION=1 npm run test:e2e -- --headed 8-2-parcours-moussa`.

9. **Aucun nouveau `data-testid` introduit** : story 8.1 AC7 a pose tous les testids necessaires (`floating-chat-button`, `interactive-choice-yes/no`, `chat-textarea`, `chat-send-button`). Pas de modification de composants UI dans 8.2.

**Resultats validation**

- E2E 8-2 : 3/3 passed en 9.3 s ; 9/9 passed en `--repeat-each=3` (17.5 s, zero flake).
- E2E 8-1 non-regression : 2/2 passed en 31.5 s.
- Vitest : 353/354 passed (1 test `useGuidedTour.resilience` pre-existant en echec, confirme via `git stash` avant nos changements — hors scope 8.2).
- TypeScript : aucune nouvelle erreur introduite (6 erreurs pre-existantes sur `useChat.ts`, `useFocusTrap.ts`, `useGuidedTour.ts` — non liees).

### File List

Modifies :
- `frontend/tests/e2e/fixtures/users.ts` — ajout imports `FundSummary/MatchListResponse/FundListResponse`, alias `FundMatchListFixture`/`FundListFixture`, fixtures `MOUSSA`, `MOUSSA_COMPANY`, `MOUSSA_FINANCING_MATCHES`, `MOUSSA_FUNDS`.
- `frontend/tests/e2e/fixtures/sse-stream.ts` — ajout helpers `sseAssistantMessageWithConsentOnFinancing(...)` et `sseRefusalAcknowledgement(...)`.
- `frontend/tests/e2e/fixtures/mock-backend.ts` — extension `MockBackendOptions.financingData`, nouveau `ChatScenario`, 3 routes financing, branche 8.2 dans `handleChatPost` (nouvel argument `financingMatches`), constante `FINANCING_INTERACTIVE_QUESTION_ID`.
- `frontend/tests/e2e/README.md` — section « Convention fixtures par parcours » + commande mode visuel ralenti.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — `8-2-tests-e2e-parcours-moussa` : `ready-for-dev` → `in-progress` → `review`.

Crees :
- `frontend/tests/e2e/8-2-parcours-moussa.spec.ts` — 3 tests (AC3 contextuel, AC4 refus, AC5 glassmorphism) + helper local `setupUntilConsent(page)`.

Non modifies (verification explicite) :
- `frontend/playwright.config.ts`
- `frontend/tests/e2e/fixtures/auth.ts`
- `frontend/tests/e2e/8-1-parcours-fatou.spec.ts`
- `frontend/app/components/**` (aucun composant UI touche).

### Change Log

- 2026-04-15 : Implementation story 8.2 — parcours Moussa (guidage refuse, chat contextuel /financing, glassmorphism). 3 tests E2E verts, 9/9 en anti-flake x3, zero regression 8.1.
