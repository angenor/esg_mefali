# Data Model: Intégration Tool Calling LangGraph

**Branch**: `012-langgraph-tool-calling` | **Date**: 2026-04-01

## Entités modifiées

### ConversationState (TypedDict existant — à étendre)

**Fichier** : `backend/app/graph/state.py`

Ajouts :
- `user_id: str | None` — ID utilisateur injecté depuis le handler HTTP (actuellement accédé via `state.get("user_id")` mais non déclaré)
- `db_session_id: str | None` — Identifiant de la session DB pour le traçage (optionnel)

Pas de nouveaux champs de routing : les `_route_*` existants suffisent.

---

## Entités nouvelles

### ToolCallLog (nouveau modèle — pour FR-022 journalisation)

**Table** : `tool_call_logs`

| Champ | Type | Contraintes |
|-------|------|-------------|
| id | UUID | PK, auto-généré |
| user_id | UUID | FK → users.id, NOT NULL |
| conversation_id | UUID | FK → conversations.id, nullable |
| node_name | VARCHAR(100) | NOT NULL — ex: "esg_scoring_node" |
| tool_name | VARCHAR(100) | NOT NULL — ex: "save_esg_criterion_score" |
| tool_args | JSONB | NOT NULL — paramètres d'entrée |
| tool_result | JSONB | nullable — résultat complet |
| duration_ms | INTEGER | nullable — durée en millisecondes |
| status | VARCHAR(20) | NOT NULL — "success", "error", "retry_success" |
| error_message | TEXT | nullable — message d'erreur si échec |
| retry_count | INTEGER | NOT NULL, default 0 |
| created_at | TIMESTAMP | NOT NULL, default now() |

**Index** : `(user_id, created_at DESC)`, `(conversation_id)`, `(tool_name, status)`

---

## Entités existantes inchangées

Les modèles métier existants ne sont PAS modifiés. Le tool calling ajoute une couche d'appel entre le LLM et les services, mais les services et modèles restent identiques :

- `CompanyProfile` — inchangé
- `ESGAssessment` — inchangé
- `CarbonAssessment` + `CarbonEntry` — inchangés
- `Fund`, `FundMatch`, `Intermediary` — inchangés
- `FundApplication` — inchangé
- `CreditScore` — inchangé
- `Document`, `DocumentAnalysis` — inchangés
- `ActionPlan`, `ActionItem`, `Reminder` — inchangés

---

## Relations

```
ToolCallLog ──(N:1)──> User
ToolCallLog ──(N:1)──> Conversation (nullable)
```

Les tools appellent les services qui opèrent sur les entités existantes. Pas de nouvelle relation entre entités métier.

---

## Transitions d'état

### Tool Call Lifecycle

```
LLM génère tool_call → tool_call_start (SSE)
  → Exécution du tool
    → Succès → tool_call_end (SSE) → log status="success"
    → Échec → Retry automatique (1x)
      → Succès → tool_call_end (SSE) → log status="retry_success"
      → Échec → tool_call_error (SSE) → log status="error"
  → Retour au LLM avec ToolMessage
```

### Confirmation Flow (finalisations)

```
LLM veut finaliser → Réponse texte demandant confirmation
  → Utilisateur confirme → LLM appelle le tool de finalisation
  → Utilisateur refuse → LLM continue normalement
```
