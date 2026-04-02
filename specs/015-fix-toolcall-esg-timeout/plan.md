# Implementation Plan: Correction des 3 anomalies bloquant les tests d'intégration

**Branch**: `015-fix-toolcall-esg-timeout` | **Date**: 2026-04-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/015-fix-toolcall-esg-timeout/spec.md`

## Summary

Corriger 3 anomalies empechant les tests d'integration de passer (29/36 actuellement) :
- **Anomalie 3** : Le module candidature ne declenche pas les tool calls (prompt trop passif + tool `create_fund_application` manquant)
- **Anomalie 4** : Le module credit ne declenche pas les tool calls (prompt insuffisamment directif)
- **Anomalie 5** : L'evaluation ESG timeout lors de la sauvegarde de 30 criteres sequentiels (besoin d'un tool batch)

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.x strict (frontend)
**Primary Dependencies**: FastAPI, LangGraph (>=0.2.0), LangChain (>=0.3.0), langchain-openai, SQLAlchemy async
**Storage**: PostgreSQL 16 + pgvector, MemorySaver (LangGraph checkpointer)
**Testing**: pytest (backend), Vitest (frontend)
**Target Platform**: Linux server (backend), Web browser (frontend)
**Project Type**: Web service (monolithe modulaire)
**Performance Goals**: Finalisation ESG < 15 secondes, tool call latence ~1-2s
**Constraints**: Timeout SSE actuellement non configure (defaut httpx ~30-60s), LLM via OpenRouter sans timeout explicite
**Scale/Scope**: PME africaines francophones, 8 modules LangGraph

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Statut | Notes |
|----------|--------|-------|
| I. Francophone-First | PASS | Prompts en francais, UI inchangee |
| II. Architecture Modulaire | PASS | Modifications limitees aux modules concernes (application, credit, esg) |
| III. Conversation-Driven UX | PASS | Les corrections renforcent l'approche conversationnelle en forcant le tool calling |
| IV. Test-First | PASS | Tests existants comme criteres d'acceptation, nouveaux tests pour batch ESG |
| V. Securite & Donnees | PASS | Pas de nouvelle surface d'attaque, validation Pydantic existante |
| VI. Inclusivite | PASS | Messages d'erreur en francais, ton pedagogique |
| VII. Simplicite & YAGNI | PASS | Corrections minimales, pas de nouvelle abstraction |

## Project Structure

### Documentation (this feature)

```text
specs/015-fix-toolcall-esg-timeout/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A - pas de nouvelle API)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── prompts/
│   │   ├── application.py     # MODIFIER — renforcer l'instruction tool calling
│   │   ├── credit.py          # MODIFIER — renforcer l'instruction tool calling
│   │   └── esg_scoring.py     # MODIFIER — ajouter instruction batch
│   ├── graph/
│   │   ├── nodes.py           # INCHANGE — architecture tool loop deja correcte
│   │   └── tools/
│   │       ├── application_tools.py  # MODIFIER — ajouter create_fund_application
│   │       ├── credit_tools.py       # INCHANGE
│   │       └── esg_tools.py          # MODIFIER — ajouter batch_save_esg_criteria
│   └── core/
│       └── config.py          # MODIFIER — ajouter timeout LLM
└── tests/
    └── test_prompts/          # MODIFIER — tests pour les corrections
```

**Structure Decision**: Backend uniquement, modifications chirurgicales dans 5-6 fichiers existants.

## Analyse Technique Detaillee

### Anomalie 3 — Module Candidature

**Diagnostic reel** (different de l'hypothese initiale) :

1. **Le prompt `application.py` n'est PAS bloque par des instructions JSON** — il n'y a aucune instruction "JSON only". Le probleme est que le ROLE est trop passif : "Tu informes l'utilisateur sur l'etat de ses dossiers de candidature, expliques les prochaines etapes, donnes des conseils". Ce role d'informateur ne pousse pas le LLM a AGIR (creer des dossiers, generer des sections).

2. **Le tool `create_fund_application` est ABSENT** de `application_tools.py`. Les tools existants supposent qu'un dossier existe deja (`application_id` requis). Le LLM ne peut pas creer de dossier car il n'a pas le tool pour le faire.

3. **L'architecture tool calling est correcte** : `graph.py` utilise `create_tool_loop` avec `ToolNode` et boucle conditionnelle (max 5 iterations). Le noeud `application_node` fait bien `bind_tools`.

**Corrections** :
- Ajouter le tool `create_fund_application` dans `application_tools.py`
- Reecrire le prompt `application.py` avec un ROLE actif et des instructions explicites d'utilisation des tools
- Le noeud `application_node` dans `nodes.py` n'a PAS besoin de modification

### Anomalie 4 — Module Credit

**Diagnostic reel** :

1. **Le prompt `credit.py` est deja correct** sur le fond — le ROLE dit "Tu generes et expliques un score" et les instructions tool du noeud disent "N'estime JAMAIS un score manuellement". Le probleme est probablement lie a la formulation trop faible du prompt principal qui ne mentionne pas explicitement les noms des tools.

2. **Les tools credit existent** et sont correctement lies.

**Corrections** :
- Renforcer le prompt `credit.py` avec des noms de tools explicites et une REGLE ABSOLUE (comme fait pour action_plan)
- Pas de nouveau tool necessaire

### Anomalie 5 — ESG Timeout

**Diagnostic confirme** :

1. **`save_esg_criterion_score` fait 1 write en base par appel** (update assessment_data, evaluated_criteria, current_pillar, status). Pour 30 criteres = 30 transactions.

2. **`finalize_esg_assessment` ne re-sauvegarde PAS les criteres** — il lit les `criteria_scores` deja en base et appelle `finalize_assessment_with_benchmark`. C'est correct.

3. **Le probleme est cote LLM** : le LLM doit generer 30 tool_calls sequentiels (un par critere), chacun etant un aller-retour complet. Avec la boucle max 5 du graphe, ca ne peut meme pas aller au-dela de 5 criteres par tour.

4. **`get_llm()` n'a pas de timeout** configure (ni `request_timeout` ni `timeout`).

**Corrections** :
- Ajouter `batch_save_esg_criteria` dans `esg_tools.py` pour sauvegarder N criteres en une seule operation
- Mettre a jour le prompt `esg_scoring.py` pour instruire l'utilisation du batch
- Ajouter `request_timeout=60` dans `get_llm()`
- Considerer l'augmentation de `MAX_TOOL_CALLS_PER_TURN` de 5 a 10 pour les evaluations ESG

## Complexity Tracking

Aucune violation de complexite. Modifications chirurgicales dans des fichiers existants.
