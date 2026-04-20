---
title: "Dette audit 18-specs (PURE)"
epic_number: 9
status: in-progress
story_count: 15
stories_done: [9.1, 9.2, 9.3, 9.4, 9.5, 9.6]
stories_to_design: [9.7, 9.8, 9.9, 9.10, 9.11, 9.12, 9.13, 9.14, 9.15]
dependencies: []
blocks: [epic-10]
fr_covered: []
nfr_renforces: [NFR16, NFR38, NFR59, NFR60, NFR64]
qo_rattachees: []
notes: "Story 9.7 (observabilité with_retry + log_tool_call) est DÉPENDANCE BLOQUANTE d'Epic 10."
---

## Epic 9 — Stories détaillées

### Story 9.7 : Instrumentation `with_retry` + `log_tool_call` sur les 9 modules tools LangChain

**As a** Équipe Mefali (SRE/DX),
**I want** que les 9 modules tools métier LangChain (`profiling_tools`, `esg_tools`, `carbon_tools`, `financing_tools`, `credit_tools`, `application_tools`, `document_tools`, `action_plan_tools`, `chat_tools`) soient instrumentés via `with_retry()` + `log_tool_call()` déjà présents dans `backend/app/graph/tools/common.py`,
**So that** les échecs transients ne causent plus d'erreurs silencieuses côté user, les investigations d'incidents bénéficient d'un log structuré sur chaque appel d'outil, et que les nouveaux modules d'Epic 10 (`projects/`, `maturity/`, `admin_catalogue/`) naissent instrumentés — clôture P1 #14 audit.

**Metadata (CQ-8)**
- `fr_covered`: [] (renforce FR-021 retry + FR-022 journalisation déjà livrés côté infra)
- `nfr_covered`: [NFR38, NFR75]
- `phase`: 0
- `cluster`: dette-audit (cluster 2 observabilité)
- `estimate`: L (re-estimé 2026-04-19 depuis M suite review story file : T1+T2 extension primitive common.py + instrumentation 9 modules × 32 tools + 35 tests minimum + README + AC10 doc = 8-12h cohérent avec L Fibonacci)
- `qo_rattachees`: —
- `blocks`: **Epic 10 — DÉPENDANCE BLOQUANTE (CQ-11)**

**Acceptance Criteria**

**AC1** — **Given** les 9 modules `backend/app/graph/tools/`, **When** un audit de code est exécuté, **Then** 100 % des tools exposés sont wrappés via `with_retry()` + `log_tool_call()` (vs 2/11 actuels `interactive_tools` + `guided_tour_tools`).

**AC2** — **Given** un tool qui lève une erreur transient (TimeoutError, ConnectionError, 5xx, 429), **When** invoqué depuis un nœud LangGraph, **Then** `with_retry()` déclenche jusqu'à 3 retries exponential backoff (1 s, 3 s, 9 s) conformément NFR75, **And** chaque tentative est loggée avec `reason`.

**AC3** — **Given** un tool qui lève une erreur définitive (400, validation Pydantic, guards fail), **When** invoqué, **Then** aucun retry n'est déclenché (NFR75) **And** l'erreur est loggée une seule fois.

**AC4** — **Given** un appel réussi, **When** `log_tool_call()` s'exécute, **Then** une entrée est créée dans `tool_call_logs` avec (`tool_name`, `user_id`, `conversation_id`, `duration_ms`, `status=success`, `input_size_bytes`, `output_size_bytes`, `timestamp`).

**AC5** — **Given** 10 échecs consécutifs sur un même endpoint LLM, **When** détectés par `with_retry()`, **Then** le circuit breaker s'active pour 60 s **And** un event d'alerting est émis (NFR75 circuit breaker).

**AC6** — **Given** la suite de tests, **When** `pytest backend/tests/test_graph/test_tools_instrumentation.py` exécuté, **Then** les 9 modules sont couverts par ≥ 1 test vérifiant le wrapping **And** coverage ≥ 85 % (code critique NFR60).

