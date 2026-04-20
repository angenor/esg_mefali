---
title: "Socle RAG refactor + intégration ≥ 5 modules"
epic_number: 19
status: planned
story_count: 2
stories: [19.1, 19.2]
dependencies:
  - epic: 10
    type: blocking
    reason: "Infra catalogue + StorageProvider"
  - story: 9.13
    type: related
    reason: "Consomme l'abstraction refactorisée pour le module applications (FR-005 spec 009)"
  - epic: 14
    type: blocking_phase1
    reason: "Phase 1 intégration ≥ 5 modules nécessite FundApplication livré"
  - epic: 15
    type: blocking_phase1
    reason: "Phase 1 intégration ≥ 5 modules nécessite deliverables"
fr_covered: [FR70, FR71]
nfr_renforces: [NFR43, NFR52]
qo_rattachees: []
notes: "Phase 0 = socle RAG refactor (abstraction réutilisable cross-module). Phase 1 = intégration ≥ 5 modules (applications FR-005 + carbon + credit + action_plan + 1 autre). Phase 4 = extension 8/8 modules."
---

## Epic 19 — Stories détaillées (Socle RAG refactor + intégration cross-module)

### Story 19.1 : Socle RAG refactor — abstraction réutilisable cross-module

**As a** Équipe Mefali (backend/AI),
**I want** refactoriser l'usage du RAG pgvector (livré spec 004) en une abstraction réutilisable (`RagService` avec méthodes typées `search(query, scope, top_k)`, `cite(chunks) -> Citations`, `chunk_document(doc) -> Chunks`) consommant l'`EmbeddingProvider` Voyage (Story 10.13),
**So that** les 5+ modules consommateurs (applications, carbon, credit, action_plan, puis 8/8 Phase 4) n'implémentent pas chacun leur propre pattern RAG (anti-duplication).

**Metadata (CQ-8)** — `fr_covered`: [FR70 partiel, FR71 partiel] · `nfr_covered`: [NFR43, NFR52, NFR60] · `phase`: 0 · `cluster`: RAG transversal · `estimate`: L · `depends_on`: [Story 10.13 Voyage, spec 004 pgvector livré]

**Acceptance Criteria**

**AC1** — **Given** `backend/app/core/rag/`, **When** auditée, **Then** elle contient `service.py` (`RagService` — interface stable), `chunker.py` (stratégies chunking par type de document), `citation.py` (formateur de citations avec nom fichier + page), `cache.py` (cache LRU optionnel).

**AC2** — **Given** l'abstraction, **When** consommée par Story 9.13 (RAG applications) ou par Story 19.2 (extension cross-module), **Then** aucune duplication du pattern pgvector dans les modules consommateurs (tous passent par `RagService`).

**AC3** — **Given** `RagService.search(query, scope={project_id, document_types?}, top_k=5)`, **When** invoquée, **Then** elle appelle `EmbeddingProvider.embed(query)` puis exécute la query pgvector avec les bons filtres RLS + retourne les chunks ordonnés par similarity score.

**AC4** — **Given** `RagService.cite(chunks)`, **When** invoquée, **Then** elle retourne un format structuré `[{fichier: str, page: int, chunk_excerpt: str, confidence: float}]` utilisable dans les prompts ou rendu UI.

**AC5** — **Given** le refactor, **When** les modules existants (documents spec 004, chat) sont migrés vers `RagService`, **Then** aucune régression fonctionnelle **And** tous les tests existants restent verts.

**AC6** — **Given** les tests, **When** `pytest backend/tests/test_core/test_rag_service.py` exécuté, **Then** scénarios (search avec scope, cite format, chunker par type doc, cache hit/miss, RLS isolation) verts + coverage ≥ 85 %.

---

### Story 19.2 : Intégration `RagService` aux modules cross-functional (carbon + credit + action_plan)

**As a** PME User,
**I want** que les modules carbon (spec 007), credit (spec 010), action_plan (spec 011) bénéficient également du RAG documentaire pour ancrer leurs analyses dans mes documents uploadés (pas seulement applications FR-005 traité par Story 9.13),
**So that** le signal PRD 6 « RAG transversal ≥ 5 modules MVP » (FR70 + SC-T9) soit tenu.

**Metadata (CQ-8)** — `fr_covered`: [FR70 complet, FR71 complet] · `nfr_covered`: [NFR60] · `phase`: 1 · `cluster`: RAG transversal · `estimate`: L · `depends_on`: [Story 19.1, Story 9.13 RAG applications (consommateur de référence)]

**Acceptance Criteria**

**Liste explicite des 5 modules consommateurs MVP** (arbitrage Lot 7) :
1. **`esg_service`** (spec 005 existant) — reconnecté à `RagService` abstraction (retire l'usage direct de pgvector spec 004).
2. **`applications_service`** — consomme via Story 9.13 (FR-005 promesse tenue).
3. **`carbon_service`** (spec 007) — nouvelle intégration RAG.
4. **`credit_service`** (spec 010) — nouvelle intégration RAG.
5. **`action_plan_service`** (spec 011) — nouvelle intégration RAG.

**AC1** — **Given** `esg_service`, **When** un verdict multi-référentiel est calculé (Story 13.4b materialization), **Then** `RagService.search(query, scope={project_id, document_types: ['bilan', 'politique_sst']})` est invoqué pour **renforcer** la traçabilité des facts utilisés (Story 13.5) avec citations documentaires vers les preuves originales (FR71) **And** le code legacy spec 005 appelant pgvector directement est migré vers `RagService` (pas de duplication).

**AC2** — **Given** `applications_service` via Story 9.13, **When** `generate_section` est exécutée, **Then** elle consomme `RagService` de l'abstraction Story 19.1 (pas de 2ᵉ pattern RAG recréé).

**AC3** — **Given** `carbon_service` (spec 007), **When** un bilan carbone est analysé, **Then** `RagService` cherche dans les documents uploadés (factures énergie, rapports transport) des éléments confirmant les valeurs déclarées **And** les chunks pertinents sont cités dans le rapport de bilan (FR71).

**AC4** — **Given** `credit_service` (spec 010), **When** le score crédit est calculé, **Then** `RagService` cherche des preuves complémentaires (historique bancaire, relevés Mobile Money documentés) **And** les citations renforcent la justification du score.

**AC5** — **Given** `action_plan_service` (spec 011), **When** le plan est généré par Claude, **Then** `RagService` fournit des extraits documentaires ciblant les faiblesses identifiées ESG (ex. « politique SST manquante » → cherche si un document interne existe déjà).

**AC6** — **Given** les 5 modules listés, **When** SC-T9 est vérifié, **Then** **exactement 5 modules consomment `RagService` MVP** (esg + applications + carbon + credit + action_plan) — signal PRD 6 tenu.

**AC7** — **Given** Phase 4, **When** évoquée, **Then** extension 8/8 modules (ajouter `financing_service`, `profiling` remplaçant `update_company_profile`, `documents_service` spec 004 déjà socle) documentée mais **non livrée MVP**.

**AC8** — **Given** les tests d'intégration, **When** `pytest backend/tests/test_rag_cross_module/` exécuté avec un fichier de test par module (`test_esg_rag.py`, `test_applications_rag.py`, `test_carbon_rag.py`, `test_credit_rag.py`, `test_action_plan_rag.py`), **Then** **chaque module** a un test vérifiant (a) `RagService` est appelé, (b) les citations sont présentes dans le résultat, (c) fallback gracieux si aucun document uploadé (pattern spec 009), (d) RLS isolation cross-user **And** coverage ≥ 80 % par module.

---
