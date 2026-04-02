# Implementation Plan: Correction du Routing Multi-tour LangGraph et du Format Timeline

**Branch**: `013-fix-multiturn-routing-timeline` | **Date**: 2026-04-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/013-fix-multiturn-routing-timeline/spec.md`

## Summary

Deux corrections : (1) ajouter un mecanisme de "module actif" (`active_module`) dans le `ConversationState` pour que le routeur LangGraph maintienne le contexte entre les tours de conversation, resolvant le bug ou les reponses aux questions des noeuds specialistes sont reroutees vers `chat_node` ; (2) normaliser le format des blocs timeline (frontend tolerant aux variantes + prompts standardises sur `events`).

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.x strict (frontend)
**Primary Dependencies**: FastAPI, LangGraph (>=0.2.0), LangChain (>=0.3.0), langchain-openai (>=0.3.0), SQLAlchemy async, Nuxt 4, Vue Composition API
**Storage**: PostgreSQL 16 + pgvector, MemorySaver (LangGraph checkpointer)
**Testing**: pytest (backend), Vitest (frontend)
**Target Platform**: Web (serveur Linux, navigateur)
**Project Type**: Web application (monolithe modulaire)
**Performance Goals**: La classification de changement de sujet (appel LLM) doit ajouter < 2s de latence supplementaire
**Constraints**: Zero regression sur les 796 tests passants, compatibilite avec le checkpointer existant
**Scale/Scope**: ~832 tests existants, 9 noeuds de graphe, 32 tools LangChain

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Statut | Justification |
|----------|--------|---------------|
| I. Francophone-First | PASS | Pas de changement UI, messages d'erreur existants en francais |
| II. Architecture Modulaire | PASS | Modification dans les frontieres du module Agent Conversationnel uniquement |
| III. Conversation-Driven UX | PASS | Le fix ameliore directement l'experience conversationnelle multi-tour |
| IV. Test-First | PASS | Tests unitaires et integration prevus pour chaque modification |
| V. Securite & Donnees | PASS | Pas de nouvelle donnee sensible, pas de changement d'authentification |
| VI. Inclusivite | PASS | Pas d'impact sur l'accessibilite |
| VII. Simplicite & YAGNI | PASS | 2 champs ajoutes au state (minimal), classification binaire simple |

**Post-Phase 1 re-check**: L'appel LLM pour la classification de changement de sujet ajoute une dependance externe dans le routeur. Justification : c'est le mecanisme le plus simple et fiable pour cette classification. L'alternative par mots-cles est trop fragile.

## Project Structure

### Documentation (this feature)

```text
specs/013-fix-multiturn-routing-timeline/
├── plan.md              # Ce fichier
├── spec.md              # Specification
├── research.md          # Decisions et alternatives
├── data-model.md        # Modele de donnees
├── quickstart.md        # Guide de demarrage rapide
├── contracts/           # Contrats d'interface
│   ├── state-contract.md
│   └── timeline-format-contract.md
└── tasks.md             # (genere par /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── graph/
│   │   ├── state.py          # MODIFIE: +active_module, +active_module_data
│   │   ├── nodes.py          # MODIFIE: router_node + noeuds specialistes
│   │   └── graph.py          # (pas de modification directe prevue)
│   └── prompts/
│       ├── action_plan.py    # MODIFIE: phases → events
│       ├── carbon.py         # MODIFIE: items → events
│       └── financing.py      # MODIFIE: items → events
└── tests/
    ├── test_graph/
    │   ├── test_graph_routing.py    # MODIFIE: +tests multi-tour
    │   └── test_active_module.py    # NOUVEAU: tests module actif
    └── test_timeline_format.py      # NOUVEAU: tests format timeline

frontend/
├── app/
│   ├── components/
│   │   └── richblocks/
│   │       └── TimelineBlock.vue    # MODIFIE: normalisation variantes
│   └── types/
│       └── richblocks.ts            # (pas de modification)
└── tests/                           # NOUVEAU: test TimelineBlock
```

**Structure Decision**: Architecture existante conservee. Modifications chirurgicales dans les fichiers existants, 2-3 nouveaux fichiers de tests uniquement.

## Complexity Tracking

Aucune violation de la constitution a justifier. Le design est minimal : 2 champs au state, 1 appel LLM conditionnel dans le routeur, normalisation frontend.

## Implementation Phases

### Phase 1: State + Router (BUG-1 core)

**Objectif**: Le routeur maintient le module actif entre les tours.

1. Modifier `state.py` : ajouter `active_module` et `active_module_data`
2. Modifier `router_node` dans `nodes.py` :
   - Lire `active_module` du state
   - Si defini : appel LLM classification binaire (continuation vs changement)
   - Si continuation : router vers `active_module` via le flag `_route_*` correspondant
   - Si changement : reset `active_module`, classifier normalement
   - Si non defini : comportement actuel inchange
3. Tests unitaires : router avec/sans module actif, detection changement de sujet

### Phase 2: Noeuds specialistes (BUG-1 complet)

**Objectif**: Chaque noeud gere le cycle de vie du module actif.

1. Modifier chaque noeud specialiste pour :
   - Activer `active_module` + `active_module_data` au demarrage de session
   - Mettre a jour `active_module_data` a chaque action
   - Desactiver `active_module` a la finalisation
2. Gerer la reprise : si `active_module` est defini mais pas de session en cours → lire session in_progress depuis la base
3. Tests integration : echange multi-tour ESG (5 Q/R), carbone (3 entrees), changement de module

### Phase 3: Timeline (BUG-2)

**Objectif**: Les blocs timeline s'affichent correctement.

1. Modifier `TimelineBlock.vue` : normalisation des variantes (phases/items → events, aliases de champs, defaut status)
2. Modifier prompts `action_plan.py`, `carbon.py`, `financing.py` : standardiser sur format `events`
3. Tests : parsing des variantes, JSON invalide, champs manquants

### Phase 4: Non-regression + Integration finale

**Objectif**: Zero regression, validation de bout en bout.

1. Executer la suite de tests complete (832 tests)
2. Verifier que les 796 tests passants restent verts
3. Verifier les nouveaux tests
4. Test manuel du parcours multi-tour complet
