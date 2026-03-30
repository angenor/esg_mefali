<!--
  Sync Impact Report
  Version change: 0.0.0 → 1.0.0
  Modified principles: N/A (initial creation)
  Added sections:
    - 7 Core Principles (Francophone-First, Architecture Modulaire,
      Conversation-Driven, Test-First, Securite & Donnees,
      Inclusivite, Simplicite)
    - Contraintes Techniques
    - Workflow de Developpement
    - Governance
  Removed sections: N/A
  Templates requiring updates:
    - .specify/templates/plan-template.md ✅ (Constitution Check compatible)
    - .specify/templates/spec-template.md ✅ (user stories compatible)
    - .specify/templates/tasks-template.md ✅ (phase structure compatible)
    - .specify/templates/checklist-template.md ✅ (no conflict)
  Follow-up TODOs: none
-->

# ESG Mefali Constitution

## Core Principles

### I. Francophone-First & Contextualisation Africaine

Toute fonctionnalite DOIT etre concue pour les PME africaines
francophones (zone UEMOA/CEDEAO) en priorite.

- L'interface utilisateur DOIT etre integralement en francais.
- Le code source (variables, fonctions, classes) DOIT etre en anglais.
- Les commentaires et la documentation DOIVENT etre en francais.
- Les referentiels ESG DOIVENT integrer les taxonomies vertes UEMOA,
  BCEAO et les reglementations CEDEAO avant les standards
  internationaux.
- Le secteur informel DOIT etre pris en compte dans tous les modules
  (scoring, profilage, financement).

### II. Architecture Modulaire

Le projet est structure en 8 modules independants qui DOIVENT
rester faiblement couples.

- Chaque module (Agent Conversationnel, Analyseur ESG, Conseiller
  Financement, Calculateur Carbone, Scoring Credit, Plan d'Action,
  Tableau de Bord, Extension Chrome) DOIT avoir des frontieres
  claires.
- Les modules communiquent via des API internes definies
  (schemas Pydantic cote backend, types TypeScript cote frontend).
- Un module DOIT pouvoir etre developpe, teste et deploye
  independamment des autres.
- Les dependances entre modules DOIVENT etre explicites et
  documentees.

### III. Conversation-Driven UX

L'experience utilisateur DOIT privilegier l'approche
conversationnelle plutot que les formulaires complexes.

- L'agent IA guide l'utilisateur pas a pas via le chat.
- Les informations sont collectees de maniere conversationnelle
  et non via des formulaires multi-champs.
- Le profilage entreprise se fait progressivement au fil des
  echanges.
- La memoire contextuelle DOIT persister entre les sessions.

### IV. Test-First (NON-NEGOTIABLE)

Le developpement suit obligatoirement le cycle TDD :
Red-Green-Refactor.

- Les tests DOIVENT etre ecrits AVANT l'implementation.
- Couverture minimale : 80%.
- Types de tests requis : unitaires, integration, E2E pour les
  parcours critiques.
- Backend : pytest. Frontend : Vitest + Playwright (E2E).
- Aucun code ne DOIT etre merge sans tests correspondants.

### V. Securite & Protection des Donnees

Les donnees des PME (financieres, ESG, Mobile Money) sont
sensibles et DOIVENT etre protegees.

- Aucun secret (cle API, mot de passe, token) ne DOIT etre
  present dans le code source.
- Toutes les entrees utilisateur DOIVENT etre validees
  (schemas Pydantic backend, Zod/Valibot frontend).
- Les donnees Mobile Money et scoring DOIVENT etre collectees
  uniquement avec consentement explicite.
- Les requetes SQL DOIVENT utiliser des requetes parametrees
  (SQLAlchemy ORM, jamais de concatenation).
- L'API DOIT implementer l'authentification, l'autorisation
  et le rate limiting.

### VI. Inclusivite & Accessibilite

La plateforme DOIT etre accessible aux utilisateurs peu
familiers avec le numerique.

