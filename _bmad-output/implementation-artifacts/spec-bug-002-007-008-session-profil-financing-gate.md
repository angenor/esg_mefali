---
title: 'BUG-002 + BUG-007 + BUG-008 — Session reload, profil inline edit, onglet fonds ESG gate'
type: 'bugfix'
created: '2026-04-23'
status: 'done'
context: []
baseline_commit: '1cd17556c1650d7de347a6fd195d6df6ef839cab'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Trois bugs frontend découverts lors des tests manuels Vague 1 (2026-04-23) : (1) la session JWT est perdue au reload F5 et l'utilisateur est renvoyé vers `/login` ; (2) le bouton ✓ d'édition inline du profil ne semble pas déclencher le PATCH et les labels de la page ont des accents manquants ; (3) l'onglet « Tous les fonds » du module financement affiche « Évaluation ESG requise » au lieu du catalogue statique.

**Approach:** Ajouter un plugin `auth.client.ts` qui initialise le store avant la première navigation (BUG-002) ; corriger les accents dans `ProfileForm.vue` et `profile.vue` et améliorer le feedback d'erreur inline (BUG-007) ; restreindre la condition ESG error au seul onglet `recommendations` dans `financing/index.vue` (BUG-008).

## Boundaries & Constraints

**Always:** TypeScript strict (aucun `any`), dark mode préservé, aucune dépendance nouvelle, aucun test existant cassé.

**Ask First:** Si BUG-007 inline edit est toujours cassé après BUG-002 fix (PATCH non envoyé confirmé via DevTools Network) — stopper et signaler avant de modifier le composant ProfileField.

**Never:** Modifier le backend, modifier les migrations, modifier `ssr` dans `nuxt.config.ts`, toucher les tests backend.

## I/O & Edge-Case Matrix

| Scénario | État initial | Comportement attendu | Gestion erreur |
|----------|-------------|----------------------|----------------|
| BUG-002 — Reload F5 sur page protégée | Token valide dans localStorage, store vide | Page se charge normalement, pas de redirect | N/A |
| BUG-002 — Reload F5 sans token | localStorage vide | Redirect vers `/login` | N/A |
| BUG-007 — Clic ✓ avec session active | Champ modifié, token en store | PATCH envoyé, valeur mise à jour, feedback visuel | Message d'erreur inline si PATCH échoue |
| BUG-008 — Onglet « Tous les fonds » avec erreur ESG | `financingStore.error` contient 'esg' | Onglet fonds affiche le catalogue | Erreur ESG visible uniquement dans onglet `recommendations` |
| BUG-008 — Onglet fonds sans erreur | Pas d'erreur | Catalogue affiché normalement | N/A |

</frozen-after-approval>

## Code Map

- `frontend/app/plugins/auth.client.ts` — à créer ; initialise `loadFromStorage()` au démarrage SPA avant toute navigation
- `frontend/app/middleware/auth.global.ts` — retirer l'appel `loadFromStorage()` (pris en charge par le plugin) ; garder la logique de redirection
- `frontend/app/pages/profile.vue` — corriger 2 accents dans le template header ; améliorer le feedback d'erreur `updateProfile`
- `frontend/app/components/profile/ProfileForm.vue` — corriger 9 accents dans `identityFields`, `esgFields` et le template
- `frontend/app/pages/financing/index.vue` — restreindre la condition `v-else-if` ESG error (ligne 194) à `activeTab === 'recommendations'`

## Tasks & Acceptance

**Execution:**

- [x] `frontend/app/plugins/auth.client.ts` -- créer le fichier avec `defineNuxtPlugin(() => { const auth = useAuthStore(); auth.loadFromStorage() })` -- garantit que le token est chargé depuis localStorage avant la première exécution du middleware
- [x] `frontend/app/middleware/auth.global.ts` -- retirer le bloc `if (import.meta.client && !authStore.accessToken) { authStore.loadFromStorage() }` ; conserver uniquement les deux redirections -- élimine le double-chargement et simplifie le middleware
- [x] `frontend/app/components/profile/ProfileForm.vue` -- corriger dans `identityFields` : `"Nombre d'employés"`, `"Année de création"` ; dans `esgFields` : `"Gestion des déchets"`, `"Politique énergétique"`, `"Transparence financière"` ; dans le template : `"Identité & Localisation"`, `"Critères ESG"`, `"Mise à jour..."` -- BUG-007b accents
- [x] `frontend/app/pages/profile.vue` -- corriger dans le template : `"Complétez votre profil pour recevoir des conseils ESG personnalisés."` ; feedback erreur déjà présent via bloc `v-if="error"` existant -- BUG-007b + meilleur feedback erreur
- [x] `frontend/app/pages/financing/index.vue` -- modifier la ligne ~194 : ajouter `&& financingStore.activeTab === 'recommendations'` à la condition `v-else-if` de la div ESG error -- BUG-008 : le catalogue statique doit être accessible indépendamment de l'état ESG

