# Contrats d'API — Backend ESG Mefali

> **Base URL** : `http://localhost:8000/api` (dev) — configurable via `NUXT_PUBLIC_API_BASE` côté frontend
> **Authentification** : JWT HS256 Bearer token dans l'header `Authorization`
> **Format** : JSON (sauf upload multipart + SSE)
> **OpenAPI** : auto-généré sur `http://localhost:8000/docs` (Swagger) et `/redoc`
> **Total endpoints** : 73 répartis sur 13 routers

## Conventions

- **Identifiants** : UUID string.
- **Timestamps** : ISO 8601 UTC (`2026-04-16T12:00:00Z`).
- **Pagination** : query params `page` (1-based) + `page_size`.
- **Réponses standard** : `200 OK` pour GET/PATCH, `201 Created` pour POST, `204 No Content` pour DELETE, `400/401/403/404/422/500` pour les erreurs.
- **Champ erreur** : `{detail: string | object}` (format FastAPI standard).

---

## 1. Auth — `/api/auth` (5 endpoints)

[backend/app/api/auth.py](../backend/app/api/auth.py)

### `GET /api/auth/detect-country`
Retourne le pays détecté via IP + la liste des pays supportés.

**200** :
```json
{ "country_code": "SN", "country_name": "Sénégal", "supported_countries": [{"code": "SN", "name": "Sénégal"}, …] }
```

### `POST /api/auth/register`
```json
// Request
{ "email": "user@ex.com", "password": "…", "full_name": "Aminata Diop", "company_name": "Solar SARL" }
// 201 Created
{ "id": "uuid", "email": "user@ex.com", "full_name": "Aminata Diop", "company_name": "Solar SARL" }
```

### `POST /api/auth/login`
```json
// Request
{ "email": "user@ex.com", "password": "…" }
// 200
{ "access_token": "eyJ…", "refresh_token": "eyJ…", "token_type": "bearer", "expires_in": 3600 }
```

### `POST /api/auth/refresh`
```json
// Request
{ "refresh_token": "eyJ…" }
// 200
{ "access_token": "eyJ…", "token_type": "bearer", "expires_in": 3600 }
```

### `GET /api/auth/me` 🔒
```json
{ "id": "uuid", "email": "…", "full_name": "…", "company_name": "…" }
```

---

## 2. Chat — `/api/chat` (9 endpoints)

[backend/app/api/chat.py](../backend/app/api/chat.py)

### `POST /api/chat/conversations` 🔒
```json
// Request
{ "title": "Bilan carbone Q1", "previous_conversation_id": "uuid?" }
// 201 — résume la conversation précédente si présente
{ "id": "uuid", "user_id": "uuid", "title": "…", "thread_id": "…", "created_at": "…" }
```

### `GET /api/chat/conversations` 🔒
Query : `page`, `page_size` (défaut 20). Tri décroissant sur `updated_at`.

```json
{ "items": [ {…} ], "total": 42, "page": 1, "page_size": 20 }
```

### `PATCH /api/chat/conversations/{conversation_id}` 🔒
```json
// Request
{ "title": "Nouveau titre" }
// 200 — ConversationResponse
```

### `DELETE /api/chat/conversations/{conversation_id}` 🔒
**204 No Content**.

### `GET /api/chat/conversations/{conversation_id}/messages` 🔒
Query : `page`, `page_size`. Renvoie messages chronologiques.

### `POST /api/chat/conversations/{conversation_id}/messages` 🔒 — **SSE streaming**
Content-Type : `multipart/form-data`.

| Champ form | Type | Obligatoire |
|---|---|---|
| `content` | str | ✅ |
| `document_upload` | file (PDF / DOCX / XLSX) | ❌ |
| `document_analysis_summary` | str | ❌ |
| `interactive_question_id` | str (uuid) | ❌ (si réponse à widget, spec 018) |
| `widget_response` | JSON str | ❌ (`{"values": [...], "justification": "..."}`) |
| `current_page` | str | ❌ (spec 3 — ex. `carbon/results`) |
| `guidance_stats` | JSON str | ❌ (spec 019 — `{refusal_count, acceptance_count}`) |