- L'interface DOIT fonctionner sur des connexions lentes
  (optimisation des assets, lazy loading).
- Le support vocal (speech-to-text) DOIT etre prevu des
  la conception.
- Les messages d'erreur DOIVENT etre en francais, clairs
  et actionnables.
- Le mode guide DOIT etre disponible pour les nouveaux
  utilisateurs.

### VII. Simplicite & YAGNI

Commencer simple, complexifier uniquement quand c'est
justifie par un besoin reel.

- Pas de microservices : monolithe modulaire (FastAPI backend,
  Nuxt frontend).
- Stockage local avant MinIO/S3.
- Traitement synchrone avant Redis/Celery.
- Pas d'abstraction prematuree : trois lignes similaires
  valent mieux qu'une abstraction speculative.
- Chaque ajout de complexite DOIT etre justifie par un
  besoin utilisateur concret.

## Contraintes Techniques

### Stack Obligatoire

- **Frontend** : Nuxt 4 + Vue Composition API + Pinia +
  TailwindCSS + GSAP + Chart.js + LangGraph/LangChain
- **Backend** : FastAPI (Python) + SQLAlchemy + Alembic
- **LLM** : Claude API (Anthropic) via OpenRouter
- **BDD** : PostgreSQL + pgvector
- **Extension** : Chrome Extension (Manifest V3)

### Conventions de Nommage

| Contexte | Convention |
|----------|-----------|
| Tables BDD | snake_case, pluriel (`companies`, `esg_scores`) |
| Python (fonctions, variables) | snake_case |
| TypeScript/Vue composants | PascalCase |
| Routes API | kebab-case (`/api/esg-scores`) |
| Fichiers Python | snake_case.py |
| Fichiers Vue | PascalCase.vue |

### Limites de Taille

- Fonctions : < 50 lignes
- Fichiers : < 800 lignes (ideal 200-400)
- Nesting : < 4 niveaux

## Workflow de Developpement

### Processus Obligatoire

1. **Recherche** : chercher des implementations existantes
   (GitHub, npm, PyPI) avant d'ecrire du code nouveau.
2. **Specification** : utiliser `/speckit.specify` pour
   formaliser les exigences.
3. **Planification** : utiliser `/speckit.plan` pour definir
   l'architecture technique.
4. **TDD** : ecrire les tests d'abord, implementer ensuite.
5. **Revue** : utiliser les agents de revue (code-reviewer,
   security-reviewer) avant tout merge.
6. **Commit** : messages conventionnels
   (`feat:`, `fix:`, `refactor:`, etc.).

### ODD de Reference

Chaque fonctionnalite DEVRAIT contribuer a au moins un ODD :
- ODD 8 (Travail decent), ODD 9 (Innovation),
  ODD 10 (Inclusion financiere), ODD 12 (Production responsable),
  ODD 13 (Climat), ODD 17 (Partenariats).

## Governance

Cette constitution est le document directeur du projet
ESG Mefali. Elle prevaut sur toute autre convention ou
pratique en cas de conflit.

### Amendements

- Toute modification DOIT etre documentee dans le Sync
  Impact Report en tete de ce fichier.
- Le versioning suit le schema semantique :
  - MAJOR : suppression ou redefinition de principes.
  - MINOR : ajout de principe ou expansion significative.
  - PATCH : clarifications, corrections mineures.
- Toute modification de principe DOIT entrainer une
  verification de coherence avec les templates
  (spec, plan, tasks, checklist).

### Conformite

- Chaque PR/revue DOIT verifier la conformite avec
  ces principes.
- La complexite ajoutee DOIT etre justifiee (voir
  Complexity Tracking dans plan-template).
- Le fichier CLAUDE.md a la racine du projet DOIT
  rester synchronise avec cette constitution.

**Version**: 1.0.0 | **Ratified**: 2026-03-30 | **Last Amended**: 2026-03-30
