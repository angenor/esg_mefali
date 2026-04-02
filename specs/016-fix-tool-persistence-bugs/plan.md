# Implementation Plan: Fix Tool Persistence & Routing Bugs

**Branch**: `016-fix-tool-persistence-bugs` | **Date**: 2026-04-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/016-fix-tool-persistence-bugs/spec.md`

## Summary

Corriger 5 bugs identifiés lors des tests d'intégration : le LLM crée les évaluations mais ne persiste pas les données détaillées (critères ESG, entrées carbone) via les tools de sauvegarde. Cause racine : prompts insuffisamment directifs et incohérences entre prompt statique et instructions tool calling injectées dans les nodes. Correction secondaire du rendu gauge bloqué et du comportement face aux données inexistantes.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.x strict (frontend)
**Primary Dependencies**: FastAPI, LangGraph (>=0.2.0), LangChain (>=0.3.0), langchain-openai, SQLAlchemy async, Nuxt 4, Vue Composition API
**Storage**: PostgreSQL 16 + pgvector
**Testing**: pytest (backend), Vitest (frontend)
**Target Platform**: Web application (serveur Linux + navigateur)
**Project Type**: web-service (monolithe modulaire)
**Performance Goals**: Réponse LLM < 30s, tool calling loop max 5 itérations
**Constraints**: request_timeout=60 pour LLM, streaming SSE
**Scale/Scope**: 8 modules, 9 nodes LangGraph, 32+ tools

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Statut | Justification |
|----------|--------|---------------|
| I. Francophone-First | PASS | Modifications de prompts en français, aucun impact UI |
| II. Architecture Modulaire | PASS | Corrections ciblées par module (ESG, carbone, financement), pas de couplage inter-modules |
| III. Conversation-Driven UX | PASS | Améliore l'UX conversationnelle en forçant la persistance des données collectées par le chat |
| IV. Test-First (NON-NEGOTIABLE) | PASS | Tests unitaires pour chaque prompt modifié, tests d'intégration pour les tool calls |
| V. Sécurité & Protection des Données | PASS | Aucune donnée sensible exposée, pas de changement d'authentification |
| VI. Inclusivité & Accessibilité | PASS | Améliore l'accessibilité en garantissant le rendu des blocs visuels |
| VII. Simplicité & YAGNI | PASS | Corrections minimales (prompts + 1 composant frontend), pas d'abstraction nouvelle |

## Project Structure

### Documentation (this feature)

```text
specs/016-fix-tool-persistence-bugs/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (léger, pas de nouveau modèle)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── prompts/
│   │   ├── esg_scoring.py      # [MODIFY] Renforcer section SAUVEGARDE + REGLE ABSOLUE
│   │   ├── carbon.py           # [MODIFY] Ajouter REGLE ABSOLUE save_emission_entry
│   │   ├── financing.py        # [MODIFY] Ajouter REGLE ABSOLUE search_compatible_funds
│   │   └── system.py           # [MODIFY] Ajouter instruction correction données inexistantes
│   └── graph/
│       └── nodes.py            # [MODIFY] Aligner tool_instructions ESG avec batch_save
└── tests/
    └── unit/
        └── prompts/            # [MODIFY] Tests de conformité des prompts

frontend/
├── app/
│   ├── composables/
│   │   └── useMessageParser.ts # [INSPECT] Vérifier handling blocs incomplets
│   └── components/
│       ├── richblocks/
│       │   └── BlockPlaceholder.vue  # [INSPECT] Timeout pour blocs bloqués
│       └── chat/
│           └── MessageParser.vue     # [MODIFY] Fallback pour blocs incomplets post-streaming
└── tests/                      # [ADD] Tests rendu gauge
```

**Structure Decision**: Corrections in-place dans les fichiers existants. Pas de nouveau module ni nouveau fichier source.

## Complexity Tracking

Aucune violation de la constitution. Pas de complexité ajoutée.