**Réponse** : `text/event-stream`. Voir [integration-architecture.md#4-streaming-sse-chat-ia](./integration-architecture.md#4-streaming-sse-chat-ia) pour la liste des events.

Format d'une ligne SSE :
```
data: {"type": "token", "content": "Bonjour"}\n\n
```

### `POST /api/chat/conversations/{conversation_id}/messages/json` 🔒
Variante JSON (sans upload). Utile pour des clients non multipart.

```json
{ "content": "…", "interactive_question_id": "uuid?", "widget_response": {…}, "current_page": "…" }
```

### `POST /api/chat/interactive-questions/{question_id}/abandon` 🔒
Marque la question comme abandonnée (spec 018, bouton "Répondre autrement").

**200** :
```json
{ "id": "uuid", "state": "abandoned", "answered_at": "…" }
```

### `GET /api/chat/conversations/{conversation_id}/interactive-questions` 🔒
Liste les questions interactives liées à la conversation (actives + historiques).

```json
{ "items": [ {"id": "…", "state": "pending|answered|abandoned|expired", …} ] }
```

---

## 3. Company — `/api/company` (3 endpoints) 🔒

[backend/app/modules/company/router.py](../backend/app/modules/company/router.py)

- `GET /api/company/profile` — `CompanyProfile`
- `PATCH /api/company/profile` — partial update (tous champs optionnels)
- `GET /api/company/profile/completion` — `{percentage: float, missing_fields: [str]}`

---

## 4. Documents — `/api/documents` (6 endpoints) 🔒

[backend/app/modules/documents/router.py](../backend/app/modules/documents/router.py)

- `POST /api/documents/upload` — multipart : `file`. Retourne `Document` en statut `processing`.
- `GET /api/documents/` — liste paginée.
- `GET /api/documents/{document_id}` — détail + `analysis`.
- `DELETE /api/documents/{document_id}` — suppression (soft delete via `status` ou hard selon le flag).
- `POST /api/documents/{document_id}/reanalyze` — relance l'analyse.
- `GET /api/documents/{document_id}/preview` — redirige vers le fichier (auth via JWT).

---

## 5. ESG — `/api/esg` (6 endpoints) 🔒

[backend/app/modules/esg/router.py](../backend/app/modules/esg/router.py)

- `POST /api/esg/assessments` — crée un draft (`conversation_id` optionnel).
- `GET /api/esg/assessments` — liste paginée.
- `GET /api/esg/assessments/{assessment_id}` — détail.
- `POST /api/esg/assessments/{assessment_id}/evaluate` — calcule `overall_score`.
- `GET /api/esg/assessments/{assessment_id}/score` — score détaillé par critère.
- `GET /api/esg/benchmarks/{sector}` — benchmark sectoriel pour comparaison.

---

## 6. Carbon — `/api/carbon` (6 endpoints) 🔒

[backend/app/modules/carbon/router.py](../backend/app/modules/carbon/router.py)

- `POST /api/carbon/assessments` — crée un bilan (unique par `year`).
- `GET /api/carbon/assessments`
- `GET /api/carbon/assessments/{assessment_id}`
- `POST /api/carbon/assessments/{assessment_id}/entries` — batch d'entrées (cat/valeur/unité).
- `GET /api/carbon/assessments/{assessment_id}/summary` — `tco2e` total + plan de réduction.
- `GET /api/carbon/benchmarks/{sector}`

---

## 7. Financing — `/api/financing` (10 endpoints) 🔒

[backend/app/modules/financing/router.py](../backend/app/modules/financing/router.py)

- `GET /api/financing/funds` — catalogue paginé, filtres `country`, `sector`, `min_amount`, `max_amount`, `access_type`.
- `GET /api/financing/funds/{fund_id}` — fiche fonds complète + intermédiaires liés.
- `POST /api/financing/funds` — (admin) création.
- `GET /api/financing/intermediaries` — annuaire paginé, filtres `type`, `country`.
- `GET /api/financing/intermediaries/nearby` — tri par proximité (requête géoloc optionnelle).
- `GET /api/financing/intermediaries/{intermediary_id}` — détail.
- `GET /api/financing/matches` — matches du user, paginés.
- `GET /api/financing/matches/{fund_id}` — détail du scoring pour un fonds donné.
- `PATCH /api/financing/matches/{match_id}/status` — change `matched` → `applied`/`shortlisted`/`rejected`.
- `GET /api/financing/matches/{match_id}/preparation-sheet` — génère une fiche PDF de préparation.

---

## 8. Applications — `/api/applications` (9 endpoints) 🔒

[backend/app/modules/applications/router.py](../backend/app/modules/applications/router.py)

- `POST /api/applications/` — création (appelée via le tool `create_fund_application` depuis le chat, spec 015).
- `GET /api/applications/`
- `GET /api/applications/{application_id}`
- `PATCH /api/applications/{application_id}/status`
- `POST /api/applications/{application_id}/generate-section` — `{section_key}` → appelle LLM pour rédiger.
- `PATCH /api/applications/{application_id}/sections/{section_key}` — édition manuelle.
- `GET /api/applications/{application_id}/checklist` — progression par section.
- `POST /api/applications/{application_id}/export` — export PDF/DOCX (WeasyPrint / python-docx).
- `POST /api/applications/{application_id}/prep-sheet` — génération fiche de préparation (résumé + to-do avant envoi).

---

## 9. Credit — `/api/credit` (5 endpoints) 🔒

[backend/app/modules/credit/router.py](../backend/app/modules/credit/router.py)

- `POST /api/credit/generate` — calcule le score (via chat ou direct).
- `GET /api/credit/score` — dernier score valide.
- `GET /api/credit/score/breakdown` — détail des facteurs.
- `GET /api/credit/score/history` — série temporelle.
- `GET /api/credit/score/certificate` — PDF WeasyPrint.

---

## 10. Reports — `/api/reports` (4 endpoints) 🔒

[backend/app/modules/reports/router.py](../backend/app/modules/reports/router.py)

- `POST /api/reports/esg/{assessment_id}/generate` — lance la génération (retourne un `report_id` en statut `generating`).
- `GET /api/reports/{report_id}/status` — polling (`generating` / `ready` / `error`).
- `GET /api/reports/{report_id}/download` — retourne le PDF.
- `GET /api/reports/` — liste paginée des rapports du user.

---

## 11. Action Plan — `/api/action-plan` (6 endpoints) 🔒

[backend/app/modules/action_plan/router.py](../backend/app/modules/action_plan/router.py)

- `POST /api/action-plan/generate` — génère un plan basé sur `assessment_id`.
- `GET /api/action-plan/` — plan actif.
- `GET /api/action-plan/{plan_id}/items` — items paginés avec filtres (`category`, `status`, `priority`).
- `PATCH /api/action-plan/items/{item_id}` — update (priority, status, completion_pct).
- `POST /api/action-plan/reminders/` — crée un rappel pour un item.
- `GET /api/action-plan/reminders/upcoming` — rappels à venir (7 jours).

---

## 12. Dashboard — `/api/dashboard` (1 endpoint) 🔒

[backend/app/modules/dashboard/router.py](../backend/app/modules/dashboard/router.py)

- `GET /api/dashboard/summary` — agrégat : score ESG courant, `tco2e` total, score crédit, nombre de matches, dossiers en cours.

---

## 13. Health — `/api/health` (1 endpoint)

[backend/app/api/health.py](../backend/app/api/health.py)

```json
// 200
{ "status": "ok", "database": "connected", "version": "0.1.0" }
```

---

## Codes d'erreur standard

| Code | Signification | Cas typique |
|---|---|---|
| 400 | Bad Request | Payload malformé |
| 401 | Unauthorized | Token absent / invalide / expiré |
| 403 | Forbidden | Pas d'accès à la ressource |
| 404 | Not Found | Resource inexistante |
| 409 | Conflict | Contrainte unique violée (ex. email déjà utilisé, bilan carbone déjà existant pour l'année) |
| 422 | Unprocessable Entity | Erreur de validation Pydantic |
| 500 | Internal Server Error | Bug ; consulter les logs |

## Limites techniques

- **Rate limiting** : ❌ absent à ce jour.
- **Taille upload** : 50 Mo (limite nginx prod).
- **Timeout SSE** : 600 s (nginx) — suffisant pour les conversations LLM longues.
- **Timeout LLM** : `request_timeout=60 s` explicitement configuré dans `get_llm()` (spec 015).
- **CORS** : uniquement `http://localhost:3000` configuré (à élargir).

## Champ `🔒`

Indique un endpoint nécessitant un `Authorization: Bearer <access_token>` valide. L'absence du token retourne `401 Unauthorized` avec le header `WWW-Authenticate: Bearer`.
