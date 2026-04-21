# Méthodologie — patterns transverses BMAD dev-stories

Ce document capitalise les patterns méthodologiques récurrents détectés lors
des code reviews Phase 4 (stories 10.x). Complément du CLAUDE.md racine,
orienté workflow dev-story + review plutôt que code applicatif.

## 1. Scan NFR66 Task 1 révèle dette cachée

**Pattern** : le scan exhaustif NFR66 en Task 1 d'une story d'abstraction
peut révéler **plus de sites de consommation** que la spec n'avait projeté.

**Exemple Story 10.13** : la spec annonçait 2 hits `OpenAIEmbeddings(`
(`documents/service.py:525, 530`) — le scan Task 1 en a trouvé **6 hits / 3
fichiers** (+ `financing/seed.py:851` + `financing/service.py:170`).

**Leçon** : systématiser en Task 1 le scan **par symbole absolu**
(`OpenAIEmbeddings(|text-embedding-3-small|ChatOpenAI\(`) plutôt que se
limiter aux callers documentés spec. Le scan remonte la dette cachée
avant que le sizing ne soit figé.

**Check-list Task 1 d'une story d'abstraction** :

```bash
# 1. Symboles vendor à remplacer (exhaustif, pas limité à la spec)
rg -n "<VendorClass>\(|<vendor_model_name>" backend/ \
    --glob '!backend/tests/**' \
    --glob '!backend/app/core/<new_abstraction>/**'

# 2. Colonnes ORM avec dimensions figées (si migration schéma requise)
rg -n "Vector\(<dim>\)" backend/app/models/ backend/alembic/

# 3. Appelants de la signature publique (shims legacy 10.6)
rg -n "<public_function>\(" backend/

# 4. Baseline pytest + coverage avant Task 2
source venv/bin/activate && pytest --collect-only -q | tail -1

# 5. Dry-run deps (évite pivot mi-story)
pip install --dry-run "<new-dep>>=<ver>"
```

Les résultats sont documentés dans Completion Notes §Scan NFR66 avec
comparaison attendu/réalisé — si écart > 0, **remonter la discussion scope
AVANT Task 2** plutôt que déférer silencieusement.

## 2. Pivot dépendance — dry-run précoce

**Pattern** : une version de dep spécifiée spec peut échouer à s'installer
(Python runtime moderne, conflits langchain-*, etc.). Détection en Task 1.5
par `pip install --dry-run` évite les pivots mi-story.

**Exemple Story 10.13** : spec exigeait `voyageai>=0.3.4`, dry-run résout
`voyageai-0.2.3` (dernière version PyPI compatible Python 3.14). Pivot
documenté Debug Log avec impact API surface (`voyageai.error.*`).

**Bonne pratique complémentaire** : pour chaque vendor SDK ajouté, créer un
test smoke `test_<vendor>_sdk_surface_compat` qui vérifie la présence des
attributs utilisés runtime. Fail-fast au prochain bump.

## 3. Calibration sizing XL infra vs XL temps réel

**Pattern** : une story XL (6-8 h projetés) d'**infrastructure provider**
(abstraction ABC + factory + migration + shim) se livre souvent en **1h30-2h**
réels car les patterns byte-identique 10.6 réduisent l'effort d'invention.

**Leçon** : ne pas confondre **XL scope** (nb de fichiers, surface couverte)
avec **XL temps réel** (complexité cognitive). Les stories XL de refactor
provider/ports-and-adapters sont souvent calibrables en L ou M si :

- Pattern parent existe (storage/ pour embeddings/, embeddings/ pour llm/).
- 8+ Q tranchées pré-dev (aucune décision durant impl).
- Tests unit mockés (pas E2E infra lourde).

**Signal d'alerte** : si la durée réelle est ≤ 30 % du sizing, vérifier
que les raccourcis pris (bench non exécuté, shim non branché, corpus
réduit) n'ont pas dégradé la satisfaction d'AC — sinon rectifier Completion
Notes honnêtement et déférer proprement.

## 4. Golden corpus + expected_ids validation

**Pattern** : tout test de qualité RAG (`recall@5`, `mrr`, `ndcg`) sur
corpus fixture doit inclure un **meta-test structurel** qui asserte :

1. Le corpus contient le nombre attendu de chunks (pas `>=`, mais `==`).
2. Les chunk IDs sont uniques.
3. **Chaque `expected_top5_chunk_ids` référence un chunk réel**.

Sans (3), un corpus désynchronisé de ses annotations ground-truth produit
des scores biaisés silencieusement (le recall est plafonné artificiellement
— e.g. 1/5 si un seul expected chunk existe).

**Implémentation référence** : `backend/tests/test_core/test_embeddings_quality.py::test_corpus_structure_is_valid`
(Story 10.13 post-review CRITICAL-1 2026-04-21).

## 5. Règle 10.5 no-duplication : scan AST-aware

**Pattern** : le scan `rg "VendorClass\("` pour enforce l'unicité
d'instantiation peut flaguer des **docstrings historiques** qui mentionnent
le vendor sans le réinstantier. Faux positif.

**Solution** : test Python qui parse l'AST, identifie les plages de
docstrings (`ast.Expr` + `ast.Constant` str de type module/function/class),
et scanne uniquement le code exécutable.

**Implémentation référence** : `test_financing_service_uses_embedding_provider`
(Story 10.13 post-review HIGH-3 2026-04-21).

## Références

- [Story 10.13 code review](../../_bmad-output/implementation-artifacts/10-13-code-review-2026-04-21.md)
- [CLAUDE.md](../../CLAUDE.md) — conventions dev globales
- [rag.md §6](./rag.md) — pattern corpus validation (détails techniques)
