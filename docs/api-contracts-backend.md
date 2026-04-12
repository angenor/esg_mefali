# Contrats d'API — Backend ESG Mefali

> **Base URL** : `http://localhost:8000/api` (dev) — configurable via `NUXT_PUBLIC_API_BASE` côté frontend
> **OpenAPI** : `http://localhost:8000/docs` (Swagger UI) / `http://localhost:8000/redoc`
> **Auth** : JWT Bearer sur la quasi-totalité des endpoints (sauf `auth/*` et `health`)

## Convention globale

- Toutes les routes sont préfixées par `/api`
- Réponses JSON. Les endpoints de génération de fichiers retournent un `StreamingResponse` (PDF/DOCX)
- Pagination : query params `?page=1&limit=20`, enveloppe `{ items, total, page, limit }`
- Erreurs : `{ detail: "..." }` (FastAPI standard) avec codes HTTP 4xx/5xx
- Dates : ISO 8601 UTC
- Identifiants : UUID v4 en string
- **Nombre total d'endpoints identifiés : ~73**

---

## 1. Auth — `/api/auth`

| Méthode | Chemin | Fonction | Description |
|---|---|---|---|
| GET | `/detect-country` | `detect_country()` | Détecte le pays via IP ; retourne la liste des pays supportés |
| POST | `/register` | `register()` | Crée un compte utilisateur + initialise `CompanyProfile` avec pays auto-détecté |
| POST | `/login` | `login()` | Authentifie ; retourne `access_token` + `refresh_token` JWT |
| POST | `/refresh` | `refresh()` | Renouvelle un `access_token` à partir d'un `refresh_token` valide |
| GET | `/me` | `me()` | Profil de l'utilisateur connecté |

Schemas : `RegisterRequest`, `LoginRequest`, `RefreshRequest`, `TokenResponse`, `UserResponse` (`schemas/auth.py`).

## 2. Chat — `/api/chat`

| Méthode | Chemin | Fonction | Description |
|---|---|---|---|
| POST | `/` | `create_conversation()` | Nouvelle conversation vide |
| GET | `/` | `list_conversations()` | Liste paginée des conversations (filtre `archived`) |
| GET | `/{id}` | `get_conversation()` | Détail conversation + premiers messages |
| PATCH | `/{id}` | `update_conversation()` | Met à jour `title` / `archived` |
| DELETE | `/{id}` | `delete_conversation()` | Suppression (cascade messages + questions interactives) |
| POST | `/{id}/messages` | `send_message()` | Envoie un message (texte + optionnel `file`), déclenche le graphe LangGraph et **streame en SSE** |
| GET | `/{id}/messages` | `list_messages()` | Messages paginés |
| POST | `/interactive-questions/{id}/abandon` | `abandon_question()` | Abandonne une question interactive en attente |
| GET | `/conversations/{id}/interactive-questions` | `list_interactive_questions()` | Liste les questions interactives d'une conversation |

### 2.1 SSE — `POST /api/chat/{id}/messages`

Corps : `multipart/form-data` avec :

- `content` : texte utilisateur (obligatoire)
- `file` : document optionnel (PDF / DOCX / XLSX / image)
- `interactive_question_id`, `interactive_question_answer`, `interactive_question_justification` : réponse à un widget interactif (feature 018)

Réponse : flux SSE `text/event-stream` avec les événements typés :

| Event | Payload | Source |
|---|---|---|
| `token` | `{content: str}` | Chunks de texte assistant |
| `done` | `{message_id, conversation_id}` | Fin de génération |
| `document_upload` | `{document_id, filename, size}` | Upload accepté |
| `document_status` | `{document_id, status}` | Progression analyse |
| `document_analysis` | `{document_id, summary}` | Analyse finalisée |
| `profile_update` | `{field, old_value, new_value}` | Extraction via tool `update_company_profile` |
| `profile_completion` | `{identity, esg, overall}` | Recalcul complétude |
| `tool_call_start` | `{tool_name, args}` | Début appel tool |
| `tool_call_end` | `{tool_name, output}` | Fin appel tool |
| `tool_call_error` | `{tool_name, error}` | Erreur tool |
| `interactive_question` | `{question_id, type, options, question_text}` | Widget interactif injecté |
| `interactive_question_resolved` | `{question_id, state, answer}` | Widget résolu |

