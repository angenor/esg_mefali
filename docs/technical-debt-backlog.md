# Backlog Dette Technique — identifiée par bmad-document-project

**Date du scan :** 2026-04-12
**Source :** BMAD `bmad-document-project` (scan profond)
**Statut :** à prioriser et traiter dans des features dédiées

## Dettes identifiées

### 1. CORS en dur sur `localhost:3000`
- **Impact :** bloquant pour déploiement multi-environnement
- **Action :** externaliser via variable d'env `CORS_ORIGINS` (liste séparée par virgules)
- **Priorité :** haute (avant prochain déploiement)

### 2. Rate limiting absent côté backend
- **Impact :** vulnérabilité DoS / abus API LLM (coûts OpenRouter)
- **Action :** ajouter `slowapi` sur les endpoints sensibles (`/api/chat/*`, `/api/documents/upload`) ou reverse-proxy Nginx
- **Priorité :** haute

### 3. Refresh token automatique côté frontend incomplet
- **Impact :** UX dégradée, déconnexions surprises
- **Action :** compléter `useAuth` avec intercepteur 401 → refresh → retry
- **Priorité :** moyenne

### 4. Couverture de tests frontend très faible (2 tests unitaires)
- **Impact :** régressions non détectées côté Vue/Nuxt
- **Action :** ajouter Vitest + tests composants critiques (`ChatMessage`, `InteractiveQuestionHost`, `DashboardCards`)
- **Priorité :** moyenne
- **Cible :** 40%+ de couverture frontend

### 5. `components/ui/` presque vide — règle de réutilisabilité non respectée
- **Impact :** duplication de code, maintenance coûteuse
- **Action :** extraire patterns répétés (cartes, inputs, boutons, modals, badges) en composants génériques parametrables
- **Priorité :** moyenne
- **Référence :** `CLAUDE.md` → section « Réutilisabilité des Composants (OBLIGATOIRE) »

### 6. Python venv en 3.14 alors que la convention projet demande 3.12
- **Impact :** risque de divergence runtime prod vs dev
- **Action :** vérifier que Docker/CI utilise bien 3.12, ou mettre à jour `CLAUDE.md` si on valide 3.14
- **Priorité :** faible à moyenne (à clarifier)

### 7. Versioning API manquant (`/v1/`)
- **Impact :** difficulté d'évolution API sans breaking changes
- **Action :** préfixer tous les endpoints par `/api/v1/` avant une API publique
- **Priorité :** moyenne (avant toute ouverture publique)

### 8. `SECRET_KEY` par défaut encore dans `.env.example`
- **Impact :** risque de fuite si quelqu'un oublie de générer une clé unique en prod
- **Action :** remplacer par placeholder explicite `CHANGE_ME_IN_PROD_$(openssl rand -hex 32)` et documenter la génération
- **Priorité :** haute (sécurité)

## Prochaines étapes

Ces dettes peuvent être traitées individuellement comme de petites features via le workflow BMAD standard (`bmad-create-prd` ou `bmad-quick-dev` pour les plus simples).
