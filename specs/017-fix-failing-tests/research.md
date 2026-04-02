# Research: Correction des 34 tests en échec

**Date**: 2026-04-02 | **Branch**: 017-fix-failing-tests

## R1 — Mécanisme d'authentification dans les tests

### Decision
Utiliser `app.dependency_overrides[get_current_user]` dans un fixture conftest au lieu de `@patch("app.api.deps.get_current_user")`.

### Rationale
FastAPI évalue les dépendances Depends() AVANT le handler HTTP. Avec `@patch`, le vrai `get_current_user` s'exécute en premier — le header `Authorization: Bearer test` n'est pas un JWT valide → 401. Le mécanisme `dependency_overrides` est le moyen officiel FastAPI pour bypasser les dépendances dans les tests.

### Alternatives considered
- `@patch` sur le module deps → ne fonctionne pas avec AsyncClient + cycle de vie async
- Header JWT valide dans les tests → nécessite un secret partagé et complexifie inutilement

### Findings
- `get_current_user` est défini dans `backend/app/api/deps.py` (ligne 17)
- Signature: `async def get_current_user(credentials, db) -> User`
- 13 fichiers l'importent
- Aucun fixture auth global n'existe dans `conftest.py`
- L'app FastAPI est importée depuis `app.main`

---

## R2 — Structure ConversationState

### Decision
Créer un helper `make_conversation_state(**overrides)` retournant un dict complet avec les 27 clés.

### Rationale
Les nodes accèdent directement aux clés du state dict. Un dict incomplet provoque des KeyError. Un helper centralisé garantit la cohérence et facilite la maintenance.

### Findings
- Défini dans `backend/app/graph/state.py` (ConversationState TypedDict)
- 27 champs requis dont: messages, user_id, user_profile, context_memory, has_document, tool_call_count, active_module, active_module_data, et les paires `*_data` / `_route_*` pour chaque module
- Le reducer `add_messages` est utilisé pour `messages`

---

## R3 — Format Form vs JSON (chat endpoint)

### Decision
Modifier les tests pour envoyer `data=` (Form multipart) au lieu de `json=` (JSON body).

### Rationale
L'endpoint `send_message` déclare `content: str = Form(None)` + `file: UploadFile = File(None)`. FastAPI ne parse pas les champs Form() depuis un body JSON. Modifier l'endpoint casserait la compatibilité avec l'upload de fichiers.

### Findings
- Endpoint: `POST /conversations/{id}/messages`
- Signature: `content: str = Form(None), file: UploadFile | None = File(None)`
- Situé dans `backend/app/api/chat.py` lignes 480-486
- Un endpoint JSON alternatif `send_message_json` existe déjà (lignes 696-712)

---

## R4 — Mock AsyncMock chain pour application node

### Decision
Utiliser `AIMessage` de LangChain + `AsyncMock` avec chaîne `bind_tools().ainvoke()` correcte.

### Rationale
`MagicMock()` ne supporte pas correctement `await` et la chaîne async `bind_tools → ainvoke`. `AsyncMock` gère nativement les coroutines.

### Findings
- Le node fait `response = await llm.ainvoke(messages)`
- Le mock doit supporter: `mock_llm.bind_tools.return_value = mock_llm` (chaînage)
- La réponse doit être un `AIMessage(content="...")`, pas un MagicMock

---

## R5 — WeasyPrint mock strategy

### Decision
Mocker WeasyPrint via `patch.dict(sys.modules, {"weasyprint": mock})` pour éviter l'import réel.

### Rationale
WeasyPrint fait un import C-level à l'import Python (`libgobject-2.0`). Un `@patch` simple ne suffit pas car l'import échoue avant que le patch soit actif. Le pattern `sys.modules` est déjà utilisé dans `test_applications/test_prep_sheet.py`.

### Findings
- Import lazily dans `backend/app/modules/reports/service.py` ligne 305
- Usage: `HTML(string=html_content).write_pdf(str(pdf_path))`
- Pattern existant dans le projet: `patch.dict(sys.modules, {"weasyprint": mock_weasyprint})`