**AC7** — **Given** cette story mergée, **When** l'Epic 10 démarre, **Then** les trois nouveaux modules `projects_tools.py`, `maturity_tools.py`, `admin_catalogue_tools.py` sont créés **instrumentés dès leur première ligne** (pas de rattrapage a posteriori).

---

### Story 9.8 : Suppression dead code `profiling_node` + `chains/extraction.py`

**As a** Équipe Mefali (DX),
**I want** supprimer définitivement `profiling_node` (~240 lignes `backend/app/graph/nodes.py:1192+`), `backend/app/chains/extraction.py` (~150 lignes), et les tests associés (`test_profiling_node.py`, `test_extraction_chain.py`, `test_chat_profiling.py`),
**So that** le codebase ne comporte plus de code non référencé depuis spec 012 (tool-calling LangGraph) et qu'aucun contributeur ne puisse réactiver accidentellement ces chemins obsolètes.

**Metadata (CQ-8)**
- `fr_covered`: —
- `nfr_covered`: [NFR59, NFR61, NFR64]
- `phase`: 0
- `cluster`: dette-audit (cluster 3)
- `estimate`: S

**Acceptance Criteria**

**AC1** — **Given** le code source, **When** `grep -r "profiling_node"` est exécuté sur `backend/` (hors changelog), **Then** zéro occurrence.

**AC2** — **Given** le code source, **When** `grep -r "chains.extraction\|from chains import extraction"` est exécuté, **Then** zéro occurrence.

**AC3** — **Given** les tests backend, **When** `pytest backend/tests/` exécuté, **Then** tous verts (baseline NFR59 zero failing tests maintenue).

**AC4** — **Given** la couverture backend, **When** mesurée post-refactor, **Then** régression ≤ 0,5 % par rapport à la baseline (compensation du retrait de code testé par la non-inclusion dans le dénominateur).

**AC5** — **Given** le graphe LangGraph runtime, **When** les nœuds sont construits, **Then** aucun nœud `profiling_node` enregistré (fonctionnalité déjà reprise par le tool `update_company_profile` depuis spec 012).

---

### Story 9.9 : 5 tests backend manquants module `financing` (spec 008)

**As a** Équipe Mefali (QA/DX),
**I want** les 5 fichiers `backend/tests/test_financing/` — `test_matching.py`, `test_models.py`, `test_router_funds.py`, `test_router_matches.py`, `test_service_pathway.py` —,
**So that** une régression sur le cœur du matching projet-financement soit détectée en CI avant déploiement, et non par un entrepreneur recevant des recommandations biaisées sans alerte.

