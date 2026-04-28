---
title: 'BUG-V2-001 + BUG-V2-002 — Chinois MiniMax + message vide post-widget'
type: 'bugfix'
created: '2026-04-23'
status: 'done'
route: 'plan-code-review'
baseline_commit: '54559d77ee2a65cc56a8bdb7d6dbde4fff71eacb'
context:
  - '{project-root}/backend/app/graph/nodes.py'
  - '{project-root}/backend/app/prompts/system.py'
  - '{project-root}/backend/app/api/chat.py'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem :** Deux régressions chat bloquent la Vague 2 de tests manuels. BUG-V2-001 : `chat_node` laisse passer des caractères chinois (ex. « 基本信息 ») dans la réponse finale après un tool call MiniMax (régression partielle BUG-011). BUG-V2-002 : après soumission d'un widget interactif, `chat_node` produit un `content=""` car MiniMax considère le tool call (`update_company_profile`, etc.) comme réponse suffisante — l'utilisateur voit une bulle assistant vide et tous les tests T-CHAT-04/08/09/14/17 + T-ESG/CARBON/FIN-chat sont bloqués.

**Approach :** Renforcer le prompt système de `chat_node` pour (a) forcer une réponse textuelle visible **après chaque tool call** et (b) réitérer la contrainte linguistique française en **fin** de prompt (dernière consigne vue par le LLM). Aucune modification du graphe LangGraph, aucun changement de schéma BDD, aucune modification frontend.

## Boundaries & Constraints

**Always :**
- Modifier uniquement `chat_node` dans `backend/app/graph/nodes.py` et les helpers qu'il appelle directement (prompts/system.py si extraction d'une constante partageable).
- Conserver le format existant de `tool_instructions` (string concaténée avec `full_prompt`).
- Garder `LANGUAGE_INSTRUCTION` en tête via `build_system_prompt` (pas de retrait).
- Les instructions ajoutées doivent être en français avec accents corrects.
- Tests unitaires pytest pour chaque nouvelle contrainte de prompt.

**Ask First :**
- Si le patch impose d'étendre la fix aux 6 nœuds spécialistes (esg/carbon/financing/application/credit/action_plan) → HALT : le scope de cette spec est `chat_node` uniquement.
- Si la détection post-génération (filet de sécurité regex CJK ou retry LLM) est nécessaire → HALT avant de l'ajouter.

**Never :**
- Ne jamais modifier le graphe `graph.py`, la boucle `_should_continue_tool_loop`, ou `MAX_TOOL_CALLS_PER_TURN`.
- Ne jamais toucher à l'orchestration SSE (`stream_graph_events`), au résolveur de widget (`_resolve_interactive_question`), ni au composable frontend `useChat.ts`.
- Ne jamais ajouter de retry automatique côté `api/chat.py` (Option B du brief écartée — garder la fix 100 % prompt).
- Ne jamais introduire un filet de sécurité regex CJK à la sortie (trop fragile, rejet explicite).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Widget QCU soumis (secteur=Agriculture) | `POST /api/chat/messages` avec `interactive_question_id` + `values=["Agriculture"]` | Tool `update_company_profile` exécuté, puis AIMessage **non vide** confirmant la mise à jour et posant la question suivante, 100 % en français | N/A |
| Widget QCM soumis (multi-choix) | Même que ci-dessus, valeurs multiples | Idem — texte visible post-tool | N/A |
| Message texte libre déclenchant un tool | User : « quel est mon score ESG ? » → tool `get_esg_assessment_chat` | Réponse textuelle visible avec score, zéro caractère CJK ou latin étranger | N/A |
| Chat général sans tool call | User : « salut » | Réponse courte française (comportement inchangé) | N/A |
| Tool call enchaîné (2 tools successifs) | LLM appelle 2 tools avant réponse finale | La réponse finale est textuelle et française | N/A |

</frozen-after-approval>

## Code Map

