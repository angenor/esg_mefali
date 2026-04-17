# Index des Audits Rétrospectifs Spec-par-Spec

**Objectif** : auditer a posteriori les 18 specs speckit du projet esg_mefali pour capturer les dettes, leçons et actions résiduelles.
**Méthode** : rétrospective post-hoc (workflow BMAD adapté — pas de sprint-status, specs speckit ≠ epics BMAD).
**Démarré** : 2026-04-16

---

## Statut global

| # | Spec | Titre | Statut audit | Date | Dettes P1 | Dettes P2 |
|---|------|-------|--------------|------|-----------|-----------|
| 001 | [001-technical-foundation](./spec-001-audit.md) | Foundation Technique | ✅ Audité | 2026-04-16 | 1 | 2 |
| 002 | [002-chat-rich-visuals](./spec-002-audit.md) | Chat Rich Visuals | ✅ Audité | 2026-04-16 | 1 | 1 |
| 003 | [003-company-profiling-memory](./spec-003-audit.md) | Company Profiling Memory | ✅ Audité | 2026-04-16 | 2 | 1 |
| 004 | [004-document-upload-analysis](./spec-004-audit.md) | Document Upload & Analysis | ✅ Audité | 2026-04-16 | 2 | 2 |
| 005 | [005-esg-scoring-assessment](./spec-005-audit.md) | ESG Scoring Assessment | ✅ Audité | 2026-04-16 | 1 | 2 |
| 006 | [006-esg-pdf-reports](./spec-006-audit.md) | ESG PDF Reports | ✅ Audité | 2026-04-16 | 3 | 2 |
| 007 | [007-carbon-footprint-calculator](./spec-007-audit.md) | Carbon Footprint Calculator | ✅ Audité | 2026-04-16 | 1 | 1 |
| 008 | [008-green-financing-matching](./spec-008-audit.md) | Green Financing Matching | 🔴 Rework | 2026-04-16 | 1 | 3 |
| 009 | [009-fund-application-generator](./spec-009-audit.md) | Fund Application Generator | ⚠️ Dettes lourdes | 2026-04-16 | 1 | 2 |
| 010 | [010-green-credit-scoring](./spec-010-audit.md) | Green Credit Scoring | ✅ Audité | 2026-04-16 | 0 | 2 |
| 011 | [011-dashboard-action-plan](./spec-011-audit.md) | Dashboard & Action Plan | ✅ Audité | 2026-04-16 | 0 | 3 |
| 012 | [012-langgraph-tool-calling](./spec-012-audit.md) | LangGraph Tool Calling | ⚠️ Dettes lourdes | 2026-04-16 | 1 | 2 |
| 013 | [013-fix-multiturn-routing-timeline](./spec-013-audit.md) | Fix Multi-turn Routing | ✅ Audité | 2026-04-16 | 0 | 1 |
| 014 | [014-concise-chat-style](./spec-014-audit.md) | Concise Chat Style | ✅ Audité | 2026-04-16 | 0 | 0 |
| 015 | [015-fix-toolcall-esg-timeout](./spec-015-audit.md) | Fix Tool-call ESG Timeout | ✅ Audité | 2026-04-16 | 0 | 0 |
| 016 | [016-fix-tool-persistence-bugs](./spec-016-audit.md) | Fix Tool Persistence Bugs | ✅ Audité | 2026-04-16 | 0 | 1 |
| 017 | [017-fix-failing-tests](./spec-017-audit.md) | Fix Failing Tests | ✅ Audité | 2026-04-16 | 0 | 1 |
| 018 | [018-interactive-chat-widgets](./spec-018-audit.md) | Interactive Chat Widgets | ✅ Audité | 2026-04-17 | 0 | 3 |

**Progression** : **18 / 18 (100 %)** 🎯 **CYCLE D'AUDIT COMPLET**

**Cumul dettes final (audit 2026-04-16)** : 14 P1 · 28 P2 · 56 P3

**Stories résolues depuis l'audit** (2026-04-17) :
- ✅ P1 #2 — Rate limiting chat (story `9-1-rate-limiting-fr013-chat-endpoint`)
- ✅ P1 #4 — Quota stockage utilisateur (story `9-2-quota-cumule-stockage-par-utilisateur`)

**P1 restants** : 12 / 14 (2 résolus, 12 à ouvrir)

---

## Légende statut

- ⏳ **Pending** — à auditer
- 🔄 **In progress** — audit en cours
- ✅ **Audité** — document livré, actions extraites, pas de rework majeur
- ⚠️ **Dettes lourdes** — audit livré, mais ≥3 dettes P1/P2 cumulées, refactoring à prévoir
- 🔴 **Rework nécessaire** — implémentation partielle, story BMAD obligatoire avant de s'appuyer dessus
- ❓ **À approfondir** — audit incomplet, besoin d'info supplémentaire

---

## Actions consolidées tous audits confondus

### Priorité P1 (à ouvrir en story BMAD)

1. **Migration 7 composables → `apiFetch`** (source : 001)
   - Composables : `useApplications`, `useCreditScore`, `useActionPlan`, `useReports`, `useDocuments`, `useCompanyProfile`, `useChat`
   - Impact : intercepteur 401 cassé → sessions expirées mal gérées

2. ~~**Implémenter FR-013 rate limiting chat** (30 msg/min)~~ → ✅ **RÉSOLU 2026-04-17** — story BMAD `9-1-rate-limiting-fr013-chat-endpoint` statut `done`
   - Fix livré : SlowAPI `slowapi>=0.1.9` + `@limiter.limit("30/minute")` sur les 2 endpoints messages + `key_func` par `user_id` (fail-fast `RuntimeError` si endpoint décoré sans `Depends(get_current_user)` — Option 3 de la décision D1 du code review)
   - Première story BMAD issue de l'audit 18-specs → **workflow éprouvé**, feu vert pour enchaîner les autres P1 du cluster 1

3. **Supprimer dead code `profiling_node` + `chains/extraction.py`** (source : 003)
   - Fichiers : `backend/app/graph/nodes.py:1192+` (`profiling_node` 240+ lignes), `backend/app/chains/extraction.py` (~150 lignes), tests associés (`test_profiling_node.py`, `test_extraction_chain.py`, `test_chat_profiling.py`)
   - Impact : ~300 lignes de code non référencées depuis spec 012 — confusion, risque de réactivation par erreur

4. ~~**Quota cumulé de stockage par utilisateur**~~ → ✅ **RÉSOLU 2026-04-17** — story BMAD `9-2-quota-cumule-stockage-par-utilisateur` statut `done`
   - Fix livré : `QUOTA_BYTES_PER_USER_MB` + `QUOTA_DOCS_PER_USER` (env-configurable, `ge=1`), `check_user_storage_quota()` dans service, vérification pré-création + pré-check batch, endpoint `GET /api/documents/quota`, SlowAPI 60/min sur upload, path converter `{document_id:uuid}` ×4 (durcissement review)
   - 15 tests quota + 41/41 module documents verts
   - 4 dettes résiduelles documentées dans `deferred-work.md` (TOCTOU race, orphelins batch, trust file_size, statuses)
   - 2ᵉ story BMAD issue de l'audit — **workflow encore plus propre** (patches appliqués en batch à la review, aucun action item résiduel)

5. **Implémenter réellement FR-019 (notification chat PDF)** + `REPORT_TOOLS` LangChain (source : 006)
   - Fichiers : `backend/app/graph/tools/report_tools.py` (à créer), `backend/app/graph/graph.py`, `backend/app/api/chat.py`
   - Impact : **fonctionnalité marquée `[X]` mais non implémentée** — 2ème cas de discordance speckit (1er : T038 spec 002)
   - L'utilisateur doit rafraîchir `/reports` pour savoir si son PDF est prêt

6. **Queue asynchrone pour opérations longues LLM + PDF** (Celery/RQ/BackgroundTask) — **élargi à spec 011 le 2026-04-16**
   - Fichiers : `backend/app/modules/reports/service.py` (génération PDF ESG ~30s), `backend/app/modules/action_plan/service.py` (`generate_action_plan` via Claude 5-30s)
   - Impact : opérations longues (PDF + LLM) bloquent les workers uvicorn → pannes cascade à > 5 utilisateurs simultanés
   - Pattern identique, même fix structurel — une seule story transverse « queue async pour opérations longues » couvre les 2 modules.
   - À étendre si d'autres modules génèrent du LLM synchrone (ex. dossiers spec 009 à vérifier).

7. **Flag `manually_edited_fields: JSONB` — édition manuelle prévaut** (source : 003) — **reclassé P2→P1 le 2026-04-16**
   - Fichier : `backend/app/models/company.py`
   - Impact : **perte de données utilisateur silencieuse**. Une extraction LLM peut écraser sans trace une correction manuelle faite via `/profile`. Règle documentée dans spec 003 mais jamais implémentée.
   - Justification P1 : confiance utilisateur (invisible côté UX, catastrophique quand ça arrive)
   - Audit additionnel requis : chercher en BDD les divergences entre `profile_update` SSE events et l'état actuel du profil — possibles écrasements passés à inventorier

8. **OCR bilingue FR+EN — tesseract `lang='fra+eng'`** (source : 004) — **reclassé P2→P1 le 2026-04-16**
   - Fichier : appel `pytesseract.image_to_string(..., lang='fra')` dans `backend/app/modules/documents/service.py`
   - Impact : **impact métier direct**. Les bailleurs climatiques internationaux (GCF, FEM, BAD) publient majoritairement en anglais. OCR dégradé → analyse ESG fausse → matching financement biaisé → score crédit vert erroné. Un user qui teste avec un doc GCF anglais conclut « ça ne marche pas ».
   - Justification P1 : le cœur de la value proposition (« accès aux fonds verts ») dépend de documents souvent anglophones