**Metadata (CQ-8)**
- `fr_covered`: — (couvre l'existant spec 008 FR-001..FR-006)
- `nfr_covered`: [NFR59, NFR60 (≥ 85 % code critique matching)]
- `phase`: 0
- `cluster`: dette-audit (cluster 3)
- `estimate`: M

**Acceptance Criteria**

**AC1** — **Given** `test_matching.py` créé, **When** `pytest` exécuté, **Then** ≥ 15 tests couvrent : secteur match/partiel/no-match, taille compatible/incompatible, géographie couverte/hors zone, seuil ESG atteint/non-atteint, docs requis présents/manquants, voie directe vs intermédiée.

**AC2** — **Given** `test_models.py`, **When** exécuté, **Then** les modèles `Fund`, `Intermediary`, `FundIntermediaryLiaison`, `FundApplication` sont testés sur invariants (relations, contraintes, defaults, enums).

**AC3** — **Given** `test_router_funds.py` + `test_router_matches.py`, **When** exécutés, **Then** les endpoints `GET /api/financing/funds`, `GET /api/financing/matches/{project_id}`, `POST /api/financing/applications` sont couverts sur happy path + 401/403/404/422.

**AC4** — **Given** `test_service_pathway.py`, **When** exécuté, **Then** les 2 parcours (direct vs intermédiaire) sont testés avec ≥ 1 cas nominal + ≥ 1 cas dégradé (fonds fermé, intermédiaire obsolète).

**AC5** — **Given** la couverture de `backend/app/modules/financing/`, **When** mesurée, **Then** ≥ 85 % (code critique NFR60).

**AC6** — **Given** les tests ajoutés, **When** exécutés dans la CI, **Then** tous verts **And** baseline augmentée d'au moins 15 tests (NFR59).

---

### Story 9.10 : Queue asynchrone `BackgroundTask` FastAPI + micro-Outbox `domain_events` pour opérations longues (LLM + PDF)

**As a** PME User,
**I want** que la génération d'un rapport ESG PDF (~30 s), d'un plan d'action IA (~5–30 s) et d'un dossier application lourd n'occupe plus un worker uvicorn synchrone pendant toute sa durée,
**So that** la plateforme reste réactive même avec > 5 utilisateurs simultanés en génération et que je reçoive une notification dès que mon livrable est prêt, **en respectant la décision architecturale « pas de Redis MVP » + micro-Outbox `domain_events`** (architecture.md §Décision 11, CCC-14).

**Metadata (CQ-8)**
- `fr_covered`: — (infra support FR36, FR51, FR32)
- `nfr_covered`: [NFR4, NFR49, NFR50]
- `phase`: 0
- `cluster`: dette-audit (cluster 4 scalabilité)
- `estimate`: **XL** (migration 3 endpoints synchrones : `reports/service.py` PDF ESG, `action_plan/service.py` LLM plan, `applications/service.py` génération de dossier)
- `depends_on`: **[Story 10.10 micro-Outbox `domain_events` + worker batch 30 s]** (Epic 10 doit livrer la table + worker avant que 9.10 consomme le pattern)
- `architecture_alignment`: Décision 11 (pas de Celery+Redis MVP, pattern micro-Outbox) + CCC-14 (transaction boundaries)

**Acceptance Criteria**

**AC1** — **Given** `BackgroundTask` FastAPI + table `domain_events` livrée par Story 10.10, **When** un user déclenche la génération d'un PDF ESG, **Then** l'appel HTTP retourne en < 500 ms p95 avec un `job_id` (vs 30 s bloquants aujourd'hui) **And** une ligne `domain_event(event_type='report_generation_requested', payload=…, status='pending')` est insérée **dans la même transaction** que la création du `Report` (CCC-14 atomicité).

**AC2** — **Given** `BackgroundTask` attachée à la response, **When** FastAPI renvoie le 202, **Then** le rendu PDF s'exécute de manière **non bloquante** dans le même process uvicorn (pool `BackgroundTask`) **And** à la complétion, un event `report_generation_completed` est émis vers `domain_events` pour traitement par le worker batch 30 s (notification SSE).

**AC3** — **Given** 10 utilisateurs simultanés déclenchent chacun une génération lourde, **When** le pool uvicorn tourne (workers = 2 × CPU + 1), **Then** aucune cascade de pannes (zéro 503 sur endpoints non-génération) **And** p95 latence chat ≤ 2 s (NFR5) préservée **And** limite concurrente BackgroundTask documentée pour éviter saturation mémoire.

**AC4** — **Given** le worker batch `domain_events` tourne toutes les 30 s (Story 10.10), **When** il consomme un event `report_generation_completed`, **Then** un événement SSE `report_ready` est envoyé sur la conversation active du user avec `job_id` + URL signée **And** l'event est marqué `status='processed'` (idempotence : redelivery sans double notification).

**AC5** — **Given** un job échoue (LLM timeout, PDF render error), **When** constaté dans le `BackgroundTask`, **Then** un event `report_generation_failed` est inséré dans `domain_events` avec motif **And** le worker déclenche l'event SSE `report_failed` avec message user-friendly + suggestion remédiation **And** une entrée loggée dans `tool_call_logs`.

**AC6** — **Given** le mode synchrone legacy (pré-9.10) doit rester possible en DEV pour debug, **When** la variable d'env `USE_ASYNC_GENERATION=false`, **Then** les 3 endpoints se comportent en mode synchrone historique (graceful degradation).

**AC7** — **Given** la suite de tests, **When** `pytest backend/tests/test_reports/test_background_tasks.py` + `test_action_plan/test_background_tasks.py` + `test_applications/test_background_tasks.py` exécutés, **Then** scénarios (enqueue via BackgroundTask, domain_event insertion atomique, worker consume 30 s, SSE notification, échec, idempotence redelivery, graceful degradation) tous verts **And** coverage ≥ 85 % (code critique NFR60).

**AC8** — **Given** le changelog technique, **When** reviewé, **Then** il explicite que **Celery + Redis sont écartés MVP** (conformément Décision 11) et que la migration vers Celery reste documentée comme option Phase Growth si la charge dépasse les capacités BackgroundTask.

---

### Story 9.11 : `batch_save_emission_entries` pour le module carbon

**As a** PME User (owner) effectuant un bilan carbone,
**I want** que mes 7–15 entrées d'émission multi-véhicules/multi-postes soient sauvegardées via un seul tool call batch,
**So that** la génération du bilan ne subisse plus un timeout LLM silencieux après le 6ᵉ appel séquentiel (incident récurrent transport/logistique — même pattern que ESG spec 015).

**Metadata (CQ-8)**
- `fr_covered`: — (infra module carbon spec 007)
- `nfr_covered`: [NFR5, NFR75]
- `phase`: 0
- `cluster`: dette-audit (cluster 4 scalabilité)
- `estimate`: S

**Acceptance Criteria**

**AC1** — **Given** `backend/app/graph/tools/carbon_tools.py`, **When** un nouveau tool `batch_save_emission_entries(entries: List[EmissionEntrySchema])` est ajouté sur le modèle `batch_save_esg_criteria`, **Then** il accepte jusqu'à 20 entrées en une seule transaction SQLAlchemy atomique.

**AC2** — **Given** une PME transport déclare 12 véhicules, **When** le LLM invoque `batch_save_emission_entries`, **Then** les 12 entrées sont persistées en ≤ 1 appel tool **And** l'appel retourne en < 2 s p95 (vs timeout 60 s aujourd'hui).

**AC3** — **Given** une entrée invalide (facteur négatif, category hors enum), **When** le batch soumis, **Then** la transaction entière échoue (atomicité) **And** le message d'erreur identifie la/les ligne(s) fautive(s).

**AC4** — **Given** le prompt `backend/app/prompts/carbon.py`, **When** le LLM décide comment collecter, **Then** une instruction explicite privilégie `batch_save_emission_entries` sur `save_emission_entry` dès ≥ 3 entrées connues.

**AC5** — **Given** les tests, **When** `pytest backend/tests/test_carbon/test_batch_save.py` exécuté, **Then** scénarios (1 entrée, 10 entrées, 20 entrées, entrée invalide, rollback) couverts **And** coverage ≥ 85 % (NFR60).

---

### Story 9.12 : FR-019 notification chat PDF + `REPORT_TOOLS` LangChain

**As a** PME User,
**I want** recevoir une notification in-chat quand mon rapport ESG PDF est prêt,
**So that** je n'aie plus à rafraîchir manuellement `/reports` et que je télécharge le PDF directement depuis la conversation où je l'ai demandé (promesse spec 006 FR-019 jamais livrée).

**Metadata (CQ-8)**
- `fr_covered`: (implémente réellement FR-019 spec 006)
- `nfr_covered`: [NFR5, NFR37, NFR74]
- `phase`: 0
- `cluster`: dette-audit (cluster 5 promesses non tenues)
- `estimate`: M
- `depends_on`: Story 9.10 (queue async) + Story 9.7 (instrumentation)

**Acceptance Criteria**

**AC1** — **Given** `backend/app/graph/tools/report_tools.py` créé, **When** le module est chargé, **Then** il expose au minimum `generate_esg_report(project_id, referentials)` + `get_report_status(job_id)` wrappés `with_retry` + `log_tool_call` (story 9.7).

**AC2** — **Given** un user demande « génère-moi mon rapport ESG » par chat, **When** le LLM invoque `generate_esg_report`, **Then** un `job_id` est retourné en < 500 ms **And** un event SSE `report_requested` est émis.

**AC3** — **Given** le job termine en succès, **When** l'event terminal remonte, **Then** un message chat auto-généré apparaît : « Votre rapport ESG est prêt. [Télécharger le PDF] » avec lien signé **And** le lien fonctionne sans rafraîchissement manuel de `/reports`.

**AC4** — **Given** le job échoue, **When** l'event d'échec remonte, **Then** un message chat explique le motif user-friendly + suggestion remédiation **And** un log structuré est créé (NFR37).

**AC5** — **Given** le graphe LangGraph, **When** `generate_esg_report` est enregistré dans `chat_node`, **Then** la route est testée dans `backend/tests/test_graph/test_report_tools.py`.

**AC6** — **Given** cette story mergée, **When** la checklist audit est mise à jour, **Then** P1 #5 audit passe à ✅ RÉSOLU **And** la discordance speckit « `[X]` sans livrable » est documentée comme cas rétrospectif.

---

### Story 9.13 : FR-005 RAG documentaire dans le module `applications`

**As a** PME User qui a uploadé bilans, statuts juridiques et politiques internes,
**I want** que les sections générées de mon dossier de financement s'ancrent dans le contenu réel de mes documents via RAG pgvector,
**So that** mon livrable soit différencié d'un dossier générique et que les sections narratives citent effectivement mes éléments de preuve (promesse spec 009 FR-005 non tenue).

**Metadata (CQ-8)**
- `fr_covered`: (implémente promesse FR-005 spec 009, préfigure FR70/FR71 Epic 19)
- `nfr_covered`: [NFR2, NFR60]
- `phase`: 0
- `cluster`: dette-audit (cluster 5 promesses non tenues)
- `estimate`: M
- `consolide_avec`: P2 #6 (RAG sous-exploité transverse)
- `depends_on`: **[Epic 19 Story 19.1 socle RAG refactor cross-module, Story 10.13 Voyage migration]** — 9.13 consomme (a) l'abstraction RAG réutilisable d'Epic 19.1 et (b) l'`EmbeddingProvider` Voyage de Story 10.13, **sans recréer de 2ᵉ abstraction**. Sprint planning ordonnancera 10.13 → 19.1 → 9.13 pour éviter double migration. 9.13 reste dans Epic 9 pour traçabilité P1 #13 dette-audit.

**Acceptance Criteria**

**AC1** — **Given** `backend/app/modules/applications/service.py::generate_section`, **When** invoquée pour un projet avec ≥ 3 documents uploadés, **Then** elle appelle `search_similar_chunks(query, top_k=5, project_id=X)` **And** incorpore les chunks dans le prompt.

**AC2** — **Given** la section générée, **When** relue, **Then** ≥ 1 citation explicite (nom fichier + page/chunk) pointe vers un document du user quand la section porte sur un sujet documentable (sécurité, bilan, politique).

**AC3** — **Given** un projet sans document uploadé, **When** `generate_section` invoquée, **Then** le fallback actuel (profil + scores) est conservé sans régression **And** aucune citation fictive n'est générée.

**AC4** — **Given** le module applications, **When** audité, **Then** ≥ 3 appels à `search_similar_chunks` présents (un par type de section narrative : contexte, impact ESG, plan d'action).

**AC5** — **Given** les projets ayant ≥ 3 docs, **When** la métrique CI est mesurée, **Then** ratio de sections avec citation ≥ 60 %.

**AC6** — **Given** les tests, **When** `pytest backend/tests/test_applications/test_rag_integration.py` exécuté, **Then** scénarios (avec docs, sans docs, fallback, citation présente) tous verts.

---

### Story 9.14 : Complétion `SECTOR_WEIGHTS` pour les 11 secteurs

**As a** PME User dans un secteur dominant AO (agroalimentaire, commerce, artisanat, textile, construction),
**I want** que le scoring ESG pondère correctement selon mon secteur réel,
**So that** mon score ne soit pas dégradé par un fallback générique et que le bailleur voie une note contextualisée fidèle à ma filière.

**Metadata (CQ-8)**
- `fr_covered`: (renforce FR23 calcul ESG score + alignement marché PME AO)
- `nfr_covered`: [NFR60]
- `phase`: 0
- `cluster`: dette-audit (cluster 6 alignement marché)
- `estimate`: S
- `prep_epic13`: préfigure migration hard-code → table BDD (Epic 13 cluster B)
- `feeds_into`: [Epic 13] (Epic 13 prendra le relais en migrant `weights.py` vers une table BDD `sector_weight` + admin UI N2 ; la story 9.14 est le garde-fou intérimaire qui comble le trou marché sans attendre Epic 13)

**Acceptance Criteria**

**AC1** — **Given** `backend/app/modules/esg/weights.py`, **When** le fichier est modifié, **Then** les 11 secteurs du profil entreprise (énergie, agriculture, transport, industrie, services, textile, agroalimentaire, commerce, artisanat, construction, général) ont chacun un jeu E-S-G explicite (vs 5/11 aujourd'hui).

**AC2** — **Given** une PME agroalimentaire sénégalaise, **When** son scoring ESG est calculé, **Then** les pondérations utilisées sont spécifiques `agroalimentaire` (à définir avec conseiller ESG AO, valeurs par défaut documentées), **And** ne tombent pas sur `general`.

**AC3** — **Given** les jeux définis, **When** le code est lu, **Then** chaque jeu porte un commentaire justifiant le choix (source référentiel, étude de marché, ou note « préliminaire à affiner pilote Phase 0 »).

**AC4** — **Given** les tests, **When** `pytest backend/tests/test_esg/test_sector_weights.py` exécuté, **Then** les 11 secteurs sont testés sur `get_sector_weights(sector)` + le scoring E2E change selon le secteur.

**AC5** — **Given** cette story mergée, **When** le fichier est lu, **Then** un `TODO migration Epic 13` explicite indique que `weights.py` sera remplacé par une table BDD + admin UI N2.

---

### Story 9.15 : Migration des 7 composables frontend vers `apiFetch`

**As a** PME User dont la session JWT expire,
**I want** que l'intercepteur 401 redirige correctement vers `/login` depuis tous les modules (applications, crédit score, plan d'action, rapports, documents, profil entreprise, chat),
**So that** je ne subisse plus d'écran blanc ou d'erreur silencieuse quand mon token expire en cours de navigation.

**Metadata (CQ-8)**
- `fr_covered`: — (dette frontend infra)
- `nfr_covered`: [NFR13, NFR59]
- `phase`: 0
- `cluster`: dette-audit (cluster 7 dette frontend)
- `estimate`: M

**Acceptance Criteria**

**AC1** — **Given** les 7 composables `useApplications`, `useCreditScore`, `useActionPlan`, `useReports`, `useDocuments`, `useCompanyProfile`, `useChat`, **When** ils sont audités, **Then** tous utilisent `apiFetch` (wrapper centralisé Nuxt) **And** aucun n'utilise `$fetch` / `fetch` / `axios` brut.

**AC2** — **Given** un JWT expiré, **When** un user invoque n'importe quel composable migré, **Then** l'intercepteur 401 d'`apiFetch` déclenche redirection `/login?redirect=<currentPath>` en < 500 ms.

**AC3** — **Given** un refresh token encore valide, **When** une 401 survient, **Then** `apiFetch` tente un refresh silencieux (1 tentative max, NFR13) avant redirection — comportement centralisé à valider non-régression.

**AC4** — **Given** la couverture frontend, **When** `npm test` exécuté, **Then** les tests unitaires des 7 composables passent **And** un test E2E Playwright vérifie « JWT expiré → redirect → re-login → retour sur page » sur ≥ 3 des 7 modules.

**AC5** — **Given** le diff git, **When** reviewé, **Then** suppression totale des anciens appels `$fetch`/`fetch` (pas de co-existence laissée en dette).

**AC6** — **Given** cette story mergée, **When** `index.md` §P1 est mis à jour, **Then** P1 #1 passe à ✅ RÉSOLU **And** l'Epic 9 progresse vers clôture.

---