Schemas : `ConversationCreate`, `ConversationResponse`, `ConversationUpdate`, `MessageCreate`, `MessageResponse`, `PaginatedResponse` (`schemas/chat.py`).

## 3. Company — `/api/company`

| Méthode | Chemin | Fonction | Description |
|---|---|---|---|
| GET | `/profile` | `get_profile()` | Profil entreprise de l'utilisateur |
| PATCH | `/profile` | `update_profile()` | Mise à jour partielle (secteur, effectifs, CA, localisation) |
| GET | `/profile/completion` | `get_completion()` | Score de complétude (`identity`, `esg`, `overall` en %) |

## 4. Documents — `/api/documents`

| Méthode | Chemin | Fonction | Description |
|---|---|---|---|
| POST | `/` | `upload_document()` | Upload + extraction + génération embeddings pgvector |
| GET | `/` | `list_documents()` | Liste paginée |
| GET | `/{id}` | `get_document()` | Détail + chunks + résumé d'analyse |
| DELETE | `/{id}` | `delete_document()` | Supprime document + chunks vectoriels |
| POST | `/{id}/reanalyze` | `reanalyze()` | Régénère l'analyse LLM |
| GET | `/{id}/preview` | `get_preview()` | Preview PDF (stream binaire) |

## 5. ESG — `/api/esg`

| Méthode | Chemin | Fonction | Description |
|---|---|---|---|
| POST | `/assessments` | `create_assessment()` | Créer une évaluation ESG (secteur obligatoire) |
| GET | `/assessments` | `list_assessments()` | Liste paginée |
| GET | `/assessments/{id}` | `get_assessment()` | Détail (critères, scores) |
| POST | `/assessments/{id}/evaluate` | `evaluate_assessment()` | Mise à jour de l'état et des scores critères |
| GET | `/assessments/{id}/score` | `get_score()` | Score synthétique (E/S/G pondéré par secteur) |
| GET | `/benchmarks/{sector}` | `get_benchmark()` | Benchmark sectoriel |

## 6. Carbon — `/api/carbon`

| Méthode | Chemin | Fonction | Description |
|---|---|---|---|
| POST | `/assessments` | `create_carbon_assessment()` | Créer un assessment (année) |
| GET | `/assessments` | `list_assessments()` | Liste paginée |
| GET | `/assessments/{id}` | `get_assessment()` | Détail + entries |
| POST | `/assessments/{id}/entries` | `add_entries()` | Ajouter N lignes d'émission (calcul tCO2 automatique) |
| GET | `/assessments/{id}/summary` | `get_summary()` | Résumé scope 1/2/3 + objectifs |
| GET | `/benchmarks/{sector}` | `get_benchmark()` | Benchmark sectoriel carbone |

## 7. Financing — `/api/financing`

| Méthode | Chemin | Fonction | Description |
|---|---|---|---|
| GET | `/funds` | `list_funds()` | Liste de fonds avec filtres : `type`, `sector`, `min_amount`, `max_amount`, `access_type` |
| GET | `/funds/{id}` | `get_fund()` | Détail fonds + intermédiaires liés |
| POST | `/funds` | `create_fund()` | Créer un fonds (réservé admin) |
| GET | `/intermediaries` | `list_intermediaries()` | Liste avec filtres `type` / `country` |
| GET | `/intermediaries/nearby` | `list_nearby()` | Intermédiaires géolocalisés (pays utilisateur) |
| GET | `/intermediaries/{id}` | `get_intermediary()` | Détail |
| GET | `/matches` | `list_matches()` | Matches calculés pour l'utilisateur |
| GET | `/matches/{fund_id}` | `get_match()` | Détail d'un match + status |
| PATCH | `/matches/{id}/status` | `update_match()` | Changer le status (`suggested` → `interested` → `preparing` → `applied`) |
| GET | `/matches/{id}/preparation-sheet` | `get_prep_sheet()` | Feuille de préparation PDF |
| PATCH | `/matches/{id}/intermediary` | `update_intermediary()` | Associer un intermédiaire au match |

