---
title: "Copilot conversationnel — extension tool-calling"
epic_number: 16
status: planned
story_count: 6
stories: [16.1, 16.2, 16.3, 16.4, 16.5, 16.6]
dependencies:
  - epic: 10
    type: blocking
    reason: "Framework prompts CCC-9 + LLM Provider Layer"
  - epic: 11
    type: blocking
    reason: "Tools rattachés au cluster A"
  - epic: 12
    type: blocking
    reason: "Tools rattachés au cluster A'"
  - epic: 13
    type: blocking
    reason: "Tools rattachés au cluster B"
  - epic: 14
    type: blocking
    reason: "Tools rattachés au cube 4D"
  - epic: 15
    type: blocking
    reason: "Tools rattachés au moteur livrables"
fr_covered: [FR45, FR46, FR47, FR48, FR49, FR50]
nfr_renforces: [NFR5, NFR17, NFR42, NFR74, NFR75]
qo_rattachees: []
notes: "Extension tool-calling LangGraph aux nouveaux modules Epic 11-15. active_project + active_module cross-turn. Widgets interactifs (FR47 étendu). Guided tours. Fallback manuel. Reprise depuis checkpoint MemorySaver."
---

## Epic 16 — Stories détaillées (Copilot conversationnel — extension tool-calling)

> **Contexte brownfield** : specs 012 (tool-calling), 013 (routing multi-tour active_module), 014 (style concis), 015/016/017 (corrections), 018 (widgets interactifs), 019 (floating copilot + guided tours) **déjà livrées**. Epic 16 est une **extension incrémentale** ciblant les nouveaux tools Epic 10–15 (projects, maturity, admin_catalogue, deliverables, cube 4D matching) et les manques FR45–FR50.

### Story 16.1 : Enregistrement tools des nouveaux modules dans LangGraph `chat_node`

**As a** PME User,
**I want** pouvoir invoquer par chat toutes les nouvelles capabilities des clusters A/A'/B/Cube 4D/C (créer Company, déclarer maturité, enregistrer facts, matcher fonds, générer livrable) de la même manière que les modules existants,
**So that** la modalité secondaire « tout invocable par chat » soit complète (FR45).

**Metadata (CQ-8)** — `fr_covered`: [FR45] · `nfr_covered`: [NFR5, NFR17, NFR38] · `phase`: 1 · `cluster`: Copilot · `estimate`: L · `depends_on`: [Story 9.7 instrumentation, Epic 10 nouveaux modules, Epic 11–15 tools métiers]

**Acceptance Criteria**

**AC1** — **Given** les nouveaux tools métier des Epics 11–15 (`projects_tools`, `maturity_tools`, `admin_catalogue_tools` UI-only côté admin, `deliverables_tools`, `cube4d_matching_tools`, `fund_application_tools`), **When** chargés, **Then** ils sont tous enregistrés dans le `ToolNode` LangGraph **And** instrumentés `with_retry` + `log_tool_call` (Story 9.7 garde-fou).

**AC2** — **Given** un user demande « crée-moi un projet agroalimentaire au Sénégal en phase idée », **When** `chat_node` traite, **Then** le LLM invoque `create_project` avec les bons arguments parsés **And** réponse streamée en < 2 s p95 premier token (NFR5).

**AC3** — **Given** une chaîne d'outils (ex. `create_project` → `attach_beneficiary_profile` → `declare_maturity_level`), **When** le LLM orchestre, **Then** max 5 tool calls par turn (pattern spec 012) + retry automatique 1× par tool + timeout LLM 60 s.

**AC4** — **Given** un tool échoue après retry, **When** constaté, **Then** le chat fallback gracieusement avec message « je n'ai pas pu <action>, voici le lien vers le formulaire » (préfigure FR49 Story 16.5).

**AC5** — **Given** les tests, **When** `pytest backend/tests/test_graph/test_chat_node_extended_tools.py` exécuté, **Then** scénarios (chaque nouveau tool invoqué, chaîne 3 tools, retry transient, fallback error) tous verts + coverage ≥ 80 %.

---

### Story 16.2 : Extension `ConversationState` avec `active_project` cross-turn

**As a** PME User,
**I want** que le copilot maintienne le contexte du projet actif à travers les tours de conversation (en plus de `active_module` déjà livré spec 013),
**So that** je n'aie pas à ré-indiquer « pour mon projet X » à chaque nouveau message quand je travaille sur un même projet.

