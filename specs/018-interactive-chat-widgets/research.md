# Phase 0 — Research : Widgets interactifs pour les questions de l'assistant IA

**Feature** : `018-interactive-chat-widgets`
**Date** : 2026-04-11
**Statut** : Complet

Ce document consolide les décisions techniques prises avant la conception détaillée. Les options rejetées sont conservées en « Alternatives considered » pour garantir la traçabilité.

Toutes les décisions s'alignent sur les clarifications enregistrées en session (spec.md § Clarifications) :

- Q1 : LLM génère le widget à la volée via un tool dédié `ask_interactive_question`.
- Q2 : La réponse widget alimente à la fois le message texte (continuité) et un payload structuré (`active_module_data`) consommé directement par les tools.
- Q3 : Bouton explicite « Répondre autrement » qui désactive le widget et ouvre la saisie libre.
- Q4 : Widget non répondu → expiré à la reprise, le noeud régénère une nouvelle question.
- Q5 : Justification plafonnée à 400 caractères.

---

## R1. Mécanisme de transport widget → frontend

**Décision** : Double canal — (a) le LLM appelle le tool `ask_interactive_question`, qui renvoie un payload JSON consolidé côté backend ; (b) le handler SSE `stream_graph_events` de [backend/app/api/chat.py](backend/app/api/chat.py#L82) détecte `on_tool_end` pour ce tool, persiste une ligne `interactive_questions` (id UUID générée serveur), et émet un nouvel événement SSE `interactive_question` avec le payload complet ; (c) le LLM est instruit d'inclure dans sa réponse textuelle un bloc fenced `\`\`\`interactive_question\nquestion_id: <uuid>\n\`\`\`` pour marquer l'emplacement du widget dans le message.

**Rationale** :
- Réutilise exactement le pipeline `astream_events(version="v2")` déjà en place pour `tool_call_start` / `tool_call_end` / `profile_update` (chat.py:141-213). Aucun nouveau canal à créer.
- Le marqueur fenced `interactive_question` s'intègre naturellement dans le parser existant [useMessageParser.ts](frontend/app/composables/useMessageParser.ts) qui scanne déjà `\`\`\`(\w+)` pour `chart, mermaid, table, gauge, progress, timeline`. Ajout d'un 7ᵉ type sans refondre la tuyauterie.
- La persistance serveur garantit SC-007 (widget toujours rendu à la reprise).
- Le payload ne traverse pas le canal token stream (il passerait dans le contenu du message comme JSON) ce qui éviterait le parsing partiel lors du streaming.

**Alternatives considérées** :
- **Embed JSON dans le texte** : le tool retourne le JSON complet, embarqué dans `\`\`\`interactive_question\n{...}\n\`\`\``. Rejeté : streaming de JSON partiel → rendus cassés visibles à l'utilisateur + pas de source de vérité côté DB pour la reprise.
- **WebSocket dédié** : canal temps réel séparé pour les widgets. Rejeté : contraint le choix de transport (SSE vs WS), ajoute une connexion à gérer, redondant avec l'astream_events en place.

---

## R2. Persistance des questions interactives

**Décision** : Nouvelle table `interactive_questions` + 0 changement à la table `messages`. Deux foreign keys nullables vers `messages.id` :

- `assistant_message_id` : FK vers le message assistant qui porte la question (rempli quand le message est sauvé à la fin du streaming SSE, dans le bloc `generate_sse` de [chat.py](backend/app/api/chat.py#L561-L657)).
- `response_message_id` : FK vers le message utilisateur qui porte la réponse (rempli lors de l'envoi du message de réponse).

**Rationale** :
- Le modèle `Message` actuel est minimal (role, content, created_at, sans JSON metadata). Ajouter une colonne JSONB impacterait toutes les queries et forcerait une migration plus large. Une table satellite respecte le principe YAGNI de la constitution (§ VII).
- Le join `messages LEFT JOIN interactive_questions ON assistant_message_id OR response_message_id` au moment du `GET /messages` attache proprement la question à son message assistant ET/OU la réponse à son message utilisateur, sans duplication.
- Permet de stocker la state machine (`pending → answered | abandoned | expired`) sans polluer messages.

**Alternatives considérées** :
- **Colonne JSONB `metadata` sur messages** : plus simple mais force à ré-interroger chaque message pour détecter la présence d'une question, et rend les mises à jour d'état (expiration au rechargement) plus lourdes (UPDATE sur messages).
- **Deux tables séparées** (`interactive_questions` + `interactive_responses`) : sur-normalisation, la relation 1-1 est stricte (une question a au plus une réponse canonique).

---

## R3. Structure du tool `ask_interactive_question`

**Décision** : Créer `backend/app/graph/tools/interaction_tools.py` exposant un tool `@tool` unique avec la signature suivante (Pydantic-typed args via `StructuredTool` / schéma LangChain) :

```python
@tool
async def ask_interactive_question(
    question_type: Literal["qcu", "qcm", "qcu_justification", "qcm_justification"],
    prompt: str,
    options: list[dict],  # [{"value": "pme", "label": "PME (50-250 salariés)", "description": null}]
    min_selections: int,
    max_selections: int,
    requires_justification: bool,
    justification_prompt: str | None,
    config: RunnableConfig,
) -> str:
```

Le tool :
1. Valide les contraintes (min/max cohérents, options ≥ 2, libellés non vides, prompt ≥ 10 caractères, ≤ 15 options, justification_prompt obligatoire si `requires_justification=True`).
2. Persiste une ligne `interactive_questions` (state=`pending`, assistant_message_id=NULL).
3. Injecte `<!--SSE:{"__sse_interactive_question__": true, "question_id": "...", "payload": {...}}-->` dans sa valeur de retour, détecté par `stream_graph_events` comme c'est déjà fait pour `__sse_profile__` (chat.py:188-201).
4. Retourne au LLM une instruction concise : `Widget créé (id=...). Incorpore \`\`\`interactive_question\nquestion_id: ...\n\`\`\` dans ta réponse pour l'afficher.`

**Rationale** :
- Un seul tool suffit (le 4 types de widget diffèrent par la config, pas par la logique). Réduit la surface d'apprentissage pour le LLM.
- Réutilise le marqueur `<!--SSE:...-->` déjà présent dans les tools profiling (pattern éprouvé feature 012).
- L'appel tool n'affecte pas `active_module_data` au moment de la création (seule la persistance DB compte) → pas de conflit avec les autres tools du même noeud.

**Alternatives considérées** :
- **4 tools séparés** (`ask_single_choice`, `ask_multiple_choice`, …) : dilue le contexte du LLM, multiplie la logique de validation. Rejeté.
- **StructuredOutput via `with_structured_output`** au lieu d'un tool : rejeté car incompatible avec le pattern `bind_tools` déjà utilisé dans les 9 noeuds + interdit le mix widget + autres tools dans un même tour (cf. feature 015).

---

## R4. Consommation de la réponse widget par les tools métier

**Décision** : Le flux de réponse utilise la route existante `POST /api/chat/conversations/{cid}/messages` augmentée d'un champ multipart/form optionnel `interactive_question_id`. Le handler `send_message` (chat.py:483-693) :

1. Valide que la question appartient à la conversation et qu'elle est `pending`.
2. Charge son payload depuis la DB, reconstruit un contenu texte lisible (ex. `Électricité nationale, Solaire` ou `PME — Parce qu'on grandit 🙂`) et crée le message user normal (content=résumé humain).
3. Met à jour `interactive_questions` : state=`answered`, `response_values`, `response_justification`, `response_message_id=<id>`, `answered_at=NOW()`.
4. Construit l'`initial_state` pour LangGraph avec une clé supplémentaire dans `active_module_data` :

```python
active_module_data = {
    ...existing fields...,
    "widget_response": {
        "question_id": str(qid),
        "question_type": "qcm",
        "values": ["electricite_nationale", "solaire"],
        "justification": None,
    },
}
```

5. Chaque noeud spécialiste, dès qu'il lit `active_module_data.widget_response` non nul, est instruit par son prompt (section « TOOL CALL OBLIGATOIRE ») d'appeler directement le tool approprié (`batch_save_esg_criteria`, `save_carbon_entry`, `update_company_profile`, etc.) avec les valeurs structurées, **sans re-parser le message texte**. Après usage, le noeud nettoie `widget_response` de son `active_module_data` retourné pour éviter une double application.

**Rationale** :
- Aligné sur la décision Q2 de la spec.
- Zero nouveau endpoint : on augmente l'existant avec un champ optionnel, compatible avec les clients actuels.
- Le nettoyage de `widget_response` après consommation évite les re-applications en cas de retry / re-run du graphe.
- Le message texte reste la source secondaire pour les features downstream (résumé de conversation, titre auto, mémoire contextuelle) qui ne connaissent pas le payload structuré.

**Alternatives considérées** :
- **Endpoint dédié `POST /interactive-questions/{qid}/answer`** : duplique la logique de création de message + SSE streaming. Rejeté pour conservation du point d'entrée unique.
- **Colonne JSON sur messages (`metadata`)** : rejeté en R2.

---

## R5. Modification des prompts des 7 noeuds concernés

**Décision** : Ajouter une section commune `### OUTIL WIDGET INTERACTIF` dans les prompts suivants :

- [backend/app/prompts/profiling.py](backend/app/prompts/profiling.py)
- [backend/app/prompts/esg_scoring.py](backend/app/prompts/esg_scoring.py)
- [backend/app/prompts/carbon.py](backend/app/prompts/carbon.py)
- [backend/app/prompts/credit.py](backend/app/prompts/credit.py)
- [backend/app/prompts/financing.py](backend/app/prompts/financing.py)
- [backend/app/prompts/application.py](backend/app/prompts/application.py)
- [backend/app/prompts/action_plan.py](backend/app/prompts/action_plan.py)

La section commune (extraite dans `backend/app/prompts/widget.py` pour réutilisation) explique :
1. Quand widgetiser (questions fermées avec options dénombrables ≤ 15, où la valeur est discrète et non libre).
2. Quand NE PAS widgetiser (questions nécessitant du texte libre : nom, description, chiffres précis, dates).
3. Comment appeler `ask_interactive_question` (exemple QCU + exemple QCM + exemple avec justification amusante).
4. Comment placer le marqueur `interactive_question` dans la réponse.
5. Comment gérer la réponse à l'étape suivante (lire `active_module_data.widget_response` et appeler directement le tool métier).

**Rationale** :
- Factorisation évite le drift entre modules.
- La section est appendée à chaque `full_prompt` du noeud (pattern déjà en place pour `STYLE_INSTRUCTION` feature 014).

**Alternatives considérées** :
- **Prompt global unique** : rejeté car la logique « quand widgetiser » diffère par module (un questionnaire ESG a 80% de questions fermées, le chat général quasiment zéro).
- **Exemples few-shot dans l'historique** : rejeté (coût tokens).

---

## R6. Cycle de vie : pending → answered | abandoned | expired

**Décision** : State machine implémentée côté backend uniquement, avec 4 transitions :

| Transition | Déclencheur | Action |
|---|---|---|
| pending → answered | `POST /messages` avec `interactive_question_id` | Valide contraintes, persiste réponse, active_module_data.widget_response |
| pending → abandoned | `POST /interactive-questions/{qid}/abandon` (appelé par le front sur click « Répondre autrement ») | Met à jour state=`abandoned`, `answered_at=NOW()`. La zone de saisie libre devient active côté UI. |
| pending → expired | Détection à la reprise d'un module (noeud spécialiste) : si `active_module_data.last_widget_id` référence une question `pending` et que le dernier message est un message user libre non lié, marquer `expired` + poser une nouvelle question via tool. |
| any → n/a | — | Les états terminaux sont immuables (pas de `replay`, pas de « répondre à nouveau »). |

**Endpoint dédié** : `POST /api/chat/interactive-questions/{question_id}/abandon` (1 seul route new, ownership-guarded par `conversation.user_id`). Retourne 204 sans corps.

**Détection expiration à la reprise** : chaque noeud spécialiste, à son entrée, appelle un helper `get_pending_widget(conversation_id, module)` qui :

- Retourne la dernière `interactive_questions` row `state=pending` pour ce module.
- Si elle est antérieure au dernier message user non widgeté → la marque `expired` et l'inclut dans `state.expired_widgets` pour informer le LLM (prompt : « une question précédente a expiré, repose-la de manière adaptée »).

**Rationale** :
- Les 4 états couvrent tous les edge cases listés dans spec.md § Edge Cases.
- Pas de cron/job — tout est déclenché au moment de l'accès utilisateur.

**Alternatives considérées** :
- **Expiration par TTL (24h)** : rejeté en Q4 (option C de la clarification).
- **Garder pending cliquable indéfiniment** : rejeté en Q4 (option B).

---

## R7. Rendu frontend & accessibilité

**Décision** : Architecture de composants :

```
components/
├── chat/
│   ├── ChatMessage.vue                    # Rendu de la bulle, embarque InteractiveQuestionHost si message.interactive_question
│   ├── MessageParser.vue                  # +1 branche v-else-if segment.type === 'interactive_question'
│   └── widgets/
│       ├── InteractiveQuestionHost.vue    # Dispatcher : résout question_type → composant concret, gère l'état (pending/answered/abandoned/expired)
│       ├── SingleChoiceWidget.vue         # QCU : <ul role="radiogroup"> + clic = envoi immédiat
│       ├── MultipleChoiceWidget.vue       # QCM : <ul role="group"> checkboxes + bouton Valider
│       ├── JustificationField.vue         # Textarea 400 max, compteur, placeholder ton amusant
│       └── AnswerElsewhereButton.vue      # Bouton « Répondre autrement » partagé
```

**Accessibilité** (FR-012, SC-005) :

- `role="radiogroup"` + `aria-labelledby=prompt-id` pour QCU.
- `role="group"` + libellés `<label>` associés aux `<input type="checkbox">` pour QCM.
- Navigation clavier : Tab entre les options, Espace/Entrée pour activer, flèches haut/bas pour parcourir un radiogroup.
- `aria-disabled="true"` dans les états answered/abandoned/expired + visuellement grisé (`opacity-60 cursor-not-allowed`).
- Textarea justification : `maxlength="400"` + compteur live `aria-live="polite"`.
- Messages d'erreur (« Sélectionnez au moins une option ») : `aria-live="assertive"`.

**Dark mode** (FR-011) : utilisation des tokens existants `dark:bg-dark-card`, `dark:text-surface-dark-text`, `dark:border-dark-border`, `dark:hover:bg-dark-hover`, `dark:bg-dark-input` (cf. CLAUDE.md § Dark Mode).

**Fallback client ancien** (FR-013) : le block `\`\`\`interactive_question\nquestion_id: …\n\`\`\`` est un code fenced — un client ne connaissant pas ce type tombe dans la branche `segment.type === 'text'` et affiche le code brut, ce qui préserve au minimum la lisibilité. L'énoncé du widget est aussi inclus dans le texte libre de l'assistant qui précède le marqueur (le prompt force le LLM à poser la question en clair avant d'insérer le marqueur).

**Alternatives considérées** :
- **Un seul composant monolithique** : rejeté car les 4 interactions diffèrent trop (envoi immédiat vs validation groupée).
- **Rendu en dehors de MessageParser** : considéré puis retenu : `MessageParser` gère la détection via fenced block, `ChatMessage` monte `InteractiveQuestionHost` ; c'est une coopération (le parser détecte la position, le host prend le relais avec la payload reçue via SSE ou rehydratée via API).

---

## R8. Validation des contraintes côté back & front

**Décision** :

- **Backend** (source de vérité, SC-004) : Pydantic schema `InteractiveQuestionAnswer` :
  - `question_id: UUID`
  - `values: list[str]` avec validators `min_length = question.min_selections`, `max_length = question.max_selections`, chaque value ∈ `{o["value"] for o in question.options}`.
  - `justification: Optional[str]` avec `max_length=400`, obligatoire si `question.requires_justification`.
  - Retour HTTP 422 avec détail si violation.
- **Frontend** : validation optimiste avant soumission (compteur, désactivation du bouton Valider tant que la sélection n'est pas valide, `aria-live` pour les retours).
- **Troncation backend de sécurité** : si un client contourne le `maxlength=400`, le backend tronque silencieusement à 400 caractères et ajoute un log warning.

**Rationale** : défense en profondeur, cohérent avec le principe V (Sécurité, validation aux frontières).

---

## R9. Tests & couverture (TDD obligatoire — constitution § IV)

**Décision** : objectif 80% sur le nouveau code (min 25 nouveaux tests).

- **Backend (pytest)**
  - `tests/test_interaction_tool.py` : validations du tool `ask_interactive_question` (happy path, chaque type, contraintes violées, payload SSE bien émis).
  - `tests/test_interactive_questions_api.py` : `POST /messages` avec `interactive_question_id` (answered), `POST /interactive-questions/{id}/abandon`, `GET /messages` rehydrate la question.
  - `tests/test_interactive_question_lifecycle.py` : transitions pending→answered/abandoned/expired, reprise de module avec widget expiré régénéré.
  - `tests/graph/test_esg_widget_integration.py` : noeud esg_scoring consomme `active_module_data.widget_response` et appelle `batch_save_esg_criteria` sans re-parsing.
  - `tests/graph/test_carbon_widget_integration.py` : idem carbon_node.
- **Frontend (vitest + @nuxt/test-utils)**
  - `tests/components/SingleChoiceWidget.test.ts` : clic = émet `answer` avec les bonnes valeurs.
  - `tests/components/MultipleChoiceWidget.test.ts` : sélection + validation + bornes min/max.
  - `tests/components/JustificationField.test.ts` : compteur 400, troncation, placeholder.
  - `tests/components/InteractiveQuestionHost.test.ts` : dispatch des types, état disabled.
  - `tests/composables/useChat.test.ts` : SSE `interactive_question` stocke le payload ; `answerInteractiveQuestion()` POST correct.
  - `tests/components/MessageParser.test.ts` : ajout branche `interactive_question`.
- **E2E Playwright** (critique pour SC-003)
  - `tests/e2e/esg-widget.spec.ts` : parcours ESG avec au moins 3 widgets répondus → score généré.

**Alternatives considérées** :
- Tests uniquement unitaires : rejeté, ne valide pas l'intégration SSE/DB.

---

## R10. Migration Alembic

**Décision** : Une seule migration :

```
backend/alembic/versions/xxxx_add_interactive_questions_table.py
```

Upgrade : `CREATE TABLE interactive_questions (...)` + index sur `(conversation_id, state)`, `(assistant_message_id)`, `(response_message_id)`.
Downgrade : `DROP TABLE interactive_questions`.

Aucun alter sur `messages` ni `conversations`. Migration purement additive, rollback sans risque.

---

## R11. Limites explicites & non-objectifs

- **Pas de support extension Chrome** v1 (hypothèse spec.md).
- **Pas de support PDF export** v1 (hypothèse spec.md).
- **Pas de widgets > 15 options** (hypothèse spec.md, validation backend bloque).
- **Pas de re-réponse** : un widget answered/abandoned/expired est immuable.
- **Pas de multi-questions parallèles** : le LLM n'est pas supposé poser 2 widgets dans un même tour. Le prompt l'interdit explicitement ; si détecté (via `get_pending_widget` retourne ≥ 2), seul le plus récent reste `pending`, les autres passent à `expired`.

---

## Résumé des Nouveaux Artéfacts

| Type | Chemin | Statut |
|---|---|---|
| Modèle | `backend/app/models/interactive_question.py` | À créer |
| Schéma Pydantic | `backend/app/schemas/interactive_question.py` | À créer |
| Tool LangChain | `backend/app/graph/tools/interaction_tools.py` | À créer |
| Prompt helper | `backend/app/prompts/widget.py` | À créer |
| Migration Alembic | `backend/alembic/versions/xxxx_add_interactive_questions_table.py` | À créer |
| Router (ajout) | `backend/app/api/chat.py` (nouveau endpoint abandon, champ form sur `send_message`) | À modifier |
| Graph nodes (6) | `backend/app/graph/nodes.py` | À modifier |
| State | `backend/app/graph/state.py` (ajout champ `expired_widgets`) | À modifier |
| Prompts (7) | `backend/app/prompts/{profiling,esg_scoring,carbon,credit,financing,application,action_plan}.py` | À modifier |
| Composants Vue (5) | `frontend/app/components/chat/widgets/*.vue` + `ChatMessage.vue` + `MessageParser.vue` | À créer/modifier |
| Composable | `frontend/app/composables/useChat.ts` | À modifier |
| Parser | `frontend/app/composables/useMessageParser.ts` | À modifier (ajout type `interactive_question`) |
| Types TS | `frontend/app/types/interactive-question.ts` + extension `Message` | À créer/modifier |
| Tests | Voir R9 | À créer |

---

**NEEDS CLARIFICATION résiduels : 0.**