- `backend/app/graph/nodes.py` — `chat_node()` lignes ~1175-1223 : construction du prompt, concaténation `tool_instructions`, appel `llm.ainvoke`. Cible principale des deux fix.
- `backend/app/prompts/system.py` — `LANGUAGE_INSTRUCTION` (lignes 3-8) et `build_system_prompt()` (ligne 179) : le prompt système commence déjà par `LANGUAGE_INSTRUCTION`, mais MiniMax le « oublie » après un ToolMessage. Pas de modification directe, mais on peut réutiliser la constante.
- `backend/app/api/chat.py` — lignes 695-735 : pour contexte uniquement (résolution widget → `message_content = synthesized`). **Aucune modification**.
- `backend/app/graph/graph.py` — `_should_continue_tool_loop` : contexte du flux post-tool. **Aucune modification**.
- `backend/tests/test_graph/` — emplacement des tests existants ; ajouter un test ciblé sur le contenu du prompt `chat_node`.

## Tasks & Acceptance

**Execution :**
- [x] `backend/app/graph/nodes.py` — Dans `chat_node()`, enrichir `tool_instructions` avec une puce explicite « Après avoir utilisé un outil, tu DOIS toujours générer une réponse textuelle visible pour l'utilisateur. Ne laisse jamais ta réponse vide après un tool call. Confirme l'action effectuée et pose la question suivante si pertinent. » — RATIONALE : corrige BUG-V2-002 (Option A du brief).
- [x] `backend/app/graph/nodes.py` — Dans `chat_node()`, **append** une copie de `LANGUAGE_INSTRUCTION` en **fin** de `full_prompt` (après `page_context`), préfixée par `RAPPEL FINAL — ` pour renforcer la consigne en dernière position du prompt. Importer la constante depuis `app.prompts.system`. RATIONALE : corrige BUG-V2-001 (primauté de la dernière instruction chez MiniMax).
- [x] `backend/tests/test_graph/test_chat_node_prompt.py` (nouveau fichier) — 3 tests unitaires pytest :
  - `test_chat_node_prompt_contains_post_tool_reminder` : vérifie que le prompt construit contient la nouvelle puce « réponse textuelle visible ».
  - `test_chat_node_prompt_ends_with_language_reminder` : vérifie que le prompt se termine par un rappel linguistique français (contient « RAPPEL FINAL » et « français »).
  - `test_chat_node_prompt_language_instruction_still_at_head` : vérifie la non-régression (LANGUAGE_INSTRUCTION présent en tête via `build_system_prompt`).
- [x] Mettre à jour `_bmad-output/implementation-artifacts/tests-manuels-vague-2-2026-04-23.md` : marquer BUG-V2-001 et BUG-V2-002 en status `FIXED` avec renvoi vers cette spec (tâche de closure).

**Acceptance Criteria :**
- Given une conversation chat où le LLM vient d'appeler un tool, when `chat_node` est réinvoqué avec le ToolMessage en historique, then la réponse assistant a `content` non vide et en français.
- Given un widget QCU soumis avec `values=["Agriculture"]`, when l'utilisateur observe la réponse, then il voit un texte de confirmation en français (« Secteur enregistré : Agriculture. Prochaine question… » ou équivalent) et non une bulle vide.
- Given une réponse générée par MiniMax après tool call, when on inspecte le contenu, then aucun caractère CJK (`一-鿿`) n'est présent dans les 50 premières réponses de test (vérification manuelle via tests manuels T-CHAT-02/04/08).
- Given la suite pytest backend complète, when elle est exécutée, then 0 régression — toutes les suites `test_graph/` et `test_chat*/` existantes passent ; 3 nouveaux tests verts.

## Spec Change Log