## 8. Applications — `/api/applications`

| Méthode | Chemin | Fonction | Description |
|---|---|---|---|
| POST | `/` | `create_application()` | Créer un dossier de candidature à un fonds |
| GET | `/` | `list_applications()` | Liste paginée |
| GET | `/{id}` | `get_application()` | Détail + sections |
| PATCH | `/{id}/status` | `update_status()` | Change le status (`draft` → `submitted` → `accepted`) |
| POST | `/{id}/generate-section` | `generate_section()` | Génère une section via LLM |
| PATCH | `/{id}/sections/{key}` | `update_section()` | Mise à jour manuelle d'une section |
| GET | `/{id}/checklist` | `get_checklist()` | Checklist complétude |
| POST | `/{id}/export` | `export_application()` | Export PDF ou DOCX |
| POST | `/{id}/prep-sheet` | `get_prep_sheet()` | Feuille de préparation PDF |
| POST | `/{id}/simulate` | `simulate_financing()` | Simulation financière (montant, durée, taux) |

## 9. Credit — `/api/credit`

| Méthode | Chemin | Fonction | Description |
|---|---|---|---|
| POST | `/generate` | `generate_score()` | Génère un score crédit (LLM + data points collectés) |
| GET | `/score` | `get_score()` | Score crédit actuel |
| GET | `/score/breakdown` | `get_breakdown()` | Détail par catégorie (solvabilité, impact, qualité données, comportement) |
| GET | `/score/history` | `get_history()` | Historique des scores |
| GET | `/score/certificate` | `get_certificate()` | Certificat PDF |

## 10. Action Plan — `/api/action-plan`

| Méthode | Chemin | Fonction | Description |
|---|---|---|---|
| POST | `/generate` | `generate_plan()` | Génère un plan d'action (horizon `6_months` / `12_months` / `24_months`) |
| GET | `/` | `get_plan()` | Plan actuel |
| GET | `/{id}/items` | `get_items()` | Items du plan (filtre `category`) |
| PATCH | `/items/{id}` | `update_item()` | Change le status d'un item |
| POST | `/reminders/` | `create_reminder()` | Crée un rappel |
| GET | `/reminders/upcoming` | `list_reminders()` | Rappels à venir (polling 60s côté frontend) |

## 11. Dashboard — `/api/dashboard`

| Méthode | Chemin | Fonction | Description |
|---|---|---|---|
| GET | `/summary` | `get_summary()` | Vue consolidée : scores ESG/carbone/crédit, matches financement, prochaines actions, badges |

## 12. Reports — `/api/reports`

| Méthode | Chemin | Fonction | Description |
|---|---|---|---|
| GET | `/` | `list_reports()` | Liste paginée |
| GET | `/{id}/download` | `download_report()` | Téléchargement PDF (stream) |

## 13. Health — `/api/health`

| Méthode | Chemin | Description |
|---|---|---|
| GET | `/health` | Status API + BDD |

---

## Authentification — modèle d'appel typique

```http
POST /api/chat/ HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{"title": "Discussion ESG"}
```

Dépendance FastAPI injectée : `Depends(get_current_user)` dans `app/api/deps.py`.

## Codes d'erreur fréquents

| Code | Cas |
|---|---|
| 401 | Token manquant, expiré ou invalide |
| 403 | Ressource appartenant à un autre utilisateur |
| 404 | ID inexistant |
| 409 | Contrainte unique (ex. `CarbonAssessment(user_id, year)`) |
| 422 | Validation Pydantic échouée |
| 429 | (À prévoir) rate limiting |
| 500 | Erreur serveur non gérée |

## À surveiller / TODO API

- **CORS** : actuellement en dur sur `localhost:3000` (voir `main.py`) — à externaliser via env `CORS_ORIGINS`
- **Rate limiting** : absent, à implémenter (slowapi / middleware)
- **Pagination** : format à standardiser entre tous les routers (certains exposent encore la liste brute)
- **Versioning** : aucune `/v1/` — à envisager avant une première API publique
- **OpenAPI security scheme** : `Depends(get_current_user)` couvre l'auth, mais Swagger pourrait afficher le bouton 'Authorize' via `security=[{"bearerAuth": []}]`