**Acceptance Criteria:**

- Given un utilisateur authentifié sur une page protégée, when il fait F5, then la page se recharge normalement sans redirect vers `/login`
- Given un utilisateur sans token en localStorage, when il tente d'accéder à une page protégée après F5, then il est redirigé vers `/login`
- Given un utilisateur sur `/profile` avec session active, when il édite un champ et clique ✓, then le PATCH est envoyé et si une erreur survient elle est affichée inline
- Given la page `/profile`, when elle s'affiche, then tous les labels ont leurs accents corrects (Identité, Année, déchets, etc.)
- Given un utilisateur sur `/financing` sans évaluation ESG, when il clique sur l'onglet « Tous les fonds », then le catalogue des fonds s'affiche (pas de message « Évaluation ESG requise »)
- Given un utilisateur sur `/financing` sans évaluation ESG, when il est sur l'onglet « Recommandations », then le message « Évaluation ESG requise » s'affiche correctement

## Design Notes

**BUG-002 — Ordre d'exécution Nuxt 4 SPA** : avec `ssr: false`, les plugins `*.client.ts` s'exécutent au démarrage de l'app, avant la première navigation et donc avant les middlewares globaux. Le plugin `auth.client.ts` garantit que `accessToken` est hydraté depuis `localStorage` dès le boot, rendant le middleware robuste sans logique conditionnelle `import.meta.client`.

**BUG-007 — Vérification implémentateur** : si après le fix BUG-002 le bouton ✓ ne déclenche toujours pas le PATCH (vérifiable via DevTools onglet Network), inspecter `handleFieldUpdate` dans `profile.vue` (ligne 16-18) et confirmer que `updateProfile` est appelé. La chaîne emit est syntaxiquement correcte ; la cause la plus probable était un 401 silencieux dû à l'expiration de session (BUG-002).

## Verification

**Commands:**
- `cd frontend && npx tsc --noEmit` -- expected: 0 erreurs TypeScript
- `cd frontend && npm run lint` -- expected: 0 erreurs ESLint

**Manual checks (si no CLI):**
- F5 sur `/dashboard` après login → reste sur `/dashboard` (BUG-002)
- `/profile` → labels avec accents corrects partout (BUG-007b)
- `/financing` onglet « Tous les fonds » avec compte sans ESG → catalogue visible (BUG-008)

## Suggested Review Order

**BUG-002 — Auth session persistence (entrée principale)**

- Plugin créé : `loadFromStorage()` au boot SPA, garantit token avant toute navigation
  [`auth.client.ts:1`](../../frontend/app/plugins/auth.client.ts#L1)

- Middleware simplifié : suppression du double-chargement, logique de redirection inchangée
  [`auth.global.ts:3`](../../frontend/app/middleware/auth.global.ts#L3)

**BUG-008 — ESG gate restreinte à l'onglet recommandations**

- Condition `activeTab === 'recommendations'` ajoutée — catalogue statique accessible sans ESG
  [`financing/index.vue:194`](../../frontend/app/pages/financing/index.vue#L194)

**BUG-007b — Accents français (ProfileForm)**

- Labels identityFields : employés, Année de création
  [`ProfileForm.vue:34`](../../frontend/app/components/profile/ProfileForm.vue#L34)

- Labels esgFields : déchets, énergétique, financière
  [`ProfileForm.vue:42`](../../frontend/app/components/profile/ProfileForm.vue#L42)

- Template : Mise à jour…, Identité & Localisation, Critères ESG
  [`ProfileForm.vue:75`](../../frontend/app/components/profile/ProfileForm.vue#L75)

**BUG-007b — Accent (profile page header)**

- Sous-titre page : Complétez…personnalisés
  [`profile.vue:35`](../../frontend/app/pages/profile.vue#L35)

## Spec Change Log