_(vide — aucun bad_spec loopback pour l'instant)_

## Design Notes

**Pourquoi l'Option A (prompt) plutôt que B (retry runtime) :**
Le retry côté `api/chat.py` après détection de contenu vide impliquerait de dupliquer la logique `astream_events`, reconstruire un tour LLM avec un HumanMessage injecté (« Continue en français »), et gérer la sauvegarde d'un second AIMessage. Risque élevé de régression SSE et doublement du coût tokens. L'Option A reste 100 % dans le prompt, testable en 3 assertions unitaires, sans impact sur le coût.

**Pourquoi répéter LANGUAGE_INSTRUCTION en fin de prompt :**
Les modèles entraînés massivement sur du chinois (MiniMax) ont tendance à respecter davantage la dernière instruction vue, surtout après qu'une `ToolMessage` (souvent en anglais technique ou JSON) a « pollué » le contexte. Placer le rappel en fin agit comme une consigne de proximité au moment de la génération. Précédent dans le projet : DEF-BUG-011-1 (commit `a7c258e`) a déjà utilisé le même pattern pour les 6 builders spécialistes.

**Exemple minimal de la section `tool_instructions` augmentée :**

```python
tool_instructions = (
    "\n\nINSTRUCTIONS CONSULTATION BASE :\n"
    # ... puces existantes inchangées ...
    "- LANGUE : Réponds TOUJOURS en français, même après avoir utilisé un outil. "
    "Jamais de chinois, jamais d'anglais dans ta réponse finale.\n"
    "- Après avoir utilisé un outil (tool call), tu DOIS toujours générer une réponse "
    "textuelle visible pour l'utilisateur. Ne laisse jamais ta réponse vide après un "
    "tool call. Confirme l'action effectuée et pose la question suivante si pertinent."
)
```

Et à la fin du `full_prompt` :

```python
from app.prompts.system import LANGUAGE_INSTRUCTION
full_prompt = full_prompt + "\n\nRAPPEL FINAL — " + LANGUAGE_INSTRUCTION
```

## Verification

**Commands :**
- `cd backend && source venv/bin/activate && pytest tests/test_graph/ -v` — expected : tous verts, 3 nouveaux tests `test_chat_node_prompt_*` passent.
- `cd backend && source venv/bin/activate && pytest -q` — expected : suite backend complète verte, aucun test précédemment passant ne casse (~935 tests).
- `cd backend && source venv/bin/activate && ruff check app/graph/nodes.py app/prompts/system.py` — expected : 0 erreur.

**Manual checks :**
- Redémarrer backend + frontend, se connecter avec `amadou@ecosolaire.sn` / `TestPass123!`, ouvrir `/chat`, déclencher un widget (profiling secteur ou question clarification), soumettre un choix → la bulle assistant suivante doit contenir un texte visible français (non vide) et aucun caractère chinois. Valider T-CHAT-02, T-CHAT-04, T-CHAT-08 dans `tests-manuels-vague-2-2026-04-23.md`.

## Suggested Review Order

**Design intent — prompt engineering MiniMax post-tool**

- Entry point : la nouvelle puce qui oblige le LLM à émettre du texte après un tool call (BUG-V2-002)
  [`nodes.py:1199`](../../backend/app/graph/nodes.py#L1199)

- Append du `RAPPEL FINAL` en queue de prompt pour dominer le dernier ToolMessage (BUG-V2-001)
  [`nodes.py:1215`](../../backend/app/graph/nodes.py#L1215)

- Import de `LANGUAGE_INSTRUCTION` depuis le module central, évite une duplication littérale
  [`nodes.py:1207`](../../backend/app/graph/nodes.py#L1207)

**Tests — invariants du prompt**

- Présence de la puce post-tool dans le SystemMessage capturé
  [`test_chat_node_prompt.py:75`](../../backend/tests/test_graph/test_chat_node_prompt.py#L75)

- Présence du rappel linguistique dans les 500 derniers caractères
  [`test_chat_node_prompt.py:88`](../../backend/tests/test_graph/test_chat_node_prompt.py#L88)

- Non-régression : `LANGUAGE_INSTRUCTION` toujours en tête via `build_system_prompt`
  [`test_chat_node_prompt.py:102`](../../backend/tests/test_graph/test_chat_node_prompt.py#L102)

**Traçabilité tests manuels**

- Ligne BUG-V2-001 / BUG-V2-002 marquées FIXED avec renvoi vers cette spec
  [`tests-manuels-vague-2-2026-04-23.md:254`](./tests-manuels-vague-2-2026-04-23.md#L254)

- Defer : étendre le pattern `RAPPEL FINAL` aux 6 nœuds spécialistes si régression observée
  [`deferred-work.md:917`](./deferred-work.md#L917)
