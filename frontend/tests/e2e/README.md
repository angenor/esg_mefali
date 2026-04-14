# Tests E2E Playwright — ESG Mefali

Cette suite valide les parcours utilisateur de bout en bout avec Playwright 1.49.

## Commandes

```bash
# Installation initiale du navigateur (une fois apres clone)
npx playwright install chromium --with-deps

# Lancer toute la suite E2E
npm run test:e2e

# Un seul fichier (glob sur nom)
npm run test:e2e -- 8-1-parcours-fatou

# Mode visuel (voir le navigateur)
npm run test:e2e -- --headed

# Mode debug pas-a-pas (DevTools ouvert, pause automatique)
npm run test:e2e -- --debug

# Interface interactive Playwright (UI mode)
npm run test:e2e -- --ui

# Anti-flake : lancer 3 fois le meme test pour detecter les flakes
npm run test:e2e -- --repeat-each=3 8-1-parcours-fatou

# Voir le rapport HTML post-run
npx playwright show-report
```

## Strategie de mocking (backend entierement mocke)

Aucun backend reel (FastAPI/Postgres/Redis/OpenRouter) n'est demarre pour les tests E2E.
Toutes les routes `/api/**` sont interceptees via `page.route()` dans
`fixtures/mock-backend.ts` et renvoient :

- **JSON statique** pour les endpoints REST standards (user, profile, dashboard, carbon)
- **Streams SSE fabriques** (`data: {json}\n\n`) pour `POST /api/chat/.../messages`

Avantages :
- Tests deterministes (<10 s / spec, pas de latence LLM)
- Pas de dependance BDD ni Docker Compose
- Focus sur l'integration frontend (le backend a son propre test suite pytest)

## Convention de nommage des specs

```
{epic}-{num}-parcours-{prenom}.spec.ts
```

Exemples :
- `8-1-parcours-fatou.spec.ts` — guidage propose et accepte (multi-pages)
- `8-2-parcours-moussa.spec.ts` — guidage refuse (a venir)
- `8-3-parcours-aminata.spec.ts` — declenchement direct (a venir)

## Structure des fixtures

```
tests/e2e/fixtures/
├── users.ts         # TestUser, FATOU, FATOU_COMPANY, FATOU_CARBON_SUMMARY
├── auth.ts          # loginAs(page, user) — injection tokens localStorage
├── sse-stream.ts    # createSSEResponse() + helpers chat (consent, tour)
└── mock-backend.ts  # installMockBackend(page, options) — toutes les routes
```

**Ou ajouter de nouvelles fixtures ?**
- Nouvel utilisateur → `fixtures/users.ts`
- Nouveau scenario chat → ajouter `ChatScenario` dans `mock-backend.ts` + helper dans `sse-stream.ts`
- Route specifique a une story → utiliser `options.extraRoutes` de `installMockBackend()`
  pour etendre sans reecrire le mock global

## Debug — routes non mockees

Le mock installe un catch-all `page.route('**/api/**', ...)` qui renvoie 404 avec
un log `console.warn` pour toute route manquante. Lors de l'ajout d'une nouvelle
spec, verifier la sortie de `--headed` ou `--debug` pour reperer les warnings.

## Anti-flake — bonnes pratiques

1. Pas de `page.waitForTimeout(ms)` — utiliser `expect(...).toBeVisible({ timeout })`.
2. `reducedMotion: 'reduce'` active dans chaque `beforeEach`.
3. Selectors stables : `getByTestId`, `getByRole`, pas de chaines CSS fragiles.
4. Timeouts explicites sur les assertions post-SSE (`timeout: 10_000`).
5. `installMockBackend()` appele AVANT `page.goto()`.