9. **Compléter SECTOR_WEIGHTS pour les 11 secteurs** (source : 005) — **reclassé P2→P1 le 2026-04-16**
   - Fichier : `backend/app/modules/esg/weights.py:12`
   - Impact : **5 secteurs sur 11 (textile, agroalimentaire, commerce, artisanat, construction) retombent sur `general`** alors qu'ils sont dans le profil. L'agroalimentaire, le commerce et l'artisanat sont **les secteurs dominants** des PME africaines francophones UEMOA/CEDEAO (>60% des PME en agro selon BCEAO). Scoring ESG dégradé pour ~50 % du marché cible.
   - Justification P1 : alignement métier avec le public cible — une PME agroalimentaire sénégalaise reçoit un score non contextualisé, le bailleur voit une note biaisée, la recommandation financement est approximative.

10. **Guards sur tous les contenus LLM persistés** (résumé exécutif spec 006 + fiche de préparation spec 008 + plan d'action JSON spec 011) — **reclassé P2→P1 le 2026-04-16, élargi progressivement**
    - Fichiers : `backend/app/modules/reports/service.py` (`generate_executive_summary`), `backend/app/modules/financing/service.py` (fiche de préparation + template), `backend/app/modules/action_plan/service.py` (`generate_action_plan` — génère 10+ actions JSON via Claude)
    - Impact : **hallucinations possibles dans tous les contenus LLM persistés par Mefali** : documents PDF (ESG + financement) ET données structurées (plan d'action en BDD, affiché en timeline, exporté).
    - Risques : compliance, crédibilité, juridique — même gravité que le rate limiting (invisible tant que ça n'arrive pas, catastrophique quand ça arrive).
    - Guards requis par type de contenu :
      - **Texte libre PDF** (résumé exécutif, fiche préparation) : longueur, langue, cohérence numérique avec données source, vocabulaire interdit
      - **JSON structuré** (plan d'action) : schéma Pydantic strict, bornes sur les montants, dates dans le futur raisonnable, `category` dans l'enum autorisé, nombre d'actions dans `[5, 20]`
    - Tests associés doivent vérifier le **contenu produit**, pas juste "200 OK".
    - Risques compliance (bailleur vérifie, rejette), crédibilité (« Mefali produit des chiffres faux »), juridique (dans un contexte de financement contractuel, un document erroné engage la responsabilité).
    - Guards requis (minimum viable) : longueur, langue détectée, cohérence numérique avec les données source, vocabulaire interdit (« garanti », « certifié », « validé par »)
    - Justification P1 : compliance/trust/juridique — même classe que le rate limiting (invisible tant que ça n'arrive pas, catastrophique quand ça arrive)

11. **Créer les 5 tests backend manquants spec 008 Financing** (source : audit forensique 2026-04-16)
    - Fichiers à créer : `backend/tests/test_financing/test_matching.py`, `test_models.py`, `test_router_funds.py`, `test_router_matches.py`, `test_service_pathway.py`
    - Impact : **silence total sur le cœur de la value proposition** (matching projet-financement). Une régression sur la logique de matching = un entrepreneur reçoit de mauvaises recommandations de fonds, sans aucune alerte CI. Le matching étant un algorithme composite (secteur, taille, géographie, ESG, documents), les bugs y sont faciles à introduire.
    - Justification P1 : la qualité des recommandations Mefali dépend de ce module ; livrer sans test = parier.
    - Pré-requis : revisiter `spec-008-audit.md` pour valider que les tests prévus couvrent toutes les branches critiques (direct vs intermédiaire, scoring, filtrages).

12. **`batch_save_emission_entries` pour le module carbon** (source : 007) — **reclassé P2→P1 le 2026-04-16**
    - Fichier : `backend/app/graph/tools/carbon_tools.py` (nouveau tool à créer sur le modèle de `batch_save_esg_criteria`)
    - Impact : **timeout LLM imminent sur bilans multi-véhicules**. Un bilan typique = 7-15 appels séquentiels à `save_emission_entry`. Avec `request_timeout=60` (fix spec 015) et 2-5 s/appel LLM, un bilan d'une PME transport/logistique déborde → timeout silencieux. Le même pattern a déjà cassé en prod pour ESG (spec 005), fix en spec 015 — non étendu à carbon.
    - Justification P1 : dette latente mais bug imminent. Mêmes symptômes, même gravité que ESG/spec 015.
    - **Consolidation recommandée** : story transverse `pattern batch_* multi-entrées` qui couvre simultanément carbon + potentiellement credit (spec 010) + application (spec 009) — à valider dans les audits suivants.

13. **Implémenter FR-005 RAG documentaire applications** (source : 009)
    - Fichier : `backend/app/modules/applications/service.py` (fonction `generate_section`)
    - Impact : **promesse non tenue**. Spec 009 prescrit explicitement "via RAG (pgvector)" mais aucune utilisation de `search_similar_chunks` dans le module. Les sections générées sont basées UNIQUEMENT sur le profil entreprise + scores ESG/carbone, **jamais sur le contenu des documents uploadés**. Un utilisateur qui uploade ses bilans, statuts juridiques ou politiques internes n'en voit pas la trace dans le dossier généré.
    - Justification P1 : c'est précisément ce qui différencierait un dossier "personnalisé Mefali" d'un dossier générique.
    - **Consolidation avec action P2 #6** (RAG sous-exploité) — cette exploitation fait partie du cluster "RAG dans 7 modules restants".

14. **Appliquer `with_retry` + `log_tool_call` aux 9 modules tools** (source : 012) — **absorbe P2 #2**
    - Fichiers : `backend/app/graph/tools/` (profiling_tools, esg_tools, carbon_tools, financing_tools, credit_tools, application_tools, document_tools, action_plan_tools, chat_tools)
    - Impact : **FR-021 (retry) + FR-022 (journalisation) non câblés** sur 9/11 modules. L'infrastructure `with_retry()` + `log_tool_call()` existe dans `common.py` mais n'est consommée que par `interactive_tools` + `guided_tour_tools`. Conséquences observées : investigations bugs 2026-04-15 (feature 019) **ralenties par absence de logs** sur les tools métier ; échecs BDD transients non retryés silencieusement → user voit l'erreur.
    - Justification P1 : 5ème cas systémique de discordance speckit, observabilité critique en prod, PR de 50-100 lignes seulement.
    - Consolidation : cette action **fusionne** P2 #2 ("Instrumenter `log_tool_call`") en le transformant en P1 + ajoute le retry FR-021.

### Priorité P2 (à ouvrir en story BMAD)

1. **Reducer `current_page` dans `ConversationState`** (source : 001)
   - Fichier : `backend/app/graph/state.py:36`
   - Impact : latent, piège à retardement si un nœud retourne un state partiel

2. ~~**Instrumenter `log_tool_call` dans les tools métier**~~ → **reclassé P1 #14** (source : 012 — absorbe la dette avec le retry FR-021)

3. **Timeout frontend sur `isStreaming` + bouton "Annuler"** (source : 002)
   - Fichier : `frontend/app/composables/useChat.ts`
   - Impact : si le streaming coince, l'utilisateur ne peut plus rien envoyer. Timeout 60s backend (spec 015) traite le symptôme côté serveur mais pas le blocage UX.

4. **Retry + log warn dans `_summarize_previous_conversation`** (source : 003)
   - Fichier : `backend/app/api/chat.py:373`
   - Impact : un échec réseau laisse la conversation définitivement sans résumé, jamais rattrapé

5. ~~**Flag `manually_edited_fields: JSONB` sur `CompanyProfile`**~~ → **reclassé P1** (voir section P1 §7)

6. ~~**Exploiter RAG documentaire dans carbon/credit/application**~~ → **Consolidé avec P1 #13** (RAG transversal)
   - La promesse FR-005 non tenue de spec 009 (applications) force la priorité à P1
   - Couvrir en même temps : applications (P1, promesse spec 009), carbon (spec 007 observation), credit (spec 010 à auditer), action_plan (spec 011 à auditer)
   - **Une seule story transverse** au lieu de 4 fragmentées → évite duplication du pattern pgvector

7. **Détection malware pour documents uploadés** (source : 004)
   - Fichier : `backend/app/modules/documents/service.py`
   - Impact : faille sécurité — PDF/DOCX avec macros malveillantes acceptés sans scan
   - Solution : intégration clamav ou équivalent

8. ~~**OCR bilingue FR+EN**~~ → **reclassé P1** (voir section P1 §8)

9. **Migrer SECTOR_BENCHMARKS vers une table BDD** (source : 005)
   - Fichier : `backend/app/modules/esg/weights.py:76` (hard-codé)
   - Impact : impossible d'affiner les moyennes avec les données réelles utilisateurs, chaque update = déploiement

10. ~~**Compléter SECTOR_WEIGHTS pour les 11 secteurs**~~ → **reclassé P1** (voir section P1 §9)

11. **Mécanisme de détection d'incohérence dans les réponses ESG** (source : 005)
    - Fichier : `backend/app/graph/nodes.py` (esg_scoring_node)
    - Impact : edge case documenté dans la spec non implémenté → scores biaisés si utilisateur répond "zéro émission" en transport diesel

12. **Signature/watermark PDF** (PyPDF2 + QR vérification) (source : 006)
    - Fichier : `backend/app/modules/reports/service.py`
    - Impact : rapports remis aux investisseurs altérables sans traçabilité d'authenticité

13. **Quota + purge rapports** (10/éval max, purge > 90j) (source : 006)
    - Fichier : `backend/app/modules/reports/service.py`
    - Impact : accumulation indéfinie des PDFs dans `uploads/reports/`

14. ~~**Guards sur résumé exécutif IA**~~ → **reclassé P1** (voir section P1 §10)

15. **Créer test frontend `credit-score.test.ts` spec 010** (source : audit forensique 2026-04-16)
    - Fichier à créer : `frontend/tests/credit-score.test.ts`
    - Impact : page `/credit-score` + store `creditScore.ts` sans couverture frontend. Cosmétiquement déclaré `[X]` dans tasks.md mais jamais livré.
    - Justification P2 : moins critique que les 5 tests backend spec 008 (qui testent la logique métier). Ici on teste le rendu/store, qui est plus simple à valider manuellement.

16. **Étendre `batch_save_*` pattern au module carbon** (source : 007)
    - Fichier : `backend/app/graph/tools/carbon_tools.py` (ajouter `batch_save_emission_entries`)
    - Impact : 5-15 appels séquentiels `save_emission_entry` par bilan = risque de timeout LLM identique à spec 005 (corrigé par spec 015 pour ESG uniquement)
    - Même dette latente que spec 005 §3.1 — généraliser aux modules carbon/credit/application

17. **Bornes supérieures par catégorie dans schemas Pydantic carbon** (source : 007)
    - Fichier : `backend/app/modules/carbon/schemas.py`
    - Impact : FR-015 "valeurs anormalement élevées" non implémenté — une saisie de 10M kWh/an passe sans alerte, acceptance scenario 4 de US1 non couvert

18. **Versioning coordonnées intermédiaires financing** (source : 008)
    - Fichier : `backend/app/models/financing.py` (ajout `last_verified_at`, `verified_by`, `deprecated` sur `Fund` + `Intermediary`)
    - Impact : coordonnées tierces (tel, email) qui vieillissent sans traçabilité → perte de crédibilité produit

19. **Interface admin CRUD fonds + intermédiaires** (source : 008)
    - Fichiers : nouvelle route `/admin/financing/*` + frontend
    - Impact : mise à jour des 12 fonds + 14 intermédiaires nécessite actuellement modification du seed.py + re-run du seed + déploiement

20. **Tests de contenu PDF** (parse + assertions sur sections) (source : 008)
    - Fichiers : `backend/tests/test_financing_preparation.py`, `backend/tests/test_report_*.py`
    - Impact : tests actuels valident "200 OK" mais pas le contenu (sections, valeurs) → hallucinations LLM invisibles

21. **Finaliser Phase 12 Polish spec 009** (source : 009)
    - Tâches : T058-T062 (dark mode formellement validé, états vides, couverture 80%, quickstart, CLAUDE.md)
    - Impact : spec 009 marquée "done" mais Phase Polish `[ ]` — qualité non auditée formellement
    - Note : dark mode détecté dans le code (26+82 occurrences `dark:`) mais validation formelle manquante

22. **Historique de versions pour `ApplicationSection`** (source : 009)
    - Fichier : `backend/app/modules/applications/service.py` + modèle
    - Impact : régénération d'une section écrase définitivement le contenu précédent — pas de rollback possible, UX dégradée pour les utilisateurs qui itèrent

23. **Versionner `FACTOR_WEIGHTS` credit scoring** (source : 010)
    - Fichier : `backend/app/modules/credit/service.py:23` + ajouter `CreditScore.weights_version: str`
    - Impact : scores historiques comparés sur des pondérations potentiellement différentes → SC-006 "évolution sur 3 versions" trompeur si règles changent

24. **Paralléliser queries `get_dashboard_summary`** (source : 011)
    - Fichier : `backend/app/modules/dashboard/service.py:465` (`asyncio.gather` sur les 5 agrégations ESG/carbon/credit/financing/applications)
    - Impact : queries sérialisées aujourd'hui → latence cumulée risque de casser SC-001 "< 3s" à grande échelle

25. **Refactorer `dashboard/service` pour consommer les services des modules** (source : 011)
    - Fichier : `backend/app/modules/dashboard/service.py` (487 lignes → pattern "God service")
    - Impact : duplication des règles métier + couplage aux tables des autres modules → migration de schéma casse silencieusement le dashboard

26. **Health check startup `bind_tools() == ToolNode.tools`** (source : 012)
    - Fichier : `backend/app/graph/graph.py` (au démarrage, vérifier la cohérence bind/ToolNode pour chaque noeud)
    - Impact : bug feature 019 a pu se produire car `GUIDED_TOUR_TOOLS` bindé sans être dans le ToolNode → LLM hallucine tool indisponible
    - **Directement actionnable** : un test pytest similaire à `test_guided_tour_toolnode_registration.py` (déjà créé 2026-04-15) mais généralisé à TOUS les tools (pas seulement `trigger_guided_tour`). ~20 lignes de code, effort minime, prévient la récidive.
    - Ou version runtime : assertion au `build_graph()` qui lève si incohérence → fail-fast au démarrage uvicorn.

27. **Enforcement applicatif des confirmations finalize** (source : 012)
    - Fichiers : `backend/app/graph/tools/esg_tools.py` + `carbon_tools.py` (finalize_* tools)
    - Impact : FR-019 confirmation actuellement via prompt seulement → si LLM ignore la consigne (prompt injection), finalisation directe possible

28. **Exposer `active_module` dans SSE events + breadcrumb frontend** (source : 013)
    - Fichiers : `backend/app/api/chat.py` (stream_graph_events) + `frontend/app/composables/useChat.ts`
    - Impact : user navigue à l'aveugle dans une conversation multi-module — ne sait pas si ses réponses partent vers ESG, carbone ou chat général

29. **Politique CI "zero failing tests on main"** (source : 017)
    - Fichier : `.github/workflows/` + règles de protection de branche
    - Impact : 34 tests en échec s'étaient accumulés sur plusieurs semaines → tolérance à la dette normalisée. Enforcer "zero failure" empêche la récidive.

30. **Implémenter régénération de widget à la reprise de module `in_progress`** (Clarification Q4 partielle) (source : 018)
    - Fichier : `backend/app/graph/nodes.py` (esg_scoring_node, carbon_node, ...)
    - Impact : Q4 documentée prescrit "expiration + régénération" ; expiration OK, régénération non active → user qui reprend voit un widget expiré grisé sans nouveau widget automatique

### Priorité P3 (nice-to-have)

1. **Refactorer `MessageParser` vers un registre extensible de blocs** (source : 002)
   - Fichier : `frontend/app/components/chat/MessageParser.vue` + `useMessageParser.ts`
   - Impact : les 6 types sont hardcodés ; spec 018 a dû contourner via un second système (interactive_questions)
   - Seulement si une nouvelle feature prévoit un 7ᵉ type de bloc

2. **Vérifier/découper `chat.spec.ts`** (source : 002)
   - Fichier attendu absent : `frontend/tests/e2e/chat.spec.ts`
   - Impact : T038 de spec 002 n'a pas de trace ; soit jamais livré, soit supprimé sans trace

3. **Unifier `ProfileNotification.vue` avec toast global** (source : 003)
   - Fichier : `frontend/app/components/chat/ProfileNotification.vue`
   - Impact : deux systèmes de notification parallèles dans l'app

4. **SSE unifié page `/documents`** (source : 004)
   - Fichier : `frontend/app/composables/useDocuments.ts`
   - Impact : page `/documents` nécessite refresh manuel vs chat temps réel

5. **Remplacer iframe PDF par pdf.js/vue-pdf-embed** (source : 004)
   - Fichier : `frontend/app/components/documents/DocumentPreview.vue`
   - Impact : expérience preview incohérente entre navigateurs

6. **Observabilité : métriques de précision détection type de document** (source : 004)
   - Fichier : `backend/app/chains/analysis.py` + logging
   - Impact : SC-003 cible "85% de précision" mais pas mesuré en prod

7. **Persister citations documentaires ESG en champ structuré** (source : 005)
   - Fichier : `backend/app/models/esg.py` (ajout `document_citations: JSONB`)
   - Impact : citations générées par LLM dans le chat mais perdues hors session

8. **Analyse comparative entre évaluations ESG successives** (source : 005)
   - Fichier : `frontend/app/pages/esg/results.vue` + service diff
   - Impact : historique = courbe brute sans insight sur ce qui a changé

9. **Instrumenter la qualité des recommandations ESG** (source : 005)
   - Impact : SC-007 cible "80% actionnables" mais pas mesuré → pas de feedback loop

10. **Versionner référentiels UEMOA/BCEAO en BDD** + champ `regulation_version` sur `Report` (source : 006)
    - Fichier : `backend/app/modules/reports/templates/esg_report.html` (actuellement hard-codé)
    - Impact : si BCEAO met à jour une taxonomie, redéploiement backend obligatoire

11. **Déclarer `UniqueConstraint` ORM carbon** (en plus de l'index BDD) (source : 007)
    - Fichier : `backend/app/models/carbon.py` (`__table_args__`)
    - Impact : en cas de race condition, on reçoit `IntegrityError` brut au lieu d'un message applicatif clair

12. **Documenter sources facteurs d'émission** (source : 007)
    - Fichier : `backend/app/modules/carbon/emission_factors.py`
    - Impact : 0.41 kgCO2e/kWh (CI) sans référence — impossible de valider SC-003 "calculs corrects à 1% près"

13. **Page édition manuelle `/carbon/assessments/{id}/edit`** (source : 007)
    - Fichier : `frontend/app/pages/carbon/[id]/edit.vue` (à créer)
    - Impact : une entrée mal extraite par le LLM ne peut être corrigée qu'en recommençant la conversation — pattern à uniformiser avec spec 003 page profil

14. **Calcul géographique réel financing (haversine ou zone)** (source : 008)
    - Fichier : `backend/app/modules/financing/service.py:563` (`recommend_intermediaries`)
    - Impact : tri actuel par string match sur ville → un user à Bouaké ne voit pas que les intermédiaires d'Abidjan couvrent la CI entière

15. **Edge case "aucun match < 20%" financing** (source : 008)
    - Fichier : `backend/app/modules/financing/service.py`
    - Impact : edge case documenté dans spec non implémenté → user sans match ne reçoit pas de suggestions d'amélioration

16. **Snapshot profil dans `FundMatch` + re-calcul automatique** (source : 008)
    - Fichier : `backend/app/models/financing.py`
    - Impact : matches stockés avec scores obsolètes quand le profil évolue (nouveau secteur, nouveau score ESG)

17. **Documenter exclusion GUIDED_TOUR_TOOLS pour application_node** (source : 009)
    - Fichiers : spec 009 + spec 019 (feature guided tour)
    - Impact : décision cross-spec non tracée — applications est volontairement exclu du parcours guidé mais aucune justification documentée

18. **Preview PDF inline avant export applications** (source : 009)
    - Fichier : `frontend/app/pages/applications/[id].vue`
    - Impact : l'utilisateur découvre un PDF mal formaté après download — ajouter preview ajoute confiance pour un document institutionnel

19. **Paramètres simulation financière en BDD versionnés** (source : 009)
    - Fichier : `backend/app/modules/applications/simulation.py` + nouvelle table `financial_parameters`
    - Impact : taux bancaires, frais intermédiaires, durées de traitement hard-codés → update = déploiement. Pas de différenciation par intermédiaire (SIB vs SGBCI supposées identiques)

20. **Snapshot des données source dans `CreditScore`** (source : 010)
    - Fichier : `backend/app/models/credit.py` (ajout `source_snapshot: JSONB`)
    - Impact : si profil évolue, scores historiques inexploitables pour comparaison temporelle

21. **Machine à états cycle de vie CreditScore** (active/expired/superseded) (source : 010)
    - Fichier : `backend/app/modules/credit/service.py`
    - Impact : ambiguïté sur le comportement d'un score expiré lu via le tool

22. **Vérification anti-gaming sur les statuts submitted** (source : 010)
    - Fichier : `backend/app/modules/applications/service.py` (lors de transition ready → submitted)
    - Impact : score auto-déclaratif sans validation → user peut gonfler son score engagement en marquant "soumis" sans action réelle

23. **Documenter cible du bonus `accepted`** (source : 010)
    - Fichier : `backend/app/modules/credit/service.py:38` + spec 010
    - Impact : ambiguïté sur la composante cible (engagement vs impact vert)

24. **Rappel auto-généré à J-7 avant échéance d'une `ActionItem`** (source : 011)
    - Fichier : `backend/app/modules/action_plan/service.py` (trigger lors de création/update action avec due_date)
    - Impact : rappels actuellement créés manuellement par l'user → échéances ratées

25. **Analyse comparative entre versions de plans** (source : 011)
    - Fichier : `frontend/app/pages/action-plan/index.vue` + nouveau service diff
    - Impact : historique sans insight sur ce qui a changé — même dette que spec 005 §3.5

26. **Badges data-driven** (`BadgeDefinition` JSONB) (source : 011)
    - Fichier : `backend/app/modules/action_plan/badges.py` + table `badge_definitions`
    - Impact : ajouter un 6ᵉ badge = PR code + déploiement

27. **Optimiser `check_and_award_badges`** (conditionné par type de changement) (source : 011)
    - Fichier : `backend/app/modules/action_plan/service.py:update_action_item`
    - Impact : vérification inutile des 5 conditions à chaque update (même si statut inchangé)

28. **Migration polling → SSE/WebSocket pour rappels** (source : 011)
    - Fichier : `frontend/app/composables/useActionPlan.ts:253`
    - Impact : polling 60s × N users = scaling linéaire — acceptable V1, coûteux > 100 users

29. **Logger `prompt_version` + `model_version` dans `ToolCallLog`** (source : 012)
    - Fichier : `backend/app/models/tool_call_log.py` + `backend/app/graph/tools/common.py`
    - Impact : sans cette trace, les investigations "pourquoi ce tool a été appelé" restent dans le noir quand les prompts évoluent (specs 013/014/015)

30. **Rate limiting par tool coûteux** (PDF, LLM long) (source : 012)
    - Fichier : `backend/app/graph/graph.py` (à implémenter après rate limiting chat général P1 #2)
    - Impact : un user peut déclencher 5 `generate_credit_certificate` en 5 messages = 5 PDFs générés

31. **Circuit breaker sur retry** (alerte ops si > X% échecs) (source : 012)
    - Fichier : `backend/app/graph/tools/common.py` (extension de `with_retry`)
    - Impact : retry silencieux masque aujourd'hui les incidents systémiques (bug code, pas timeout transient)

32. **Heuristique rapide avant LLM `_is_topic_continuation`** (source : 013)
    - Fichier : `backend/app/graph/nodes.py:176`
    - Impact : appel LLM à CHAQUE message pendant un module actif (30 messages ESG = 30 appels LLM) — coût cumulé tokens + latence

33. **Circuit breaker timeouts LLM classification** (source : 013)
    - Fichier : `backend/app/graph/nodes.py:176`
    - Impact : FR-005 défaut "continuation" bloque les vraies demandes de changement si LLM timeout systématique

34. **TypedDict par module pour `active_module_data`** (source : 013)
    - Fichier : `backend/app/graph/state.py:35`
    - Impact : erreurs de frappe non détectées au runtime (dict générique accepte n'importe quel schéma)

35. **TTL sur `active_module`** (24h d'inactivité) (source : 013)
    - Fichier : `backend/app/graph/nodes.py` (router_node)
    - Impact : user inactive 1 semaine reprend et reçoit des réponses ESG alors qu'il voulait chat général

36. **Logger usages aliases `normalizeTimeline`** (source : 013)
    - Fichier : `frontend/app/utils/normalizeTimeline.ts`
    - Impact : tolérance actuelle masque les bugs de schéma LLM → pas de rétro-boucle pour corriger les prompts

37. **Extraire helper dédié `_should_inject_guided_tour()`** (source : 014)
    - Fichier : `backend/app/prompts/system.py:213-214`
    - Impact : **couplage fragile** déjà documenté dans deferred-work.md — `STYLE_INSTRUCTION` + `GUIDED_TOUR_INSTRUCTION` partagent la même branche conditionnelle `_has_minimum_profile`. Modifier le seuil du style change silencieusement le guidage.

38. **Framework d'injection d'instructions transverses** (registry + builder unifié) (source : 014)
    - Fichier : `backend/app/prompts/system.py` (refactor)
    - Impact : pattern dupliqué 3 fois (STYLE / WIDGET / GUIDED_TOUR) — une 4ème instruction = 4ème duplication. Abstraire via registry + builder réduit la dette future.

39. **Tests de conformité au style** sur fixtures golden (source : 014)
    - Fichier : `backend/tests/test_prompts/test_style_instruction.py` + fixtures
    - Impact : SC-003/SC-004/SC-005 mesurables en théorie mais aucune instrumentation → style dérive silencieusement au fil des upgrades LLM/prompts.

40. **Constantes nommées pour seuils magiques** (ex: `MINIMUM_PROFILE_FIELDS_FOR_STYLE = 2`) (source : 014)
    - Fichier : `backend/app/prompts/system.py:163-168`
    - Impact : "2" hard-codé sans justification documentée

41. **Instructions de style configurables par user** (style expert/débutant/concis) (source : 014)
    - Fichier : nouveau (préférences user) + `build_system_prompt`
    - Impact : impossible d'A/B tester ou de personnaliser le style — tout est monolithique backend

42. **Helper `build_tool_calling_rule()`** pour prompts répétés (source : 015)
    - Fichier : `backend/app/prompts/` (nouveau helper) + refactor application.py, credit.py, esg_scoring.py
    - Impact : pattern "ROLE actif + OUTILS DISPONIBLES + REGLE ABSOLUE" dupliqué 3× — une 4ème REGLE = 4ème duplication. Consolider avec spec 014 §3.2 (framework injection instructions)

43. **Tests d'intégration "le LLM appelle-t-il vraiment le tool ?"** (source : 015)
    - Fichiers : `backend/tests/test_prompts/` (fixtures + tests comportementaux)
    - Impact : tests actuels vérifient le contenu string du prompt, pas le comportement LLM observé → upgrade LLM ou régression prompt peut casser sans détection

44. **Constante `LLM_REQUEST_TIMEOUT_SECONDS = 60`** (source : 015)
    - Fichier : `backend/app/graph/nodes.py:315`
    - Impact : magic number `request_timeout=60` hard-codé, oubli possible si autre module crée un LLM ailleurs

45. **Instrumenter `batch_save_*` usage** (métriques `batch_size` dans `tool_call_logs`) (source : 015)
    - Fichier : `backend/app/graph/tools/common.py` + `esg_tools.py`
    - Impact : impossible de vérifier si le LLM respecte l'instruction de batcher (post-pilier ESG) ou continue les appels séquentiels

46. **Tests de charge courbe latence finalisation ESG** (N=10/30/50/100 critères) (source : 015)
    - Fichier : `backend/tests/test_tools/test_esg_tools.py`
    - Impact : SC-003 vérifie N=30 en < 15s, mais courbe non mesurée pour extensions futures

47. **Robustesse `GaugeBlock`** (fallback sur JSON malformé / valeur invalide) (source : 016)
    - Fichier : `frontend/app/components/richblocks/GaugeBlock.vue`
    - Impact : fix spec 016 est conditionnel sur `isStreaming` dans `MessageParser`, pas sur la robustesse du composant → JSON malformé peut encore afficher un gauge vide

48. **Dashboard bugs par module** (métrique bugs ESG/carbon/financing/gauge) (source : 016)
    - Nouveau outil de monitoring
    - Impact : après 4 specs-correctif en 2 semaines (013/015/016/017), pas de visibilité sur "combien de bugs par module" → anticipation impossible

49. **Linter custom "tous les tests API utilisent `override_auth`"** (source : 017)
    - Fichier : script pytest collection hook ou lint personnalisé
    - Impact : si un futur test API oublie le fixture, test échoue avec 401 sans alerte préventive

50. **`make_conversation_state` dérivé de `ConversationState.__annotations__`** (source : 017)
    - Fichier : `backend/tests/conftest.py:101`
    - Impact : helper duplique manuellement 27 clés du TypedDict — ajouter un 28ème champ = mise à jour manuelle oubliable

51. **Dockeriser les tests** (conteneur avec deps système Cairo/Pango/Tesseract) (source : 017)
    - Fichier : `backend/tests/Dockerfile.test` + CI config
    - Impact : dépendances système C aujourd'hui mockées pour portabilité CI → masque un problème d'isolation environnement

52. **Budget temps + profiling suite de tests** (source : 017)
    - Fichier : CI config + profiling pytest
    - Impact : 907 tests mais temps d'exécution non mesuré — pas de budget (ex: "< 5 min en CI")

53. **Tests Vitest 6 composants Vue widgets** (SingleChoiceWidget, MultipleChoiceWidget, JustificationField, AnswerElsewhereButton, InteractiveQuestionHost, InteractiveQuestionInputBar) (source : 018)
    - Fichier : `frontend/tests/unit/`
    - Impact : 6 composants en prod sans tests unitaires Vitest — robustesse frontend non validée formellement

54. **Tests E2E Playwright pour les 4 US widgets** (QCU, QCM, justification, fallback) (source : 018)
    - Fichier : `frontend/tests/e2e/interactive-widgets-*.spec.ts`
    - Impact : parcours UX non couverts en E2E — régressions UX invisibles sans audit manuel

55. **Instrumentation SC widgets** (temps de réponse, taux de complétion, nb widgets/question fermée par module) (source : 018)
    - Fichier : nouveau module d'analytics + hooks frontend
    - Impact : SC-001 à SC-004 et SC-006 mesurables en théorie, pas mesurés → impact réel de la feature non vérifié

56. **Garde-fous contre abus LLM du tool `ask_interactive_question`** (15+ options, widget sur question ouverte, fréquence) (source : 018)
    - Fichier : `backend/app/graph/tools/interactive_tools.py` + tests
    - Impact : validation Pydantic couvre 2-8 options mais pas les cas "widget inapproprié" ou "spam de widgets"

---

## Dette transverse critique — Investigation root cause US1 spec 016

**Action P2 dédiée** (source : 016 §3.4)

**Hypothèse à confirmer** : lors d'une évaluation ESG, le LLM confond parfois `update_company_profile` (bindé sur `chat_node`) avec `save_esg_criterion_score` (bindé sur `esg_scoring_node`). Cela suggère un **couplage routing ↔ tool binding** :
- Si le routing multi-tour spec 013 fait un faux négatif ("continuation") et route vers `chat_node` au lieu de `esg_scoring_node`, les tools disponibles changent
- Le prompt ESG ne s'applique plus (chat_node a son propre prompt)
- Le LLM, ayant accès à `update_company_profile` mais pas à `save_esg_criterion_score`, "traduit" la réponse utilisateur en update profil

**Fix chirurgical spec 016** : prompt plus directif. Insuffisant si la cause racine est le routing.

**Action** : instrumenter `tool_call_logs` pour tracer (conversation_id, node_name, tool_name) sur les évaluations ESG — confirmer/infirmer l'hypothèse avant d'accumuler d'autres "REGLE ABSOLUE".

---

## Findings méthodologiques speckit

Patterns révélés par les audits, non attribuables à une spec individuelle mais au **workflow speckit appliqué au projet**. Ces findings doivent informer les décisions méthodologiques futures (speckit → BMAD à partir de spec 019).

### 🚨 Typologie des discordances speckit (5 types observés)

Après 9 audits, on identifie **5 types distincts** de discordance entre ce qu'annonce la spec et ce qui est réellement livré :

| # | Type | Spécificité | Cas observés |
|---|------|-------------|--------------|
| 1 | Artefact cité absent | Task `[X]` référence un fichier qui n'existe pas dans le repo | Spec 002 T038 (`chat.spec.ts`), Spec 006 T030/T031 (`REPORT_TOOLS`) |
| 2 | Test déclaré mais non écrit | Fichier de test cité dans `tasks.md`, absent du repo | Spec 008 (×5), Spec 010 (×1) |
| 3 | **FR explicite non implémentée** | Fonctional Requirement écrit dans `spec.md`, aucune trace dans le code | Spec 002 FR-013 (rate limiting), Spec 003 (édition manuelle prévaut), Spec 009 FR-005 (RAG applications) |
| 4 | Edge case documenté non implémenté | Scénario décrit dans spec mais pas couvert par une tâche | Spec 005 (détection incohérence réponses) |
| 5 | Phase non terminée `[ ]` | Phase officielle non close, spec livrée en état ambigu | Spec 009 Phase 12 Polish + Spec 013 T056 (vérification manuelle quickstart) — 2 cas observés |

**Le type 5 est paradoxalement plus sain** : au moins c'est honnête. Mais ça révèle qu'une spec peut être « officiellement incomplète » sans que le workflow speckit force sa clôture.

**Les types 1-4 sont plus problématiques** : déclarations mensongères (intentionnelles ou pas), invisible sans audit manuel, impossible à détecter via la progression `tasks.md [X]`.

### 🚨 Discordance tasks `[X]` vs artefacts réels (type 1+2 détaillé)

Les tâches marquées `[X]` dans `tasks.md` sont **auto-déclaratives sans gate de vérification code**. Plusieurs cas confirmés :

- **Spec 002 T038** — `frontend/tests/e2e/chat.spec.ts` absent du repo
- **Spec 006 T030/T031** — notification chat FR-019 jamais implémentée (pas de `REPORT_TOOLS`, pas d'event SSE `report_ready`, aucune référence à "report" dans `graph.py`)

**Ratio confirmé après audit forensique 2026-04-16** : 2,4 % de vrais manquants sur 253 paths audités (specs 007-018). Voir `docs/audit-tasks-discordance.md`.

**Résultat de l'audit forensique** :

| Verdict | Count | % |
|---|---|---|
| ✅ Présents | 228 | 90,1 % |
| 🔴 Vrais manquants | 6 | 2,4 % |
| 🟡 Typos / renommages | 6 | 2,4 % |
| ⚪ Supprimé intentionnellement | 1 | 0,4 % |

**Vrais manquants concentrés sur 2 specs** :

- **Spec 008 (Financing) — CRITIQUE** : 5 tests backend absents sur le module **matching projet-financement** (cœur de la value proposition Mefali)
  - `backend/tests/test_financing/test_matching.py` — logique matching (sans test)
  - `backend/tests/test_financing/test_models.py` — modèles Fund/Intermediary (sans test)
  - `backend/tests/test_financing/test_router_funds.py` — endpoints catalogue
  - `backend/tests/test_financing/test_router_matches.py` — endpoints matching
  - `backend/tests/test_financing/test_service_pathway.py` — parcours direct/intermédiaire
  - Impact : silence total en cas de régression sur le matching. À prioriser P1.

- **Spec 010 (Credit)** : `frontend/tests/credit-score.test.ts` absent (page + store `creditScore.ts` sans couverture frontend)
  - Impact : P2, dette de couverture

**Observations méthodologiques** :

- **Specs 011-018 : 0 manquant** — discipline de livraison nettement meilleure sur la seconde moitié du projet. Le problème n'est pas systémique.
- Les discordances en prose (sans path, ex : spec 002 T038 chat.spec.ts, spec 006 T030/T031 REPORT_TOOLS) sont hors périmètre du script — détectées uniquement par retros manuelles.
- Conclusion : l'intuition initiale « features partiellement livrées » est confirmée mais **localisée** (specs 002, 006, 008, 010 principalement).

**Actions consolidées issues de cet audit** :
- P1 : créer les 5 tests backend spec 008 (ajouté à la liste P1 ci-dessous §11)
- P2 : créer le test frontend spec 010 (ajouté à la liste P2 ci-dessous)

### 📝 Exigences spec documentées mais non implémentées

3 cas confirmés (specs 002, 003, 005) d'exigences explicites dans `spec.md` **sans tâche associée dans tasks.md** → non livrées :

- **Spec 002** : FR-013 rate limiting 30 msg/min (P1 sécurité)
- **Spec 003** : règle « édition manuelle prévaut » (P1 — perte de données)
- **Spec 005** : détection d'incohérence dans les réponses ESG (P2)

**Cause racine** : le passage `spec.md → tasks.md` ne garantit pas la couverture exhaustive des FRs et edge cases documentés.

**Mitigation pour BMAD** : le workflow `bmad-check-implementation-readiness` (gate obligatoire avant stories) couvre ce trou — à systématiser sur toute feature future.

### 🏗️ Design rigide qui a dû muter en aval

Plusieurs specs initiales ont livré des designs qui ont nécessité des refactors majeurs dans les specs suivantes :

- **Spec 001 → 013** : `ConversationState` sous-dimensionné, a dû ajouter `active_module` + `active_module_data`
- **Spec 001 → 012** : `chat_node` monolithique, explosion en 9 nœuds + ToolNodes + boucle conditionnelle
- **Spec 002 → 013** : `TimelineBlock` schema rigide, a dû créer `normalizeTimeline` (5 aliases tolérés)
- **Spec 002 → 018** : `MessageParser` 6 blocs hardcodés, spec 018 a créé un système parallèle (`interactive_questions`) plutôt qu'un 7ᵉ bloc
- **Spec 003 → 013** : router heuristique regex remplacé par classification LLM

**Leçon** : les points d'extension (state, schemas, parsers, routers) doivent être conçus comme **contrats extensibles** dès la foundation, pas comme des structures de convenance.

### 💾 Hard-coding systémique des données métier (confirmé spec 005/006/007/008)

Pattern **massif** révélé par les audits 005-008 : **toute la donnée métier de la plateforme est hard-codée dans le code source**, pas en BDD avec interface admin.

| Spec | Données hard-codées | Volume | Conséquence |
|---|---|---|---|
| 005 | `SECTOR_WEIGHTS`, `SECTOR_BENCHMARKS` | 6 secteurs | Scoring ESG non paramétrable |
| 006 | Référentiels UEMOA/BCEAO dans templates HTML | ~30 lignes | Mise à jour réglementaire = redéploiement |
| 007 | Facteurs d'émission sans sources + `SECTOR_BENCHMARKS` carbon | 7+ facteurs, 8 secteurs | Calculs invérifiables (SC-003 : "1% précision" non auditable) |
| 008 | **12 fonds + 14 intermédiaires + ~50 liaisons** | **889 lignes de `seed.py`** | **Infos bailleurs vont vieillir sans traçabilité** |

**Conséquences métier, pas seulement techniques** :
- Les fonds climatiques changent régulièrement leurs conditions (montants, échéances, critères) → Mefali affiche des données obsolètes sans savoir lesquelles
- Les intermédiaires changent d'adresse / contact → user tente de contacter un interlocuteur injoignable → perte de confiance
- Pas de `last_verified_at` ni provenance → impossible de réauditer
- Toute correction = développeur + déploiement + pas d'A/B test

**Action transverse à anticiper dans le PRD suivant** :
- Table `fund` + `intermediary` + `fund_intermediary_link` avec admin panel + champs `last_verified_at`, `source_url`, `verified_by_user_id`
- Table `esg_sector_config` (weights + benchmarks)
- Table `carbon_emission_factor` (facteurs + source + date de révision)
- Table `regulation_reference` (taxonomies UEMOA/BCEAO versionnées)

**Gravité** : pas bloquant en MVP mais **incompatible avec une mise en production** où des utilisateurs réels s'engageraient sur la base de ces données.

### 🎨 Validation absente sur contenus LLM persistés

Pattern détecté sur specs 006 + 008 (les deux documents PDF générés aux utilisateurs ont le problème — résumé exécutif ESG + fiche de préparation financement). À anticiper sur specs 009 (dossiers financement générés par IA) et 011 (plans d'action générés par IA). Tout contenu LLM qui devient un **document persisté** (PDF, dossier, plan) doit avoir des guards : longueur, langue, cohérence numérique, vocabulaire interdit.

**Déjà consolidé** en P1 #10 de la section actions (couvre 006 + 008). À étendre si 009 et 011 révèlent le même pattern.

### 🔧 Features construites mais sous-exploitées

- **RAG pgvector** : utilisé par 1/8 modules (ESG seul). Coût embeddings payé pour 12,5 % de la valeur.
  - Spec 007 confirme : carbon ne consomme pas non plus le RAG (factures électricité, bilans comptables idéaux pour alimenter `save_emission_entry`).

À surveiller sur les audits 008-011 pour identifier d'autres cas de sur-investissement.

### 🔁 Tool-calling séquentiel multi-entrées (à consolider)

Pattern de design récurrent : un tool appelé 5-30 fois séquentiellement pour sauvegarder des données en lot, causant des timeouts LLM sur les cas réels.

- **Spec 005** (ESG) : 30 critères → 30 appels `save_esg_criterion_score` → timeout → **fix en spec 015** (`batch_save_esg_criteria`)
- **Spec 007** (carbon) : 5-15 entrées → 5-15 appels `save_emission_entry` → timeout imminent → **pas de fix à ce jour** (P1 dans actions consolidées §12)
- **Specs 009 (application) et 010 (credit)** : **audits confirment que ce pattern n'est PAS présent** — application utilise 1 appel par section (opérations distinctes, pas un batch), credit utilise `generate_credit_score` en 1 appel qui agrège tout en interne. ✅

**Consolidation finale** : le pattern n'affecte que carbon (à fixer) — ESG est déjà corrigé, application/credit ne sont pas concernés. Story unique P1 #12 suffit.

### 🚨 Saturation du pattern « prompts directifs » (signal systémique, spec 016)

**4 specs-correctifs consécutives** en 2 semaines (013, 015, 016, 017) traitent toutes le même symptôme sous-jacent : le LLM n'appelle pas les tools comme prescrit, ou appelle les mauvais tools, ou ignore les consignes. À chaque fois, le fix consiste à **ajouter des instructions directives** dans les prompts (`REGLE ABSOLUE`, `OBLIGATOIRE`, `JAMAIS/TOUJOURS`).

**Saturation observée** :
- `"REGLE ABSOLUE"` apparaît désormais **5-6 fois** dans les prompts modules (esg_scoring, carbon, credit, application, financing + `tool_instructions` chat)
- Instructions contradictoires possibles entre sections (cas observé avec guided_tour spec 019 : `## OUTILS DISPONIBLES` fermé + `GUIDED_TOUR_INSTRUCTION` tardif ignoré)
- Le prompt total dépasse 15 000 chars pour certains modules → risque de *attention discount* du LLM

**Limites atteintes** :
- Plus on ajoute de prompts directifs, plus on perd en déterminisme
- Un upgrade LLM peut régresser silencieusement
- Debug complexe (quelle instruction a été ignorée ?)

**Solutions structurelles à considérer dans le prochain PRD** :
1. **Enforcement applicatif** : flags `pending_confirmation`, state machines explicites, guards *avant* l'exécution des tools
2. **Décomposition** : agents LangGraph dédiés par étape métier avec state partagé explicite, plutôt qu'un seul nœud avec 10 tools
3. **Tests de comportement LLM** : pas juste « le prompt contient X », mais « le LLM appelle Y dans ce contexte »

**Signal pour le prochain PRD** : cette saturation **mérite une réflexion architecturale** avant d'ajouter de nouvelles fonctionnalités qui généreront encore plus de prompts directifs.

### 💡 Principe de design : « Prompt qui contient la donnée = tool ignoré »

Leçon de spec 016 US3 : la BDD des 12 fonds était dans le prompt financing → le LLM les régurgitait de mémoire au lieu d'appeler `search_compatible_funds`. Fix : retirer la donnée du prompt. Résultat : le LLM est obligé d'appeler le tool.

**Principe transférable** : si un prompt contient des informations qu'un tool pourrait retourner, le LLM zappera le tool dans N % des cas. Garder les prompts **légers en données**, **riches en instructions**.

**Applications à vérifier** :
- `company_context` est injecté dans esg_scoring_node, carbon_node... Le LLM appelle-t-il quand même `get_company_profile` ? À instrumenter.
- `applicable_categories` dans carbon_node — le LLM appelle-t-il `get_applicable_categories` ?
- Plus largement : toute donnée injectée dans un prompt **doit être une donnée qui n'est pas accessible via un tool**.

### 🧰 Gouvernance CI laxiste — tolérance à la dette normalisée (spec 017)

Spec 017 a révélé que **34 tests en échec se sont accumulés sur plusieurs semaines** (probablement depuis specs 009-011). La CI a continué à accepter ces échecs comme « known failures » sans bloquer les merges.

**Signal de gouvernance** : tolérer des tests rouges sur `main` normalise la dette technique et rend impossible la détection de vraies régressions (on ne peut plus distinguer un nouveau bug d'un vieux échec connu).

**Règle à instaurer** :
- **Zero failing tests on main** : protection de branche GitHub bloquant les merges tant qu'un test échoue
- Pas de « known failure » : soit skip explicite avec ticket, soit fix immédiat
- CI temps d'exécution surveillé (budget ~5 min max pour ~1000 tests)

Cette règle est plus importante que le fix lui-même, car elle empêche la réaccumulation.

### 🔍 Absence d'analyse root cause dans les spec-correctifs

Pattern méthodologique observé sur specs 015 + 016 : les spec-correctifs documentent **le symptôme** et **le fix** mais pas **la cause racine** ni **les hypothèses alternatives**.

Exemple spec 016 US1 : le fix « le LLM confond `update_company_profile` et `save_esg_criterion_score` » ajoute une REGLE ABSOLUE. Mais :
- Pourquoi cette confusion apparaît-elle soudainement ?
- Est-ce un couplage routing (spec 013) / tool binding (spec 012) ? — hypothèse non vérifiée
- Le fix prompt-directif cache-t-il un bug de routing sous-jacent ?

**Recommandation pour les correctifs BMAD futurs** : intégrer une section « Root Cause Hypothesis » dans le workflow spec-correctif qui force à documenter : (1) symptôme observé, (2) hypothèse root cause, (3) vérification de l'hypothèse *avant* fix, (4) fix ciblé sur la cause plutôt que sur le symptôme.

### 📏 « Fix au pattern, pas à l'instance » (leçon méthodologique spec 015)

Spec 015 (fix ESG timeout) a résolu un symptôme précis (30 tool calls séquentiels causant timeout sur les évaluations ESG) **sans généraliser au pattern**. Résultat : la même classe de bug survit en spec 007 carbon (5-15 tool calls séquentiels sur bilans multi-véhicules), non corrigée.

**Principe à appliquer pour les prochaines spec-correctifs** : quand une spec-correctif traite un symptôme d'une classe de bug, **identifier tous les représentants connus de cette classe et les fixer simultanément**. Sinon la dette latente se réalise plus tard sur un autre module, avec un coût investigation + fix supérieur.

**Cas observés dans ce projet** :
- Tool-calling séquentiel : ESG fix en 015 → carbon non fix (dette P1 #12 créée après coup)
- Guards LLM persistés : spec 006 identifié → spec 008 même pattern → spec 011 idem (P1 #10 consolidé progressivement a posteriori)
- Queue asynchrone : spec 006 PDF identifié → spec 011 LLM plan (P1 #6 consolidé a posteriori)

**Test à ajouter aux retros futures** : « cette spec-correctif généralise-t-elle au pattern ou seulement à l'instance observée ? ». Si instance seulement, ouvrir une story de généralisation immédiatement pour éviter la réapparition du bug sur un autre module.

### 🏛️ Violation de l'encapsulation inter-services (« God service »)

Pattern détecté en spec 011 : `dashboard/service.py` (487 lignes) consomme **directement les tables** `companies`, `esg_scores`, `carbon_assessments`, `credit_scores`, `fund_matches`, `action_items`, `reminders` au lieu de passer par les services respectifs de chaque module.

**Conséquences** :
- **Duplication des règles métier** : filtres « quel score afficher si plusieurs assessments », invariants, jointures — potentiellement redéfinis entre `esg/service.py` et `dashboard/service.py`
- **Fragilité** : une migration de schéma dans un module casse silencieusement le dashboard sans alerte
- **Couplage fort** : le dashboard est effectivement couplé à la **structure BDD** de 5 autres modules, pas à leurs API publiques

**Leçon** : les agrégateurs (dashboard, rapports, export) doivent consommer les **services** des modules, jamais leurs tables directement. Frontière claire à garder.

À surveiller sur spec 006 (reports) et spec 012 (tool-calling agrégé) : même pattern possible.

### 📸 Pas de snapshot des données source dans les calculs historiques

Pattern détecté sur specs 008 + 010 :
- **Spec 008 `FundMatch`** : score de matching calculé au moment T avec profil T. Si le profil change à T+1, le match affiche toujours les mêmes chiffres mais ils ne correspondent plus à l'état du profil.
- **Spec 010 `CreditScore`** : même problème sur les scores de crédit. L'historique « évolution sur 3 versions » (SC-006) est trompeur si les `FACTOR_WEIGHTS` ou les données source ont changé entre-temps.

**Conséquence** : tout graphe d'évolution temporelle dans le produit est techniquement faux. Le user voit « mon score passe de 62 à 68 » alors qu'il s'agit peut-être d'un changement de pondérations, pas d'une amélioration réelle.

**Fix type** : ajouter un champ `source_snapshot: JSONB` sur `FundMatch` et `CreditScore` qui capture au moment du calcul : profil + pondérations + version du scoring. À faire quand les modules seront migrés vers l'architecture data-driven (cf. signaux PRD).

### ✅ Patterns positifs à reproduire (référence architecturale)

**Spec 010 Green Credit Scoring** est identifiée comme la spec la plus mature du projet :

| Critère | Spec 010 | Autres specs métier |
|---|---|---|
| Tools LangChain | ✅ `CREDIT_TOOLS + INTERACTIVE_TOOLS + GUIDED_TOUR_TOOLS` (3 groupes) | Partiel |
| Tests backend | ✅ 4 fichiers (service, router, node, chain) | Variable |
| Frontend complet | ✅ page + store + composable + 7 composants + attestation PDF | Variable |
| Coefficient confiance | ✅ 0.5-1.0 module le score selon couverture données | Absent ailleurs |
| Innovation produit | ✅ Interactions intermédiaires comme signal (FR-002/FR-004) | — |

**Utilisation recommandée** : lors de la planification de toute nouvelle feature de scoring/évaluation, **prendre spec 010 comme template mental**. Les patterns (coefficient confiance, barème transparent, intégration des interactions externes comme signal) sont transférables.

**Spec 011 Dashboard & Action Plan** = 2ᵉ référence, pour les features d'intégration multi-modules :

| Critère | Spec 011 | Spec 008 (comparaison) |
|---|---|---|
| Couverture tests | ✅ 105 tests | ❌ 5 tests backend manquants (🔴 Rework) |
| Snapshot des données liées | ✅ `ActionItem` snapshot les coordonnées intermédiaires au moment de la création | ❌ `FundMatch` pas de snapshot profil |
| Unicité BDD avancée | ✅ Partial index `postgresql_where=text("status = 'active'")` | — |
| Gamification intégrée | ✅ 5 badges auto-awardés dans les mutations | — |
| Activity Feed | ✅ Agrégation multi-sources (5 sources) | — |
| Discordance tasks↔code | ✅ 0 | ❌ 5 tests [X] fantômes |

**Spec 011 apprend des dettes des précédentes** — c'est un signe positif que le workflow speckit s'améliore au fil du projet. Les specs 011-018 n'ont 0 manquant (audit forensique) : la discipline s'est nettement renforcée sur la 2ᵉ moitié.

**Spec 013 Fix Multi-turn Routing** = 3ᵉ référence, pour les **spec-correctifs** (template à reproduire quand on doit fixer une dette technique identifiée a posteriori) :

| Critère | Spec 013 |
|---|---|
| Diagnostic ciblé | ✅ 2 bugs identifiés précisément (spec 003 §3.2 + spec 002 §3.2) |
| Fix chirurgical | ✅ active_module mechanism + normalizeTimeline — minimum nécessaire |
| Couverture tests | ✅ 806 lignes backend + 218 frontend, fichier dédié `test_active_module.py` |
| Zero régression | ✅ 796 tests existants toujours verts (vérifié dans CLAUDE.md) |
| Défaut sécuritaire | ✅ FR-005 « continuation » en cas de doute — comportement prévisible sous incertitude |

**Pattern transférable pour les futurs correctifs** : diagnostic précis → fix ciblé → tests dédiés → vérification non-régression explicite.

**Spec 014 Concise Chat Style** = 4ᵉ référence, pour les **micro-specs d'instruction transverse** (toute nouvelle consigne à injecter dans les 7 prompts modules simultanément) :

| Critère | Spec 014 |
|---|---|
| Scope bien défini | ✅ 22 tâches, 7 fichiers, 8 tests |
| DRY | ✅ Instruction définie une fois (`STYLE_INSTRUCTION`) puis importée dans les 6 modules |
| Adoption par les specs suivantes | ✅ 018 (`WIDGET_INSTRUCTION`) + 019 (`GUIDED_TOUR_INSTRUCTION`) ont copié le pattern |
| 0 régression | ✅ 7 tests existants + 8 nouveaux tests |
| Discordance | ✅ 0 |

**Pattern transférable** pour toute nouvelle instruction transverse dans l'évolution future (ex. instructions pour « projet dynamique », « étude d'impact »).

**Spec 017 Fix Failing Tests** = 5ᵉ référence, pour les **spec-nettoyage** (toute campagne de remise à zéro des tests en échec) :

| Critère | Spec 017 |
|---|---|
| Diagnostic root cause structuré | ✅ 5 causes racines distinctes identifiées sur 34 tests (pas un fix-par-test) |
| Fixtures partagés | ✅ `override_auth` + `make_conversation_state` corrigent 22/34 tests à elles seules |
| Zero modification code de prod | ✅ Tous les fixes dans les tests — risque nul de régression fonctionnelle |
| Validation globale | ✅ 907/907 tests pass (SC-002) |
| Idiomatique framework | ✅ `dependency_overrides` FastAPI privilégié sur `@patch` |

**Pattern transférable** : diagnostic root cause → fixtures partagés → fixes par batch → validation globale → zero régression. À appliquer dès qu'une accumulation de tests en échec est détectée.

---

## Signaux pour le prochain PRD

Observations qui ne méritent pas une story isolée mais doivent **alimenter la réflexion du prochain PRD d'évolution** (projet dynamique, ESG relatifs, étude d'impact, dashboard graphique).

### Architecture data-driven vs hard-coded — **DÉCISION PRIORITAIRE** (cf. section « 💾 Hard-coding systémique »)

Décision structurante à prendre : toutes les données métier (fonds, intermédiaires, benchmarks sectoriels, pondérations scoring, facteurs d'émission, taxonomies réglementaires) doivent-elles migrer en tables BDD avec admin panel, ou rester hard-codées en MVP assumé ?

**Impact direct** sur tes évolutions futures :
- « Financement de projet » → nécessite de pouvoir ajouter/retirer des fonds sans déploiement
- « Critères ESG relatifs » → nécessite par définition des critères paramétrables
- « Étude d'impact » → nécessite des matrices de pondération adaptatives
- « Dashboard graphique » → nécessite des seuils/benchmarks visibles et ajustables

Si la décision est « data-driven » (**fortement recommandée avant go-live prod**), prévoir :

| Table | Contenu | Priorité |
|---|---|---|
| `fund` + `intermediary` + `fund_intermediary_link` | 12 fonds + 14 intermédiaires + ~50 liaisons (spec 008) | **Critique** (change souvent) |
| `esg_sector_config` | weights + benchmarks + critères par secteur (spec 005) | Haute |
| `carbon_emission_factor` | facteurs + source + date de révision (spec 007) | Haute |
| `regulation_reference` | taxonomies UEMOA/BCEAO versionnées (spec 006) | Moyenne |

Plus admin API `/api/admin/config/*` + UI admin back-office pour les modifier sans redéploiement. Champs obligatoires : `last_verified_at`, `source_url`, `verified_by_user_id`.

### RAG transversal ou ESG-only assumé

Le RAG pgvector est installé mais utilisé par 1/8 modules. Le futur PRD doit trancher :

**Option A** — Étendre transversalement (credit, action_plan, application, carbon, financing, profiling, document)
- Pro : capture toute la valeur des embeddings payés
- Pro : aligne avec les évolutions (étude d'impact, profil projet) qui bénéficieraient de la recherche documentaire
- Contra : refactor modéré dans 7 modules

**Option B** — Assumer ESG-only et documenter
- Pro : status quo, pas de refactor
- Contra : gâchis budget embeddings, opportunité manquée

### Framework d'injection d'instructions transverses

Le pattern de spec 014 (injection d'une instruction transverse dans les 7 prompts modules) a été **dupliqué 3 fois** (`STYLE_INSTRUCTION`, `WIDGET_INSTRUCTION`, `GUIDED_TOUR_INSTRUCTION`). Chaque nouvelle instruction = 7 fichiers modifiés + 6 imports + 6 concaténations.

Pour les évolutions à venir (« projet dynamique » / « étude d'impact » / « dashboard graphique » nécessiteront sans doute de nouvelles instructions transverses), décider dans le prochain PRD :

**Option A** — Refactor préventif en registre :
```python
# backend/app/prompts/registry.py
INSTRUCTION_REGISTRY = [
    Instruction("style", STYLE_INSTRUCTION, predicate=_has_minimum_profile),
    Instruction("widget", WIDGET_INSTRUCTION, predicate=always),
    Instruction("guided_tour", GUIDED_TOUR_INSTRUCTION, predicate=always),
]
# build_*_prompt() → auto-collecte
```

**Option B** — Accepter la duplication tant que ≤ 5-6 instructions, refactorer si 7ᵉ arrive.

**Signal** : au-delà de 5 instructions, la charge de modification devient non-linéaire et le risque d'incohérence entre modules (une instruction oubliée dans un prompt) augmente.

**Couplage fragile à noter** : `STYLE_INSTRUCTION` et `GUIDED_TOUR_INSTRUCTION` partagent la même branche conditionnelle `_has_minimum_profile(user_profile)` (system.py:213-214). Toute modification du seuil du style déplace silencieusement le guidage. Déjà documenté dans `deferred-work.md` (spec 019 review).

### Rich Blocks extensibles

`MessageParser` actuellement 6 blocs hardcodés. La spec 018 a créé un système parallèle (interactive_questions) plutôt que d'étendre. L'évolution « dashboard plus expressif, plus graphique » va sans doute rencontrer le même mur.

Décision pour le futur PRD : refactor `MessageParser` en registre extensible, ou continuer à créer des systèmes parallèles (dette accélérée).

### Validation des contenus LLM persistés

Tous les modules qui génèrent des documents officiels (PDF, dossiers, plans, attestations) doivent avoir un étage de validation entre la sortie LLM et la persistance. À formaliser en pattern transverse dans le prochain PRD.

### Évolutions produit anticipées (rappel de ta demande)

Pour mémoire, les évolutions à venir qui seront impactées par les dettes ci-dessus :

1. Financement de projet (vs entreprise) → impact sur dossiers et profil
2. Profil dynamique entreprise + projets → impact sur modèle de données
3. Dossier projet OU entreprise → nécessite abstraction polymorphe
4. Critères ESG relatifs → nécessite architecture data-driven
5. Étude d'impact → nouvelle feature, bénéficierait de RAG transversal
6. Dashboard graphique → impact sur Rich Blocks

---

## Historique

- **2026-04-16** — Création de l'index. Premier audit : spec 001-technical-foundation ✅
- **2026-04-16** — Audit spec 002-chat-rich-visuals ✅ — découverte majeure : **FR-013 rate limiting jamais implémenté** (P1 sécurité)
- **2026-04-16** — Audit spec 003-company-profiling-memory ✅ — découverte majeure : **dead code `profiling_node` + `chains/extraction.py`** (~300 lignes) remplacé par `update_company_profile` tool en spec 012 sans nettoyage
- **2026-04-16** — Audit spec 004-document-upload-analysis ✅ — architecture saine (pas de dette archi), mais **RAG sous-exploité** (1/8 modules) + quota stockage manquant + pas de détection malware
- **2026-04-16** — Audit spec 005-esg-scoring-assessment ✅ — architecture saine, mais **30 appels tool séquentiels → timeout** (fix spec 015) + benchmarks hard-codés + 5/11 secteurs non pondérés
- **2026-04-16** — Audit spec 006-esg-pdf-reports ✅ — **US4 marquée `[X]` mais non implémentée** (2ème cas de discordance speckit) + génération synchrone non scalable + pas de signature PDF
- **2026-04-16** — 📋 Rattrapage transverse : 4 reclassements P2→P1 appliqués (spec 003/004/005/006), ajout sections « Findings méthodologiques » et « Signaux pour le prochain PRD »
- **2026-04-16** — 🔍 Audit forensique `tasks [X]` vs artefacts réels sur specs 007-018. Résultat : **2,4 % de vrais manquants** (6/253). Concentrés sur spec 008 (5 tests backend financing critiques, P1) et spec 010 (1 test frontend credit, P2). Specs 011-018 = 0 manquant (discipline améliorée). Voir `docs/audit-tasks-discordance.md`.
- **2026-04-16** — Audit spec 007-carbon-footprint-calculator ✅ — 0 discordance, architecture saine, 8 secteurs benchmarkés. **Reclassement P2→P1** : pattern tool-calling séquentiel `save_emission_entry` (même que ESG fix en spec 015, non étendu à carbon). Consolidation recommandée en story transverse `pattern batch_* multi-entrées`. Nouvelle section « 🔁 Tool-calling séquentiel multi-entrées » ajoutée aux findings méthodologiques.
- **2026-04-16** — Audit spec 008-green-financing-matching 🔴 **Rework nécessaire** — 5 tests backend absents sur le cœur de la value proposition (matching, router_matches, pathway, router_funds, models). 12 fonds + 14 intermédiaires hard-codés dans `seed.py` (889 lignes) sans `last_verified_at`. Test fiche PDF sans assertions contenu → **consolidation avec P1 #10 (guards sur contenus LLM persistés en PDF)**. Section « 💾 Hard-coding systémique » élargie pour couvrir les données métier. Section « Architecture data-driven » dans signaux PRD renforcée avec tableau priorité des tables à créer. 3ème spec avec discordance majeure.
- **2026-04-16** — Audit spec 009-fund-application-generator ⚠️ **Dettes lourdes** — 🔴 **FR-005 RAG non implémenté** (promesse spec non tenue, aucun `search_similar_chunks` dans `applications/`) + Phase 12 Polish `[ ]` (5ᵉ type de discordance speckit découvert : « phase incomplète »). Bonne couverture de tests (7 fichiers), machine à états propre, 4 templates par `target_type`. **Nouveau P1 #13 (RAG applications)** + consolidation du P2 #6 dans le même cluster « RAG transversal ». Nouvelle section « Typologie des discordances speckit » ajoutée aux findings méthodologiques avec les 5 types observés.
- **2026-04-16** — Audit spec 010-green-credit-scoring ✅ — **référence architecturale n°1** : la plus mature des specs métier (3 groupes de tools, 4 tests backend, frontend complet, coefficient confiance, innovation produit interactions-comme-signal). Nouveau pattern méthodologique **« Pas de snapshot des données source »** (spec 008 FundMatch + spec 010 CreditScore — historique trompeur). Nouvelle section **« Patterns positifs à reproduire »**, spec 010 comme template mental. Confirmation que le pattern tool-calling séquentiel N'AFFECTE PAS application/credit → story P1 #12 reste limitée à carbon.
- **2026-04-16** — Audit spec 011-dashboard-action-plan ✅ — **référence architecturale n°2** : 105 tests, 0 discordance, spec qui **apprend des dettes des précédentes** (snapshot intermédiaires dans `ActionItem` — corrige la dette de spec 008 FundMatch). Nouveau finding méthodologique **« 🏛️ Violation de l'encapsulation inter-services (God service) »** (dashboard consomme directement 5 tables au lieu des services). **Consolidations** : P1 #10 élargi au plan d'action JSON (guards sur contenus LLM persistés), P1 #6 élargi à la génération LLM (queue async transverse PDF + LLM). Dettes opérationnelles liées au scale (5 queries sérialisées dans `get_dashboard_summary`, polling 60s rappels). 0 P1 spécifique à spec 011.
- **2026-04-16** — Audit spec 012-langgraph-tool-calling ⚠️ **Dettes lourdes** — **refactor architectural majeur réussi** (32 tools, `create_tool_loop`, `ToolCallLog`, `with_retry`). **MAIS 5ème cas systémique de discordance speckit** : FR-021 (retry) + FR-022 (journalisation) non câblés sur 9/11 modules malgré primitives créées. Absorbe la dette P2 #2 existante en la promouvant P1 #14. Contribution la plus structurante du projet après spec 001.
- **2026-04-16** — Audit spec 013-fix-multiturn-routing-timeline ✅ — **spec-correctif exemplaire** (806 lignes tests backend, zero régression). Répare 2 dettes héritées : spec 003 §3.2 (routeur heuristique) + spec 002 §3.2 (TimelineBlock rigide). 0 dette P1. Seule dette P2 : `active_module` non exposé au frontend → user navigue à l'aveugle dans conversation multi-module.
- **2026-04-16** — Audit spec 014-concise-chat-style ✅ — **micro-spec parfaitement exécutée** (22 tâches, 7 fichiers, 8 tests, pattern DRY). Pose le **standard d'injection d'instructions transverses** repris par features BMAD 018 (WIDGET_INSTRUCTION) et 019 (GUIDED_TOUR_INSTRUCTION). 0 dette P1/P2 mais 5 dettes P3 (couplage fragile `_has_minimum_profile` déjà dans deferred-work, framework d'injection à abstraire, mesurabilité SC, seuils magiques, configurabilité style).
- **2026-04-16** — Audit spec 015-fix-toolcall-esg-timeout ✅ — **spec-correctif chirurgical P1 réussi** (3 anomalies résolues, 14 tests, zero régression sur 856). 2 nouveaux tools (`batch_save_esg_criteria`, `create_fund_application`) + 3 prompts renforcés (ROLE actif + REGLE ABSOLUE) + `request_timeout=60`. **Mais** n'a pas généralisé le batch pattern au module carbon — dette P1 #12 (batch_save_emission_entries) déjà identifiée par audit spec 007. Leçon clé : quand un fix s'applique à un pattern, généraliser au pattern, pas à l'instance.
- **2026-04-16** — Audit spec 016-fix-tool-persistence-bugs ✅ — **2ème spec-correctif en 2 semaines sur le même pattern** (tool calling + prompts). 5 bugs chirurgicalement résolus (13 tests, zero régression) mais **signal systémique** : 4 specs-correctif d'affilée (013, 015, 016, 017) sur un système LLM+tools fragile. Pattern "REGLE ABSOLUE" dupliqué 5-6 fois. **33 tests pré-existants en échec** documentés mais non adressés (spec 017 créée pour ça). Hypothèse root cause US1 non diagnostiquée : couplage routing spec 013 ↔ tool binding spec 012.
- **2026-04-16** — Audit spec 017-fix-failing-tests ✅ — **spec-nettoyage exemplaire**. 34 tests → 0 échec via diagnostic en 5 causes racines distinctes : 15 auth (`override_auth` fixture), 7 state incomplet (`make_conversation_state` helper), 3 Form/JSON, 1 mock type, 6 WeasyPrint. 2 fixtures partagés couvrent 22/34. **Zero code production modifié, 907/907 tests pass**. Rétablit la santé de la suite après 4 semaines d'accumulation. Action P2 ajoutée : politique CI "zero failing tests on main".
- **2026-04-17** — Audit spec 018-interactive-chat-widgets ✅ — 🎯 **DERNIÈRE SPEC SPECKIT / CYCLE D'AUDIT COMPLET 18/18**. **Spec la plus mature du cycle** : 5 clarifications (record), honnêteté documentaire avec `[ ]` explicites justifiés (vs faux `[x]` specs précédentes), 6 composants Vue livrés (1 bonus), validation Pydantic croisée, pattern cohérent avec spec 014 (WIDGET_INSTRUCTION), 935 tests backend verts. Dettes résiduelles : tests frontend Vitest + E2E Playwright reportés (P2), régénération widget à la reprise partiellement implémentée (P2), instrumentation SC non faite (P3). Démontre que speckit peut produire des specs matures quand on investit dans les clarifications.
- **2026-04-17** — 🎯 **FIN DU CYCLE D'AUDIT** : 18/18 specs audités. **Cumul final** : 14 P1, 28 P2, 56 P3. Document `index.md` = source de vérité pour le backlog de dettes à ouvrir en stories BMAD.
