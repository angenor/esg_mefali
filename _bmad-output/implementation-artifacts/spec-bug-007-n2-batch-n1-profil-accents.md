---
title: 'BUG-007 N2 + Batch N1 — Bouton ✓ profil inline + accents login/register/layout/404'
type: 'bugfix'
created: '2026-04-23'
status: 'done'
route: 'one-shot'
context: []
---

## Intent

**Problem:** (1) Le bouton ✓ d'édition inline sur `/profile` n'envoie pas le PATCH backend — `useCompanyProfile.ts` utilisait `fetch()` brut sans cycle 401→refresh→retry, contrairement aux autres composables qui utilisent `apiFetch` de `useAuth`. (2) Cinq accents manquants découverts lors des tests Vague 1 : login (BUG-004), register (BUG-005), sidebar (BUG-003), et absence d'une page 404 française (BUG-010).

**Approach:** Migrer `useCompanyProfile.ts` vers `apiFetch`/`SessionExpiredError`/`ApiFetchError` de `useAuth` pour bénéficier du refresh token automatique et d'une gestion d'erreur cohérente ; corriger les 5 accents inline ; créer `app/error.vue` avec traduction française et dark mode complet.

## Suggested Review Order

**BUG-007 N2 — Migration apiFetch dans useCompanyProfile**

- Import `useAuth`, `SessionExpiredError`, `ApiFetchError` ; suppression `useAuthStore` et `fetch()` brut
  [`frontend/app/composables/useCompanyProfile.ts:1`](../../frontend/app/composables/useCompanyProfile.ts#L1)

- `updateProfile` : PATCH via `apiFetch` avec catch `SessionExpiredError` → `handleAuthFailure` + `ApiFetchError 422`
  [`frontend/app/composables/useCompanyProfile.ts:30`](../../frontend/app/composables/useCompanyProfile.ts#L30)

- `fetchProfile` et `fetchCompletion` alignés sur le même pattern
  [`frontend/app/composables/useCompanyProfile.ts:16`](../../frontend/app/composables/useCompanyProfile.ts#L16)

**Batch N1 — Accents BUG-003/004/005**

- Login : "Connectez-vous à votre compte" (accent ajouté sur "à")
  [`frontend/app/pages/login.vue:33`](../../frontend/app/pages/login.vue#L33)

- Register : "Créer un compte", "Minimum 8 caractères", "Déjà un compte ?"
  [`frontend/app/pages/register.vue:59`](../../frontend/app/pages/register.vue#L59)

- Sidebar : "Déconnexion" (accent ajouté sur "é")
  [`frontend/app/components/layout/AppSidebar.vue:143`](../../frontend/app/components/layout/AppSidebar.vue#L143)

**BUG-010 — Page 404 française avec dark mode**

- Nouvelle page Nuxt error.vue : statut HTTP, message FR contextuel 404 vs autre, bouton `clearError` retour accueil, dark mode complet
  [`frontend/app/error.vue:1`](../../frontend/app/error.vue#L1)