**Metadata (CQ-8)** — `fr_covered`: [FR46] · `nfr_covered`: [NFR50] · `phase`: 1 · `cluster`: Copilot · `estimate`: M · `depends_on`: [Story 16.1, spec 013 `active_module` livré]

**Acceptance Criteria**

**AC1** — **Given** `ConversationState`, **When** auditée, **Then** elle porte **toujours** le champ `active_project_id: UUID|null` (schéma unique, pas de variant conditionnel — infra toujours prête) + reducer approprié (pattern spec 013 pour `active_module`) + persistance LangGraph MemorySaver **And** défaut `null` + aucune contrainte `NOT NULL`.

**AC2** — **Given** `ENABLE_PROJECT_MODEL=false` (Story 10.9), **When** `router_node` traite un tour, **Then** il **ignore** la valeur de `active_project_id` dans sa classification (feature masquée côté routing) **And** aucune erreur n'est levée si le champ est déjà peuplé.

**AC3** — **Given** un user dans une conversation avec `active_project_id=P1` et `ENABLE_PROJECT_MODEL=true`, **When** il demande « génère le rapport ESG », **Then** le copilot comprend implicitement `project_id=P1` (pas de ressaisie).

**AC4** — **Given** l'user change de projet dans le chat (« travaillons sur P2 maintenant »), **When** détecté par le routing (spec 013 pattern classification continuation vs changement), **Then** `active_project_id` passe à P2 + event SSE UI updaté + `active_module` réinitialisé.

**AC5** — **Given** une transition flag `false → true` en cours de migration Phase 1, **When** constatée, **Then** **pas de backfill forcé** sur les conversations existantes : `active_project_id` reste `null` **And** est settée progressivement à la prochaine interaction user avec un tool `projects_*` (set progressif lazy).

**AC6** — **Given** un user a `N > 3` projets et en nomme un ambigu, **When** le LLM ne peut trancher, **Then** il propose widget QCU listant les projets candidats (réutilise Story 16.3 interactive widgets).

---

### Story 16.3 : Extension widgets interactifs aux nouveaux modules (FR47 étendu)

**As a** PME User,
**I want** que le copilot utilise les widgets interactifs (QCU, QCM, QCU+justification livrés spec 018) pour la collecte de données structurées dans les nouveaux modules (maturité niveau, pack ESG, voie d'accès Fund, niveau confirmation snapshot),
**So that** les nouveaux parcours bénéficient de la même ergonomie que les parcours existants.

**Metadata (CQ-8)** — `fr_covered`: [FR47] · `nfr_covered`: [NFR54, NFR56] · `phase`: 1 · `cluster`: Copilot · `estimate`: M · `depends_on`: [Story 16.1, spec 018 widgets livré]

**Acceptance Criteria**

**AC1** — **Given** un user demande « quelle est ma maturité administrative ? », **When** le LLM interroge, **Then** il propose un widget QCU avec les 4 niveaux (spec 018 pattern) + ARIA roles conformes (NFR56).

**AC2** — **Given** les widgets sont déjà mono-pending (spec 018 invariant), **When** un nouveau widget est émis, **Then** l'ancien `pending` est marqué `expired` automatiquement (pas de régression).

**AC3** — **Given** l'user répond via widget, **When** valeur captée, **Then** le tool adapté est invoqué avec la valeur structurée (`declare_maturity_level`, `select_pack`, etc.).

---

### Story 16.4 : Extension guided tours aux nouveaux parcours Epic 11–15

**As a** PME User nouvel arrivant,
**I want** que le copilot propose des guided tours (infrastructure livrée spec 019) pour les nouveaux parcours (création Company, FormalizationPlan, évaluation ESG 3-couches, cube 4D matching, génération livrable),
**So that** je découvre l'app fluidement sans lire une doc.

**Metadata (CQ-8)** — `fr_covered`: [FR48] · `nfr_covered`: [NFR55] · `phase`: 1 · `cluster`: Copilot · `estimate`: M · `depends_on`: [Story 16.1, spec 019 guided tours livrée, Epic 11–15 UI livrées]

**Acceptance Criteria**

**AC1** — **Given** le registre de parcours guidés spec 019, **When** étendu, **Then** il inclut au minimum 5 nouveaux parcours : `company_creation`, `formalization_plan`, `esg_facts_entry`, `fund_matching`, `application_generation`.

**AC2** — **Given** chaque nouvelle UI Epic 11–15, **When** les composants clés sont implémentés, **Then** ils portent les attributs `data-guide-target="<id>"` conformes au pattern spec 019.

**AC3** — **Given** un user demande ou le LLM détecte un besoin (nouveau user, action inédite), **When** guided tour `company_creation` est déclenché, **Then** il navigue les étapes avec retract du widget (spec 019 livré) + decompteur multi-pages.

---

### Story 16.5 : Fallback gracieux manual input quand LLM échoue

**As a** PME User,
**I want** que lorsque le LLM échoue répétitivement (timeout persistant, guards bloquants, erreur parsing), le copilot bascule gracieusement vers le formulaire manuel correspondant,
**So that** je ne sois jamais bloqué dans une impasse conversationnelle (FR49).

**Metadata (CQ-8)** — `fr_covered`: [FR49] · `nfr_covered`: [NFR42, NFR75] · `phase`: 1 · `cluster`: Copilot · `estimate`: M · `depends_on`: [Story 16.1]

**Acceptance Criteria**

**AC1** — **Given** un tool échoue 3 fois consécutives (NFR75 retry budget épuisé), **When** le circuit breaker s'active, **Then** le chat affiche message « Je rencontre un souci temporaire sur <action>. Voici le lien vers le formulaire » avec deep-link via `?prefill_key=<uuid>` (pas de JSON en query string — éviter limite 8 Kio).

**AC2** — **Given** table `prefill_drafts(id UUID PK, payload JSONB, user_id UUID FK, expires_at TIMESTAMP, created_at)` (migration consolidée dans Story 10.1), **When** un tool échoue + fallback, **Then** le backend crée un enregistrement avec TTL 1 h **And** retourne l'UUID au chat.

**AC3** — **Given** RLS sur `prefill_drafts` (pattern Story 10.5 étendu), **When** un user charge `/projects/new?prefill_key=<uuid>`, **Then** l'endpoint `GET /api/prefill-drafts/{uuid}` retourne `200 payload` si user propriétaire + non expiré, **404** sinon (RLS masque cross-user).

**AC4** — **Given** la page du formulaire charge le prefill, **When** les champs sont remplis, **Then** l'user voit immédiatement ses données captées + peut corriger avant soumission (conservation du travail).

**AC5** — **Given** le nettoyage des drafts expirés, **When** le worker `domain_events` (Story 10.10) tourne sa passe batch 30 s, **Then** il consomme un handler `prefill_drafts_cleanup` qui supprime les lignes `WHERE expires_at < now()` **And** aucun 2ᵉ worker cron séparé n'est nécessaire.

**AC6** — **Given** l'user complète le formulaire manuel, **When** il revient ensuite au chat, **Then** la conversation continue comme si le tool avait réussi (pas de rupture contexte).

**AC7** — **Given** les tests, **When** `pytest backend/tests/test_graph/test_chat_fallback.py` + `test_core/test_prefill_drafts.py` exécutés, **Then** scénarios (retry échec → fallback UUID, prefill RLS isolé, 404 cross-user, nettoyage TTL expiré, reprise chat) tous verts.

---

### Story 16.6 : Reprise conversation interrompue depuis checkpoint LangGraph MemorySaver

**As a** PME User,
**I want** reprendre une conversation là où je l'ai laissée après fermeture onglet / déconnexion / appareil différent,
**So that** mon travail ESG (facts collectés, verdicts générés, FormalizationPlan progression) ne soit jamais perdu (FR50).

**Metadata (CQ-8)** — `fr_covered`: [FR50] · `nfr_covered`: [NFR30, NFR49] · `phase`: 1 · `cluster`: Copilot · `estimate`: S · `depends_on`: [Story 16.1, LangGraph checkpointer persisté BDD livré]

**Acceptance Criteria**

**AC1** — **Given** un user ferme son onglet pendant une conversation active, **When** il rouvre l'app sur un autre appareil, **Then** la conversation reprend depuis le dernier checkpoint persisté (MemorySaver PostgreSQL) **And** `active_project_id` + `active_module` sont restaurés.

**AC2** — **Given** une conversation > 30 min sans activité, **When** l'user revient, **Then** un récapitulatif automatique des N derniers échanges est injecté dans le contexte (spec 003 pattern `_summarize_previous_conversation`).

**AC3** — **Given** un user supprime explicitement une conversation, **When** confirmé, **Then** l'historique est purgé (NFR21 soft delete + purge différée 30 j).

---
